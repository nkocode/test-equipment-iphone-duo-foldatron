"""Rev C motion, vacuum-permissive and thermocouple acquisition drivers."""

import math
import time

from .models import Telemetry
from .protocols import CommunicationError, Modbus, SerialPort, Zaber

MICROSTEP_DEG = 0.000234375


def opening_degrees(steps, calibration):
    fraction = (steps - calibration.open_steps) / (
        calibration.closed_steps - calibration.open_steps
    )
    return 180 * (1 - fraction)


def target_steps(opening, calibration):
    return round(
        calibration.open_steps
        + (1 - opening / 180)
        * (calibration.closed_steps - calibration.open_steps)
    )


def decode_temperature(raw):
    """Type K, engineering format: signed tenths C, NOT hundredths C."""
    if raw in (0x7FFF, 0x8000):
        raise CommunicationError("Thermocouple over/under-range or open wire")
    signed = raw if raw < 0x8000 else raw - 65536
    value = signed / 10
    if not -20 <= value <= 100:
        raise CommunicationError(
            "Temperature outside bench plausibility range"
        )
    return value


class Hardware:
    """No home or reset operation is exposed; setup is done without a phone."""

    simulated = False

    def __init__(self, settings):
        self.settings = settings
        self.cal = settings.calibration
        if not self.cal.released:
            raise ValueError("Hardware requires a locally released traveler")
        if settings.io_address == settings.temperature_address:
            raise ValueError("Modbus addresses must be distinct")
        self.ports = []
        try:
            self.ports.append(
                SerialPort(settings.stage_port, settings.stage_baud)
            )
            self.stage = Zaber(self.ports[0])
            self.ports.append(SerialPort(settings.io_port, 9600))
            self.bus = Modbus(self.ports[1])
            self.verify()
        except BaseException:
            self.close()
            raise

    def verify(self):
        checks = [
            (0, "serial", str(self.cal.stage_serial)),
            (0, "version", self.cal.stage_version),
            (0, "comm.checksum", "1"),
            (0, "comm.alert", "0"),
            (1, "resolution", "64"),
            (1, "driver.current.run", str(self.cal.run_current_units)),
            (1, "driver.current.hold", str(self.cal.hold_current_units)),
            (1, "accel", str(self.cal.acceleration_units)),
        ]
        for axis, name, expected in checks:
            reply = self.stage.command(f"get {name}", axis=axis)
            if reply.data != expected or reply.status != "IDLE":
                raise CommunicationError(f"Stage setup differs: {name}")
        device = self.settings.temperature_address
        if self.bus.registers(device, 480, 2) != (
            self.cal.thermocouple_firmware_words
        ):
            raise CommunicationError("Thermocouple firmware changed")
        if self.bus.registers(device, 482, 2) != (0x1822, 0x0070):
            raise CommunicationError("Expected an M-7018R module")
        if self.bus.registers(device, 486, 1)[0] != 15:
            raise CommunicationError("Thermocouple input type must be K")
        if self.bus.registers(device, 489, 1)[0] != 3:
            raise CommunicationError(
                "Enable only temperature channels 0 and 1"
            )
        # Base-one 00268/00269 -> zero-based 267/268: CJC and engineering.
        if self.bus.read(device, 1, 267, 2)[0] & 3 != 3:
            raise CommunicationError("CJC and engineering format required")
        # Clear the read-to-clear power-up indication at connection only.
        self.bus.read(device, 1, 272, 1)

    def sample(self):
        started = time.monotonic()
        device = self.settings.temperature_address
        inputs = self.bus.read(self.settings.io_address, 2, 0, 8)[0]
        if self.bus.read(device, 1, 272, 1)[0] & 1:
            raise CommunicationError("Temperature module rebooted")
        values = self.bus.registers(device, 0, 2, function=4)
        temperatures = tuple(decode_temperature(v) for v in values)
        position = self.stage.command("get pos")
        if time.monotonic() - started > 0.5:
            raise CommunicationError("Acquisition exceeded 0.5 s freshness")
        return Telemetry(
            timestamp=time.time(),
            stage_steps=int(position.data),
            opening_deg=opening_degrees(int(position.data), self.cal),
            moving=position.status == "BUSY",
            permit=bool(inputs & 1),
            vacuum_ok=tuple(bool(inputs & (1 << n)) for n in range(1, 5)),
            case_temperature_c=temperatures[0],
            ambient_temperature_c=temperatures[1],
            warning=position.warning,
            simulated=False,
        )

    def move(self, steps, speed):
        lower, upper = sorted((self.cal.open_steps, self.cal.closed_steps))
        if not lower <= steps <= upper:
            raise ValueError("Position outside commissioned range")
        if not 0 < speed <= self.cal.max_speed_deg_s:
            raise ValueError("Speed exceeds commissioned maximum")
        # Driver checks its own fresh position, independently of the worker.
        current = self.stage.command("get pos")
        if current.status != "IDLE":
            raise CommunicationError("Cannot queue overlapping segments")
        if abs(steps - int(current.data)) * MICROSTEP_DEG > (
            self.cal.segment_deg + MICROSTEP_DEG
        ):
            raise ValueError("Motion segment exceeds commissioned bound")
        units = math.floor(speed * 1.6384 / MICROSTEP_DEG)
        if self.stage.command("get maxspeed").data != str(units):
            self.stage.command(f"set maxspeed {units}")
            if self.stage.command("get maxspeed").data != str(units):
                raise CommunicationError("Speed readback mismatch")
        self.stage.command(f"move abs {steps}")

    def stop(self):
        self.stage.command("stop", allow_warning=True)

    def close(self):
        for port in getattr(self, "ports", []):
            port.close()


class Simulator:
    simulated = True

    def __init__(self, settings):
        self.cal = settings.calibration
        self.position = float(self.cal.open_steps)
        self.target = self.position
        self.speed = 0
        self.last = time.monotonic()
        self.fault = "none"
        self.moves = []

    def verify(self):
        return None

    def sample(self):
        now = time.monotonic()
        delta = self.target - self.position
        change = min(abs(delta), self.speed * (now - self.last))
        self.position += math.copysign(change, delta)
        self.last = now
        if self.fault == "communication":
            raise CommunicationError("Simulated serial timeout")
        return Telemetry(
            timestamp=time.time(),
            stage_steps=round(self.position),
            opening_deg=opening_degrees(self.position, self.cal),
            moving=abs(self.target - self.position) > 0.1,
            permit=self.fault != "permit",
            vacuum_ok=(self.fault != "vacuum", True, True, True),
            case_temperature_c=80 if self.fault == "temperature" else 24,
            ambient_temperature_c=22,
            simulated=True,
        )

    def move(self, steps, speed):
        self.target = steps
        self.speed = speed / MICROSTEP_DEG
        self.moves.append((steps, speed))

    def stop(self):
        self.target = self.position
        self.speed = 0

    def close(self):
        self.stop()
