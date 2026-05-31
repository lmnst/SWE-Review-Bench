"""Per-instance × per-variant oracle-leakage assertions.

For every SWE-bench Lite instance in the 100-instance sample and every
Round 2 prompt variant (A, B, C), this test renders the prompt the
reviewer would actually see and asserts that no oracle-derived content
appears in it.

Checks (per H.3 leakage spec):

1. ``problem_statement`` verbatim substring (whitespace-trimmed, >=32 chars)
2. ``hints_text`` verbatim substring (>=32 chars; SWE-bench Lite has no
   such field, but the assertion is kept for parity with future variants)
3. Patch markers via multiline regex ``^(@@|--- a/|\\+\\+\\+ b/)``
4. ``test_patch`` verbatim substring (>=32 chars)
5. Test function/class names extracted from ``test_patch`` via
   ``def (test_\\w+)`` / ``class (Test\\w+)``. Allowed if the same name
   also appears in the reviewer-visible source file (legitimate project
   code).
6. Oracle line numbers (each oracle hunk's range expanded by ±2) must
   not appear as bare integers in the prompt -- excluding occurrences
   that are themselves part of the source-line-number rendering
   (``^\\s*\\d+\\s*[:|]\\s`` or ``^\\s*\\d+\\t``) and excluding the
   known-boilerplate substring ``"1-indexed"`` which contains a ``1``
   token by design.

Generic vocabulary (``bug``, ``fix``, ``issue``, ``review``,
``correctness``, ``reliability``, ``defect``, ``error``, ``failure``,
``test``) is **NOT** asserted against -- banning it would distort
ordinary code-review language.

This test runs the same expensive ``ensure_repo_at_commit`` step once
per instance via a session-scoped fixture, so the wall time is
dominated by git checkouts (the first run also clones the repos new to
the n=100 sample) rather than the per-cell assertions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest

from swe_review_bench.config import load_config
from swe_review_bench.data.loader import load_instances
from swe_review_bench.data.repos import RepoUnavailable, ensure_repo_at_commit
from swe_review_bench.reviewers.prompt_variants import VARIANTS, render_prompt
from swe_review_bench.run import _prepare_reviewer_inputs


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 100 instance IDs sampled with seed=42 from princeton-nlp/SWE-bench_Lite.
# Hard-coded so test collection stays robust even without dataset access;
# test_instance_ids_match_sample asserts this list equals
# load_instances(n=100, seed=42), guarding against drift.
INSTANCE_IDS: tuple[str, ...] = (
    "astropy__astropy-14995",
    "django__django-11001",
    "django__django-11049",
    "django__django-11099",
    "django__django-11133",
    "django__django-11179",
    "django__django-11283",
    "django__django-11422",
    "django__django-11564",
    "django__django-11583",
    "django__django-11630",
    "django__django-11797",
    "django__django-11905",
    "django__django-12708",
    "django__django-12747",
    "django__django-12908",
    "django__django-12915",
    "django__django-13033",
    "django__django-13220",
    "django__django-13315",
    "django__django-13321",
    "django__django-13448",
    "django__django-13551",
    "django__django-13590",
    "django__django-13658",
    "django__django-13757",
    "django__django-13768",
    "django__django-14017",
    "django__django-14155",
    "django__django-14382",
    "django__django-14580",
    "django__django-14752",
    "django__django-14787",
    "django__django-14855",
    "django__django-14997",
    "django__django-15347",
    "django__django-15498",
    "django__django-15695",
    "django__django-15789",
    "django__django-15851",
    "django__django-15902",
    "django__django-16400",
    "django__django-16408",
    "django__django-16527",
    "django__django-16816",
    "django__django-16873",
    "django__django-17051",
    "django__django-17087",
    "matplotlib__matplotlib-23476",
    "matplotlib__matplotlib-25079",
    "matplotlib__matplotlib-25311",
    "matplotlib__matplotlib-25498",
    "matplotlib__matplotlib-26020",
    "pallets__flask-4045",
    "psf__requests-1963",
    "psf__requests-863",
    "pylint-dev__pylint-6506",
    "pylint-dev__pylint-7080",
    "pylint-dev__pylint-7228",
    "pytest-dev__pytest-5103",
    "pytest-dev__pytest-5227",
    "pytest-dev__pytest-5413",
    "pytest-dev__pytest-5692",
    "pytest-dev__pytest-6116",
    "pytest-dev__pytest-7168",
    "pytest-dev__pytest-7432",
    "pytest-dev__pytest-7490",
    "pytest-dev__pytest-9359",
    "scikit-learn__scikit-learn-10508",
    "scikit-learn__scikit-learn-10949",
    "scikit-learn__scikit-learn-13496",
    "scikit-learn__scikit-learn-13497",
    "scikit-learn__scikit-learn-13779",
    "scikit-learn__scikit-learn-14087",
    "scikit-learn__scikit-learn-14092",
    "sphinx-doc__sphinx-8273",
    "sphinx-doc__sphinx-8282",
    "sphinx-doc__sphinx-8474",
    "sphinx-doc__sphinx-8595",
    "sphinx-doc__sphinx-8721",
    "sympy__sympy-12454",
    "sympy__sympy-13177",
    "sympy__sympy-13437",
    "sympy__sympy-13480",
    "sympy__sympy-13895",
    "sympy__sympy-14817",
    "sympy__sympy-16792",
    "sympy__sympy-17655",
    "sympy__sympy-18087",
    "sympy__sympy-19007",
    "sympy__sympy-19254",
    "sympy__sympy-20212",
    "sympy__sympy-20322",
    "sympy__sympy-20442",
    "sympy__sympy-21627",
    "sympy__sympy-22005",
    "sympy__sympy-22714",
    "sympy__sympy-23117",
    "sympy__sympy-23191",
    "sympy__sympy-23262",
)


PATCH_MARKER_RE = re.compile(r"^(@@|--- a/|\+\+\+ b/)", re.MULTILINE)
TEST_DEF_RE = re.compile(r"def\s+(test_\w+)")
TEST_CLS_RE = re.compile(r"class\s+(Test\w+)")
SOURCE_NUMBERED_LINE_RE = re.compile(r"^\s*\d+\s*[:|]\s|^\s*\d+\t")

# Known boilerplate substrings that contain digit tokens by design.
# The Round 1/2 prompt template body contains "1-indexed" in the JSON
# schema description; without this exclusion, the ±2 expansion of an
# oracle line of 1 / 2 / 3 would falsely match.
BOILERPLATE_DIGIT_EXCLUSIONS: tuple[str, ...] = ("1-indexed",)


# ---------------------------------------------------------------------------
# Fixtures (session-scoped so the 20 git checkouts happen once per pytest run)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def _cfg():
    return load_config()


@pytest.fixture(scope="session")
def _oracle_index() -> dict[str, Any]:
    p = PROJECT_ROOT / "outputs" / "n100" / "oracle_index.json"
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def _prepared(_cfg, tmp_path_factory) -> dict[str, tuple]:
    """Map ``instance_id -> (Instance, reviewer_inputs, error)``."""
    out: dict[str, tuple] = {}
    instances = load_instances(
        n=100, seed=42, dataset="princeton-nlp/SWE-bench_Lite", split="test"
    )
    failures_tmp = tmp_path_factory.mktemp("failures") / "failures.jsonl"
    for inst in instances:
        try:
            repo_path = ensure_repo_at_commit(
                inst.repo,
                inst.base_commit,
                repos_cache_dir=_cfg.repos_cache_dir,
            )
        except RepoUnavailable as e:
            out[inst.instance_id] = (inst, None, f"{type(e).__name__}: {e}")
            continue
        ris, _ = _prepare_reviewer_inputs(
            inst, repo_path, failures_path=failures_tmp
        )
        out[inst.instance_id] = (inst, ris, None)
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _strip_source_numbered_lines(prompt: str) -> str:
    """Drop lines that match the source-numbering prefix entirely."""
    return "\n".join(
        line
        for line in prompt.split("\n")
        if not SOURCE_NUMBERED_LINE_RE.match(line)
    )


def _mask_boilerplate(text: str) -> str:
    """Remove known-boilerplate substrings that would falsely match the
    line-number leak check via incidental digit tokens."""
    for needle in BOILERPLATE_DIGIT_EXCLUSIONS:
        text = text.replace(needle, "[GUARDED]")
    return text


def _oracle_lines_for(oracle_index: dict, instance_id: str) -> set[int]:
    """All oracle hunk line numbers ±2, positive integers only."""
    inst = oracle_index["instances"].get(instance_id) or {}
    lines: set[int] = set()
    for site in inst.get("sites", []):
        start = int(site["line_start"])
        end = int(site["line_end"])
        for L in range(start - 2, end + 3):
            if L > 0:
                lines.add(L)
    return lines


# ---------------------------------------------------------------------------
# Tests (100 instances x 3 variants = 300 parametrised cells)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("variant_name", sorted(VARIANTS.keys()))
@pytest.mark.parametrize("instance_id", INSTANCE_IDS)
def test_no_oracle_leakage(
    _prepared, _oracle_index, instance_id: str, variant_name: str
) -> None:
    inst, reviewer_inputs, err = _prepared[instance_id]
    if err is not None:
        pytest.skip(f"repo unavailable for {instance_id}: {err}")
    if not reviewer_inputs:
        pytest.skip(f"no reviewer inputs for {instance_id}")

    variant = VARIANTS[variant_name]

    problem_statement = (inst.problem_statement or "").strip()
    # SWE-bench Lite's Instance dataclass does not carry hints_text;
    # treated as empty for parity with future variants.
    hints_text = ""
    test_patch = inst.test_patch or ""
    test_names: set[str] = set()
    test_names.update(TEST_DEF_RE.findall(test_patch))
    test_names.update(TEST_CLS_RE.findall(test_patch))
    oracle_lines = _oracle_lines_for(_oracle_index, instance_id)

    for ri in reviewer_inputs:
        prompt = render_prompt(variant, ri.file_path, ri.file_content)
        ctx = f"{instance_id}/{variant_name}/{ri.file_path}"

        # 1. problem_statement
        if len(problem_statement) >= 32:
            assert problem_statement not in prompt, (
                f"problem_statement leak in {ctx}"
            )

        # 2. hints_text
        if len(hints_text) >= 32:
            assert hints_text not in prompt, f"hints_text leak in {ctx}"

        # 3. patch markers
        assert PATCH_MARKER_RE.search(prompt) is None, (
            f"patch-marker line found in prompt for {ctx}"
        )

        # 4. test_patch body
        if len(test_patch) >= 32:
            assert test_patch not in prompt, f"test_patch leak in {ctx}"

        # 5. test names from test_patch (allowed only if also in source)
        for tn in test_names:
            if tn in prompt and tn not in ri.file_content:
                pytest.fail(
                    f"orphan test name {tn!r} appears in prompt for {ctx} "
                    f"but not in the reviewer-visible source -- oracle leak"
                )

        # 6. oracle line numbers ±2
        stripped = _strip_source_numbered_lines(prompt)
        masked = _mask_boilerplate(stripped)
        for L in oracle_lines:
            assert re.search(rf"\b{L}\b", masked) is None, (
                f"oracle line {L} (±2 expansion of an oracle hunk) appears "
                f"as a bare integer in the prompt for {ctx} after "
                f"stripping source-numbering prefixes and known boilerplate"
            )


def test_instance_ids_match_sample() -> None:
    """Guard against drift: the hard-coded ids must equal the live sample."""
    sampled = tuple(
        i.instance_id
        for i in load_instances(
            n=100, seed=42, dataset="princeton-nlp/SWE-bench_Lite", split="test"
        )
    )
    assert len(INSTANCE_IDS) == 100
    assert sampled == INSTANCE_IDS
