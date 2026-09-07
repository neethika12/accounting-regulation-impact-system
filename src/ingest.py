"""Ingestion stage: load real FASB ASU standards and validate them.

Also generates a structurally-realistic synthetic firm-adoption panel used to
demonstrate the impact-measurement methodology (see docs/DATA_SOURCES.md for
why firm-level adoption data is simulated rather than sourced live).
"""
from __future__ import annotations

import csv
import random
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASU_CSV = ROOT / "data" / "seed_asu_standards.csv"

SECTORS = ["Technology", "Manufacturing", "Retail", "Financial Services", "Healthcare", "Energy"]


class ValidationError(ValueError):
    pass


@dataclass(frozen=True)
class AsuRecord:
    asu_number: str
    topic_code: str
    title: str
    issued_date: date
    comment_deadline: date | None
    effective_date_public: date
    effective_date_other: date | None
    early_adoption_permitted: bool


def _parse_date(value: str) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)


def load_asu_csv(path: Path = ASU_CSV) -> list[AsuRecord]:
    records: list[AsuRecord] = []
    seen: set[str] = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            asu_number = row["asu_number"].strip()
            if not asu_number:
                raise ValidationError("empty asu_number in seed data")
            if asu_number in seen:
                raise ValidationError(f"duplicate asu_number: {asu_number}")
            seen.add(asu_number)

            issued = _parse_date(row["issued_date"])
            effective_public = _parse_date(row["effective_date_public"])
            if issued is None or effective_public is None:
                raise ValidationError(f"{asu_number}: issued_date and effective_date_public are required")
            if effective_public < issued:
                raise ValidationError(f"{asu_number}: effective date precedes issuance date")

            comment_deadline = _parse_date(row["comment_deadline"])
            if comment_deadline is not None and comment_deadline > issued:
                raise ValidationError(
                    f"{asu_number}: comment_deadline must close before issuance "
                    "(the exposure-draft comment period precedes finalization)"
                )

            records.append(
                AsuRecord(
                    asu_number=asu_number,
                    topic_code=row["topic_code"].strip(),
                    title=row["title"].strip(),
                    issued_date=issued,
                    comment_deadline=comment_deadline,
                    effective_date_public=effective_public,
                    effective_date_other=_parse_date(row["effective_date_other"]),
                    early_adoption_permitted=row["early_adoption_permitted"].strip().upper() == "TRUE",
                )
            )
    if not records:
        raise ValidationError("no ASU records found in seed data")
    return records


def load_standards(conn: sqlite3.Connection, records: list[AsuRecord]) -> int:
    conn.executemany(
        """
        INSERT INTO asu_standards
            (asu_number, topic_code, title, issued_date, comment_deadline,
             effective_date_public, effective_date_other, early_adoption_permitted)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(asu_number) DO UPDATE SET
            topic_code=excluded.topic_code,
            title=excluded.title,
            issued_date=excluded.issued_date,
            comment_deadline=excluded.comment_deadline,
            effective_date_public=excluded.effective_date_public,
            effective_date_other=excluded.effective_date_other,
            early_adoption_permitted=excluded.early_adoption_permitted
        """,
        [
            (
                r.asu_number, r.topic_code, r.title, r.issued_date.isoformat(),
                r.comment_deadline.isoformat() if r.comment_deadline else None,
                r.effective_date_public.isoformat(),
                r.effective_date_other.isoformat() if r.effective_date_other else None,
                int(r.early_adoption_permitted),
            )
            for r in records
        ],
    )
    return len(records)


def generate_firm_panel(
    records: list[AsuRecord],
    n_firms: int = 40,
    seed: int = 42,
) -> list[tuple]:
    """Generate a synthetic (firm, standard) adoption panel.

    Adoption timing is modeled around each standard's public effective date:
    ~20% early adopters (before effective date, only if permitted), ~65%
    on-time (within 90 days after), ~15% late (up to a year late) — a
    realistic-shaped distribution for demonstrating adoption-lag analysis.
    """
    rng = random.Random(seed)
    firms = [(f"FIRM{idx:04d}", rng.choice(SECTORS)) for idx in range(n_firms)]

    rows = []
    for record in records:
        for firm_id, sector in firms:
            roll = rng.random()
            if record.early_adoption_permitted and roll < 0.20:
                offset_days = -rng.randint(30, 270)
            elif roll < 0.85:
                offset_days = rng.randint(0, 90)
            else:
                offset_days = rng.randint(91, 365)

            adoption_date = record.effective_date_public + timedelta(days=offset_days)

            # Late/rushed adopters have a higher illustrative restatement rate.
            restatement_prob = 0.03 if offset_days <= 90 else 0.12
            restatement = 1 if rng.random() < restatement_prob else 0

            base_fee = {
                "Technology": 1_800_000, "Manufacturing": 2_400_000, "Retail": 1_500_000,
                "Financial Services": 3_200_000, "Healthcare": 2_100_000, "Energy": 2_700_000,
            }[sector]
            audit_fee = int(base_fee * rng.uniform(0.85, 1.25))

            rows.append((firm_id, sector, record.asu_number, adoption_date.isoformat(), restatement, audit_fee))
    return rows


def load_firm_panel(conn: sqlite3.Connection, rows: list[tuple]) -> int:
    conn.executemany(
        """
        INSERT INTO firm_adoptions (firm_id, sector, asu_number, adoption_date, restatement_filed, audit_fee_usd)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(firm_id, asu_number) DO UPDATE SET
            sector=excluded.sector,
            adoption_date=excluded.adoption_date,
            restatement_filed=excluded.restatement_filed,
            audit_fee_usd=excluded.audit_fee_usd
        """,
        rows,
    )
    return len(rows)
