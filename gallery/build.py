"""Build the static revision gallery without changing historical viewers."""

import argparse
import html
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/nkocode/test-equipment-iphone-duo-foldatron"


def esc(value):
    return html.escape(str(value), quote=True)


def page(title, body, prefix=""):
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)} · foldatron</title>"
        '<meta name="description" content="Explore the evolution of the '
        'foldatron test bench, with preserved engineering revisions.">'
        f'<link rel="stylesheet" href="{prefix}style.css"></head><body>'
        f'<header><a class="brand" href="{prefix}index.html">foldatron'
        "<small>DESIGN EVOLUTION</small></a>"
        f'<a class="repo" href="{REPO}">Repository ↗</a></header>'
        f"{body}<footer><span>Engineering history · physical validation "
        'remains revision-specific.</span><a href="'
        f'{REPO}/tree/main/revisions">All revision materials ↗</a>'
        "</footer></body></html>"
    )


def build(output):
    revisions = json.loads((ROOT / "gallery/revisions.json").read_text())
    output.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "gallery/style.css", output / "style.css")
    sections = []
    for number, revision in enumerate(revisions, 1):
        rid, name = revision["id"], revision["name"]
        folder = output / rid
        folder.mkdir(exist_ok=True)
        commit = revision["commit"]
        archive = (
            f"{REPO}/archive/{commit}.zip"
            if commit
            else f"{REPO}/tree/main/revisions/{rid}"
        )
        material = f"{REPO}/tree/main/revisions/{rid}"
        if revision["image"]:
            shutil.copy2(ROOT / revision["image"], folder / "preview.jpg")
            visual = (
                f'<a href="{rid}/"><img src="{rid}/preview.jpg" '
                f'alt="{name} bench visualization" loading="lazy"></a>'
            )
        else:
            visual = '<div class="placeholder">Catalog-only architecture</div>'
        sections.append(
            f'<section class="revision" id="{rid}"><div class="number">'
            f'{number:02}</div><div><div class="eyebrow">{name} / '
            f"{esc(revision['status'])}</div><h2>"
            f"{esc(revision['title'])}</h2><p>"
            f'{esc(revision["description"])}</p><p class="detail">'
            f'{esc(revision["detail"])}</p><div class="links">'
            f'<a href="{rid}/">Explore {name} →</a>'
            f'<a href="{material}">Revision files ↗</a></div></div>'
            f"{visual}</section>"
        )
        document_links = []
        for label, path in revision["documents"]:
            local_file = ROOT / path
            # Large STEP files exceed the static host's per-file limit.
            if (revision.get("local_downloads")
                    and local_file.stat().st_size < 24 * 1024 * 1024):
                target = folder / "files" / Path(path).name
                target.parent.mkdir(exist_ok=True)
                shutil.copy2(ROOT / path, target)
                document_links.append(
                    f'<a href="files/{esc(target.name)}" download>'
                    f"{esc(label)} ↓</a>"
                )
            else:
                document_links.append(
                    f'<a href="{REPO}/blob/{commit or "main"}/{path}">'
                    f"{esc(label)} ↗</a>"
                )
        docs = "".join(document_links)
        if revision["viewer"]:
            shutil.copy2(ROOT / revision["viewer"], folder / "viewer.html")
            display = (
                f'<iframe class="frame" src="viewer.html" '
                f'title="{name} interactive bench visualization" '
                'allow="fullscreen"></iframe>'
            )
            controls = (
                '<a href="viewer.html" target="_blank">'
                "Full-screen viewer ↗</a>"
                '<a href="viewer.html" download>Download offline viewer ↓</a>'
            )
        else:
            display = '<section class="resources"><h2>Development review</h2>'
            if revision["image"]:
                display += (
                    '<img class="review-preview" src="preview.jpg" '
                    'alt="Rev C drawing review using original vendor CAD">'
                )
            display += (
                "<p>Full natural closure is required. The current package "
                "contains structure and interface drawings, a working parts "
                "register and a phone-measurement traveler. The contact "
                "fixture, complete assembly instructions, wiring and Rev C "
                "hardware drivers are still in development.</p></section>"
            )
            controls = ""
        download_label = (
            revision.get("archive_label", "Complete source snapshot ↓")
            if commit
            else "Revision folder ↗"
        )
        body = (
            '<div class="viewer-bar"><div><h1>'
            f"{name} · {esc(revision['title'])}</h1><p>"
            f"{esc(revision['status'])}"
            f"{' · source ' + commit[:7] if commit else ''}</p></div>"
            f'<div class="links">{controls}</div></div>{display}'
            '<section class="resources"><h2>Engineering materials</h2>'
            f'<p>{esc(revision["description"])}</p><div class="links">'
            f'{docs}<a href="{archive}">'
            f"{download_label}"
            f'</a><a href="{material}">Browse revision files ↗</a></div>'
            "<p>Historical viewers are preserved unchanged. Their original "
            "labels, assumptions and release holds still apply. Current "
            "revision-specific documents take precedence over earlier designs."
            "</p></section>"
        )
        (folder / "index.html").write_text(page(name, body, "../"))
    hero = (
        '<section class="hero"><div class="hero-copy"><div class="eyebrow">'
        "A test bench, through its revisions</div><h1>foldatron"
        "<span>Design. Build.<br>Reconsider.</span></h1><p>"
        "Follow the folding-phone tester from its first concept to a "
        "drawing-defined bench and a catalog-only redesign.</p>"
        '<a class="action" href="#revisions">Explore the revisions <span>↓'
        '</span></a></div><img src="rev-b/preview.jpg" '
        'alt="Rev B CAD mechanism with floating cradle and bearing supports">'
        '</section><section class="overview" id="revisions">'
        "<h2>Keep the evidence.<br>Show the evolution.</h2><p>"
        "Each revision has its own interactive page and materials. "
        "Rev A and Rev B are frozen snapshots; future work does not overwrite "
        "the earlier designs.</p></section>"
    )
    comparison = (
        '<section class="comparison"><h2>What changed</h2>'
        '<div class="table-wrap"><table><thead><tr><th>Design choice</th>'
        "<th>Rev A</th><th>Rev B</th><th>Rev C brief</th></tr></thead><tbody>"
        "<tr><td>Mechanical basis</td><td>Concept envelopes</td>"
        "<td>1010 and custom drawing CAD</td><td>Catalog assemblies</td></tr>"
        "<tr><td>Custom machining</td><td>Proposed</td><td>Required</td>"
        "<td>Not permitted</td></tr><tr><td>Controller interface</td>"
        "<td>Prototype wiring</td><td>Documented custom interface board</td>"
        "<td>Purchased I/O modules</td></tr><tr><td>Evidence</td>"
        "<td>Design and illustrated manual</td>"
        "<td>Drawings, STEP, traveler</td>"
        "<td>Supplier interfaces and assembly drawings</td></tr>"
        "</tbody></table></div></section>"
    )
    (output / "index.html").write_text(
        page("Design evolution", hero + "".join(sections) + comparison)
    )
    print(f"Built {len(revisions)} revision pages in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output.resolve())
