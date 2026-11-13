"""Purchased fixture layout and dimensional interface models.

Original Thorlabs and Zaber solids retain their vendor geometry. The XY
stage, extrusion and vacuum parts are explicitly catalog interface models.
This export is a review assembly, not evidence of physical commissioning.
"""

import json
from pathlib import Path

import cadquery as cq
from build_structure import box, extrusion, image, vendor

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "hardware"
CAD = DATA / "cad"
VIEWS = DATA / "views"
PARTS = []
COLORS = {
    "motion": (0.20, 0.28, 0.32),
    "mast": (0.70, 0.74, 0.77),
    "vacuum": (0.12, 0.45, 0.56),
    "phone": (0.28, 0.43, 0.48),
}


def add(name, part, shape, group, evidence, color="motion"):
    if not shape.isValid():
        raise ValueError(f"Invalid solid: {name}")
    PARTS.append({
        "name": name, "part": part, "shape": shape, "group": group,
        "evidence": evidence, "color": COLORS[color],
    })
    return shape


def catalog(name, part, shape, group, color="motion"):
    return add(name, part, shape, group, "Catalog interface model", color)


def original(name, part, shape, group):
    return add(name, part, shape, group, "Original vendor STEP")


def rail(name, center, bottom, group):
    shape = vendor("RLA300-M").rotate((0, 0, 0), (1, 1, 1), 120)
    return original(name, "RLA300/M", shape.translate(
        (center[0], center[1], bottom + 5.08)), group)


def carrier(name, center, rail_bottom, group):
    # Nominal seated position for the layout. Final assembled height is a
    # receiving/assembly measurement; the locked carrier is setup-only.
    shape = vendor("RC2-M").rotate((0, 0, 0), (1, 0, 0), 90)
    offset = (center[0] - 25.4, center[1] + 12.7, rail_bottom + 4.08)
    return original(name, "RC2/M", shape.translate(offset), group)


def xy_stage(center, bottom):
    """Mounting-envelope model; no invented roller/race internal geometry."""
    x, y = center
    lower = box(44.45, 22.225, 10.16, (x, y, bottom + 5.08))
    for dx in (-16.6624, 16.6624):
        lower = lower.cut(cq.Solid.makeCylinder(
            1.9939, 11, cq.Vector(x + dx, y, bottom - 0.1)))
        lower = lower.cut(cq.Solid.makeCylinder(
            3.048, 4, cq.Vector(x + dx, y, bottom + 6.477)))
    middle = box(44.45, 44.45, 10.16,
                 (x, y, bottom + 18.9992))
    upper = box(44.45, 44.45, 8.0772,
                (x, y, bottom + 33.9598))
    holes = [(a, b) for a in (-12.7, 12.7) for b in (-12.7, 12.7)]
    holes.extend([(0, -16.6624), (0, 16.6624)])
    for dx, dy in holes:
        upper = upper.cut(cq.Solid.makeCylinder(
            1.35255, 9, cq.Vector(x + dx, y + dy, bottom + 29.5)))
    for label, shape in [("base", lower), ("middle", middle),
                         ("carriage", upper)]:
        catalog(f"xy-{label}", "R451P-XY", shape, "moving")
    return bottom + 37.9984


def angle(name, mount_center, bottom, group):
    # Original horizontal leg is normal to Y. After the cyclic rotation,
    # its slot runs along X and its outside vertical wall faces -X.
    shape = vendor("AB90").rotate((0, 0, 0), (1, 1, 1), 120)
    shift = (mount_center[0] - 5.08, mount_center[1], bottom + 25.4)
    return original(name, "AB90", shape.translate(shift), group)


def cylinder_x(radius, length, point):
    return cq.Solid.makeCylinder(radius, length, cq.Vector(*point),
                                 cq.Vector(1, 0, 0))


def grip(name, y, bottom, length, group):
    # Contact plane x=5 mm for the 5 mm thick illustrative leaf.
    # BA1/M has a 0.381 mm underside relief at its central mounting hole.
    cup_plane = 5.0
    holder_rear = cup_plane + 11.6 + 28.0
    plate_rear = holder_rear + 9.619
    mast_back = plate_rear + 25.4
    mast = extrusion(length).translate(
        (plate_rear + 12.7, y, bottom + length / 2))
    catalog(f"{name}-mast", f"1010 / {length:g} mm", mast, group, "mast")
    for number, height in enumerate((160.0, 240.0), 1):
        plate = vendor("BA1-M").rotate((0, 0, 0), (0, 0, 1), -90)
        plate = plate.translate((holder_rear + 4.619, y, height))
        original(f"{name}-cup-plate-{number}", "BA1/M", plate, group)
        # Body/port envelopes retain catalog mounting dimensions; seals,
        # hex flats and pneumatic passages are not represented as tooling.
        body = cylinder_x(6, 28, (cup_plane + 11.6, y, height))
        port = cq.Solid.makeCylinder(
            5, 20.4, cq.Vector(holder_rear - 14.4, y, height),
            cq.Vector(0, 1 if group == "moving" else -1, 0))
        catalog(f"{name}-holder-{number}", "ESH-HB-4-QS / 189209",
                body.fuse(port), group, "vacuum")
        cup = cq.Solid.makeCone(
            10, 7.75, 11.6, cq.Vector(cup_plane, y, height),
            cq.Vector(1, 0, 0))
        catalog(f"{name}-cup-{number}", "ESS-20-SN / 189294",
                cup, group, "vacuum")
    return mast_back


def mesh(shape, angular_tolerance=0.2):
    vertices, triangles = shape.tessellate(0.3, angular_tolerance)
    return {
        "vertices": [round(v, 5) for p in vertices for v in p.toTuple()],
        "triangles": [v for triangle in triangles for v in triangle],
    }


def upright_view(shape, filename, direction):
    """Keep machine Z upward despite OpenCascade's automatic view axes."""
    image(shape, filename, direction, width=1000, height=1000)


def build():
    PARTS.clear()
    CAD.mkdir(exist_ok=True)
    VIEWS.mkdir(exist_ok=True)
    original("rotary-stage", "X-RSW60A-E03",
             vendor("X-RSW60A-E03").rotate(
                 (0, 0, 0), (1, 0, 0), 90), "fixed")
    # Rail's rear end is -37.5 mm from the rotary axis. Mounting it at
    # +37.5 mm instead would produce a -112.5 mm tail and a grip collision.
    rail("rotating-adjustment-rail", (112.5, 12.5), 31.75, "moving")
    rail("stationary-adjustment-rail", (50, -50), 0, "fixed")
    q = 5 + 11.6 + 28 + 9.619 + 25.4 + 30.48
    moving_carrier = carrier("rotating-locked-carrier", (q, 12.5),
                              31.75, "moving")
    fixed_carrier = carrier("stationary-locked-carrier", (q, -50),
                             0, "fixed")
    carrier_top = moving_carrier.BoundingBox().zmax
    plate = vendor("BA2-M").rotate((0, 0, 0), (1, 0, 0), 90)
    plate = plate.translate((q, 12.5, carrier_top + 4.8095))
    original("xy-mounting-plate", "BA2/M", plate, "moving")
    xy_top = xy_stage((q, 37.5), plate.BoundingBox().zmax)
    angle("moving-mast-angle", (q, 50.2), xy_top, "moving")
    angle("fixed-mast-angle", (q, -50),
          fixed_carrier.BoundingBox().zmax, "fixed")
    grip("moving", 50.2, xy_top, 200, "moving")
    grip("fixed", -50, fixed_carrier.BoundingBox().zmax, 300, "fixed")
    catalog("moving-surrogate-leaf", "Illustrative 70 x 160 x 5 mm leaf",
            box(5, 70, 160, (2.5, 35, 210)), "moving-phone", "phone")
    catalog("fixed-surrogate-leaf", "Illustrative 70 x 160 x 5 mm leaf",
            box(5, 70, 160, (2.5, -35, 210)), "fixed-phone", "phone")
    return PARTS


def main():
    build()

    assembly = cq.Assembly(name="foldatron-rev-c-fixture-development")
    for item in PARTS:
        assembly.add(item["shape"], name=item["name"],
                     color=cq.Color(*item["color"]))
    cq.exporters.export(assembly.toCompound(),
                        str(CAD / "fixture-development.step"))
    for label, angle_deg in (("open", 0), ("midstroke", 90), ("closed", 180)):
        shapes = [item["shape"].rotate((0, 0, 0), (0, 0, 1), angle_deg)
                  if item["group"].startswith("moving") else item["shape"]
                  for item in PARTS]
        compound = cq.Compound.makeCompound(shapes)
        upright_view(compound, f"fixture-{label}-iso.svg", (1.3, -1.6, 0.9))
        upright_view(compound, f"fixture-{label}-plan.svg", (0, 0, 1))
    output = []
    for item in PARTS:
        row = {key: value for key, value in item.items() if key != "shape"}
        row.update(mesh(item["shape"]))
        output.append(row)
    (DATA / "fixture-model.json").write_text(json.dumps({
        "units": "mm",
        "status": "DEVELOPMENT: fasteners and hoses not yet modeled",
        "phone": "Surrogate only; not an iPhone dimensional model",
        "rotation_axis": [0, 0, 1],
        "parts": output,
    }, separators=(",", ":")) + "\n")
    print(f"Exported {len(PARTS)} fixture components")


if __name__ == "__main__":
    main()
