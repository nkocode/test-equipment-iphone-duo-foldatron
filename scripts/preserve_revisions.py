"""Preserve exact tracked revision trees with per-file integrity manifests."""

import hashlib
import io
import json
import subprocess
import tarfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISIONS = (
    ("rev-a", "516acfc", "Concept design and original interactive explorer"),
    ("rev-b", "cffc8cf", "1010 CAD, drawing book, traveler and motion study"),
)


def main():
    for revision, ref, title in REVISIONS:
        commit = subprocess.check_output(
            ["git", "rev-parse", ref], cwd=ROOT, text=True
        ).strip()
        target = ROOT / "revisions" / revision
        target.mkdir(parents=True, exist_ok=True)
        raw = subprocess.check_output(
            ["git", "archive", "--format=tar", commit], cwd=ROOT
        )
        entries = {}
        with tarfile.open(fileobj=io.BytesIO(raw)) as archive:
            for member in archive.getmembers():
                if not member.isfile():
                    continue
                data = archive.extractfile(member).read()
                path = target / "project" / member.name
                if path.exists() and path.read_bytes() != data:
                    raise ValueError(f"Existing snapshot changed: {path}")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                entries[member.name] = hashlib.sha256(data).hexdigest()
        manifest = {"revision": revision, "commit": commit, "files": entries}
        (target / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )
        viewer = "project/visualization/index.html"
        drawings = (
            "project/docs/Foldatron-illustrated-assembly-manual.pdf"
            if revision == "rev-a"
            else "project/docs/rev-b/Foldatron-Rev-B-drawing-book.pdf"
        )
        (target / "README.md").write_text(
            f"# foldatron {revision.upper()} — preserved snapshot\n\n"
            f"{title}. Source commit: `{commit}`.\n\n"
            "Every tracked file from that commit is preserved byte-for-byte "
            "under `project/`, including controller source, dependencies, "
            "drawings, BOM, build scripts, tests and visualization. "
            "This snapshot is immutable; corrections belong in a later "
            "revision or a separate errata note.\n\n"
            f"- [Open/download the original viewer]({viewer})\n"
            f"- [Drawings / illustrated manual]({drawings})\n"
            "- [Full project index](project/README.md)\n"
            "- [Source-file SHA-256 manifest](manifest.json)\n\n"
            "Untracked virtual environments, downloaded vendor documents "
            "and local caches were never part of the Git source snapshot. "
            "Rev B source-register URLs and hashes identify the vendor "
            "references; the separately delivered engineering package "
            "also contains the acquired vendor files.\n\n"
            "Historical software and engineering holds remain as written. "
            "Archiving does not qualify the hardware or update dependencies.\n"
        )
        name = f"Foldatron-{revision.title()}-source-snapshot.zip"
        output = ROOT.parents[1] / "outputs" / name
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as bundle:
            for path in sorted(target.rglob("*")):
                if path.is_file():
                    bundle.write(path, str(path.relative_to(target)))
        with zipfile.ZipFile(output) as bundle:
            assert bundle.testzip() is None
        print(f"{revision}: {len(entries)} exact files, {commit}")


if __name__ == "__main__":
    main()
