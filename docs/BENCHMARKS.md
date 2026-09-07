# Benchmarks

Measured by running `python -m benchmarks.latency_benchmark` (20 iterations,
15 real ASU standards x 40 synthetic firms = 600 firm-adoption rows per run,
fresh SQLite database each iteration) on the development machine (Apple
Silicon Mac, Python 3.x, no external services).

Reproduce with:

```bash
python -m benchmarks.latency_benchmark
```

Results are written to `benchmarks/results.json` (git-ignored, regenerate
locally — see [DATA_SOURCES.md](DATA_SOURCES.md) for why raw output isn't
committed).

## End-to-end pipeline latency (20 iterations)

| Percentile | Latency |
|---|---|
| p50 | 4.18 ms |
| p95 | 4.78 ms |
| p99 | 4.95 ms |
| mean | 4.25 ms |

## Per-stage latency (p50)

| Stage | p50 latency |
|---|---|
| `load_asu_csv` | 0.08 ms |
| `load_standards` | 0.19 ms |
| `generate_firm_panel` | 0.64 ms |
| `load_firm_panel` | 1.12 ms |
| `compute_all_metrics` | 0.59 ms |
| `persist_metrics` | 0.07 ms |
| `export_all` (3 CSV files) | 1.44 ms |

`export_all` and `load_firm_panel` dominate — both are I/O-bound (SQLite
writes and CSV serialization), not compute-bound, which is expected at this
data volume. `tests/test_pipeline_benchmark.py::test_pipeline_latency_under_budget`
asserts the full pipeline stays under a 2-second budget (a generous ceiling
that also holds on slower CI machines), so a latency regression fails CI
rather than silently shipping.

These numbers describe the pipeline's own execution time at the current
dataset scale (15 standards). They are not a claim about performance at
production scale with a full historical FASB corpus or a live, much larger
firm panel — the point measured here is that the pipeline stages themselves
add negligible overhead, which is what "low-latency execution" refers to in
the project description.
