"""Acceptance tests for the n=100 analysis modules.

These run on the frozen n=20 Round 2 artefacts, so they need no API calls
and no n=100 run to be present.
"""

from __future__ import annotations

import csv
from pathlib import Path

from swe_review_bench.diagnostics.paired_comparison import mcnemar_exact_p
from swe_review_bench.diagnostics.tolerance_sweep import sweep


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_mcnemar_exact_known_values() -> None:
    # All nine discordant pairs favour one side: 2 * P(X <= 0) = 2 / 2^9.
    assert abs(mcnemar_exact_p(9, 0) - 2 / 512) < 1e-12
    # The statistic is symmetric in (b, c).
    assert abs(mcnemar_exact_p(0, 9) - 2 / 512) < 1e-12
    # No discordant pairs: nothing to test, p = 1.
    assert mcnemar_exact_p(0, 0) == 1.0
    # Evenly split discordant pairs: doubled tail caps at 1.
    assert mcnemar_exact_p(5, 5) == 1.0


def test_tolerance_sweep_reproduces_headline(tmp_path) -> None:
    rows = sweep(
        PROJECT_ROOT / "outputs" / "round2" / "variant_results.csv",
        PROJECT_ROOT / "outputs" / "round2" / "oracle_index.json",
        tmp_path,
        tolerances=(3,),
    )
    got = {(r["reviewer"], r["prompt_variant"]): r["instance_hit_rate"] for r in rows}

    expected: dict[tuple[str, str], float] = {}
    summary = PROJECT_ROOT / "outputs" / "round2" / "variant_summary.csv"
    with summary.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            expected[(row["reviewer"], row["prompt_variant"])] = float(
                row["instance_hit_rate"]
            )

    assert got, "sweep produced no rows"
    for key, exp in expected.items():
        assert key in got, f"missing {key} in sweep output"
        assert abs(got[key] - exp) < 1e-9, (
            f"{key}: sweep {got[key]} != headline {exp}"
        )
