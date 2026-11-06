"""Explicit installation configuration; no live API can widen limits."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from .models import Calibration


@dataclass
class Settings:
    mode: str = "simulation"
    data_dir: Path = Path("data")
    api_key: str = ""
    port: str = "/dev/serial/by-id/SET_U2D2_ID"
    gpio_chip: str = "/dev/gpiochip0"
    gpio_lines: tuple[int, int, int] = (17, 27, 22)
    case_probe: str = ""
    ambient_probe: str = ""
    calibration: Calibration = field(default_factory=Calibration)
    tick_s: float = 0.05
    simulation_speed: float = 1.0

    @classmethod
    def from_env(cls):
        path = os.getenv("FOLDBENCH_CALIBRATION")
        calibration = Calibration()
        if path:
            calibration = Calibration.model_validate(
                json.loads(Path(path).read_text())
            )
        mode = os.getenv("FOLDBENCH_MODE", "simulation")
        if mode not in {"simulation", "hardware"}:
            raise ValueError("FOLDBENCH_MODE must be simulation or hardware")
        return cls(
            mode=mode,
            data_dir=Path(os.getenv("FOLDBENCH_DATA", "data")),
            api_key=os.getenv("FOLDBENCH_API_KEY", ""),
            port=os.getenv("FOLDBENCH_PORT", "/dev/serial/by-id/SET_U2D2_ID"),
            gpio_chip=os.getenv("FOLDBENCH_GPIO", "/dev/gpiochip0"),
            case_probe=os.getenv("FOLDBENCH_CASE_PROBE", ""),
            ambient_probe=os.getenv("FOLDBENCH_AMBIENT_PROBE", ""),
            calibration=calibration,
        )
