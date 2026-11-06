"""Build the Rev B development assembly using CadQuery / OpenCascade.

All coordinates are millimetres. This is a development design, not a claim
of physical validation. Features and procurement evidence are separate.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/rev-b"
CAD = OUT / "cad"
VIEWS = OUT / "views"
SILVER = (0.70, 0.75, 0.79)
BLUE = (0.12, 0.30, 0.43)
BLACK = (0.16, 0.18, 0.20)
GOLD = (0.75, 0.56, 0.22)
PARTS = {}
INSTANCES = []


def box(x, y, z, center=(0, 0, 0)):
    """Return a centered solid."""
    return cq.Workplane("XY").box(x, y, z).translate(center).val()


def cylinder(radius, length, origin=(0, 0, 0), axis=(0, 0, 1)):
    return cq.Solid.makeCylinder(
        radius, length, cq.Vector(*origin), cq.Vector(*axis)
    )


def bore(shape, radius, length, origin, axis=(0, 0, 1)):
    return shape.cut(cylinder(radius, length, origin, axis))


def register(pid, title, shape, material, features, notes, status="REVIEW"):
    PARTS[pid] = {
        "id": pid,
        "title": title,
        "shape": shape,
        "material": material,
        "features": features,
        "notes": notes,
        "status": status,
    }
    return shape


def plate(
    pid,
    title,
    width,
    height,
    thick,
    holes=(),
    slots=(),
    material="6061-T6 aluminum",
    notes=(),
    status="REVIEW",
):
    """Flat part: XY centered datum, bottom Z=0; holes along +Z."""
    shape = box(width, height, thick, (0, 0, thick / 2))
    features = []
    for i, (x, y, diameter, label) in enumerate(holes, 1):
        shape = bore(shape, diameter / 2, thick + 2, (x, y, -1))
        features.append(
            {
                "tag": f"H{i}",
                "x": x,
                "y": y,
                "callout": label,
                "diameter": diameter,
            }
        )
    for i, (x, y, length, width_s, angle, label) in enumerate(slots, 1):
        cut = (
            cq.Workplane("XY")
            .center(x, y)
            .slot2D(length, width_s, angle)
            .extrude(thick + 2)
            .translate((0, 0, -1))
            .val()
        )
        shape = shape.cut(cut)
        features.append(
            {
                "tag": f"S{i}",
                "x": x,
                "y": y,
                "callout": label,
                "diameter": width_s,
            }
        )
    return register(
        pid,
        title,
        shape,
        material,
        features,
        [
            f"Blank {width} x {height} x {thick}.",
            "Datum: XY center; Z=0 bottom. All holes THRU unless "
            "a thread or depth is stated.",
            *notes,
        ],
        status,
    )


def add(
    name,
    pid,
    shape=None,
    pos=(0, 0, 0),
    rotation=None,
    group="fixture",
    color=BLUE,
    moving=False,
    opacity=1.0,
):
    if shape is None:
        shape = PARTS[pid]["shape"]
    if rotation:
        shape = shape.rotate((0, 0, 0), rotation[0], rotation[1])
    shape = shape.translate(pos)
    INSTANCES.append(
        {
            "name": name,
            "part": pid,
            "shape": shape,
            "group": group,
            "color": color,
            "moving": moving,
            "opacity": opacity,
        }
    )
    return shape


def extrusion(length):
    """Interface model: actual envelope; slot relief is illustrative only."""
    shape = box(25.4, 25.4, length)
    # Deliberately do not manufacture or mass-estimate from this section.
    for angle in (0, 90, 180, 270):
        slot = box(6.5, 4, length + 2, (0, 11.5, 0))
        shape = shape.cut(slot.rotate((0, 0, 0), (0, 0, 1), angle))
    return shape


def bracket():
    """80/20 4119 mounting geometry, small edge radii omitted."""
    t = 4.7752
    shape = box(25.4, 22.225, t, (12.7, 0, t / 2))
    shape = shape.fuse(box(t, 22.225, 25.4, (t / 2, 0, 12.7)))
    shape = bore(shape, 3.5687, 8, (12.7, 0, -1))
    return bore(shape, 3.5687, 8, (-1, 0, 12.7), (1, 0, 0))


def build_frame():
    for z, tier in ((-20.7, "lower"), (512.7, "upper")):
        for y in (-266.7, 266.7):
            add(
                f"{tier}_x_{y}",
                "V01",
                extrusion(660.4),
                (0, y, z),
                ((0, 1, 0), 90),
                "frame",
                SILVER,
            )
        for x in (-317.5, 317.5):
            add(
                f"{tier}_y_{x}",
                "V02",
                extrusion(508),
                (x, 0, z),
                ((1, 0, 0), 90),
                "frame",
                SILVER,
            )
    for x in (-317.5, 317.5):
        for y in (-266.7, 266.7):
            add(
                f"post_{x}_{y}",
                "V02",
                extrusion(508),
                (x, y, 246),
                group="frame",
                color=SILVER,
            )
    for y in (-150, 150):
        add(
            f"crossmember_{y}",
            "V03",
            extrusion(609.6),
            (0, y, -20.7),
            ((0, 1, 0), 90),
            "frame",
            SILVER,
        )
    joint = bracket()
    for z, top in ((-8, False), (500, True)):
        for sx in (-1, 1):
            for sy in (-1, 1):
                a = joint.mirror("YZ") if sx == 1 else joint
                b = joint.rotate((0, 0, 0), (0, 0, 1), 90)
                if sy == 1:
                    b = b.mirror("XZ")
                if top:
                    a, b = a.mirror("XY"), b.mirror("XY")
                add(
                    f"post_joint_x_{sx}_{sy}_{z}",
                    "V04",
                    a,
                    (sx * 304.8, sy * 266.7, z),
                    group="frame",
                    color=SILVER,
                )
                add(
                    f"post_joint_y_{sx}_{sy}_{z}",
                    "V04",
                    b,
                    (sx * 317.5, sy * 254, z),
                    group="frame",
                    color=SILVER,
                )
    horizontal = joint.rotate((0, 0, 0), (1, 0, 0), -90)
    for z in (-20.7, 512.7):
        for sx in (-1, 1):
            for sy in (-1, 1):
                a = horizontal
                if sx == 1:
                    a = a.mirror("YZ")
                if sy == 1:
                    a = a.mirror("XZ")
                add(
                    f"rail_corner_{sx}_{sy}_{z}",
                    "V04",
                    a,
                    (sx * 304.8, sy * 254, z),
                    group="frame",
                    color=SILVER,
                )
    for sx in (-1, 1):
        for sy in (-1, 1):
            a = horizontal
            if sx == 1:
                a = a.mirror("YZ")
            if sy == 1:
                a = a.mirror("XZ")
            add(
                f"cross_joint_{sx}_{sy}",
                "V04",
                a,
                (sx * 304.8, sy * 137.3, -20.7),
                group="frame",
                color=SILVER,
            )
    return joint


def build_custom():
    base_holes = [
        (x, y, 6.8, "D6.8 THRU; 1/4-20 frame bolt")
        for x in (-200, 200)
        for y in (-150, 150)
    ]
    base_holes += [
        (x, y, 5, "M6 x 1 THRU") for x in (-40, 40) for y in (-159, 159)
    ]
    base_holes += [
        (x, y, 4.2, "M5 x 0.8 THRU") for x in (-95, -35) for y in (-45, 45)
    ]
    base_holes += [
        (x, y, 4.2, "M5 x 0.8 THRU") for x in (-45, 45) for y in (-210, -180)
    ]
    base_holes += [
        (x, -167, 5.5, "D5.5 THRU; M5 x 16 into stop post")
        for x in (-67.5, 67.5)
    ]
    base_holes += [
        (x, y, 4.2, "M5 x 0.8 THRU; endpoint stand")
        for x in (-67.5, 67.5)
        for y in (187, 217)
    ]
    plate(
        "B101",
        "Fixture base",
        500,
        460,
        8,
        base_holes,
        notes=[
            "Top is assembly datum A (global Z=0).",
            "Mount at global Z=-8. Flatness 0.20 over plate.",
            "Thread depths are limited to 8 mm; do not bottom bolts.",
        ],
        status="PROTOTYPE",
    )
    for x in (-200, 200):
        for y in (-150, 150):
            PARTS["B101"]["shape"] = bore(
                PARTS["B101"]["shape"], 10, 4, (x, y, 4)
            )
    PARTS["B101"]["notes"].append(
        "Four frame mounting holes: counterbore D20 x 4 deep from "
        "top for 3393 fasteners and 1 mm washers."
    )
    tower = plate(
        "B102",
        "Bearing tower",
        100,
        160,
        8,
        [
            (0, 50, 8.2, "D8.2 THRU; bearing axis"),
            *[
                (x, y, 4.2, "M5 x 0.8 THRU")
                for x in (-30, 30)
                for y in (-65, -45)
            ],
            *[
                (x, y, 2.5, "M3 x 0.5 THRU; retainer")
                for x in (-15, 15)
                for y in (35, 65)
            ],
        ],
        notes=[
            "Counterbore D19 H7 (+0.021/0) from Z=8 face, "
            "depth 6.05 +0.05/0. Ra 1.6 seat.",
            "Bearing axis true position D0.05 to bottom "
            "and side datums; paired tower axes coaxial "
            "within D0.05 after assembly.",
        ],
    )
    tower = bore(tower, 9.5, 6.05, (0, 50, 1.95))
    PARTS["B102"]["shape"] = tower
    plate(
        "B103",
        "Tower sole plate",
        100,
        50,
        10,
        [(x, 10, 6.6, "D6.6 THRU; M6 x 16 + washer") for x in (-40, 40)]
        + [(x, 0, 4.2, "M5 x 0.8 THRU; angle foot") for x in (-30, 30)],
        status="PROTOTYPE",
    )
    for x in (-40, 40):
        PARTS["B103"]["shape"] = bore(
            PARTS["B103"]["shape"], 6.5, 2, (x, 10, 8)
        )
    PARTS["B103"]["notes"].append(
        "Two M6 holes: counterbore D13 x 2 deep from top. M6 x 16 "
        "+ 1 mm washer gives 7 mm engagement into base."
    )
    angle = box(100, 40, 6, (0, 20, 3)).fuse(box(100, 6, 50, (0, 3, 25)))
    for x in (-30, 30):
        angle = bore(angle, 2.75, 8, (x, 25, -1))
        for z in (15, 35):
            angle = bore(angle, 2.75, 8, (x, -1, z), (0, 1, 0))
    register(
        "B104",
        "Tower angle",
        angle,
        "6061-T6 aluminum",
        [],
        [
            "Machine from 100 x 40 x 50 stock; 6 mm legs.",
            "Base holes: X +/-30, Y25, D5.5 THRU along Z.",
            "Upright holes: X +/-30, Z15 and 35, D5.5 along Y.",
            "Origin at upright outside / base underside intersection.",
            "Inside relief R2 max; outside angle 90 +/-0.05 deg.",
        ],
    )
    plate(
        "B105",
        "Bearing retaining plate",
        40,
        40,
        2,
        [(0, 0, 17, "D17 THRU; retain OUTER race only")]
        + [
            (x, y, 3.4, "D3.4 THRU; M3 x 8")
            for x in (-15, 15)
            for y in (-15, 15)
        ],
        notes=[
            "Do not clamp inner race; check 0.05-0.10 axial "
            "outer-race clearance before tightening."
        ],
    )
    # Arms: two webs, with counterweight slots outside phone envelope.
    outline = [
        (-130, -30),
        (-55, -30),
        (-15, -18),
        (15, -18),
        (110, -56.6),
        (150, -56.6),
        (150, -16.6),
        (115, -16.6),
        (15, 20),
        (-30, 20),
        (-130, 10),
    ]
    arm = cq.Workplane("XY").polyline(outline).close().extrude(6).val()
    arm_features = []
    for x, y, d in [
        (0, 0, 6.6),
        (0, 10, 3.4),
        (0, -10, 3.4),
        (10, 0, 3.4),
        (-10, 0, 3.4),
        (130, -44.6, 4.5),
        (130, -28.6, 4.5),
    ]:
        arm = bore(arm, d / 2, 8, (x, y, -1))
        arm_features.append(
            {
                "tag": f"H{len(arm_features) + 1}",
                "x": x,
                "y": y,
                "diameter": d,
                "callout": f"D{d} THRU",
            }
        )
    for x in (-105, -65):
        slot = (
            cq.Workplane("XY")
            .center(x, -5)
            .slot2D(20, 4.5, 0)
            .extrude(8)
            .translate((0, 0, -1))
            .val()
        )
        arm = arm.cut(slot)
        arm_features.append(
            {
                "tag": f"S{len(arm_features) - 6}",
                "x": x,
                "y": -5,
                "diameter": 4.5,
                "callout": "20 x 4.5 slot along X",
            }
        )
    register(
        "B106",
        "Yoke / counterbalance arm",
        arm,
        "6061-T6 aluminum",
        arm_features,
        [
            "6 mm plate. Datum XY=shaft axis; Z=0 outer face.",
            "Profile vertices in profile-vertices.json / native STEP.",
            "D0.05 position for the four hub holes; other holes +/-0.10.",
            "Front and rear arm are identical blanks; install mirrored.",
        ],
    )
    (OUT / "profile-vertices.json").write_text(
        json.dumps({"B106": outline}, indent=2) + "\n"
    )
    cross = box(30, 158, 30)
    # Open pocket from bottom: 6 mm top web, 6 mm end walls.
    cross = cross.cut(box(20, 146, 24, (0, 0, -3)))
    for x in (-6, 6):
        for y in (-45, 45):
            cross = bore(cross, 1.65, 8, (x, y, 8))
    for y, direction in ((-80, 1), (80, -1)):
        for z in (-8, 8):
            cross = bore(cross, 1.65, 7, (0, y, z), (0, direction, 0))
    register(
        "B107",
        "Lightened crossbar",
        cross,
        "6061-T6 aluminum",
        [],
        [
            "Blank 30 X x 158 Y x 30 Z; origin at center.",
            "Pocket 20 X x 146 Y x 24 deep from bottom; R3 corners "
            "permitted. Model has sharp pocket corners.",
            "Top: 4 x M4 x 0.7 THRU at X +/-6, Y +/-45.",
            "Each end: 2 x M4 x 0.7 THRU at X0, Z +/-8.",
            "Use M4 x 10 through 6 mm arms/strips: 4 mm engagement.",
        ],
    )
    rail_holes = [
        (x, 0, 1.6, "M2 x 0.4 THRU; rail")
        for x in (-55, -40, -25, -10, 5, 20, 35)
    ]
    rail_holes += [
        (x, y, 1.6, "M2 x 0.4 THRU; stop")
        for x in (-42.25, 2.25)
        for y in (-8, 8)
    ]
    rail_holes += [(x, 0, 4.5, "D4.5 THRU; M4 x 10") for x in (49, 61)]
    plate(
        "B108",
        "Guide carrier strip",
        140,
        25,
        6,
        rail_holes,
        notes=[
            "Install global X=75, Y=+/-45, Z=118.4.",
            "Rail holes become X20..110; rail start X15.",
            "Guide stops were re-centered to actual block travel.",
        ],
    )
    plate(
        "B109",
        "Floating contact plate blank",
        100,
        135,
        4,
        [
            (x, y, 2.4, "D2.4 THRU; M2 x 6 into MGN7C")
            for x in (-4, 4)
            for y in (-51, -39, 39, 51)
        ],
        notes=[
            "Install center global X55, Y0, bottom Z132.4.",
            "4 mm plate + M2 x 6 gives 2 mm block engagement.",
            "Phone-contact inserts and restraint holes are HOLD "
            "P1 until actual phone is measured.",
        ],
    )
    stop = plate(
        "B110",
        "Guide travel stop",
        6,
        20,
        8,
        [(0, y, 2.4, "D2.4 THRU; M2 x 12") for y in (-8, 8)],
        material="POM-C acetal",
        notes=[
            "Underside channel 6 long x 7.2 wide x 4.9 "
            "deep, centered Y=0, clears rail.",
            "Bond 2 mm silicone pad to inward X face.",
            "Stop body centers X=32.75 and 77.25 on each "
            "rail; nominal float +/-6 about X55.",
        ],
    )
    PARTS["B110"]["shape"] = stop.cut(box(8, 7.2, 4.9, (0, 0, 2.45)))
    plate(
        "B111",
        "Counterweight",
        40,
        40,
        25,
        [(x, 0, 3.3, "M4 x 0.7 THRU") for x in (-10, 10)],
        material="Low-carbon steel; zinc plate after machining",
        notes=[
            "Nominal 0.31 kg each; weigh finished part.",
            "Initial center X=-85, Z=165; adjust on B120.",
            "Use M4 x 16 + 1 mm washer through 4 mm B120: "
            "11 mm thread engagement.",
            "Balance both X and Z moments; verify Q04 sweep.",
        ],
    )
    # Hubs have radial set screws and a documented flat, not imagined clamps.
    hub = cylinder(8, 10).fuse(cylinder(15, 6, (0, 0, 10)))
    hub = bore(hub, 3, 18, (0, 0, -1))
    for x, y in ((10, 0), (-10, 0), (0, 10), (0, -10)):
        hub = bore(hub, 1.25, 7, (x, y, 9.5))
    for axis in ((1, 0, 0), (0, 1, 0)):
        hub = bore(hub, 1.25, 7, (0, 0, 5), axis)
    register(
        "B112",
        "Output flange hub",
        hub,
        "6061-T6 aluminum",
        [],
        [
            "Origin: barrel end center; shaft axis Z.",
            "Barrel D16 x 10; flange D30 x 6; bore D6 H7.",
            "Flange 4 x M3 x 0.5 THRU on PCD20, at 0/90/180/270 deg.",
            "Two radial M3 x 0.5 THRU at Z5; axes +X, +Y.",
            "M3 x 4 flat-point screws contact shaft flats; proof "
            "torque 0.75 N m off-phone. Do not use adhesive as retention.",
        ],
    )
    for pid, length in (("B113", 108), ("B114", 84)):
        shaft = cylinder(3, length)
        register(
            pid,
            "Ground output shaft",
            shaft,
            "Ground stainless steel, D6 g6",
            [],
            [
                f"Cut length {length} +/-0.2; chamfer 0.2 x 45 deg.",
                "Shaft D6 g6: 5.988..5.996 mm; no plating on fits.",
                "Machine two perpendicular flats, 0.30 deep, 8 long, "
                "at hub set-screw station shown in axial stack.",
                "Model omits clocked flats until clutch datum "
                "is confirmed (HOLD P2).",
            ],
        )
    for pid, length in (("B115", 2), ("B116", 4)):
        spacer = cylinder(4, length).cut(cylinder(3.1, length))
        register(
            pid,
            "Inner-race spacer",
            spacer,
            "303 stainless",
            [],
            [
                f"D8 OD x D6.2 ID x {length} +/-0.02 long.",
                "Faces parallel 0.02; no burrs. Contact inner race only.",
            ],
        )
    plate(
        "B117",
        "Fixed tray",
        100,
        135,
        6,
        [
            (x, y, 4.5, "D4.5 THRU; M4 x 12 into posts")
            for x in (-30, 30)
            for y in (-45, 45)
        ],
        notes=[
            "Install X=-65, Y0, Z130.4. 1 mm pad on top.",
            "Actual phone restraint/insert mounting: HOLD P1.",
        ],
    )
    post = cylinder(6, 130.4)
    post = bore(post, 1.65, 12, (0, 0, 119))
    post = bore(post, 2.1, 12, (0, 0, -0.1))
    register(
        "B118",
        "Fixed tray standoff",
        post,
        "6061-T6 aluminum",
        [],
        [
            "D12 x 130.4 +/-0.05; top M4 x 0.7, 10 deep.",
            "Bottom M5 x 0.8, 10 deep; bottom fasteners from "
            "below base require base holes D5.5, not M5 tapped.",
            "Corrected base-hole callout is applied automatically.",
        ],
    )
    # Correct base tray attachments to clearance, not tapped-to-tapped.
    base = PARTS["B101"]["shape"]
    for feature in PARTS["B101"]["features"]:
        if feature["x"] in (-95, -35) and feature["y"] in (-45, 45):
            feature["diameter"] = 5.5
            feature["callout"] = "D5.5 THRU; M5 x 16 from underside"
            base = bore(base, 2.75, 10, (feature["x"], feature["y"], -1))
    PARTS["B101"]["shape"] = base
    plate(
        "B119",
        "Motor mounting side cheek",
        65,
        143.25,
        6,
        [
            (x, y, 2.9, "D2.9 THRU; M2.5 x 8, 2 mm engagement")
            for x in (-6, 6)
            for y in (56.375, 32.375)
        ]
        + [
            (x, -61.625, 4.5, "D4.5 THRU; M4 x 16 into B121")
            for x in (-20, 20)
        ],
        notes=[
            "Side holes follow ROBOTIS drawing: 12 x 24 pattern; "
            "top row 4 below output axis.",
            "Cheek bottom global Z=8; output axis global Z=140.",
            "Motor depth datum is 17 behind horn face; side holes "
            "are 11 and 23 behind front body face.",
            "Two cheeks fit motor 28.5 mm width; shim at body "
            "if needed without exceeding 3 mm screw engagement.",
        ],
    )
    plate(
        "B120",
        "Counterweight adjustment plate",
        60,
        60,
        4,
        [
            (x, -15, 4.5, "D4.5 THRU; M4 x 20 + washer + locknut")
            for x in (-20, 20)
        ],
        [
            (x, 15, 20, 4.5, 90, "20 x 4.5 vertical slot; M4 x 16")
            for x in (-10, 10)
        ],
        notes=[
            "Install center X=-85, Z=150, on arm outer face.",
            "Arm slots provide X travel +/-7.75; upper slots "
            "provide Z travel +/-7.75. Adjust both weights equally.",
            "Do not enlarge slots if actual balance lies outside "
            "range; revise weight mass and recheck swept clearance.",
        ],
    )
    foot = box(100, 110, 8, (0, 0, 4))
    for x in (-26.25, 26.25):
        foot = foot.fuse(box(12, 65, 20, (x, -21, 18)))
        for y in (-41, -1):
            foot = bore(foot, 1.65, 14, (x - 7, y, 18), (1, 0, 0))
    for x in (-45, 45):
        for y in (10, 40):
            cut = (
                cq.Workplane("XY")
                .center(x, y)
                .slot2D(25, 5.5, 90)
                .extrude(10)
                .translate((0, 0, -1))
                .val()
            )
            foot = foot.cut(cut)
    register(
        "B121",
        "Motor adjustable pedestal",
        foot,
        "6061-T6 aluminum",
        [],
        [
            "Origin XY center of 100 x 110 sole; sole Z0..8.",
            "Two integral lugs 12 X x 65 Y x 20 high above sole; "
            "centers X+/-26.25, Y=-21, global local Z18.",
            "Lug bores 4 x M4 THRU along X at Y=-41/-1, Z18.",
            "4 slots 25 x 5.5 along Y, centers X+/-45, Y10/40.",
            "Install global Y=-220; M5 x 16 + 1 mm washer through "
            "8 mm sole gives 7 mm engagement in 8 mm base.",
            "Usable axial adjustment -3 to +9.75 (guard limits "
            "forward travel); confirm clutch insertion "
            "before tightening. Root relief R2 allowed.",
        ],
    )
    adapter = cylinder(13, 6).fuse(cylinder(3, 12, (0, 0, 6)))
    adapter = bore(adapter, 2.75, 3, (0, 0, 0))
    for x, y in ((8, 0), (-8, 0), (0, 8), (0, -8)):
        adapter = bore(adapter, 1.2, 7, (x, y, -0.5))
    register(
        "B122",
        "Integral motor input flange / shaft",
        adapter,
        "303 stainless steel",
        [],
        [
            "D26 flange x 6; integral D6 g6 shaft x 12 above flange.",
            "4 x D2.4 THRU, PCD16 at 0/90/180/270 degrees.",
            "Underside central relief D5.5 x 3 deep; check central "
            "horn bolt clears relief by >=0.5 before installation.",
            "M2 x 8 + 0.2 mm shim washer gives 1.8 mm engagement "
            "in horn; maximum allowed by ROBOTIS is 2.0 mm.",
            "Do not loosen the central horn retaining bolt.",
            "Clutch insertion length and set-screw flat: HOLD P2.",
        ],
    )
    cam = cylinder(8, 10).fuse(cylinder(15, 6, (0, 0, 10)))
    cam = cam.fuse(box(75, 10, 6, (37.5, 0, 13)))
    cam = bore(cam, 3, 18, (0, 0, -1))
    for axis in ((1, 0, 0), (0, 1, 0)):
        cam = bore(cam, 1.25, 9, (0, 0, 5), axis)
    register(
        "B123",
        "Output angular-stop cam",
        cam,
        "6061-T6 aluminum",
        [],
        [
            "Barrel D16 x 10; flange D30 x 6 at Z10..16; bore D6 H7.",
            "Integral radial tab X0..75, Y+/-5, Z10..16.",
            "Two radial M3 x 0.5 at Z5, directions +X and +Y.",
            "Two M3 x 4 flat-point screws on shaft flats; "
            "proof at 0.75 N m off-phone.",
            "Installed tab points +X at fixture zero degrees. "
            "Cam origin global (0,-180,140), axis along +Y.",
        ],
    )
    stop_post = cylinder(8, 120)
    stop_post = bore(stop_post, 2.5, 25, (0, 0, 95))
    stop_post = bore(stop_post, 2.1, 10, (0, 0, 0))
    register(
        "B124",
        "Angular-stop post",
        stop_post,
        "303 stainless steel",
        [],
        [
            "D16 x 120; top M6 x 1, 25 deep; bottom M5 x 0.8, 10 deep.",
            "Install X+/-67.5, Y=-167 on base. M5 x 16 from underside.",
            "Top M6 x 25 cap screw + M6 jam nut; 1 mm silicone pad "
            "bonded to cap head. Model contact height 135.00 mm "
            "for 0/180 degree backup stops; normal motion 5..175.",
            "Lock nut after setting; minimum screw engagement 10 mm.",
            "Mechanical stops are overload backups, not cycle targets.",
        ],
    )
    build_endpoint_parts()
    build_guard_switch_parts()
    # Screw-removable front access panel avoids an unverified hinge pattern.
    for pid, name, w, h in (
        ("B201", "Side guard blank", 558.8, 558.8),
        ("B202", "Rear guard blank", 660.4, 558.8),
        ("B203", "Roof guard blank", 660.4, 558.8),
        ("B204", "Front access panel", 654.4, 552.8),
    ):
        if pid == "B203":
            panel_holes = [
                (x, y, 8, "D8 THRU; floating panel fastener")
                for x in (-317.5, 317.5)
                for y in (-200, 200)
            ]
        else:
            xs = (-266.7, 266.7) if pid == "B201" else (-317.5, 317.5)
            panel_holes = [
                (x, y, 8, "D8 THRU; floating panel fastener")
                for x in xs
                for y in (-266.7, 0, 266.7)
            ]
            if pid == "B204":
                panel_holes += [
                    (x, 98, 7, "D7 THRU; key sleeve B130")
                    for x in (-282.5, -267.5)
                ]
        plate(
            pid,
            name,
            w,
            h,
            4,
            panel_holes,
            material="Clear polycarbonate",
            notes=[
                "Saw / router blank; deburr R0.5 edges.",
                "3393 1/4-20 x 1/2 screws + 18 OD x 6.6 ID x "
                "1 mm washers; 2 N m initial assembly torque.",
                "B128-B130 define interlock/key mounts. Physical "
                "insertion/access test remains P3. No hinge fitted.",
                "Do not substitute acrylic for polycarbonate.",
            ],
        )


def build_endpoint_parts():
    """Output-shaft cam and independently adjustable endpoint supports."""
    PARTS["B114"]["notes"].append(
        "Additional sensing-cam flats: two perpendicular0.30-deep "
        "x8-long flats centered at localZ71 (globalY156). Clock "
        "to the assembled cam; do not cut into a bearing seat."
    )
    points = []
    for degrees in range(-180, 180):
        radius = 25.0
        if abs(degrees) < 12:
            radius += 0.6 * (1 + math.cos(math.pi * degrees / 12))
        angle = math.radians(degrees)
        points.append((radius * math.cos(angle), radius * math.sin(angle)))
    cam = cq.Workplane("XY").polyline(points).close().extrude(6)
    cam = cam.translate((0, 0, 10)).val().fuse(cylinder(8, 10))
    cam = bore(cam, 3, 18, (0, 0, -1))
    for axis in ((1, 0, 0), (0, 1, 0)):
        cam = bore(cam, 1.25, 9, (0, 0, 5), axis)
    register(
        "B125",
        "Endpoint sensing cam",
        cam,
        "POM-C acetal",
        [],
        [
            "Barrel D16 x10; disc6 thick at Z10..16; bore D6 H7.",
            "Polar profile: R25 outside +/-12deg about +X. Within "
            "that sector R=25+0.6*(1+cos(pi*angle/12deg)). Max R26.2.",
            "STEP samples profile each1deg; finish follower surface "
            "Ra0.8, remove facets/burrs without changing radius >0.03.",
            "Two radial M3 x0.5 at Z5; M3x4 flat-point screws. "
            "Light initial torque0.10Nm; no holding/safety credit.",
            "Origin global(0,151,140), axis+Y. Peak points+X at open. "
            "Disc global Y161..167, shaft engagement16mm.",
            "Adjust each switch separately. At peak, measure actual "
            "overtravel0.35..0.45mm after electrical make; never exceed "
            "the purchased switch's allowed travel. Physical test P3.",
        ],
    )
    plate(
        "B126",
        "Endpoint stand sole",
        160,
        50,
        12,
        [
            (x, y, 5.5, "D5.5 THRU; M5 x20 +1mm washer")
            for x in (-67.5, 67.5)
            for y in (-15, 15)
        ]
        + [
            (x, y, 3.3, "M4 x0.7 THRU; upright")
            for x in (-43.8, 43.8)
            for y in (-15, 0)
        ],
        notes=[
            "Install center(0,202), bottomZ0. Four M5 base screws.",
            "Upright feet startY167; foot holesY187/202.",
            "Front edgeY177 clears rear tower sole by3mm. Upright "
            "foot bottomZ12 clears tower sole topZ10 by2mm.",
        ],
    )
    upright = box(30, 45, 6, (0, 22.5, 3)).fuse(box(30, 6, 155, (0, 3, 77.5)))
    for y in (20, 35):
        upright = bore(upright, 2.25, 8, (0, y, -1))
    features = []
    for x in (-11, 11):
        for z in (118.35, 124.85, 131.15, 137.65):
            cutter = (
                cq.Workplane("XZ")
                .center(x, z)
                .slot2D(6, 2.4, 0)
                .extrude(8)
                .translate((0, 7, 0))
                .val()
            )
            upright = upright.cut(cutter)
            features.append(
                {
                    "tag": f"S{len(features) + 1}",
                    "x": x,
                    "y": z,
                    "diameter": 2.4,
                    "callout": "6x2.4 slot alongX; Y column=Z",
                }
            )
    register(
        "B127",
        "Endpoint switch upright",
        upright,
        "6061-T6 aluminum",
        features,
        [
            "Machine angle: width30; footY0..45,t6; uprightY0..6,H155.",
            "Local origin: Xmid-width,Yfront,Zfoot bottom. "
            "Slot chart uses X,Z coordinates, not top-view X,Y.",
            "Foot holes D4.5 THRU at X0,Y20/35. Use M4x12 with1mm "
            "washers:5mm engagement in B126.",
            "Install X+/-43.8,Y167,Z12. FaceY167 supports switches.",
            "Right switch: inward lower pair, global X32.8, "
            "Z130.35/136.85. Left: inward upper pair,X-32.8, "
            "Z143.15/149.65. Other slots unused.",
            "M2x16 through switch and upright; plain washer at head, "
            "spring washer and hex nut behind upright; torque0.08..0.10Nm.",
            "Slots give+/-1.8mm radial setup. Lock after continuity "
            "and overtravel measurements; never clamp across lever.",
        ],
    )


def build_guard_switch_parts():
    """Front-post switch mount and reinforced removable-panel key mount."""
    mount = box(50, 6, 110, (0, 3, 55)).fuse(
        box(6, 44.85, 110, (-26.8, -16.425, 55))
    )
    features = []
    for x, z in ((-11, 61.5), (11, 14.5)):
        mount = bore(mount, 2.25, 8, (x, -1, z), (0, 1, 0))
        features.append(
            {
                "tag": f"H{len(features) + 1}",
                "x": x,
                "y": z,
                "diameter": 4.5,
                "callout": "D4.5 throughY; chart Y=localZ",
            }
        )
    for z in (35, 85):
        mount = bore(mount, 3.4, 8, (-31, -28.55, z), (1, 0, 0))
        mount = bore(mount, 6.5, 1.225, (-23.8, -28.55, z), (-1, 0, 0))
    register(
        "B128",
        "Guard-switch post bracket",
        mount,
        "6061-T6 aluminum",
        features,
        [
            "Local X=plate midwidth,Y=switch seating face,Z=bottom. "
            "Back plate X+/-25,Y0..6,Z0..110.",
            "Side leg X-29.8..-23.8,Y-38.85..6,Z0..110. "
            "Inside root radius<=3 allowed; keep switch seating face flat.",
            "Side holes alongX: D6.8 at Y-28.55,Z35/85; "
            "counterbore D13x1.225 fromX=-23.8 face. Effective "
            "clamp thickness4.775 matches4119/3393 stack.",
            "Install origin(-275,-238.15,255). Side leg seats on "
            "left-front post inner faceX=-304.8. Two3393 sets.",
            "Switch diagonal M4 pitch22x47; body torque0.5..0.7Nm. "
            "Do not use the optional locating-stud holes as bolt holes.",
            "Cut two M4x50 blanks to measured device/bracket/washer/"
            "nut stack +two full threads; deburr and record final length.",
        ],
    )
    plate(
        "B129",
        "Guard-key backing plate",
        50,
        25,
        6,
        [(x, 0, 3.3, "M4 x0.7 THRU; key15mm pitch") for x in (-7.5, 7.5)],
        notes=[
            "Outside front panel; centerX=-275,Z344; "
            "inner faceY=-283.4, outer faceY=-289.4.",
            "Two M4x12 screws through key/washer/B130 sleeves, "
            "nominal4.9mm engagement. Key mounting torque2.4..2.8Nm.",
            "B130 sleeves carry clamp load; do not torque directly "
            "through unsupported polycarbonate. No adhesive retention.",
        ],
    )
    sleeve = cylinder(3, 4.1).cut(cylinder(2.25, 4.1))
    register(
        "B130",
        "Guard-key compression sleeve",
        sleeve,
        "303 stainless",
        [],
        [
            "OD6, ID4.5, nominalL4.1. Finish actual length to measured "
            "panel thickness +0.10/+0.15; record finished length.",
            "Faces parallel0.02, deburr0.1. Two sleeves in D7 panel "
            "holes. Sleeve ends bear on key and B129, not plastic.",
            "Changing sleeve length changes key insertion datum; "
            "verify40..42.5mm per S23 after clamping.",
        ],
    )


def build_fixture():
    add("base", "B101", pos=(0, 0, -8), color=SILVER)
    for sign in (-1, 1):
        side = "front" if sign == -1 else "rear"
        # Local XY plate becomes global XZ; local +Z points inward.
        angle = 90 if sign == 1 else -90
        # Front local Y must also point up; rotate rear about X=90:
        # local Y -> +Z, +Z -> -Y. Front is mirrored separately.
        tower = PARTS["B102"]["shape"].rotate((0, 0, 0), (1, 0, 0), 90)
        if sign == -1:
            tower = tower.mirror("XZ")
        add(f"tower_{side}", "B102", tower, (0, sign * 124, 90))
        sole = PARTS["B103"]["shape"]
        if sign == -1:
            sole = sole.mirror("XZ")
        add(f"sole_{side}", "B103", sole, pos=(0, sign * 149, 0))
        foot = PARTS["B104"]["shape"]
        if sign == -1:
            foot = foot.mirror("XZ")
        add(f"angle_{side}", "B104", foot, (0, sign * 124, 10))
        add(
            f"retainer_{side}",
            "B105",
            pos=(0, sign * 116, 140),
            rotation=((1, 0, 0), angle),
            color=SILVER,
        )
        bearing = cylinder(9.5, 6).cut(cylinder(3, 6))
        add(
            f"bearing_{side}",
            "V09",
            bearing,
            (0, sign * 122.05, 140),
            ((1, 0, 0), -90 * -sign),
            color=SILVER,
        )
        arm = PARTS["B106"]["shape"].rotate((0, 0, 0), (1, 0, 0), 90)
        if sign == -1:
            arm = arm.mirror("XZ")
        add(f"arm_{side}", "B106", arm, (0, sign * 85, 140), moving=True)
        hub = PARTS["B112"]["shape"]
        add(
            f"hub_{side}",
            "B112",
            hub,
            (0, sign * 101, 140),
            ((1, 0, 0), 90 * sign),
            color=GOLD,
            moving=True,
        )
        # Mirror rather than rotate -90, so local drawing Y remains +Z.
        adjust = PARTS["B120"]["shape"].rotate((0, 0, 0), (1, 0, 0), 90)
        weight = PARTS["B111"]["shape"].rotate((0, 0, 0), (1, 0, 0), 90)
        if sign == 1:
            adjust = adjust.mirror("XZ")
            weight = weight.mirror("XZ")
        add(
            f"weight_adjust_{side}",
            "B120",
            adjust,
            pos=(-85, sign * 85, 150),
            moving=True,
            color=SILVER,
        )
        add(
            f"weight_{side}",
            "B111",
            weight,
            pos=(-85, sign * 89, 165),
            color=BLACK,
            moving=True,
        )
        for label, start, pid in (
            ("inner", 116.05, "B115"),
            ("outer", 122.05, "B116"),
        ):
            direction = 90 * sign if label == "inner" else -90 * sign
            add(
                f"spacer_{side}_{label}",
                pid,
                pos=(0, sign * start, 140),
                rotation=((1, 0, 0), direction),
                color=SILVER,
                moving=True,
            )
        for start in (105.05, 126.05):
            collar = cylinder(8, 9).cut(cylinder(3, 9))
            collar = collar.cut(box(1, 12, 11, (0, 6, 4.5)))
            add(
                f"collar_{side}_{start}",
                "V10",
                collar,
                (0, sign * start, 140),
                ((1, 0, 0), -90 * sign),
                color=BLACK,
                moving=True,
            )
    add(
        "front_shaft",
        "B113",
        pos=(0, -193, 140),
        rotation=((1, 0, 0), -90),
        color=SILVER,
        moving=True,
    )
    add(
        "rear_shaft",
        "B114",
        pos=(0, 85, 140),
        rotation=((1, 0, 0), -90),
        color=SILVER,
        moving=True,
    )
    add("crossbar", "B107", pos=(130, 0, 103.4), moving=True)
    for y in (-45, 45):
        add(f"carrier_{y}", "B108", pos=(75, y, 118.4), moving=True)
        rail = box(100, 7, 4.8)
        for x in (-45, -30, -15, 0, 15, 30, 45):
            rail = bore(rail, 1.2, 6, (x, 0, -3))
            rail = bore(rail, 2.1, 2.3, (x, 0, 0.1))
        add(
            f"rail_{y}", "V11", rail, (65, y, 126.8), color=SILVER, moving=True
        )
        block = box(23.1, 17, 6.2).cut(box(24, 7.1, 3.1, (0, 0, -1.55)))
        for x in (-4, 4):
            for yy in (-6, 6):
                block = bore(block, 0.8, 2.5, (x, yy, 0.6))
        add(
            f"block_{y}",
            "V11",
            block,
            (55, y, 129.3),
            color=BLACK,
            moving=True,
        )
        for x in (32.75, 77.25):
            add(
                f"stop_{x}_{y}",
                "B110",
                pos=(x, y, 124.4),
                moving=True,
                color=BLACK,
            )
    add("float_plate", "B109", pos=(55, 0, 132.4), moving=True, color=SILVER)
    add("fixed_tray", "B117", pos=(-65, 0, 130.4), color=SILVER)
    add(
        "endpoint_cam",
        "B125",
        pos=(0, 151, 140),
        rotation=((1, 0, 0), -90),
        moving=True,
        color=GOLD,
    )
    add("endpoint_sole", "B126", pos=(0, 202, 0))
    for sign in (-1, 1):
        add(f"endpoint_upright_{sign}", "B127", pos=(sign * 43.8, 167, 12))
        z_center = 133.6 if sign == 1 else 146.4
        switch = box(7, 5.8, 12.8, (sign * 31.3, 164.1, z_center))
        for z in (z_center - 3.25, z_center + 3.25):
            switch = bore(switch, 1.0, 8, (sign * 32.8, 160.5, z), (0, 1, 0))
        add(f"endpoint_switch_{sign}", "V31", switch, color=BLACK)
    for x in (-95, -35):
        for y in (-45, 45):
            add(f"fixed_post_{x}_{y}", "B118", pos=(x, y, 0), color=SILVER)
    # Phone is an explicitly unverified fit-check envelope, not an Apple CAD.
    for x in (-40, 40):
        add(
            f"phone_envelope_{x}",
            "DUT",
            box(78, 117.8, 5.2),
            (x, 0, 140),
            color=(0.18, 0.52, 0.55),
            moving=x > 0,
        )
    # Clutch envelope follows catalogue, but bore engagement needs RFQ.
    clutch = cylinder(9.525, 31.75, (0, -215.875, 140), (0, 1, 0))
    clutch = bore(clutch, 3, 34, (0, -217, 140), (0, 1, 0))
    add("clutch_RFQ", "V12", clutch, color=GOLD)
    # Servo body / side-hole datum from manufacturer drawing (11.25 axis).
    servo = box(28.5, 34, 46.5, (0, -241, 128))
    for y in (-247, -235):
        for z in (136, 112):
            servo = bore(servo, 1.025, 30, (-15, y, z), (1, 0, 0))
    add("XM430_interface_model", "V08", servo, color=BLACK)
    horn = cylinder(9.75, 2, (0, -224, 140), (0, 1, 0))
    for i in range(8):
        a = i * math.pi / 4
        horn = bore(
            horn,
            0.8,
            3,
            (8 * math.cos(a), -224.5, 140 + 8 * math.sin(a)),
            (0, 1, 0),
        )
    add("XM430_horn", "V08", horn, color=SILVER)
    for x in (-20.25, 14.25):
        add(
            f"motor_cheek_{x}",
            "B119",
            pos=(x, -241, 79.625),
            rotation=((1, 1, 1), 120),
        )
    add("motor_foot", "B121", pos=(0, -220, 0))
    add(
        "motor_adapter",
        "B122",
        pos=(0, -222, 140),
        rotation=((1, 0, 0), -90),
        color=SILVER,
    )
    add(
        "angular_cam",
        "B123",
        pos=(0, -180, 140),
        rotation=((1, 0, 0), -90),
        color=GOLD,
        moving=True,
    )
    for x in (-67.5, 67.5):
        add(f"angular_stop_{x}", "B124", pos=(x, -167, 0), color=SILVER)
        bolt = cylinder(3, 25).fuse(cylinder(5, 6, (0, 0, 25)))
        add(f"stop_bolt_{x}", "F-M6-25", bolt, (x, -167, 103), color=BLACK)
        add(
            f"stop_pad_{x}",
            "C-SILICONE",
            cylinder(5, 1),
            (x, -167, 134),
            color=BLACK,
        )


def build_guards():
    for x in (-334.2, 330.2):
        add(
            f"side_guard_{x}",
            "B201",
            pos=(x, 0, 246),
            rotation=((0, 1, 0), 90),
            group="guard",
            color=(0.55, 0.77, 0.85),
            opacity=0.12,
        )
    add(
        "rear_guard",
        "B202",
        pos=(0, 283.4, 246),
        rotation=((1, 0, 0), 90),
        group="guard",
        color=(0.55, 0.77, 0.85),
        opacity=0.12,
    )
    add(
        "roof",
        "B203",
        pos=(0, 0, 525.4),
        group="guard",
        color=(0.55, 0.77, 0.85),
        opacity=0.12,
    )
    add(
        "door",
        "B204",
        pos=(0, -279.4, 246),
        rotation=((1, 0, 0), 90),
        group="guard",
        color=(0.55, 0.77, 0.85),
        opacity=0.10,
    )
    add(
        "guard_switch_mount",
        "B128",
        pos=(-275, -238.15, 255),
        group="guard",
        color=BLUE,
    )
    add(
        "guard_key_backing",
        "B129",
        pos=(-275, -283.4, 344),
        rotation=((1, 0, 0), 90),
        group="guard",
        color=SILVER,
    )
    for x in (-282.5, -267.5):
        add(
            f"guard_key_sleeve_{x}",
            "B130",
            pos=(x, -283.4, 344),
            rotation=((1, 0, 0), -90),
            group="guard",
            color=SILVER,
        )
    switch = box(31, 31.5, 55, (-275, -253.9, 289)).fuse(
        box(30.2, 30.6, 41, (-275, -253.45, 337))
    )
    for x, z in ((-286, 316.5), (-264, 269.5)):
        switch = bore(switch, 2.15, 34, (x, -271, z), (0, 1, 0))
    switch = switch.cut(box(14, 28, 3, (-275, -265.4, 350)))
    add("guard_switch_envelope", "V29", switch, group="guard", color=BLACK)
    key = box(30, 2, 10.5, (-275, -278.3, 344)).fuse(
        box(13, 28, 2, (-275, -265.3, 350))
    )
    for x in (-282.5, -267.5):
        key = bore(key, 2.15, 4, (x, -281, 344), (0, 1, 0))
    add("guard_key_envelope", "V29", key, group="guard", color=GOLD)
    cabinet = box(299.33, 239.46, 119.73).cut(
        box(291.33, 231.46, 113.73, (0, 0, 3))
    )
    add(
        "cabinet_envelope",
        "V20",
        cabinet,
        (540, 0, 26.465),
        group="electrical",
        color=(0.72, 0.74, 0.72),
    )


def render(items, path, view="iso", size=(1800, 1300)):
    """Render tessellated CAD surfaces with VTK; no illustrative primitives."""
    import vtk

    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.96, 0.97, 0.98)
    renderer.SetBackground2(1, 1, 1)
    renderer.GradientBackgroundOn()
    for item in items:
        vertices, triangles = item["shape"].tessellate(0.15, 0.15)
        points = vtk.vtkPoints()
        for v in vertices:
            points.InsertNextPoint(v.x, v.y, v.z)
        cells = vtk.vtkCellArray()
        for tri in triangles:
            cells.InsertNextCell(3, tri)
        mesh = vtk.vtkPolyData()
        mesh.SetPoints(points)
        mesh.SetPolys(cells)
        normals = vtk.vtkPolyDataNormals()
        normals.SetInputData(mesh)
        normals.SetFeatureAngle(35)
        normals.Update()
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(normals.GetOutputPort())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        prop = actor.GetProperty()
        prop.SetColor(*item.get("color", SILVER))
        prop.SetOpacity(item.get("opacity", 1))
        prop.SetSpecular(0.30)
        prop.SetSpecularPower(35)
        prop.SetAmbient(0.35)
        prop.SetDiffuse(0.65)
        renderer.AddActor(actor)
        edges = vtk.vtkFeatureEdges()
        edges.SetInputData(mesh)
        edges.SetFeatureAngle(35)
        edges.BoundaryEdgesOn()
        edges.NonManifoldEdgesOff()
        edges.ManifoldEdgesOff()
        edges.Update()
        edge_mapper = vtk.vtkPolyDataMapper()
        edge_mapper.SetInputConnection(edges.GetOutputPort())
        edge_mapper.ScalarVisibilityOff()
        edge_actor = vtk.vtkActor()
        edge_actor.SetMapper(edge_mapper)
        edge_actor.GetProperty().SetColor(0.25, 0.30, 0.33)
        edge_actor.GetProperty().SetOpacity(item.get("opacity", 1))
        renderer.AddActor(edge_actor)
    camera = renderer.GetActiveCamera()
    directions = {
        "iso": (1.3, -1.8, 1.3),
        "front": (0, -1, 0),
        "top": (0, 0, 1),
        "side": (1, 0, 0),
    }
    camera.SetPosition(*directions[view])
    camera.SetFocalPoint(0, 0, 0)
    camera.SetViewUp(0, 1, 0) if view == "top" else camera.SetViewUp(0, 0, 1)
    camera.ParallelProjectionOn()
    renderer.ResetCamera()
    camera.Zoom(0.95)
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(*size)
    window.SetMultiSamples(4)
    window.AddRenderer(renderer)
    window.Render()
    anchors = []
    for item in items:
        if "part" not in item:
            continue
        center = item["shape"].Center()
        renderer.SetWorldPoint(center.x, center.y, center.z, 1)
        renderer.WorldToDisplay()
        px, py, _ = renderer.GetDisplayPoint()
        anchors.append(
            {"part": item["part"], "name": item["name"], "x": px, "y": py}
        )
    path.with_suffix(".anchors.json").write_text(
        json.dumps({"size": size, "anchors": anchors}, indent=2) + "\n"
    )
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.SetScale(1)
    capture.Update()
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(path))
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()
    window.Finalize()


def normalize_svg_lines(path):
    """Keep plotted line widths constant when a small part is enlarged."""
    content = path.read_text()
    match = re.search(r"scale\(([-\d.]+),", content)
    if not match:
        raise ValueError(f"Missing CAD view scale: {path}")
    scale = abs(float(match.group(1)))
    content = re.sub(
        r'stroke-width="[^"]+"', f'stroke-width="{1.0 / scale:.8f}"', content
    )
    content = re.sub(
        r'stroke-dasharray="[^"]+"',
        f'stroke-dasharray="{3 / scale:.8f},{2 / scale:.8f}"',
        content,
    )
    path.write_text(
        "\n".join(line.rstrip() for line in content.splitlines()) + "\n"
    )


def export():
    assembly = cq.Assembly(name="foldatron_rev_b_development")
    for item in INSTANCES:
        assembly.add(
            item["shape"],
            name=item["name"].replace(".", "_"),
            color=cq.Color(*item["color"]),
        )
    assembly.save(str(CAD / "foldatron-rev-b.step"))
    manifest = []
    for pid, part in PARTS.items():
        shape = part["shape"]
        if not shape.isValid():
            raise ValueError(f"Invalid CAD solid: {pid}")
        cq.exporters.export(shape, str(CAD / f"{pid}.step"))
        for view, direction in (
            ("plan", (0, 0, 1)),
            ("front", (0, -1, 0)),
            ("iso", (1, -1.5, 1)),
        ):
            view_shape = shape
            if view == "front":
                view_shape = shape.rotate((0, 0, 0), (1, 0, 0), -90)
                direction = (0, 0, 1)
            elif view == "iso":
                view_shape = shape.rotate((0, 0, 0), (0, 0, 1), 45)
                view_shape = view_shape.rotate((0, 0, 0), (1, 0, 0), 54.7356)
                direction = (0, 0, 1)
            cq.exporters.export(
                view_shape,
                str(VIEWS / f"{pid}-{view}.svg"),
                opt={
                    "width": 700,
                    "height": 440,
                    "marginLeft": 40,
                    "marginTop": 30,
                    "projectionDir": direction,
                    "showAxes": False,
                    "showHidden": view != "iso",
                    "strokeWidth": 0.65,
                    "strokeColor": (30, 55, 65),
                    "hiddenColor": (170, 185, 190),
                },
            )
            normalize_svg_lines(VIEWS / f"{pid}-{view}.svg")
        # Section below top counterbores preserves through-hole diameters.
        if pid in (
            "B101",
            "B103",
            "B105",
            "B106",
            "B108",
            "B109",
            "B111",
            "B117",
            "B119",
            "B126",
            "B120",
            "B201",
            "B202",
            "B203",
            "B204",
        ):
            bounds = shape.BoundingBox()
            section = (
                cq.Workplane("XY")
                .newObject([shape])
                .section(bounds.zmin + min(0.5, bounds.zlen / 2))
            )
            cq.exporters.exportDXF(
                section, str(CAD / f"{pid}.dxf"), doc_units=4
            )
        b = shape.BoundingBox()
        record = {k: v for k, v in part.items() if k != "shape"}
        record.update(
            {
                "volume_mm3": round(shape.Volume(), 3),
                "bounds_mm": [
                    round(v, 4)
                    for v in (b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax)
                ],
                "solid_valid": shape.isValid(),
                "quantity": sum(i["part"] == pid for i in INSTANCES),
            }
        )
        manifest.append(record)
    (OUT / "custom-parts.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    views = {
        "general": INSTANCES,
        "frame": [i for i in INSTANCES if i["group"] == "frame"],
        "fixture": [i for i in INSTANCES if i["group"] == "fixture"],
        "moving": [i for i in INSTANCES if i["moving"]],
        "bearing": [
            i
            for i in INSTANCES
            if "front" in i["name"]
            and i["name"].startswith(
                (
                    "tower_",
                    "sole_",
                    "angle_",
                    "retainer_",
                    "bearing_",
                    "spacer_",
                    "collar_",
                    "hub_",
                )
            )
        ],
        "float": [
            i
            for i in INSTANCES
            if i["group"] == "fixture"
            and i["name"].startswith(
                (
                    "carrier_",
                    "rail_",
                    "block_",
                    "stop_32",
                    "stop_77",
                    "float_",
                    "crossbar",
                )
            )
        ],
        "endpoints": [
            i for i in INSTANCES if i["name"].startswith("endpoint_")
        ],
        "guard-switch": [
            i for i in INSTANCES if i["name"].startswith("guard_")
        ],
        "supports": [
            i
            for i in INSTANCES
            if i["name"].startswith(("lower_", "crossmember_"))
            or (
                i["name"].startswith("rail_corner_")
                and i["name"].endswith("-20.7")
            )
        ],
        "lower": [
            i
            for i in INSTANCES
            if i["name"].startswith("lower_")
            or (
                i["name"].startswith("rail_corner_")
                and i["name"].endswith("-20.7")
            )
        ],
        "base_towers": [
            i
            for i in INSTANCES
            if i["name"] == "base"
            or i["name"].startswith(("tower_", "sole_", "angle_"))
        ],
        "drive": [
            i
            for i in INSTANCES
            if i["name"].startswith(
                ("motor_", "XM430", "clutch", "front_shaft")
            )
        ],
        "angular_stops": [
            i
            for i in INSTANCES
            if i["name"].startswith(
                ("angular_", "stop_bolt", "stop_pad", "front_shaft")
            )
        ],
        "yoke": [
            i
            for i in INSTANCES
            if i["name"].startswith(("arm_", "hub_", "crossbar", "weight_"))
        ],
    }
    for label, items in views.items():
        for view in (
            ("iso", "front", "top", "side")
            if label in ("fixture", "frame")
            else ("iso",)
        ):
            render(items, VIEWS / f"{label}-{view}.png", view)
    vendor_checks = []
    for filename in ("NC3FD-LX.stp", "NC4FD-LX.stp"):
        path = OUT / "vendor" / filename
        if path.is_file():
            original = cq.importers.importStep(str(path)).val()
            # Some vendor assemblies contain open or tolerance-invalid
            # surfaces. Preserve the original and report, never silently
            # turn an imported reference into a manufacturing approval.
            print(f"Vendor {filename}: imported; valid={original.isValid()}")
            vendor_checks.append(
                {
                    "file": filename,
                    "imported": True,
                    "ocp_valid": original.isValid(),
                    "solids": len(original.Solids()),
                    "purpose": "Vendor reference; not approved fabrication",
                }
            )
            render(
                [{"shape": original, "color": SILVER}],
                VIEWS / (filename[:-4] + ".png"),
            )
    (OUT / "vendor-cad-checks.json").write_text(
        json.dumps(vendor_checks, indent=2) + "\n"
    )
    # Exploded bearing view: displace layers along the actual shaft axis.
    exploded = []
    for item in views["bearing"]:
        copy = dict(item)
        center = item["shape"].Center()
        copy["shape"] = item["shape"].translate((0, (center.y + 120) * 2, 0))
        exploded.append(copy)
    render(exploded, VIEWS / "bearing-exploded.png")
    export_fasteners()
    check_geometry()


def export_fasteners():
    """Standard-derived fastener envelopes; threads deliberately unmodeled."""
    dimensions = {
        2: (3.8, 2, 1.5),
        2.5: (4.5, 2.5, 2),
        3: (5.5, 3, 2.5),
        4: (7, 4, 3),
        5: (8.5, 5, 4),
        6: (10, 6, 5),
    }
    sizes = [
        (2, 6),
        (2, 8),
        (2, 12),
        (2, 16),
        (2.5, 8),
        (3, 8),
        (3, 12),
        (4, 10),
        (4, 12),
        (4, 16),
        (4, 20),
        (5, 12),
        (5, 14),
        (5, 16),
        (5, 20),
        (6, 16),
        (6, 25),
    ]
    folder = CAD / "fasteners"
    folder.mkdir(exist_ok=True)
    for d, length in sizes:
        hd, hh, key = dimensions[d]
        shape = cylinder(d / 2, length).fuse(
            cylinder(hd / 2, hh, (0, 0, length))
        )
        socket = (
            cq.Workplane("XY")
            .polygon(6, key / math.cos(math.pi / 6))
            .extrude(hh * 0.55)
            .translate((0, 0, length + hh * 0.45))
            .val()
        )
        shape = shape.cut(socket)
        cq.exporters.export(shape, str(folder / f"ISO4762-M{d}x{length}.step"))
    (folder / "README.md").write_text(
        "# Standard-derived fastener envelopes\n\n"
        "Nominal ISO4762 geometry from Bossard BN612 dimensional tables "
        "(S28). These are project-generated STEP files, not original "
        "Bossard CAD. Threads, under-head radii and finish are omitted. "
        "Use the fastener schedule for length, thread, strength and "
        "quantity; do not manufacture screws from these envelopes.\n"
    )


def check_geometry():
    """Geometry evidence, kept distinct from physical acceptance testing."""
    moving = [i for i in INSTANCES if i["moving"] and i["part"] != "DUT"]
    custom_mass = []
    for item in moving:
        material = PARTS.get(item["part"], {}).get("material", "")
        density = (
            7.85e-6
            if any(s in material.lower() for s in ("steel", "stainless"))
            else 2.70e-6
        )
        if "acetal" in material.lower():
            density = 1.41e-6
        if item["part"] not in PARTS:
            continue
        mass = item["shape"].Volume() * density
        center = item["shape"].Center()
        custom_mass.append(
            {
                "name": item["name"],
                "kg": mass,
                "x_mm": center.x,
                "z_mm": center.z - 140,
            }
        )
    moment_x = sum(p["kg"] * p["x_mm"] for p in custom_mass)
    moment_z = sum(p["kg"] * p["z_mm"] for p in custom_mass)
    # Check sampled moving-solid clearance against actual static supports.
    obstacles = [
        i
        for i in INSTANCES
        if i["group"] == "fixture" and not i["moving"] and i["part"] != "DUT"
    ]
    hits = []
    minimum_z = float("inf")
    for angle in range(0, 181, 5):
        for item in moving:
            shape = item["shape"].rotate((0, 0, 140), (0, 1, 140), -angle)
            bounds = shape.BoundingBox()
            minimum_z = min(minimum_z, bounds.zmin)
            for obstacle in obstacles:
                b = obstacle["shape"].BoundingBox()
                if not (
                    bounds.xmax > b.xmin
                    and bounds.xmin < b.xmax
                    and bounds.ymax > b.ymin
                    and bounds.ymin < b.ymax
                    and bounds.zmax > b.zmin
                    and bounds.zmin < b.zmax
                ):
                    continue
                volume = shape.intersect(obstacle["shape"]).Volume()
                if volume > 0.01:
                    hits.append(
                        {
                            "angle": angle,
                            "moving": item["name"],
                            "static": obstacle["name"],
                            "overlap_mm3": round(volume, 3),
                        }
                    )
    endpoint_hits = []
    for item in obstacles:
        if not item["name"].startswith("endpoint_"):
            continue
        for other in obstacles:
            if item["name"] == other["name"]:
                continue
            volume = item["shape"].intersect(other["shape"]).Volume()
            if volume > 0.01:
                endpoint_hits.append(
                    {
                        "part": item["name"],
                        "other": other["name"],
                        "volume_mm3": round(volume, 3),
                    }
                )
    checks = {
        "date": "2026-11-05",
        "scope": "CAD checks only; no hardware assembled or operated",
        "all_custom_solids_valid": all(
            p["shape"].isValid() for p in PARTS.values()
        ),
        "frame_outer_mm": [660.4, 558.8, 558.8],
        "cut_lengths_mm": {"660.4": 4, "508": 8, "609.6": 2},
        "total_extrusion_mm": 4 * 660.4 + 8 * 508 + 2 * 609.6,
        "phone_dimensions_verified": False,
        "complete_assembly_interference_verified": False,
        "sampled_sweep_degrees": list(range(0, 181, 5)),
        "sampled_static_obstacles": [i["name"] for i in obstacles],
        "sampled_sweep_collisions": hits,
        "endpoint_static_collisions": endpoint_hits,
        "sampled_minimum_moving_z_mm": minimum_z,
        "sweep_limitations": "Discrete 5 degree samples; excludes DUT, "
        "unmodelled wiring, screw heads and switch-lever deflection. "
        "Not a continuous collision proof.",
        "custom_moving_mass_kg": sum(p["kg"] for p in custom_mass),
        "custom_only_gravity_peak_Nm": math.hypot(moment_x, moment_z)
        * 9.80665
        / 1000,
        "mass_exclusions": "Guide blocks, rails, collars, fasteners, pads "
        "and phone. Counterweight setting must be measured.",
        "custom_mass_components": custom_mass,
        "checks": [
            {
                "id": "G01",
                "result": "PASS",
                "detail": "500 mm base fits within 609.6 mm crossmember span.",
            },
            {
                "id": "G02",
                "result": "PASS",
                "detail": "M2 x 6 through 4 mm plate engages block 2 mm < 2.5 "
                "max.",
            },
            {
                "id": "G03",
                "result": "PASS",
                "detail": "Two MGN7C mounting patterns are 12 x 8 mm; "
                "purchased thread pitch still requires confirmation.",
            },
            {
                "id": "G04",
                "result": "HOLD",
                "detail": "Clutch engagement and phone inserts, plus "
                "interlock actuation still require physical acceptance.",
            },
        ],
    }
    (OUT / "verification.json").write_text(json.dumps(checks, indent=2) + "\n")


def main():
    CAD.mkdir(parents=True, exist_ok=True)
    VIEWS.mkdir(parents=True, exist_ok=True)
    build_custom()
    build_frame()
    build_fixture()
    build_guards()
    export()
    print(f"Built {len(PARTS)} custom parts and {len(INSTANCES)} instances")


if __name__ == "__main__":
    main()
