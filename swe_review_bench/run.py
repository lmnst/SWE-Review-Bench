"""Entry point for SWE-Review-Bench.

Two CLI modes:

* ``--smoke-test``  -- runs the data prep + 3 reviewers + scoring on a
                       single instance, no files written. Used for
                       development verification.
* otherwise         -- the full Milestone D pipeline: clone & checkout N
                       instances, run each reviewer, score, and write
                       ``results.csv`` / ``summary.csv`` /
                       ``hit_fp_bar_chart.png`` / ``failures.jsonl`` /
                       ``run_meta.json`` under ``--output-dir``.
"""

from __future__ import annotations

import importlib.metadata
import platform
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import litellm
import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from unidiff import PatchSet

from .config import Config, load_config
from .data.loader import Instance, load_instances
from .data.oracle import (
    OracleSite,
    build_oracle_sites,
    is_multi_file_bug,
    oracle_files,
)
from .data.repos import (
    RepoUnavailable,
    ensure_repo_at_commit,
    read_file_bytes,
    try_decode_utf8,
)
from .reporting.charts import write_hit_fp_chart
from .reporting.export import (
    ReviewerRunAggregate,
    append_failure,
    write_results_csv,
    write_run_meta,
    write_summary_csv,
)
from .reviewers.base import ReviewResult, Reviewer, ReviewerInput
from .reviewers.llm import LLMReviewer
from .reviewers.static import StaticReviewer
from .scoring.metrics import (
    InstanceScore,
    ReviewerSummary,
    score_instance,
    summarise_reviewer,
)

console = Console()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patched_files_from_patch(patch_text: str) -> list[str]:
    """List the distinct file paths touched by a patch.

    Prefers the source-side path (pre-fix file); falls back to the
    target-side path for new files added by the patch.
    """
    out: list[str] = []
    for pfile in PatchSet(patch_text):
        src = pfile.source_file or ""
        if src and src != "/dev/null":
            rel = src[2:] if src.startswith(("a/", "b/")) else src
        else:
            tgt = pfile.target_file or ""
            if not tgt or tgt == "/dev/null":
                continue
            rel = tgt[2:] if tgt.startswith(("a/", "b/")) else tgt
        if rel and rel not in out:
            out.append(rel)
    return out


def _assert_no_oracle_leak(
    reviewer_inputs: list[ReviewerInput], instance: Instance
) -> None:
    """Hard guard: no oracle text may appear in any ``ReviewerInput``."""
    payload = "\n".join(ri.serialised() for ri in reviewer_inputs)
    if instance.patch and instance.patch in payload:
        raise AssertionError("LEAK: fix patch body found inside ReviewerInput payload.")
    if instance.test_patch and instance.test_patch in payload:
        raise AssertionError("LEAK: test patch body found inside ReviewerInput payload.")
    ps = (instance.problem_statement or "").strip()
    if len(ps) >= 32 and ps in payload:
        raise AssertionError("LEAK: problem_statement found inside ReviewerInput payload.")
    sample = asdict(reviewer_inputs[0]) if reviewer_inputs else {}
    forbidden = {"problem_statement", "patch", "test_patch", "base_commit", "instance_id"}
    overlap = forbidden & set(sample.keys())
    if overlap:
        raise AssertionError(f"LEAK: ReviewerInput exposes oracle fields: {overlap}")


def _print_sites(sites: list[OracleSite]) -> None:
    if not sites:
        console.print("[yellow](no sites)[/yellow]")
        return
    t = Table(show_header=True, header_style="bold")
    t.add_column("site_id")
    t.add_column("file")
    t.add_column("range", justify="right")
    for s in sites:
        t.add_row(s.site_id, s.file, f"{s.line_start}-{s.line_end}")
    console.print(t)


def _build_reviewers(
    spec: str,
    cfg: Config,
    *,
    max_comments_per_file: int,
    prompt_variant: str = "A",
) -> list[Reviewer]:
    """Construct the requested reviewers in the order given.

    ``spec`` is a comma-separated list. ``static`` maps to the union
    Ruff+Pylint reviewer; any other id is treated as an LLM model id and
    routed through litellm. ``prompt_variant`` selects the Round 2
    template (A = Round 1 v1 byte-identical, B = no-suppression, C =
    force-emit). Static reviewer is variant-agnostic.
    """
    out: list[Reviewer] = []
    for raw_id in spec.split(","):
        rid = raw_id.strip()
        if not rid:
            continue
        if rid == "static":
            out.append(StaticReviewer(cfg, max_comments_per_file=max_comments_per_file))
        else:
            out.append(LLMReviewer(rid, cfg, prompt_variant=prompt_variant))
    return out


def _print_review(reviewer: Reviewer, result: ReviewResult) -> None:
    """Render one reviewer's output -- comments table plus meta line."""
    m = result.meta
    if result.comments:
        t = Table(show_header=True, header_style="bold cyan", title=f"{reviewer.name} comments")
        t.add_column("line", justify="right")
        t.add_column("sev")
        t.add_column("message")
        for c in result.comments:
            line = f"{c.line_start}" if c.line_start == c.line_end else f"{c.line_start}-{c.line_end}"
            t.add_row(line, c.severity, c.message[:140])
        console.print(t)
    else:
        console.print(
            f"[cyan]{reviewer.name}[/cyan]: no comments "
            f"({'cache' if m.cache_hit else 'fresh'}, "
            f"skipped_reason={m.skipped_reason or '-'}, "
            f"parse_error={m.parse_error})"
        )
    cost = f"${m.estimated_cost_usd:.5f}" if m.estimated_cost_usd is not None else "n/a"
    console.print(
        f"  meta: latency={m.latency_seconds:.2f}s | "
        f"in={m.input_tokens or '-'} | out={m.output_tokens or '-'} | "
        f"est_in={m.estimated_input_tokens or '-'} | cost={cost} | "
        f"cache_hit={m.cache_hit} | parse_error={m.parse_error} | "
        f"skipped={m.skipped_reason or '-'}"
    )


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def _print_scores(scores: list[InstanceScore], *, tolerance: int) -> None:
    """Render per-reviewer score rows for a single instance."""
    t = Table(
        show_header=True,
        header_style="bold magenta",
        title=f"Per-reviewer scores (tolerance N={tolerance})",
    )
    t.add_column("reviewer")
    t.add_column("comments", justify="right")
    t.add_column("hits", justify="right")
    t.add_column("FP", justify="right")
    t.add_column("hit?", justify="center")
    t.add_column("site_recall", justify="right")
    t.add_column("p@1", justify="right")
    t.add_column("p@3", justify="right")
    t.add_column("p@5", justify="right")
    for s in scores:
        recall = (s.n_sites_hit / s.n_sites) if s.n_sites else 0.0
        t.add_row(
            s.reviewer,
            str(s.n_comments),
            str(s.n_hits),
            str(s.n_fp),
            "[green]Y[/green]" if s.has_hit else "[red]N[/red]",
            f"{recall:.2f}",
            f"{s.precision_at.get(1, 0.0):.2f}",
            f"{s.precision_at.get(3, 0.0):.2f}",
            f"{s.precision_at.get(5, 0.0):.2f}",
        )
    console.print(t)


def _run_smoke_test(
    *,
    seed: int,
    dataset: str,
    split: str,
    reviewers_spec: str,
    max_comments_per_file: int,
    tolerance: int,
) -> None:
    cfg = load_config()
    if cfg.model_id_override:
        for src, dst in cfg.model_id_override.items():
            console.print(
                f"[bold red]MODEL ID OVERRIDE ACTIVE:[/bold red] {src} -> {dst}"
            )

    console.rule("[bold]Step 1: load 1 instance from SWE-bench Lite")
    instances = load_instances(n=1, seed=seed, dataset=dataset, split=split)
    inst = instances[0]
    meta = Table(show_header=False, box=None)
    meta.add_row("instance_id", inst.instance_id)
    meta.add_row("repo", inst.repo)
    meta.add_row("base_commit", inst.base_commit)
    meta.add_row("patch length (chars)", str(len(inst.patch)))
    meta.add_row("test_patch length (chars)", str(len(inst.test_patch)))
    meta.add_row("problem_statement length (chars)", str(len(inst.problem_statement)))
    console.print(meta)

    console.rule("[bold]Step 2: clone repo and checkout base_commit")
    try:
        repo_path = ensure_repo_at_commit(
            inst.repo,
            inst.base_commit,
            repos_cache_dir=cfg.repos_cache_dir,
        )
    except RepoUnavailable as e:
        console.print(f"[red]FAIL[/red]: {e}")
        sys.exit(2)
    console.print(f"repo_path = {repo_path}")

    console.rule("[bold]Step 3: patched files (from the fix patch)")
    patched = _patched_files_from_patch(inst.patch)
    for f in patched:
        console.print(f"  - {f}")

    console.rule("[bold]Step 4: oracle sites (default: full hunk source range)")
    sites = build_oracle_sites(inst.patch, strict_mode=False)
    _print_sites(sites)

    console.rule("[bold]Step 5: oracle sites (strict_mode=True, sanity check)")
    strict_sites = build_oracle_sites(inst.patch, strict_mode=True)
    _print_sites(strict_sites)

    console.print(
        f"[bold]bug-file classification[/bold]: "
        f"non-test files in oracle = {oracle_files(sites)!r}; "
        f"is_multi_file_bug = {is_multi_file_bug(sites)}"
    )

    console.rule("[bold]Step 6: read patched files from working tree")
    reviewer_inputs: list[ReviewerInput] = []
    missing: list[str] = []
    binary: list[str] = []
    for rel in patched:
        try:
            data = read_file_bytes(repo_path, rel)
        except FileNotFoundError:
            missing.append(rel)
            console.print(f"  - {rel} [yellow](missing at base_commit)[/yellow]")
            continue
        text = try_decode_utf8(data)
        if text is None:
            binary.append(rel)
            console.print(f"  - {rel} ({len(data):,} bytes, [yellow]binary -- skipped[/yellow])")
            continue
        nlines = text.count("\n") + (0 if text.endswith("\n") or not text else 1)
        preview = text.splitlines()[:3]
        console.print(f"  - {rel} ({len(data):,} bytes, {nlines} lines)")
        for i, line in enumerate(preview, start=1):
            console.print(f"      {i}: {line[:120]}")
        reviewer_inputs.append(ReviewerInput(file_path=rel, file_content=text))

    console.rule("[bold]Step 7: leakage check")
    _assert_no_oracle_leak(reviewer_inputs, inst)
    console.print(
        "[green]OK[/green]: no oracle fields and no oracle bodies leaked "
        "into ReviewerInput."
    )

    console.rule("[bold]Step 8: instantiate reviewers")
    try:
        reviewers = _build_reviewers(
            reviewers_spec, cfg, max_comments_per_file=max_comments_per_file
        )
    except RuntimeError as e:
        console.print(f"[red]Reviewer construction failed:[/red] {e}")
        sys.exit(3)
    for r in reviewers:
        extra = ""
        if isinstance(r, LLMReviewer):
            extra = f"  resolved={r.resolved_model}  context_window={r.context_window:,}"
        console.print(f"  - {r.name}{extra}")

    console.rule("[bold]Step 9: run each reviewer on each file")
    # Accumulate comments per reviewer across all files so the scoring step
    # can build one InstanceScore per (instance, reviewer).
    per_reviewer_comments: dict[str, list] = {r.name: [] for r in reviewers}
    for ri in reviewer_inputs:
        console.print(f"[bold]file:[/bold] {ri.file_path}")
        for r in reviewers:
            try:
                result = r.review(ri)
            except Exception as e:  # noqa: BLE001
                console.print(
                    f"  [red]{r.name} raised {type(e).__name__}:[/red] {e}"
                )
                continue
            _print_review(r, result)
            per_reviewer_comments[r.name].extend(result.comments)
            console.print()

    console.rule("[bold]Step 10: scoring against oracle")
    scores: list[InstanceScore] = []
    for r in reviewers:
        scores.append(
            score_instance(
                instance_id=inst.instance_id,
                reviewer=r.name,
                comments=per_reviewer_comments.get(r.name, []),
                sites=sites,
                tolerance=tolerance,
            )
        )
    _print_scores(scores, tolerance=tolerance)

    console.rule("[bold]Smoke test complete")
    console.print(
        f"reviewer_inputs prepared: {len(reviewer_inputs)} "
        f"(binary skipped: {len(binary)}, missing: {len(missing)}); "
        f"reviewers run: {len(reviewers)}"
    )


# ---------------------------------------------------------------------------
# Full run orchestrator (Milestone D)
# ---------------------------------------------------------------------------


_LLM_PROBE_NAMES = ("claude-sonnet-4-5", "gpt-4o-mini")


def _safe_pkg_version(pkg: str) -> str:
    """Return the installed version of ``pkg``, or ``'unknown'`` if missing."""
    try:
        return importlib.metadata.version(pkg)
    except importlib.metadata.PackageNotFoundError:
        return "unknown"


def _is_test_file_skipped(rel: str) -> bool:
    """Reviewer-input filter -- skip clearly non-source artefacts.

    We DO send tests to reviewers (a real reviewer would see them too),
    but we skip vendored ``__pycache__`` etc. to keep prompts tight.
    """
    return "__pycache__" in rel.split("/")


def _prepare_reviewer_inputs(
    inst: Instance,
    repo_path: Path,
    *,
    failures_path: Path,
) -> tuple[list[ReviewerInput], list[str]]:
    """Read each file touched by ``inst.patch`` from disk into a
    ``ReviewerInput``. Returns the list of inputs plus the list of file
    paths that were skipped (binary or missing); both are logged.
    """
    patched = _patched_files_from_patch(inst.patch)
    inputs: list[ReviewerInput] = []
    skipped: list[str] = []
    for rel in patched:
        if _is_test_file_skipped(rel):
            skipped.append(rel)
            continue
        try:
            data = read_file_bytes(repo_path, rel)
        except FileNotFoundError:
            append_failure(
                failures_path,
                instance_id=inst.instance_id,
                file=rel,
                error_type="FileMissingAtBaseCommit",
            )
            skipped.append(rel)
            continue
        text = try_decode_utf8(data)
        if text is None:
            append_failure(
                failures_path,
                instance_id=inst.instance_id,
                file=rel,
                error_type="BinaryFile",
                bytes=len(data),
            )
            skipped.append(rel)
            continue
        inputs.append(ReviewerInput(file_path=rel, file_content=text))
    return inputs, skipped


def _log_review_failure(
    failures_path: Path,
    *,
    inst: Instance,
    reviewer: Reviewer,
    ri: ReviewerInput,
    result: ReviewResult,
) -> None:
    """Translate reviewer-side meta flags into ``failures.jsonl`` events."""
    meta = result.meta
    reviewer_model = (
        reviewer.resolved_model if isinstance(reviewer, LLMReviewer) else None
    )
    context_window = (
        reviewer.context_window if isinstance(reviewer, LLMReviewer) else None
    )
    limit_tokens = (
        int(reviewer.context_window * reviewer.token_budget_fraction)
        if isinstance(reviewer, LLMReviewer)
        else None
    )

    if meta.skipped_reason == "TokenLimitExceeded":
        append_failure(
            failures_path,
            instance_id=inst.instance_id,
            reviewer=reviewer.name,
            file=ri.file_path,
            error_type="TokenLimitExceeded",
            estimated_tokens=meta.estimated_input_tokens,
            limit_tokens=limit_tokens,
            model=reviewer_model,
            context_window=context_window,
        )
    elif meta.skipped_reason and meta.skipped_reason.startswith("APIError"):
        append_failure(
            failures_path,
            instance_id=inst.instance_id,
            reviewer=reviewer.name,
            file=ri.file_path,
            error_type="APIError",
            detail=meta.skipped_reason,
            model=reviewer_model,
        )
    elif meta.skipped_reason and meta.skipped_reason != "UnsupportedFileType":
        # Don't spam the log with the routine "static reviewer skipping a
        # non-Python file" case; it's expected and documented.
        append_failure(
            failures_path,
            instance_id=inst.instance_id,
            reviewer=reviewer.name,
            file=ri.file_path,
            error_type=meta.skipped_reason,
        )
    if meta.parse_error:
        append_failure(
            failures_path,
            instance_id=inst.instance_id,
            reviewer=reviewer.name,
            file=ri.file_path,
            error_type="ParseError",
            raw_output_path=meta.raw_output_path,
        )


def _build_results_rows(
    *,
    inst: Instance,
    reviewer: Reviewer,
    per_file: list[tuple[ReviewerInput, ReviewResult]],
    score: InstanceScore,
    tolerance: int,
    n_oracle_files: int,
) -> list[dict[str, Any]]:
    """Expand per-file review results into ``results.csv`` rows.

    Two row kinds:
        * One row per emitted ``Comment``.
        * One placeholder row whenever a (reviewer, file) was skipped
          (``TokenLimitExceeded`` etc.) so downstream stats can distinguish
          "no comments" from "didn't run".
    """
    rows: list[dict[str, Any]] = []
    comment_idx = 0
    base: dict[str, Any] = {
        "instance_id": inst.instance_id,
        "repo": inst.repo,
        "base_commit": inst.base_commit,
        "reviewer": reviewer.name,
        "tolerance": tolerance,
        "instance_n_oracle_files": n_oracle_files,
    }
    site_for_idx = score.outcome.comment_to_site if score.outcome else ()

    for ri, result in per_file:
        meta = result.meta
        common = {
            **base,
            "latency_seconds": meta.latency_seconds,
            "input_tokens": meta.input_tokens,
            "output_tokens": meta.output_tokens,
            "estimated_cost_usd": meta.estimated_cost_usd,
            "raw_output_path": meta.raw_output_path or "",
        }

        # Placeholder row for skipped (reviewer, file).
        if meta.skipped_reason and meta.skipped_reason not in (None, "UnsupportedFileType"):
            rows.append(
                {
                    **common,
                    "file": ri.file_path,
                    "line_start": None,
                    "line_end": None,
                    "severity": "",
                    "message": "",
                    "is_hit": False,
                    "matched_oracle_site_id": "",
                    "skipped_reason": meta.skipped_reason,
                }
            )
            continue

        if not result.comments:
            continue

        for c in result.comments:
            site_id = (
                site_for_idx[comment_idx] if comment_idx < len(site_for_idx) else None
            )
            rows.append(
                {
                    **common,
                    "file": c.file,
                    "line_start": c.line_start,
                    "line_end": c.line_end,
                    "severity": c.severity,
                    "message": c.message,
                    "is_hit": site_id is not None,
                    "matched_oracle_site_id": site_id or "",
                    "skipped_reason": "",
                }
            )
            comment_idx += 1
    return rows


def _print_run_summary(
    summaries: list[ReviewerSummary],
    aggregates: dict[str, ReviewerRunAggregate],
    *,
    tolerance: int,
    n_instances: int,
) -> None:
    """Render the final summary table to the console."""
    t = Table(
        show_header=True,
        header_style="bold magenta",
        title=f"Run summary (N={n_instances}, tolerance={tolerance})",
    )
    t.add_column("reviewer")
    t.add_column("hit_rate", justify="right")
    t.add_column("site_recall", justify="right")
    t.add_column("FP/inst (mean)", justify="right")
    t.add_column("FP/inst (med)", justify="right")
    t.add_column("p@1", justify="right")
    t.add_column("p@3", justify="right")
    t.add_column("p@5", justify="right")
    t.add_column("avg latency", justify="right")
    t.add_column("total $", justify="right")
    t.add_column("single", justify="right")
    t.add_column("multi", justify="right")
    for s in summaries:
        agg = aggregates.get(s.reviewer)
        t.add_row(
            s.reviewer,
            f"{s.instance_hit_rate:.2f}",
            f"{s.site_recall:.2f}",
            f"{s.fp_per_instance_mean:.2f}",
            f"{s.fp_per_instance_median:.2f}",
            f"{s.precision_at.get(1, 0.0):.2f}",
            f"{s.precision_at.get(3, 0.0):.2f}",
            f"{s.precision_at.get(5, 0.0):.2f}",
            f"{agg.mean_latency():.2f}s" if agg else "-",
            f"${agg.total_cost():.4f}" if agg else "-",
            f"{s.instance_hit_rate_single_file:.2f}({s.n_instances_single_file})",
            f"{s.instance_hit_rate_multi_file:.2f}({s.n_instances_multi_file})",
        )
    console.print(t)


def _run_full(
    *,
    n: int,
    seed: int,
    dataset: str,
    split: str,
    reviewers_spec: str,
    tolerance: int,
    max_comments_per_file: int,
    output_dir: Path,
    prompt_variant: str = "A",
) -> None:
    """The Milestone D full pipeline.

    Per-instance failures (clone, checkout, file read, token limit,
    parse, API error) are recorded in ``failures.jsonl`` and the run
    continues. A leakage assertion is treated as a hard bug and is NOT
    caught: it aborts the run so we don't silently produce poisoned data.
    """
    wall_start = time.monotonic()

    cfg = load_config()
    if cfg.model_id_override:
        for src, dst in cfg.model_id_override.items():
            console.print(
                f"[bold red]MODEL ID OVERRIDE ACTIVE:[/bold red] {src} -> {dst}"
            )

    output_dir = output_dir if output_dir.is_absolute() else cfg.project_root / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    results_path = output_dir / "results.csv"
    summary_path = output_dir / "summary.csv"
    chart_path = output_dir / "hit_fp_bar_chart.png"
    failures_path = output_dir / "failures.jsonl"
    run_meta_path = output_dir / "run_meta.json"
    # Start with a clean failures log so it always reflects THIS run only.
    failures_path.unlink(missing_ok=True)

    console.rule(f"[bold]Loading {n} instances from {dataset} (seed={seed})")
    instances = load_instances(n=n, seed=seed, dataset=dataset, split=split)
    console.print(f"got {len(instances)} instances")

    reviewers = _build_reviewers(
        reviewers_spec,
        cfg,
        max_comments_per_file=max_comments_per_file,
        prompt_variant=prompt_variant,
    )
    for r in reviewers:
        extra = ""
        if isinstance(r, LLMReviewer):
            extra = (
                f"  resolved={r.resolved_model}  context_window={r.context_window:,}"
            )
        console.print(f"reviewer: {r.name}{extra}")

    all_results_rows: list[dict[str, Any]] = []
    scores_by_reviewer: dict[str, list[InstanceScore]] = {r.name: [] for r in reviewers}
    aggregates: dict[str, ReviewerRunAggregate] = {
        r.name: ReviewerRunAggregate(latencies=[], fresh_costs=[]) for r in reviewers
    }
    n_instances_with_oracle = 0

    progress = Progress(
        TextColumn("[bold]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=False,
    )
    with progress:
        task_id = progress.add_task("instances", total=len(instances))
        for inst in instances:
            progress.update(task_id, description=f"instance {inst.instance_id}")

            # ----- repo cache / checkout -----
            try:
                repo_path = ensure_repo_at_commit(
                    inst.repo,
                    inst.base_commit,
                    repos_cache_dir=cfg.repos_cache_dir,
                )
            except RepoUnavailable as e:
                append_failure(
                    failures_path,
                    instance_id=inst.instance_id,
                    repo=inst.repo,
                    base_commit=inst.base_commit,
                    error_type="RepoUnavailable",
                    error_message=str(e),
                )
                progress.advance(task_id)
                continue

            # ----- oracle -----
            sites = build_oracle_sites(inst.patch, strict_mode=False)
            if not sites:
                append_failure(
                    failures_path,
                    instance_id=inst.instance_id,
                    error_type="NoOracleSites",
                    error_message="Fix patch produced no oracle sites (new files only?)",
                )
                progress.advance(task_id)
                continue
            n_oracle_files = len(oracle_files(sites))

            # ----- reviewer inputs -----
            reviewer_inputs, _skipped = _prepare_reviewer_inputs(
                inst, repo_path, failures_path=failures_path
            )
            if not reviewer_inputs:
                append_failure(
                    failures_path,
                    instance_id=inst.instance_id,
                    error_type="NoReadableFiles",
                )
                progress.advance(task_id)
                continue

            _assert_no_oracle_leak(reviewer_inputs, inst)
            n_instances_with_oracle += 1

            # ----- run each reviewer over each file -----
            for r in reviewers:
                per_file: list[tuple[ReviewerInput, ReviewResult]] = []
                all_comments = []
                for ri in reviewer_inputs:
                    try:
                        result = r.review(ri)
                    except Exception as e:  # noqa: BLE001
                        append_failure(
                            failures_path,
                            instance_id=inst.instance_id,
                            reviewer=r.name,
                            file=ri.file_path,
                            error_type="ReviewerCrash",
                            detail=f"{type(e).__name__}: {e}",
                        )
                        continue
                    aggregates[r.name].latencies.append(result.meta.latency_seconds)
                    if (
                        result.meta.estimated_cost_usd is not None
                        and not result.meta.cache_hit
                    ):
                        aggregates[r.name].fresh_costs.append(
                            result.meta.estimated_cost_usd
                        )
                    _log_review_failure(
                        failures_path, inst=inst, reviewer=r, ri=ri, result=result
                    )
                    per_file.append((ri, result))
                    all_comments.extend(result.comments)

                score = score_instance(
                    instance_id=inst.instance_id,
                    reviewer=r.name,
                    comments=all_comments,
                    sites=sites,
                    tolerance=tolerance,
                )
                scores_by_reviewer[r.name].append(score)
                all_results_rows.extend(
                    _build_results_rows(
                        inst=inst,
                        reviewer=r,
                        per_file=per_file,
                        score=score,
                        tolerance=tolerance,
                        n_oracle_files=n_oracle_files,
                    )
                )
            progress.advance(task_id)

    # ----- aggregate, write artefacts -----
    summaries = [summarise_reviewer(name, scs) for name, scs in scores_by_reviewer.items()]

    console.rule("[bold]Writing artefacts")
    write_results_csv(all_results_rows, results_path)
    console.print(f"  {results_path.relative_to(cfg.project_root)} "
                  f"({len(all_results_rows)} rows)")
    write_summary_csv(summaries, aggregates, summary_path)
    console.print(f"  {summary_path.relative_to(cfg.project_root)}")
    write_hit_fp_chart(
        summaries, chart_path, tolerance=tolerance, n_instances=n_instances_with_oracle
    )
    console.print(f"  {chart_path.relative_to(cfg.project_root)}")

    wall = time.monotonic() - wall_start
    meta = {
        "dataset": dataset,
        "split": split,
        "n_requested": n,
        "n_loaded": len(instances),
        "n_scored": n_instances_with_oracle,
        "seed": seed,
        "tolerance": tolerance,
        "max_comments_per_file": max_comments_per_file,
        "reviewers": [r.name for r in reviewers],
        "resolved_models": {
            r.name: r.resolved_model
            for r in reviewers
            if isinstance(r, LLMReviewer)
        },
        "model_id_override": cfg.model_id_override,
        "prompt_template_id": "v1",
        "strict_oracle_mode": False,
        "litellm_version": _safe_pkg_version("litellm"),
        "wall_seconds": round(wall, 2),
    }
    write_run_meta(run_meta_path, meta)
    console.print(f"  {run_meta_path.relative_to(cfg.project_root)}")
    if failures_path.exists():
        console.print(
            f"  {failures_path.relative_to(cfg.project_root)} "
            f"({failures_path.stat().st_size} bytes)"
        )

    console.rule("[bold]Final summary")
    _print_run_summary(
        summaries, aggregates, tolerance=tolerance, n_instances=n_instances_with_oracle
    )
    console.print(f"wall: {wall:.1f}s")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(
    n: int = typer.Option(20, "--n", help="Number of instances for the full run."),
    seed: int = typer.Option(42, "--seed", help="Sampling seed."),
    dataset: str = typer.Option("princeton-nlp/SWE-bench_Lite", "--dataset"),
    split: str = typer.Option("test", "--split"),
    reviewers: str = typer.Option(
        "claude-sonnet-4-5,gpt-4o-mini,static",
        "--reviewers",
        help="Comma-separated list of reviewer ids.",
    ),
    tolerance: int = typer.Option(3, "--tolerance", min=0),
    max_comments_per_file: int = typer.Option(20, "--max-comments-per-file", min=1),
    output_dir: Path = typer.Option(Path("outputs"), "--output-dir"),
    cache_dir: Path = typer.Option(Path(".cache"), "--cache-dir"),
    prompt_variant: str = typer.Option(
        "A",
        "--prompt-variant",
        help="Round 2 prompt variant: A (Round 1 v1), B (no suppression), "
        "C (force-emit, diagnostic-only).",
    ),
    smoke_test: bool = typer.Option(
        False,
        "--smoke-test",
        help="Run on 1 instance and exit; no CSVs are written.",
    ),
) -> None:
    """SWE-Review-Bench MVP CLI."""
    if smoke_test:
        _run_smoke_test(
            seed=seed,
            dataset=dataset,
            split=split,
            reviewers_spec=reviewers,
            max_comments_per_file=max_comments_per_file,
            tolerance=tolerance,
        )
        return
    _ = cache_dir  # cache directory is fixed by load_config() under PROJECT_ROOT
    _run_full(
        n=n,
        seed=seed,
        dataset=dataset,
        split=split,
        reviewers_spec=reviewers,
        tolerance=tolerance,
        max_comments_per_file=max_comments_per_file,
        output_dir=output_dir,
        prompt_variant=prompt_variant,
    )


def app() -> None:
    """Script entry point used by ``pyproject.toml`` and ``python -m``."""
    typer.run(main)


if __name__ == "__main__":
    app()
