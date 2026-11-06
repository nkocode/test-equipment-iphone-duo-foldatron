"""Package tracked project files and identified local vendor references."""

import argparse
import hashlib
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "hardware/rev-b"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    tracked = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
        .decode()
        .split("\0")
    )
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    files = [(ROOT / name, "project/" + name) for name in tracked if name]
    sources = json.loads((DATA / "source-register.json").read_text())
    for source in sources:
        if not source.get("sha256"):
            continue
        path = DATA / "vendor" / source["filename"]
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != source["sha256"]:
            raise ValueError(f"Changed vendor file: {path.name}")
        files.append((path, "vendor-references/" + path.name))
    for name in (
        "adafruit-permaproto-LICENSE.txt",
        "adafruit-permaproto-README.md",
    ):
        files.append((DATA / "vendor" / name, "vendor-references/" + name))
    intro = (
        "# foldatron Rev B engineering review handoff\n\n"
        f"Project commit: {commit}\n\n"
        "Start with project/hardware/rev-b/README.md and the two PDFs in "
        "project/docs/rev-b/. The separate assembly traveler has 20 "
        "operations plus phone metrology and acceptance records.\n\n"
        "The package contains the Python src layout, FastAPI/OpenAPI, "
        "deployment files, tests, current Rev B CAD/drawings/BOM and "
        "rebuild tools. Open project/visualization/index.html for the "
        "offline Rev B CAD motion study and assembly walkthrough. "
        "Earlier manuals outside docs/rev-b are Rev A history.\n\n"
        "NOT A COMPLETE FABRICATION RELEASE. P1: shop measures the phone "
        "and releases contact inserts. P2: obtain configured clutch "
        "interfaces and confirm the guide thread. P3: physically verify "
        "guard and endpoint actuation. P4: complete electrical mounting, "
        "harness/probe details, fuse coordination and machine acceptance. "
        "See the release table for exact boundaries. No machine was "
        "built or physically tested.\n\n"
        "vendor-references/ contains original downloaded references "
        "for internal engineering use. They retain vendor copyrights; "
        "the project MIT license does not relicense them. Read the "
        "third-party notices for Adafruit CC BY-SA3.0 materials and "
        "the Raspberry Pi archive's included license.\n\n"
        "The source register includes URLs for references that could "
        "not be downloaded. Missing vendor STEP files have not been "
        "replaced with falsely attributed originals.\n"
    )
    manifest = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path, name in files
    }
    archive = output / "Foldatron-Rev-B-engineering-package.zip"
    with zipfile.ZipFile(
        archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6
    ) as bundle:
        bundle.writestr("START-HERE.md", intro)
        for path, name in sorted(files, key=lambda item: item[1]):
            bundle.write(path, name)
        bundle.writestr(
            "SHA256-MANIFEST.json", json.dumps(manifest, indent=2) + "\n"
        )
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        for name, expected in manifest.items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == expected
    for name in (
        "Foldatron-Rev-B-drawing-book.pdf",
        "Foldatron-Rev-B-assembly-traveler.pdf",
    ):
        shutil.copy2(ROOT / "docs/rev-b" / name, output / name)
    shutil.copy2(DATA / "bom.csv", output / "Foldatron-Rev-B-BOM.csv")
    shutil.copy2(
        DATA / "cad/foldatron-rev-b.step",
        output / "Foldatron-Rev-B-assembly.step",
    )
    (output / "Foldatron-Rev-B-START-HERE.md").write_text(intro)
    print(f"Verified {len(files)} packaged files at commit {commit}")
    print(f"Archive size: {archive.stat().st_size / 1_000_000:.1f} MB")


if __name__ == "__main__":
    main()
