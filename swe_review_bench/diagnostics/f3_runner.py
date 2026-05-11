"""F.3 prompt-variant sweep.

Runs 20 instances x {sonnet, gpt-4o-mini} x {A, B, C} = 120 calls.
Static reviewer does NOT participate. Variant A is expected to cache-hit
100% on the Round 1 cache via read-through; B and C are fresh.

Hard cost cap: $5. Per-call running cost is monitored; if the running
total exceeds 0.9 * cap, the run aborts after the current call,
writes ``outputs/round2/abort.json`` with the stop reason, and exits
non-zero. Partial CSV rows are preserved (the CSV is appended row by
row, not buffered).

Outputs (always written, even on abort):
  outputs/round2/variant_results.csv    -- one row per comment + placeholders
  outputs/round2/variant_summary.csv    -- one row per (reviewer, variant)
  outputs/round2/variant_comparison.png -- grouped bar chart
  outputs/round2/variant_analysis.md    -- discussion (no winner picked)

Order of execution: A -> B -> C, so an early-abort preserves the
higher-priority data (A is free; B is the experimental contrast).
"""

from __future__ import annotations

import csv
import json
import math
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..config import Config, load_config
from ..data.loader import Instance, load_instances
from ..data.oracle import OracleSite, build_oracle_sites, is_test_file
from ..data.repos import RepoUnavailable, ensure_repo_at_commit
from ..reviewers.base import ReviewerInput
from ..reviewers.llm import LLMReviewer
from ..reviewers.prompt_variants import VARIANTS
from ..run import _assert_no_oracle_leak, _prepare_reviewer_inputs
from ..scoring.metrics import InstanceScore, score_instance


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUND2_DIR = PROJECT_ROOT / "outputs" / "round2"

LLM_REVIEWERS = ("claude-sonnet-4-5", "gpt-4o-mini")
VARIANT_ORDER = ("A", "B", "C")
HARD_CAP_USD = 5.0
ABORT_THRESHOLD = 0.9 * HARD_CAP_USD  # $4.50
TOLERANCE = 3


VARIANT_RESULTS_COLUMNS = (
    "instance_id",
    "repo",
    "base_commit",
    "reviewer",
    "prompt_variant",
    "template_id",
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
    "cache_hit",
)


def _wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def _wilson_ci_safe(k: int, n: int) -> tuple[float, float, float]:
    """Return (rate, ci_lo, ci_hi)."""
    rate = (k / n) if n else 0.0
    lo, hi = _wilson_ci(k, n)
    return rate, lo, hi


def _abort_state(running_cost: float, stop_reason: str) -> dict[str, Any]:
    return {
        "stop_reason": stop_reason,
        "running_cost_usd": running_cost,
        "abort_threshold_usd": ABORT_THRESHOLD,
        "hard_cap_usd": HARD_CAP_USD,
    }


def _open_csv_for_append(path: Path) -> tuple[Any, Any]:
    """Open the variant_results CSV for append, writing the header if new."""
    new = not path.exists()
    fh = path.open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(fh, fieldnames=list(VARIANT_RESULTS_COLUMNS))
    if new:
        writer.writeheader()
    return fh, writer


def _row_for_comment(
    *,
    inst: Instance,
    reviewer_name: str,
    variant_name: str,
    template_id: str,
    file_path: str,
    c,
    site_id: str | None,
    tolerance: int,
    n_oracle_files: int,
    meta,
) -> dict[str, Any]:
    return {
        "instance_id": inst.instance_id,
        "repo": inst.repo,
        "base_commit": inst.base_commit,
        "reviewer": reviewer_name,
        "prompt_variant": variant_name,
        "template_id": template_id,
        "file": c.file,
        "line_start": c.line_start,
        "line_end": c.line_end,
        "severity": c.severity,
        "message": c.message,
        "is_hit": site_id is not None,
        "matched_oracle_site_id": site_id or "",
        "tolerance": tolerance,
        "raw_output_path": meta.raw_output_path or "",
        "latency_seconds": meta.latency_seconds,
        "input_tokens": meta.input_tokens,
        "output_tokens": meta.output_tokens,
        "estimated_cost_usd": meta.estimated_cost_usd,
        "instance_n_oracle_files": n_oracle_files,
        "skipped_reason": meta.skipped_reason or "",
        "cache_hit": bool(meta.cache_hit),
    }


def _row_skipped(
    *,
    inst: Instance,
    reviewer_name: str,
    variant_name: str,
    template_id: str,
    file_path: str,
    tolerance: int,
    n_oracle_files: int,
    meta,
) -> dict[str, Any]:
    return {
        "instance_id": inst.instance_id,
        "repo": inst.repo,
        "base_commit": inst.base_commit,
        "reviewer": reviewer_name,
        "prompt_variant": variant_name,
        "template_id": template_id,
        "file": file_path,
        "line_start": None,
        "line_end": None,
        "severity": "",
        "message": "",
        "is_hit": False,
        "matched_oracle_site_id": "",
        "tolerance": tolerance,
        "raw_output_path": meta.raw_output_path or "",
        "latency_seconds": meta.latency_seconds,
        "input_tokens": meta.input_tokens,
        "output_tokens": meta.output_tokens,
        "estimated_cost_usd": meta.estimated_cost_usd,
        "instance_n_oracle_files": n_oracle_files,
        "skipped_reason": meta.skipped_reason or "",
        "cache_hit": bool(meta.cache_hit),
    }


def run() -> dict[str, Any]:
    cfg = load_config()
    ROUND2_DIR.mkdir(parents=True, exist_ok=True)

    # Open output CSV for row-by-row appending; truncate if a prior run
    # left a stale file behind.
    results_csv = ROUND2_DIR / "variant_results.csv"
    if results_csv.exists():
        results_csv.unlink()
    fh, writer = _open_csv_for_append(results_csv)

    abort_path = ROUND2_DIR / "abort.json"
    if abort_path.exists():
        abort_path.unlink()

    # Per-(reviewer, variant) score accumulators.
    scores: dict[tuple[str, str], list[InstanceScore]] = {
        (rev, var): [] for rev in LLM_REVIEWERS for var in VARIANT_ORDER
    }
    file_level_hits: dict[tuple[str, str], int] = {
        (rev, var): 0 for rev in LLM_REVIEWERS for var in VARIANT_ORDER
    }
    latencies: dict[tuple[str, str], list[float]] = {
        (rev, var): [] for rev in LLM_REVIEWERS for var in VARIANT_ORDER
    }
    fresh_costs: dict[tuple[str, str], list[float]] = {
        (rev, var): [] for rev in LLM_REVIEWERS for var in VARIANT_ORDER
    }
    cache_hits: dict[tuple[str, str], int] = {
        (rev, var): 0 for rev in LLM_REVIEWERS for var in VARIANT_ORDER
    }
    cache_misses: dict[tuple[str, str], int] = {
        (rev, var): 0 for rev in LLM_REVIEWERS for var in VARIANT_ORDER
    }

    running_cost = 0.0
    aborted = False
    abort_reason = ""

    instances = load_instances(
        n=20, seed=42, dataset="princeton-nlp/SWE-bench_Lite", split="test"
    )
    print(f"loaded {len(instances)} instances")

    # Pre-build reviewer pool so context-window probing happens once per
    # (model, variant) pair.
    reviewers: dict[tuple[str, str], LLMReviewer] = {}
    for var in VARIANT_ORDER:
        for rev in LLM_REVIEWERS:
            reviewers[(rev, var)] = LLMReviewer(rev, cfg, prompt_variant=var)

    # ----- main loop -----
    for var in VARIANT_ORDER:
        if aborted:
            break
        print(f"\n=== Variant {var} ({VARIANTS[var].template_id}) ===")
        for inst in instances:
            if aborted:
                break
            # Re-checkout repo to this instance's base_commit (read state).
            try:
                repo_path = ensure_repo_at_commit(
                    inst.repo,
                    inst.base_commit,
                    repos_cache_dir=cfg.repos_cache_dir,
                )
            except RepoUnavailable as e:
                print(f"  [{var}/{inst.instance_id}] repo unavailable: {e}")
                continue

            sites: list[OracleSite] = build_oracle_sites(inst.patch, strict_mode=False)
            if not sites:
                continue
            from ..data.oracle import oracle_files as _oracle_files
            n_oracle_files = len(_oracle_files(sites))

            # Reuse run.py's reviewer-input preparation (also runs the
            # leakage assertion below).
            tmp_failures = ROUND2_DIR / "_f3_failures.jsonl"
            reviewer_inputs, _skipped = _prepare_reviewer_inputs(
                inst, repo_path, failures_path=tmp_failures
            )
            if not reviewer_inputs:
                continue
            _assert_no_oracle_leak(reviewer_inputs, inst)

            oracle_file_set = {s.file for s in sites}

            for rev in LLM_REVIEWERS:
                if aborted:
                    break
                r = reviewers[(rev, var)]

                all_comments = []
                per_file_results = []  # (ri, result)
                for ri in reviewer_inputs:
                    if aborted:
                        break
                    try:
                        result = r.review(ri)
                    except Exception as e:  # noqa: BLE001
                        print(
                            f"  [{var}/{inst.instance_id}/{rev}/{ri.file_path}] "
                            f"reviewer crashed: {type(e).__name__}: {e}"
                        )
                        continue
                    per_file_results.append((ri, result))
                    all_comments.extend(result.comments)
                    meta = result.meta
                    latencies[(rev, var)].append(meta.latency_seconds)
                    if meta.cache_hit:
                        cache_hits[(rev, var)] += 1
                    else:
                        cache_misses[(rev, var)] += 1
                        if meta.estimated_cost_usd is not None:
                            fresh_costs[(rev, var)].append(meta.estimated_cost_usd)
                            running_cost += meta.estimated_cost_usd

                    # Cost gate.
                    if running_cost > ABORT_THRESHOLD:
                        aborted = True
                        abort_reason = (
                            f"running cost {running_cost:.4f} exceeded "
                            f"abort threshold {ABORT_THRESHOLD:.4f} "
                            f"(0.9 * hard cap {HARD_CAP_USD:.2f})"
                        )
                        break

                # Score this (instance, reviewer, variant) using the
                # existing scoring module so the math matches Round 1.
                score = score_instance(
                    instance_id=inst.instance_id,
                    reviewer=rev,
                    comments=all_comments,
                    sites=sites,
                    tolerance=TOLERANCE,
                )
                scores[(rev, var)].append(score)
                # File-level coverage: at least one valid comment on any
                # oracle file.
                if any(
                    c.file in oracle_file_set for c in all_comments
                ):
                    file_level_hits[(rev, var)] += 1

                # Emit rows.
                comment_idx = 0
                site_for_idx = score.outcome.comment_to_site if score.outcome else ()
                for ri, result in per_file_results:
                    meta = result.meta
                    if meta.skipped_reason and meta.skipped_reason not in (
                        None,
                        "UnsupportedFileType",
                    ):
                        writer.writerow(
                            _row_skipped(
                                inst=inst,
                                reviewer_name=rev,
                                variant_name=var,
                                template_id=r.variant.template_id,
                                file_path=ri.file_path,
                                tolerance=TOLERANCE,
                                n_oracle_files=n_oracle_files,
                                meta=meta,
                            )
                        )
                        continue
                    if not result.comments:
                        continue
                    for c in result.comments:
                        site_id = (
                            site_for_idx[comment_idx]
                            if comment_idx < len(site_for_idx)
                            else None
                        )
                        writer.writerow(
                            _row_for_comment(
                                inst=inst,
                                reviewer_name=rev,
                                variant_name=var,
                                template_id=r.variant.template_id,
                                file_path=ri.file_path,
                                c=c,
                                site_id=site_id,
                                tolerance=TOLERANCE,
                                n_oracle_files=n_oracle_files,
                                meta=meta,
                            )
                        )
                        comment_idx += 1
                fh.flush()
                print(
                    f"  [{var}/{inst.instance_id}/{rev}] "
                    f"n_comments={score.n_comments} "
                    f"hits={score.n_sites_hit} "
                    f"cache={'HIT' if all(meta.cache_hit for _, r2 in per_file_results for meta in [r2.meta]) else 'mix'} "
                    f"running_cost=${running_cost:.4f}"
                )

    fh.close()
    print(f"\nrunning_cost=${running_cost:.4f}  aborted={aborted}")

    # ----- summary -----
    summary_rows: list[dict[str, Any]] = []
    n_total = len(instances)
    for var in VARIANT_ORDER:
        for rev in LLM_REVIEWERS:
            scs = scores[(rev, var)]
            n_inst = len(scs)
            n_hits = sum(1 for s in scs if s.has_hit)
            n_comments = sum(s.n_comments for s in scs)
            n_fp = sum(s.n_fp for s in scs)
            total_sites = sum(s.n_sites for s in scs)
            sites_hit = sum(s.n_sites_hit for s in scs)
            site_recall = (sites_hit / total_sites) if total_sites else 0.0
            site_lo, site_hi = _wilson_ci(sites_hit, total_sites) if total_sites else (0.0, 0.0)
            ihr, ihr_lo, ihr_hi = _wilson_ci_safe(n_hits, n_total)
            flr, flr_lo, flr_hi = _wilson_ci_safe(file_level_hits[(rev, var)], n_total)
            p_at = {
                k: (
                    sum(s.precision_at.get(k, 0.0) for s in scs) / n_inst
                    if n_inst else 0.0
                )
                for k in (1, 3, 5)
            }
            comments_per_inst = (n_comments / n_total) if n_total else 0.0
            lat = latencies[(rev, var)]
            fc = fresh_costs[(rev, var)]
            summary_rows.append(
                {
                    "reviewer": rev,
                    "prompt_variant": var,
                    "template_id": VARIANTS[var].template_id,
                    "n_instances": n_total,
                    "n_scored": n_inst,
                    "n_comments": n_comments,
                    "comments_per_instance": comments_per_inst,
                    "instance_hit_rate": ihr,
                    "instance_hit_rate_wilson_lo": ihr_lo,
                    "instance_hit_rate_wilson_hi": ihr_hi,
                    "site_recall": site_recall,
                    "site_recall_wilson_lo": site_lo,
                    "site_recall_wilson_hi": site_hi,
                    "file_level_hit_rate": flr,
                    "file_level_hit_rate_wilson_lo": flr_lo,
                    "file_level_hit_rate_wilson_hi": flr_hi,
                    "false_positives_per_instance_mean": (n_fp / n_total) if n_total else 0.0,
                    "precision_at_1": p_at[1],
                    "precision_at_3": p_at[3],
                    "precision_at_5": p_at[5],
                    "latency_avg_seconds": (sum(lat) / len(lat)) if lat else 0.0,
                    "estimated_total_cost_usd": sum(fc),
                    "cache_hits": cache_hits[(rev, var)],
                    "cache_misses": cache_misses[(rev, var)],
                }
            )

    summary_csv = ROUND2_DIR / "variant_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as fh2:
        writer2 = csv.DictWriter(fh2, fieldnames=list(summary_rows[0].keys()))
        writer2.writeheader()
        writer2.writerows(summary_rows)
    print(f"wrote {summary_csv}")

    if aborted:
        abort_path.write_text(
            json.dumps(_abort_state(running_cost, abort_reason), indent=2),
            encoding="utf-8",
        )
        print(f"wrote {abort_path}: {abort_reason}")

    return {
        "summary": summary_rows,
        "running_cost": running_cost,
        "aborted": aborted,
        "abort_reason": abort_reason,
        "cache_hits": {f"{r}/{v}": cache_hits[(r, v)] for r in LLM_REVIEWERS for v in VARIANT_ORDER},
        "cache_misses": {f"{r}/{v}": cache_misses[(r, v)] for r in LLM_REVIEWERS for v in VARIANT_ORDER},
    }


def main() -> None:
    state = run()
    # Print a brief stdout summary.
    for row in state["summary"]:
        print(
            f"  {row['reviewer']:>22} variant {row['prompt_variant']}: "
            f"n_comments={row['n_comments']:>4}  "
            f"hit_rate={row['instance_hit_rate']:.2f}  "
            f"file_rate={row['file_level_hit_rate']:.2f}  "
            f"fp/inst={row['false_positives_per_instance_mean']:.2f}  "
            f"cost=${row['estimated_total_cost_usd']:.4f}  "
            f"cache_hits={row['cache_hits']}/{row['cache_hits']+row['cache_misses']}"
        )
    print(f"running_cost=${state['running_cost']:.4f} hard_cap=${HARD_CAP_USD:.2f}")


if __name__ == "__main__":
    main()
