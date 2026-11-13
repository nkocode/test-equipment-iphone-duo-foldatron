"""Combine purchased fixture, 1010 frame and dimensioned guard layout.

This assembly distinguishes vendor solids, drawing reconstructions and
installation envelopes. It does not certify a physical machine.
"""

import json
from pathlib import Path

import build_structure as structure
import cadquery as cq
from build_fixture import build, mesh, upright_view
from build_structure import box, extrusion, flat_plate

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "hardware"
PARTS = []
SILVER = (0.70, 0.74, 0.77)
BLUE = (0.18, 0.42, 0.52)
DARK = (0.20, 0.24, 0.25)
GLASS = (0.65, 0.83, 0.84)
DOOR_LEFT = -354.0252
DOOR_RIGHT = 340.5
DOOR_BOTTOM = 26.9875
DOOR_TOP = 633.4125
DOOR_WIDTH = DOOR_RIGHT - DOOR_LEFT
AXIS = (12.5, 12.5, 38.1)


def add(name, part, shape, group, color=SILVER,
        evidence="Catalog drawing reconstruction"):
    if not shape.isValid():
        raise ValueError(name)
    item = dict(name=name, part=part, shape=shape, group=group,
                color=color, evidence=evidence)
    PARTS.append(item)
    return shape


def rail(name, length, center, axis="z", group="frame"):
    shape = extrusion(length)
    if axis == "x":
        shape = shape.rotate((0, 0, 0), (0, 1, 0), 90)
    if axis == "y":
        shape = shape.rotate((0, 0, 0), (1, 0, 0), 90)
    return add(name, f"80/20 1010 / {length:.4f} mm supplier cut",
               shape.translate(center), group)


def panel(name, size, center, group="guard"):
    return add(name, "80/20 2643 / rectangular supplier cut",
               box(*size, center), group, GLASS)


def guard():
    for side in (-1, 1):
        panel(f"side-panel-{side}", (3, 723.2, 621.6),
              (side * 368.3, 0, 330.2))
    panel("rear-panel", (723.2, 3, 621.6), (0, 368.3, 330.2))
    panel("roof-panel", (723.2, 723.2, 3), (0, 0, 647.7))
    cx = (DOOR_LEFT + DOOR_RIGHT) / 2
    for x in (DOOR_LEFT + 12.7, DOOR_RIGHT - 12.7):
        rail(f"door-stile-{x:.4f}", DOOR_TOP - DOOR_BOTTOM,
             (x, -368.3, 330.2), group="door")
    for z in (DOOR_BOTTOM + 12.7, DOOR_TOP - 12.7):
        rail(f"door-crossbar-{z:.4f}", DOOR_WIDTH - 50.8,
             (cx, -368.3, z), axis="x", group="door")
    panel("door-panel", (DOOR_WIDTH - 38.8, 3, 567.625),
          (cx, -368.3, 330.2), "door-glass")
    for x, sx in ((DOOR_LEFT + 12.7, 1), (DOOR_RIGHT - 12.7, -1)):
        for z, sz in ((DOOR_BOTTOM + 12.7, 1),
                      (DOOR_TOP - 12.7, -1)):
            p = flat_plate()
            if sx < 0:
                p = p.mirror("YZ")
            if sz < 0:
                p = p.mirror("XZ")
            p = p.rotate((0, 0, 0), (1, 0, 0), 90)
            add(f"door-corner-{x}-{z}", "80/20 4151",
                p.translate((x, -381, z)), "door", BLUE)
    # Drawing-derived hinge geometry: 26.9748 transverse screw pitch,
    # 25.4 longitudinal screw pitch. Knuckle is a visual envelope.
    for z in (150, 510):
        pivot_x = (-355.6 + DOOR_LEFT) / 2
        for label, cx in (("fixed", -368.3),
                          ("door", DOOR_LEFT + 12.7)):
            leaf = box(25.4, 1.9812, 50.8, (cx, -381.9906, z))
            for dz in (-12.7, 12.7):
                hole = cq.Solid.makeCylinder(
                    3.2639, 5, cq.Vector(cx, -385, z + dz),
                    cq.Vector(0, 1, 0))
                leaf = leaf.cut(hole)
            add(f"hinge-{z}-{label}", "80/20 2086 + 3386 hardware",
                leaf, "door" if label == "door" else "guard", DARK)
        knuckle = cq.Solid.makeCylinder(
            4.2418, 50.8, cq.Vector(pivot_x, -385.2418, z - 25.4))
        add(f"hinge-{z}-knuckle", "80/20 2086",
            knuckle, "guard", DARK, "Catalog envelope; hinge pin omitted")
    # Left-hinged pair, mounting lines 40.5 apart; active faces 2.5 apart.
    for label, line_x, direction in (("sensor", 368.3, -1),
                                     ("actuator", 327.8, 1)):
        body = box(26, 13, 36, (line_x + direction * 6, -387.5, 330.2))
        for dz in (-11, 11):
            hole = cq.Solid.makeCylinder(
                2.25, 15, cq.Vector(line_x, -395, 330.2 + dz),
                cq.Vector(0, 1, 0))
            body = body.cut(hole)
        part = "BNS 260-02Z-L / 101184385" if label == "sensor" else (
            "BPS 260-1 / 101184395")
        add(f"guard-{label}", part, body,
            "guard" if label == "sensor" else "door", DARK)
    # Handle mounting holes are 75.006 mm apart along the door stile.
    x = DOOR_RIGHT - 12.7
    grip = box(21.006, 12, 112, (x, -410.99, 440))
    feet = [box(21.006, 29.99, 18, (x, -395.995, 440 + dz))
            for dz in (-37.503, 37.503)]
    add("door-handle", "80/20 2062 + 2 x 3491", grip.fuse(*feet),
        "door", DARK, "Catalog envelope; mounting pitch retained")


def cabinet():
    # Rails sit just in front of rear posts. Their top slots meet 4119
    # brackets on the front slots of the posts without drilling any ends.
    # Rails can be shifted vertically to the supplied enclosure tabs.
    for z in (370, 624):
        rail(f"cabinet-support-{z}", 762, (0, 342.9, z), "x")
    outer = box(361, 165, 254, (0, 247.7, 497))
    cavity = box(346, 152, 239, (0, 240.2, 497))
    shell = outer.cut(cavity)
    add("control-enclosure-base", "Altech 127-912 PC3625-16-m",
        shell, "cabinet", (0.65, 0.67, 0.64),
        "Catalog envelope; knockouts and mounting tabs not yet modeled")
    add("control-enclosure-cover", "Altech 127-912 supplied cover",
        box(361, 4, 254, (0, 163.2, 497)), "cabinet-cover",
        (0.65, 0.67, 0.64), "Installation envelope")
    # Layout top/bottom clearances are explicit. Internal rail elevations
    # will be finalized against the factory boss positions, not drilled.
    modules = [
        ("safety-controller", "Banner SC10-2roe", 45, 115, 100, -130),
        ("digital-io", "Waveshare 26244", 72, 121, 34, -61.5),
        ("thermocouple-io", "ICP DAS M-7018R", 76, 120, 42, 22.5),
    ]
    for name, part, width, height, depth, x in modules:
        add(name, part, box(width, depth, height,
                           (x, 305 - depth / 2, 528)), "electrical",
            BLUE if name == "safety-controller" else DARK,
            "Manufacturer overall envelope; terminals not represented")


def main():
    PARTS.clear()
    structure.main()
    for p in structure.STRUCTURE_PARTS:
        if p["name"] != "purchased-rotary-stage":
            item = p.copy()
            if item["group"] == "plates":
                item["part"] = "80/20 4151"
            elif item["name"] == "purchased-breadboard":
                item["part"] = "Thorlabs MB6060/M"
            elif item["group"] == "frame":
                item["part"] = "80/20 1010 / supplier cut"
            PARTS.append(item)
    for item in build():
        p = item.copy()
        p["shape"] = p["shape"].translate(AXIS)
        PARTS.append(p)
    guard()
    cabinet()
    all_shapes = [p["shape"] for p in PARTS]
    cq.exporters.export(cq.Compound.makeCompound(all_shapes),
                        str(DATA / "cad/bench-development.step"))
    visible = [p["shape"] for p in PARTS if p["group"] not in
               ("guard", "door-glass", "cabinet-cover")]
    upright_view(cq.Compound.makeCompound(visible), "bench-iso.svg",
                 (1.3, -1.8, 1.0))
    upright_view(cq.Compound.makeCompound(all_shapes), "bench-front.svg",
                 (0, -1, 0))
    guard_shapes = [p["shape"] for p in PARTS if p["group"] in
                    ("door", "door-glass", "guard")]
    upright_view(cq.Compound.makeCompound(guard_shapes), "guard-front.svg",
                 (0, -1, 0))
    rows = []
    for p in PARTS:
        row = {k: v for k, v in p.items() if k != "shape"}
        angular = 0.7 if p["name"] == "purchased-breadboard" else 0.2
        row.update(mesh(p["shape"], angular_tolerance=angular))
        rows.append(row)
    (DATA / "bench-model.json").write_text(json.dumps({
        "units": "mm", "rotation_origin": AXIS,
        "door_pivot": [(-355.6 + DOOR_LEFT) / 2, -385.2418, 0],
        "status": "Development assembly: hardware/hose routing incomplete",
        "parts": rows,
    }, separators=(",", ":")) + "\n")
    print(f"Exported {len(PARTS)} bench components", flush=True)


if __name__ == "__main__":
    main()
