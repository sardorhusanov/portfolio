"""Vercel entrypoint for the existing API and server-rendered page metadata."""

import sys
from pathlib import Path

# Keep the backend's existing absolute imports and local uvicorn workflow intact.
sys.path.insert(0, str(Path(__file__).resolve().parent / "backend"))

from app.main import app as app  # noqa: E402
