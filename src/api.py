"""REST API serving the regulation-impact pipeline's data to the React dashboard.

Run: uvicorn src.api:app --reload --port 8000
Requires the pipeline to have been run at least once (python -m src.pipeline)
so db/regulation_impact.db exists.
"""
from __future__ import annotations

import sqlite3
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from . import db, impact_metrics, ingest
from .pipeline import run_pipeline

app = FastAPI(title="Accounting Regulation Impact API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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


@app.post("/api/upload")
async def upload_standards(file: UploadFile = File(...)) -> dict:
    """Validate and analyze a user-supplied CSV of ASU standards.

    Runs the uploaded file through the exact same code the real pipeline
    uses (src.ingest.load_asu_csv, generate_firm_panel, impact_metrics) --
    a bad file is rejected with the real ValidationError message, not a
    reimplemented check. Nothing is persisted: everything runs against a
    throwaway SQLite database in a temp directory for this request only.
    """
    content = await file.read()

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".csv", delete=False) as tmp_csv:
        tmp_csv.write(content)
        csv_path = Path(tmp_csv.name)

    try:
        records = ingest.load_asu_csv(csv_path)
    except ingest.ValidationError as e:
        return {"valid": False, "error": str(e)}
    except (KeyError, UnicodeDecodeError) as e:
        return {"valid": False, "error": f"Could not parse CSV: {e}"}
    finally:
        csv_path.unlink(missing_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_db_path = Path(tmp_dir) / "upload_test.db"
        db.init_db(tmp_db_path)
        with db.get_connection(tmp_db_path) as conn:
            ingest.load_standards(conn, records)
            panel = ingest.generate_firm_panel(records, n_firms=40, seed=42)
            ingest.load_firm_panel(conn, panel)
            metrics = impact_metrics.compute_all_metrics(conn)

    standards_by_number = {r.asu_number: r for r in records}
    enriched_metrics = [
        {
            **m,
            "title": standards_by_number[m["asu_number"]].title,
            "topic_code": standards_by_number[m["asu_number"]].topic_code,
            "issued_date": standards_by_number[m["asu_number"]].issued_date.isoformat(),
            "effective_date_public": standards_by_number[m["asu_number"]].effective_date_public.isoformat(),
        }
        for m in metrics
    ]

    return {"valid": True, "n_standards": len(records), "metrics": enriched_metrics}


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
