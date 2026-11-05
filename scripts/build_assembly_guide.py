"""Build the separate illustrated assembly book and editable SVG figures."""

import html
import json
import math
from pathlib import Path

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "docs/assembly"
OUTPUT = ROOT / "docs/Foldatron-illustrated-assembly-manual.pdf"
W, H = A4
INK = "#182f3c"
TEAL = "#087f83"
PALE = "#dceff0"
GRAY = "#dde3e6"
MUTED = "#657782"
ORANGE = "#b35d1c"
LIGHT = "#f3f6f7"
RED = "#a33335"
FONT_DIR = Path(reportlab.__file__).parent / "fonts"
pdfmetrics.registerFont(TTFont("Guide", str(FONT_DIR / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("GuideBold", str(FONT_DIR / "VeraBd.ttf")))


def colour(value):
    return colors.HexColor(value)


def para(c, text, x, top, width, size=9.4, leading=13, bold=False):
    style = ParagraphStyle(
        "p",
        fontName="GuideBold" if bold else "Guide",
        fontSize=size,
        leading=leading,
        textColor=colour(INK),
        splitLongWords=True,
    )
    p = Paragraph(text, style)
    _, height = p.wrap(width, 1000)
    p.drawOn(c, x, top - height)
    return top - height


class Figure:
    """One geometry source renders both PDF vectors and editable SVG."""

    def __init__(self, c):
        self.c = c
        self.svg = []

    def line(self, x1, y1, x2, y2, color=INK, width=1.2, dash=False):
        c = self.c
        c.setStrokeColor(colour(color))
        c.setLineWidth(width)
        c.setDash([4, 3] if dash else [])
        c.line(x1, y1, x2, y2)
        extra = ' stroke-dasharray="4 3"' if dash else ""
        self.svg.append(
            f'<line x1="{x1}" y1="{280 - y1}" x2="{x2}" '
            f'y2="{280 - y2}" stroke="{color}" '
            f'stroke-width="{width}"{extra}/>'
        )
        c.setDash([])

    def poly(self, points, fill=GRAY, stroke=INK, width=1):
        c = self.c
        p = c.beginPath()
        p.moveTo(*points[0])
        for point in points[1:]:
            p.lineTo(*point)
        p.close()
        c.setLineWidth(width)
        c.setFillColor(colour(fill))
        c.setStrokeColor(colour(stroke))
        c.drawPath(p, fill=1, stroke=1)
        pts = " ".join(f"{x},{280 - y}" for x, y in points)
        self.svg.append(
            f'<polygon points="{pts}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{width}"/>'
        )

    def rect(self, x, y, w, h, fill=GRAY, stroke=INK):
        self.poly(
            [(x, y), (x + w, y), (x + w, y + h), (x, y + h)], fill, stroke
        )

    def circle(self, x, y, r, fill="#ffffff", stroke=INK):
        c = self.c
        c.setFillColor(colour(fill))
        c.setStrokeColor(colour(stroke))
        c.setLineWidth(1)
        c.circle(x, y, r, fill=1, stroke=1)
        self.svg.append(
            f'<circle cx="{x}" cy="{280 - y}" r="{r}" '
            f'fill="{fill}" stroke="{stroke}"/>'
        )

    def text(self, x, y, text, size=9, color=INK, bold=False):
        self.c.setFillColor(colour(color))
        self.c.setFont("GuideBold" if bold else "Guide", size)
        self.c.drawString(x, y, text)
        weight = ' font-weight="bold"' if bold else ""
        self.svg.append(
            f'<text x="{x}" y="{280 - y}" font-family="sans-serif" '
            f'font-size="{size}" fill="{color}"{weight}>'
            f"{html.escape(text)}</text>"
        )

    def arrow(self, x1, y1, x2, y2, color=TEAL, both=False):
        self.line(x1, y1, x2, y2, color, 1.6)
        angle = math.atan2(y2 - y1, x2 - x1)
        for x, y, a in [(x2, y2, angle)] + (
            [(x1, y1, angle + math.pi)] if both else []
        ):
            pts = [(x, y)] + [
                (x - 7 * math.cos(a + t), y - 7 * math.sin(a + t))
                for t in [-0.4, 0.4]
            ]
            self.poly(pts, color, color)

    def tag(self, text, x, y, target):
        self.line(x, y - 5, *target, MUTED, 0.8)
        self.circle(*target, 2, TEAL, TEAL)
        width = pdfmetrics.stringWidth(text, "GuideBold", 8.6)
        self.rect(x - 2, y - 2, width + 4, 12, "#ffffff", "#ffffff")
        self.text(x, y, text, 8.6, bold=True)

    def dim(self, x1, y1, x2, y2, label):
        self.arrow(x1, y1, x2, y2, MUTED, both=True)
        self.text((x1 + x2) / 2 - 20, (y1 + y2) / 2 + 7, label, 8, MUTED)

    def box(self, x, y, w, h, label, fill=LIGHT):
        self.rect(x, y, w, h, fill)
        for index, row in enumerate(label.split("|")):
            self.text(x + 8, y + h - 16 - index * 13, row, 8.5)

    def iso(self, x, y, z):
        return 255 + 0.55 * x + 0.35 * y, 100 - 0.18 * x + 0.22 * y + 0.62 * z

    def block(self, x, y, z, dx, dy, dz, fill=GRAY):
        p = self.iso
        faces = [
            [(x, y, z), (x + dx, y, z), (x + dx, y, z + dz), (x, y, z + dz)],
            [
                (x + dx, y, z),
                (x + dx, y + dy, z),
                (x + dx, y + dy, z + dz),
                (x + dx, y, z + dz),
            ],
            [
                (x, y, z + dz),
                (x + dx, y, z + dz),
                (x + dx, y + dy, z + dz),
                (x, y + dy, z + dz),
            ],
        ]
        for face in faces:
            self.poly([p(*point) for point in face], fill, INK, 0.8)

    def shaft(self, y1, y2, z=140, color=TEAL):
        self.line(*self.iso(0, y1, z), *self.iso(0, y2, z), color, 5)

    def base(self):
        self.block(-250, -200, -8, 500, 400, 8, LIGHT)

    def towers(self, active=False):
        for y in [-95, 95]:
            self.block(-45, y - 4, 0, 90, 8, 180, PALE if active else GRAY)
            self.circle(*self.iso(0, y, 140), 9, "#ffffff")
            self.circle(*self.iso(0, y, 140), 3, "#ffffff")

    def yoke(self, active=False):
        fill = PALE if active else GRAY
        for y in [-95, 95]:
            self.block(-8, y - 12, 134, 135, 24, 6, fill)
        self.block(103, -108, 134, 24, 216, 6, fill)
        self.shaft(-150, -70)
        self.shaft(70, 135)
        for y in [-105, -85, 85, 105]:
            self.circle(*self.iso(0, y, 140), 5, PALE)
        for y in [-95, 95]:
            for offset in [-6, 6]:
                self.circle(*self.iso(115, y + offset, 141), 2, TEAL)

    def write(self, path):
        path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" '
            'width="1040" height="560" viewBox="0 0 520 280">'
            '<rect width="520" height="280" fill="white"/>'
            + "\n".join(self.svg)
            + "</svg>\n"
        )


def mechanical(f, kind):
    f.base()
    if kind == "base":
        for x in [-230, 230]:
            for y in [-180, 180]:
                f.block(x - 12, y - 12, -30, 24, 24, 12, PALE)
                f.arrow(*f.iso(x, y, -18), *f.iso(x, y, -5))
        f.tag("FAB-M01: 500 x 400 x 8", 20, 245, f.iso(-100, 0, 0))
        f.tag("BOM M07: M6 foot x4", 300, 205, f.iso(230, 180, -20))
        f.tag("Foot centers: +/-230, +/-180", 20, 25, f.iso(-230, -180, 0))
        return
    f.towers(kind == "towers")
    if kind == "towers":
        f.shaft(-180, 180, color=ORANGE)
        f.tag("Temporary rod - REMOVE", 20, 250, f.iso(0, -160, 140))
        f.tag("D08 bearing x2", 340, 245, f.iso(0, 95, 140))
        f.tag("FAB-M02 towers x2", 310, 30, f.iso(30, -95, 45))
        f.dim(95, 80, 95, 168, "Z 140")
        f.text(20, 210, "Centers: X=0, Y=+/-95 mm", 9, TEAL)
        return
    f.yoke(kind == "yoke")
    if kind == "yoke":
        f.tag("D11 hub + FAB-M03 arm x2", 20, 255, f.iso(0, -95, 140))
        f.tag("FAB-M04 crossbar / H1", 340, 230, f.iso(115, 50, 140))
        f.tag("Two separate D09 stubs", 20, 40, f.iso(0, -140, 140))
        f.text(20, 22, "No continuous shaft through Y=-70 to +70", 9, RED)
        f.line(*f.iso(0, -70, 140), *f.iso(0, 70, 140), RED, 1, True)
        return
    if kind in {"drive", "index"}:
        f.block(-45, -195, 110, 90, 85, 6, GRAY)
        f.block(-20, -195, 120, 40, 40, 40, PALE)
        f.shaft(-155, -137, color=TEAL)
        f.circle(*f.iso(0, -130, 140), 11, PALE)
        f.tag("D01 motor + D04 horn", 20, 250, f.iso(0, -180, 140))
        f.tag("D07 clutch - horizontal", 300, 245, f.iso(0, -130, 140))
        f.tag("FAB-M09 shelf + M11 adapter", 20, 20, f.iso(0, -165, 120))
        f.text(
            20, 225, "Mechanically disconnected for initial indexing", 9, RED
        )
        f.arrow(110, 92, 143, 110)
        if kind == "drive":
            f.rect(8, 5, 506, 65, "#ffffff", "#ffffff")
            labels = [
                "D01|motor",
                "D04|horn",
                "M11|adapter",
                "D09|input link",
                "D07|clutch",
                "D09|stub",
            ]
            for i, label in enumerate(labels):
                x = 10 + i * 85
                f.box(x, 24, 73, 38, label, PALE)
                if i < 5:
                    f.arrow(x + 74, 42, x + 83, 42)
            f.text(10, 8, "Axial assembly order; no shaft through phone", 8)
        if kind == "index":
            f.box(
                350,
                30,
                155,
                65,
                "CLOSED reference|Example tick 1024|5 deg; measure actual",
                PALE,
            )
        return
    if kind in {"rails", "cradle", "shoes", "force", "dummy", "release"}:
        if kind == "rails":
            for y in [-45, 45]:
                f.block(8, y - 4, 150, 100, 8, 8, TEAL)
                f.block(40, y - 10, 163, 25, 20, 8, PALE)
            f.block(0, -67, 205, 100, 134, 4, PALE)
            f.arrow(*f.iso(45, 0, 200), *f.iso(45, 0, 173))
            f.tag("FAB-M05 moving plate", 20, 255, f.iso(40, -55, 209))
            f.tag("D12 MGN7 x2", 365, 245, f.iso(75, 45, 157))
            f.tag("FAB-M12 carrier x2", 20, 25, f.iso(70, -45, 140))
            f.text(275, 35, "+/-6 mm radial travel", 9, TEAL)
            f.text(275, 18, "Keep >=2 mm end reserve", 9, RED)
        else:
            f.block(-98, -67, 125, 100, 134, 4, PALE)
            f.block(2, -67, 125, 100, 134, 4, GRAY)
            for y in [-45, 45]:
                f.block(-92, y - 3, 0, 70, 6, 124, GRAY)
            if kind == "cradle":
                f.tag("FAB-M06 fixed plate", 20, 245, f.iso(-60, -30, 130))
                f.tag("FAB-M07 risers x2", 320, 35, f.iso(-45, 45, 65))
                f.text(300, 245, "USB half stays fixed", 9, TEAL)
            else:
                f.block(-82, -59, 135, 80, 118, 5, GRAY)
                f.block(2, -59, 135, 80, 118, 5, PALE)
                for x in [-78, -10, 10, 78]:
                    for y in [-50, 50]:
                        f.block(x - 5, y - 6, 140, 10, 12, 7, TEAL)
                f.tag("Fixed USB half", 20, 245, f.iso(-55, -20, 140))
                f.tag("Floating moving half", 340, 245, f.iso(55, 30, 140))
                if kind == "force":
                    f.arrow(390, 100, 390, 160, ORANGE)
                    f.text(390, 80, "F tangent", 9, ORANGE)
                    f.text(20, 28, "Clutch test: phone removed; 100 mm arm", 9)
                    f.text(20, 12, "2.0 N x 0.100 m = 0.20 N m", 9, TEAL)
                else:
                    f.text(
                        20,
                        25,
                        "Shown open. Sweep the complete arc by hand first.",
                        9,
                    )
        return
    if kind in {"stops", "damper"}:
        if kind == "damper":
            f.circle(*f.iso(0, 150, 140), 15, PALE)
            f.line(*f.iso(0, 150, 140), *f.iso(0, 150, 50), TEAL, 4)
            f.tag("D13 damper / H4", 330, 245, f.iso(0, 150, 140))
            f.tag("Reaction bracket to fixed frame", 20, 25, f.iso(0, 150, 50))
        else:
            f.block(90, -150, 100, 30, 20, 30, PALE)
            f.circle(*f.iso(110, -135, 135), 5, TEAL)
            f.tag("M06 bumper + FAB-M10", 20, 250, f.iso(105, -140, 125))
            f.tag("S01 switch + FAB-M13 cam", 290, 25, f.iso(110, -95, 135))
            f.text(285, 250, "Two endpoint sets", 9, TEAL)
            f.text(20, 30, "Cams AFTER clutch", 9, RED)


def inventory(f):
    labels = [
        ("C / CONTROL", "Pi + power + storage"),
        ("D / DRIVE", "Servo, clutch, rails"),
        ("FAB / MACHINED", "M01-M14 drawing IDs"),
        ("G / GUARD", "Extrusions + panels"),
        ("E / ELECTRICAL", "Relay + controls"),
        ("S / SENSORS", "Switches + probes"),
    ]
    for i, (title, subtitle) in enumerate(labels):
        x, y = 12 + (i % 3) * 170, 155 - (i // 3) * 115
        f.rect(x, y, 155, 100, LIGHT)
        f.text(x + 9, y + 79, title, 8.5, TEAL, True)
        f.text(x + 9, y + 12, subtitle, 7.6)
        f.rect(x + 20, y + 35, 50, 24, PALE)
        for k in range(3):
            f.circle(x + 90 + k * 15, y + 48, 5, GRAY)
    f.text(
        12,
        12,
        "Also sort W wire, F fasteners, T tools and optional O parts.",
        9,
    )


def fabricate(f):
    f.rect(75, 50, 325, 190, PALE)
    for x in range(120, 370, 16):
        for y in range(90, 210, 16):
            f.circle(x, y, 1.2, "#ffffff")
    for x in [88, 387]:
        for y in [62, 228]:
            f.circle(x, y, 3, "#ffffff")
    f.dim(75, 30, 400, 30, "500 mm")
    f.dim(425, 50, 425, 240, "400")
    f.tag("6.6 diameter / 25 mm pitch", 80, 263, (200, 160))
    f.text(
        12, 12, "FAB-M01 top view. Grid extent: 350 x 250. Schematic only.", 9
    )


def shoes(f):
    for x, label in [(115, "FIXED"), (340, "MOVING / H2")]:
        f.text(x - 60, 255, label, 10, TEAL, True)
        for y, w, h, fill in [
            (42, 130, 12, GRAY),
            (85, 42, 10, PALE),
            (130, 70, 25, PALE),
        ]:
            f.rect(x - w / 2, y, w, h, fill)
        f.rect(x + 1, 180, 34, 6, TEAL)
        f.line(x - 22, 205, x - 22, 55, INK, 4)
        f.rect(x - 32, 207, 20, 7, GRAY)
        if x == 340:
            f.rect(x - 35, 110, 26, 8, PALE)
            f.rect(x - 35, 67, 26, 8, PALE)
            f.arrow(x - 45, 140, x + 45, 140, both=True)
        f.arrow(x + 60, 195, x + 60, 60)
    f.tag("1 mm silicone", 25, 225, (132, 185))
    f.tag("FAB-M08 acetal", 20, 112, (90, 145))
    f.tag("Spacer / bushings / captive washer", 230, 22, (340, 90))
    f.text(230, 238, "Shoulder must not crush compliance", 8, RED)
    f.text(
        20,
        3,
        "Exploded concept; H2 defines shoulder, spacer "
        "and retention dimensions.",
        8,
    )


def guard(f, door=False):
    x, y, w, h = 120, 45, 260, 190
    f.poly(
        [
            (x, y + h),
            (x + 70, y + h + 32),
            (x + w + 70, y + h + 32),
            (x + w, y + h),
        ],
        LIGHT,
    )
    f.poly(
        [
            (x + w, y),
            (x + w + 70, y + 32),
            (x + w + 70, y + h + 32),
            (x + w, y + h),
        ],
        LIGHT,
    )
    f.rect(x, y, w, h, "#ffffff")
    for a, b in [
        ((x, y), (x, y + h)),
        ((x + w, y), (x + w, y + h)),
        ((x, y), (x + w, y)),
        ((x, y + h), (x + w, y + h)),
    ]:
        f.line(*a, *b, TEAL, 6)
    f.box(
        190,
        70,
        120,
        100,
        "Guarded fixture|>=25 mm from|moving envelope",
        LIGHT,
    )
    if door:
        f.poly(
            [(x, y), (x - 75, y + 10), (x - 75, y + h + 10), (x, y + h)], PALE
        )
        f.rect(113, 85, 14, 20, GRAY)
        f.rect(113, 185, 14, 20, GRAY)
        f.box(388, 110, 120, 60, "E05 switch|E06 captive key", PALE)
        f.circle(440, 67, 17, RED)
        f.circle(484, 67, 9, TEAL)
        f.text(410, 35, "E-stop / reset", 8)
        f.tag("Door + two hinges", 12, 15, (90, 120))
    else:
        f.tag("G01 2020 extrusion", 12, 270, (120, 235))
        f.tag("G03 4 mm polycarbonate", 12, 15, (310, 200))
        f.text(180, 20, "Approx. 600 W x 500 D x 400 H", 9)


def enclosure(f):
    f.rect(55, 30, 405, 225, LIGHT)
    f.line(75, 205, 440, 205, GRAY, 9)
    f.box(75, 145, 85, 88, "E08|2-pole DC|disconnect", PALE)
    f.box(178, 145, 63, 88, "E09|F1 / F2", PALE)
    f.box(262, 115, 95, 118, "E03|PNOZ X3|774310", GRAY)
    f.box(375, 145, 65, 88, "E11|TB", GRAY)
    f.box(75, 45, 150, 70, "12 V motor zone|D03 hub / D02 interface", PALE)
    f.box(260, 45, 180, 53, "24 V | opto barrier | 3.3 V", PALE)
    f.text(
        55, 265, "Enclosure layout concept - verify delivered clearances", 9
    )
    for x in [90, 165, 245, 330, 415]:
        f.circle(x, 30, 7, "#ffffff")


def power(f):
    rows = [
        (225, "12 V +", "pole A", "F1 3 A", "13 / 14", "23 / 24", "HUB +"),
        (140, "24 V +", "pole B", "F2 0.5 A", "B1", "33 / 34", "PERMIT"),
    ]
    for y, *labels in rows:
        for i, label in enumerate(labels):
            x = 7 + i * 85
            f.box(x, y - 32, 76, 32, label, PALE if i in [3, 4] else LIGHT)
            if i < 5:
                f.arrow(x + 76, y - 16, x + 84, y - 16)
        if y == 140:
            # 33 is a parallel fused supply branch, not a series B1 path.
            f.rect(338, 120, 12, 9, "#ffffff", "#ffffff")
            f.line(250, 124, 250, 165, TEAL)
            f.line(250, 165, 370, 165, TEAL)
            f.arrow(370, 165, 370, 142)
    f.text(
        10, 178, "12 V negative ---------------------------------> HUB GND", 9
    )
    f.text(
        10,
        90,
        "24 V negative -------------------------> B2 / opto LED return",
        9,
    )
    f.box(
        10,
        20,
        235,
        48,
        "Pi 27 W USB-C supply -> Pi|Independent of motor contacts",
        LIGHT,
    )
    f.box(
        265,
        20,
        243,
        48,
        "PNOZ contacts 13-14 + 23-24|Series motor-power interruption",
        PALE,
    )
    f.text(
        7, 263, "Power paths / keyed hub pinout checked on delivered part", 9
    )


def safety(f):
    for y, start, end in [(225, "S21", "S22"), (150, "S31", "S32")]:
        f.text(10, y, start, 10, TEAL, True)
        f.line(48, y + 3, 95, y + 3)
        f.box(
            95,
            y - 14,
            135,
            37,
            "E-stop NC " + ("A" if y == 225 else "B"),
            PALE,
        )
        f.line(230, y + 3, 275, y + 3)
        f.box(
            275,
            y - 14,
            140,
            37,
            "Guard NC " + ("A" if y == 225 else "B"),
            PALE,
        )
        f.line(415, y + 3, 462, y + 3)
        f.text(470, y, end, 10, TEAL, True)
    f.line(160, 211, 160, 173, MUTED, dash=True)
    f.line(345, 211, 345, 173, MUTED, dash=True)
    f.box(10, 30, 145, 60, "S11 ---- S12|Link for this circuit", LIGHT)
    f.box(
        175,
        30,
        190,
        60,
        "S33 -- NO reset -- S34|Monitored physical start",
        LIGHT,
    )
    f.box(385, 30, 120, 60, "S13 / S14|NO LINK", PALE)
    f.text(
        10,
        265,
        "R1 pp.12-13 + project series-device adaptation / H5 review",
        9,
    )
    f.text(
        10,
        110,
        "NC by function: both open on demand. Verify device terminal IDs.",
        8,
    )


def opto(f):
    f.box(15, 175, 110, 55, "PNOZ 34|24 V status", PALE)
    f.box(150, 175, 90, 55, "2 kohm|0.5 W", LIGHT)
    f.arrow(125, 202, 150, 202)
    f.box(265, 150, 100, 95, "LTV-817C|1 A / 2 K|4 C / 3 E", PALE)
    f.arrow(240, 202, 265, 202)
    f.line(290, 150, 290, 125)
    f.line(290, 125, 30, 125)
    f.text(15, 108, "K -> 24 V negative", 9)
    f.text(15, 85, "1N4148 reverse across LED:", 8.5)
    f.text(15, 70, "diode K -> LED A; diode A -> LED K", 8)
    f.line(375, 40, 375, 260, ORANGE, 1, True)
    f.text(385, 247, "C -> Pi 3.3 V", 8.5)
    f.line(365, 225, 405, 225, TEAL)
    f.line(365, 172, 405, 172, TEAL)
    f.circle(405, 172, 3, TEAL)
    f.text(410, 174, "E / node", 8.5)
    f.box(415, 115, 90, 32, "1 kohm", LIGHT)
    f.line(405, 172, 405, 130)
    f.line(405, 130, 415, 130)
    f.text(415, 98, "-> GPIO17", 8.5)
    f.text(415, 84, "physical 11", 8.5)
    f.line(405, 130, 405, 55)
    f.text(410, 55, "10 kohm", 8)
    f.text(410, 40, "to Pi GND", 8)
    f.text(
        15,
        20,
        "R8 pin functions shown; verify pin-1 mark on delivered package.",
        9,
        RED,
    )


def sensors(f):
    f.text(10, 261, "Repeat endpoint circuit x2", 10, TEAL, True)
    f.box(10, 190, 105, 40, "3.3 V -> COM", LIGHT)
    f.box(145, 190, 75, 40, "S01 NO", PALE)
    f.box(270, 190, 85, 40, "1 kohm", LIGHT)
    f.box(390, 190, 120, 40, "GPIO27 / 22", PALE)
    for a, b in [(115, 145), (220, 270), (355, 390)]:
        f.arrow(a, 210, b, 210)
    f.line(245, 210, 245, 166)
    f.text(190, 150, "10 kohm -> Pi ground", 9)
    f.text(
        10,
        126,
        "Two powered DS18B20 probes / one shared pullup",
        10,
        TEAL,
        True,
    )
    f.box(
        15,
        20,
        125,
        80,
        "CASE probe|VDD = 3.3 V|GND = Pi GND|DQ = data bus",
        PALE,
    )
    f.box(
        190,
        20,
        125,
        80,
        "AMBIENT probe|VDD = 3.3 V|GND = Pi GND|DQ = data bus",
        PALE,
    )
    f.line(140, 40, 175, 40)
    f.line(175, 40, 175, 110)
    f.line(175, 110, 350, 110)
    f.line(315, 40, 350, 40)
    f.line(350, 40, 350, 110)
    f.arrow(350, 75, 390, 75)
    f.text(390, 75, "GPIO4 / pin 7", 9)
    f.text(370, 45, "4.7 kohm to 3.3 V", 8.5)
    f.line(350, 45, 365, 45)


def pi(f):
    f.box(
        10,
        95,
        150,
        140,
        "C01 Raspberry Pi 5|C03 cooler / case|C04 storage|C02 independent PSU",
        PALE,
    )
    f.box(205, 160, 110, 65, "D02 U2D2|3-pin TTL", LIGHT)
    f.box(365, 160, 140, 65, "D03 power hub|Switched 12 V", LIGHT)
    f.arrow(160, 190, 205, 190)
    f.text(167, 202, "USB", 8)
    f.arrow(315, 190, 365, 190)
    f.box(365, 55, 140, 60, "D01 XM430-T|Connect power OFF", PALE)
    f.arrow(430, 160, 430, 115)
    f.box(
        195,
        15,
        140,
        100,
        "HEADER / physical pins|1: 3.3 V    6: ground|7: data / GPIO4|"
        "11: permit / GPIO17|13: open / GPIO27|15: closed / GPIO22",
        LIGHT,
    )
    f.arrow(160, 120, 195, 90)
    f.text(
        10,
        260,
        "Identify pin 1 from board markings; avoid mirrored connector views.",
        9,
    )


def meter(f, energized=False):
    f.box(
        20,
        75,
        180,
        150,
        "KEYED HUB OUTPUT|Motor disconnected|Measure actual + / GND",
        LIGHT,
    )
    f.rect(315, 65, 155, 175, PALE)
    f.rect(330, 175, 125, 40, "#ffffff")
    f.text(340, 188, "12.0 V" if energized else "POWER OFF", 12, TEAL, True)
    f.circle(390, 130, 25, GRAY)
    f.line(380, 70, 275, 35, RED, 2)
    f.line(275, 35, 180, 100, RED, 2)
    f.line(420, 70, 265, 20, INK, 2)
    f.line(265, 20, 180, 130, INK, 2)
    f.text(20, 255, "Voltage mode only on energized circuits", 10, RED, True)
    if energized:
        f.text(20, 8, "Guard or E-stop open -> motor power absent", 9)
    else:
        f.text(
            20, 8, "Continuity mode only after zero-voltage verification", 9
        )


def software(f):
    f.box(
        20,
        85,
        225,
        155,
        "Pi / single controller|src/foldbench/|Pipenv locked environment|"
        "Local /docs API interface|One worker; no reload",
        PALE,
    )
    f.box(
        300,
        160,
        200,
        80,
        "INSTALLATION CONFIG|Serial + GPIO chip|Case/ambient probe serials",
        LIGHT,
    )
    f.box(
        300,
        45,
        200,
        80,
        "CALIBRATION RECORD|Measured angles/ticks/limits|"
        "commissioned=false initially",
        LIGHT,
    )
    f.arrow(300, 195, 245, 195)
    f.arrow(300, 85, 245, 120)
    f.text(
        20,
        30,
        "Simulation -> static checks -> dummy authorization -> phone trial",
        9,
        TEAL,
    )


def index_diagram(f):
    f.text(
        12,
        262,
        "INDEXING SETUP: MOTOR DISCONNECTED FROM FIXTURE",
        10,
        RED,
        True,
    )
    f.box(
        20,
        130,
        90,
        80,
        "D01 motor|Torque enabled|only by local|index command",
        PALE,
    )
    f.rect(115, 145, 12, 50, GRAY)
    f.rect(135, 152, 22, 36, PALE)
    f.line(157, 170, 185, 170, TEAL, 5)
    f.box(265, 146, 60, 48, "D07|clutch", GRAY)
    f.line(325, 170, 440, 170, INK, 5)
    f.rect(355, 135, 30, 70, GRAY)
    f.line(440, 170, 485, 215, INK, 5)
    f.arrow(193, 170, 255, 170, ORANGE, both=True)
    f.text(185, 135, "OPEN GAP", 10, ORANGE, True)
    f.tag("D04 horn / FAB-M11 adapter", 15, 235, (138, 188))
    f.tag("D08 supported output stub", 335, 235, (369, 204))
    f.box(
        20,
        25,
        220,
        70,
        "MOTOR ONLY: example tick 1024|No phone; coupling visibly open|"
        "Guard and safety permit healthy",
        PALE,
    )
    f.box(
        265,
        25,
        245,
        70,
        "FIXTURE: closed-angle reference|After indexing: isolate power, "
        "then|reconnect without shifting either side",
        LIGHT,
    )


def force_diagram(f):
    f.text(
        12,
        263,
        "A / PHONE FIT - POWER OFF, CLUTCH DISENGAGED",
        9.5,
        TEAL,
        True,
    )
    f.rect(65, 185, 130, 45, GRAY)
    f.rect(205, 185, 130, 45, PALE)
    f.line(200, 172, 200, 245, MUTED, 1, True)
    f.arrow(220, 168, 320, 168, both=True)
    f.text(355, 213, "Radial float", 9)
    f.text(355, 196, ">=2 mm reserve", 9)
    f.text(65, 237, "Stationary half", 8)
    f.text(210, 237, "Moving half", 8)
    f.line(10, 148, 510, 148, GRAY)
    f.text(
        12, 132, "B / CLUTCH BREAKAWAY TEST - PHONE REMOVED", 9.5, TEAL, True
    )
    f.circle(95, 53, 16, PALE)
    f.line(95, 53, 270, 53, INK, 5)
    f.circle(270, 53, 4, TEAL)
    f.arrow(270, 53, 270, 109, ORANGE)
    f.dim(95, 25, 270, 25, "100 mm")
    f.text(12, 79, "Clutch axis", 8.5)
    f.text(290, 90, "Gauge force perpendicular to arm", 8.5)
    f.text(290, 68, "2.0 N x 0.100 m = 0.20 N m", 9)
    f.text(290, 44, "Measure both directions repeatedly", 8.5)
    f.text(
        12,
        5,
        "Restrain the other clutch side with a fixture, never fingers.",
        8.5,
    )


def draw_figure(c, kind, path):
    f = Figure(c)
    if kind == "index":
        index_diagram(f)
    elif kind == "force":
        force_diagram(f)
    elif kind in {
        "base",
        "towers",
        "yoke",
        "drive",
        "rails",
        "cradle",
        "stops",
        "damper",
        "index",
        "dummy",
        "force",
        "release",
    }:
        mechanical(f, kind)
    elif kind == "inventory":
        inventory(f)
    elif kind == "fabricate":
        fabricate(f)
    elif kind == "shoes":
        shoes(f)
    elif kind in {"guard", "door"}:
        guard(f, kind == "door")
    elif kind == "enclosure":
        enclosure(f)
    elif kind == "power":
        power(f)
    elif kind == "safety":
        safety(f)
    elif kind == "opto":
        opto(f)
    elif kind == "sensors":
        sensors(f)
    elif kind == "pi":
        pi(f)
    elif kind in {"meter", "power_test"}:
        meter(f, kind == "power_test")
    elif kind == "software":
        software(f)
    else:
        raise ValueError(kind)
    f.write(path)


def footer(c, page):
    key = f"page-{page}"
    c.bookmarkPage(key)
    c.addOutlineEntry(c._guide_heading, key, level=0)
    c.setStrokeColor(colour(GRAY))
    c.line(36, 43, W - 36, 43)
    c.setFont("Guide", 7)
    c.setFillColor(colour(MUTED))
    c.drawString(36, 28, "foldatron  /  ASSEMBLY COMPANION A1  /  Prototype")
    c.drawRightString(W - 36, 28, f"{page:02d}")


def title(c, label, heading, subtitle="", heading_size=23):
    c._guide_heading = f"{label}: {heading}"
    para(c, html.escape(label), 36, H - 34, W - 72, 9, 12, True)
    bottom = para(
        c,
        html.escape(heading),
        36,
        H - 57,
        W - 72,
        heading_size,
        heading_size + 5,
        True,
    )
    if subtitle:
        bottom = para(c, subtitle, 36, bottom - 10, W - 72, 9.5, 13)
    return bottom - 20


def table(c, headers, rows, top, widths, size=8.2):
    style = ParagraphStyle(
        "cell",
        fontName="Guide",
        fontSize=size,
        leading=size + 3,
        textColor=colour(INK),
        splitLongWords=True,
    )
    cells = [[Paragraph(html.escape(str(v)), style) for v in headers]]
    cells += [
        [Paragraph(html.escape(str(v)), style) for v in row] for row in rows
    ]
    t = Table(cells, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colour(PALE)),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colour(LIGHT)],
                ),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, 0), (-1, -1), 0.3, colour(GRAY)),
            ]
        )
    )
    _, height = t.wrap(W - 72, 1000)
    if top - height < 60:
        raise ValueError(f"Table overflows page: {headers}")
    t.drawOn(c, 36, top - height)
    return top - height


HOLDS = [
    (
        "H1 / yoke",
        "FAB-M03/M04, hubs, horn, bearings",
        "Resolve arm/hub center alignment and joint edge distances. The old "
        "190 mm crossbar spans support centers +/-95, but hole rows at +/-6 "
        "from those centers can fall beyond its ends. The arm envelope also "
        "puts outer holes too close to an edge. Release corrected blanks, "
        "joints and vendor mounting patterns before machining.",
    ),
    (
        "H2 / float",
        "Rails, carriers, shoes and shoulder-screw stack",
        "Release carrier connections, rail/carriage screws, travel retainers "
        "and bushing/spacer dimensions. Demonstrate +/-6 mm radial and "
        "approximately +/-2 mm tangential travel without losing retention.",
    ),
    (
        "H3 / guard",
        "Frame joints, outriggers, panels and controls",
        "Release load-bearing supports from 500 x 400 base to wider guard, "
        "frame overlaps, panel/door hole patterns and control mounting panel. "
        "G01 has only 480 mm stock remaining before saw kerfs after its "
        "listed frame cuts; recheck extra material and fasteners.",
    ),
    (
        "H4 / drive",
        "Configured clutch and damper",
        "Confirm EAS12 configuration and low-torque adjustment with vendor; "
        "select the actual damper and design its stationary reaction bracket "
        "and output coupling. These are not fully specified purchased kits.",
    ),
    (
        "H5 / electrical",
        "Safety circuit and permit board",
        "Approve relay revision, series-device fault behavior, fuses/inrush, "
        "device contact IDs and optocoupler package pin map. Verify actual "
        "motor-power removal and no automatic restart.",
    ),
]

FABRICATION = [
    ("M01", "1", "Base 500 x 400 x 8; grid/foot holes: step 02", "BOM M01"),
    (
        "M02",
        "2",
        "Tower 100 x 180 x 8 + 100 x 50 x 6 foot; vendor adapters",
        "BOM M02",
    ),
    (
        "M03",
        "2",
        "Arm 125 x 25 x 6 envelope; H1 revised joint required",
        "BOM M02",
    ),
    (
        "M04",
        "1",
        "Crossbar 190 x 25 x 6 envelope; H1 revision required",
        "BOM M02",
    ),
    ("M05", "1", "Moving plate 100 x 135 x 4; four 4.5 x 20 slots", "BOM M02"),
    (
        "M06",
        "1",
        "Fixed plate 100 x 135 x 4; measured camera relief",
        "BOM M02",
    ),
    (
        "M07",
        "2",
        "Riser 100 x 125 x 6 + 100 x 40 x 6 foot; shim height",
        "BOM M02",
    ),
    (
        "M08",
        "8",
        "Acetal shoe 20 x 15 x 8; 4.5 x 10 slot; measured contour",
        "BOM M03",
    ),
    ("M09", "1", "Shelf 100 x 100 x 6 + two 100 mm slotted angles", "BOM M02"),
    (
        "M10",
        "4",
        "Stop/switch angle 40 x 25 x 3; 4.5 x 15 base slots",
        "BOM M02",
    ),
    (
        "M11",
        "1",
        "Adapter diameter 30 x 10; 6 H7 split bore; vendor horn pattern",
        "BOM M02",
    ),
    (
        "M12",
        "2",
        "Guide carrier 100 x 25 x 4; rail pattern and joints H2",
        "BOM M02",
    ),
    (
        "M13",
        "2",
        "Acetal cam 20 x 15 x 3; output-side adjustable fixing",
        "BOM M02*",
    ),
    (
        "M14",
        "5",
        "4 mm panels: 560 x 360 (2), 460 x 360 (2), 560 x 460 (1)",
        "BOM G03",
    ),
]

WIRES = [
    ("P12-01", "12 V +", "DC pole A input", "18 AWG"),
    (
        "P12-02/03",
        "DC pole A output / F1 output",
        "F1 input / relay 13",
        "18 AWG",
    ),
    ("P12-04/05", "Relay 14 / relay 24", "Relay 23 / hub +", "18 AWG"),
    ("P12-00", "12 V negative", "Hub GND", "18 AWG"),
    (
        "P24-01/02",
        "24 V + / DC pole B output",
        "DC pole B input / F2 input",
        "22 AWG",
    ),
    ("P24-03/04", "F2 output", "Relay B1 and 33 (branch)", "22 AWG"),
    ("P24-00", "24 V negative", "Relay B2 / opto LED return", "22 AWG"),
    ("SA-1/2/3", "S21 -> E-stop A -> guard A", "S22 (series chain)", "22 AWG"),
    (
        "SB-1/2/3",
        "S31 -> E-stop B -> guard B",
        "S32 (separate series chain)",
        "22 AWG",
    ),
    ("SR-1/2", "S33 -> reset NO", "S34", "22 AWG"),
    ("SL-1", "S11", "S12 link for selected R1 circuit", "22 AWG"),
    (
        "ST-1/2",
        "Relay 34 -> 2 kohm -> LED A",
        "LED K -> 24 V negative",
        "24-26 AWG",
    ),
    ("PI-01/06", "Pi pins 1 / 6", "3.3 V / ground signal buses", "24-26 AWG"),
    (
        "PI-11",
        "Permit emitter node via 1 kohm",
        "GPIO17 / physical 11",
        "24-26 AWG",
    ),
    (
        "PI-13/15",
        "Open / closed NO node via 1 kohm",
        "GPIO27 / 22, physical 13 / 15",
        "24-26 AWG",
    ),
    (
        "PI-07",
        "Both probe DQ; 4.7 kohm pullup",
        "GPIO4 / physical 7",
        "24-26 AWG",
    ),
]

SOURCES = [
    (
        "R1",
        "Pilz PNOZ X3 20547-EN-10, pp.12-13; wiring authority",
        "https://www.pilz.com/download/open/PNOZ_X3_Operating_Manual_20547-EN-10.pdf",
    ),
    (
        "R2",
        "ROBOTIS XM430-W350: model, modes, tick scale and watchdog",
        "https://emanual.robotis.com/docs/en/dxl/x/xm430-w350/",
    ),
    (
        "R3",
        "ROBOTIS U2D2: TTL connection and external motor power",
        "https://emanual.robotis.com/docs/en/parts/interface/u2d2/",
    ),
    (
        "R4",
        "OMRON D4NS: delivered switch/key mounting and contact data",
        "https://www.ia.omron.com/data_pdf/cat/d4ns_d4ns-sk_ds_e_9_9_csm1235.pdf",
    ),
    (
        "R5",
        "Analog Devices DS18B20: powered 1-Wire connection",
        "https://www.analog.com/media/en/technical-documentation/data-sheets/ds18b20.pdf",
    ),
    (
        "R6",
        "Raspberry Pi: physical GPIO header and 3.3 V interface",
        "https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#gpio",
    ),
    (
        "R7",
        "Dynatect Slip-Ease: EAS12 configuration; obtain accepted quote",
        "https://www.dynatect.de/en/product/slip-ease-slip-clutches/",
    ),
    (
        "R8",
        "Lite-On LTV-817 family datasheet, package pin functions "
        "(manufacturer document hosted by Datasheets.com)",
        "https://www.datasheets.com/lite-on/ltv-817s-b/datasheet.pdf",
    ),
]


def overview(c):
    f = Figure(c)
    f.iso = lambda x, y, z: (
        205 + 0.35 * x + 0.20 * y,
        60 - 0.10 * x + 0.13 * y + 0.38 * z,
    )
    f.base()
    f.towers()
    f.yoke(True)
    f.block(-90, -60, 130, 85, 120, 5, GRAY)
    f.block(5, -60, 130, 85, 120, 5, PALE)
    f.block(-20, -200, 120, 40, 40, 40, TEAL)
    f.block(330, -160, 0, 150, 130, 190, LIGHT)
    f.block(330, 10, 0, 90, 60, 40, PALE)
    # Guard edges only, so the internal mechanism remains visible.
    for x in [-300, 300]:
        for y in [-250, 250]:
            f.line(*f.iso(x, y, 0), *f.iso(x, y, 400), MUTED, 1.4)
    for z in [0, 400]:
        for x in [-300, 300]:
            f.line(*f.iso(x, -250, z), *f.iso(x, 250, z), MUTED, 1.4)
        for y in [-250, 250]:
            f.line(*f.iso(-300, y, z), *f.iso(300, y, z), MUTED, 1.4)
    f.tag("G01-G04 guard / front door", 12, 272, f.iso(-300, -250, 350))
    f.tag("Fixed + floating cradles", 10, 210, f.iso(50, 0, 135))
    f.tag("D01 drive + D07 clutch", 10, 20, f.iso(0, -180, 140))
    f.tag("E10 electrical panel", 350, 220, f.iso(400, -90, 190))
    f.tag("C01 Raspberry Pi", 355, 150, f.iso(370, 40, 40))
    f.write(DATA / "assets/overview.svg")


def intro(c, steps):
    title(
        c,
        "foldatron / ASSEMBLY COMPANION A1",
        "Build the bench",
        "Illustrated engineering work instructions | 26 numbered operations",
    )
    c.saveState()
    c.translate(36, 350)
    overview(c)
    c.restoreState()
    para(
        c,
        "One station. From sorted parts to a supervised phone trial.",
        36,
        330,
        W - 72,
        17,
        23,
        True,
    )
    para(
        c,
        "Separate from the FoldBench design-and-assembly document. "
        "This book adds assembly order, exploded views, part callouts, "
        "wire schedules and inspection records. The Python package "
        "remains <b>foldbench</b>.",
        36,
        264,
        W - 72,
        11,
        16,
    )
    c.setFillColor(colour(PALE))
    c.rect(36, 111, W - 72, 90, fill=1, stroke=0)
    para(
        c,
        "PROTOTYPE / ENGINEERING RELEASE REQUIRED",
        48,
        185,
        W - 96,
        10,
        14,
        True,
    )
    para(
        c,
        "Physical hardware has not been built or validated. Close H1-H5 "
        "before the affected work. Illustrations show assembly intent; "
        "they are not scale templates or collision-checked CAD.",
        48,
        160,
        W - 96,
        10,
        14,
    )
    para(
        c,
        "Units: mm unless stated. Published 4 November 2026. "
        "Build serial: ____________________",
        36,
        87,
        W - 72,
        9,
        13,
    )
    footer(c, 1)
    c.showPage()

    y = title(c, "READ FIRST", "How to use this book")
    y = (
        para(
            c,
            "Read the entire operation before picking up a tool. The "
            "parts strip identifies the kit. Teal highlights the assembly "
            "of interest, gray is context, arrows show fit/direction, "
            "and dashed lines are alignments or signal relationships. "
            "Colour is supplementary: every critical item is labeled.",
            36,
            y,
            W - 72,
            10,
            15,
        )
        - 20
    )
    rows = [
        (
            "01-02",
            "Prepare",
            "Inventory, actual specimen measurements, fabrication",
            "5-6",
        ),
        (
            "03-11",
            "Mechanics",
            "Base, towers, yoke, drive, float, shoes, stops, damper",
            "7-15",
        ),
        (
            "12-13",
            "Guard",
            "Frame, panels, door and external controls",
            "16-17",
        ),
        (
            "14-19",
            "Electrical",
            "Enclosure, power, interlocks, signals and Pi",
            "18-23",
        ),
        (
            "20-26",
            "Commission",
            "Static checks, indexing, dummy and phone trials",
            "24-30",
        ),
        (
            "A-D",
            "Bench references",
            "Wire list, fasteners, software, signed records",
            "31-35",
        ),
    ]
    y = (
        table(
            c, ["Steps", "Stage", "Work", "Pages"], rows, y, [52, 80, 335, 56]
        )
        - 24
    )
    y = para(c, "Before starting", 36, y, W - 72, 15, 19, True) - 12
    for text in [
        "Work on a rigid, level bench. Provide access to all supply plugs "
        "and the E-stop. Keep the phone away until step 25.",
        "Use the complete 60-line procurement BOM in hardware/BOM.md. "
        "This companion repeats the parts needed at each operation; it "
        "does not certify that provisional mounting allowances are complete.",
        "Use caliper/angle gauge, straightedge/square, low-range torque "
        "tool, hex keys, crimp tools and meter. Add an indicator/height "
        "gauge, straight 6 mm setup rod and timing/video reference if not "
        "already available; these are additional metrology aids.",
        "Isolate all supplies before adjusting mechanical parts or "
        "wiring. The Pi supply is independent of the motor disconnect. "
        "Restrain gravity-loaded parts before releasing a clamp/coupling.",
    ]:
        y = para(c, text, 36, y, W - 72, 9.5, 14) - 12
    footer(c, 2)
    c.showPage()

    y = title(
        c,
        "FABRICATION HOLD POINTS",
        "Release before cutting",
        "This booklet exposes gaps in the previous envelope design. "
        "An engineer must close the items below, not infer hidden dimensions.",
    )
    y = (
        table(
            c,
            ["Hold", "Affected parts", "Required engineering release"],
            HOLDS,
            y,
            [66, 122, 335],
            8.5,
        )
        - 18
    )
    para(
        c,
        "Retain signed drawings with this booklet. Blank fields are "
        "intentional measurements, not permission to guess. The assembly "
        "figures are conceptual and may show revised joint proportions; "
        "they do not supersede the released fabrication drawing. Update "
        "the stock/fastener order after H1-H4 are resolved.",
        36,
        y,
        W - 72,
        9.5,
        14,
    )
    footer(c, 3)
    c.showPage()

    y = title(
        c,
        "PART IDENTIFICATION",
        "Fabricated-part register",
        "Prefix every drawing identifier with FAB. BOM-M03 is a "
        "shoe blank; FAB-M03 is a yoke arm. Never interchange them.",
    )
    y = (
        table(
            c,
            ["FAB ID", "Qty", "Reference stock / operation", "Procurement"],
            FABRICATION,
            y,
            [53, 30, 340, 100],
            8,
        )
        - 16
    )
    para(
        c,
        "*FAB-M13 must be acetal although grouped in the plate-stock "
        "allowance. General metal: 6061-T6. Contact shoes: acetal plus "
        "1 mm silicone. Stock sizes are Rev A references; H1/H2 may "
        "require revised blanks and additional retainers/brackets. "
        "Vendor patterns and fastener torques follow delivered parts.",
        36,
        y,
        W - 72,
        9,
        13,
    )
    footer(c, 4)
    c.showPage()


def step_page(c, index, step):
    width = pdfmetrics.stringWidth(step["title"], "GuideBold", 23)
    heading_size = min(23, 23 * (W - 73) / width)
    title(
        c,
        f"{index:02d} / {step['phase']}",
        step["title"],
        heading_size=heading_size,
    )
    c.setFillColor(colour(LIGHT))
    c.rect(36, 670, W - 72, 64, fill=1, stroke=0)
    bottom = para(
        c,
        "<b>PARTS</b>  " + html.escape(step["parts"]),
        45,
        726,
        W - 90,
        8.5,
        11,
    )
    bottom = para(
        c,
        "<b>TOOLS</b>  " + html.escape(step["tools"]),
        45,
        bottom - 4,
        W - 90,
        8.3,
        11,
    )
    if bottom < 673:
        raise ValueError(f"Parts strip overflow: step {index}")
    c.saveState()
    c.translate(37, 407)
    c.scale(1, 0.9)
    draw_figure(c, step["figure"], DATA / f"assets/step-{index:02d}.svg")
    c.restoreState()
    c.setStrokeColor(colour(GRAY))
    c.line(36, 404, W - 36, 404)
    y = 390
    for number, action in enumerate(step["actions"], 1):
        para(c, f"{number}.", 36, y, 19, 10, 13, True)
        y = para(c, html.escape(action), 58, y, W - 94, 9.2, 12.6) - 9
    if y < 145:
        raise ValueError(f"Action text overflow step {index}: y={y}")
    c.setFillColor(colour(PALE))
    c.rect(36, 77, W - 72, 62, fill=1, stroke=0)
    para(c, "CHECK BEFORE CONTINUING", 46, 129, W - 92, 8.5, 11, True)
    b = para(c, html.escape(step["check"]), 46, 113, W - 92, 8.8, 12)
    if b < 79:
        raise ValueError(f"Acceptance box overflow step {index}")
    para(c, html.escape(step["record"]), 36, 65, W - 72, 8, 10)
    footer(c, index + 4)
    c.showPage()


def appendices(c):
    y = title(
        c,
        "APPENDIX A / WIRE SCHEDULE",
        "Label both ends",
        "Project wire labels below supplement the power-net IDs in "
        "the design guide. Confirm actual terminal and connector markings.",
    )
    y = (
        table(
            c,
            ["Wire IDs", "From / path", "To", "Size"],
            WIRES,
            y,
            [68, 186, 204, 65],
            7.8,
        )
        - 16
    )
    para(
        c,
        "Use one verified optocoupler package pin map with step 17. "
        "Pi input nodes each have 10 kohm to Pi ground; each GPIO line "
        "has 1 kohm in series. Endpoint COM and opto collector use 3.3 V. "
        "The two probe grounds use Pi ground, not the isolated 24 V return.",
        36,
        y,
        W - 72,
        9,
        13,
    )
    footer(c, 31)
    c.showPage()

    y = title(
        c,
        "APPENDIX B / FASTENERS",
        "Choose the length from the joint",
        "Inventory kits contain common lengths, not a fully released "
        "bolt schedule. Record each final joint before ordering extras.",
    )
    rows = [
        (
            "Base/feet",
            "4 x M6 at four corner holes",
            "Foot stud/insert depth + plate + washers/lock",
        ),
        (
            "Tower/feet/adapters",
            "M6 reference; quantity per released drawing",
            "Bearing and angle patterns from delivered parts",
        ),
        (
            "Yoke outer joints",
            "4 x M4 total, two per joint",
            "6 mm arm + 6 mm crossbar + washers + locknut; H1",
        ),
        (
            "Fixed/moving plates",
            "Four adjustment slots per plate",
            "M4 shoulder or standard screw as joint requires; H2",
        ),
        (
            "Moving shoes",
            "4 x M4 shoulder-screw assemblies",
            "8 bushings, spacers and capture washers; H2 stack",
        ),
        (
            "Rails/horn/servo/hubs",
            "Use component-specific screws",
            "No assumed thread, depth or tightening torque",
        ),
        (
            "Stop/switch brackets",
            "2 stops + 2 switches, four brackets",
            "M4 bracket slots; switch screws from datasheet",
        ),
        (
            "Guard/enclosure",
            "24 corner brackets + panel clips/hardware",
            "Matching M5 slot hardware; H3 determines extras",
        ),
    ]
    y = (
        table(
            c,
            ["Joint", "Known quantity / size", "Selection rule"],
            rows,
            y,
            [104, 180, 239],
            8.3,
        )
        - 20
    )
    y = (
        para(
            c,
            "A bolt must clamp before it bottoms",
            36,
            y,
            W - 72,
            14,
            19,
            True,
        )
        - 9
    )
    y = (
        para(
            c,
            "For a through joint, add all gripped material, washers and "
            "the actual locking-nut thickness, then allow the locking "
            "element's specified thread protrusion. Example: two 6 mm "
            "plates already consume 12 mm before washers/nut; an M4x16 "
            "from F02 may be too short. Confirm the stack and procure "
            "the correct length. For tapped joints, verify engagement "
            "and remaining blind-hole clearance from the component drawing.",
            36,
            y,
            W - 72,
            10,
            14,
        )
        - 14
    )
    table(
        c,
        [
            "Joint ID / qty",
            "Selected fastener",
            "Torque + authority",
            "Initials",
        ],
        [["____________", "____________", "____________", "______"]] * 4,
        y,
        [110, 150, 190, 73],
        8.3,
    )
    footer(c, 32)
    c.showPage()

    y = title(
        c,
        "APPENDIX C / SOFTWARE AT THE BENCH",
        "Bring-up reference",
        "Run from the repository with Python 3.12 and Pipenv. "
        "See README.md for account, service and network configuration.",
    )
    commands = [
        "PIPENV_VENV_IN_PROJECT=1 pipenv sync --dev",
        "pipenv run test",
        "# Simulation: generate a private API key first",
        "export FOLDBENCH_MODE=simulation",
        "pipenv run serve",
        "# Stop service / server before the hardware probe",
        "pipenv run python -m foldbench.probe \\",
        "  --port /dev/serial/by-id/ACTUAL_U2D2_ID",
        "# Only after physically uncoupling the motor:",
        "pipenv run python -m foldbench.probe \\",
        "  --port /dev/serial/by-id/ACTUAL_U2D2_ID \\",
        "  --index-tick 1024 --uncoupled \\",
        "  --gpio-chip /dev/ACTUAL_HEADER_CHIP",
    ]
    c.setFillColor(colour(LIGHT))
    c.rect(36, y - 194, W - 72, 194, fill=1, stroke=0)
    c.setFont("Guide", 8.1)
    c.setFillColor(colour(INK))
    for index, line in enumerate(commands):
        c.drawString(46, y - 18 - index * 13, line)
    y -= 215
    rows = [
        (
            "Calibration",
            "File outside live API; archive example; record actual "
            "angles/ticks, current, speed and temperature limits.",
        ),
        (
            "Hardware mode",
            "FOLDBENCH_MODE=hardware; verify serial, GPIO chip and both "
            "probe paths. Stop service before editing configuration.",
        ),
        (
            "API key",
            "Set FOLDBENCH_API_KEY to a random secret; authorize "
            "X-API-Key in /docs. Keep environment file access restricted.",
        ),
        (
            "Trial request",
            "POST /v1/runs; new Idempotency-Key. specimen=actual identifier, "
            "cycles=1, speed_deg_s=5, dwell_s=2, "
            "current_limit_ma=measured value.",
        ),
        (
            "Local limits",
            "Initial design ceilings: 15 deg/s, 150 mA; commissioned "
            "values must be justified. Absolute design bounds: "
            "350 mA, 0.50 N m clutch.",
        ),
        (
            "Thermal record",
            "Initial case 40 C, motor 55 C, ambient 10-30 C. These "
            "are starting choices, not validated phone limits.",
        ),
    ]
    y = (
        table(
            c, ["Item", "Required installation work"], rows, y, [95, 428], 8.4
        )
        - 16
    )
    para(
        c,
        "The trial flag and record authorize motion, not safety by "
        "themselves. Use distinct EMPTY-FIXTURE and PHONE-TRIAL records; "
        "sign routine release only after the staged tests pass.",
        36,
        y,
        W - 72,
        9,
        13,
    )
    footer(c, 33)
    c.showPage()

    y = title(
        c,
        "APPENDIX D / STATIC ACCEPTANCE",
        "Record the actual results",
        "Station serial: ______________  Date: __________  "
        "Inspector: __________________",
    )
    rows = [
        ("H1-H5 drawings", "All affected interfaces signed/revisioned", ""),
        (
            "Mechanical alignment",
            "Bearing <=0.2 mm; drive target <=0.1 mm",
            "",
        ),
        (
            "Float and retention",
            "+/-6 mm radial; >=2 mm reserve; captive shoes",
            "",
        ),
        (
            "Cold continuity",
            "Wire list/polarity matches; supplies isolated",
            "",
        ),
        (
            "24 V side / Pi side",
            "No intentional connection across optocoupler",
            "",
        ),
        ("Guard open; no servo", "Hub power absent; permit low", ""),
        ("E-stop pressed; no servo", "Hub power absent; permit low", ""),
        ("Close/release only", "No power restoration without valid reset", ""),
        ("Valid reset", "Hub nominal 12 V; permit >2.0 and <=3.3 V", ""),
        ("Held reset / restart", "Cannot defeat monitored-start behavior", ""),
        (
            "Each safety channel",
            "Independently tested by approved procedure",
            "",
        ),
        ("Endpoint states", "Only correct endpoint high; open wire low", ""),
        (
            "Probe mapping",
            "Two distinct CRC-valid serials; case attachment",
            "",
        ),
        (
            "Uncoupled identity",
            "Model 1020, firmware >=38, ID 1, 57600 baud",
            "",
        ),
    ]
    y = (
        table(
            c,
            ["Check", "Acceptance", "Measured result / initials"],
            rows,
            y,
            [130, 235, 158],
            8.4,
        )
        - 20
    )
    para(
        c,
        "Authorization for supervised empty/dummy motion: "
        "________________________________<br/><br/>"
        "Unresolved items / restrictions: "
        "________________________________________________<br/><br/>"
        "Reviewer and date: __________________________________________",
        36,
        y,
        W - 72,
        9.5,
        16,
    )
    footer(c, 34)
    c.showPage()

    y = title(
        c,
        "APPENDIX D / DYNAMIC ACCEPTANCE",
        "Release the assembled station",
        "All motion tests use a closed guard and a reachable E-stop. "
        "Retain the full commissioning record in docs/COMMISSIONING.md.",
    )
    rows = [
        (
            "Motor stop / gravity settling",
            "Time: ______   Distance/angle: ______",
        ),
        ("Guard access timing", "Access prevented until stopped: ______"),
        (
            "USB / Pi process / Pi power loss",
            "Fault/no automatic resume: ______",
        ),
        (
            "Endpoint/probe failures + dummy jam",
            "Fault/no false count: ______",
        ),
        (
            "100 / 1,000 dummy cycles",
            "Count/wear/temperature evidence: ______",
        ),
        (
            "Phone fit at reachable angles",
            "Slide reserve / no contact / no slip: ______",
        ),
        (
            "Clutch bidirectional repeatability",
            "CW: ____ CCW: ____ spread: ____ N m",
        ),
        (
            "Phone trial 1 / 10 / 100 cycles",
            "Display/touch/frame/hinge inspections: ______",
        ),
        ("Installed calibration", "Record ID: ______  Git commit: ______"),
        (
            "Routine supervised release",
            "Reviewer/date: ________________________",
        ),
    ]
    y = (
        table(
            c,
            ["Test / record", "Measured result / evidence location"],
            rows,
            y,
            [230, 293],
            9,
        )
        - 22
    )
    y = (
        para(
            c, "First-run and maintenance handoff", 36, y, W - 72, 14, 19, True
        )
        - 10
    )
    y = (
        para(
            c,
            "Before every run: test E-stop/guard, inspect pads, "
            "fasteners, cable loops, probe attachment and disk space. "
            "Initially inspect every 1,000 cycles; record pass before "
            "resuming. Check clutch setting, rail lubrication per vendor, "
            "witness marks and temperature history. Recommission after "
            "changes to shoes, clutch, stops, servo, firmware or wiring.",
            36,
            y,
            W - 72,
            10,
            15,
        )
        - 18
    )
    para(
        c,
        "Routine operating restrictions: __________________________"
        "_________________<br/><br/>"
        "As-built drawing and backup location: _______________________"
        "_________________<br/><br/>"
        "Unattended operation: NOT RELEASED by this booklet. A separate "
        "validated machine/thermal risk assessment and duty qualification "
        "are required.",
        36,
        y,
        W - 72,
        9.5,
        15,
    )
    footer(c, 35)
    c.showPage()

    y = title(
        c,
        "REFERENCES / DOCUMENT CONTROL",
        "Keep these with the bench",
        "Manufacturer sources checked 4 November 2026. "
        "Match their revision and ratings to the delivered components.",
    )
    for ident, label, url in SOURCES:
        y = (
            para(
                c,
                f"<b>{ident}  {html.escape(label)}</b>",
                36,
                y,
                W - 72,
                9.3,
                13,
            )
            - 4
        )
        y = (
            para(
                c,
                f'<link href="{html.escape(url)}" color="{TEAL}">'
                f"{html.escape(url)}</link>",
                36,
                y,
                W - 72,
                8,
                11,
            )
            - 14
        )
    y = (
        para(
            c,
            "Project source of dimensions and behavior",
            36,
            y,
            W - 72,
            13,
            17,
            True,
        )
        - 8
    )
    y = (
        para(
            c,
            "hardware/BOM.json and BOM.md; "
            "docs/DESIGN_AND_ASSEMBLY.md; hardware/foldbench.scad "
            "(envelope only); hardware/calibration.example.json; "
            "src/foldbench/models.py, probe.py and settings.py; "
            "docs/COMMISSIONING.md; deploy/ and README.md.",
            36,
            y,
            W - 72,
            9.3,
            13,
        )
        - 16
    )
    para(
        c,
        "All assembly drawings in this companion are original vector "
        "illustrations. Editable SVGs and the content source are in "
        "docs/assembly/. Regenerate using pipenv run assembly-manual. "
        "This publication adds instructions and identifies unresolved "
        "interfaces; it does not claim a fabricated, tested or certified "
        "machine.",
        36,
        y,
        W - 72,
        9.3,
        13,
    )
    footer(c, 36)
    c.showPage()


def write_markdown(steps):
    lines = [
        "# foldatron - Illustrated assembly manual",
        "",
        "Assembly companion A1. Separate from the design guide. "
        "Prototype: physical validation and H1-H5 release required.",
        "",
        "[Printable PDF](../Foldatron-illustrated-assembly-manual.pdf)",
        "",
        "## Engineering release register",
        "",
    ]
    for hold, parts, description in HOLDS:
        lines += [f"### {hold}", "", parts + ": " + description, ""]
    lines += [
        "## Fabricated parts",
        "",
        "| FAB ID | Qty | Reference | BOM |",
        "| --- | --- | --- | --- |",
    ]
    lines += ["| " + " | ".join(row) + " |" for row in FABRICATION]
    for i, step in enumerate(steps, 1):
        lines += [
            "",
            f"## {i:02d}. {step['title']}",
            "",
            f"![Step {i}](assets/step-{i:02d}.svg)",
            "",
            "**Parts:** " + step["parts"],
            "",
            "**Tools:** " + step["tools"],
            "",
        ]
        lines += [
            f"{n}. {action}" for n, action in enumerate(step["actions"], 1)
        ]
        lines += ["", "**Check:** " + step["check"], "", step["record"], ""]
    lines += [
        "## Wire schedule",
        "",
        "| IDs | From/path | To | Size |",
        "| --- | --- | --- | --- |",
    ]
    lines += ["| " + " | ".join(row) + " |" for row in WIRES]
    lines += ["", "## Manufacturer references", ""]
    lines += [f"- {ident}: [{label}]({url})" for ident, label, url in SOURCES]
    lines += [
        "",
        "The PDF also contains fastener-selection, software "
        "bring-up and static/dynamic acceptance worksheets.",
        "",
    ]
    (DATA / "README.md").write_text("\n".join(lines))


def main():
    steps = json.loads((DATA / "steps.json").read_text())
    if len(steps) != 26:
        raise ValueError("Update page cross-references if step count changes")
    (DATA / "assets").mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUTPUT), pagesize=A4, invariant=1)
    c.setTitle("foldatron - Illustrated assembly manual")
    c.setAuthor("foldatron engineering project")
    c.setSubject("Assembly companion A1; prototype engineering instructions")
    intro(c, steps)
    for i, step in enumerate(steps, 1):
        step_page(c, i, step)
    appendices(c)
    c.save()
    write_markdown(steps)
    print(f"36 pages / 26 operations / 27 editable SVGs: {OUTPUT}")


if __name__ == "__main__":
    main()
