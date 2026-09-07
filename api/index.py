"""Vercel Python serverless function entrypoint.

Vercel auto-detects any file under /api exporting a FastAPI `app` instance
and deploys it as a serverless function. This just re-exports the real
backend app (src/api.py) so the same code path serves both local dev
(uvicorn) and the live Vercel deployment.

Only /api/upload is expected to work meaningfully here -- /api/summary,
/api/standards, and /api/metrics require db/regulation_impact.db, which
isn't part of this deployment (the dashboard uses static JSON snapshots
in production instead, see docs/DEPLOYMENT.md). Those routes will return
a 503 here, which is fine since the deployed frontend never calls them.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.api import app  # noqa: E402,F401
