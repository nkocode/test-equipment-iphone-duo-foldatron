"""Extract technical illustrations for the assembly traveler from sheets."""

import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "docs/rev-b/Foldatron-Rev-B-drawing-book.pdf"
SCRATCH = ROOT / "work/rev-b/extracts"
VIEWS = ROOT / "hardware/rev-b/views"


def main():
    SCRATCH.mkdir(parents=True, exist_ok=True)
    pages = subprocess.check_output(
        ["pdftotext", "-layout", str(PDF), "-"], text=True
    ).split("\f")
    illustrations = [
        ("E-005", "controller-board", (0.063, 0.17, 0.758, 0.787)),
        ("E-003", "cabinet-layout", (0.035, 0.145, 0.56, 0.875)),
        ("E-001", "stop-circuits", (0.038, 0.18, 0.95, 0.79)),
    ]
    for sheet, name, crop in illustrations:
        # The PDF text footer line also contains units and release status.
        matches = [
            i
            for i, text in enumerate(pages, 1)
            if any(
                line.strip().startswith(sheet)
                for line in text.splitlines()[-5:]
            )
        ]
        if len(matches) != 1:
            raise ValueError(f"Expected one sheet {sheet}: {matches}")
        prefix = SCRATCH / name
        subprocess.run(
            [
                "pdftoppm",
                "-f",
                str(matches[0]),
                "-singlefile",
                "-scale-to",
                "2000",
                "-png",
                str(PDF),
                str(prefix),
            ],
            check=True,
        )
        with Image.open(prefix.with_suffix(".png")) as image:
            bounds = tuple(
                round(value * image.size[i % 2])
                for i, value in enumerate(crop)
            )
            image.crop(bounds).save(VIEWS / f"{name}.png")
        print(f"Extracted {sheet} -> {name}")


if __name__ == "__main__":
    main()
