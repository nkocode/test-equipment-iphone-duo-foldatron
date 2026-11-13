"""One serialized worker owns motion, sensors, and durable cycle commits."""

import queue
import shutil
import threading
import time
import uuid
from concurrent.futures import Future, TimeoutError

from .hardware import Dynamixel, HardwareFault, Simulator
from .models import Recipe, Run, Status
from .storage import Store, utc_now


class Conflict(RuntimeError):
    pass


class Controller:
    def __init__(self, settings, driver=None):
        self.settings = settings
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        # Excludes another Uvicorn worker or service using the same data dir.
        import fcntl

        self.lease = open(settings.data_dir / "controller.lock", "a+")
        try:
            fcntl.flock(self.lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self.lease.close()
            raise RuntimeError("Another controller owns this data directory")
        self.lock = threading.RLock()
        self.store = Store(settings.data_dir / "foldbench.sqlite3")
        self.store.recover()
        self.driver = driver
        self.run = None
        self.telemetry = None
        self.state = "idle"
        self.fault = None
        self.unconfirmed_stop = False
        self.commands = queue.Queue(maxsize=32)
        self.stop_request = threading.Event()
        self.shutdown = threading.Event()
        self.pause_requested = False
        self.inspection_required = False
        self.jogging = False
        self.target = None
        self.target_sensor = None
        self.deadline = 0.0
        self.dwell_until = 0.0
        self.settled_since = None
        self.last_sample = 0.0
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _connect(self):
        if self.driver is None:
            factory = (
                Simulator
                if self.settings.mode == "simulation"
                else (Dynamixel)
            )
            self.driver = factory(self.settings)

    def call(self, name, *args):
        future = Future()
        try:
            self.commands.put_nowait((future, name, args))
        except queue.Full:
            raise Conflict("Controller command queue is full")
        try:
            return future.result(timeout=10)
        except TimeoutError:
            future.cancel()
            self.stop_request.set()
            raise Conflict("Controller timed out; protective stop requested")

    def snapshot(self):
        with self.lock:
            return Status(
                mode=self.settings.mode,
                state=self.state,
                fault=self.fault,
                active_run=self.run,
                telemetry=self.telemetry,
            ).model_copy(deep=True)

    def emergency_stop(self):
        # Set without waiting for the bus, database, queue, or controller lock.
        self.stop_request.set()

    def _disable(self):
        if self.driver:
            self.driver.disable()

    def _fault(self, message):
        self.state = "faulted"
        self.fault = message
        self.jogging = False
        try:
            self._disable()
        except Exception:
            self.unconfirmed_stop = True
            self.fault += "; torque-off unconfirmed: use physical E-stop"
        if self.run and self.run.state in {"running", "paused"}:
            self.run.state = "faulted"
            self.run.phase = "faulted"
            self.run.fault = self.fault
            try:
                self.store.save(self.run)
                self.store.event(self.run.id, "fault", {"detail": self.fault})
            except Exception:
                self.fault += "; persistence failed"

    def _healthy(self, sample):
        cal = self.settings.calibration
        checks = (
            (not sample.safety_permit, "Safety circuit open"),
            (
                sample.open_sensor and sample.closed_sensor,
                "Both endpoint sensors active",
            ),
            (sample.hardware_error != 0, "Servo hardware fault"),
            (sample.watchdog_error, "Servo watchdog tripped"),
            (sample.case_c >= cal.max_case_c, "Phone case temperature limit"),
            (sample.motor_c >= cal.max_motor_c, "Motor temperature limit"),
            (
                not 10 <= sample.ambient_c <= cal.max_ambient_c,
                "Ambient temperature outside test range",
            ),
            (not 10.5 <= sample.supply_v <= 13.0, "Motor supply out of range"),
            (
                not cal.closed_tick - 25
                <= sample.motor_tick
                <= cal.open_tick + 25,
                "Position outside stroke",
            ),
        )
        for condition, message in checks:
            if condition:
                raise HardwareFault(message)
        if sample.open_sensor and abs(sample.motor_tick - cal.open_tick) > 30:
            raise HardwareFault("Open sensor disagrees with motor encoder")
        if (
            sample.closed_sensor
            and abs(sample.motor_tick - cal.closed_tick) > 30
        ):
            raise HardwareFault("Closed sensor disagrees with motor encoder")
        current_limit = cal.max_current_ma
        if self.run and self.run.state == "running":
            current_limit = self.run.recipe.current_limit_ma
        if abs(sample.current_ma) > current_limit + 15:
            raise HardwareFault("Motor current exceeded configured limit")

    def _limits(self, recipe):
        cal = self.settings.calibration
        if recipe.speed_deg_s > cal.max_speed_deg_s:
            raise Conflict("Recipe speed exceeds installation limit")
        if recipe.current_limit_ma > cal.max_current_ma:
            raise Conflict("Recipe current exceeds installation limit")
        if self.settings.mode == "hardware" and not cal.commissioned:
            raise Conflict("Hardware installation is not commissioned")

    def _idle(self):
        if self.state != "idle":
            raise Conflict("Controller must be idle and fault-free")

    def _prepare(self, recipe):
        self._limits(recipe)
        self._connect()
        self._healthy(self.driver.read())
        self.driver.prepare(recipe)

    def _move(self, target_sensor, speed):
        cal = self.settings.calibration
        self.target_sensor = target_sensor
        self.target = (
            cal.open_tick if target_sensor == "open" else cal.closed_tick
        )
        self.driver.move(self.target)
        # Conservative full-stroke timeout allows acceleration/deceleration.
        self.deadline = time.monotonic() + 180 / speed + 8
        self.settled_since = None

    def _start(self, recipe, key):
        existing = self.store.request(key)
        if existing:
            if Recipe.model_validate_json(existing[1]) != recipe:
                raise Conflict("Idempotency key used for another recipe")
            return self.store.get(existing[0])
        self._idle()
        self._limits(recipe)
        if shutil.disk_usage(self.settings.data_dir).free < 100 * 1024**2:
            raise Conflict("Less than 100 MiB disk space remains")
        run = Run(
            id=str(uuid.uuid4()),
            mode=self.settings.mode,
            state="running",
            phase="initial_open",
            completed_cycles=0,
            recipe=recipe,
            calibration=self.settings.calibration.model_copy(deep=True),
            started_at=utc_now(),
            updated_at=utc_now(),
        )
        self.run = run
        # Commit intent before enabling torque. A crash becomes interrupted.
        self.store.create_run(run, key)
        self.store.event(run.id, "start", {})
        self._prepare(recipe)
        self.state = "running"
        self.pause_requested = False
        self.inspection_required = False
        self._move("open", recipe.speed_deg_s)
        return self.run.model_copy(deep=True)

    def _pause(self, run_id):
        self._active(run_id, "running")
        self.pause_requested = True
        return {"accepted": True, "detail": "Pause at next complete cycle"}

    def _resume(self, run_id):
        self._active(run_id, "paused")
        if self.inspection_required:
            raise Conflict("A passing inspection is required before resuming")
        self._prepare(self.run.recipe)
        self.run.state = "running"
        self.run.phase = "initial_open"
        self.state = "running"
        self.pause_requested = False
        self.store.save(self.run)
        self.store.event(run_id, "resume", {})
        self._move("open", self.run.recipe.speed_deg_s)
        return self.run.model_copy(deep=True)

    def _active(self, run_id, state=None):
        if not self.run or self.run.id != run_id:
            raise Conflict("This is not the active run")
        if state and self.run.state != state:
            raise Conflict(f"Run must be {state}")

    def _stop(self, run_id):
        self._active(run_id)
        if self.run.state not in {"running", "paused"}:
            return self.run.model_copy(deep=True)
        self._disable()
        self.run.state = "stopped"
        self.run.phase = "stopped"
        self.state = "idle"
        self.store.save(self.run)
        self.store.event(run_id, "stop", {})
        return self.run.model_copy(deep=True)

    def _reset(self):
        if self.state in {"running", "jogging", "paused"}:
            raise Conflict("Stop the active operation before reset")
        self._connect()
        self._disable()
        self.unconfirmed_stop = False
        sample = self.driver.read()
        self._healthy(sample)
        self.fault = None
        self.state = "idle"
        self.telemetry = sample
        self.store.event(None, "reset", {})
        return {"accepted": True, "detail": "Fault reset; motion remains off"}

    def _inspect(self, run_id, inspection):
        self._active(run_id, "paused")
        self.store.event(run_id, "inspection", inspection.model_dump())
        if inspection.result == "fail":
            self._fault("Operator inspection failed: " + inspection.notes)
        else:
            self.inspection_required = False
        return self.run.model_copy(deep=True)

    def _jog(self, target):
        self._idle()
        recipe = Recipe(
            specimen="commissioned setup jog",
            cycles=1,
            speed_deg_s=5,
            current_limit_ma=min(
                100, self.settings.calibration.max_current_ma
            ),
        )
        self._prepare(recipe)
        self.jogging = True
        self.state = "jogging"
        self._move(target, recipe.speed_deg_s)
        self.store.event(None, "jog", {"target": target})
        return {"accepted": True, "detail": "Guarded endpoint jog started"}

    def _arrived(self, now):
        sample = self.telemetry
        sensor = (
            sample.open_sensor
            if self.target_sensor == "open"
            else sample.closed_sensor
        )
        if abs(sample.motor_tick - self.target) <= 12 and sensor:
            if self.settled_since is None:
                self.settled_since = now
            return now - self.settled_since >= 0.15
        self.settled_since = None
        return False

    def _advance(self, now):
        if self.state not in {"running", "jogging"}:
            return
        if self.state == "jogging":
            if self._arrived(now):
                self._disable()
                self.jogging = False
                self.state = "idle"
            elif now > self.deadline:
                raise HardwareFault("Jog timed out; inspect alignment")
            return
        phase = self.run.phase
        if phase in {"open_dwell", "closed_dwell"}:
            # Endpoint evidence must persist throughout the dwell.
            if not self._arrived(now):
                raise HardwareFault("Endpoint lost during dwell")
            if now >= self.dwell_until:
                if phase == "open_dwell":
                    self.run.phase = "closing"
                    self._move("closed", self.run.recipe.speed_deg_s)
                else:
                    self.run.phase = "opening"
                    self._move("open", self.run.recipe.speed_deg_s)
            return
        if not self._arrived(now):
            if now > self.deadline:
                raise HardwareFault("Stroke timed out; jam, slip, or sensor")
            return
        self.store.sample(self.run.id, self.telemetry)
        if phase == "opening":
            # Only confirmed open -> closed -> open increments the count.
            self.run.completed_cycles += 1
            self.store.save(self.run)
            if self.run.completed_cycles >= self.run.recipe.cycles:
                self._disable()
                self.run.state = "completed"
                self.run.phase = "completed"
                self.state = "idle"
                self.store.save(self.run)
                self.store.event(self.run.id, "completed", {})
                return
            self.inspection_required = (
                self.run.completed_cycles % self.run.recipe.inspection_every
                == 0
            )
            if self.pause_requested or self.inspection_required:
                self._disable()
                self.run.state = "paused"
                self.run.phase = (
                    "inspection" if self.inspection_required else "paused"
                )
                self.state = "paused"
                self.store.save(self.run)
                self.store.event(self.run.id, "pause", {})
                return
        self.run.phase = "closed_dwell" if phase == "closing" else "open_dwell"
        self.dwell_until = now + self.run.recipe.dwell_s

    def _loop(self):
        while not self.shutdown.is_set():
            started = time.monotonic()
            with self.lock:
                try:
                    if self.stop_request.is_set():
                        self.stop_request.clear()
                        self._fault("API protective stop requested")
                    try:
                        future, name, args = self.commands.get_nowait()
                    except queue.Empty:
                        pass
                    else:
                        if future.set_running_or_notify_cancel():
                            try:
                                result = getattr(self, "_" + name)(*args)
                            except Conflict as exc:
                                future.set_exception(exc)
                            except Exception as exc:
                                self._fault(str(exc))
                                future.set_exception(Conflict(self.fault))
                            else:
                                future.set_result(result)
                    if self.unconfirmed_stop:
                        raise HardwareFault("Torque-off remains unconfirmed")
                    self._connect()
                    self.telemetry = self.driver.read()
                    if self.state != "faulted":
                        self._healthy(self.telemetry)
                    now = time.monotonic()
                    self._advance(now)
                    if now - self.last_sample >= 1:
                        self.last_sample = now
                        if self.state == "running":
                            if (
                                shutil.disk_usage(self.settings.data_dir).free
                                < 100 * 1024**2
                            ):
                                raise HardwareFault("Disk space below 100 MiB")
                            self.store.sample(self.run.id, self.telemetry)
                except Exception as exc:
                    if self.state != "faulted":
                        self._fault(str(exc))
                    self.telemetry = None
            delay = max(0, self.settings.tick_s - (time.monotonic() - started))
            self.shutdown.wait(delay)
        with self.lock:
            if self.run and self.run.state in {"running", "paused"}:
                self._fault("Service shutdown; no automatic resumption")
            if self.driver:
                self.driver.close()

    def close(self):
        self.stop_request.set()
        self.shutdown.set()
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            raise RuntimeError("Controller did not stop; use physical E-stop")
        self.store.close()
        self.lease.close()
