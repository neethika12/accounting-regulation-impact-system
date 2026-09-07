from pathlib import Path

from src import db, export, ingest
from src.pipeline import run_pipeline

LATENCY_BUDGET_SECONDS = 2.0  # generous ceiling for CI machines; local runs are far faster


def test_pipeline_end_to_end(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    test_db = tmp_path / "pipeline_test.db"

    result = run_pipeline(db_path=test_db, n_firms=15, seed=1, fresh=True)

    records = ingest.load_asu_csv()
    assert result.n_standards == len(records)
    assert result.n_firm_adoptions == len(records) * 15
    assert result.n_metrics == len(records)
    assert result.export_counts["asu_standards"] == len(records)

    with db.get_connection(test_db) as conn:
        count = conn.execute("SELECT COUNT(*) FROM standard_impact_metrics").fetchone()[0]
        assert count == len(records)


def test_pipeline_is_idempotent_with_fresh_flag(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    test_db = tmp_path / "pipeline_test2.db"

    result_a = run_pipeline(db_path=test_db, n_firms=5, seed=99, fresh=True)
    result_b = run_pipeline(db_path=test_db, n_firms=5, seed=99, fresh=True)
    assert result_a.n_standards == result_b.n_standards
    assert result_a.n_firm_adoptions == result_b.n_firm_adoptions


def test_pipeline_latency_under_budget(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(Path(__file__).resolve().parent.parent)
    test_db = tmp_path / "pipeline_latency.db"

    result = run_pipeline(db_path=test_db, n_firms=40, seed=42, fresh=True)
    assert result.total_seconds < LATENCY_BUDGET_SECONDS, (
        f"pipeline took {result.total_seconds:.3f}s, over the {LATENCY_BUDGET_SECONDS}s budget"
    )
