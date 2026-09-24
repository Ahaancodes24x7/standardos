"""Vercel entry point for the StandardOS API (FastAPI, ASGI).

Vercel routes every request of this project here (see ../vercel.json); the app
and the engine are copied next to this file by backend/scripts/build_vercel_api.py.
"""

import os
import sys
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BUNDLE))
os.environ.setdefault("STANDARDOS_RESULTS_DIR", str(BUNDLE / "results"))

from app.main import app  # noqa: E402

__all__ = ["app"]
