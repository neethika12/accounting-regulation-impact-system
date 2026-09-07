"""Benchmark the pipeline's end-to-end latency over repeated runs.

Run: python -m benchmarks.latency_benchmark
Writes p50/p95/p99 stage-level and total latency to benchmarks/results.json.
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

from src.pipeline import run_pipeline

ROOT = Path(__file__).resolve().parent.parent
RESULTS_PATH = ROOT / "benchmarks" / "results.json"


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    values = sorted(values)
    k = (len(values) - 1) * pct
    f, c = int(k), min(int(k) + 1, len(values) - 1)
    if f == c:
        return values[f]
    return values[f] + (values[c] - values[f]) * (k - f)


def run_benchmark(iterations: int = 20) -> dict:
    totals = []
    per_stage: dict[str, list[float]] = {}

    for i in range(iterations):
        result = run_pipeline(fresh=True)
        totals.append(result.total_seconds)
        for stage in result.stage_timings:
            per_stage.setdefault(stage.name, []).append(stage.seconds)

    summary = {
        "iterations": iterations,
        "total_seconds": {
            "p50": percentile(totals, 0.50),
            "p95": percentile(totals, 0.95),
            "p99": percentile(totals, 0.99),
            "mean": statistics.mean(totals),
        },
        "stages": {
            name: {
                "p50": percentile(vals, 0.50),
                "p95": percentile(vals, 0.95),
                "mean": statistics.mean(vals),
            }
            for name, vals in per_stage.items()
        },
    }
    RESULTS_PATH.write_text(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    summary = run_benchmark()
    print(json.dumps(summary, indent=2))
