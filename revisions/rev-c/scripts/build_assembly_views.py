"""Render staged assembly views from the purchased-part fixture geometry."""

import cadquery as cq
from build_fixture import build, upright_view


def main():
    parts = build()
    selections = {
        "assembly-rail.svg": [
            "rotary-stage", "rotating-adjustment-rail",
            "rotating-locked-carrier",
        ],
        "assembly-xy.svg": [
            "rotating-locked-carrier", "xy-mounting-plate",
            "xy-base", "xy-middle", "xy-carriage", "moving-mast-angle",
        ],
        "assembly-fixed.svg": [
            p["name"] for p in parts
            if p["group"] == "fixed" and p["name"] != "rotary-stage"
        ],
        "assembly-cup.svg": [
            "moving-cup-plate-1", "moving-holder-1", "moving-cup-1",
        ],
    }
    for filename, names in selections.items():
        shapes = [p["shape"] for p in parts if p["name"] in names]
        upright_view(cq.Compound.makeCompound(shapes), filename,
                     (1.3, -1.8, 1.0))
    offsets = {
        "rotating-locked-carrier": 15, "xy-mounting-plate": 35,
        "xy-base": 55, "xy-middle": 55, "xy-carriage": 55,
        "moving-mast-angle": 80,
    }
    shapes = [p["shape"].translate((0, 0, offsets[p["name"]]))
              for p in parts if p["name"] in offsets]
    upright_view(cq.Compound.makeCompound(shapes),
                 "assembly-xy-exploded.svg", (1.3, -1.8, 1.0))
    print("Rendered five fixture assembly views")


if __name__ == "__main__":
    main()
