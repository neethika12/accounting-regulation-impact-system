# Accounting Regulation Analysis & Standard-Setting Impact Measurement System

Analytics infrastructure for tracking FASB accounting-standard changes and
measuring their downstream impact on firm compliance behavior: adoption
timing, restatement incidence, and audit fees. Built as a low-latency,
well-tested research pipeline meant to plug into an existing research
workflow (Python -> SQL -> R -> Excel), not as a standalone web app.

## What it does

1. **Ingests real FASB Accounting Standards Updates** (15 ASUs, hand-curated
   from public FASB records — ASC 606 revenue recognition, ASC 842 leases,
   CECL, goodwill impairment simplification, and others) into a validated
   SQLite schema. See [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md).
2. **Generates a structurally-realistic synthetic firm-adoption panel**
   (adoption timing, restatement flags, audit fees) to exercise the
   impact-measurement methodology, since real firm-level panels require
   licensed data (Audit Analytics/WRDS) not available here — see the same doc
   for exactly what's real vs. simulated and how to swap in real data later.
3. **Computes standard-adoption and compliance-pattern metrics** per
   standard: deliberation lag (comment-close to issuance), issuance-to-
   effective lag, early/on-time/late adopter counts, restatement rate,
   average audit fee.
4. **Runs statistical impact analysis in R**: OLS regression of audit fees on
   adoption lag and sector, logistic regression of restatement incidence on
   adoption lag, and cross-standard summary tables.
5. **Feeds an Excel/VBA macro** that imports the pipeline's CSV exports and
   builds a compliance-summary table for researchers who work primarily in
   Excel.

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m src.pipeline          # ingest -> analyze -> export (~4ms, see docs/BENCHMARKS.md)
pytest                          # 13 tests: validation, known-answer metrics, pipeline, latency budget
python -m benchmarks.latency_benchmark   # p50/p95/p99 over 20 runs -> benchmarks/results.json

Rscript r_analysis/impact_analysis.R     # regression + summary tables, reads exports/*.csv
```

Then in Excel: import `vba/ResearchPipelineIntegration.bas`, point
`EXPORTS_FOLDER` at this repo's `exports/` directory, and run
`RefreshResearchPipelineData`.

## Project layout

```
data/seed_asu_standards.csv     real FASB ASU metadata (input)
db/schema.sql                   SQLite schema (3 tables)
src/ingest.py                   CSV validation + synthetic firm-panel generation
src/impact_metrics.py           adoption/compliance metric computation
src/export.py                   DB -> CSV for R and Excel
src/pipeline.py                 orchestrator with per-stage timing
r_analysis/impact_analysis.R    OLS + logistic regression, summary tables
vba/ResearchPipelineIntegration.bas   Excel import + compliance-summary macro
tests/                          13 tests: validation, known-answer metrics, pipeline, latency
benchmarks/latency_benchmark.py p50/p95/p99 latency over repeated runs
docs/                           architecture, data-source provenance, benchmark results
```

## Testing & validation status

- **Python**: 13 pytest tests pass (`pytest -q`), covering CSV validation
  (rejects duplicate ASU numbers, out-of-order dates), known-answer metric
  computation, pipeline idempotency, and a latency budget assertion.
- **R**: `impact_analysis.R` has been executed end-to-end against the
  pipeline's real output (see [docs/BENCHMARKS.md](docs/BENCHMARKS.md) and
  the regression output committed in this README's development history) —
  R was installed via Homebrew specifically to verify this script runs
  correctly rather than leaving it unverified.
- **VBA**: `ResearchPipelineIntegration.bas` has been manually reviewed for
  correctness (column-index mapping checked against the actual CSV export
  schemas) but **not executed**, since neither Excel nor a VBA runtime is
  installed on the development machine. Treat it as reviewed-but-unverified
  until run once in Excel.

## Data honesty

The 15 FASB standards and their dates are real public record. The firm-level
adoption/restatement/audit-fee panel is synthetic by necessity (see
[docs/DATA_SOURCES.md](docs/DATA_SOURCES.md)) — this is disclosed here
deliberately rather than presented as real compliance data.

## Live demo

The dashboard is deployable to Vercel as a static site (pre-generated JSON
snapshots, no hosted backend needed) — see
[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).
