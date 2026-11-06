"""Check the built wheel imports without relying on the source checkout."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main():
    wheel = max(
        (ROOT / "dist").glob("foldbench-*.whl"),
        key=lambda path: path.stat().st_mtime,
    )
    with ZipFile(wheel) as archive:
        names = archive.namelist()
        if "foldbench/api.py" not in names:
            raise RuntimeError("Wheel is missing the application package")
        if any(name.startswith(("src/", "tests/")) for name in names):
            raise RuntimeError("Wheel includes an unintended source directory")
    code = (
        "import foldbench; "
        f"assert foldbench.__file__.startswith({str(wheel)!r}); "
        "from foldbench.api import create_app; "
        "from foldbench.settings import Settings; "
        "assert '/v1/runs' in create_app(Settings()).openapi()['paths']; "
        "print('Wheel import and API schema verified outside the checkout')"
    )
    with tempfile.TemporaryDirectory(prefix="foldbench-wheel-") as directory:
        subprocess.run(
            [sys.executable, "-c", code],
            cwd=directory,
            env={**os.environ, "PYTHONPATH": str(wheel)},
            check=True,
        )


if __name__ == "__main__":
    main()
