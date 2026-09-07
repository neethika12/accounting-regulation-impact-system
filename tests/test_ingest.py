import sqlite3
from pathlib import Path

import pytest

from src import ingest


def test_load_asu_csv_parses_all_rows():
    records = ingest.load_asu_csv()
    assert len(records) >= 10
    numbers = {r.asu_number for r in records}
    assert "2016-02" in numbers  # ASC 842 Leases
    assert "2014-09" in numbers  # ASC 606 Revenue Recognition


def test_load_asu_csv_rejects_duplicate(tmp_path: Path):
    bad_csv = tmp_path / "dupes.csv"
    bad_csv.write_text(
        "asu_number,topic_code,title,issued_date,comment_deadline,"
        "effective_date_public,effective_date_other,early_adoption_permitted\n"
        "2020-01,100,Dup,2020-01-01,,2020-06-01,,TRUE\n"
        "2020-01,100,Dup,2020-01-01,,2020-06-01,,TRUE\n"
    )
    with pytest.raises(ingest.ValidationError, match="duplicate"):
        ingest.load_asu_csv(bad_csv)


def test_load_asu_csv_rejects_effective_before_issued(tmp_path: Path):
    bad_csv = tmp_path / "bad_dates.csv"
    bad_csv.write_text(
        "asu_number,topic_code,title,issued_date,comment_deadline,"
        "effective_date_public,effective_date_other,early_adoption_permitted\n"
        "2020-01,100,Bad,2020-06-01,,2020-01-01,,TRUE\n"
    )
    with pytest.raises(ingest.ValidationError, match="precedes"):
        ingest.load_asu_csv(bad_csv)


def test_load_standards_upserts(tmp_path: Path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(Path("db/schema.sql").read_text())

    records = ingest.load_asu_csv()
    n_inserted = ingest.load_standards(conn, records)
    conn.commit()
    assert n_inserted == len(records)

    count = conn.execute("SELECT COUNT(*) FROM asu_standards").fetchone()[0]
    assert count == len(records)

    # Re-running should upsert, not duplicate.
    ingest.load_standards(conn, records)
    conn.commit()
    count_after = conn.execute("SELECT COUNT(*) FROM asu_standards").fetchone()[0]
    assert count_after == len(records)
    conn.close()


def test_generate_firm_panel_is_deterministic_for_fixed_seed():
    records = ingest.load_asu_csv()
    panel_a = ingest.generate_firm_panel(records, n_firms=10, seed=7)
    panel_b = ingest.generate_firm_panel(records, n_firms=10, seed=7)
    assert panel_a == panel_b
    assert len(panel_a) == 10 * len(records)


def test_generate_firm_panel_respects_early_adoption_flag():
    records = [r for r in ingest.load_asu_csv() if not r.early_adoption_permitted]
    if not records:
        pytest.skip("no non-early-adoption-permitted standards in seed data")
    panel = ingest.generate_firm_panel(records, n_firms=50, seed=1)
    from datetime import date
    effective_by_asu = {r.asu_number: r.effective_date_public for r in records}
    for firm_id, sector, asu_number, adoption_date, restated, fee in panel:
        assert date.fromisoformat(adoption_date) >= effective_by_asu[asu_number]
