"""Simulated and physical drivers; hardware access stays in one worker."""

import os
import struct
import threading
import time
from pathlib import Path

from .models import Telemetry
from .storage import utc_now


class HardwareFault(RuntimeError):
    """A missing, invalid, or unsafe hardware observation."""


class Simulator:
    def __init__(self, settings):
        self.settings = settings
        self.cal = settings.calibration
        self.position = float(self.cal.open_tick)
        self.target = self.position
        self.speed = 100.0
        self.enabled = False
        self.permit = True
        self.jammed = False
        self.case_c = 25.0
        self.current_ma = 40.0
        self.last = time.monotonic()

    def prepare(self, recipe):
        self.enabled = True
        self.speed = (
            recipe.speed_deg_s * 4096 / 360 * self.settings.simulation_speed
        )
        self.target = self.position

    def move(self, target):
        self.target = float(target)

    def read(self):
        now = time.monotonic()
        step = self.speed * (now - self.last)
        self.last = now
        if self.enabled and not self.jammed:
            delta = self.target - self.position
            self.position += max(-step, min(step, delta))
        fraction = (self.position - self.cal.closed_tick) / (
            self.cal.open_tick - self.cal.closed_tick
        )
        angle = self.cal.closed_angle_deg + fraction * (
            self.cal.open_angle_deg - self.cal.closed_angle_deg
        )
        return Telemetry(
            timestamp=utc_now(),
            mode="simulation",
            angle_deg=angle,
            motor_tick=round(self.position),
            current_ma=self.current_ma,
            motor_c=30,
            case_c=self.case_c,
            ambient_c=23,
            supply_v=12,
            safety_permit=self.permit,
            open_sensor=abs(self.position - self.cal.open_tick) < 10,
            closed_sensor=abs(self.position - self.cal.closed_tick) < 10,
        )

    def disable(self):
        self.enabled = False

    def close(self):
        self.disable()


class GpioInputs:
    """Linux GPIO character-device v1 ABI, without an extra Python package.

    Physical BCM lines: 17=permit, 27=open, 22=closed. All active high,
    externally pulled down. Linux must have CONFIG_GPIO_CDEV_V1 enabled.
    Chip name/offset mapping must be verified during commissioning.
    """

    def __init__(self, chip, lines):
        import fcntl

        self.ioctl = fcntl.ioctl
        # struct gpiohandle_request: 64 u32, u32, 64 u8, 32 char, u32, s32.
        request = bytearray(
            struct.pack(
                "=64II64B32sIi",
                *lines,
                *([0] * (64 - len(lines))),
                1,
                *([0] * 64),
                b"foldbench-inputs",
                len(lines),
                0,
            )
        )
        with open(chip, "rb", buffering=0) as device:
            self.ioctl(device.fileno(), 0xC16CB403, request, True)
        self.fd = struct.unpack_from("=i", request, 360)[0]

    def read(self):
        data = bytearray(64)
        self.ioctl(self.fd, 0xC040B408, data, True)
        return tuple(bool(value) for value in data[:3])

    def close(self):
        os.close(self.fd)


def read_probe(path):
    lines = Path(path).read_text().splitlines()
    if len(lines) != 2 or not lines[0].endswith("YES"):
        raise HardwareFault("Temperature probe CRC failure")
    if "t=" not in lines[1]:
        raise HardwareFault("Temperature probe has no measurement")
    value = int(lines[1].split("t=")[-1]) / 1000
    if not -10 <= value <= 70:
        raise HardwareFault("Temperature reading outside plausible range")
    return value


class Temperatures:
    """Slow 1-wire conversions never block the motor watchdog loop."""

    def __init__(self, case, ambient):
        if not case or not ambient or case == ambient:
            raise HardwareFault("Two distinct temperature probes required")
        self.paths = (case, ambient)
        self.snapshot = (0.0, None, "Temperature probes not ready")
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self):
        while not self.stop.is_set():
            try:
                values = tuple(read_probe(path) for path in self.paths)
                self.snapshot = (time.monotonic(), values, None)
            except Exception as exc:
                self.snapshot = (time.monotonic(), None, str(exc))
            self.stop.wait(0.25)

    def read(self):
        stamp, values, error = self.snapshot
        if error or time.monotonic() - stamp > 3.0:
            raise HardwareFault(error or "Temperature probes stale")
        return values

    def close(self):
        self.stop.set()
        self.thread.join(timeout=2)


class Dynamixel:
    """XM430-W350-T, ID 1, Protocol 2, 57600 baud, U2D2 TTL.

    No fallback to a simulator is permitted. Mode 5 has NO position-limit
    enforcement in the servo; the fixture needs independent hard stops.
    """

    def __init__(self, settings):
        from dynamixel_sdk import PacketHandler, PortHandler

        self.cal = settings.calibration
        self.port = PortHandler(settings.port)
        self.packet = PacketHandler(2.0)
        self.inputs = None
        self.temps = None
        if not self.port.openPort() or not self.port.setBaudRate(57600):
            self.port.closePort()
            raise HardwareFault("Cannot open U2D2 serial port")
        try:
            self.port.ser.exclusive = True
            self.port.ser.write_timeout = 0.2
            self.port.getCurrentTime = lambda: time.monotonic() * 1000
            self.disable()
            if self._read(0, 2) != 1020:
                raise HardwareFault("Expected XM430-W350 model 1020")
            if self._read(6, 1) < 38:
                raise HardwareFault("Firmware 38+ required for bus watchdog")
            self.inputs = GpioInputs(settings.gpio_chip, settings.gpio_lines)
            self.temps = Temperatures(
                settings.case_probe, settings.ambient_probe
            )
        except Exception:
            self.close()
            raise

    def _check(self, result, error):
        if result != 0 or error:
            raise HardwareFault(
                f"DYNAMIXEL communication/device error: {result}/{error}"
            )

    def _read(self, address, size):
        method = getattr(self.packet, f"read{size}ByteTxRx")
        value, result, error = method(self.port, 1, address)
        self._check(result, error)
        return value

    def _write(self, address, size, value):
        method = getattr(self.packet, f"write{size}ByteTxRx")
        result, error = method(self.port, 1, address, value)
        self._check(result, error)

    def prepare(self, recipe):
        if not self.cal.commissioned:
            raise HardwareFault("Local commissioning record is required")
        self.disable()
        if not self.inputs.read()[0]:
            raise HardwareFault("Safety power is not enabled")
        # EEPROM is written only if a value differs, with torque disabled.
        values = (
            (10, 1, 0),
            (11, 1, 5),
            (20, 4, 0),
            (38, 2, int(self.cal.max_current_ma / 2.69)),
            (63, 1, 61),
        )
        for address, size, value in values:
            if self._read(address, size) != value:
                self._write(address, size, value)
        if self._read(6, 1) >= 45 and self._read(60, 1) != 0:
            self._write(60, 1, 0)
        self._write(98, 1, 0)
        current = self._read(132, 4)
        if not self.cal.closed_tick - 20 <= current <= self.cal.open_tick + 20:
            raise HardwareFault("Position outside calibrated stroke")
        # Velocity-based profile, approximately 10 deg/s^2 acceleration.
        self._write(108, 4, 1)
        velocity = max(1, int(recipe.speed_deg_s / (0.229 * 6)))
        self._write(112, 4, velocity)
        self._write(102, 2, int(recipe.current_limit_ma / 2.69))
        self._write(116, 4, current)
        self._write(98, 1, 25)  # 500 ms; NOT a safety-rated stop.
        self._write(64, 1, 1)
        # Torque enable can change position representation. Verify it.
        if abs(self._read(132, 4) - current) > 20:
            self.disable()
            raise HardwareFault("Position changed representation on enable")

    def move(self, target):
        if not self.cal.closed_tick <= target <= self.cal.open_tick:
            raise HardwareFault("Target exceeds commissioned limits")
        self._write(116, 4, target)

    def read(self):
        permit, opened, closed = self.inputs.read()
        if not permit:
            raise HardwareFault("Guard / emergency stop / safety power open")
        case, ambient = self.temps.read()
        position = self._read(132, 4)
        if position >= 2**31:
            position -= 2**32
        current = self._read(126, 2)
        if current >= 32768:
            current -= 65536
        fraction = (position - self.cal.closed_tick) / (
            self.cal.open_tick - self.cal.closed_tick
        )
        angle = self.cal.closed_angle_deg + fraction * (
            self.cal.open_angle_deg - self.cal.closed_angle_deg
        )
        return Telemetry(
            timestamp=utc_now(),
            mode="hardware",
            motor_tick=position,
            angle_deg=angle,
            current_ma=current * 2.69,
            motor_c=self._read(146, 1),
            case_c=case,
            ambient_c=ambient,
            supply_v=self._read(144, 2) / 10,
            safety_permit=permit,
            open_sensor=opened,
            closed_sensor=closed,
            hardware_error=self._read(70, 1),
            watchdog_error=self._read(98, 1) == 255,
        )

    def disable(self):
        self._write(64, 1, 0)

    def close(self):
        try:
            self.disable()
        except Exception:
            pass
        if self.inputs:
            self.inputs.close()
        if self.temps:
            self.temps.close()
        self.port.closePort()
