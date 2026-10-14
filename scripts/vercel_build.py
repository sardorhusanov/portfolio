"""Build React and stage CDN assets while keeping HTML rendering in FastAPI."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "frontend" / "dist"
PUBLIC = ROOT / "public"


def main() -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "vercel_requirements.py"), "--check"],
        cwd=ROOT,
        check=True,
    )
    subprocess.run(
        ["npm", "ci", "--include=dev", "--no-audit", "--no-fund"],
        cwd=ROOT / "frontend",
        check=True,
    )
    frontend_env = os.environ.copy()
    frontend_env.setdefault("VITE_MAX_IMAGE_UPLOAD_MB", "4")
    subprocess.run(
        ["npm", "run", "build"], cwd=ROOT / "frontend", env=frontend_env, check=True
    )
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
