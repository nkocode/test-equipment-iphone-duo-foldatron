"""One worker owns hardware. Motion proceeds only through bounded segments."""

import fcntl
import threading
import time
import uuid

from .drivers import MICROSTEP_DEG, Hardware, Simulator, target_steps
from .models import Run, Status
from .storage import Store


class Conflict(RuntimeError):
    pass


class Controller:
    def __init__(self, settings, driver=None, start_worker=True):
        self.settings = settings
        self.cal = settings.calibration
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        self.process_lock = (settings.data_dir / "controller.lock").open("a")
        try:
            fcntl.flock(self.process_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BaseException:
            self.process_lock.close()
            raise RuntimeError("Another Rev C controller owns this data path")
        try:
            self.store = Store(settings.data_dir / "runs.sqlite3")
            self.driver = driver or (
                Hardware(settings)
                if settings.mode == "hardware"
                else Simulator(settings)
            )
        except BaseException:
            if hasattr(self, "store"):
                self.store.close()
            self.process_lock.close()
            raise
        self.lock = threading.RLock()
        self.quit = threading.Event()
        self.stop_requested = threading.Event()
        self.state = "idle"
        self.fault = None
        self.telemetry = None
        self.last_sample = None
        self.last_record = 0
        self.run = None
        self.phase = None
        self.goal = None
        self.speed = None
        self.segment_deadline = None
        self.segment_target = None
        self.dwell_until = None
        self.pause_requested = False
        self.thread = None
        if start_worker:
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()

    def _loop(self):
        while not self.quit.is_set():
            with self.lock:
                try:
                    self.tick()
                except Exception as exc:
                    self.trip(f"Controller error: {type(exc).__name__}: {exc}")
            self.quit.wait(self.settings.tick_s)

    def snapshot(self):
        with self.lock:
            return Status(
                mode=self.settings.mode,
                state=self.state,
                fault=self.fault,
                telemetry=self.telemetry.model_copy(deep=True)
                if self.telemetry
                else None,
                telemetry_age_s=time.monotonic() - self.last_sample
                if self.last_sample is not None
                else None,
                run=self.run.model_copy(deep=True) if self.run else None,
                commissioning_released=self.cal.released,
            )

    def _event(self, detail):
        self.store.record(
            self.run.id if self.run else None,
            "event",
            {
                "detail": detail,
                "state": self.state,
            },
        )

    def trip(self, reason):
        self.goal = self.segment_target = self.segment_deadline = None
        self.phase = self.dwell_until = None
        self.pause_requested = False
        self.state = "faulted"
        try:
            self.driver.stop()
        except Exception as exc:
            reason += f"; stop unconfirmed: {exc}"
        self.fault = reason
        if self.run and self.run.state in {"running", "paused"}:
            self.run.state = "faulted"
            self.run.detail = reason
            self.run.ended_at = time.time()
            self.store.save(self.run)
        self._event(reason)

    def _check_sample(self, sample):
        if not sample.permit:
            raise Conflict("Hardwired permit is absent")
        if not all(sample.vacuum_ok):
            raise Conflict("One or more cup vacuum permissives are absent")
        if sample.case_temperature_c >= self.cal.max_temperature_c:
            raise Conflict("Phone temperature limit reached")
        if not -0.05 <= sample.opening_deg <= 180.05:
            raise Conflict("Position outside commissioned travel")
        if sample.warning != "--":
            raise Conflict(f"Motion-controller warning: {sample.warning}")

    def tick(self):
        if self.stop_requested.is_set():
            self.stop_requested.clear()
            self.trip("API protective stop requested")
            return
        try:
            sample = self.driver.sample()
        except Exception as exc:
            # A failed acquisition can never leave usable old telemetry.
            self.telemetry = None
            self.last_sample = None
            if self.state != "faulted":
                self.trip(f"Acquisition failed: {exc}")
            return
        self.telemetry = sample
        now = time.monotonic()
        self.last_sample = now
        if (
            self.run
            and self.run.state in {"running", "paused"}
            and (now - self.last_record >= 1)
        ):
            self.store.record(self.run.id, "sample", sample.model_dump())
            self.last_record = now
        if self.state == "faulted":
            return
        try:
            self._check_sample(sample)
        except Conflict as exc:
            if self.state in {"running", "jogging", "paused"} or sample.moving:
                self.trip(str(exc))
            return
        if self.state not in {"running", "jogging"}:
            if sample.moving:
                self.trip("Unexpected motion while controller is idle")
            return
        if self.segment_deadline is not None:
            if now > self.segment_deadline:
                self.trip("Motion segment deadline exceeded")
                return
            if sample.moving:
                return
            if abs(sample.stage_steps - self.segment_target) > 4:
                self.trip("Segment stopped short of commanded position")
                return
            self.segment_deadline = self.segment_target = None
        if sample.moving:
            self.trip("Uncommanded motion between segments")
            return
        if self.dwell_until is not None:
            if now >= self.dwell_until:
                self.dwell_until = None
                self._endpoint()
            return
        if abs(sample.stage_steps - self.goal) <= 4:
            if self.state == "jogging":
                self.state = "idle"
                self.goal = None
                self._event("Jog completed")
            else:
                self.store.record(self.run.id, "sample", sample.model_dump())
                self.dwell_until = now + self.run.recipe.endpoint_dwell_s
            return
        step = max(1, int(self.cal.segment_deg / MICROSTEP_DEG))
        difference = self.goal - sample.stage_steps
        target = sample.stage_steps + max(-step, min(step, difference))
        if self.stop_requested.is_set():
            return
        self.driver.move(target, self.speed)
        duration = (
            abs(target - sample.stage_steps) * MICROSTEP_DEG / self.speed
        )
        self.segment_target = target
        self.segment_deadline = time.monotonic() + max(2, duration * 3 + 0.5)

    def _endpoint(self):
        if self.phase == "close":
            self.phase = "open"
            self.goal = self.cal.open_steps
            return
        # Only a completed close + open pair earns a cycle.
        self.run.completed_cycles += 1
        self._event(f"Cycle {self.run.completed_cycles} completed")
        if self.run.completed_cycles >= self.run.recipe.cycles:
            self.run.state = "completed"
            self.run.ended_at = time.time()
            self.state = "idle"
            self.goal = None
        elif self.pause_requested:
            self.pause_requested = False
            self.run.state = self.state = "paused"
            self.goal = None
        else:
            self.phase = "close"
            self.goal = self.cal.closed_steps
        self.store.save(self.run)

    def ready(self):
        if self.state != "idle":
            raise Conflict(f"Controller is {self.state}")
        if self.stop_requested.is_set():
            raise Conflict("Stop is pending")
        if self.telemetry is None or self.last_sample is None:
            raise Conflict("No valid telemetry")
        if time.monotonic() - self.last_sample > 0.5:
            raise Conflict("Telemetry is stale")
        self._check_sample(self.telemetry)
        if self.telemetry.moving:
            raise Conflict("Stage has not stopped")

    def start(self, recipe, key):
        old = self.store.by_key(key)
        if old:
            if old.recipe != recipe:
                raise Conflict("Idempotency key belongs to a different recipe")
            return old
        self.ready()
        if abs(self.telemetry.stage_steps - self.cal.open_steps) > 4:
            raise Conflict("Start requires the commissioned open position")
        if recipe.speed_deg_s > self.cal.max_speed_deg_s:
            raise Conflict("Recipe speed exceeds the local limit")
        self.run = Run(
            id=str(uuid.uuid4()),
            recipe=recipe,
            state="running",
            started_at=time.time(),
        )
        self.store.save(self.run, key)
        self.state = "running"
        self.phase = "close"
        self.goal = self.cal.closed_steps
        self.speed = recipe.speed_deg_s
        self._event("Run started")
        return self.run.model_copy(deep=True)

    def jog(self, body):
        self.ready()
        if body.speed_deg_s > self.cal.max_speed_deg_s:
            raise Conflict("Jog speed exceeds the local limit")
        self.state = "jogging"
        self.goal = target_steps(body.opening_deg, self.cal)
        self.speed = body.speed_deg_s
        self._event("Jog requested")

    def reset(self):
        if self.state != "faulted":
            raise Conflict("Reset requires a latched fault")
        if self.stop_requested.is_set():
            raise Conflict("Stop is pending")
        self.driver.verify()
        sample = self.driver.sample()
        self._check_sample(sample)
        if sample.moving:
            raise Conflict("Stop has not been verified")
        self.telemetry = sample
        self.last_sample = time.monotonic()
        self.fault = None
        self.state = "idle"
        self._event("Fault reset; run remains ended; no automatic resumption")

    def run_action(self, run_id, action):
        if not self.run or self.run.id != run_id:
            raise Conflict("This is not the active run")
        if action == "pause" and self.state == "running":
            self.pause_requested = True
        elif action == "resume" and self.state == "paused":
            if (
                self.telemetry is None
                or self.last_sample is None
                or (time.monotonic() - self.last_sample > 0.5)
            ):
                raise Conflict("Fresh telemetry required")
            self._check_sample(self.telemetry)
            if (
                self.telemetry.moving
                or abs(self.telemetry.stage_steps - self.cal.open_steps) > 4
            ):
                raise Conflict("Resume requires a stopped, open fixture")
            if self.stop_requested.is_set():
                raise Conflict("Stop is pending")
            self.run.state = self.state = "running"
            self.phase = "close"
            self.goal = self.cal.closed_steps
        elif action == "stop" and self.state in {"running", "paused"}:
            self.driver.stop()
            self.run.state = "stopped"
            self.run.ended_at = time.time()
            self.goal = self.segment_target = self.segment_deadline = None
            self.phase = self.dwell_until = None
            self.pause_requested = False
            # Poll a fresh stopped sample before permitting another action.
            self.state = "faulted"
            self.fault = "Run stopped; reset verifies stationary state"
        else:
            raise Conflict("Action is invalid in the current state")
        self.store.save(self.run)
        self._event(f"Run action: {action}")
        return self.run.model_copy(deep=True)

    def close(self):
        self.quit.set()
        if self.thread:
            self.thread.join(timeout=3)
            if self.thread.is_alive():
                raise RuntimeError("Worker shutdown exceeded bounded deadline")
        with self.lock:
            try:
                if self.run and self.run.state in {"running", "paused"}:
                    self.trip("Service shutdown")
                else:
                    self.driver.stop()
            finally:
                self.driver.close()
                self.store.close()
                self.process_lock.close()
