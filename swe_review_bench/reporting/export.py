"""CSV / JSONL / run-metadata writers for the Milestone D full run.

Three artefacts are emitted in ``outputs/``:

* ``results.csv``        one row per emitted comment, plus a placeholder
                         row whenever a reviewer/file pair was skipped
                         (e.g. ``TokenLimitExceeded``) so the downstream
                         analysis can tell "no comments" apart from
                         "didn't run".
* ``summary.csv``        one row per reviewer, with the agreed
                         single/multi-file bug breakdown columns.
* ``failures.jsonl``     append-only event log; one JSON object per line.
* ``run_meta.json``      reproducibility metadata for the run.

Columns and field names follow the spec exactly.
"""

from __future__ import annotations

import json
import platform
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from ..scoring.metrics import ReviewerSummary


# ---------------------------------------------------------------------------
# Column orders (single source of truth)
# ---------------------------------------------------------------------------

RESULTS_COLUMNS: tuple[str, ...] = (
    "instance_id",
    "repo",
    "base_commit",
    "reviewer",
    "file",
    "line_start",
    "line_end",
    "severity",
    "message",
    "is_hit",
    "matched_oracle_site_id",
    "tolerance",
    "raw_output_path",
    "latency_seconds",
    "input_tokens",
    "output_tokens",
    "estimated_cost_usd",
    "instance_n_oracle_files",
    "skipped_reason",
)

SUMMARY_COLUMNS: tuple[str, ...] = (
    "reviewer",
    "n_instances",
    "instance_hit_rate",
    "site_recall",
    "false_positives_per_instance_mean",
    "false_positives_per_instance_median",
    "precision_at_1",
    "precision_at_3",
    "precision_at_5",
    "latency_avg_seconds",
    "total_estimated_cost_usd",
    "n_instances_single_file",
    "n_instances_multi_file",
    "instance_hit_rate_single_file",
    "instance_hit_rate_multi_file",
)


# ---------------------------------------------------------------------------
# Per-reviewer cost / latency aggregation
# ---------------------------------------------------------------------------


@dataclass
class ReviewerRunAggregate:
    """Runtime cost/latency accumulator for one reviewer across the whole run.

    ``latency_avg_seconds`` is the mean over EVERY ``Reviewer.review`` call,
    including cache hits (which contribute ~0). ``total_estimated_cost_usd``
    counts a call only when ``cache_hit`` is False -- a cache hit cost the
    user nothing on this run.
    """

    latencies: list[float]
    fresh_costs: list[float]

    def mean_latency(self) -> float:
        return sum(self.latencies) / len(self.latencies) if self.latencies else 0.0

    def total_cost(self) -> float:
        return sum(self.fresh_costs)


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------


def write_results_csv(rows: list[dict[str, Any]], path: Path) -> None:
    """Write the per-comment results CSV in the fixed column order."""
    df = pd.DataFrame(rows, columns=list(RESULTS_COLUMNS))
    df.to_csv(path, index=False)


def write_summary_csv(
    summaries: list[ReviewerSummary],
    aggregates: dict[str, ReviewerRunAggregate],
    path: Path,
) -> None:
    """Write one row per reviewer with all aggregate metrics."""
    rows: list[dict[str, Any]] = []
    for s in summaries:
        agg = aggregates.get(s.reviewer)
        rows.append(
            {
                "reviewer": s.reviewer,
                "n_instances": s.n_instances,
                "instance_hit_rate": s.instance_hit_rate,
                "site_recall": s.site_recall,
                "false_positives_per_instance_mean": s.fp_per_instance_mean,
                "false_positives_per_instance_median": s.fp_per_instance_median,
                "precision_at_1": s.precision_at.get(1, 0.0),
                "precision_at_3": s.precision_at.get(3, 0.0),
                "precision_at_5": s.precision_at.get(5, 0.0),
                "latency_avg_seconds": agg.mean_latency() if agg else 0.0,
                "total_estimated_cost_usd": agg.total_cost() if agg else 0.0,
                "n_instances_single_file": s.n_instances_single_file,
                "n_instances_multi_file": s.n_instances_multi_file,
                "instance_hit_rate_single_file": s.instance_hit_rate_single_file,
                "instance_hit_rate_multi_file": s.instance_hit_rate_multi_file,
            }
        )
    df = pd.DataFrame(rows, columns=list(SUMMARY_COLUMNS))
    df.to_csv(path, index=False)


def append_failure(path: Path, **fields: Any) -> None:
    """Append one structured failure event to ``failures.jsonl``."""
    fields.setdefault("timestamp", _utc_now_iso())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(fields, ensure_ascii=False, default=str) + "\n")


def write_run_meta(path: Path, meta: dict[str, Any]) -> None:
    """Write ``run_meta.json`` for reproducibility."""
    meta = dict(meta)
    meta.setdefault("timestamp", _utc_now_iso())
    meta.setdefault("python_version", platform.python_version())
    meta.setdefault("platform", platform.platform())
    path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
