"""Build an explicitly illustrative closure study and catalog bracket views.

The surrogate is not an iPhone dimensional model. Its single-axis hinge
only checks the contact-envelope principle, not complete bench clearance.
"""

import json
import math
from pathlib import Path

from build_structure import image, vendor

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "hardware"
VIEWS = DATA / "views"


def rectangle(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def rotate(points, degrees):
    angle = math.radians(degrees)
    cosine, sine = math.cos(angle), math.sin(angle)
    return [(x * cosine - y * sine, x * sine + y * cosine) for x, y in points]


def overlaps(a, b, tolerance=1e-8):
    """Convex polygon SAT; touching boundaries are not volume overlap."""
    for polygon in (a, b):
        for start, end in zip(polygon, polygon[1:] + polygon[:1]):
            axis = (start[1] - end[1], end[0] - start[0])
            pa = [x * axis[0] + y * axis[1] for x, y in a]
            pb = [x * axis[0] + y * axis[1] for x, y in b]
            if max(pa) <= min(pb) + tolerance:
                return False
            if max(pb) <= min(pa) + tolerance:
                return False
    return True


def main():
    VIEWS.mkdir(parents=True, exist_ok=True)
    # Explicit surrogate dimensions, not product measurements.
    fixed_leaf = rectangle(-70, -5, 0, 0)
    moving_leaf = rectangle(0, -5, 70, 0)
    fixed_grip = rectangle(-50, -45, -30, -5)
    moving_grip = rectangle(30, -45, 50, -5)
    if not overlaps(fixed_leaf, fixed_leaf):
        raise ValueError("Overlap detector failed its positive control")
    if overlaps(fixed_leaf, moving_leaf):
        raise ValueError("Touching-edge detector failed its boundary control")
    failed = []
    for index in range(361):
        rotation = index / 2
        leaf = rotate(moving_leaf, rotation)
        grip = rotate(moving_grip, rotation)
        if (
            overlaps(fixed_leaf, leaf)
            or overlaps(fixed_leaf, grip)
            or overlaps(fixed_grip, leaf)
            or overlaps(fixed_grip, grip)
        ):
            failed.append(rotation)
    if failed:
        raise ValueError(f"Surrogate overlap at rotations: {failed}")
    audit = {
        "status": "Illustrative 2D envelopes only; NOT bench validation",
        "source": "Owner full-closure decision; dimensions are a surrogate",
        "surrogate_leaf_width_mm": 70,
        "surrogate_leaf_thickness_mm": 5,
        "surrogate_contact_radius_mm": 40,
        "contact_envelope_width_mm": 20,
        "contact_envelope_projection_mm": 40,
        "rotation_step_deg": 0.5,
        "samples": 361,
        "overlapping_samples": failed,
        "excluded": [
            "Actual phone and non-circular hinge path",
            "Support brackets, rails, screw heads and stage",
            "Hoses, cable loops and thermal probes",
            "Cup deformation, grip retention and load capacity",
        ],
    }
    (DATA / "closure-study.json").write_text(
        json.dumps(audit, indent=2) + "\n"
    )
    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'width="1100" height="450" viewBox="0 0 1100 450">',
        '<rect width="1100" height="450" fill="white"/>',
    ]
    for i, angle in enumerate((0, 90, 180)):
        cx, cy, scale = 190 + i * 355, 240, 1.85
        shapes = [
            (fixed_leaf, "#c6d5dd"),
            (rotate(moving_leaf, angle), "#6eb4bb"),
            (fixed_grip, "#b6c0c5"),
            (rotate(moving_grip, angle), "#a8d2d5"),
        ]
        for polygon, color in shapes:
            points = " ".join(
                f"{cx + x * scale:.2f},{cy - y * scale:.2f}"
                for x, y in polygon
            )
            parts.append(
                f'<polygon points="{points}" fill="{color}" '
                'stroke="#183846" stroke-width="1.5"/>'
            )
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="4" fill="#b57124"/>')
        parts.append(
            f'<text x="{cx}" y="45" text-anchor="middle" '
            'font-family="Helvetica" font-size="23" '
            f'fill="#183846">{180 - angle} deg opening</text>'
        )
        parts.append(
            f'<text x="{cx}" y="395" text-anchor="middle" '
            'font-family="Helvetica" font-size="15" '
            'fill="#183846">Outside grips stay out of gap</text>'
        )
    parts.append("</svg>")
    (VIEWS / "closure-sequence.svg").write_text("\n".join(parts))
    bracket = vendor("AB90")
    if not bracket.isValid():
        raise ValueError("Invalid original AB90 vendor solid")
    image(bracket, "vacuum-bracket-iso.svg", (1, 1, 1))
    print("361 surrogate contact-envelope positions checked; bench untested")


if __name__ == "__main__":
    main()
