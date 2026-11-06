"""Tessellate the drawing CAD for the offline Rev B motion-study viewer."""

import hashlib
import json
from pathlib import Path

import build_rev_b_cad as cad

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "hardware/rev-b"
OUT = ROOT / "visualization/src/rev-b-model.json"


def category(item):
    name, part = item["name"], item["part"]
    if part == "DUT":
        return "specimen", 12
    if item["group"] == "electrical":
        return "control", 16
    if item["group"] == "guard":
        return "guard", 15
    if item["group"] == "frame":
        if name.startswith(("lower_", "rail_corner_")) and "512.7" not in name:
            return "frame", 3
        if name.startswith(("crossmember_", "cross_joint_")):
            return "frame", 4
        return "frame", 5
    if name.startswith("endpoint_"):
        return "endpoints", 14
    if name.startswith(("XM430_", "motor_", "clutch_")):
        return "drive", 11
    if name.startswith(("angular_", "stop_bolt_", "stop_pad_", "fixed_")):
        return "foundation", 10
    if name == "base" or name.startswith(("tower_", "sole_", "angle_")):
        return "foundation", 6
    if name.startswith(("bearing_", "retainer_", "spacer_", "collar_")):
        return "bearings", 7
    if name in ("front_shaft", "rear_shaft"):
        return "bearings", 7
    if name.startswith(("rail_", "block_", "carrier_", "stop_")):
        return "float", 9
    if name == "float_plate":
        return "float", 9
    return "yoke", 8


def main():
    cad.build_custom()
    cad.build_frame()
    cad.build_fixture()
    cad.build_guards()
    custom = {
        p["id"]: p
        for p in json.loads((DATA / "custom-parts.json").read_text())
    }
    bom = {
        p["id"]: p
        for p in json.loads((DATA / "bom.json").read_text())["items"]
    }
    instances = []
    for item in cad.INSTANCES:
        vertices, triangles = item["shape"].tessellate(0.15, 0.15)
        group, stage = category(item)
        # B-rep vertices retain their per-face seams, so normals preserve
        # sharp machined edges. Three uses X,Z,-Y, a proper rotation.
        positions = [round(c, 4) for v in vertices for c in (v.x, v.z, -v.y)]
        bb = item["shape"].BoundingBox()
        instances.append(
            {
                "name": item["name"],
                "part": item["part"],
                "group": group,
                "stage": stage,
                "moving": item["moving"],
                "float": item["name"] == "float_plate"
                or item["name"].startswith("block_")
                or item["name"] == "phone_envelope_40",
                "rotor": item["name"] in ("XM430_horn", "motor_adapter"),
                "color": item["color"],
                "opacity": item["opacity"],
                "positions": positions,
                "indices": [i for t in triangles for i in t],
                "bounds": [
                    bb.xmin,
                    bb.zmin,
                    -bb.ymax,
                    bb.xmax,
                    bb.zmax,
                    -bb.ymin,
                ],
            }
        )
    records = {}
    for item in instances:
        part = item["part"]
        bom_part = {"F-M6-25": "F15", "C-SILICONE": "C01"}.get(part, part)
        purchase = bom.get(bom_part, {})
        drawing = custom.get(part, {})
        records[part] = {
            "title": drawing.get("title", purchase.get("part_number", part)),
            "description": purchase.get(
                "description", "Unverified fit-check envelope"
            ),
            "material": drawing.get("material", ""),
            "notes": drawing.get("notes", []),
            "source": purchase.get("source", "REFERENCE ONLY"),
            "status": purchase.get("status", "HOLD P1"),
        }
    sources = [
        "scripts/build_rev_b_cad.py",
        "hardware/rev-b/custom-parts.json",
        "hardware/rev-b/assembly-operations.json",
        "hardware/rev-b/bom.json",
        "hardware/rev-b/verification.json",
    ]
    payload = {
        "revision": "B",
        "units": "mm",
        "axis": [0, 140, 0],
        "provenance": {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in sources
        },
        "instances": instances,
        "parts": records,
        "operations": json.loads(
            (DATA / "assembly-operations.json").read_text()
        ),
        "verification": json.loads((DATA / "verification.json").read_text()),
    }
    OUT.write_text(json.dumps(payload, separators=(",", ":")) + "\n")
    print(
        f"Exported {len(instances)} CAD instances, "
        f"{sum(len(i['indices']) // 3 for i in instances)} triangles; "
        f"{OUT.stat().st_size / 1e6:.2f} MB"
    )


if __name__ == "__main__":
    main()
