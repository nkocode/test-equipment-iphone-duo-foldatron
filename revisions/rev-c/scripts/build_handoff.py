"""Build separate drawing and assembly review books from revision data.

All unresolved design interfaces are carried into both books. This script
must not silently promote a review into a manufacturing release.
"""

import csv
import json
from pathlib import Path

from build_review import (
    AMBER,
    INK,
    PALE,
    SMALL,
    TEAL,
    H,
    W,
    dimension,
    paragraph,
    table,
)
from reportlab.graphics import renderPDF
from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph
from svglib.svglib import svg2rlg

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA = ROOT / "hardware"
DATE = "2026-11-13"


def view(c, name, x, y, width, height):
    """Fit actual CAD ink bounds, excluding the exporter's empty canvas."""
    drawing = svg2rlg(str(DATA / "views" / name))
    left, bottom, right, top = drawing.getBounds()
    scale = min(width / (right - left), height / (top - bottom))
    dx = x + (width - (right - left) * scale) / 2
    dy = y + (height - (top - bottom) * scale) / 2
    c.saveState()
    c.translate(dx - left * scale, dy - bottom * scale)
    c.scale(scale, scale)
    renderPDF.draw(drawing, c, 0, 0)
    c.restoreState()


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
    c.drawString(42, 42, "DESIGN REVIEW - OPEN HOLDS - NOT FOR BUILD")
    c.setFillColor(INK)
    c.drawRightString(W - 42, 42,
                      f"foldatron | C-0.3 | {code} | mm | {DATE}")


def label(c, text, x, y, size=10, bold=False, color=INK):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, text)


def block(c, title, sub, x, y, width=180, height=65):
    c.setFillColor(PALE)
    c.setStrokeColor(TEAL)
    c.roundRect(x, y, width, height, 4, fill=1, stroke=1)
    label(c, title, x + 10, y + height - 21, 11, True)
    p = Paragraph(sub, SMALL)
    _, text_height = p.wrap(width - 20, height)
    p.drawOn(c, x + 10, y + height - 31 - text_height)


def line(c, x1, y1, x2, y2, text=None):
    c.setStrokeColor(TEAL)
    c.setLineWidth(1.3)
    c.line(x1, y1, x2, y2)
    if text:
        label(c, text, (x1 + x2) / 2 - 20, (y1 + y2) / 2 + 6, 8)


def electrical(c, x=60, y=170, scale=1):
    c.saveState()
    c.translate(x, y)
    c.scale(scale, scale)
    block(c, "MOTOR SUPPLY", "24 V isolated / F1", 0, 360, 150)
    block(c, "RO1", "13 -> 14", 190, 360, 120)
    block(c, "RO2", "43 -> 44", 350, 360, 120)
    block(c, "ZABER STAGE", "+24 V / PTB2", 510, 360, 150)
    for a, b in ((150, 190), (310, 350), (470, 510)):
        line(c, a, 392, b, 392)
    label(c, "W001/W002", 45, 439, 9)
    label(c, "W003", 307, 439, 9)
    label(c, "W004", 485, 439, 9)
    line(c, 70, 330, 585, 330, "Motor return W005")
    line(c, 70, 330, 70, 360)
    line(c, 585, 330, 585, 360)
    block(c, "E-STOP", "Two separate NC contacts", 0, 205, 190)
    block(c, "GUARD", "BNS / BPS, non-LED", 0, 105, 190)
    block(c, "SC10-2roe", "IN1/2 E-stop; IN3/4 guard<br/>"
          "IN5 monitored manual reset<br/>IO1/IO2 distinct test pulses",
          275, 125, 280, 145)
    line(c, 190, 237, 275, 237, "2 channels")
    line(c, 190, 137, 275, 137, "2 channels")
    block(c, "PHYSICAL RESET", "NO / separate local action", 0, 0, 190)
    line(c, 190, 32, 415, 32)
    line(c, 415, 32, 415, 125)
    label(c, "RO1 + RO2 enable only after both inputs healthy and reset",
          0, 292, 10, True)
    label(c, "Vacuum remains applied on protective stop.", 0, -27, 11,
          True)
    c.restoreState()


def pneumatic(c, x=60, y=170, scale=1):
    c.saveState()
    c.translate(x, y)
    c.scale(scale, scale)
    block(c, "FR1 / SV1", "Filter regulator / supply shutoff", 0, 375,
          240)
    block(c, "EJ1 + EJ2", "One ejector per phone half", 340, 375, 250)
    line(c, 240, 407, 340, 407, "T1 air tee")
    label(c, "Each ejector splits into TWO identical retained-cup branches",
          0, 342, 11, True)
    block(c, "VACUUM SPLITTER", "T2 or T3", 0, 245, 190)
    block(c, "CHECK VALVE", "H-QS-6 / arrow toward ejector", 260, 245, 300)
    line(c, 190, 277, 260, 277)
    line(c, 410, 245, 410, 205)
    block(c, "MANUAL RELEASE", "HE-3: 1 source; 2 cup; 3 atmosphere",
          260, 140, 300)
    block(c, "SDE5 SENSOR", "One-port sensing branch", 0, 20, 210)
    block(c, "CUP-SIDE TEE", "T4-T7: retained vacuum measurement",
          260, 20, 300)
    line(c, 410, 140, 410, 85, "Port 2")
    line(c, 210, 52, 260, 52)
    line(c, 560, 52, 650, 52)
    c.setStrokeColor(TEAL)
    c.circle(675, 52, 25)
    label(c, "CUP", 663, 48, 9, True)
    label(c, "Repeat x4. Release only after both phone halves are supported.",
          0, -30, 11, True)
    c.restoreState()


def io_diagram(c, x=60, y=170, scale=1):
    c.saveState()
    c.translate(x, y)
    c.scale(scale, scale)
    block(c, "Raspberry Pi 3B", "Python / FastAPI / SQLite", 200, 350, 300)
    block(c, "Zaber X-USBDC", "Separate USB / RS232 bus", 0, 210, 260)
    block(c, "ICP tM-7561", "Isolated USB / RS485", 370, 210, 260)
    line(c, 300, 350, 130, 275)
    line(c, 400, 350, 500, 275)
    block(c, "X-RSW60A-E03", "Address 1 / 115200 / 8N1", 0, 70, 260)
    block(c, "Waveshare 26244", "Address 1 / 9600 / 8N1", 370, 70, 260)
    line(c, 130, 210, 130, 135)
    line(c, 500, 210, 500, 135)
    block(c, "M-7018R", "Address 2 / 9600 / 8N1; CH0 + CH1", 370, -70,
          260)
    line(c, 500, 70, 500, -5)
    label(c, "DI1 = permit (bit 0)", 0, 25, 13, True)
    label(c, "DI2-DI5 = cup V1-V4 (bits 1-4)", 0, 3, 11)
    label(c, "DI COM = 0 V; outputs unwired", 0, -19, 11)
    c.restoreState()


def api_diagram(c, x=60, y=170, scale=1):
    c.saveState()
    c.translate(x, y)
    c.scale(scale, scale)
    items = [
        ("Authenticated REST", "/v1/status /runs /jogs /stop", 350),
        ("One controller worker", "Fresh telemetry and local limits", 235),
        ("Bounded serial commands", "Short segments; checked replies", 120),
        ("Durable records", "SQLite; interrupted run never resumes", 5),
    ]
    for title, sub, yy in items:
        block(c, title, sub, 90, yy, 470)
        if yy > 5:
            line(c, 325, yy, 325, yy - 50)
    label(c, "Physical E-stop and guard operate independently of this stack.",
          0, -40, 11, True)
    c.restoreState()


DIAGRAMS = {
    "electrical": electrical, "pneumatic": pneumatic,
    "io": io_diagram, "api": api_diagram,
}


def markdown_table(filename, header):
    lines = (DOCS / filename).read_text().splitlines()
    start = next(i for i, line in enumerate(lines)
                 if line.startswith(header))
    rows = []
    for line in lines[start:]:
        if not line.startswith("|"):
            break
        if set(line.replace("|", "").strip()) <= {"-", ":", " "}:
            continue
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


def assembly_book():
    path = DOCS / "Foldatron-Rev-C-assembly-manual.pdf"
    c = canvas.Canvas(str(path), pagesize=landscape(A3))
    c.setTitle("foldatron Rev C - illustrated assembly review")
    operations = json.loads((DOCS / "assembly-operations.json").read_text())
    for op in operations:
        sheet(c, "A" + op["number"], op["number"] + " / " + op["title"],
              "Purchased components only | Assembly sequence and acceptance")
        c.setFillColor(PALE)
        c.roundRect(42, 215, 610, 495, 6, fill=1, stroke=0)
        if "view" in op:
            view(c, op["view"], 52, 245, 590, 440)
            label(c, "CAD review view - not to scale", 58, 230, 9)
        else:
            DIAGRAMS[op["diagram"]](c, 60, 265, 0.79)
        y = paragraph(c, "<b>PARTS / TOOLS</b><br/>" + op["parts"],
                      680, 710, W - 725)
        for index, instruction in enumerate(op["instructions"], 1):
            y = paragraph(c, f"<b>{index}.</b> {instruction}",
                          680, y - 3, W - 725)
        paragraph(c, "<b>ACCEPTANCE</b><br/>" + op["checks"],
                  56, 190, 585)
        paragraph(c, "<b>HOLD / VERIFY</b><br/>" + op["hold"],
                  680, min(y - 8, 225), W - 725, SMALL)
        c.showPage()
    c.save()
    return path


def drawing_book():
    path = DOCS / "Foldatron-Rev-C-drawing-book.pdf"
    c = canvas.Canvas(str(path), pagesize=landscape(A3))
    c.setTitle("foldatron Rev C - technical design review")
    sheet(c, "D01", "General arrangement", "83 modeled components | "
          "Original vendor solids and identified reconstructed envelopes")
    view(c, "bench-iso.svg", 40, 130, 740, 570)
    paragraph(c, "<b>DESIGN BASIS</b><br/>762 x 762 x 660.4 frame; "
              "25.4 mm 1010 profiles. Purchased optical breadboard and "
              "rotary stage. Passive purchased XY bearing. Four outside-"
              "surface vacuum contacts allow a natural closed pose.",
              815, 700, 320)
    paragraph(c, "<b>DATUMS</b><br/>Origin at frame footprint center. "
              "Z=0 is support surface; front is negative Y. Rotary axis "
              "at (12.5, 12.5, 38.1). Fixture-local coordinates are "
              "relative to that axis. Views are not print-scale templates.",
              815, 550, 320)
    paragraph(c, "<b>MODEL LIMITS</b><br/>Fasteners, detailed cabinet "
              "mounts, latch/stop, pneumatic mounts and hose routes are "
              "not complete. A model count is not a complete BOM. "
              "Do not infer unmodeled mounting holes or a build release.",
              815, 395, 320)
    paragraph(c, "<b>DOCUMENTS</b><br/>This drawing book is separate "
              "from the 18-operation assembly manual. Electrical, "
              "pneumatic and fastener schedules provide the connection "
              "detail. The release register identifies every open hold.",
              815, 230, 320)
    c.showPage()

    sheet(c, "D02", "Structure / purchased cut schedule",
          "No shop machining, drilling, tapping or panel notching")
    view(c, "structure-front.svg", 45, 235, 625, 460)
    dimension(c, 80, 200, 625, 200, "762 outside")
    dimension(c, 55, 245, 55, 670, "660.4 outside height")
    table(c, [
        ["Qty", "1010 supplier cut", "Use"],
        [4, "762", "Upper/lower long frame rails"],
        [6, "711.2", "4 perimeter + 2 board supports"],
        [4, "609.6", "Vertical posts"],
        [2, "606.425", "Door stiles"],
        [2, "643.7252", "Door crossbars"],
        [2, "762", "Cabinet supports; mount detail open"],
        [1, "200", "Moving grip mast"],
        [1, "300", "Fixed grip mast"],
    ], 710, 710, [45, 135, 260])
    paragraph(c, "<b>Assembly targets:</b> breadboard supports at "
              "Y=+/-275; top faces Z=25.4. Board top Z=38.1. Posts centered "
              "at X/Y=+/-368.3. Confirm supplier tolerances before "
              "accepting the decimal cut lengths; extra decimals describe "
              "nominal geometry, not guaranteed manufacturing precision.",
              65, 165, 600)
    c.showPage()

    sheet(c, "D03", "Door / guard interface",
          "Front view | catalog hinge and switch mounting dimensions")
    view(c, "guard-front.svg", 45, 220, 650, 485)
    dimension(c, 100, 185, 625, 185, "Door outside width 694.5252")
    table(c, [
        ["Feature", "Nominal value / position"],
        ["Door outside height", "606.425"],
        ["Left / right edge X", "-354.0252 / +340.5"],
        ["Bottom / top edge Z", "26.9875 / 633.4125"],
        ["Hinge center Z", "150 and 510"],
        ["Handle center Z / pitch", "440 / 75.006"],
        ["Switch mounting lines X", "368.3 fixed / 327.8 door"],
        ["Switch hole pitch / gap", "22 / 2.5"],
        ["Right opening", "15.1; reach analysis required"],
        ["Panel edge capture", "6 nominal; gasket fit open"],
    ], 720, 710, [175, 250])
    paragraph(c, "Front frame plates go on the inside/back face. "
              "Do not use switch housings as stops. The current 300 mm "
              "radial motion allowance leaves 193.0 mm to the nearest "
              "latch opening in plan; hoses, reach and stopping time "
              "still require verification.", 65, 155, 600)
    c.showPage()

    sheet(c, "D04", "Fixture / open pose and datums",
          "Illustrative phone only | purchased rail, carrier and XY stack")
    view(c, "fixture-open-plan.svg", 50, 350, 620, 350)
    view(c, "fixture-open-iso.svg", 55, 90, 610, 275)
    table(c, [
        ["Fixture-local feature", "Nominal mm"],
        ["Rotating rail center X/Y", "112.5 / 12.5"],
        ["Rotating rail rear / front X", "-37.5 / +262.5"],
        ["Fixed rail center X/Y", "50 / -50"],
        ["Moving carrier center X", "110.099"],
        ["XY base center X/Y", "110.099 / 37.5"],
        ["XY total travel per axis", "25.4; qualify middle 20"],
        ["Cup contact plane X", "5, surrogate only"],
        ["Cup heights Z", "160 / 240, surrogate only"],
        ["Surrogate leaf dimensions", "70 x 160 x 5 each"],
    ], 705, 710, [230, 210])
    paragraph(c, "The actual phone is measured by the shop. The fixed "
              "and moving RC2 carriers are locked after setup; only the "
              "purchased plain XY stage floats. No hardware is placed "
              "between the closing display surfaces.", 715, 230, 410)
    c.showPage()

    sheet(c, "D05", "Moving interface / purchased mounting chain",
          "Exploded view | separation is illustrative")
    view(c, "assembly-xy-exploded.svg", 60, 160, 610, 540)
    table(c, [
        ["Order, bottom to top", "Interface"],
        ["RC2/M", "Locked carrier; M4 threads"],
        ["BA2/M + SD1", "M4 x 14; 5.491 engagement"],
        ["R451P-XY base", "#6 through bolts; 33.3248 pitch"],
        ["R451P-XY carriage", "#6-32 imperial threads"],
        ["AB90 + SD1", "#6-32 x 5/8; bearing review"],
        ["1010 mast", "M6 T-slot connection"],
        ["BA1/M / ESH / ESS", "Exterior vacuum contacts"],
    ], 710, 710, [190, 250])
    paragraph(c, "The BA2 slot nominally admits the two #6 shanks "
              "without machining. SD1 is marketed for #8/M4; the #6 "
              "head-bearing application remains M02. Do not treat this "
              "drawing as vendor approval of the mixed stack.",
              720, 300, 420)
    c.showPage()

    sheet(c, "D06", "Natural closure / sampled motion study",
          "Motor rotation is not a direct measurement of phone hinge angle")
    for name, x, title in [
        ("fixture-open-iso.svg", 45, "OPEN / 0 degree stage rotation"),
        ("fixture-midstroke-iso.svg", 425, "MID / 90 degree stage rotation"),
        ("fixture-closed-iso.svg", 805, "CLOSED / 180 degree stage rotation"),
    ]:
        view(c, name, x, 295, 340, 390)
        label(c, title, x + 5, 270, 10, True)
    paragraph(c, "<b>Calculated evidence:</b> the saved rigid-solid "
              "sweep checks 13 poses at 15 degree increments using B-rep "
              "intersection after bounding-box filtering. It found no "
              "overlap in those modeled moving/fixed solids. This is "
              "not continuous collision verification.", 60, 225, 510)
    paragraph(c, "<b>Excluded:</b> actual phone compound hinge motion, "
              "XY displaced positions, fasteners, hoses, cables, between-"
              "sample clearance and stop dynamics. Full natural closure "
              "is an acceptance requirement; no overtravel is allowed "
              "to force an ideal drawing endpoint.", 625, 225, 510)
    c.showPage()

    sheet(c, "D07", "Electrical / motor disconnect architecture",
          "Point-to-point details: electrical-installation.md | E01-E04 open")
    electrical(c, 65, 180, 1.05)
    paragraph(c, "<b>CONTROL POWER</b><br/>Independent fused 24 V "
              "supply feeds SC10, digital I/O, temperature module and "
              "sensors. Pi uses its own purchased 5 V supply. "
              "All mains remains inside factory equipment.",
              820, 700, 310)
    paragraph(c, "<b>PERMIT CONTACTS</b><br/>Control +24 -> RO1:23-24 "
              "-> RO2:53-54 -> Waveshare DI1. DI COM -> 0 V. "
              "This is a process permissive; it does not turn the API "
              "into a safety controller.", 820, 520, 310)
    paragraph(c, "<b>RELEASE GATE</b><br/>The actual Banner tool "
              "configuration and exported wiring report must verify "
              "input blocks, pulse-source support, terminal assignment, "
              "manual reset, no automatic restart and DC load rating.",
              820, 340, 310)
    c.showPage()

    sheet(c, "D08", "Pneumatic / independently retained cup branches",
          "Functional connection drawing | repeat retained branch four times")
    pneumatic(c, 60, 180, 1.0)
    paragraph(c, "<b>ORIENTATION</b><br/>Check-valve airflow is "
              "cup -> ejector. SDE5 Q6E has one sensing port. "
              "Sense downstream of the release valve. The release "
              "valve vents only a physically supported phone.",
              820, 700, 310)
    paragraph(c, "<b>ROUTING</b><br/>6 mm OD tube; 50 mm minimum "
              "design bend radius for moving loops. Keep all tubing "
              "outside the display gap and qualified guard-access "
              "allowance. Final cuts come from the actual route.",
              820, 500, 310)
    paragraph(c, "<b>QUALIFICATION</b><br/>Setpoints and holding "
              "force cannot be taken from ideal cup area. Measure "
              "retention, peel, surface marking, leak response and "
              "supply-loss behavior on the actual contact surface.",
              820, 300, 310)
    c.showPage()

    sheet(c, "D09", "I/O / process acquisition",
          "Physical terminal labels and zero-based software bit map")
    io_diagram(c, 70, 220, 1.0)
    table(c, [
        ["Signal", "Terminal", "Bit/channel"],
        ["Hardwired permit", "DI1", "0"],
        ["Fixed lower vacuum", "DI2", "1"],
        ["Fixed upper vacuum", "DI3", "2"],
        ["Moving lower vacuum", "DI4", "3"],
        ["Moving upper vacuum", "DI5", "4"],
        ["Phone exterior Type K", "CH0", "0"],
        ["Ambient Type K", "CH1", "1"],
    ], 775, 710, [185, 80, 100])
    paragraph(c, "The software map uses zero-based wire addresses. "
              "Temperature engineering words are signed tenths of "
              "a degree C. Confirm firmware, channel type, CJC and "
              "open-wire behavior using actual hardware.",
              785, 270, 345)
    c.showPage()

    schedules = [
        ("F", "Fastener interface schedule", "fastener-schedule.md",
         "| Joint |", [180, 45, 310, 85, 85, 300], 8),
        ("E", "Electrical point-to-point schedule",
         "electrical-installation.md", "| Wire |",
         [65, 290, 340, 310], 15),
        ("P", "Pneumatic hose schedule", "pneumatic-installation.md",
         "| Labels |", [100, 50, 600, 355], 12),
    ]
    for prefix, title, filename, header, widths, count in schedules:
        entries = markdown_table(filename, header)
        for start in range(1, len(entries), count):
            page_number = (start - 1) // count + 1
            sheet(c, f"{prefix}{page_number:02}", title,
                  "Installation proposal | unresolved rows remain holds; "
                  "do not substitute nominal values for receiving checks")
            table(c, [entries[0]] + entries[start:start + count],
                  42, 710, widths, size=9)
            paragraph(c, "Controlling notes and manufacturer source links "
                      f"are in {filename}. This schedule is part of the "
                      "C-0.3 review package. Confirm polarity, thread form, "
                      "actual seating and catalog compatibility before "
                      "release. No custom adapter or machining is allowed.",
                      60, 150, 1050)
            c.showPage()

    with (DATA / "assembly-parts.tsv").open() as stream:
        parts = list(csv.DictReader(stream, delimiter="\t"))
    for start in range(0, len(parts), 10):
        number = 10 + start // 10
        sheet(c, f"D{number:02}", "Purchased parts / selection register",
              "Candidate and held items are explicit; not a complete "
              "purchase release | live URLs in assembly-parts.tsv")
        rows = [["ID", "Qty", "Vendor / part", "Description", "Status"]]
        for p in parts[start:start + 10]:
            rows.append([p["id"], p["qty"] + " " + p["unit"],
                         p["vendor"] + " / " + p["part_number"],
                         p["description"], p["status"]])
        table(c, rows, 42, 710, [60, 65, 305, 365, 310], size=9)
        c.showPage()
    register = json.loads((DOCS / "release-register.json").read_text())
    for number, entries in enumerate([
        register["design_holds"][:6], register["design_holds"][6:],
        register["physical_qualification"],
    ], 1):
        sheet(c, f"R{number:02}", "Release evidence / open items",
              "Design completion and physical qualification are separate")
        rows = [["Gate", "Subject", "Required evidence"]]
        rows += [[r["id"], r["subject"], r["required"]] for r in entries]
        table(c, rows, 42, 710, [65, 270, 770], size=11)
        paragraph(c, "No signature, pass result or physical measurement "
                  "has been invented. The complete current source and "
                  "saved tests travel with this revision. Close design "
                  "holds before issuing build instructions; close physical "
                  "qualification before unattended testing.",
                  60, 200, 1050)
        c.showPage()
    c.save()
    return path


def main():
    for path in (drawing_book(), assembly_book()):
        print(f"{path.name}: {path.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()
