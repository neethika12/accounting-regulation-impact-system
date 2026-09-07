"""Generate static JSON snapshots of the API's data for the Vercel-deployed
build of the dashboard, which has no live backend to talk to.

Run after `python -m src.pipeline`. Regenerate and re-commit whenever the
seed data (data/seed_asu_standards.csv) or metrics logic changes:

    python -m src.pipeline
    python scripts/export_static_data.py

The frontend automatically uses these files instead of the live API in
production builds (import.meta.env.PROD) -- see frontend/src/lib/api.js.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import db  # noqa: E402

OUT_DIR = ROOT / "frontend" / "public" / "data"


def _rows(conn, query, params=()):
    return [dict(r) for r in conn.execute(query, params).fetchall()]


def main() -> None:
    if not db.DB_PATH.exists():
        raise SystemExit("db/regulation_impact.db not found -- run `python -m src.pipeline` first")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with db.get_connection() as conn:
        summary_row = conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM asu_standards) AS n_standards,
                (SELECT COUNT(DISTINCT firm_id) FROM firm_adoptions) AS n_firms,
                (SELECT COUNT(*) FROM firm_adoptions) AS n_adoptions,
                (SELECT AVG(restatement_rate) FROM standard_impact_metrics) AS avg_restatement_rate,
                (SELECT AVG(deliberation_lag_days) FROM standard_impact_metrics) AS avg_deliberation_lag_days
            """
        ).fetchone()
        summary = dict(summary_row)

        standards = _rows(conn, "SELECT * FROM asu_standards ORDER BY issued_date")

        metrics = _rows(
            conn,
            """
            SELECT m.*, s.title, s.topic_code, s.issued_date, s.effective_date_public
            FROM standard_impact_metrics m
            JOIN asu_standards s ON s.asu_number = m.asu_number
            ORDER BY s.issued_date
            """,
        )

    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    (OUT_DIR / "standards.json").write_text(json.dumps(standards, indent=2))
    (OUT_DIR / "metrics.json").write_text(json.dumps(metrics, indent=2))

    print(f"Wrote {OUT_DIR}/summary.json, standards.json, metrics.json")


if __name__ == "__main__":
    main()
