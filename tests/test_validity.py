"""Tests for the validity-diagnostics analyses (zero API, offline).

Unit tests pin the hand-rolled statistics against textbook values;
integration tests cross-check the two analyses against numbers already
recorded in the frozen n=100 artifacts (``paired_comparison.csv`` and
``oracle_validity_report.md``), so a regression in the new code shows up
as a mismatch with an independently produced figure.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from swe_review_bench.validity.stats import (
    fisher_exact_two_sided,
    odds_ratio_ci,
)
from swe_review_bench.validity import hit_overlap, no_enrichment

PROJECT_ROOT = Path(__file__).resolve().parents[1]
N100_DIR = PROJECT_ROOT / "outputs" / "n100"
RESULTS_CSV = N100_DIR / "variant_results.csv"
ORACLE_INDEX = N100_DIR / "oracle_index.json"
TEMPLATE_CSV = N100_DIR / "oracle_validity_template.csv"


# --------------------------------------------------------------------------
# Unit: Fisher exact
# --------------------------------------------------------------------------


def test_fisher_tea_tasting():
    # The 2x2 [[3,1],[1,3]] "lady tasting tea" table: exact two-sided
    # p = 34/70 by hand (tables with a in {0,1,3,4} are <= the observed
    # probability; a=2 is the single more-central, higher-probability
    # table and is excluded).
    assert fisher_exact_two_sided(3, 1, 1, 3) == pytest.approx(34 / 70, abs=1e-12)


def test_fisher_strong_association():
    # scipy.stats.fisher_exact([[8,2],[1,5]], 'two-sided') == 0.03496...
    assert fisher_exact_two_sided(8, 2, 1, 5) == pytest.approx(0.034965, abs=1e-5)


def test_fisher_degenerate_table_returns_one():
    # An empty column (no hits anywhere) carries no association signal.
    assert fisher_exact_two_sided(0, 20, 0, 10) == 1.0


# --------------------------------------------------------------------------
# Unit: odds ratio + CI
# --------------------------------------------------------------------------


def test_odds_ratio_no_zero_cell():
    r = odds_ratio_ci(3, 1, 1, 3)
    assert r["haldane_applied"] is False
    assert r["odds_ratio"] == pytest.approx(9.0)
    assert r["ci_low"] == pytest.approx(0.3666, abs=1e-3)
    assert r["ci_high"] == pytest.approx(220.9, rel=1e-3)


def test_odds_ratio_zero_cell_triggers_haldane():
    r = odds_ratio_ci(2, 18, 0, 10)
    assert r["haldane_applied"] is True
    # (2.5*10.5)/(18.5*0.5) = 2.8378...
    assert r["odds_ratio"] == pytest.approx(2.8378, abs=1e-3)
    assert r["ci_low"] > 0.0


# --------------------------------------------------------------------------
# Integration: bug-site flags match the audit report
# --------------------------------------------------------------------------


def test_bug_site_flags_match_report():
    flags = no_enrichment.load_bug_site_flags(TEMPLATE_CSV)
    assert len(flags) == 30  # 30 audited instances
    assert sum(flags.values()) == 20  # 20/30 carry >=1 bug site (report)


# --------------------------------------------------------------------------
# Integration: hit-overlap cross-checks paired_comparison.csv
# --------------------------------------------------------------------------


def test_hit_overlap_matches_paired_comparison():
    from swe_review_bench.diagnostics.paired_comparison import load_hits
    import json

    hits = load_hits(RESULTS_CSV)
    universe = set(json.loads(ORACLE_INDEX.read_text(encoding="utf-8"))["instances"].keys())
    rows = hit_overlap.overlap_rows(hits, universe)
    by_pair = {(r["cell_x"], r["cell_y"]): r for r in rows}

    # Reviewer contrast under variant A: paired_comparison.csv records
    # both_hit=1, x_only=11 (Claude-only), y_only=6 (GPT-only).
    r = by_pair[("claude-sonnet-4-5/A", "gpt-4o-mini/A")]
    assert (r["both_hit"], r["x_only"], r["y_only"]) == (1, 11, 6)
    assert r["jaccard"] == pytest.approx(1 / 18)
    assert r["n"] == 100


# --------------------------------------------------------------------------
# Integration: no-enrichment cross-checks the audited-subset rates
# --------------------------------------------------------------------------


def test_no_enrichment_subset_rates_match_report():
    rows = no_enrichment.run(RESULTS_CSV, TEMPLATE_CSV, PROJECT_ROOT / "outputs" / "validity_study")
    by_group = {r["group"]: r for r in rows}
    # Report "Audited-subset sensitivity": claude-A 2/20, gpt-B 6/20.
    assert (by_group["claude-sonnet-4-5/A"]["hit_bug"], by_group["claude-sonnet-4-5/A"]["n_bug"]) == (2, 20)
    assert (by_group["gpt-4o-mini/B"]["hit_bug"], by_group["gpt-4o-mini/B"]["n_bug"]) == (6, 20)
    # Every per-cell table sums to the 30 audited instances.
    for g, r in by_group.items():
        assert r["n_audited"] == 30
