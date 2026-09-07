"""REST API serving the regulation-impact pipeline's data to the React dashboard.

Run: uvicorn src.api:app --reload --port 8000
Requires the pipeline to have been run at least once (python -m src.pipeline)
so db/regulation_impact.db exists.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .pipeline import run_pipeline

app = FastAPI(title="Accounting Regulation Impact API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict]:
    return [dict(r) for r in rows]


def _require_db() -> None:
    if not db.DB_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Database not found. Run `python -m src.pipeline` first.",
        )


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "db_exists": db.DB_PATH.exists()}


@app.post("/api/pipeline/run")
def trigger_pipeline() -> dict:
    result = run_pipeline()
    return result.to_dict()


@app.get("/api/standards")
def list_standards() -> list[dict]:
    _require_db()
    with db.get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM asu_standards ORDER BY issued_date"
        ).fetchall()
    return _rows_to_dicts(rows)


@app.get("/api/metrics")
def list_metrics() -> list[dict]:
    _require_db()
    with db.get_connection() as conn:
        rows = conn.execute(
            """
            SELECT m.*, s.title, s.topic_code, s.issued_date, s.effective_date_public
            FROM standard_impact_metrics m
            JOIN asu_standards s ON s.asu_number = m.asu_number
            ORDER BY s.issued_date
            """
        ).fetchall()
    return _rows_to_dicts(rows)


@app.get("/api/firm-adoptions")
def list_firm_adoptions(asu_number: str | None = None) -> list[dict]:
    _require_db()
    with db.get_connection() as conn:
        if asu_number:
            rows = conn.execute(
                "SELECT * FROM firm_adoptions WHERE asu_number = ? ORDER BY adoption_date",
                (asu_number,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM firm_adoptions ORDER BY asu_number, adoption_date"
            ).fetchall()
    return _rows_to_dicts(rows)


@app.get("/api/summary")
def summary() -> dict:
    _require_db()
    with db.get_connection() as conn:
        n_standards = conn.execute("SELECT COUNT(*) AS c FROM asu_standards").fetchone()["c"]
        n_firms = conn.execute(
            "SELECT COUNT(DISTINCT firm_id) AS c FROM firm_adoptions"
        ).fetchone()["c"]
        n_adoptions = conn.execute("SELECT COUNT(*) AS c FROM firm_adoptions").fetchone()["c"]
        avg_restatement = conn.execute(
            "SELECT AVG(restatement_rate) AS v FROM standard_impact_metrics"
        ).fetchone()["v"]
        avg_deliberation = conn.execute(
            "SELECT AVG(deliberation_lag_days) AS v FROM standard_impact_metrics"
        ).fetchone()["v"]
    return {
        "n_standards": n_standards,
        "n_firms": n_firms,
        "n_adoptions": n_adoptions,
        "avg_restatement_rate": avg_restatement,
        "avg_deliberation_lag_days": avg_deliberation,
    }


@app.get("/api/benchmarks")
def benchmarks() -> dict:
    results_path = Path(__file__).resolve().parent.parent / "benchmarks" / "results.json"
    if not results_path.exists():
        raise HTTPException(
            status_code=404,
            detail="No benchmark results yet. Run `python -m benchmarks.latency_benchmark` first.",
        )
    import json

    return json.loads(results_path.read_text())
