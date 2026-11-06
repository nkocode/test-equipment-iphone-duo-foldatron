"""Create the printable engineering manual with bundled document libraries."""

import html
import json
import re
import textwrap
from pathlib import Path

import reportlab
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE
OUTPUT = BASE / "docs/FoldBench-design-and-assembly.pdf"
FONT_DIR = Path(reportlab.__file__).parent / "fonts"
INK = colors.HexColor("#173243")
TEAL = colors.HexColor("#267e79")
pdfmetrics.registerFont(TTFont("Helvetica", str(FONT_DIR / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("Helvetica-Bold", str(FONT_DIR / "VeraBd.ttf")))
styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        "BodyFB",
        fontName="Helvetica",
        fontSize=9.3,
        leading=13.3,
        textColor=INK,
        spaceAfter=7,
        splitLongWords=True,
    )
)
styles.add(
    ParagraphStyle(
        "H1FB",
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=27,
        textColor=INK,
        spaceBefore=12,
        spaceAfter=15,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        "H2FB",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=TEAL,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        "H3FB",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=INK,
        spaceBefore=11,
        spaceAfter=6,
        keepWithNext=True,
    )
)
styles.add(
    ParagraphStyle(
        "CellFB",
        fontName="Helvetica",
        fontSize=8,
        leading=10.5,
        textColor=INK,
        splitLongWords=True,
    )
)
styles.add(
    ParagraphStyle(
        "CodeFB",
        fontName="Courier",
        fontSize=7.2,
        leading=10,
        backColor=colors.HexColor("#eef3f5"),
        leftIndent=8,
        spaceBefore=5,
        spaceAfter=8,
    )
)


def ascii_text(text):
    return text.translate(
        str.maketrans(
            {
                "–": "-",
                "—": "-",
                "−": "-",
                "→": "->",
                "×": "x",
                "±": "+/-",
                "≥": ">=",
                "≤": "<=",
                "°": " deg",
                "’": "'",
                "‘": "'",
                "“": '"',
                "”": '"',
                "‑": "-",
            }
        )
    )


def rich(text):
    text = html.escape(ascii_text(text))
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    text = re.sub(
        r"\[([^]]+)\]\((https?://[^)]+)\)",
        r'<link href="\2" color="#267e79">\1</link>',
        text,
    )
    return text


def para(text, style="BodyFB"):
    return Paragraph(rich(text), styles[style])


def table(rows):
    count = len(rows[0])
    width = 174 * mm
    fractions = {
        2: [0.30, 0.70],
        3: [0.24, 0.55, 0.21],
        4: [0.20, 0.12, 0.18, 0.50],
        6: [0.07, 0.05, 0.53, 0.08, 0.09, 0.18],
    }.get(count, [1 / count] * count)
    if count == 3 and rows[0][1] == "Qty":
        fractions = [0.22, 0.07, 0.71]
    if count == 3 and rows[0][0] == "Method":
        fractions = [0.10, 0.38, 0.52]
    data = [[para(cell, "CellFB") for cell in row] for row in rows]
    result = Table(
        data,
        colWidths=[width * value for value in fractions],
        repeatRows=1,
        hAlign="LEFT",
    )
    result.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9e9eb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, 0), 0.6, TEAL),
                (
                    "LINEBELOW",
                    (0, 1),
                    (-1, -1),
                    0.25,
                    colors.HexColor("#cbd7dc"),
                ),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f5f8f9")],
                ),
            ]
        )
    )
    return result


def markdown(path, story):
    lines = path.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("```"):
            block = []
            i += 1
            while i < len(lines) and not lines[i].startswith("```"):
                block.extend(
                    textwrap.wrap(lines[i], 105, replace_whitespace=False)
                    or [""]
                )
                i += 1
            story.append(Preformatted("\n".join(block), styles["CodeFB"]))
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                cells = [
                    cell.strip() for cell in lines[i].strip("|").split("|")
                ]
                if not all(re.fullmatch(r"[-: ]+", cell) for cell in cells):
                    rows.append(cells)
                i += 1
            story.extend([table(rows), Spacer(1, 8)])
            continue
        elif line.startswith("### "):
            story.append(para(line[4:], "H3FB"))
        elif line.startswith("## "):
            story.append(para(line[3:], "H2FB"))
        elif line.startswith("# "):
            story.append(para(line[2:], "H1FB"))
        else:
            if line.startswith("- "):
                line = "• " + line[2:]
            story.append(para(line))
        i += 1


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#b7cbd3"))
    canvas.line(18 * mm, 16 * mm, 192 * mm, 16 * mm)
    canvas.setFillColor(INK)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(
        18 * mm,
        11 * mm,
        "FoldBench | Revision A | Prototype - physical validation required",
    )
    canvas.drawRightString(192 * mm, 11 * mm, str(doc.page))
    canvas.restoreState()


story = [
    Spacer(1, 10 * mm),
    para("FOLDBENCH", "H1FB"),
    para("iPhone Duo endurance tester", "H2FB"),
    para("Design, procurement, assembly and Raspberry Pi control", "H3FB"),
    para("Revision A / 4 November 2026"),
    Spacer(1, 4 * mm),
]
bom = json.loads((ROOT / "hardware/BOM.json").read_text())
story.append(
    para(
        "A guarded single-phone folding fixture with current-limited "
        "actuation, independent endpoint verification, durable cycle "
        "records and an authenticated "
        "FastAPI interface. Includes a simulator and real hardware driver."
    )
)
story.append(
    Image(
        str(BASE / "docs/assets/layout.png"), width=164 * mm, height=123 * mm
    )
)
story.append(
    para(
        f"Station parts allowance: ${bom['station_total']:,.0f}; phone and "
        "fabrication labor excluded. Software checked locally; "
        "hardware unbuilt "
        "and unvalidated. Commission before any phone trial."
    )
)
story.append(PageBreak())
markdown(ROOT / "docs/DESIGN_AND_ASSEMBLY.md", story)
story += [PageBreak(), para("Assembly and wiring drawings", "H1FB")]
story.append(
    Image(
        str(BASE / "docs/assets/layout.png"), width=174 * mm, height=130.5 * mm
    )
)
story.append(
    para(
        "Editable vector originals and the OpenSCAD envelope model are in "
        "the hardware directory. Vendor mounting patterns and actual "
        "phone-contact profiles must be verified before fabrication."
    )
)
story += [PageBreak(), para("Power and signal architecture", "H1FB")]
story.append(
    Image(
        str(BASE / "docs/assets/wiring.png"), width=174 * mm, height=116 * mm
    )
)
story.append(
    para(
        "Use the detailed netlist and the manufacturer's current relay "
        "input schematic together. This drawing is a functional architecture, "
        "not a substitute for terminal-level safety-circuit verification."
    )
)
for path in [
    "hardware/BOM.md",
    "README.md",
    "docs/API.md",
    "docs/COMMISSIONING.md",
    "docs/VALIDATION.md",
]:
    story.append(PageBreak())
    markdown(ROOT / path, story)

doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=A4,
    rightMargin=18 * mm,
    leftMargin=18 * mm,
    topMargin=17 * mm,
    bottomMargin=22 * mm,
    title="FoldBench - iPhone Duo Design and Assembly",
    author="FoldBench engineering package",
    pageCompression=1,
)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUTPUT)
