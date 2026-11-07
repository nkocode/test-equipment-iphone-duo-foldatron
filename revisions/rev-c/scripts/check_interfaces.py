"""Measure original vendor STEP interfaces and record rejected screw stacks."""

import json
from pathlib import Path

import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "hardware"


def cylinders(part, radius, bottom, top):
    """Find Y-axis hole centers in original, untransformed vendor CAD."""
    shape = cq.importers.importStep(
        str(DATA / "vendor" / f"{part}.step")
    ).val()
    if not shape.isValid():
        raise ValueError(f"Invalid vendor shape: {part}")
    points = set()
    for face in shape.Faces():
        if face.geomType() != "CYLINDER":
            continue
        cylinder = BRepAdaptor_Surface(face.wrapped).Cylinder()
        if abs(cylinder.Axis().Direction().Y()) < 0.999:
            continue
        bounds = face.BoundingBox()
        if (
            abs(cylinder.Radius() - radius) < 0.001
            and abs(bounds.ymin - bottom) < 0.001
            and abs(bounds.ymax - top) < 0.001
        ):
            point = cylinder.Location()
            points.add((round(point.X(), 4), round(point.Z(), 4)))
    return sorted(points)


def require(actual, expected, label):
    if actual != sorted(expected):
        raise ValueError(f"{label}: expected {expected}; found {actual}")


def main():
    top = cylinders("X-RSW60A-E03", 2.5, 26, 31.75)
    require(
        top,
        [(x, z) for x in [-12.5, 12.5] for z in [-12.5, 12.5]],
        "Rotary top metric pattern",
    )
    base = cylinders("X-RSW60A-E03", 3.25, 0, 5.5)
    metric_base = [p for p in base if all(abs(v) == 25 for v in p)]
    require(
        metric_base,
        [(-25, -25), (-25, 25), (25, 25)],
        "Three base mounting positions",
    )
    rail = cylinders("RLA150-M", 3.3655, -4.826, -2.54)
    require(rail, [(0, z) for z in [-50, -25, 0, 25, 50]], "Rail pitch")
    carrier = cylinders("RC2-M", 1.65, 8.1034, 15.24)
    require(carrier, [(12.9032, 12.7), (37.8968, 12.7)], "Carrier taps")
    clamp = cylinders("FP01", 2.3876, -10.16, -8.128)
    require(clamp, [(0.254, 0)], "Clamp counterbore axis")
    checks = {
        "status": "CAD interface checks passed; NOT build release",
        "units": "mm",
        "coordinate_system": "Original vendor CAD; Y is vertical",
        "stage_top_M6_centers": top,
        "stage_base_metric_centers": metric_base,
        "rail_clearance_centers": rail,
        "carrier_M4_centers": carrier,
        "clamp_clearance_center": clamp,
        "carrier_pitch": round(carrier[1][0] - carrier[0][0], 4),
        "rail_to_stage": {
            "nominal_seat_stack": 2.54,
            "drawing_thread_depth": 6.5,
            "candidate_screw": "ISO 4762 M6 x 8; inspection pending",
            "nominal_engagement": 5.46,
            "rejected_screw": "M6 x 10",
            "rejected_projection": 7.46,
        },
        "clamp_to_carrier": {
            "nominal_seat_stack": 2.286,
            "drawing_usable_thread": 6.0,
            "candidate_screw": "ISO 4762 M4 x 8; inspection pending",
            "nominal_engagement": 5.714,
            "rejected_screw": "M4 x 10",
            "rejected_projection": 7.714,
        },
        "remaining": [
            "Thread leads, tolerances and screw seating not represented",
            "Clamping loads and friction not measured",
            "Guard, full fastener schedule and contact fixture incomplete",
        ],
    }
    (DATA / "interface-checks.json").write_text(
        json.dumps(checks, indent=2) + "\n"
    )
    print("Passed five original-CAD hole-pattern checks")


if __name__ == "__main__":
    main()
