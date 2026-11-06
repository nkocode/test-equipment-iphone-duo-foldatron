"""Check deliverable integrity and critical CAD interfaces independently."""

import hashlib
import json
from pathlib import Path

import cadquery as cq
import ezdxf

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "hardware/rev-b"


def close(actual, expected, tolerance=1e-4):
    if abs(actual - expected) > tolerance:
        raise AssertionError(f"Expected {expected}, received {actual}")


def main():
    parts = json.loads((DATA / "custom-parts.json").read_text())
    bom = json.loads((DATA / "bom.json").read_text())["items"]
    bom_by_id = {p["id"]: p for p in bom}
    for part in parts:
        pid = part["id"]
        shape = cq.importers.importStep(str(DATA / "cad" / f"{pid}.step"))
        solid = shape.val()
        assert solid.isValid(), pid
        close(solid.Volume(), part["volume_mm3"], 0.002)
        assert part["quantity"] > 0, f"Uninstalled custom part {pid}"
        assert bom_by_id[pid]["quantity"] == part["quantity"], pid
    for path in (DATA / "cad").glob("*.dxf"):
        document = ezdxf.readfile(path)
        assert document.units == 4, f"DXF is not millimetres: {path}"
        assert len(document.modelspace()) > 0, path
        assert not document.audit().has_errors, path
    by_id = {p["id"]: p for p in parts}
    # Check critical interfaces against independent nominal requirements.
    plate_holes = by_id["B109"]["features"]
    assert {(f["x"], f["y"]) for f in plate_holes} == {
        (x, y) for x in (-4, 4) for y in (-51, -39, 39, 51)
    }
    close(6 - 4, 2)  # Block screw engagement, maximum vendor depth 2.5.
    assert 6 - 4 < 2.5
    close(8 - 6 - 0.2, 1.8)  # Horn screw engagement, maximum 2.0.
    assert 8 - 6 - 0.2 < 2
    close(8 - 6, 2)  # Actuator case screw engagement, maximum 3.0.
    assert 8 - 6 < 3
    checks = json.loads((DATA / "verification.json").read_text())
    assert checks["sampled_sweep_collisions"] == [], checks[
        "sampled_sweep_collisions"
    ]
    assert checks["endpoint_static_collisions"] == [], checks[
        "endpoint_static_collisions"
    ]
    heights = sorted({f["y"] for f in by_id["B127"]["features"]})
    close(heights[1] - heights[0], 6.5)
    close(heights[3] - heights[2], 6.5)
    close(20 - 12 - 1, 7)  # Endpoint sole screw engagement in 8mm base.
    assert checks["sampled_minimum_moving_z_mm"] > 5
    assert checks["total_extrusion_mm"] == 7924.8
    for source in json.loads((DATA / "source-register.json").read_text()):
        if source.get("filename"):
            assert source.get("sha256"), source["id"]
            path = DATA / "vendor" / source["filename"]
            if path.exists():
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                assert actual == source["sha256"], source["id"]
    board = json.loads((DATA / "controller-board.json").read_text())
    assert board["checks"]["no_unintended_copper_shorts"]
    assert board["checks"]["occupied_holes"] == 55
    assert board["checks"]["distinct_circuit_nets"] == 13
    assert board["checks"]["endpoint_gpio_max_v"] < 3.3
    assert board["checks"]["endpoint_contact_min_a"] >= 0.001
    for name in (
        "Foldatron-Rev-B-drawing-book.pdf",
        "Foldatron-Rev-B-assembly-traveler.pdf",
    ):
        assert (ROOT / "docs/rev-b" / name).read_bytes().startswith(b"%PDF-")
    print(
        f"PASS: {len(parts)} STEP solids, BOM quantities, DXF units, "
        "guide/motor screw interfaces and sampled motion clearances"
    )
    print(
        "Not checked: actual purchased hardware, continuous motion, "
        "phone contacts, complete harness, safety performance or endurance"
    )


if __name__ == "__main__":
    main()
