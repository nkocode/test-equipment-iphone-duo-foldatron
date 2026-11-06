"""Download named public vendor references, rejecting HTML error pages."""

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "hardware/rev-b"


def main():
    folder = DATA / "vendor"
    folder.mkdir(exist_ok=True)
    sources = json.loads((DATA / "source-register.json").read_text())
    results = []
    for source in sources:
        name = source.get("filename")
        if not name:
            continue
        path = folder / name
        expected = source.get("sha256")
        if (
            path.is_file()
            and hashlib.sha256(path.read_bytes()).hexdigest() == expected
        ):
            print(f"Verified existing {name}")
            continue
        try:
            request = Request(
                source["url"],
                headers={
                    "User-Agent": "foldatron-engineering-reference-fetch/1.0"
                },
            )
            with urlopen(request, timeout=45) as response:
                content = response.read()
            prefix = (
                b"%PDF-"
                if name.endswith(".pdf")
                else b"PK"
                if name.endswith(".zip")
                else b"<?xml"
                if name.endswith(".brd")
                else b"ISO-10303-21;"
            )
            if not content.lstrip().startswith(prefix):
                raise ValueError("Not the expected file format")
            actual = hashlib.sha256(content).hexdigest()
            if expected and actual != expected:
                revised = path.with_name(path.stem + "-changed" + path.suffix)
                revised.write_bytes(content)
                raise ValueError(f"Vendor content changed; review {revised}")
            path.write_bytes(content)
            results.append({"file": name, "sha256": actual})
            print(f"Downloaded {name}")
        except Exception as exc:
            results.append({"file": name, "error": str(exc)})
            print(f"UNAVAILABLE {name}: {exc}")
    (folder / "fetch-result.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
