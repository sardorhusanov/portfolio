"""Build React and stage CDN assets while keeping HTML rendering in FastAPI."""

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "frontend" / "dist"
PUBLIC = ROOT / "public"


def main() -> None:
    # Vercel installs the committed requirements.txt before this command runs.
    # Validate its lockfile export locally; the build environment need not ship uv.
    if not (ROOT / "requirements.txt").is_file():
        raise SystemExit("Missing root requirements.txt for Vercel's Python runtime.")
    subprocess.run(
        ["npm", "ci", "--include=dev", "--no-audit", "--no-fund"],
        cwd=ROOT / "frontend",
        check=True,
    )
    frontend_env = os.environ.copy()
    frontend_env.setdefault("VITE_MAX_IMAGE_UPLOAD_MB", "4")
    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", env=frontend_env, check=True)
    if not (DIST / "index.html").is_file():
        raise SystemExit("The frontend build did not produce dist/index.html.")

    # This directory is generated and ignored by Git. Publishing index.html here
    # would bypass per-page metadata, real 404 statuses, and old-slug redirects.
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    shutil.copytree(DIST, PUBLIC, ignore=shutil.ignore_patterns("*.html"))
    print("Built frontend/dist for FastAPI and public/ assets for the Vercel CDN.")


if __name__ == "__main__":
    main()
