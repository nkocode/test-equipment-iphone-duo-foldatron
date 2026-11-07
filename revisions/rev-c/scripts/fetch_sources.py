"""Fetch pinned public manufacturer references without new dependencies.

Vendor files remain copyrighted by their manufacturers. Downloading them
does not make them project-authored or grant a redistribution license.
"""

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def validate(data, suffix):
    """Reject an HTML error page masquerading as a drawing or CAD file."""
    signatures = {".pdf": b"%PDF-", ".step": b"ISO-10303-21;"}
    signature = signatures.get(suffix.lower())
    if signature and not data.lstrip().startswith(signature):
        raise ValueError(f"Invalid {suffix} file signature")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    records = json.loads((ROOT / "hardware/sources.json").read_text())
    destination = ROOT / "hardware/vendor"
    destination.mkdir(parents=True, exist_ok=True)
    for record in records:
        path = destination / record["file"]
        if not path.exists():
            if args.verify_only:
                raise FileNotFoundError(path)
            request = Request(
                record["url"], headers={"User-Agent": "Mozilla/5.0"}
            )
            with urlopen(request, timeout=60) as response:
                data = response.read()
            validate(data, path.suffix)
            if hashlib.sha256(data).hexdigest() != record["sha256"]:
                raise ValueError(f"Vendor reference changed: {path.name}")
            path.write_bytes(data)
        data = path.read_bytes()
        validate(data, path.suffix)
        if hashlib.sha256(data).hexdigest() != record["sha256"]:
            raise ValueError(f"Checksum mismatch: {path.name}")
        print(f"Verified {path.name}: {len(data):,} bytes")


if __name__ == "__main__":
    main()
