"""Export stage: flatten DB tables to CSV for R analysis and the VBA macro."""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPORTS_DIR = ROOT / "exports"


def _export_query(conn: sqlite3.Connection, query: str, out_path: Path) -> int:
    rows = conn.execute(query).fetchall()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        if not rows:
            return 0
        writer = csv.writer(f)
        writer.writerow(rows[0].keys())
        writer.writerows(tuple(r) for r in rows)
    return len(rows)


def export_all(conn: sqlite3.Connection, out_dir: Path = EXPORTS_DIR) -> dict[str, int]:
    counts = {}
    counts["asu_standards"] = _export_query(conn, "SELECT * FROM asu_standards", out_dir / "asu_standards.csv")
    counts["firm_adoptions"] = _export_query(conn, "SELECT * FROM firm_adoptions", out_dir / "firm_adoptions.csv")
    counts["standard_impact_metrics"] = _export_query(
        conn, "SELECT * FROM standard_impact_metrics", out_dir / "standard_impact_metrics.csv"
    )
    return counts
