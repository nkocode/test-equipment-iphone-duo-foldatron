"""Bundle the tracked project, including the manual, without local data."""

import subprocess
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "artifacts/FoldBench-complete-package.zip"
    output.parent.mkdir(exist_ok=True)
    paths = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
        .decode()
        .split("\0")
    )
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for relative in sorted(path for path in paths if path):
            archive.write(ROOT / relative, "FoldBench/" + relative)
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise RuntimeError("Archive verification failed")
        print(f"Verified {len(archive.namelist())} files: {output}")


if __name__ == "__main__":
    main()
