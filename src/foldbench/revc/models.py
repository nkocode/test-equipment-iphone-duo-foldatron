"""Installation contract and API types for the catalog-only Rev C bench."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Commissioning(StrictModel):
    """Local file only. Values must come from the signed shop traveler."""

    released: bool = False
    evidence_record: str = ""
    phone_id: str = ""
    operator: str = ""
    stage_serial: int = Field(0, ge=0)
    open_steps: int = 0
    closed_steps: int = 768000
    max_speed_deg_s: float = Field(2.0, gt=0, le=10)
    segment_deg: float = Field(0.25, gt=0, le=0.5)
    max_temperature_c: float = Field(40.0, gt=10, le=60)
    run_current_units: int = Field(0, ge=0, le=106)
    hold_current_units: int = Field(0, ge=0, le=75)
    acceleration_units: int = Field(0, ge=0)
    stage_version: str = ""
    thermocouple_firmware_words: tuple[int, int] = (0, 0)
    hardware_acceptance: bool = False
    full_closure_verified: bool = False
    vacuum_loss_tested: bool = False
    stop_circuit_tested: bool = False
    hose_sweep_tested: bool = False
    load_limit_tested: bool = False

    @model_validator(mode="after")
    def release_evidence(self):
        span = abs(self.closed_steps - self.open_steps) * 0.000234375
        if not 150 <= span <= 185:
            raise ValueError("Commissioned fold span must be 150..185 degrees")
        if self.released:
            evidence = (
                self.evidence_record,
                self.phone_id,
                self.operator,
                self.stage_serial,
                self.stage_version,
                self.run_current_units,
                self.acceleration_units,
                self.thermocouple_firmware_words != (0, 0),
                self.hardware_acceptance,
                self.full_closure_verified,
                self.vacuum_loss_tested,
                self.stop_circuit_tested,
                self.hose_sweep_tested,
                self.load_limit_tested,
            )
            if not all(evidence):
                raise ValueError(
                    "Release requires the completed shop traveler"
                )
        return self


@dataclass
class Settings:
    mode: str = "simulation"
    api_key: str = ""
    data_dir: Path = Path("data/rev-c")
    stage_port: str = "/dev/serial/by-id/SET_ZABER_ADAPTER"
    io_port: str = "/dev/serial/by-id/SET_RS485_ADAPTER"
    stage_baud: int = 115200
    io_address: int = 1
    temperature_address: int = 2
    tick_s: float = 0.05
    calibration: Commissioning = field(default_factory=Commissioning)

    @classmethod
    def from_env(cls):
        path = os.getenv("FOLDATRON_C_COMMISSIONING")
        calibration = Commissioning()
        if path:
            calibration = Commissioning.model_validate_json(
                Path(path).read_text()
            )
        mode = os.getenv("FOLDATRON_C_MODE", "simulation")
        if mode not in {"simulation", "hardware"}:
            raise ValueError("Mode must be simulation or hardware")
        return cls(
            mode=mode,
            api_key=os.getenv("FOLDATRON_C_API_KEY", ""),
            data_dir=Path(os.getenv("FOLDATRON_C_DATA", "data/rev-c")),
            stage_port=os.getenv("FOLDATRON_C_STAGE_PORT", cls.stage_port),
            io_port=os.getenv("FOLDATRON_C_IO_PORT", cls.io_port),
            calibration=calibration,
        )


class Recipe(StrictModel):
    sample_id: str = Field(min_length=1, max_length=120)
    cycles: int = Field(1, ge=1, le=1_000_000)
    speed_deg_s: float = Field(1.0, gt=0, le=10)
    endpoint_dwell_s: float = Field(1.0, ge=0.1, le=60)


class Jog(StrictModel):
    opening_deg: float = Field(ge=0, le=180)
    speed_deg_s: float = Field(0.5, gt=0, le=2)


class SimulationFault(StrictModel):
    fault: Literal["vacuum", "permit", "temperature", "communication", "none"]


class Telemetry(StrictModel):
    timestamp: float
    stage_steps: int
    opening_deg: float
    moving: bool
    permit: bool
    vacuum_ok: tuple[bool, bool, bool, bool]
    case_temperature_c: float
    ambient_temperature_c: float
    warning: str = "--"
    simulated: bool


class Run(StrictModel):
    id: str
    recipe: Recipe
    state: Literal["running", "paused", "completed", "stopped", "faulted"]
    completed_cycles: int = 0
    started_at: float
    ended_at: float | None = None
    detail: str = ""


class Status(StrictModel):
    mode: str
    state: str
    fault: str | None
    telemetry: Telemetry | None
    telemetry_age_s: float | None
    run: Run | None
    commissioning_released: bool


class Action(StrictModel):
    detail: str


class Inspection(StrictModel):
    operator: str = Field(min_length=1, max_length=100)
    note: str = Field(min_length=1, max_length=2000)
    passed: bool


def write_example(path):
    Path(path).write_text(
        json.dumps(Commissioning().model_dump(), indent=2) + "\n"
    )
