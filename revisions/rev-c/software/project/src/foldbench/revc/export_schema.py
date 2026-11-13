"""Export both deployment schemas without opening serial ports."""

import json
from pathlib import Path

from .api import create_app
from .models import Settings, write_example

ROOT = Path("revisions/rev-c/software")


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    for mode in ("simulation", "hardware"):
        schema = create_app(Settings(mode=mode)).openapi()
        (ROOT / f"openapi-{mode}.json").write_text(
            json.dumps(schema, indent=2) + "\n"
        )
    write_example(ROOT / "commissioning.example.json")


if __name__ == "__main__":
    main()
