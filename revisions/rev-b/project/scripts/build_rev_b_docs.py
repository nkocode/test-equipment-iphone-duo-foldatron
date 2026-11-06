"""Publish the CAD drawing book and separate technical assembly traveler."""

from __future__ import annotations

import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from svglib.svglib import svg2rlg

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "hardware/rev-b"
VIEWS = DATA / "views"
DOCS = ROOT / "docs/rev-b"
PAGE_W, PAGE_H = landscape(A3)
NAVY = colors.HexColor("#173647")
TEAL = colors.HexColor("#156b76")
GRAY = colors.HexColor("#526572")
PALE = colors.HexColor("#eef3f5")
AMBER = colors.HexColor("#9b591d")
BODY = ParagraphStyle(
    "body",
    fontName="Helvetica",
    fontSize=10,
    leading=14,
    textColor=NAVY,
    alignment=TA_LEFT,
)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=8, leading=10.5)
CALLOUTS = {
    "fixture-iso.png": [
        ("B102", 0.10, 0.88),
        ("B106", 0.78, 0.90),
        ("V08", 0.10, 0.25),
        ("B117", 0.82, 0.17),
        ("B125", 0.90, 0.65),
    ],
    "base_towers-iso.png": [
        ("B101", 0.10, 0.15),
        ("B102", 0.80, 0.85),
        ("B103", 0.15, 0.40),
        ("B104", 0.88, 0.40),
    ],
    "bearing-exploded.png": [
        ("B102", 0.10, 0.45),
        ("B105", 0.85, 0.85),
        ("V09", 0.85, 0.63),
        ("V10", 0.12, 0.80),
    ],
    "yoke-iso.png": [
        ("B106", 0.10, 0.80),
        ("B107", 0.88, 0.20),
        ("B111", 0.15, 0.25),
        ("B120", 0.85, 0.85),
    ],
    "float-iso.png": [
        ("B108", 0.10, 0.40),
        ("B109", 0.85, 0.85),
        ("V11", 0.10, 0.80),
        ("B110", 0.85, 0.45),
        ("B107", 0.85, 0.12),
    ],
    "endpoints-iso.png": [
        ("B125", 0.10, 0.85),
        ("B126", 0.85, 0.15),
        ("B127", 0.85, 0.85),
        ("V31", 0.10, 0.45),
    ],
    "guard-switch-iso.png": [
        ("B128", 0.12, 0.80),
        ("B129", 0.85, 0.85),
        ("B130", 0.88, 0.60),
        ("V29", 0.85, 0.25),
    ],
    "drive-iso.png": [
        ("B119", 0.12, 0.75),
        ("B121", 0.12, 0.20),
        ("B122", 0.85, 0.60),
        ("V08", 0.12, 0.45),
        ("V12", 0.85, 0.80),
    ],
    "angular_stops-iso.png": [
        ("B123", 0.12, 0.85),
        ("B124", 0.85, 0.25),
    ],
}


def para(c, text, x, y, width, style=BODY):
    """Draw downward from y and return the next baseline."""
    p = Paragraph(text, style)
    _, height = p.wrap(width, PAGE_H)
    p.drawOn(c, x, y - height)
    return y - height - 9


def table(c, rows, x, y, widths, size=8):
    style = ParagraphStyle(
        "cell", parent=SMALL, fontSize=size, leading=size + 2.5
    )
    cells = [
        [Paragraph(escape(str(cell)), style) for cell in row] for row in rows
    ]
    t = Table(cells, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PALE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, TEAL),
                (
                    "LINEBELOW",
                    (0, 1),
                    (-1, -1),
                    0.25,
                    colors.HexColor("#cad5da"),
                ),
            ]
        )
    )
    _, height = t.wrap(sum(widths), PAGE_H)
    if y - height < 62:
        raise ValueError(f"Table exceeds sheet: {rows[0]}, height={height}")
    t.drawOn(c, x, y - height)
    return y - height - 12


class Book:
    def __init__(self, path, title):
        self.c = canvas.Canvas(str(path), pagesize=(PAGE_W, PAGE_H))
        self.c.setTitle(title)
        self.c.setAuthor("foldatron engineering development")
        self.number = 0
        self.title = title

    def page(self, code, title, subtitle=""):
        if self.number:
            self.c.showPage()
        self.number += 1
        c = self.c
        c.setStrokeColor(NAVY)
        c.setLineWidth(0.8)
        c.rect(22, 22, PAGE_W - 44, PAGE_H - 44)
        c.setFillColor(TEAL)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(40, PAGE_H - 48, "foldatron / REV B")
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 23)
        c.drawString(40, PAGE_H - 80, title)
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 10)
        c.drawString(40, PAGE_H - 101, subtitle)
        c.line(40, 57, PAGE_W - 40, 57)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(40, 40, code)
        c.setFont("Helvetica", 8)
        c.drawString(145, 40, "mm | CAD views NTS | dimensions govern")
        c.setFillColor(AMBER)
        c.drawString(420, 40, "DEVELOPMENT REVIEW - NOT A FABRICATION RELEASE")
        c.setFillColor(GRAY)
        c.drawRightString(
            PAGE_W - 40, 40, f"2026-11-05  |  Sheet {self.number:02d}"
        )
        c.bookmarkPage(code)
        c.addOutlineEntry(f"{code}  {title}", code)
        return c

    def save(self):
        self.c.save()


def picture(c, name, x, y, width, height):
    c.drawImage(
        str(VIEWS / name),
        x,
        y,
        width,
        height,
        preserveAspectRatio=True,
        anchor="c",
        mask="auto",
    )
    if name not in CALLOUTS:
        return
    data = json.loads((VIEWS / name).with_suffix(".anchors.json").read_text())
    iw, ih = data["size"]
    scale = min(width / iw, height / ih)
    ix, iy = x + (width - iw * scale) / 2, y + (height - ih * scale) / 2
    for part, fx, fy in CALLOUTS[name]:
        anchor = next(a for a in data["anchors"] if a["part"] == part)
        ax, ay = ix + anchor["x"] * scale, iy + anchor["y"] * scale
        lx, ly = x + width * fx, y + height * fy
        c.setStrokeColor(TEAL)
        c.setLineWidth(0.65)
        c.line(lx, ly, ax, ay)
        c.setFillColor(TEAL)
        c.circle(ax, ay, 2, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.roundRect(lx - 22, ly - 9, 44, 18, 3, fill=1, stroke=1)
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 8.5)
        c.drawCentredString(lx, ly - 3, part)


def svg(c, name, x, y, width, height):
    path = VIEWS / name
    drawing = svg2rlg(str(path))
    scale = min(width / drawing.width, height / drawing.height)
    c.saveState()
    c.translate(x, y)
    c.scale(scale, scale)
    renderPDF.draw(drawing, c, 0, 0)
    c.restoreState()
    # SVG px are converted by svglib at 0.75 pt/px. Dimension overlays
    # must use the same conversion as the rendered CAD vectors.
    return scale * drawing.width / 700


def dim(c, x1, y1, x2, y2, text, vertical=False):
    c.setStrokeColor(TEAL)
    c.setFillColor(TEAL)
    c.setLineWidth(0.55)
    c.line(x1, y1, x2, y2)
    if vertical:
        for x, y in ((x1, y1), (x2, y2)):
            c.line(x - 4, y, x + 4, y)
        c.saveState()
        c.translate(x1 - 5, (y1 + y2) / 2)
        c.rotate(90)
        c.setFont("Helvetica", 9)
        c.drawCentredString(0, 0, text)
        c.restoreState()
    else:
        for x, y in ((x1, y1), (x2, y2)):
            c.line(x, y - 4, x, y + 4)
        c.setFont("Helvetica", 9)
        c.drawCentredString((x1 + x2) / 2, y1 + 5, text)


def part_plan(c, part, x, y, width, height):
    name = part["id"] + "-plan.svg"
    scale = svg(c, name, x, y, width, height)
    raw = (VIEWS / name).read_text()
    match = re.search(
        r"scale\(([-\d.]+), [-\d.]+\)\s+"
        r"translate\(([-\d.]+),([-\d.]+)\)",
        raw,
    )
    if not match:
        return
    s, tx, ty = map(float, match.groups())

    def point(px, py):
        return x + scale * s * (px + tx), y + scale * (440 + s * (py + ty))

    xmin, xmax, ymin, ymax, _, _ = part["bounds_mm"]
    left, bottom = point(xmin, ymin)
    right, top = point(xmax, ymax)
    dim(c, left, bottom - 16, right, bottom - 16, f"{xmax - xmin:g}")
    dim(c, left - 18, bottom, left - 18, top, f"{ymax - ymin:g}", True)
    ox, oy = point(0, 0)
    c.setStrokeColor(GRAY)
    c.setDash(4, 3)
    c.line(ox - 15, oy, ox + 25, oy)
    c.line(ox, oy - 15, ox, oy + 25)
    c.setDash()
    c.setFont("Helvetica", 7)
    c.drawString(ox + 27, oy, "+X")
    c.drawString(ox + 3, oy + 27, "+Y")


def draw_parts(book, parts):
    for part in parts:
        c = book.page(
            part["id"],
            part["title"],
            f"Qty {part['quantity']} | {part['material']} | "
            "Local part coordinates; see assembly placement",
        )
        part_plan(c, part, 55, 333, 650, 395)
        svg(c, part["id"] + "-iso.svg", 55, 78, 410, 250)
        svg(c, part["id"] + "-front.svg", 460, 100, 250, 180)
        c.setFillColor(GRAY)
        c.setFont("Helvetica", 9)
        c.drawString(70, 309, "PLAN / LOCAL XY")
        c.drawString(70, 83, "ISOMETRIC")
        c.drawString(480, 88, "EDGE / LOCAL XZ")
        y = PAGE_H - 132
        if part["features"]:
            rows = [["ID", "X", "Y", "Feature"]]
            rows += [
                [f["tag"], f"{f['x']:g}", f"{f['y']:g}", f["callout"]]
                for f in part["features"]
            ]
            y = table(c, rows, 744, y, [28, 45, 45, 260], size=7.5)
        for note in part["notes"]:
            y = para(c, escape(note), 750, y, 365, SMALL)
        y = para(
            c,
            "<b>General:</b> machined dimensions +/-0.10; "
            "angles +/-0.5 deg unless stated. Deburr 0.2-0.5. "
            "Threads are modeled at tap-drill diameter; apply "
            "callouts. Do not infer thread size from STEP.",
            750,
            y,
            365,
            SMALL,
        )
        if y < 65:
            raise ValueError(f"Part notes overflow: {part['id']}")


def drawing_book(parts, sources, bom, checks):
    book = Book(
        DOCS / "Foldatron-Rev-B-drawing-book.pdf",
        "foldatron Rev B - CAD and engineering drawing book",
    )
    c = book.page(
        "GA-001",
        "The bench, resolved in CAD",
        "1010 one-inch extrusion | vendor interfaces | "
        "machined fixture | guarded development station",
    )
    picture(c, "general-iso.png", 40, 95, 815, 615)
    y = 700
    for title, text in [
        (
            "A real geometry model",
            "OpenCascade solids, STEP assembly, "
            "individual custom STEP parts and millimetre DXF profiles. "
            "The views in this book are generated from that same model.",
        ),
        (
            "A traceable source package",
            "Manufacturer drawings are "
            "indexed by source ID. Original vendor files are separated "
            "from reconstructed interface models and custom designs.",
        ),
        (
            "Build status",
            "This issue supports a development-shop "
            "review and prototype quotation. It is not a fully released "
            "build package. P1-P4 identify the interfaces that still "
            "prevent complete assembly and powered commissioning.",
        ),
    ]:
        y = para(c, f"<b>{title}</b><br/>{text}", 865, y, 270)
    c = book.page(
        "GA-002",
        "Datums and installation envelope",
        "A = top of fixture base | X = across phone | Y = hinge axis | Z = up",
    )
    picture(c, "frame-front.png", 40, 350, 540, 350)
    picture(c, "frame-top.png", 600, 350, 530, 350)
    table(
        c,
        [
            ["Dimension / location", "Value", "Basis"],
            [
                "Frame outside, excluding panel thickness",
                "660.4 x 558.8 x 558.8",
                "26 x 22 x 22 in; 1010 is 25.4 mm square",
            ],
            [
                "Frame underside / roof extrusion top",
                "Z=-33.4 / +525.4",
                "Base top is zero; guard roof top +529.4",
            ],
            [
                "Fixture base / support crossmembers",
                "500 x 460 x 8 / Y=+/-150",
                "Base top Z0; frame rail top Z=-8",
            ],
            [
                "Hinge axis / bearing tower outside faces",
                "X0, Z140 / Y=+/-124",
                "Bearing pockets face inward; fixture bolts allow alignment",
            ],
            [
                "Cabinet envelope; independent on bench",
                "299.33 x 239.46 x 119.73",
                "Hammond 1554YA2GY, source S13; no unsupported frame "
                "cantilever",
            ],
            [
                "Recommended work surface",
                "1200 x 800 minimum",
                "Project allowance for cabinet, leads and service access",
            ],
        ],
        45,
        335,
        [325, 310, 465],
        9,
    )
    c = book.page(
        "FR-001",
        "Frame cut list and joint schedule",
        "80/20 1010 / 4119 / 3393 | do not substitute metric 2020 hardware",
    )
    picture(c, "frame-iso.png", 40, 130, 635, 565)
    y = table(
        c,
        [
            ["Member", "Qty", "Cut length", "Location"],
            ["V01", 4, "660.4 +/-0.25", "Front/rear; top/bottom"],
            ["V02", 4, "508.0 +/-0.25", "Side rails; top/bottom"],
            ["V02", 4, "508.0 +/-0.25", "Vertical posts"],
            ["V03", 2, "609.6 +/-0.25", "Base crossmembers"],
        ],
        710,
        700,
        [60, 40, 125, 200],
        9,
    )
    y = para(
        c,
        "<b>Total cut length: 7,924.8 mm.</b> Order cut-to-length "
        "or add saw kerf and end-trim waste to stock. Match paired "
        "members within 0.10 mm; deburr ends.",
        715,
        y,
        410,
    )
    y = table(
        c,
        [
            ["Joints", "4119", "3393 sets"],
            ["8 horizontal corner joints", 8, 16],
            ["4 posts x 2 ends x 2 directions", 16, 32],
            ["2 crossmembers x 2 ends", 4, 8],
            ["Total structural joints", 28, 56],
        ],
        710,
        y,
        [265, 75, 85],
        9,
    )
    para(
        c,
        "The model includes all 28 brackets. The schedule "
        "above governs their hardware quantities. Confirm wrench "
        "access and bracket-to-bracket clearance at the first corner "
        "before repeating. Frame diagonal difference <=0.5 mm per "
        "rectangle; no foot rocking on the installation surface.",
        715,
        y,
        410,
    )
    c = book.page(
        "ME-001",
        "Fixture arrangement and motion",
        "Counterbalanced yoke | twin supported stub shafts | "
        "radial float | physical output stop cam",
    )
    picture(c, "fixture-iso.png", 40, 275, 760, 440)
    picture(c, "fixture-front.png", 40, 70, 760, 220)
    y = 700
    for note in [
        "<b>Fixed half:</b> B117 on four B118 posts. B117 top is "
        "Z136.4; 1 mm pad gives nominal contact surface Z137.4.",
        "<b>Moving half:</b> B109 plate on two MGN7C blocks; "
        "B108 carriers bolt to B107. Axis is X0/Z140; yoke rotates "
        "about Y. The phone envelope is unverified, not an Apple model.",
        "<b>Float:</b> block centers X55; four B110 stops produce "
        "5.7..6.0 mm travel each way after 2 mm pads are fitted, "
        "depending on end-seal length. Rails start X15 and finish X115.",
        "<b>Balance:</b> move both B120 plates in X, then B111 weights "
        "in Z. Measure residual gravity torque with the actual dummy "
        "and all wiring installed. Goal <=0.02 N m; do not substitute "
        "the CAD mass estimate for this measurement.",
        "<b>Stops:</b> B123 is on the output shaft, so the slip clutch "
        "cannot hide output overtravel. B124 posts carry adjustable "
        "M6 screws and soft pads. Normal operation must stop short "
        "of these mechanical stops.",
    ]:
        y = para(c, note, 830, y, 300)
    c = book.page(
        "ME-002",
        "Bearing and shaft stack",
        "Use inner-race spacers; do not preload bearings by "
        "tightening collars",
    )
    picture(c, "bearing-exploded.png", 40, 280, 740, 425)
    table(
        c,
        [
            ["Front-side item", "Y interval / position", "Interface"],
            ["B113 output shaft", "-193 to -85", "D6 g6, 108 long"],
            ["B123 cam", "-180 to -164", "D6 H7 bore; two flats at Y=-175"],
            [
                "Outer collar / B116 spacer",
                "-135.05..-126.05 / -126.05..-122.05",
                "Collar D16; spacer D8 clears tower D8.2",
            ],
            [
                "NSK 626 bearing",
                "-122.05..-116.05",
                "6 x 19 x 6; pocket D19 H7",
            ],
            [
                "B115 spacer / inner collar",
                "-116.05..-114.05 / -114.05..-105.05",
                "Spacer contacts inner race only",
            ],
            [
                "B112 hub / B106 arm",
                "-101..-85 / -85..-79",
                "4 x M3 on PCD20; two shaft flats at Y=-96",
            ],
            [
                "Rear stack",
                "Mirror bearing/hub stack; shaft +85..+169",
                "B114 = 84 long; B125 endpoint cam on rear tail",
            ],
        ],
        45,
        270,
        [280, 410, 410],
        8.5,
    )
    y = 690
    for note in [
        "Press only the bearing outer race into the tower seat. "
        "Never transmit press force through the balls.",
        "Retainer B105 has D17 opening. Pocket depth 6.05 "
        "leaves at least 0.05 mm outer-race clearance.",
        "Set collars with 0.05-0.10 mm total axial freedom. "
        "Ruland MCL-6-A screw torque is 2.1 N m (S08).",
        "Flat clocking and clutch engagement remain P2. "
        "Do not cut the output shaft short to suit an assumed "
        "clutch internal dimension.",
    ]:
        y = para(c, escape(note), 810, y, 315)
    endpoint_page(book)
    guard_mount_page(book)
    electrical_pages(book)
    panel_pages(book)
    controller_board_pages(book)
    cabinet_installation_pages(book)
    draw_parts(book, parts)
    catalog_pages(book, sources, bom)
    supplier_page(book)
    verification_page(book, checks)
    book.save()


def catalog_pages(book, sources, bom):
    for index in range(0, len(bom), 11):
        c = book.page(
            f"BOM-{index // 11 + 1:03d}",
            "Procurement and fabrication register",
            "No generic fastener kits | quantities exclude spares | "
            "RFQ is not an orderable confirmed SKU",
        )
        rows = [
            [
                "ID",
                "Qty",
                "Manufacturer / part",
                "Specification / disposition",
                "Evidence",
            ]
        ]
        rows += [
            [
                p["id"],
                p["quantity"],
                p["part_number"],
                p["description"],
                p["source"] + " / " + p["status"],
            ]
            for p in bom[index : index + 11]
        ]
        table(c, rows, 40, 710, [75, 40, 255, 540, 200], 8.5)
    for index in range(0, len(sources), 7):
        c = book.page(
            f"SRC-{index // 7 + 1:03d}",
            "Vendor evidence and CAD provenance",
            "Access checked 2026-11-05 | downloaded files are hashed "
            "in source-register.json",
        )
        y = 710
        for source in sources[index : index + 7]:
            y = para(
                c,
                f"<b>{source['id']} / {escape(source['manufacturer'])} "
                f"/ {escape(source['title'])}</b><br/>"
                f"{escape(source['dimensions'])}<br/>"
                f"<font color='#526572'>{escape(source['file_status'])}; "
                f"{escape(source['model_status'])}</font><br/>"
                f"<link href='{escape(source['url'])}' color='#156b76'>"
                f"{escape(source['url'])}</link>",
                50,
                y,
                1080,
                SMALL,
            )
        if y < 65:
            raise ValueError("Source page overflow")


def endpoint_page(book):
    c = book.page(
        "ME-003",
        "Output-side endpoint sensing",
        "B125 sensing cam / B126 sole / two B127 uprights | "
        "normal position feedback, not a safety stop",
    )
    picture(c, "endpoints-iso.png", 45, 230, 690, 460)
    y = 705
    for text in [
        "<b>Mounting datums</b><br/>Cam axis X0,Z140; barrel "
        "Y151..161, discY161..167. Sole center X0,Y202, bottomZ0. "
        "Upright origins X+/-43.8,Y167,Z12.",
        "<b>Exact switch</b><br/>OMRON D2F-01L-D3 has solder terminals. "
        "Both mounting-hole pairs are6.5mm apart. Right body center "
        "Z133.6; left Z146.4, rotated180deg about Y. This places "
        "both lever tips approximately at Z140. See S24.",
        "<b>Radial adjustment</b><br/>Start hole baselines at "
        "X+/-32.8. Adjust each switch in its6x2.4 slots with a "
        "continuity meter. Mounting torque0.08..0.10Nm; do not "
        "crush the switch body.",
        "<b>Travel acceptance</b><br/>Measure electrical make, "
        "release and actual remaining lever travel. At the cam peak, "
        "target0.35..0.45mm beyond make, within the published "
        "minimum available overtravel0.55mm. Test the whole sweep; "
        "a nominal OP dimension cannot establish a safe setting.",
        "<b>Timing</b><br/>Set signals near fixture5deg and175deg, "
        "before backup stops0/180deg. Confirm one signal at each end "
        "and both low through mid-travel. Inspect cam retention and "
        "wear during dummy endurance testing.",
    ]:
        y = para(c, text, 770, y, 355, SMALL)
    table(
        c,
        [
            ["Element", "Verified source / design boundary"],
            [
                "D2F-01L-D3",
                "OP6.8+/-1.5; MDmax0.5; "
                "OTmin0.55; hinge lever maximum force0.78N (S24)",
            ],
            [
                "B125",
                "Project cam: R25 base, R26.2 peak, "
                "cosine rise over+/-12deg. Actual make/release measured.",
            ],
            [
                "CAD image",
                "Switch bodies are interface envelopes; "
                "spring-lever deflection and solder tails are not modeled.",
            ],
            [
                "P3",
                "Endpoint hardware is dimensioned. Physical "
                "actuation, insertion and access tests remain open.",
            ],
        ],
        45,
        218,
        [150, 950],
        9,
    )


def guard_mount_page(book):
    c = book.page(
        "ME-004",
        "Guard interlock / reinforced key mount",
        "OMRON D4NS-1BF + D4DS-K2 | B128-B130 | "
        "straight withdrawal of screw-removable front panel",
    )
    picture(c, "guard-switch-iso.png", 45, 230, 690, 470)
    y = 705
    for text in [
        "<b>Frame mount</b><br/>B128 origin(-275,-238.15,255). "
        "Its left face contacts the left-front post at X=-304.8. "
        "Preload two3393 T-nuts in that post's inward-facing slot. "
        "Recesses preserve the vendor bracket's4.775mm clamp stack.",
        "<b>Switch mount</b><br/>Rear seating planeY=-238.15. "
        "Two diagonal body bolts: (-286,316.5) and(-264,269.5) in "
        "global X,Z. Set head to front insertion. Cut M4x50 blanks "
        "to measured stack plus nut and two threads; record length.",
        "<b>Key mount</b><br/>Key hole centers X=-282.5/-267.5,Z344. "
        "B129 backs the outside of the front panel. B130 sleeves "
        "carry the clamping force through the D7 panel holes. "
        "Measure panel thickness before finishing sleeve length.",
        "<b>Insertion datum</b><br/>Nominal rear-plane to key "
        "seating-plane distance41.15mm with4.1mm sleeves. Actual "
        "must be40..42.5mm. Align key tip to opening within+/-1mm "
        "in both directions; key-slot center is nominalZ350.",
        "<b>Physical acceptance P3</b><br/>Guard seats against frame, "
        "not against the switch. Withdraw squarely without levering "
        "the key. Test both channels and loss of permit before "
        "reachable motion. Validate stopping distance and anti-tamper "
        "measures; a fitted key alone does not establish guard safety.",
    ]:
        y = para(c, text, 770, y, 355, SMALL)
    table(
        c,
        [
            ["Connection", "Required assembly check"],
            [
                "Switch body",
                "0.5..0.7Nm; no distorted housing. "
                "Use actual body seating/bolt recesses, not envelope depth.",
            ],
            [
                "Operation key",
                "2.4..2.8Nm. Verify sleeve ends bear "
                "on metal; plastic must not carry the bolt preload.",
            ],
            [
                "Drawing scope",
                "Switch/key are reconstructed "
                "interface envelopes, not original OMRON manufacturing CAD.",
            ],
            [
                "Cable entry",
                "D4NS-1BF is PG13.5. Use compatible "
                "plastic gland; cabinet M16 gland does not fit this entry.",
            ],
        ],
        45,
        218,
        [150, 950],
        9,
    )


def electrical_pages(book):
    c = book.page(
        "E-001",
        "Independent stop circuits / wiring review",
        "Exact PNOZ X3 terminal references | two separate input "
        "devices | HOLD P4 before energizing",
    )
    c.setFont("Helvetica-Bold", 11)
    for row, label, contacts in [
        (
            640,
            "12 V MOTOR POWER",
            ["F1 / DC fuse", "K1 13-14", "K2 13-14", "Hub VDD"],
        ),
        (
            530,
            "24 V PERMIT STATUS",
            ["K1 33-34", "K2 33-34", "2 kohm / 1 W", "Opto LED"],
        ),
    ]:
        c.setFillColor(NAVY)
        c.drawString(55, row + 38, label)
        c.setStrokeColor(TEAL)
        c.setLineWidth(1.4)
        c.line(55, row, 1110, row)
        for i, label_ in enumerate(contacts):
            x = 175 + i * 250
            c.setFillColor(colors.white)
            c.rect(x - 75, row - 23, 150, 46, fill=1)
            c.setFillColor(NAVY)
            c.drawCentredString(x, row - 4, label_)
    rows = [["Circuit", "Connection", "Rule / source"]]
    rows += [
        [
            "Both relays: supply",
            "+24V -> B1; 0V24 -> B2",
            "774310 DC variant; A1/A2 unused",
        ],
        [
            "K1 E-stop channel A",
            "S31 -> E-stop NC block A11 -> A12 -> S32",
            "Direct-opening NC; source S20 p12",
        ],
        [
            "K1 E-stop channel B",
            "S21 -> E-stop NC block B11 -> B12 -> S22",
            "Two distinct contact blocks; do not join channels",
        ],
        [
            "K2 guard channel A",
            "S31 -> D4NS11 -> 12 -> S32",
            "Use actual device terminal markings",
        ],
        [
            "K2 guard channel B",
            "S21 -> D4NS21 -> 22 -> S22",
            "No E-stop contacts in series in these inputs",
        ],
        [
            "Both relays: link",
            "S11 -> S12",
            "Cross-short-detection configuration, S20 p12",
        ],
        [
            "K1 and K2: separate reset",
            "S33 -> respective NO reset -> S34",
            "Monitored reset; S13/S14 remain unlinked; S20 p13",
        ],
        [
            "Unused outputs",
            "23/24,41/42,Y31/Y32",
            "Leave isolated; no undocumented bridges",
        ],
    ]
    y = table(c, rows, 45, 465, [220, 500, 380], 8.5)
    para(
        c,
        "<b>Review limits:</b> F1=V52(2A), F2=V53(1A). Fuse coordination, "
        "connector adapter cables, wiring protection and terminal "
        "allocations are not released by this diagram. Verify relay "
        "load/inrush ratings, supply fault current and the current "
        "manufacturer manual. The drawing does not assign a machine "
        "performance level or replace a stopping test.",
        55,
        y,
        1080,
    )
    c = book.page(
        "E-002",
        "Controller interface and connector details",
        "Active-high signals preserved for existing FastAPI driver | "
        "no 24 V on Pi header",
    )
    picture(c, "NC3FD-LX.png", 45, 435, 360, 260)
    picture(c, "NC4FD-LX.png", 425, 435, 360, 260)
    y = 700
    y = para(
        c,
        "<b>Original vendor CAD</b><br/>These connector views "
        "are rendered from Neutrik's downloaded STEP files, not "
        "reconstructed cylinders. Original models are supplied "
        "in the vendor reference archive.",
        835,
        y,
        290,
    )
    y = para(
        c,
        "<b>Panel pattern</b><br/>D24.0 +0.1/0 opening; two "
        "D3.2 mount holes at (-9.5,+12) and (+9.5,-12), measured "
        "from connector center. Mirror only if the vendor drawing "
        "shows the opposite viewing face. Trial-fit a scrap panel "
        "before cutting the enclosure.",
        835,
        y,
        290,
    )
    para(
        c,
        "<b>Project pinout</b><br/>NC3: 1=0V12,2=+12V,3 unused.<br/>"
        "NC4: 1=0V24,4=+24V,2/3 unused.<br/>"
        "Label both DC ONLY. Inspect solder-cup pin numbers; do not "
        "wire from a front-view mirror image.",
        835,
        y,
        290,
    )
    rows = [["Signal", "BCM / header", "Connection / inspection"]]
    rows += [
        [
            "Safety permit",
            "GPIO17 / pin11",
            "LTV-817C collector to3.3V; emitter to node;10k "
            "node-to-GND;1k node-to-pin11. High=permit.",
        ],
        [
            "Open endpoint",
            "GPIO27 / pin13",
            "Switch COM to Pi5V(pin2). NO ->1.8k,1% ->GPIO27; "
            "2.7k,1% GPIO27-to-GND. Nominal high3.0V, switch1.11mA.",
        ],
        [
            "Closed endpoint",
            "GPIO22 / pin15",
            "Same5V switch/1.8k+2.7k divider as open endpoint. "
            "Do not connect5V directly to a GPIO pin.",
        ],
        [
            "Temperature data",
            "GPIO4 / pin7",
            "Two powered DS18B20 sensors;one4.7k pullup to3.3V. "
            "Record both serial numbers.",
        ],
        [
            "Logic supply / return",
            "pin1 / pin6",
            "3.3V / Pi GND. Endpoint COM only uses5V pin2. "
            "No direct24V connection. Verify GPIO highs2.0..3.3V.",
        ],
        [
            "TTL motor lead",
            "JST EHR-03",
            "1=GND,2=VDD12V,3=DATA. Use U2D2 TTL port; not RS-485.",
        ],
    ]
    y = table(c, rows, 45, 410, [210, 170, 720], 9)
    para(
        c,
        "Opto input: K2:34 -> 2 kohm /1W -> LED anode; "
        "LED cathode ->0V24. Fit1N4148 antiparallel across the LED. "
        "Check the selected LTV-817C package pinout/CTR and cover the "
        "board. This status circuit is not the safety power-cut path. "
        "Endpoint correction: S24's microload graph starts at5V/1mA. "
        "The earlier3.3V/10k switch circuit is outside that graph. "
        "Require measured COM supply5.00..5.25V under full Pi load. "
        "With1% resistors, calculated GPIO high is2.976..3.175V "
        "and contact current is at least1.10mA. If supply is below5V, "
        "hold commissioning pending a qualified regulated supply. "
        "Measure with GPIO disconnected before attaching the Pi.",
        55,
        y,
        1080,
    )


def verification_page(book, checks):
    c = book.page(
        "QA-001",
        "Verification and release boundary",
        "Computer checks establish model consistency; physical "
        "acceptance remains separate",
    )
    rows = [["Check", "Result", "What was checked"]]
    rows += [
        [
            "Custom solid validity",
            str(checks["all_custom_solids_valid"]),
            "OpenCascade validity for every exported custom part",
        ],
        [
            "Moving sweep against base, tray, posts and towers",
            f"{len(checks['sampled_sweep_collisions'])} overlaps",
            "37 positions, 0..180 degrees in 5-degree steps; >0.01 "
            "mm3 threshold",
        ],
        [
            "Lowest sampled moving surface",
            f"{checks['sampled_minimum_moving_z_mm']:.2f} mm above base",
            "At nominal counterweight settings; excludes wiring and "
            "screw heads",
        ],
        [
            "Phone geometry / clutch insertion / safety validation",
            "NOT VERIFIED",
            "Actual phone, configured clutch drawing and assembled "
            "hardware required",
        ],
    ]
    y = table(c, rows, 45, 700, [340, 220, 540], 10)
    for hold in holds():
        y = para(c, f"<b>{hold[0]} - {hold[1]}</b><br/>{hold[2]}", 55, y, 1070)
    para(
        c,
        "<b>Release signature:</b> mechanical owner __________  "
        "electrical owner __________  shop lead __________  date "
        "__________<br/>"
        "Do not mark a hold closed merely because the associated STEP "
        "file opens or a simulated cycle passes.",
        55,
        y - 6,
        1070,
    )


def holds():
    return [
        (
            "P1",
            "Phone-contact inserts",
            "Measure the actual iPhone Duo "
            "case, hinge-axis path, protrusions, buttons and screen "
            "keep-outs. "
            "Release contact inserts and retention features after an actual "
            "fit test. The current rectangular envelope is not verified.",
        ),
        (
            "P2",
            "Configured clutch and shaft interfaces",
            "Obtain Dynatect's "
            "drawing for an EAS12 shaft-to-shaft clutch with two exact 6 mm "
            "bores. Confirm insertion depths, set-screw locations and stable "
            "0.20 N m bidirectional slip. Confirm B122 center-bolt clearance "
            "and finish the shaft flats from the approved stack.",
        ),
        (
            "P3",
            "Guard sensing and endpoint sensing",
            "Fit-check B128-B130 interlock/key mounts against the "
            "purchased devices. B125-B127 define endpoint mounts and cam. "
            "Confirm "
            "their switch actuation before "
            "hard-stop contact and guard opening before any reachable motion. "
            "Record actual switch-body bolt lengths, key sleeve "
            "lengths, insertion datum and both-channel opening behavior.",
        ),
        (
            "P4",
            "Electrical panel and machine acceptance",
            "Finish the "
            "cabinet mounting/cutout layout, fuse coordination and wiring "
            "release for the exact purchased components. Perform the "
            "independent stop, reset, restart, cable-disconnect and thermal "
            "tests. This issue has no machine safety-category certification.",
        ),
    ]


def panel_pages(book):
    """Dimension the panel allocation without inventing vendor holes."""
    c = book.page(
        "E-003",
        "Cabinet backplate / component allocation",
        "Hammond1554YPL | front view | datum at panel center | "
        "fit review before drilling",
    )
    scale, ox, oy = 2.25, 365, 420

    def region(x, y, width, height, label, fill=PALE):
        c.setFillColor(fill)
        c.setStrokeColor(NAVY)
        c.rect(
            ox + (x - width / 2) * scale,
            oy + (y - height / 2) * scale,
            width * scale,
            height * scale,
            fill=1,
        )
        c.setFillColor(NAVY)
        c.setFont("Helvetica", 9)
        c.drawCentredString(ox + x * scale, oy + y * scale, label)

    region(0, 0, 250.5, 214.52, "", colors.white)
    for y in (30, -70):
        region(-40, y, 140, 35, "")
    region(-78, 30, 45, 121, "K1 / PNOZ X3")
    region(-28, 30, 45, 121, "K2 / PNOZ X3")
    region(75, 30, 48, 57, "U2D2 hub")
    region(75, -45, 50.8, 81.28, "Interface PCB")
    for number in range(20):
        region(-89.4 + number * 5.2, -70, 5.2, 47.7, "")
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(ox - 40 * scale, oy - 70 * scale, "X1:1 ... 20")
    dim(c, ox - 125.25 * scale, 155, ox + 125.25 * scale, 155, "250.50")
    dim(
        c,
        58,
        oy - 107.26 * scale,
        58,
        oy + 107.26 * scale,
        "214.52",
        vertical=True,
    )
    rows = [["Item", "Center X,Y", "Envelope / allocation"]]
    rows += [
        ["Upper DIN rail", "-40,+30", "140 x35; 7.5 high"],
        ["Lower DIN rail", "-40,-70", "140 x35; 7.5 high"],
        ["K1 / K2", "-78,+30 / -28,+30", "45 x121 each;87 deep"],
        ["X1 bank", "-40,-70", "20x5.2=104;47.7 tall"],
        ["Hub PCB", "+75,+30", "48 x57; use supplied10mm supports"],
        ["Interface PCB", "+75,-45", "50.8 x81.28; long axisY"],
        ["Terminal end cover", "Open side of bank", "2.2 wide"],
        ["End brackets", "Either side of each bank", "5.2 wide each"],
    ]
    y = table(c, rows, 710, 700, [125, 145, 155], 8)
    for text in [
        "<b>Defined fit:</b> terminal bank + cover + two end "
        "brackets =116.6mm, within140mm rail. Relay bank including "
        "5mm gap and two end brackets =105.4mm. Nominal gap between "
        "relay body and terminal body is15.65mm.",
        "<b>Depth check:</b> catalogue enclosure internal height111.75mm; "
        "relay87mm + rail7.5mm leaves17.25mm before panel/support "
        "offsets and lid features. Measure the actual stack; this is "
        "not a verified terminal-wire or lid-button clearance.",
        "<b>Drilling:</b> preserve the factory panel mounting holes. "
        "Locate rail fixings using actual slots; use at least two "
        "fixings per rail. Transfer the hub's purchased mounting "
        "pattern. Neither vendor pattern is invented here.",
        "<b>P4:</b> E-009 locates operators/inlets. Fuse-holder "
        "restraints and remaining harness entries require fit review. "
        "Keep the Pi outside. No component on the lid may occupy the "
        "relay depth envelope.",
    ]:
        y = para(c, text, 715, y, 420, SMALL)
    para(
        c,
        "Coordinates are a dimensioned allocation plan, not a released "
        "drill template. The panel's factory corners and holes are "
        "omitted in this view; preserve them.",
        85,
        123,
        555,
        SMALL,
    )

    c = book.page(
        "E-004",
        "Terminal allocation and bus inspection",
        "X1 =20 Phoenix UT2,5 terminals | separate12V,24V and Pi logic",
    )
    rows = [["Terminal", "Net", "Side A", "Side B / bridge"]]
    rows += [
        ["X1:1", "12V inlet", "NC3 pin2", "F1 input"],
        ["X1:2", "0V12", "NC3 pin1", "Power-hub GND"],
        ["X1:3", "24V inlet", "NC4 pin4", "F2 input"],
        ["X1:4", "0V24 inlet", "NC4 pin1", "Wire to X1:9 sideA"],
        ["X1:5", "+24V fused", "F2 output", "K1:B1; FBS4-5 bridges5..8"],
        ["X1:6", "+24V fused", "K2:B1", "Spare; bus5..8"],
        ["X1:7", "+24V fused", "K1:33 permit feed", "Spare; bus5..8"],
        ["X1:8", "+24V fused", "Spare", "Spare; bus5..8"],
        ["X1:9", "0V24", "Wire from X1:4 sideB", "K1:B2; bridge9..12"],
        ["X1:10", "0V24", "K2:B2", "Spare; bus9..12"],
        ["X1:11", "0V24", "Opto LED cathode", "Spare; bus9..12"],
        ["X1:12", "0V24", "Spare", "Spare; bus9..12"],
        ["X1:13", "Switched12V", "K2:14", "Power-hub VDD"],
        ["X1:14..20", "Reserved", "Unconnected", "No bridges installed"],
    ]
    y = table(c, rows, 45, 710, [115, 175, 350, 460], 9)
    for text in [
        "<b>Direct safety-power wires:</b> F1 output -> K1:13; "
        "K1:14 -> K2:13. The motor return is X1:2; do not switch it "
        "instead of positive power. Keep supply and motor wiring "
        "physically distinct from the Pi logic harness.",
        "<b>Permit chain:</b> X1:7 -> K1:33; K1:34 -> K2:33; "
        "K2:34 ->2kohm/1W -> opto LED anode. Cathode ->X1:11. "
        "Use E-001 for channel and reset wiring; E-002 for GPIO wiring.",
        "<b>Assembly inspection:</b> one conductor per clamping point. "
        "Strip9mm and tighten UT terminals0.5..0.6Nm. Number both ends "
        "of every wire. Before fitting bridges, continuity-check each "
        "terminal against adjacent terminals; after fitting, verify "
        "only5..8 and9..12 are common. No 12V/24V/Pi-GND cross-bridge.",
        "<b>P4 remains:</b> wire sizes, cable jacket specifications, "
        "fuse coordination, exact termination accessories, cut lengths "
        "and physical routing require the final wiring release. This "
        "allocation does not authorize energizing the station.",
    ]:
        y = para(c, text, 55, y, 1080, SMALL)


def controller_board_pages(book):
    """Draw actual board coordinates and the solder/inspection schedules."""
    board = json.loads((DATA / "controller-board.json").read_text())
    rows = board["rows_mm"]
    c = book.page(
        "E-005",
        "Controller board / component-side placement",
        "E-BOARD-01 | Adafruit1609 | dimensions mm | solder on reverse side",
    )
    scale, ox, oy = 10, 490, 440

    def point(hole):
        return (
            ox + (-36.83 + (int(hole[1:]) - 1) * 2.54) * scale,
            oy + rows[hole[0]] * scale,
        )

    c.setFillColor(colors.HexColor("#f4f0e4"))
    c.setStrokeColor(NAVY)
    c.roundRect(
        ox - 40.64 * scale,
        oy - 25.4 * scale,
        81.28 * scale,
        50.8 * scale,
        25.4,
        fill=1,
    )
    c.setStrokeColor(colors.HexColor("#d1c9b3"))
    c.setLineWidth(4)
    for n in range(1, 31):
        for a, b in (("A", "E"), ("F", "J")):
            c.line(*point(f"{a}{n}"), *point(f"{b}{n}"))
    for row, color in (("P", TEAL), ("N", GRAY)):
        c.setStrokeColor(color)
        c.line(*point(row + "1"), *point(row + "30"))
    for row in rows:
        for n in range(1, 31):
            x, y = point(f"{row}{n}")
            c.setFillColor(colors.white)
            c.setStrokeColor(GRAY)
            c.setLineWidth(0.5)
            c.circle(x, y, 2.6, fill=1)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(NAVY)
        c.drawRightString(94, point(row + "1")[1] - 3, row)
    for n in range(1, 31):
        c.drawCentredString(point(f"A{n}")[0], 270, str(n))
    for x in (-36.83, 36.83):
        c.setFillColor(colors.white)
        c.circle(ox + x * scale, oy, 16, fill=1)
    for jumper in board["jumpers"]:
        c.setStrokeColor(TEAL)
        c.setLineWidth(2)
        a, b = [point(h) for h in jumper["holes"]]
        c.line(*a, *b)
    for part in board["components"]:
        pts = [point(h) for h in part["holes"]]
        c.setFillColor(NAVY)
        c.setStrokeColor(NAVY)
        c.setLineWidth(1.2)
        if part["ref"] == "U1":
            x, y = pts[0]
            c.roundRect(x - 10, y + 8, 45.4, 60.2, 4, fill=1)
            c.setFillColor(colors.white)
            c.circle(x, y + 19, 3, fill=1, stroke=0)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(x + 12.7, y + 39, "U1")
        else:
            a, b = pts
            c.line(*a, *b)
            mx, my = (a[0] + b[0]) / 2, a[1]
            c.setFillColor(colors.HexColor("#e8c990"))
            width = 17 if part["ref"] == "D1" else 65
            c.roundRect(mx - width / 2, my - 10, width, 20, 4, fill=1)
            c.setFillColor(NAVY)
            c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(mx, my - 3, part["ref"])
    dim(c, ox - 40.64 * scale, 150, ox + 40.64 * scale, 150, "81.28")
    dim(
        c,
        925,
        oy - 25.4 * scale,
        925,
        oy + 25.4 * scale,
        "50.80",
        vertical=True,
    )
    y = 700
    for text in [
        "<b>Read the real board</b><br/>A-E are one copper strip per "
        "column; F-J are another. P is the upper inner rail atY=19.05 "
        "(+3.3V). N is the upper outer rail atY=21.59 (Pi GND). "
        "The two lower rails are unused and omitted here.",
        "<b>Orientation</b><br/>View from component side, column1 "
        "left. U1 pins:1=E10,2=E11,3=F11,4=F10. White dot marks "
        "pin1. Do not mirror this view while soldering underneath.",
        "<b>Mounting</b><br/>Two D3.2 holes on73.66 pitch; use "
        "insulating M3 supports. Keep metal and solder tails clear "
        "of the panel. Cabinet mounting and cover acceptance are P4.",
        "<b>Lead forming</b><br/>Use insulated jumpers. Sleeve any "
        "exposed lead that crosses a pad or another lead. D1 is "
        "upright with an insulated return bend, cathode atC10.",
    ]:
        y = para(c, text, 965, y, 175, SMALL)
    para(
        c,
        "Board grid derived from Limor Fried/Ladyada, Adafruit "
        "Perma-Proto original EAGLE CAD (S36). This derived placement "
        "drawing is CC BY-SA3.0; see THIRD-PARTY-NOTICES.md. "
        "Component bodies are placement symbols; use E-006 hole IDs.",
        85,
        116,
        1040,
        SMALL,
    )

    c = book.page(
        "E-006",
        "Controller board / soldering schedule",
        "One lead per listed hole | resistor bodies PR01 "
        "6.5 x2.5 nominal | do not substitute a solderless board",
    )
    data = [["Ref", "Component", "Hole assignments"]]
    data.extend(
        [p["ref"], p["value"], ", ".join(p["holes"])]
        for p in board["components"]
    )
    data.extend(
        [p["ref"], "Insulated 24AWG jumper", " to ".join(p["holes"])]
        for p in board["jumpers"]
    )
    y = table(c, data, 45, 710, [100, 600, 400], 9)
    for text in [
        "<b>1 / Prepare:</b> confirm PCB identity, clean pads and inspect "
        "for shipping damage. Verify A-E and F-J column connectivity "
        "and four separate rails with an unpowered meter. Compare "
        "the received PCB with the drawing before adding components.",
        "<b>2 / Fit:</b> install insulated jumpers, resistors, D1 then "
        "U1. Form axial resistor leads outside their coated bodies. "
        "Raise bodies about2mm above PCB; keep all formed leads "
        "insulated at crossovers. Route external wires from the "
        "underside with insulated tails and strain relief.",
        "<b>3 / Inspect:</b> solder using component-maker temperature "
        "limits. Trim tails to1mm maximum, clean flux, inspect under "
        "magnification for bridges, cold joints and lead damage. "
        "No solder bridge may replace an insulated jumper.",
        "<b>4 / Protect:</b> board requires a screwed insulating cover "
        "and strain relief before cabinet acceptance. Keep24V wires "
        "at columns5..11 separate from the Pi harness. Neither this "
        "board nor U1 performs the motor safety-disconnect function.",
    ]:
        y = para(c, text, 55, y, 1080, SMALL)

    c = book.page(
        "E-007",
        "Controller board / external terminations",
        "Tag both ends | powered DS18B20 mode | "
        "header numbers are physical pin numbers",
    )
    data = [["Board hole", "Wire destination", "Net"]]
    data.extend(
        [p["hole"], p["connection"], p["net"]] for p in board["external"]
    )
    y = table(c, data, 45, 710, [130, 730, 240], 9)
    para(
        c,
        "Use 24AWG stranded insulated signal wire, minimum60V/80C. "
        "Use red for3.3V, orange for5V, black for Pi GND, violet for "
        "signals; label every conductor because color is not proof "
        "of voltage. Keep permit24V pair separately sleeved and "
        "labeled. Do not connect Pi GND to0V24. Verify the actual "
        "header pin1 mark before connecting. The final locking "
        "header harness and probe termination remain P4.",
        55,
        y,
        1080,
        SMALL,
    )

    c = book.page(
        "E-008",
        "Controller board / inspection and bench test",
        "Pi, motor and probes disconnected until low-voltage "
        "checks pass | meter readings become as-built evidence",
    )
    data = [["Net", "Holes that must be common before components"]]
    data.extend(
        [name, ", ".join(holes)]
        for name, holes in board["continuity_groups"].items()
    )
    y = table(c, data, 45, 710, [210, 890], 8.5)
    for text in [
        "<b>Copper check:</b> after jumpers but before resistors/U1, "
        "each listed group must read below1ohm (subtract lead "
        "resistance); different groups must be open. After components "
        "are fitted, resistors and semiconductors intentionally join "
        "some nets: do not apply the open-circuit rule to that stage.",
        "<b>Endpoint test:</b> independently apply5.00..5.25V toA25 "
        "and GND toN30 with current limit20mA. Close each actual "
        "switch. I27/J29 must each be2.976..3.175V high and below0.2V "
        "when open; disconnect either switch wire and confirm low. "
        "Verify COM stays at least5.00V with the Pi fully loaded later.",
        "<b>Permit test:</b> supplyP30 with3.3V relativeN30; apply "
        "24V toA5/A11 using a separately isolated current-limited "
        "source. J20 must rise above2.0V and remain below3.3V; remove "
        "24V and confirm below0.2V. Verify polarity atU1. R1 is1W: "
        "calculated worst dissipation0.326W at26.4V with1% tolerance.",
        "<b>Final connection:</b> remove test supplies before plugging "
        "in the Pi. Confirm pin2 has no continuity to any GPIO "
        "through a direct wire. Confirm R8 is the only external "
        "1Wire pullup. Record highs/lows at actual Pi header and "
        "both probe serials; simulator checks do not satisfy this test.",
    ]:
        y = para(c, text, 55, y, 1080, SMALL)
    if y < 70:
        raise ValueError("Controller inspection page overflow")


def cabinet_installation_pages(book):
    c = book.page(
        "E-009",
        "Cabinet machining / proposed cutout coordinates",
        "Hammond1554YA2GY | datum at outside center "
        "| trial assembly and P4 sign-off before cutting",
    )
    scale, ox, oy = 2.25, 385, 435
    c.setStrokeColor(NAVY)
    c.setFillColor(PALE)
    c.roundRect(
        ox - 149.665 * scale,
        oy - 119.73 * scale,
        299.33 * scale,
        239.46 * scale,
        12,
        fill=1,
    )
    for x, y, label in [
        (75, 75, "E-STOP"),
        (75, 0, "E-STOP RESET"),
        (75, -70, "GUARD RESET"),
    ]:
        c.setFillColor(colors.white)
        c.circle(ox + x * scale, oy + y * scale, 11.25 * scale, fill=1)
        c.setFillColor(NAVY)
        c.setFont("Helvetica-Bold", 9)
        c.drawRightString(ox + x * scale - 34, oy + y * scale - 3, label)
        c.drawString(ox + x * scale + 32, oy + y * scale - 3, f"({x:+},{y:+})")
    dim(c, ox - 149.665 * scale, 130, ox + 149.665 * scale, 130, "299.33")
    y = table(
        c,
        [
            ["Feature", "Location", "Cutout"],
            ["Lid, all3 operators", "X=+75;Y=+75,0,-70", "D22.5 +0.2/0"],
            ["Front wall,12V inlet", "X=-85;Z=38", "D24 +0.1/0"],
            ["Front wall,24V inlet", "X=-35;Z=38", "D24 +0.1/0"],
            [
                "Each inlet fixing",
                "Offsets(-9.5,+12),(+9.5,-12) from center",
                "2xD3.2",
            ],
            ["Front wall,guard cable", "X=+25;Z=38", "D16 +0.2/0;M16"],
        ],
        770,
        710,
        [120, 155, 100],
        8,
    )
    for text in [
        "<b>Datums:</b> lid X/Y are measured from its outside "
        "bounding-box center, viewed from above. Front-wall X is "
        "measured from enclosure center; Z from outside bottom. "
        "Front wall is Y=-119.73. Do not use molded lettering as a datum.",
        "<b>Trial fit:</b> install panel and all components on "
        "temporary supports. At the inlet centerZ38, verify the "
        "actual connector rear body clears the terminal bank, its "
        "wiring and the base ribs. The bodies are not included in "
        "the simplified allocation view. Record clearance; revise "
        "coordinates before cutting if below10mm.",
        "<b>Lid depth:</b> operators are confined to the right-hand "
        "zone. Confirm at least10mm free clearance to PCBs, covers "
        "and wiring with the lid fully seated. No operator may "
        "overlap the relay depth envelope. Protect the gasket groove.",
        "<b>Fixing:</b> remove all electronics before machining. "
        "Clamp a sacrificial backing; deburr0.2 max. Fit operator "
        "anti-rotation hardware to its current maker drawing. "
        "Connector screws: M3 with washer/nut, trim so2threads "
        "protrude; do not bottom against internal parts.",
    ]:
        y = para(c, text, 775, y, 365, SMALL)
    para(
        c,
        "This coordinates the known cutouts. Remaining Pi/sensor "
        "harness passages and supports must be added to the as-built "
        "drawing after connector selection. This is not a complete "
        "sealed-enclosure modification release.",
        70,
        100,
        1060,
        SMALL,
    )

    c = book.page(
        "E-010",
        "Harness routing / service isolation / fuses",
        "External factory AC/DC supplies | all cabinet "
        "wiring low voltage | lengths recorded after routing",
    )
    y = table(
        c,
        [
            ["Circuit", "Conductor / termination", "Routing / acceptance"],
            [
                "12V motor power",
                "18AWG stranded,105C,300V;red positive/black return",
                "F1=0287002.L2A; FHAC holder;"
                "keep positive/return paired; do not extend thin TTL leads",
            ],
            [
                "24V supply and relay wiring",
                "0.5mm2 stranded,80C min;numbered conductors",
                "F2=0287001.L1A; separate from Pi low-voltage bundle",
            ],
            [
                "Guard channels",
                "LAPP1119754,4x0.5mm2;stock1.8m; nominalOD5.7",
                "Cores1/2=11/12;3/4=21/22. "
                "LAPP53015130 PG13.5 plastic gland at switch",
            ],
            [
                "Guard cable entry",
                "Hammond1427BCGM16, M16x1.5,4..8mm clamp",
                "Cabinet only; never install "
                "metal M16 gland in PG13.5 plastic switch",
            ],
            [
                "Logic / endpoints / probes",
                "24AWG stranded,60V/80C; E-007 wire destinations",
                "Separate sleeves from power; "
                "keep moving lead clear of cam, rails and phone hinge",
            ],
            [
                "Screw-clamp ends",
                "One conductor per clamp; matched insulated ferrule",
                "Use calibrated ratchet die; "
                "no tinned ends; pull-check every crimp",
            ],
        ],
        45,
        710,
        [180, 420, 500],
        9,
    )
    for text in [
        "<b>Prepare:</b> route with lids and guards temporarily "
        "fitted, allow service loops without touching moving parts, "
        "then cut. Record actual length and wire ID in the as-built "
        "schedule. Use screwed cable anchors; adhesive-only anchors "
        "are not accepted. Clamp jackets, never individual insulated "
        "cores, at enclosure entries. Keep the four guard cores in "
        "their own jacket; no intermediate bypass connectors.",
        "<b>Terminal details:</b> UT2,5 strip9mm,0.5..0.6Nm. "
        "D4NS terminals0.6..0.8Nm; use0.5mm2 conductors and the "
        "manufacturer's internal lead-length preparation. PG13.5 "
        "gland has9mm thread, equal to the switch's9mm maximum. "
        "Verify it seats without fouling the internal wiring.",
        "<b>Fuse qualification:</b>2A and1A are prototype selections, "
        "not evidence of coordination. Measure normal peak current, "
        "inrush and wire temperature. Check the exact supply overload "
        "behavior against fuse curves. A current-limited24V supply "
        "may never clear a1A fuse; all wiring must withstand its "
        "maximum sustained fault output. Do not increase fuse values "
        "to cure nuisance opening without a revised review.",
        "<b>Service isolation:</b> stop motion, support the yoke, "
        "then disconnect the AC plugs of the12V,24V and Pi supplies. "
        "Keep all three disconnected plugs under the servicing "
        "person's exclusive control. Check absence of voltage at "
        "X1:1/2,3/4,13/2 and Pi5V/GND before work. If exclusive "
        "control is not possible, provide a site-approved lockable "
        "isolation method. E-stop is not service isolation. Do not "
        "unmate the DC connectors while energized.",
    ]:
        y = para(c, text, 55, y, 1080, SMALL)
    if y < 70:
        raise ValueError("Harness page overflow")


def supplier_page(book):
    c = book.page(
        "RFQ-001",
        "Supplier confirmation / interface release",
        "Send the relevant drawings with this sheet | record actual "
        "responses before closing P2",
    )
    rows = [
        ["Interface", "Required written confirmation", "Evidence / result"]
    ]
    rows += [
        [
            "Dynatect EAS12",
            "Two6.000mm nominal bores; shaft-to-shaft "
            "configuration; bore tolerance, insertion depth both ends, "
            "setscrew positions, wrench access and approved shaft flat.",
            "Drawing/revision: ____________________",
        ],
        [
            "Clutch performance",
            "Stable bidirectional0.20Nm nominal "
            "slip; minimum adjustment range, breakaway/running variation, "
            "thermal drift, allowable slip duty and service life.",
            "Supplier response: ___________________",
        ],
        [
            "HIWIN MGN7C",
            "MGNR7 rail100mm;7holes at15mm pitch,5mm end "
            "distance; block length/seal code; confirm actual M2 thread "
            "pitch and maximum engagement2.5mm.",
            "Order code: _________________________",
        ],
        [
            "ROBOTIS horn",
            "Included horn PCD16; actual center bolt "
            "head and projection; verify B122 recess clearance>=0.5mm "
            "and1.8mm screw engagement before coupling.",
            "Measured clearance: ________________",
        ],
        [
            "Shaft stack",
            "Apply the approved clutch insertion data to "
            "B113/B122; record pedestal shift, shaft end gaps and flat "
            "clocking. Confirm no axial preload.",
            "Updated drawings: ___________________",
        ],
    ]
    y = table(c, rows, 45, 710, [190, 620, 290], 10)
    para(
        c,
        "<b>Disposition:</b> accepted / revise design / reject "
        "substitution<br/>Mechanical owner ____________________  "
        "Supplier ____________________  Date __________<br/>"
        "Attach supplier drawing, quotation and received-part inspection. "
        "A catalogue maximum torque is not proof of reliable operation "
        "at the much lower requested setpoint.",
        55,
        y,
        1080,
    )


def phone_measurement_pages(book):
    c = book.page(
        "PM-001",
        "Actual-phone metrology / insert design input",
        "Owner decision: shop measures the phone before machining "
        "inserts | no assumed Apple dimensions",
    )
    y = para(
        c,
        "Device/model ____________________ Serial __________ "
        "Case fitted / bare __________ Inspector __________ "
        "Date __________<br/>Instrument ID __________ Resolution "
        "__________ Calibration __________ Photos/datum sketch "
        "reference __________",
        50,
        710,
        1080,
    )
    rows = [["Measurement / datum", "Method and required record", "Actual mm"]]
    rows += [
        [
            "Datum A / B / C",
            "A=fixed-half supported back plane; "
            "B=long side edge; C=end face. Attach an annotated actual "
            "phone photograph showing the datums and axes.",
            "__________",
        ],
        [
            "Half lengths L1 / L2",
            "Measure each half independently; "
            "record corner radii and taper at the contact locations.",
            "____ / ____",
        ],
        [
            "Half widths W1 / W2",
            "Measure from hinge-side boundary "
            "to outer edge; distinguish case/frame from active display.",
            "____ / ____",
        ],
        [
            "Contact thickness T1 / T2",
            "Measure at each planned "
            "clamp/support point; photograph the point labels.",
            "____ / ____",
        ],
        [
            "Camera and other protrusions",
            "Record outline, XY position "
            "from B/C and height above A. Include cable plugs in the "
            "required swept envelope.",
            "__________",
        ],
        [
            "Keep-out map",
            "Outline display, hinge seam, buttons, ports, "
            "speakers and fragile finishes. No pad or retaining finger "
            "may land in a keep-out.",
            "Drawing ____",
        ],
        [
            "Mass / moving-half load",
            "Weigh whole phone; measure "
            "assembled moving torque using the approved dummy before "
            "selecting final counterweight settings.",
            "____ g",
        ],
        [
            "Permitted test angles",
            "Obtain owner/device limits; never "
            "force a mechanical endpoint to discover range.",
            "____ to ____ deg",
        ],
    ]
    y = table(c, rows, 45, y - 6, [210, 680, 210], 10)
    para(
        c,
        "<b>Insert release deliverables:</b> dimensioned insert "
        "drawings with datum/fastener pattern, material and finish; "
        "pad thickness/adhesive; retention method; actual-device "
        "keep-out overlay; dummy drawing; and approved contact "
        "photographs. Record clearance and pad compression at every "
        "contact. The two current flat trays are mounting interfaces, "
        "not completed phone-retention fixtures.",
        55,
        y,
        1080,
    )

    c = book.page(
        "PM-002",
        "Hinge-motion and fit acceptance record",
        "Measure without forcing the phone | fixture angle0=open; "
        "record any restricted range",
    )
    y = para(
        c,
        "Place the fixed half on a protected reference support. "
        "Track at least two non-collinear fiducials on the moving "
        "half with a calibrated optical or coordinate method. "
        "Record moving-back-plane translation and rotation relative "
        "to datum A at each angle; do not infer a stationary hinge "
        "axis from the phone's exterior seam.",
        50,
        710,
        1080,
    )
    rows = [
        [
            "Fixture angle",
            "Measured angle",
            "Delta X mm",
            "Delta Z mm",
            "Remaining float mm",
            "Contact / interference",
        ]
    ]
    rows += [
        [
            f"{angle} deg",
            "________",
            "________",
            "________",
            "________",
            "________________________",
        ]
        for angle in (0, 30, 60, 90, 120, 150, 180)
    ]
    y = table(c, rows, 45, y, [130, 140, 140, 140, 170, 280], 10)
    for text in [
        "<b>Compliance decision:</b> required measured travel "
        "________mm; uncertainty ________mm; reserved margin "
        "________mm. The present guide provides only one-axis "
        "translation, nominally +/-5.7..6.0mm. If measured out-of-plane "
        "motion or rotation cannot be accommodated by the released "
        "contacts, revise the fixture before testing the phone.",
        "<b>Dummy acceptance:</b> no display/hinge-seam load; no "
        "retainer migration; retained at every permitted angle; no "
        "travel-stop contact in normal motion; no pad snag or cable "
        "tension. Record the worst contact clearance and force. "
        "Use a force gauge; servo current is not a contact-force reading.",
        "<b>P1 disposition:</b> approved / revise / rejected<br/>"
        "Final insert drawing IDs ____________________ "
        "Dummy drawing __________<br/>Mechanical owner __________ "
        "Shop lead __________ Date __________<br/>"
        "Attach the completed measurement file and actual-device "
        "photographs to the bench serial record.",
    ]:
        y = para(c, text, 55, y, 1080)


def assembly_book(checks):
    book = Book(
        DOCS / "Foldatron-Rev-B-assembly-traveler.pdf",
        "foldatron Rev B - technical assembly traveler",
    )
    c = book.page(
        "AT-000",
        "Assembly traveler",
        "A separate shop document | follow the operation order | "
        "record every inspection",
    )
    picture(c, "fixture-iso.png", 40, 135, 760, 560)
    y = 700
    for text in [
        "<b>Before starting</b><br/>Read GA-001 and QA-001 in "
        "the drawing book. This is a development issue with "
        "four explicit release holds. Work may proceed only "
        "to the hold identified in each operation.",
        "<b>Part identity</b><br/>Bxxx identifies a custom part; "
        "Vxx a purchased component; Fxx a fastener. Match "
        "part marking to the drawing, not to color in a view.",
        "<b>Record</b><br/>Bench serial __________<br/>"
        "Builder __________<br/>Inspector __________<br/>"
        "Drawing issue __________<br/>Start date __________",
    ]:
        y = para(c, text, 830, y, 300)
    steps = assembly_steps()
    for number, step in enumerate(steps, 1):
        c = book.page(
            f"AT-{number:03d}",
            f"{number:02d} / {step['title']}",
            step["parts"],
        )
        picture(c, step["view"], 40, 210, 720, 500)
        y = 705
        for i, action in enumerate(step["actions"], 1):
            y = para(c, f"<b>{i}.</b> {escape(action)}", 790, y, 345)
        y = para(
            c,
            f"<b>Inspection / stop point</b><br/>{escape(step['check'])}",
            790,
            y - 8,
            345,
        )
        if y < 85:
            raise ValueError(f"Assembly text overflow: {step['title']}")
        c.setFillColor(PALE)
        c.roundRect(50, 80, 695, 108, 5, fill=1, stroke=0)
        para(
            c,
            "<b>SHOP RECORD</b><br/>"
            "Actual measurement / observation: "
            "______________________________________<br/>"
            "_________________________________________________________________<br/>"
            "Assembler __________   Inspector __________   Date "
            "__________   Pass / Hold",
            65,
            171,
            660,
        )
    phone_measurement_pages(book)
    verification_page(book, checks)
    book.save()


def assembly_steps():
    return json.loads((DATA / "assembly-operations.json").read_text())


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    parts = json.loads((DATA / "custom-parts.json").read_text())
    sources = json.loads((DATA / "source-register.json").read_text())
    bom = json.loads((DATA / "bom.json").read_text())["items"]
    checks = json.loads((DATA / "verification.json").read_text())
    drawing_book(parts, sources, bom, checks)
    assembly_book(checks)
    print("Created drawing book and separate assembly traveler")


if __name__ == "__main__":
    main()
