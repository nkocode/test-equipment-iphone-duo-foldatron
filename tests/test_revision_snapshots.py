"""Historical source snapshots must remain unchanged."""

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("revision", ["rev-a", "rev-b"])
def test_snapshot_integrity(revision):
    folder = ROOT / "revisions" / revision
    manifest = json.loads((folder / "manifest.json").read_text())
    project = folder / "project"
    actual_files = {
        path.relative_to(project).as_posix()
        for path in project.rglob("*")
        if path.is_file()
    }
    assert actual_files == set(manifest["files"])
    for name, expected in manifest["files"].items():
        actual = hashlib.sha256((project / name).read_bytes()).hexdigest()
        assert actual == expected, f"Historical source changed: {name}"


def test_gallery_uses_frozen_viewers():
    revisions = json.loads((ROOT / "gallery/revisions.json").read_text())
    for revision in revisions:
        if revision["id"] not in {"rev-a", "rev-b"}:
            continue
        folder = ROOT / "revisions" / revision["id"]
        manifest = json.loads((folder / "manifest.json").read_text())
        assert revision["commit"] == manifest["commit"]
        assert (ROOT / revision["viewer"]).is_file()
        for _, document in revision["documents"]:
            assert document in manifest["files"]
