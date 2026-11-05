"""Validated API contracts and installation limits."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Recipe(Model):
    specimen: str = Field(min_length=1, max_length=100)
    cycles: int = Field(default=100, ge=1, le=10_000_000, strict=True)
    speed_deg_s: float = Field(default=15, ge=1, le=30)
    dwell_s: float = Field(default=1, ge=0.25, le=60)
    current_limit_ma: float = Field(default=150, ge=20, le=350)
    inspection_every: int = Field(default=1000, ge=1, le=10_000)


class Calibration(Model):
    # Deliberately uncommissioned: simulator runs; hardware refuses motion.
    commissioned: bool = False
    record_id: str = Field(default="UNCOMMISSIONED", max_length=100)
    closed_tick: int = Field(default=1024, ge=256, le=3839)
    open_tick: int = Field(default=2958, ge=256, le=3839)
    closed_angle_deg: float = Field(default=5, ge=0, le=15)
    open_angle_deg: float = Field(default=175, ge=165, le=180)
    max_current_ma: float = Field(default=150, ge=20, le=350)
    max_speed_deg_s: float = Field(default=15, ge=1, le=30)
    max_case_c: float = Field(default=40, ge=25, le=42)
    max_motor_c: float = Field(default=55, ge=30, le=60)
    max_ambient_c: float = Field(default=30, ge=15, le=35)

    @model_validator(mode="after")
    def valid_stroke(self):
        if not 1500 <= self.open_tick - self.closed_tick <= 2100:
            raise ValueError("Open tick must be 1500–2100 above closed tick")
        motor_span = (self.open_tick - self.closed_tick) * 360 / 4096
        phone_span = self.open_angle_deg - self.closed_angle_deg
        if abs(motor_span - phone_span) > 2:
            raise ValueError("Angle/tick span must agree for the 1:1 drive")
        if self.commissioned and self.record_id == "UNCOMMISSIONED":
            raise ValueError("Commissioning requires a recorded inspection ID")
        return self


class Telemetry(Model):
    timestamp: str
    mode: Literal["simulation", "hardware"]
    angle_deg: float
    motor_tick: int
    current_ma: float
    motor_c: float
    case_c: float
    ambient_c: float
    supply_v: float
    safety_permit: bool
    open_sensor: bool
    closed_sensor: bool
    hardware_error: int = 0
    watchdog_error: bool = False


class Run(Model):
    id: str
    mode: Literal["simulation", "hardware"]
    state: Literal[
        "running", "paused", "completed", "stopped", "faulted", "interrupted"
    ]
    phase: str
    completed_cycles: int
    recipe: Recipe
    calibration: Calibration
    started_at: str
    updated_at: str
    fault: str | None = None


class Status(Model):
    mode: Literal["simulation", "hardware"]
    state: str
    fault: str | None
    active_run: Run | None
    telemetry: Telemetry | None


class Sample(Telemetry):
    seq: int


class Event(Model):
    seq: int
    at: str
    kind: str
    body: dict[str, Any]


class Inspection(Model):
    result: Literal["pass", "fail"]
    notes: str = Field(min_length=1, max_length=2000)


class Jog(Model):
    target: Literal["open", "closed"]


class Action(Model):
    accepted: bool = True
    detail: str


class Error(Model):
    detail: str
