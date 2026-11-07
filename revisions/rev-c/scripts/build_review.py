"Publish the development drawing review, with explicit release holds."

import csv
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.graphics import renderPDF
from reportlab.lib import colors
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Table, TableStyle
from svglib.svglib import svg2rlg

ROOT = Path(__file__).resolve().parents[1]
W, H = landscape(A3)
INK = colors.HexColor("#183846")
TEAL = colors.HexColor("#146b73")
PALE = colors.HexColor("#eef4f5")
AMBER = colors.HexColor("#98500c")
BODY = ParagraphStyle(
    "body", fontName="Helvetica", fontSize=11, leading=15, textColor=INK
)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=9, leading=12)
ROWS = [
    (
        "C101",
        "4",
        "80/20",
        "1010",
        "762 mm supplier cut",
        "Structure study",
        "https://8020.net/1010.html",
    ),
    (
        "C102",
        "4",
        "80/20",
        "1010",
        "711.2 mm supplier cut",
        "Structure study",
        "https://8020.net/1010.html",
    ),
    (
        "C103",
        "4",
        "80/20",
        "1010",
        "609.6 mm supplier cut",
        "Structure study",
        "https://8020.net/1010.html",
    ),
    (
        "C104",
        "2",
        "80/20",
        "1010",
        "711.2 mm breadboard supports",
        "Structure study",
        "https://8020.net/1010.html",
    ),
    (
        "C105",
        "12",
        "80/20",
        "4151",
        "76.2 x 76.2; 4.7752 thick",
        "Modeled interface",
        "https://8020.net/4151.html",
    ),
    (
        "C106",
        "60",
        "80/20",
        "3321",
        "5 screw/T-nut sets per 4151",
        "Not modeled",
        "https://8020.net/3321.html",
    ),
    (
        "C107",
        "8",
        "80/20",
        "4119",
        "Base corners/support connections",
        "Placement review",
        "https://8020.net/4119.html",
    ),
    (
        "C108",
        "16",
        "80/20",
        "3061 + 3382",
        "2 screw/T-nut pairs per 4119",
        "Placement review",
        "https://8020.net/4119.html",
    ),
    (
        "C109",
        "4",
        "80/20",
        "3873",
        "M6 nut for breadboard; screw TBD",
        "Stack open",
        "https://8020.net/3873.html",
    ),
    (
        "C110",
        "1",
        "Thorlabs",
        "MB6060/M",
        "600 x 600 x 12.7; M6/25 grid",
        "Original STEP",
        "https://www.thorlabs.com/",
    ),
    (
        "C111",
        "1",
        "Zaber",
        "X-RSW60A-E03",
        "60 mm rotary top; 24-48 V",
        "Original STEP",
        "https://www.zaber.com/products/rotary-stages/X-RSW-E",
    ),
    (
        "C112",
        "candidate",
        "Thorlabs",
        "RLA150/M",
        "150 mm dovetail rail",
        "Top interface only",
        "https://www.thorlabs.com/",
    ),
    (
        "C113",
        "candidate",
        "Thorlabs",
        "RC2/M",
        "M4 taps; 24.9936 mm CAD pitch",
        "Drag/retention open",
        "https://www.thorlabs.com/",
    ),
    (
        "C114",
        "candidate",
        "Thorlabs",
        "RC1",
        "25.4 mm carrier as stop",
        "Retention open",
        "https://www.thorlabs.com/",
    ),
    (
        "C115",
        "0",
        "Thorlabs",
        "FP01",
        "22.9 mm wide; 14.7 mm capacity",
        "REJECTED: closure gap",
        "https://www.thorlabs.com/",
    ),
    (
        "C116",
        "candidate",
        "Thorlabs",
        "DT12/M",
        "12.7 mm manual adjustment",
        "Mounting open",
        "https://www.thorlabs.com/",
    ),
    (
        "C120",
        "candidate",
        "80/20",
        "2086",
        "10-series metal hinge",
        "Door not released",
        "https://8020.net/2086.html",
    ),
    (
        "C121",
        "candidate",
        "80/20",
        "2643",
        "3 mm clear polycarbonate",
        "Panel sizes open",
        "https://8020.net/2643.html",
    ),
    (
        "C122",
        "candidate",
        "80/20",
        "2116",
        "10-series panel gasket",
        "Capture open",
        "https://8020.net/2116.html",
    ),
    (
        "C201",
        "1",
        "Banner",
        "SC10-2roe / 806222",
        "45 W x 115 H x 100 D",
        "Configuration open",
        "https://www.bannerengineering.com/us/en/products/part.806222.html",
    ),
    (
        "C202",
        "1",
        "Schmersal",
        "BNS 260-02Z-L",
        "101184385; 26 x 36 x 13",
        "Mounting open",
        "https://products.schmersal.com/en_IO/bns-260-02z-l-101184385",
    ),
    (
        "C203",
        "1",
        "Schmersal",
        "BPS 260-1",
        "101184395; matching actuator",
        "Mounting open",
        "https://products.schmersal.com/en_IO/bps-260-1-101184395",
    ),
    (
        "C204",
        "4",
        "80/20",
        "3666",
        "10-series M4 roll-in T-nut",
        "Mounting open",
        "https://8020.net/3666.html",
    ),
    (
        "C205",
        "1",
        "Schneider",
        "XALK178FH29",
        "Dual-NC complete E-stop station",
        "Wiring/mount open",
        "https://www.se.com/se/sv/product/XALK178FH29/",
    ),
    (
        "C206",
        "1",
        "Waveshare",
        "26244",
        "72 x 121 x 34; Modbus RTU I/O",
        "I/O map open",
        "https://www.waveshare.com/product/modbus-rtu-io-8ch.htm",
    ),
    (
        "C207",
        "1",
        "ICP DAS",
        "M-7018R",
        "76 x 120 x 42; thermocouple input",
        "Firmware/map open",
        "https://icpdasusa.com/m-7018r",
    ),
    (
        "C208",
        "1 pack",
        "Omega",
        "SA1-K",
        "5-pack; use 2; 13 x 19 x 0.5 pad",
        "Attachment open",
        "https://br.omega.com/omegaFiles/temperature/pdf/SA1.pdf",
    ),
    (
        "C209",
        "1",
        "ICP DAS",
        "tM-7561",
        "Isolated USB to RS485",
        "Bus design open",
        "https://www.icpdas.com/en/download/file.php?num=2724",
    ),
    (
        "C210",
        "1",
        "Raspberry Pi",
        "3 Model B",
        "Headless host; separate supply",
        "Mount/case open",
        "https://www.raspberrypi.com/products/raspberry-pi-3-model-b/",
    ),
]
ROWS.extend(
    [
        (
            "C150",
            "4 proposed",
            "Festo",
            "ESS-20-SN / 189294",
            "20 mm flat NBR cup; M6 vacuum thread",
            "Contact qualification open",
            "https://ftp.festo.com/public/PNEUMATIC/SOFTWARE_SERVICE/"
            "DataSheet/EN_GB/189294.pdf",
        ),
        (
            "C151",
            "4 proposed",
            "Festo",
            "ESH-HB-4-QS / 189209",
            "28 mm holder; M6 mount; 6 mm tube port",
            "Mount screw stack open",
            "https://ftp.festo.com/Public/PNEUMATIC/SOFTWARE_SERVICE/"
            "DataSheet/EN_GB/189209.pdf",
        ),
        (
            "C152",
            "2 proposed",
            "Thorlabs",
            "AB90",
            "50.8 x 50.8 x 38.1 angle; counterbored M6 slots",
            "Stock mounting candidate",
            "https://www.thorlabs.com/thorproduct.cfm?partnumber=AB90",
        ),
    ]
)


def paragraph(c, text, x, y, width, style=BODY):
    p = Paragraph(text, style)
    _, height = p.wrap(width, H)
    if y - height < 65:
        raise ValueError("Text exceeds drawing content area")
    p.drawOn(c, x, y - height)
    return y - height - 12


def table(c, rows, x, y, widths, size=9):
    style = ParagraphStyle(
        "cell", parent=SMALL, fontSize=size, leading=size + 3
    )
    cells = [[Paragraph(escape(str(v)), style) for v in row] for row in rows]
    t = Table(cells, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PALE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, 0), 0.8, TEAL),
                ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.lightgrey),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    _, h = t.wrap(sum(widths), H)
    if y - h < 65:
        raise ValueError("Table exceeds drawing content area")
    t.drawOn(c, x, y - h)
    return y - h - 16


def view(c, name, x, y, width, height):
    drawing = svg2rlg(str(ROOT / "hardware/views" / name))
    scale = min(width / drawing.width, height / drawing.height)
    drawing.scale(scale, scale)
    renderPDF.draw(drawing, c, x, y)


def sheet(c, code, title, subtitle):
    c.setStrokeColor(INK)
    c.setLineWidth(0.6)
    c.rect(24, 24, W - 48, H - 48)
    c.setFont("Helvetica-Bold", 23)
    c.setFillColor(INK)
    c.drawString(42, H - 65, title)
    c.setFont("Helvetica", 10)
    c.drawString(43, H - 87, subtitle)
    c.setStrokeColor(TEAL)
    c.line(42, H - 103, W - 42, H - 103)
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(AMBER)
    c.drawString(42, 42, "DEVELOPMENT REVIEW - NOT FOR BUILD")
    c.setFillColor(INK)
    c.drawRightString(
        W - 42, 42, f"foldatron | REV C-0.2 | {code} | mm | 2026-11-07"
    )


def dimension(c, x1, y1, x2, y2, label):
    c.setStrokeColor(TEAL)
    c.setFillColor(TEAL)
    c.setLineWidth(0.6)
    c.line(x1, y1, x2, y2)
    for x, y in [(x1, y1), (x2, y2)]:
        c.line(x - 3, y - 3, x + 3, y + 3)
    c.setFont("Helvetica", 10)
    if y1 == y2:
        c.drawCentredString((x1 + x2) / 2, y1 + 7, label)
    else:
        c.saveState()
        c.translate(x1 - 8, (y1 + y2) / 2)
        c.rotate(90)
        c.drawCentredString(0, 0, label)
        c.restoreState()


def main():
    docs = ROOT / "docs"
    docs.mkdir(exist_ok=True)
    sources = json.loads((ROOT / "hardware/sources.json").read_text())
    with (ROOT / "hardware/procurement-status.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "id",
                "study_quantity",
                "vendor",
                "part_number",
                "description",
                "status",
                "catalog_url",
            ]
        )
        for row in ROWS:
            values = list(row)
            if values[6] == "https://www.thorlabs.com/":
                values[6] = next(
                    source["url"]
                    for source in sources
                    if source["part"] == values[3]
                    and source["file"].endswith(".pdf")
                )
            writer.writerow(values)
    checks = json.loads((ROOT / "hardware/interface-checks.json").read_text())
    path = docs / "Foldatron-Rev-C-structure-and-interface-review.pdf"
    c = canvas.Canvas(str(path), pagesize=(W, H))
    c.setTitle("foldatron Rev C - structure and interface review")
    c.setAuthor("foldatron engineering development")

    sheet(
        c,
        "C-000",
        "Rev C / Purchased-part architecture",
        (
            "A traceable development review, separate from the "
            "preserved Rev A and Rev B packages"
        ),
    )
    view(c, "structure-iso.svg", 35, 150, 720, 540)
    y = H - 140
    for text in [
        (
            "<b>1010 aluminum structure</b><br/>762 x 762 mm footprint."
            " A stock metric breadboard carries a complete rotary stage"
            " with a vertical axis."
        ),
        (
            "<b>What this package establishes</b><br/>Original CAD "
            "provenance, structure placements, measured mounting "
            "patterns and two rejected fastener lengths."
        ),
        (
            "<b>Full closure is required</b><br/>Back-surface vacuum "
            "grip, passive compliance, force protection, guard "
            "details and complete electrical wiring."
        ),
        (
            "<b>No fabrication permission</b><br/>Buy the catalog "
            "components. These reconstructed views are not drawings "
            "from which to manufacture substitutes."
        ),
        (
            f"<b>Evidence inventory</b><br/>{len(sources)} pinned "
            "vendor files. The structure STEP contains 28 instances; "
            "omitted hardware is listed explicitly."
        ),
    ]:
        y = paragraph(c, text, 790, y, 345)
    paragraph(
        c,
        (
            "The structure view omits door, panels, base brackets, "
            "fasteners, phone fixture and cabinet. No phone dimensions "
            "are assumed."
        ),
        60,
        128,
        680,
        SMALL,
    )
    c.showPage()

    sheet(
        c,
        "C-101",
        "Structure envelope and cut schedule",
        (
            "Proposed assembly dimensions; supplier cuts only; all "
            "lengths in millimetres"
        ),
    )
    x0, y0, scale = 115, 175, 0.62
    c.setStrokeColor(INK)
    c.setFillColor(PALE)
    for x, z, w, h in [
        (0, 0, 762, 25.4),
        (0, 635, 762, 25.4),
        (0, 25.4, 25.4, 609.6),
        (736.6, 25.4, 25.4, 609.6),
    ]:
        c.rect(x0 + x * scale, y0 + z * scale, w * scale, h * scale, fill=1)
    dimension(c, x0, y0 - 36, x0 + 762 * scale, y0 - 36, "762.0 OVERALL")
    dimension(c, x0 - 40, y0, x0 - 40, y0 + 660.4 * scale, "660.4 FRAME")
    dimension(
        c,
        x0 + 25.4 * scale,
        y0 + 350 * scale,
        x0 + 736.6 * scale,
        y0 + 350 * scale,
        "711.2 CLEAR",
    )
    dimension(
        c,
        x0 + 800 * scale,
        y0 + 25.4 * scale,
        x0 + 800 * scale,
        y0 + 635 * scale,
        "609.6 CLEAR",
    )
    y = table(
        c,
        [
            ["ID", "Qty", "Length", "Location"],
            ["C101", 4, "762.0", "Front/rear, base and roof"],
            ["C102", 4, "711.2", "Side rails, base and roof"],
            ["C103", 4, "609.6", "Four vertical posts"],
            ["C104", 2, "711.2", "Breadboard supports at Y +/-275"],
        ],
        730,
        H - 140,
        [55, 40, 65, 215],
    )
    for text in [
        (
            "Order 80/20 1010, square cuts, no end taps or access "
            "holes. Door profiles are not included in this schedule."
        ),
        (
            "Coordinate origin: center of the footprint, bench surface "
            "Z=0. Base rail centers Z=12.7; roof rail centers Z=647.7; "
            "posts span Z=25.4 to 635.0."
        ),
        (
            "C105 exterior plates use five C106 screw/T-nut assemblies "
            "each. Eight plates join posts in front/rear planes; four "
            "join roof corners. Base corner/support brackets remain to "
            "be modeled."
        ),
        (
            "Slot interiors in the CAD are indicative. Panel capture, "
            "fastener bottoming, frame stiffness and door clearances "
            "require closure before release."
        ),
    ]:
        y = paragraph(c, text, 730, y, 375)
    c.showPage()

    sheet(
        c,
        "C-102",
        "Purchased breadboard and stage placement",
        (
            "Original Thorlabs and Zaber STEP geometry; plan view; no "
            "fabricated base plate"
        ),
    )
    view(c, "base-plan.svg", 35, 110, 690, 580)
    y = table(
        c,
        [
            ["Interface", "Design value"],
            ["Breadboard", "MB6060/M; 600 x 600 x 12.7"],
            ["Grid", "M6 x 1; 25 mm spacing; 12.5 mm edge offset"],
            ["Board bottom / top Z", "25.4 / 38.1"],
            ["Rotary axis X, Y", "12.5, 12.5 relative to board center"],
            ["Stage support Z", "38.1"],
            [
                "Board fasteners",
                "Four corner counterbores; supports at Y +/-275",
            ],
        ],
        755,
        H - 140,
        [125, 270],
    )
    y = paragraph(
        c,
        (
            "<b>Three stage base screws</b><br/>In the modeled "
            "orientation, breadboard coordinates are (-12.5, -12.5), "
            "(-12.5, 37.5), and (37.5, -12.5). The fourth quadrant is "
            "not a fourth mounting hole."
        ),
        755,
        y,
        395,
    )
    paragraph(
        c,
        (
            "The base mounting CAD has 5.5 mm seating height. Screw "
            "lengths and washers for the breadboard and its 10-series "
            "T-nuts are still open; do not reuse Rev B hardware by "
            "assumption."
        ),
        755,
        y,
        395,
    )
    c.showPage()

    sheet(
        c,
        "C-103",
        "Rotary stage / catalog interface",
        (
            "Zaber X-RSW60A-E03 - original CAD; model placement is "
            "separate from functional qualification"
        ),
    )
    view(c, "stage-iso.svg", 35, 290, 690, 400)
    view(c, "stage-plan.svg", 120, 75, 440, 230)
    y = table(
        c,
        [
            ["Feature", "Manufacturer data / CAD observation"],
            ["Rotating top", "Diameter 60 mm"],
            [
                "Metric pattern",
                "4 x M6 x 1 on 25 mm square; drawing depth 6.5",
            ],
            ["Imperial pattern", "Separate #8-32 pattern; do not substitute"],
            ["Height", "31.75 CAD; 31.7 rounded drawing"],
            [
                "Supply / link",
                "24-48 V; RS232 ASCII; M8 power path also present",
            ],
            ["Encoder", "Motor-side measurement; not phone angle sensing"],
        ],
        750,
        H - 140,
        [115, 280],
    )
    paragraph(
        c,
        (
            "<b>Design hold C3</b><br/>The published 2.25 N m "
            "continuous-torque capability is not an allowable phone "
            "load. Current limiting does not establish hinge torque. "
            "Force protection and safe release of retained load remain "
            "unresolved."
        ),
        750,
        y,
        395,
    )
    c.showPage()

    sheet(
        c,
        "C-104",
        "Rail mounting and blind-thread engagement",
        (
            "Candidate interface only - original CAD stack; inspect "
            "received parts before selecting screws"
        ),
    )
    view(c, "top-interface-iso.svg", 35, 235, 695, 460)
    y = table(
        c,
        [
            ["Check", "Result"],
            ["Rail", "RLA150/M; 5 mounting positions at 25 mm pitch"],
            ["Stage row", "Two adjacent metric holes; offset 12.5 from axis"],
            [
                "Seat stack",
                "2.54 nominal from STEP support plane to screw seat",
            ],
            ["M6 x 8 candidate", "8 - 2.54 = 5.46 nominal projection"],
            [
                "M6 x 10 rejected",
                "10 - 2.54 = 7.46; exceeds drawing depth 6.5",
            ],
        ],
        750,
        H - 140,
        [130, 265],
    )
    y = paragraph(
        c,
        (
            "The modeled top holes are 5.75 mm deep; the vendor drawing"
            " calls out 6.5 mm. Treat this as a source discrepancy. "
            "Verify actual usable thread and screw clearance; do not "
            "lengthen screws based only on the drawing."
        ),
        750,
        y,
        395,
    )
    paragraph(
        c,
        (
            "The offset rail does not place the phone hinge on the "
            "rotary axis. Transverse adjustment, carrier retention and "
            "acceptable drag are open interfaces."
        ),
        750,
        y,
        395,
    )
    paragraph(
        c,
        (
            "This STEP study shows only stage + rail. It contains no "
            "fitted phone, passive slide qualification, end stops or "
            "released fastener assembly."
        ),
        65,
        165,
        620,
        SMALL,
    )
    c.showPage()

    sheet(
        c,
        "C-105",
        "Rejected edge contacts / retained fit audit",
        (
            "Actual clamp and carrier geometry - no phone envelope or "
            "force limit is invented"
        ),
    )
    view(c, "clamp-iso.svg", 35, 365, 600, 310)
    view(c, "carrier-iso.svg", 35, 75, 600, 300)
    y = table(
        c,
        [
            ["Item / check", "Finding"],
            ["FP01", "Single M4 counterbore; 22.9 wide; 14.7 capacity"],
            ["RC2/M", "2 M4 taps; 6 mm usable thread; measured pitch 24.9936"],
            [
                "FP02 direct pair",
                "25.4 mm clearance-hole pitch; not approved on RC2/M",
            ],
            [
                "FP01 + M4 x 8",
                "Nominal 5.714 mm engagement; inspection pending",
            ],
            ["FP01 + M4 x 10", "7.714 mm projection; rejected"],
        ],
        690,
        H - 140,
        [125, 330],
    )
    for text in [
        (
            "<b>Owner decision: full closure required</b><br/>Edge "
            "clamps are rejected for the working fixture. Their jaws "
            "occupy the closing gap. The replacement uses outside-"
            "surface vacuum contacts; qualification remains open."
        ),
        (
            "<b>Contact decision</b><br/>Measure the actual phone. "
            "Identify rigid, permissible contact areas; exclude "
            "display, buttons, ports, cameras and hinge. No custom "
            "insert is permitted."
        ),
        (
            "<b>Compliance decision</b><br/>The RC carrier is a spring-"
            "loaded dovetail. Measure breakaway and running drag under "
            "the intended load. A loose carrier knob is not a proven "
            "bearing or torque limiter."
        ),
    ]:
        y = paragraph(c, text, 690, y, 455)
    c.showPage()

    sheet(
        c,
        "C-106",
        "Outside-surface vacuum contacts / catalog interfaces",
        "Replacement direction for full closure; purchasing and "
        "phone-load qualification remain on hold",
    )
    view(c, "vacuum-bracket-iso.svg", 35, 260, 560, 410)
    paragraph(
        c,
        "<b>AB90 - original Thorlabs CAD</b><br/>50.8 mm legs; "
        "38.1 mm width; nominal 8.9 mm wall. Both faces have a "
        "counterbored slot for M6 cap screws and washers. The drawing "
        "places slot arc centers 25.4 mm apart. This is a purchased "
        "bracket, not permission to machine a substitute.",
        55,
        245,
        505,
    )
    y = table(
        c,
        [
            ["Candidate", "Catalog interface"],
            ["ESS-20-SN / 189294", "20 mm cup; NBR; M6 x 1 plug"],
            ["Cup drawing", "L1 11.6; plug L2 2.4; suction stroke 1.8"],
            ["ESH-HB-4-QS / 189209", "M6 female mount; M6 cup seat"],
            ["Holder drawing", "H1 28; D7 12; side port QS-6"],
            ["AB90", "Stock M6 counterbored slots; adjustment by sliding"],
            ["Quantity direction", "2 cups per outside leaf; 4 total"],
        ],
        620,
        H - 140,
        [205, 315],
        size=10,
    )
    for text in [
        "<b>Interface chain</b><br/>Purchased support - AB90 - "
        "M6 screw through slot - ESH holder - matching ESS cup. "
        "Screw length, usable holder thread and support connection "
        "remain unverified; no drilling or tapped adapters are allowed.",
        "<b>Contact limitation</b><br/>The 189294 datasheet lists "
        "16.3 N holding and 11.5 N lateral force at -0.7 bar. These "
        "are catalog values, not allowable phone loads, peel capacity "
        "or a certified grip on coated phone surfaces.",
        "<b>Vacuum system still required</b><br/>Select a purchased "
        "generator, branch monitoring, hoses, filter and retained-grip "
        "stop/recovery arrangement. Do not release vacuum on a motor "
        "stop and let the phone fall. Cup slip is not a torque limiter.",
    ]:
        y = paragraph(c, text, 620, y, 520)
    c.showPage()

    sheet(
        c,
        "C-107",
        "Full closure / contact-envelope study",
        "Owner requirement: full natural closure. Illustrative "
        "single-axis surrogate, not measured iPhone geometry",
    )
    view(c, "closure-sequence.svg", 150, 360, 890, 350)
    y = table(
        c,
        [
            ["Study input", "Value / boundary"],
            ["Surrogate leaf", "70 mm wide x 5 mm thick; not phone data"],
            ["Grip envelope", "20 mm wide x 40 mm deep; 40 mm radius"],
            ["Sweep", "361 positions at 0.5 degree increments"],
            ["Result", "No overlap of these four 2D envelopes"],
            ["Not included", "Supports, cables, hoses, real hinge path"],
        ],
        50,
        330,
        [180, 400],
        size=10,
    )
    paragraph(
        c,
        "<b>Physical endpoint</b><br/>Measure the natural closed "
        "state on the actual phone. An ideal diagram at zero opening "
        "angle does not authorize forcing a phone to zero degrees. "
        "Record hinge motion and clearance over the full path.<br/><br/>"
        "<b>What this study establishes</b><br/>Moving the contacts "
        "outside the leaves removes the edge-jaw obstruction in the "
        "simplified model. It does not establish that the complete "
        "stock mounting chain clears, retains the phone, or limits load. "
        "The separate phone measurement traveler defines the evidence "
        "needed before detailed fixture release.",
        670,
        325,
        465,
    )
    c.showPage()

    sheet(
        c,
        "C-201",
        "Controls / independent stop architecture",
        (
            "Functional block diagram only - terminal wiring and "
            "safety-controller configuration are not released"
        ),
    )
    blocks = [
        (70, 520, 220, 100, "Dual-NC E-stop", "Schneider XALK178FH29"),
        (70, 335, 220, 100, "Dual-contact guard", "BNS 260-02Z-L + BPS 260-1"),
        (
            400,
            420,
            245,
            120,
            "Purchased safety controller",
            "Banner SC10-2roe",
        ),
        (
            785,
            420,
            285,
            120,
            "Motor power interruption",
            "Zaber 24 V supply path",
        ),
        (400, 175, 245, 100, "Raspberry Pi 3B", "API, sequence and records"),
        (
            785,
            175,
            285,
            100,
            "Factory I/O + probes",
            "Waveshare / ICP DAS / Omega",
        ),
    ]
    for x, y, w, h, title, detail in blocks:
        c.setFillColor(PALE)
        c.setStrokeColor(TEAL)
        c.roundRect(x, y, w, h, 6, fill=1)
        paragraph(
            c, f"<b>{title}</b><br/>{detail}", x + 14, y + h - 20, w - 28
        )
    c.setStrokeColor(TEAL)
    c.setLineWidth(1.3)
    for points in [
        (290, 570, 400, 505),
        (290, 385, 400, 455),
        (645, 480, 785, 480),
        (645, 225, 785, 225),
    ]:
        c.line(*points)
    paragraph(c, "Separate monitored pairs", 300, 640, 330, SMALL)
    paragraph(
        c, "Physical reset only. No automatic restart.", 400, 385, 300, SMALL
    )
    paragraph(
        c,
        (
            "Pi observes permit and commands motion; it does not "
            "replace the hardwired stop function."
        ),
        70,
        135,
        1020,
        SMALL,
    )
    c.showPage()

    sheet(
        c,
        "C-202",
        "Electrical interface checks",
        (
            "Purchasable modules replace Rev B's custom interface "
            "board; fit and wiring remain controlled holds"
        ),
    )
    y = table(
        c,
        [
            ["Component", "Verified data", "Remaining work"],
            [
                "BNS 260-02Z-L",
                "26 x 36 x 13; two 4.5 mounting holes / 22 pitch; no LED",
                (
                    "Direct T-slot mounting, tamper resistance, gap and stop-"
                    "time validation"
                ),
            ],
            [
                "SC10-2roe",
                "45 x 115 x 100; 24 V; inputs 5 mA typical / 50 mA peak",
                (
                    "Separate guard/E-stop inputs; physical reset; validated "
                    "configuration"
                ),
            ],
            [
                "Current compatibility",
                "Non-LED BNS 260: 400 mA maximum; SC10 peak 50 mA",
                "Rating comparison only; circuit validation still required",
            ],
            [
                "Waveshare 26244",
                "72 x 121 x 34; DIN; 7-36 V; Modbus RTU",
                "DI polarity, address, stale-data behavior and wiring",
            ],
            [
                "M-7018R",
                "Manufacturer 76 x 120 x 42; Type K; 10-30 V",
                "Require firmware supporting open-wire detection; verify maps",
            ],
            [
                "Omega SA1-K",
                "Self-adhesive 13 x 19 x 0.5 pad; factory 1 m leads",
                "Phone surface suitability, lead routing and response check",
            ],
            [
                "Enclosure / harness",
                "Factory entries, stock rails, sealed external supplies",
                "Complete cable-entry plan, mounts, fuse schedule and BOM",
            ],
        ],
        45,
        H - 140,
        [175, 405, 520],
        size=10,
    )
    paragraph(
        c,
        (
            "Guard candidate differs from the early 80/20 22202 OSSD "
            "proposal. Do not mix their wiring. The original 22202 "
            "datasheet is retained solely as alternative-source "
            "evidence."
        ),
        55,
        y,
        1070,
    )
    c.showPage()

    for index, start in enumerate(range(0, len(ROWS), 16), 1):
        sheet(
            c,
            f"C-30{index}",
            "Procurement status / working register",
            (
                "Not a complete purchase BOM - candidate quantities and "
                "unresolved accessories are intentional holds"
            ),
        )
        table(
            c,
            [["ID", "Qty", "Vendor / part", "Description", "Status"]]
            + [
                [r[0], r[1], r[2] + " / " + r[3], r[4], r[5]]
                for r in ROWS[start : start + 16]
            ],
            43,
            H - 130,
            [55, 70, 280, 445, 255],
            size=9,
        )
        c.showPage()

    sheet(
        c,
        "C-400",
        "Assembly release gates",
        (
            "The next assembly traveler must close these items; none "
            "are delegated to undocumented shop fabrication"
        ),
    )
    table(
        c,
        [
            ["Gate", "Required evidence before release"],
            [
                "C1 / Phone contact",
                (
                    "Full natural closure; actual phone measurements; "
                    "purchased grip; stock mounting chain; no display "
                    "loading."
                ),
            ],
            [
                "C2 / Compliance",
                (
                    "Measured hinge path; retained slide travel; "
                    "breakaway/running drag; cyclic wear and contamination "
                    "behavior."
                ),
            ],
            [
                "C3 / Force protection",
                (
                    "Permitted phone loads; qualified independent "
                    "limiting/protection; retained-load recovery procedure."
                ),
            ],
            [
                "C4 / Structure and guard",
                (
                    "Fasteners and brackets; door/panel geometry; sensor "
                    "mounting; door gaps, stopping time and reach assessment."
                ),
            ],
            [
                "C5 / Electrical",
                (
                    "Factory enclosure entries; detailed wire/terminal "
                    "schedule; fuses; configuration record; supply load "
                    "budget."
                ),
            ],
            [
                "C6 / Software",
                (
                    "Rev C drivers and OpenAPI; communication/watchdog faults;"
                    " temperature open-wire and staleness; explicit local "
                    "commissioning."
                ),
            ],
            [
                "C7 / Handoff",
                (
                    "Complete BOM; separate assembly traveler; full "
                    "CAD interference review; documented physical acceptance."
                ),
            ],
        ],
        45,
        H - 140,
        [170, 930],
        size=11,
    )
    paragraph(
        c,
        (
            "The Rev B application uses a different actuator and I/O "
            "architecture. It must not be installed as a working Rev C "
            "hardware controller. Simulation and preserved historic "
            "viewers remain available independently."
        ),
        55,
        220,
        1060,
    )
    c.showPage()

    sheet(
        c,
        "C-900",
        "Source provenance and rebuild record",
        (
            "Every original download is pinned by SHA-256; original "
            "vendor ownership is retained"
        ),
    )
    y = paragraph(
        c,
        (
            f"<b>{len(sources)} original reference files</b> are indexed "
            "in hardware/sources.json. The JSON records exact URLs, "
            "retrieval date, byte count and checksum. Original files "
            "are retrieved with scripts/fetch_sources.py; --verify-only "
            "checks existing copies. The public repository contains "
            "the source register and our derived work, not a blanket "
            "redistribution of vendor manuals."
        ),
        50,
        H - 135,
        1090,
    )
    y = table(
        c,
        [
            ["Primary evidence", "Original source"],
            [
                "Zaber stage",
                "zaber.com - X-RSW60A-E03 STEP and X-RSW-E drawing",
            ],
            [
                "Thorlabs mechanism",
                "media.thorlabs.com - original part STEP and PDF assets",
            ],
            [
                "Banner controls",
                "info.bannerengineering.com - 174868 manual; 209332 drawings",
            ],
            [
                "Schmersal guard",
                "products.schmersal.com - BNS 260 operating instructions",
            ],
            [
                "I/O and probes",
                "icpdas.com - M-7018R data; br.omega.com - SA1 data",
            ],
            [
                "1010 structure",
                "8020.net - 1010, 4151, 3321, 4119 and mounting hardware",
            ],
            [
                "Vacuum contacts",
                "ftp.festo.com - ESS and ESH drawings; 189294/189209 data",
            ],
        ],
        45,
        y,
        [240, 860],
        size=10,
    )
    y = paragraph(
        c,
        (
            "<b>Rebuild sequence</b><br/>Use the repository Pipenv "
            "environment: fetch_sources.py, check_interfaces.py, "
            "build_structure.py, build_closure_study.py and "
            "build_review.py, all under "
            "revisions/rev-c/scripts. No new production dependency is "
            "required."
        ),
        50,
        y,
        1090,
    )
    paragraph(
        c,
        (
            f"<b>Measured audit</b><br/>{escape(checks['status'])}. "
            "Five hole-pattern checks pass. This is evidence about "
            "CAD interfaces, not proof of mechanical function, "
            "fatigue life, phone compatibility or machine safety."
        ),
        50,
        y,
        1090,
    )
    c.showPage()
    c.save()
    print(path)


if __name__ == "__main__":
    main()
