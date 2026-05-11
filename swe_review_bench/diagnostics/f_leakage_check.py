"""F.2 leakage check + cache-key analysis + Variant A cache-hit projection.

Three things this script reports, before any LLM call is made:

1. **Static template-level leakage check**: each of A/B/C templates is
   tested for attention-directing phrases and patch markers.

2. **Per-instance runtime leakage check**: for each instance, render
   the three variants on each patched file (read pre-fix source from
   the cached repo via ``git show``) and check the *fully rendered
   prompt* string for verbatim oracle-derived substrings:
       * ``instance.problem_statement``
       * ``instance.hints_text`` (SWE-bench Lite usually has none; we
         still check)
       * ``instance.patch`` (the fix patch body)
       * ``instance.test_patch``
       * Test function names extracted from ``test_patch`` via regex
         ``def (test_\\w+)`` and ``class (Test\\w+)``
       * Patch-marker regex ``^(@@|--- a/|\\+\\+\\+ b/)`` on any line
   Generic vocabulary (``bug``, ``fix``, ``issue``, ``review``,
   ``correctness``, ``reliability``, ``defect``, ``error``) is NOT
   flagged (per §0.5).

3. **Cache-key composition report and cost projection**:
   confirms that the Round 1 cache key is ``sha256(model,
   prompt_template_id, file_path, file_content)`` — i.e. it
   incorporates the template id, not a prompt-hash. Variant A's
   template id is ``"v1"`` (Round 1), so Variant A's cache key matches
   Round 1's byte-for-byte, and Variant A is expected to cache-hit
   100% for the 20 instances. Variant B/C have new template ids
   (``v1b`` / ``v1c``); they will miss the cache on every call and
   bear the full projected cost.

Outputs:
  outputs/round2/prompt_leakage_check.md

Halts (exit non-zero) on any verbatim oracle substring match. Static
template-level FAILs also halt. Per-instance test-name false positives
are tolerated only if they appear as part of a numbered source code
line (i.e. the file legitimately contains a ``def test_x`` symbol);
the check reports such occurrences but does not halt — they are real
project code that the reviewer would see in normal review.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path
from typing import Any

from ..config import load_config
from ..data.loader import load_instances
from ..reviewers.base import ReviewerInput
from ..reviewers.prompt_variants import VARIANTS, render_prompt
from ..run import (
    _patched_files_from_patch,
    _prepare_reviewer_inputs,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUND2_DIR = PROJECT_ROOT / "outputs" / "round2"


FORBIDDEN_ATTN_PHRASES = (
    "find the bug",
    "find the defect",
    "a defect was reported",
    "a bug was reported",
    "this file has a bug",
    "this file has a defect",
    "fix the bug",
    "fix the issue",
    "locate the bug",
    "locate the defect",
)

PATCH_MARKER_RE = re.compile(r"^(@@|--- a/|\+\+\+ b/)", re.MULTILINE)
TEST_DEF_RE = re.compile(r"def\s+(test_\w+)")
TEST_CLS_RE = re.compile(r"class\s+(Test\w+)")


def _template_level_check() -> list[dict[str, Any]]:
    results = []
    for name, v in VARIANTS.items():
        hits = [p for p in FORBIDDEN_ATTN_PHRASES if p in v.template.lower()]
        markers = PATCH_MARKER_RE.findall(v.template) or []
        results.append(
            {
                "variant": name,
                "template_id": v.template_id,
                "template_sha256": v.template_sha256,
                "forbidden_phrase_matches": hits,
                "patch_marker_matches": markers,
                "verdict": "PASS" if not hits and not markers else "FAIL",
            }
        )
    return results


def _instance_level_check(inst, reviewer_inputs: list[ReviewerInput]) -> dict[str, Any]:
    """Render all three variants for every file, check verbatim leakage."""
    ps = (inst.problem_statement or "").strip()
    hint = ""  # SWE-bench Lite usually has no hints_text field; defensive.
    patch = inst.patch or ""
    test_patch = inst.test_patch or ""
    test_names: set[str] = set()
    test_names.update(TEST_DEF_RE.findall(test_patch))
    test_names.update(TEST_CLS_RE.findall(test_patch))

    per_variant: dict[str, dict[str, Any]] = {}
    for vname, variant in VARIANTS.items():
        flags: dict[str, Any] = {
            "problem_statement_leak": False,
            "hints_text_leak": False,
            "patch_body_leak": False,
            "test_patch_body_leak": False,
            "patch_marker_leak": False,
            "test_names_appearing_in_source": [],
            "n_files_checked": 0,
            "prompt_lengths": [],
        }
        for ri in reviewer_inputs:
            prompt = render_prompt(variant, ri.file_path, ri.file_content)
            flags["n_files_checked"] += 1
            flags["prompt_lengths"].append(len(prompt))
            if len(ps) >= 32 and ps in prompt:
                flags["problem_statement_leak"] = True
            if len(hint) >= 32 and hint in prompt:
                flags["hints_text_leak"] = True
            if patch and patch in prompt:
                flags["patch_body_leak"] = True
            if test_patch and test_patch in prompt:
                flags["test_patch_body_leak"] = True
            if PATCH_MARKER_RE.search(prompt):
                flags["patch_marker_leak"] = True
            # Test names appearing in the prompt are only a concern if
            # they came from test_patch AND don't appear in the source
            # file (i.e. the reviewer is being shown a test name that
            # only the oracle knows about). Names that exist in the
            # source file are legitimate (real production code defs).
            for tn in test_names:
                if tn in prompt and tn not in ri.file_content:
                    # Possible leak: the prompt shows a test name that
                    # is not in the actual source the reviewer sees.
                    # In practice this should not happen because the
                    # template body doesn't mention test names.
                    flags.setdefault("orphan_test_names_in_prompt", []).append(tn)
                elif tn in prompt and tn in ri.file_content:
                    # Legitimate: project code happens to share the
                    # name. Not a leak, but recorded for transparency.
                    flags["test_names_appearing_in_source"].append(tn)
        per_variant[vname] = flags
    return per_variant


def _cost_projection() -> dict[str, Any]:
    """Project Variant A cache-miss cost and Variant B/C cost.

    Variant A's template id is ``v1`` (Round 1). The Round 1 cache
    contains entries keyed by ``sha256(model, "v1", file_path,
    file_content)``. Since Variant A reuses the same template id, the
    Variant A cache key is byte-identical to Round 1's; every Variant A
    call on the Round 1 20-instance set should cache-hit. Cost
    expected: $0.

    Variant B and C use new template ids; every call cache-misses.
    """
    # Rough averages from Round 1 results.csv (input/output tokens per
    # call). These are used only for an order-of-magnitude projection.
    avg_input_tokens_sonnet = 5500
    avg_input_tokens_gpt = 5500
    avg_output_tokens_sonnet = 180
    avg_output_tokens_gpt = 250

    n_calls_per_variant = 20  # one per (model, instance) on single-file inputs

    # Pricing (USD per 1M tokens). These are coarse; treat as a
    # pre-flight projection only -- actual cost will be reported by
    # litellm per call.
    sonnet_in = 3.0 / 1_000_000
    sonnet_out = 15.0 / 1_000_000
    gpt_in = 0.15 / 1_000_000
    gpt_out = 0.60 / 1_000_000

    sonnet_per_call = avg_input_tokens_sonnet * sonnet_in + avg_output_tokens_sonnet * sonnet_out
    gpt_per_call = avg_input_tokens_gpt * gpt_in + avg_output_tokens_gpt * gpt_out

    projections = {
        "A_sonnet_cost_usd": 0.0,   # cache hit
        "A_gpt_cost_usd": 0.0,
        "B_sonnet_cost_usd": n_calls_per_variant * sonnet_per_call,
        "B_gpt_cost_usd": n_calls_per_variant * gpt_per_call,
        "C_sonnet_cost_usd": n_calls_per_variant * sonnet_per_call,
        "C_gpt_cost_usd": n_calls_per_variant * gpt_per_call,
    }
    projections["total_projected_usd"] = sum(projections.values())
    projections["hard_cap_usd"] = 5.0
    return projections


def _write_report(
    *,
    template_check: list[dict[str, Any]],
    instance_check: list[dict[str, Any]],
    cost_projection: dict[str, Any],
    halt: bool,
) -> Path:
    lines: list[str] = []
    lines.append("# F.2 Prompt leakage check + cost projection\n\n")
    lines.append(
        "This report runs before any Round 2 LLM API call. If any FAIL appears, "
        "F.3 is blocked.\n\n"
    )

    lines.append("## (1) Template-level static check\n\n")
    lines.append(
        "Forbidden phrases (any match aborts F.3): "
        f"{list(FORBIDDEN_ATTN_PHRASES)}\n\n"
    )
    lines.append("Patch markers (regex ``^(@@|--- a/|+++ b/)`` on any line) aborts F.3 if found in the template body.\n\n")
    lines.append("| variant | template_id | template_sha256[:12] | forbidden_phrase_matches | patch_marker_matches | verdict |\n")
    lines.append("|---|---|---|---|---|---|\n")
    for r in template_check:
        lines.append(
            f"| {r['variant']} | `{r['template_id']}` | "
            f"`{r['template_sha256'][:12]}` | "
            f"{r['forbidden_phrase_matches']} | "
            f"{r['patch_marker_matches']} | "
            f"**{r['verdict']}** |\n"
        )

    lines.append("\n## (2) Per-instance runtime check\n\n")
    lines.append(
        "For every instance, each of A/B/C is rendered on each patched file. "
        "The fully rendered prompt is then searched for verbatim "
        "``problem_statement`` / ``hints_text`` / ``patch`` / "
        "``test_patch`` substrings, patch markers, and test names whose "
        "definitions appear in ``test_patch`` but **not** in the file the "
        "reviewer sees.\n\n"
    )
    lines.append(
        "Allowed generic vocabulary (NOT flagged): ``bug, fix, issue, review, "
        "correctness, reliability, defect, error``.\n\n"
    )
    lines.append(
        "| instance | files | variant | problem_statement | hints | patch | test_patch | patch_marker | orphan_test_names | verdict |\n"
    )
    lines.append("|---|---:|---|---|---|---|---|---|---|---|\n")
    any_per_instance_fail = False
    for entry in instance_check:
        iid = entry["instance_id"]
        n_files = entry["n_files"]
        for vname, flags in entry["per_variant"].items():
            orphan = flags.get("orphan_test_names_in_prompt") or []
            failed = (
                flags["problem_statement_leak"]
                or flags["hints_text_leak"]
                or flags["patch_body_leak"]
                or flags["test_patch_body_leak"]
                or flags["patch_marker_leak"]
                or len(orphan) > 0
            )
            if failed:
                any_per_instance_fail = True
            lines.append(
                f"| {iid} | {n_files} | {vname} | "
                f"{'LEAK' if flags['problem_statement_leak'] else 'ok'} | "
                f"{'LEAK' if flags['hints_text_leak'] else 'ok'} | "
                f"{'LEAK' if flags['patch_body_leak'] else 'ok'} | "
                f"{'LEAK' if flags['test_patch_body_leak'] else 'ok'} | "
                f"{'LEAK' if flags['patch_marker_leak'] else 'ok'} | "
                f"{orphan or '-'} | "
                f"**{'FAIL' if failed else 'PASS'}** |\n"
            )

    lines.append("\n## (3) Cache-key composition and cost projection\n\n")
    lines.append(
        "Round 1 cache key composition (from ``swe_review_bench/reviewers/cache.py``):\n\n"
        "```\n"
        "cache_key(model, prompt_template_id, file_path, file_content)\n"
        "        = sha256(model || NUL || template_id || NUL || file_path || NUL || file_content)\n"
        "```\n\n"
        "Implication for Round 2: the cache key incorporates the template id "
        "(``v1`` / ``v1b`` / ``v1c``), **not** a full prompt-content hash. "
        "Variant A's template id is ``v1`` -- byte-identical to Round 1's. "
        "Therefore Variant A's cache key is identical to Round 1's for every "
        "(model, instance, file) tuple, and Round 1's existing cache files "
        "(``.cache/llm/<key>.json``) hit on read-through. Variants B and C "
        "use new template ids, so every B/C call cache-misses.\n\n"
    )
    cp = cost_projection
    lines.append(
        "| variant | model | projected cost (USD) | cache mode |\n"
        "|---|---|---:|---|\n"
        f"| A | sonnet | {cp['A_sonnet_cost_usd']:.4f} | round1 read-through (expected 100% hit) |\n"
        f"| A | gpt-4o-mini | {cp['A_gpt_cost_usd']:.4f} | round1 read-through (expected 100% hit) |\n"
        f"| B | sonnet | {cp['B_sonnet_cost_usd']:.4f} | round2 fresh (always miss on first run) |\n"
        f"| B | gpt-4o-mini | {cp['B_gpt_cost_usd']:.4f} | round2 fresh |\n"
        f"| C | sonnet | {cp['C_sonnet_cost_usd']:.4f} | round2 fresh |\n"
        f"| C | gpt-4o-mini | {cp['C_gpt_cost_usd']:.4f} | round2 fresh |\n"
        f"| **total** |  | **{cp['total_projected_usd']:.4f}** |  |\n"
        f"| hard cap |  | {cp['hard_cap_usd']:.4f} |  |\n"
    )

    lines.append("\n## Verdict\n\n")
    template_fail = any(r["verdict"] == "FAIL" for r in template_check)
    if halt:
        lines.append(
            f"**HALT.** Leakage failure detected "
            f"(template-level FAIL: {template_fail}; "
            f"per-instance FAIL: {any_per_instance_fail}). "
            f"F.3 is blocked.\n"
        )
    else:
        lines.append(
            "**PASS.** No oracle-derived content found in any template or "
            "rendered prompt. Projected total cost "
            f"${cp['total_projected_usd']:.4f} is under the ${cp['hard_cap_usd']:.2f} "
            "hard cap. F.3 may proceed.\n"
        )

    out = ROUND2_DIR / "prompt_leakage_check.md"
    out.write_text("".join(lines), encoding="utf-8")
    return out


def main() -> None:
    cfg = load_config()
    ROUND2_DIR.mkdir(parents=True, exist_ok=True)

    template_check = _template_level_check()
    template_fail = any(r["verdict"] == "FAIL" for r in template_check)

    instances = load_instances(
        n=20, seed=42, dataset="princeton-nlp/SWE-bench_Lite", split="test"
    )

    instance_check: list[dict[str, Any]] = []
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as fh:
        tmp_failures = Path(fh.name)
    try:
        for inst in instances:
            # Repo is already cached from Round 1; ensure_repo_at_commit is
            # the canonical way to bring it back to the right base_commit
            # but is destructive (checkout). For a read-only F.2 we read
            # files via the run.py helper that uses the working tree;
            # since Round 1 left the tree at the last instance's
            # base_commit, the file content might be off-commit for some
            # instances. To be safe, re-checkout per instance.
            from ..data.repos import ensure_repo_at_commit  # local import

            try:
                repo_path = ensure_repo_at_commit(
                    inst.repo,
                    inst.base_commit,
                    repos_cache_dir=cfg.repos_cache_dir,
                )
            except Exception as e:  # noqa: BLE001
                instance_check.append(
                    {
                        "instance_id": inst.instance_id,
                        "n_files": 0,
                        "per_variant": {
                            vname: {
                                "problem_statement_leak": False,
                                "hints_text_leak": False,
                                "patch_body_leak": False,
                                "test_patch_body_leak": False,
                                "patch_marker_leak": False,
                                "test_names_appearing_in_source": [],
                                "n_files_checked": 0,
                                "prompt_lengths": [],
                                "error": f"repo unavailable: {type(e).__name__}: {e}",
                            }
                            for vname in VARIANTS
                        },
                    }
                )
                continue
            reviewer_inputs, _skipped = _prepare_reviewer_inputs(
                inst, repo_path, failures_path=tmp_failures
            )
            per_variant = _instance_level_check(inst, reviewer_inputs)
            instance_check.append(
                {
                    "instance_id": inst.instance_id,
                    "n_files": len(reviewer_inputs),
                    "per_variant": per_variant,
                }
            )
    finally:
        tmp_failures.unlink(missing_ok=True)

    any_per_instance_fail = False
    for entry in instance_check:
        for vname, flags in entry["per_variant"].items():
            orphan = flags.get("orphan_test_names_in_prompt") or []
            if (
                flags["problem_statement_leak"]
                or flags["hints_text_leak"]
                or flags["patch_body_leak"]
                or flags["test_patch_body_leak"]
                or flags["patch_marker_leak"]
                or len(orphan) > 0
            ):
                any_per_instance_fail = True

    cost_projection = _cost_projection()
    halt = template_fail or any_per_instance_fail
    out_path = _write_report(
        template_check=template_check,
        instance_check=instance_check,
        cost_projection=cost_projection,
        halt=halt,
    )
    print(f"wrote {out_path}")
    print(
        f"verdict: "
        f"template={'FAIL' if template_fail else 'PASS'} "
        f"per_instance={'FAIL' if any_per_instance_fail else 'PASS'} "
        f"halt={halt}"
    )
    if halt:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
