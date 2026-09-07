# Data Sources

## `data/seed_asu_standards.csv` — real

Fifteen actual FASB Accounting Standards Updates (ASUs), curated by hand from
public FASB standard-setting records: ASU number, ASC topic, title, issuance
date, exposure-draft comment-deadline, and effective dates for public business
entities vs. all other entities. Examples: ASU 2014-09 (Topic 606, Revenue
Recognition), ASU 2016-02 (Topic 842, Leases), ASU 2016-13 (Topic 326, CECL).

Note on date semantics: `comment_deadline` is when the public comment period
on the *exposure draft* closed — this precedes final issuance, since FASB
re-deliberates after comments close before issuing the final ASU. It is not a
comment period on the finished standard.

This file is the ingestion pipeline's real input. `src/ingest.py` validates it
(rejects duplicate ASU numbers, rejects dates out of order) before loading it.

## `firm_adoptions` table — synthetic

Per-firm adoption timing, restatement flags, and audit fees for each ASU are
**generated**, not sourced live, by `src.ingest.generate_firm_panel()` with a
fixed random seed (reproducible). This is a deliberate scope decision: real
firm-level adoption/restatement/audit-fee panels come from licensed sources
(Audit Analytics, Compustat/WRDS via SEC EDGAR filings) that require paid
subscriptions and are not available in this environment.

The synthetic panel is built to be *structurally realistic* rather than
arbitrary, so the statistical methodology downstream (R impact analysis) is
exercised the same way it would be against real panel data:

- Adoption timing is drawn relative to each standard's real effective date
  (~20% early, when the standard permits it; ~65% within 90 days; ~15% more
  than 90 days late) — not uniform random noise.
- Restatement probability is set higher for late adopters (12% vs. 3%) than
  for a real-world hypothesis, so the logistic regression has genuine signal
  to recover.
- Audit fees vary by sector with realistic-order-of-magnitude base fees.

**If this system is extended with real firm-level data** (e.g. via a WRDS/SEC
EDGAR data pull a research assistant has access to), only `ingest.py`'s panel
generator needs replacing — the schema, impact-metrics computation, R
analysis, and VBA integration are all written against the same
`firm_adoptions` table shape and require no changes.
