import sqlite3
from pathlib import Path

import pytest

from src import impact_metrics


@pytest.fixture
def conn(tmp_path: Path):
    db_path = tmp_path / "test.db"
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(Path("db/schema.sql").read_text())

    connection.execute(
        """
        INSERT INTO asu_standards
            (asu_number, topic_code, title, issued_date, comment_deadline,
             effective_date_public, effective_date_other, early_adoption_permitted)
        VALUES ('2099-01', '999', 'Test Standard', '2020-03-01', '2020-01-01',
                '2020-07-01', '2021-01-01', 1)
        """
    )

    # 2 early (before effective), 1 on-time (within 90d), 1 late (>90d), one with a restatement.
    rows = [
        ("F1", "Tech", "2099-01", "2020-06-01", 0, 1_000_000),   # early
        ("F2", "Tech", "2099-01", "2020-06-15", 0, 1_100_000),   # early
        ("F3", "Tech", "2099-01", "2020-08-01", 0, 1_200_000),   # on-time (+31d)
        ("F4", "Tech", "2099-01", "2021-01-01", 1, 1_300_000),   # late (+184d), restated
    ]
    connection.executemany(
        "INSERT INTO firm_adoptions (firm_id, sector, asu_number, adoption_date, restatement_filed, audit_fee_usd) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    connection.commit()
    yield connection
    connection.close()


def test_compute_metrics_for_standard_known_answer(conn):
    metrics = impact_metrics.compute_metrics_for_standard(conn, "2099-01")
    assert metrics["deliberation_lag_days"] == 60  # comment close 2020-01-01 -> issued 2020-03-01
    assert metrics["issuance_to_effective_days"] == 122  # issued 2020-03-01 -> effective 2020-07-01
    assert metrics["n_firms_tracked"] == 4
    assert metrics["n_early_adopters"] == 2
    assert metrics["n_on_time_adopters"] == 1
    assert metrics["n_late_adopters"] == 1
    assert metrics["restatement_rate"] == pytest.approx(0.25)
    assert metrics["avg_audit_fee_usd"] == pytest.approx(1_150_000)


def test_compute_metrics_unknown_standard_raises(conn):
    with pytest.raises(KeyError):
        impact_metrics.compute_metrics_for_standard(conn, "9999-99")


def test_compute_metrics_no_adoptions_handles_empty_gracefully(conn):
    conn.execute(
        """
        INSERT INTO asu_standards
            (asu_number, topic_code, title, issued_date, effective_date_public, early_adoption_permitted)
        VALUES ('2099-02', '998', 'Untracked Standard', '2020-01-01', '2020-07-01', 0)
        """
    )
    conn.commit()
    metrics = impact_metrics.compute_metrics_for_standard(conn, "2099-02")
    assert metrics["n_firms_tracked"] == 0
    assert metrics["restatement_rate"] is None
    assert metrics["avg_audit_fee_usd"] is None
    assert metrics["deliberation_lag_days"] is None


def test_persist_metrics_upserts(conn):
    metrics = impact_metrics.compute_all_metrics(conn)
    n1 = impact_metrics.persist_metrics(conn, metrics)
    conn.commit()
    assert n1 == len(metrics)

    n2 = impact_metrics.persist_metrics(conn, metrics)
    conn.commit()
    assert n2 == len(metrics)

    count = conn.execute("SELECT COUNT(*) FROM standard_impact_metrics").fetchone()[0]
    assert count == len(metrics)
