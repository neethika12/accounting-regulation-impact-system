# Architecture

```
data/seed_asu_standards.csv (real FASB ASUs)
        |
        v
  src/ingest.py  --load_asu_csv (validate)--> AsuRecord list
        |                                          |
        |                                          v
        |                              generate_firm_panel (synthetic,
        |                               structurally realistic, seeded)
        v                                          |
  db/schema.sql --init_db-->  regulation_impact.db (SQLite)
        ^                                          |
        |___________________load_standards_________|_____load_firm_panel___
                                                    |
                                                    v
                                    src/impact_metrics.py
                              (deliberation lag, adoption timing,
                               restatement rate, avg audit fee)
                                                    |
                                                    v
                                standard_impact_metrics table
                                                    |
                                                    v
                                        src/export.py --> exports/*.csv
                                                    |
                          ______________________________________
                         |                                      |
                         v                                      v
              r_analysis/impact_analysis.R          vba/ResearchPipelineIntegration.bas
        (OLS + logistic regression,                (imports CSVs into Excel,
         adoption-lag summary by topic)              builds Compliance_Summary sheet)
```

## Stages (all timed by `src/pipeline.py`)

1. **`load_asu_csv`** — parse and validate the real ASU seed data (duplicate
   ASU numbers, out-of-order dates rejected).
2. **`load_standards`** — upsert into `asu_standards`.
3. **`generate_firm_panel`** — build the synthetic firm-adoption panel
   (see [DATA_SOURCES.md](DATA_SOURCES.md)).
4. **`load_firm_panel`** — upsert into `firm_adoptions`.
5. **`compute_all_metrics`** / **`persist_metrics`** — derive and store
   per-standard compliance/adoption metrics.
6. **`export_all`** — flatten all three tables to CSV for R and Excel/VBA
   consumption, so neither downstream tool needs a SQLite driver.

Each stage is wrapped in `time.perf_counter()` timing
(`src/pipeline.py:_timed`); `benchmarks/latency_benchmark.py` runs the full
pipeline repeatedly and reports p50/p95/p99 latency per stage — see
[BENCHMARKS.md](BENCHMARKS.md) for measured numbers on this machine.

## Why SQLite, not Postgres

The whole ASU + firm-panel dataset here is small (hundreds to low thousands of
rows) and the target audience is a single researcher's laptop, not a
multi-user service — SQLite gives zero-setup, file-based persistence with the
same SQL surface `schema.sql` would need for a Postgres upgrade path (the
schema avoids SQLite-only syntax beyond `AUTOINCREMENT` and `PRAGMA`).

## Why CSV as the interchange format between Python, R, and Excel/VBA

R's `RSQLite` and a VBA ODBC/SQLite driver both require extra installed
components a research collaborator may not have. Flat CSV exports work
everywhere `read.csv()` or Excel's built-in text-import wizard already runs,
which is the point of the resume's "straightforward integration into existing
research pipelines" claim — no new driver or library to install downstream.
