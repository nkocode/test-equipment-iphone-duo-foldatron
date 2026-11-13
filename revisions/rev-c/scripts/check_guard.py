"""Check dimension arithmetic and conservative guard-opening clearance."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def reach_margin(radius, x=340.5, y=-355.6):
    return math.hypot(x - 12.5, y - 12.5) - radius


def main():
    door_left = -355.6 + 1.5748
    door_right = 340.5
    door_width = door_right - door_left
    sensing_gap = 368.3 - (door_right - 12.7) - 2 * 19
    assert math.isclose(sensing_gap, 2.5, abs_tol=1e-8)
    assert math.isclose(door_width - 50.8, 643.7252, abs_tol=1e-8)
    assert 0 < 6 < 8.2042
    clearance = reach_margin(300)
    assert clearance > 150
    # Negative control: reject a hose loop extending near the opening.
    assert reach_margin(400) < 150
    report = {
        "status": "PASS_FOR_NOMINAL_LAYOUT_ONLY",
        "door_width_mm": round(door_width, 4),
        "latch_side_opening_mm": 15.1,
        "switch_gap_mm": sensing_gap,
        "panel_capture_mm": 6,
        "conservative_motion_radius_mm": 300,
        "nearest_opening_clearance_mm": round(clearance, 3),
        "design_minimum_clearance_mm": 150,
        "negative_control_400_mm_radius_rejected": True,
        "excluded": ["Physical reach/stopping time", "Panel retention",
                     "Tolerance stack", "Actual hose routing",
                     "Door swing and latch solids", "Actual phone"],
    }
    (ROOT / "hardware/guard-checks.json").write_text(
        json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
