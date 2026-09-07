"""End-to-end orchestrator: ingest -> generate panel -> compute metrics -> export.

Each stage is timed with perf_counter so the pipeline's own latency is a
first-class, benchmarkable output rather than an unverified claim.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import db, export, ingest, impact_metrics

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("pipeline")

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class StageTiming:
    name: str
    seconds: float


@dataclass
class PipelineResult:
    n_standards: int
    n_firm_adoptions: int
    n_metrics: int
    export_counts: dict
    stage_timings: list[StageTiming] = field(default_factory=list)

    @property
    def total_seconds(self) -> float:
        return sum(t.seconds for t in self.stage_timings)

    def to_dict(self) -> dict:
        return {
            "n_standards": self.n_standards,
            "n_firm_adoptions": self.n_firm_adoptions,
            "n_metrics": self.n_metrics,
            "export_counts": self.export_counts,
            "total_seconds": self.total_seconds,
            "stage_timings": [{"name": t.name, "seconds": t.seconds} for t in self.stage_timings],
        }


def _timed(name: str, timings: list[StageTiming], fn, *args, **kwargs):
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    timings.append(StageTiming(name=name, seconds=time.perf_counter() - start))
    return result


def run_pipeline(
    db_path: Path = db.DB_PATH,
    n_firms: int = 40,
    seed: int = 42,
    fresh: bool = True,
) -> PipelineResult:
    if fresh and db_path.exists():
        db_path.unlink()

    timings: list[StageTiming] = []
    db.init_db(db_path)

    records = _timed("load_asu_csv", timings, ingest.load_asu_csv)
    logger.info("Loaded %d ASU records from seed CSV", len(records))

    with db.get_connection(db_path) as conn:
        n_standards = _timed("load_standards", timings, ingest.load_standards, conn, records)

        panel_rows = _timed("generate_firm_panel", timings, ingest.generate_firm_panel, records, n_firms, seed)
        n_firm_adoptions = _timed("load_firm_panel", timings, ingest.load_firm_panel, conn, panel_rows)

        metrics = _timed("compute_all_metrics", timings, impact_metrics.compute_all_metrics, conn)
        n_metrics = _timed("persist_metrics", timings, impact_metrics.persist_metrics, conn, metrics)

        export_counts = _timed("export_all", timings, export.export_all, conn)

    result = PipelineResult(
        n_standards=n_standards,
        n_firm_adoptions=n_firm_adoptions,
        n_metrics=n_metrics,
        export_counts=export_counts,
        stage_timings=timings,
    )
    logger.info("Pipeline complete in %.4fs: %s", result.total_seconds, result.to_dict())
    return result


if __name__ == "__main__":
    res = run_pipeline()
    print(json.dumps(res.to_dict(), indent=2))
