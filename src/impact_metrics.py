"""Standard-adoption and compliance-pattern analysis.

Computes, per ASU: comment-period length, issuance-to-effective lag,
early/on-time/late adopter counts, restatement rate, and average audit fee.
Results are written to standard_impact_metrics for downstream consumption
(R analysis, VBA export, dashboards).
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone


def compute_metrics_for_standard(conn: sqlite3.Connection, asu_number: str) -> dict:
    standard = conn.execute(
        "SELECT * FROM asu_standards WHERE asu_number = ?", (asu_number,)
    ).fetchone()
    if standard is None:
        raise KeyError(f"unknown asu_number: {asu_number}")

    issued = date.fromisoformat(standard["issued_date"])
    effective = date.fromisoformat(standard["effective_date_public"])
    comment_deadline = (
        date.fromisoformat(standard["comment_deadline"]) if standard["comment_deadline"] else None
    )

    # comment_deadline (exposure-draft comment window close) precedes issuance;
    # this is the re-deliberation lag between comments closing and final issuance.
    deliberation_lag_days = (issued - comment_deadline).days if comment_deadline else None
    issuance_to_effective_days = (effective - issued).days

    adoptions = conn.execute(
        "SELECT adoption_date, restatement_filed, audit_fee_usd FROM firm_adoptions WHERE asu_number = ?",
        (asu_number,),
    ).fetchall()

    n_firms = len(adoptions)
    n_early = n_on_time = n_late = n_restated = 0
    fee_total = 0
    fee_count = 0

    for row in adoptions:
        adoption_date = date.fromisoformat(row["adoption_date"])
        delta_days = (adoption_date - effective).days
        if delta_days < 0:
            n_early += 1
        elif delta_days <= 90:
            n_on_time += 1
        else:
            n_late += 1

        if row["restatement_filed"]:
            n_restated += 1

        if row["audit_fee_usd"] is not None:
            fee_total += row["audit_fee_usd"]
            fee_count += 1

    restatement_rate = n_restated / n_firms if n_firms else None
    avg_audit_fee = fee_total / fee_count if fee_count else None

    return {
        "asu_number": asu_number,
        "deliberation_lag_days": deliberation_lag_days,
        "issuance_to_effective_days": issuance_to_effective_days,
        "n_firms_tracked": n_firms,
        "n_early_adopters": n_early,
        "n_on_time_adopters": n_on_time,
        "n_late_adopters": n_late,
        "restatement_rate": restatement_rate,
        "avg_audit_fee_usd": avg_audit_fee,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def compute_all_metrics(conn: sqlite3.Connection) -> list[dict]:
    asu_numbers = [r["asu_number"] for r in conn.execute("SELECT asu_number FROM asu_standards")]
    return [compute_metrics_for_standard(conn, asu) for asu in asu_numbers]


def persist_metrics(conn: sqlite3.Connection, metrics: list[dict]) -> int:
    conn.executemany(
        """
        INSERT INTO standard_impact_metrics
            (asu_number, deliberation_lag_days, issuance_to_effective_days, n_firms_tracked,
             n_early_adopters, n_on_time_adopters, n_late_adopters, restatement_rate,
             avg_audit_fee_usd, computed_at)
        VALUES (:asu_number, :deliberation_lag_days, :issuance_to_effective_days, :n_firms_tracked,
                :n_early_adopters, :n_on_time_adopters, :n_late_adopters, :restatement_rate,
                :avg_audit_fee_usd, :computed_at)
        ON CONFLICT(asu_number) DO UPDATE SET
            deliberation_lag_days=excluded.deliberation_lag_days,
            issuance_to_effective_days=excluded.issuance_to_effective_days,
            n_firms_tracked=excluded.n_firms_tracked,
            n_early_adopters=excluded.n_early_adopters,
            n_on_time_adopters=excluded.n_on_time_adopters,
            n_late_adopters=excluded.n_late_adopters,
            restatement_rate=excluded.restatement_rate,
            avg_audit_fee_usd=excluded.avg_audit_fee_usd,
            computed_at=excluded.computed_at
        """,
        metrics,
    )
    return len(metrics)
