"""Exact B-rep overlap checks after a bounding-box broad-phase filter.

This checks the modeled rigid solids only. It does not validate unmodeled
hoses, fasteners, clearances between samples or an actual phone hinge path.
"""

import argparse
import json
from pathlib import Path

from build_fixture import build

ROOT = Path(__file__).resolve().parents[1]


def bbox_overlap(a, b, tolerance=0.001):
    return all(min(getattr(a, axis + "max"), getattr(b, axis + "max"))
               - max(getattr(a, axis + "min"), getattr(b, axis + "min"))
               > tolerance for axis in "xyz")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, default=10)
    args = parser.parse_args()
    if not 1 <= args.step <= 30:
        parser.error("step must be between 1 and 30 degrees")
    parts = build()
    moving = [p for p in parts if p["group"].startswith("moving")]
    fixed = [p for p in parts if p["group"].startswith("fixed")]
    fixed = [(p, p["shape"].BoundingBox()) for p in fixed]
    angles = sorted(set(range(0, 181, args.step)) | {180})
    tested = 0
    collisions = []
    for angle in angles:
        for mobile in moving:
            shape = mobile["shape"].rotate((0, 0, 0), (0, 0, 1), angle)
            bounds = shape.BoundingBox()
            for stationary, fixed_bounds in fixed:
                if not bbox_overlap(bounds, fixed_bounds):
                    continue
                overlap = shape.intersect(stationary["shape"])
                tested += 1
                volume = sum(s.Volume() for s in overlap.Solids())
                if volume > 0.01:
                    collisions.append({
                        "angle_deg": angle,
                        "moving": mobile["name"],
                        "fixed": stationary["name"],
                        "overlap_mm3": round(volume, 5),
                    })
        print(f"Checked {angle} degrees; overlaps {len(collisions)}",
              flush=True)
    report = {
        "status": "FAIL" if collisions else "PASS_FOR_MODELED_SAMPLES_ONLY",
        "angles_deg": angles,
        "exact_intersections": tested,
        "collisions": collisions,
        "excluded": [
            "Hoses, cables and fasteners not yet represented",
            "Actual phone geometry and compound hinge motion",
            "Clearance between angular samples",
            "Compliance-stage displaced positions",
            "Intentional permanent mounting contacts within each group",
        ],
    }
    path = ROOT / "hardware/fixture-sweep.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    if collisions:
        raise SystemExit("Rigid-solid sweep found overlaps; inspect report")


if __name__ == "__main__":
    main()
