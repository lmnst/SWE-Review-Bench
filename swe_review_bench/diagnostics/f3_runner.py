"""F.3 prompt-variant sweep, parameterised for n=100 scaling.

Originally the Round 2 sweep over 20 instances x {sonnet, gpt-4o-mini} x
{A, B, C} = 120 calls. ``run()`` is now parameterised on ``n``,
``variants``, ``reviewers``, ``output_dir`` and ``hard_cap``; the defaults
reproduce the original Round 2 behaviour byte for byte. Static reviewer
does NOT participate here (it is variant-agnostic and free; run it via the
main CLI). Variant A cache-hits the Round 1 cache via read-through; B and
C live under the Round 2 cache.

Hard cost cap (default $5): per-call running cost is monitored; if the
running total exceeds 0.9 * cap, the run aborts after the current call,
writes ``<output_dir>/abort.json`` with the stop reason, and exits
non-zero. Partial CSV rows are preserved (the CSV is appended row by row,
not buffered).

A ``--dry-run`` mode loads the instances, asserts that the n=20 pilot is a
subset of the requested sample, counts the reviewer-input files (one LLM
call each), and prints the projected call count and cost without issuing
any API call.

Outputs (always written, even on abort):
  <output_dir>/variant_results.csv    -- one row per comment + placeholders
  <output_dir>/variant_summary.csv    -- one row per (reviewer, variant)
  <output_dir>/abort.json             -- only if the cost gate tripped

Order of execution: variants in the given order (default A -> B -> C), so
an early abort preserves the higher-priority data (A is free; B is the
experimental contrast).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ..config import Config, load_config
from ..data.loader import Instance, load_instances
from ..data.oracle import OracleSite, build_oracle_sites, is_test_file, oracle_files
from ..data.repos import RepoUnavailable, ensure_repo_at_commit
from ..reviewers.base import ReviewerInput
from ..reviewers.llm import LLMReviewer
from ..reviewers.prompt_variants import VARIANTS
from ..run import (
    _assert_no_oracle_leak,
    _is_test_file_skipped,
    _patched_files_from_patch,
    _prepare_reviewer_inputs,
)
from ..scoring.metrics import InstanceScore, score_instance


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUND2_DIR = PROJECT_ROOT / "outputs" / "round2"

LLM_REVIEWERS = ("claude-sonnet-4-5", "gpt-4o-mini")
VARIANT_ORDER = ("A", "B", "C")
HARD_CAP_USD = 5.0
ABORT_THRESHOLD = 0.9 * HARD_CAP_USD  # $4.50
TOLERANCE = 3

DATASET = "princeton-nlp/SWE-bench_Lite"
SPLIT = "test"
PILOT_N = 20
PILOT_SEED = 42

# Observed per-call cost (one reviewed file). Variant A uses the Round 1
# rates; B and C use the slightly higher Round 2 rates (Variant C lengthens
# completions). Source: outputs/summary.csv and outputs/round2/variant_summary.csv.
COST_PER_CALL: dict[tuple[str, str], float] = {
    ("claude-sonnet-4-5", "A"): 0.04369,
    ("claude-sonnet-4-5", "B"): 0.04597,
    ("claude-sonnet-4-5", "C"): 0.04597,
    ("gpt-4o-mini", "A"): 0.00180,
    ("gpt-4o-mini", "B"): 0.00195,
    ("gpt-4o-mini", "C"): 0.00195,
}


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


def _abort_state(
    running_cost: float,
    stop_reason: str,
    *,
    abort_threshold: float,
    hard_cap: float,
) -> dict[str, Any]:
    return {
        "stop_reason": stop_reason,
        "running_cost_usd": running_cost,
        "abort_threshold_usd": abort_threshold,
        "hard_cap_usd": hard_cap,
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


def _resolve(
    variants: tuple[str, ...] | None,
    reviewers: tuple[str, ...] | None,
    output_dir: Path | None,
    hard_cap: float | None,
) -> tuple[tuple[str, ...], tuple[str, ...], Path, float]:
    variants = tuple(variants) if variants is not None else VARIANT_ORDER
    reviewers = tuple(reviewers) if reviewers is not None else LLM_REVIEWERS
    output_dir = Path(output_dir) if output_dir is not None else ROUND2_DIR
    hard_cap = float(hard_cap) if hard_cap is not None else HARD_CAP_USD
    for v in variants:
        if v not in VARIANTS:
            raise ValueError(f"unknown variant {v!r}; expected one of {sorted(VARIANTS)}")
    if "static" in reviewers:
        raise ValueError(
            "static is variant-agnostic and free; run it via the main CLI, "
            "not this LLM-only sweep"
        )
    return variants, reviewers, output_dir, hard_cap


def _llm_calls_for_instance(inst: Instance) -> int:
    """Number of reviewer-input files for an instance.

    One LLM call is issued per reviewed file. The reviewer sees every
    patched file except ``__pycache__`` artefacts (tests are included).
    This is an upper bound on billed calls: it does not subtract files
    that turn out to be missing at ``base_commit`` or binary, which only a
    repo checkout can detect.
    """
    return sum(
        1
        for rel in _patched_files_from_patch(inst.patch)
        if not _is_test_file_skipped(rel)
    )


def dry_run(
    *,
    n: int = 100,
    seed: int = 42,
    variants: tuple[str, ...] | None = None,
    reviewers: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Project call counts and cost for the requested sweep, no API calls."""
    variants, reviewers, _, _ = _resolve(variants, reviewers, None, None)

    pilot = load_instances(n=PILOT_N, seed=PILOT_SEED, dataset=DATASET, split=SPLIT)
    full = load_instances(n=n, seed=seed, dataset=DATASET, split=SPLIT)
    pilot_ids = {i.instance_id for i in pilot}
    full_ids = {i.instance_id for i in full}
    subset_ok = pilot_ids <= full_ids
    if not subset_ok:
        missing = sorted(pilot_ids - full_ids)
        raise AssertionError(
            f"pilot ids are NOT a subset of the n={n} sample; cache reuse is "
            f"unsafe. missing from sample: {missing}"
        )

    new = [i for i in full if i.instance_id not in pilot_ids]
    calls_new = sum(_llm_calls_for_instance(i) for i in new)
    calls_pilot = sum(_llm_calls_for_instance(i) for i in pilot)

    multi_file_new = sum(
        1 for i in new if len(oracle_files(build_oracle_sites(i.patch))) >= 2
    )
    repos: dict[str, int] = {}
    for i in full:
        repos[i.repo] = repos.get(i.repo, 0) + 1

    print(f"dry run: n={n} seed={seed} variants={list(variants)} reviewers={list(reviewers)}")
    print(f"  pilot ids subset of sample: {subset_ok} ({len(pilot_ids)}/{len(pilot_ids)})")
    print(f"  instances: {len(full)} total, {len(new)} new, {len(pilot)} reused (cache hit)")
    print(f"  new multi-file instances: {multi_file_new}")
    print(f"  reviewer-input files (upper bound on calls): {calls_new} new, {calls_pilot} reused")
    print("  repo distribution (full sample):")
    for r in sorted(repos):
        print(f"    {r:>28}  {repos[r]}")

    total_cost = 0.0
    print("  projected billed cost (reused instances are cache hits at $0):")
    rows: list[dict[str, Any]] = []
    for var in variants:
        for rev in reviewers:
            price = COST_PER_CALL.get((rev, var), 0.0)
            cost = calls_new * price
            total_cost += cost
            rows.append(
                {"reviewer": rev, "variant": var, "new_calls": calls_new, "cost_usd": cost}
            )
            print(f"    {rev:>22} variant {var}: {calls_new} new calls x ${price:.5f} = ${cost:.4f}")
    print(f"  PROJECTED TOTAL (upper bound): ${total_cost:.4f}")
    print(f"  suggested hard cap: ${math.ceil(total_cost * 1.3):.0f}")

    return {
        "n": n,
        "seed": seed,
        "variants": list(variants),
        "reviewers": list(reviewers),
        "subset_ok": subset_ok,
        "n_total": len(full),
        "n_new": len(new),
        "n_reused": len(pilot),
        "new_multi_file": multi_file_new,
        "calls_new": calls_new,
        "calls_reused": calls_pilot,
        "projected_total_usd": total_cost,
        "rows": rows,
        "repos": repos,
    }


def run(
    *,
    n: int = 20,
    seed: int = 42,
    variants: tuple[str, ...] | None = None,
    reviewers: tuple[str, ...] | None = None,
    output_dir: Path | None = None,
    hard_cap: float | None = None,
) -> dict[str, Any]:
    variants, reviewers, output_dir, hard_cap = _resolve(
        variants, reviewers, output_dir, hard_cap
    )
    abort_threshold = 0.9 * hard_cap

    cfg = load_config()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Open output CSV for row-by-row appending; truncate if a prior run
    # left a stale file behind.
    results_csv = output_dir / "variant_results.csv"
    if results_csv.exists():
        results_csv.unlink()
    fh, writer = _open_csv_for_append(results_csv)

    abort_path = output_dir / "abort.json"
    if abort_path.exists():
        abort_path.unlink()

    # Per-(reviewer, variant) score accumulators.
    scores: dict[tuple[str, str], list[InstanceScore]] = {
        (rev, var): [] for rev in reviewers for var in variants
    }
    file_level_hits: dict[tuple[str, str], int] = {
        (rev, var): 0 for rev in reviewers for var in variants
    }
    latencies: dict[tuple[str, str], list[float]] = {
        (rev, var): [] for rev in reviewers for var in variants
    }
    fresh_costs: dict[tuple[str, str], list[float]] = {
        (rev, var): [] for rev in reviewers for var in variants
    }
    cache_hits: dict[tuple[str, str], int] = {
        (rev, var): 0 for rev in reviewers for var in variants
    }
    cache_misses: dict[tuple[str, str], int] = {
        (rev, var): 0 for rev in reviewers for var in variants
    }

    running_cost = 0.0
    aborted = False
    abort_reason = ""

    instances = load_instances(n=n, seed=seed, dataset=DATASET, split=SPLIT)
    print(f"loaded {len(instances)} instances")

    # Pre-build reviewer pool so context-window probing happens once per
    # (model, variant) pair.
    reviewer_pool: dict[tuple[str, str], LLMReviewer] = {}
    for var in variants:
        for rev in reviewers:
            reviewer_pool[(rev, var)] = LLMReviewer(rev, cfg, prompt_variant=var)

    # ----- main loop -----
    for var in variants:
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
            tmp_failures = output_dir / "_f3_failures.jsonl"
            reviewer_inputs, _skipped = _prepare_reviewer_inputs(
                inst, repo_path, failures_path=tmp_failures
            )
            if not reviewer_inputs:
                continue
            _assert_no_oracle_leak(reviewer_inputs, inst)

            oracle_file_set = {s.file for s in sites}

            for rev in reviewers:
                if aborted:
                    break
                r = reviewer_pool[(rev, var)]

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
                    if running_cost > abort_threshold:
                        aborted = True
                        abort_reason = (
                            f"running cost {running_cost:.4f} exceeded "
                            f"abort threshold {abort_threshold:.4f} "
                            f"(0.9 * hard cap {hard_cap:.2f})"
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
    for var in variants:
        for rev in reviewers:
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

    summary_csv = output_dir / "variant_summary.csv"
    with summary_csv.open("w", newline="", encoding="utf-8") as fh2:
        writer2 = csv.DictWriter(fh2, fieldnames=list(summary_rows[0].keys()))
        writer2.writeheader()
        writer2.writerows(summary_rows)
    print(f"wrote {summary_csv}")

    if aborted:
        abort_path.write_text(
            json.dumps(
                _abort_state(
                    running_cost,
                    abort_reason,
                    abort_threshold=abort_threshold,
                    hard_cap=hard_cap,
                ),
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"wrote {abort_path}: {abort_reason}")

    return {
        "summary": summary_rows,
        "running_cost": running_cost,
        "aborted": aborted,
        "abort_reason": abort_reason,
        "hard_cap": hard_cap,
        "cache_hits": {f"{r}/{v}": cache_hits[(r, v)] for r in reviewers for v in variants},
        "cache_misses": {f"{r}/{v}": cache_misses[(r, v)] for r in reviewers for v in variants},
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Prompt-variant sweep (LLM reviewers only).")
    p.add_argument("--n", type=int, default=20, help="Number of instances.")
    p.add_argument("--seed", type=int, default=42, help="Sampling seed.")
    p.add_argument(
        "--variants",
        default=",".join(VARIANT_ORDER),
        help="Comma-separated variant names (A,B,C).",
    )
    p.add_argument(
        "--reviewers",
        default=",".join(LLM_REVIEWERS),
        help="Comma-separated LLM reviewer ids.",
    )
    p.add_argument(
        "--output-dir",
        default=str(ROUND2_DIR),
        help="Where to write variant_results.csv and variant_summary.csv.",
    )
    p.add_argument("--hard-cap", type=float, default=HARD_CAP_USD, help="USD hard cap.")
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Project call count and cost without any API call.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    variants = tuple(v.strip().upper() for v in args.variants.split(",") if v.strip())
    reviewers = tuple(r.strip() for r in args.reviewers.split(",") if r.strip())

    if args.dry_run:
        dry_run(n=args.n, seed=args.seed, variants=variants, reviewers=reviewers)
        return

    state = run(
        n=args.n,
        seed=args.seed,
        variants=variants,
        reviewers=reviewers,
        output_dir=Path(args.output_dir),
        hard_cap=args.hard_cap,
    )
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
    print(f"running_cost=${state['running_cost']:.4f} hard_cap=${state['hard_cap']:.2f}")


if __name__ == "__main__":
    main()
