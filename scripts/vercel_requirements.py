"""Export Vercel's root requirements from the backend's canonical lockfile."""

import argparse
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER = (
    "# Generated from backend/uv.lock; do not edit manually.\n"
    "# Refresh with: python scripts/vercel_requirements.py\n"
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the export is stale")
    args = parser.parse_args()
    exported = subprocess.run(
        [
            "uv",
            "export",
            "--project",
            str(ROOT / "backend"),
            "--locked",
            "--no-dev",
            "--no-emit-project",
            "--no-hashes",
            "--no-annotate",
            "--no-header",
        ],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    expected = HEADER + exported
    destination = ROOT / "requirements.txt"
    if args.check:
        if not destination.exists() or destination.read_text() != expected:
            raise SystemExit(
                "requirements.txt is stale. Run python scripts/vercel_requirements.py."
            )
        print("Vercel requirements match backend/uv.lock.")
    else:
        destination.write_text(expected)
        print("Updated requirements.txt from backend/uv.lock.")


if __name__ == "__main__":
    main()
