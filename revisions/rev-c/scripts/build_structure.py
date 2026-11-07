"""Build the Rev C structure study from purchased-part interfaces.

This is a development assembly, not a fabrication or machine build release.
The phone-contact fixture and electrical cabinet are deliberately absent.
"""

import json
from pathlib import Path

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "hardware"
VENDOR = DATA / "vendor"
CAD = DATA / "cad"
VIEWS = DATA / "views"
SILVER = cq.Color(0.70, 0.74, 0.77)
BLACK = cq.Color(0.16, 0.19, 0.21)
BLUE = cq.Color(0.18, 0.42, 0.52)


def box(x, y, z, center=(0, 0, 0)):
    return cq.Workplane("XY").box(x, y, z).translate(center).val()


def extrusion(length):
    """Catalog envelope; indicative slots, not a manufacturer section."""
    result = box(25.4, 25.4, length)
    for angle in (0, 90, 180, 270):
        relief = box(6.5, 7.5, length + 2, (0, 10.5, 0))
        result = result.cut(relief.rotate((0, 0, 0), (0, 0, 1), angle))
    return result


def flat_plate():
    """4151 catalog mounting geometry; small edge radii omitted."""
    outline = [
        (-12.7, -12.7),
        (63.5, -12.7),
        (63.5, 12.7),
        (12.7, 12.7),
        (12.7, 63.5),
        (-12.7, 63.5),
    ]
    result = cq.Workplane("XY").polyline(outline).close().extrude(4.7752)
    for x, y in [(0, 0), (25.4, 0), (50.8, 0), (0, 25.4), (0, 50.8)]:
        hole = cq.Solid.makeCylinder(6.5278 / 2, 7, cq.Vector(x, y, -1))
        result = result.cut(hole)
    return result.val()


def vendor(part):
    """Use original vendor solid, preserving its units and shape."""
    return cq.importers.importStep(str(VENDOR / f"{part}.step")).val()


def image(shape, filename, direction, width=1200, height=800):
    cq.exporters.export(
        shape,
        str(VIEWS / filename),
        exportType="SVG",
        opt={
            "width": width,
            "height": height,
            "projectionDir": direction,
            "showAxes": False,
            "showHidden": False,
            "strokeWidth": 0.4,
            "strokeColor": (25, 52, 66),
            "marginLeft": 30,
            "marginTop": 30,
        },
    )


def main():
    CAD.mkdir(parents=True, exist_ok=True)
    VIEWS.mkdir(parents=True, exist_ok=True)
    assembly = cq.Assembly(name="foldatron-rev-c-structure-study")
    instances = []
    groups = {}

    def add(name, part, shape, group, evidence, color=SILVER):
        assembly.add(shape, name=name, color=color)
        bounds = shape.BoundingBox()
        instances.append(
            {
                "name": name,
                "part": part,
                "group": group,
                "geometry": evidence,
                "bounds_mm": [
                    round(v, 5)
                    for v in (
                        bounds.xmin,
                        bounds.xmax,
                        bounds.ymin,
                        bounds.ymax,
                        bounds.zmin,
                        bounds.zmax,
                    )
                ],
            }
        )
        groups.setdefault(group, []).append(shape)

    for z, tier in [(12.7, "base"), (647.7, "roof")]:
        for sign in [-1, 1]:
            shape = (
                extrusion(762)
                .rotate((0, 0, 0), (0, 1, 0), 90)
                .translate((0, sign * 368.3, z))
            )
            add(
                f"{tier}-x-{sign}",
                "C101",
                shape,
                "frame",
                "Catalog envelope / indicative slot relief",
            )
            shape = (
                extrusion(711.2)
                .rotate((0, 0, 0), (1, 0, 0), 90)
                .translate((sign * 368.3, 0, z))
            )
            add(
                f"{tier}-y-{sign}",
                "C102",
                shape,
                "frame",
                "Catalog envelope / indicative slot relief",
            )
    for x in [-368.3, 368.3]:
        for y in [-368.3, 368.3]:
            shape = extrusion(609.6).translate((x, y, 330.2))
            add(
                f"post-{x}-{y}",
                "C103",
                shape,
                "frame",
                "Catalog envelope / indicative slot relief",
            )
    for y in [-275, 275]:
        shape = (
            extrusion(711.2)
            .rotate((0, 0, 0), (0, 1, 0), 90)
            .translate((0, y, 12.7))
        )
        add(
            f"breadboard-support-{y}",
            "C104",
            shape,
            "frame",
            "Catalog envelope / indicative slot relief",
        )

    # External plates avoid notching the side and rear guard panels.
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            for z, up in [(12.7, 1), (647.7, -1)]:
                p = flat_plate()
                if sx == 1:
                    p = p.mirror("YZ")
                if up == -1:
                    p = p.mirror("XZ")
                p = p.rotate((0, 0, 0), (1, 0, 0), 90)
                if sy == 1:
                    p = p.mirror("XZ")
                p = p.translate((sx * 368.3, sy * 381, z))
                add(
                    f"upright-plate-{sx}-{sy}-{z}",
                    "C105",
                    p,
                    "plates",
                    "Catalog-derived interface",
                    BLUE,
                )
            p = flat_plate()
            if sx == 1:
                p = p.mirror("YZ")
            if sy == 1:
                p = p.mirror("XZ")
            p = p.translate((sx * 368.3, sy * 368.3, 660.4))
            add(
                f"roof-plate-{sx}-{sy}",
                "C105",
                p,
                "plates",
                "Catalog-derived interface",
                BLUE,
            )

    board = (
        vendor("MB6060-M")
        .rotate((0, 0, 0), (1, 0, 0), 90)
        .translate((0, 0, 25.4))
    )
    add(
        "purchased-breadboard",
        "C110",
        board,
        "base",
        "Original Thorlabs STEP",
        BLACK,
    )
    stage = (
        vendor("X-RSW60A-E03")
        .rotate((0, 0, 0), (1, 0, 0), 90)
        .translate((12.5, 12.5, 38.1))
    )
    add(
        "purchased-rotary-stage",
        "C111",
        stage,
        "motion",
        "Original Zaber STEP",
        BLACK,
    )

    cq.exporters.export(
        assembly.toCompound(), str(CAD / "structure-study.step")
    )
    (DATA / "structure-instances.json").write_text(
        json.dumps(instances, indent=2) + "\n"
    )
    structural = cq.Compound.makeCompound(groups["frame"] + groups["plates"])
    image(structural, "structure-iso.svg", (1, -1.4, 1.0))
    image(structural, "structure-front.svg", (0, -1, 0))
    image(cq.Compound.makeCompound([board, stage]), "base-plan.svg", (0, 0, 1))
    image(stage, "stage-iso.svg", (1, -1, 0.8))
    image(stage, "stage-plan.svg", (0, 0, 1))
    image(vendor("FP01"), "clamp-iso.svg", (1, 1, 1))
    image(vendor("RC2-M"), "carrier-iso.svg", (1, 1, 1))
    image(vendor("RLA150-M"), "rail-iso.svg", (1, 1, 1))

    # Nominal top interface only: not the released contact mechanism.
    rail = (
        vendor("RLA150-M")
        .rotate((0, 0, 0), (1, 1, 1), 120)
        .translate((50, 25, 38.1 + 31.75 + 5.08))
    )
    top_study = cq.Compound.makeCompound([stage, rail])
    image(top_study, "top-interface-iso.svg", (1, -1, 0.8))
    cq.exporters.export(top_study, str(CAD / "top-interface-study.step"))
    print(f"Exported {len(instances)} structure instances; fixture absent")


if __name__ == "__main__":
    main()
