"""Create an independent Rev C source copy and integrity-checked download."""

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

REV = Path(__file__).resolve().parents[1]
ROOT = REV.parents[1]
OUT = ROOT.parents[1] / "outputs"


def runtime_copy():
    target = REV / "software/project"
    target.mkdir(parents=True, exist_ok=True)
    for filename in ("pyproject.toml", "Pipfile", "Pipfile.lock", "LICENSE"):
        shutil.copy2(ROOT / filename, target / filename)
    shutil.copytree(ROOT / "src", target / "src", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.egg-info"))
    shutil.copytree(ROOT / "tests/revc", target / "tests/revc",
                    dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__"))
    (target / "README.md").write_text(
        "# foldatron Rev C runtime source\n\n"
        "Self-contained source-layout copy of the maintained root package. "
        "Use Pipenv and `python -m foldbench.revc`. Simulation is the "
        "default. See ../README.md and ../protocols.md before installation. "
        "The original entry point remains for compatibility; it is not "
        "the Rev C driver. Regenerate this copy with package_review.py.\n"
    )


def main():
    runtime_copy()
    OUT.mkdir(exist_ok=True)
    files = []
    for path in sorted(REV.rglob("*")):
        relative = path.relative_to(REV)
        if not path.is_file() or any(part in {
            "vendor", "__pycache__", ".venv", ".pytest_cache",
        } for part in relative.parts):
            continue
        if path.name in {"SHA256.json", ".DS_Store"}:
            continue
        files.append(path)
    hashes = {
        str(p.relative_to(REV)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in files
    }
    manifest = REV / "SHA256.json"
    manifest.write_text(json.dumps({
        "revision": "C-0.3", "release": "DEVELOPMENT_REVIEW_NOT_FOR_BUILD",
        "files": hashes,
    }, indent=2) + "\n")
    files.append(manifest)
    archive = OUT / "Foldatron-Rev-C-engineering-review.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in files:
            bundle.write(path, path.relative_to(REV))
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None:
            raise ValueError("Archive integrity failed")
        for name, digest in hashes.items():
            if hashlib.sha256(bundle.read(name)).hexdigest() != digest:
                raise ValueError(name)
    for filename in ("Foldatron-Rev-C-drawing-book.pdf",
                     "Foldatron-Rev-C-assembly-manual.pdf"):
        shutil.copy2(REV / "docs" / filename, OUT / filename)
    shutil.copy2(REV / "visualization/index.html",
                 OUT / "Foldatron-Rev-C-assembly-viewer.html")
    shutil.copy2(REV / "hardware/assembly-parts.tsv",
                 OUT / "Foldatron-Rev-C-parts-register.tsv")
    shutil.copy2(REV / "README.md", OUT / "Foldatron-Rev-C-START-HERE.md")
    size = archive.stat().st_size
    print(f"{len(files)} files; ZIP verified; {size:,} bytes")


if __name__ == "__main__":
    main()
