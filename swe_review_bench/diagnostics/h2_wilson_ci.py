"""H-lite Task 2 — Wilson 95% CI augmentation.

Re-emits Round 1 and Round 2 summary tables with explicit numerator,
denominator, and Wilson 95% CI bounds for every rate metric.

Round 1 source:
  - ``outputs/summary.csv`` (rates per reviewer)
  - ``outputs/round2/file_level_metrics.csv`` (file_level + line_level
    numerators per reviewer; produced read-only during Milestone E.4)
  - ``outputs/round2/oracle_index.json`` (oracle-site total used as the
    site_recall denominator)

Round 2 source:
  - ``outputs/round2/variant_summary.csv`` (rates + existing CIs per
    (reviewer, prompt_variant); produced during F.3)

Original CSVs are read-only; new CSVs go under
``outputs/round2/h_lite/`` only. No API calls.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUND2_DIR = PROJECT_ROOT / "outputs" / "round2"
H_LITE_DIR = ROUND2_DIR / "h_lite"

# Two-sided 95% normal quantile, no continuity correction.
Z_95 = 1.959963984540054


def wilson_ci(k: int, n: int, *, z: float = Z_95) -> tuple[float, float]:
    """Two-sided Wilson 95% interval (no continuity correction).

    Defined for n >= 0. Returns (0.0, 0.0) for n == 0; this is a
    diagnostic-only fallback so the table can be rendered even when a
    metric's denominator is undefined.
    """
    if n <= 0:
        return 0.0, 0.0
    if k < 0 or k > n:
        raise ValueError(f"invalid (k={k}, n={n}); require 0 <= k <= n")
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def _round_num(rate: float, n: int) -> int:
    """Recover an integer numerator from a stored rate.

    SWE-Review-Bench summary CSVs store rates as quotients of small
    integers (k <= 20, n in {20, 32}), so rounding is unambiguous: the
    true integer satisfies abs(k_true - rate * n) < 1e-6 in every
    cell. The assertion below guards against silent drift.
    """
    raw = rate * n
    k = int(round(raw))
    assert abs(raw - k) < 1e-6, (
        f"rate {rate} times denom {n} = {raw} does not round to an "
        f"integer within tolerance; CSV stored rate is unexpectedly "
        f"non-quotient"
    )
    return k


# ---------------------------------------------------------------------------
# Round 1
# ---------------------------------------------------------------------------


def round1_with_ci() -> list[dict[str, Any]]:
    summary = pd.read_csv(PROJECT_ROOT / "outputs" / "summary.csv")
    file_lv = pd.read_csv(ROUND2_DIR / "file_level_metrics.csv")
    oracle = json.loads((ROUND2_DIR / "oracle_index.json").read_text(encoding="utf-8"))
    sites_total = sum(int(inst["n_sites"]) for inst in oracle["instances"].values())

    rows: list[dict[str, Any]] = []
    for _, r in summary.iterrows():
        reviewer = r["reviewer"]
        n_instances = int(r["n_instances"])

        # instance_hit_rate
        ihr = float(r["instance_hit_rate"])
        ihr_n = n_instances
        ihr_k = _round_num(ihr, ihr_n)
        ihr_lo, ihr_hi = wilson_ci(ihr_k, ihr_n)

        # site_recall (denominator is total oracle sites across scored instances)
        sr = float(r["site_recall"])
        sr_n = sites_total
        sr_k = _round_num(sr, sr_n)
        sr_lo, sr_hi = wilson_ci(sr_k, sr_n)

        # file_level_hit_rate (pulled from E.4 artefact for numerator)
        fl = file_lv[file_lv["reviewer"] == reviewer]
        if len(fl) == 1:
            fl_k = int(fl.iloc[0]["file_level_hit_count"])
            fl_n = int(fl.iloc[0]["n_instances"])
            fl_lo, fl_hi = wilson_ci(fl_k, fl_n)
        else:
            fl_k, fl_n, fl_lo, fl_hi = -1, -1, 0.0, 0.0

        # precision@k -- numerator and denominator are not recoverable
        # from the aggregated summary CSV (per-instance comment counts
        # are not stored); CI columns are emitted as 'unavailable'.
        rows.append(
            {
                "reviewer": reviewer,
                "n_instances": n_instances,
                "instance_hit_n": ihr_k,
                "instance_total_n": ihr_n,
                "instance_hit_rate": ihr,
                "instance_hit_rate_ci_low": ihr_lo,
                "instance_hit_rate_ci_high": ihr_hi,
                "sites_hit_n": sr_k,
                "sites_total_n": sr_n,
                "site_recall": sr,
                "site_recall_ci_low": sr_lo,
                "site_recall_ci_high": sr_hi,
                "file_hit_instances_n": fl_k,
                "file_total_instances_n": fl_n,
                "file_level_hit_rate": fl_k / fl_n if fl_n > 0 else 0.0,
                "file_level_hit_rate_ci_low": fl_lo,
                "file_level_hit_rate_ci_high": fl_hi,
                "false_positives_per_instance_mean": float(
                    r["false_positives_per_instance_mean"]
                ),
                "precision_at_1": float(r["precision_at_1"]),
                "precision_at_1_ci_low": "unavailable",
                "precision_at_1_ci_high": "unavailable",
                "precision_at_3": float(r["precision_at_3"]),
                "precision_at_3_ci_low": "unavailable",
                "precision_at_3_ci_high": "unavailable",
                "precision_at_5": float(r["precision_at_5"]),
                "precision_at_5_ci_low": "unavailable",
                "precision_at_5_ci_high": "unavailable",
                "total_estimated_cost_usd": float(r["total_estimated_cost_usd"]),
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Round 2 variants
# ---------------------------------------------------------------------------


def round2_with_ci() -> list[dict[str, Any]]:
    """Re-emit ``variant_summary.csv`` with explicit numerator and
    denominator columns. The CIs themselves are recomputed here so the
    file is self-contained and uses the same Wilson formula as Round 1.
    """
    summary = pd.read_csv(ROUND2_DIR / "variant_summary.csv")
    oracle = json.loads((ROUND2_DIR / "oracle_index.json").read_text(encoding="utf-8"))
    sites_total = sum(int(inst["n_sites"]) for inst in oracle["instances"].values())

    rows: list[dict[str, Any]] = []
    for _, r in summary.iterrows():
        n_instances = int(r["n_instances"])

        ihr = float(r["instance_hit_rate"])
        ihr_n = n_instances
        ihr_k = _round_num(ihr, ihr_n)
        ihr_lo, ihr_hi = wilson_ci(ihr_k, ihr_n)

        sr = float(r["site_recall"])
        sr_n = sites_total
        sr_k = _round_num(sr, sr_n)
        sr_lo, sr_hi = wilson_ci(sr_k, sr_n)

        flr = float(r["file_level_hit_rate"])
        fl_n = n_instances
        fl_k = _round_num(flr, fl_n)
        fl_lo, fl_hi = wilson_ci(fl_k, fl_n)

        rows.append(
            {
                "reviewer": r["reviewer"],
                "prompt_variant": r["prompt_variant"],
                "template_id": r["template_id"],
                "n_instances": n_instances,
                "n_comments": int(r["n_comments"]),
                "comments_per_instance": float(r["comments_per_instance"]),
                "instance_hit_n": ihr_k,
                "instance_total_n": ihr_n,
                "instance_hit_rate": ihr,
                "instance_hit_rate_ci_low": ihr_lo,
                "instance_hit_rate_ci_high": ihr_hi,
                "sites_hit_n": sr_k,
                "sites_total_n": sr_n,
                "site_recall": sr,
                "site_recall_ci_low": sr_lo,
                "site_recall_ci_high": sr_hi,
                "file_hit_instances_n": fl_k,
                "file_total_instances_n": fl_n,
                "file_level_hit_rate": flr,
                "file_level_hit_rate_ci_low": fl_lo,
                "file_level_hit_rate_ci_high": fl_hi,
                "false_positives_per_instance_mean": float(
                    r["false_positives_per_instance_mean"]
                ),
                "precision_at_1": float(r["precision_at_1"]),
                "precision_at_1_ci_low": "unavailable",
                "precision_at_1_ci_high": "unavailable",
                "precision_at_3": float(r["precision_at_3"]),
                "precision_at_3_ci_low": "unavailable",
                "precision_at_3_ci_high": "unavailable",
                "precision_at_5": float(r["precision_at_5"]),
                "precision_at_5_ci_low": "unavailable",
                "precision_at_5_ci_high": "unavailable",
                "latency_avg_seconds": float(r["latency_avg_seconds"]),
                "estimated_total_cost_usd": float(r["estimated_total_cost_usd"]),
                "cache_hits": int(r["cache_hits"]),
                "cache_misses": int(r["cache_misses"]),
            }
        )
    return rows


def write_methodology(sites_total: int) -> Path:
    txt = f"""# CI methodology (H-lite Task 2)

All rate metrics in ``round1_with_ci.csv`` and ``variant_summary_with_ci.csv``
carry a two-sided Wilson 95% confidence interval. Both files share the
same formula and the same z value; the only difference between them is
which population they describe.

## Formula

For a binomial proportion p_hat = k / n with k successes out of n
independent trials, the two-sided Wilson 95% confidence interval is

```
centre = (p_hat + z^2 / (2n)) / (1 + z^2 / n)
margin = z * sqrt( p_hat (1 - p_hat) / n + z^2 / (4 n^2) ) / (1 + z^2 / n)
low  = clamp(centre - margin, 0, 1)
high = clamp(centre + margin, 0, 1)
```

with z = 1.959963984540054 (the exact two-sided 95% normal quantile,
not the rounded 1.96).

**No continuity correction is applied.** The non-corrected Wilson
interval is the default reported in most epidemiology / statistics
references (see e.g. Newcombe 1998, *Statistics in Medicine*, Method 3)
and is what ``statsmodels.proportion.proportion_confint(method='wilson')``
returns. The corrected variant ("Wilson with continuity correction",
Newcombe Method 4) is slightly more conservative on small n but is not
used here; documenting the choice here makes any external comparison
unambiguous.

## Why not normal approximation

The normal-approximation CI ``p_hat +/- z * sqrt(p_hat (1 - p_hat) / n)``
is unreliable at small n or rates near 0 / 1. At n = 20 with p_hat = 0
(the Round 1 baseline for Claude), normal-approx returns [0, 0]; Wilson
returns [0.000, 0.161]. The latter is the honest representation of
sampling uncertainty.

## Denominators per metric

| metric | numerator (k) | denominator (n) |
|---|---|---|
| ``instance_hit_rate`` | reviewer scored a hit on the instance under tolerance=3 | total instances scored (20) |
| ``site_recall`` | oracle sites hit (any comment matched site within tolerance=3) | total oracle sites across scored instances ({sites_total}) |
| ``file_level_hit_rate`` | instances where the reviewer emitted >=1 valid comment on any oracle file (line numbers ignored) | total instances scored (20) |

The site total of {sites_total} is the sum of ``n_sites`` across all
20 instances in ``outputs/round2/oracle_index.json`` (Round 1 used
``strict_mode=False``, one site per hunk). Every reviewer in Round 1
and every (reviewer, variant) pair in Round 2 is scored against the
same 20 instances, so the site denominator is constant per row.

## precision@k

The CI columns for ``precision_at_{{1,3,5}}`` are marked
``unavailable``. ``precision@k`` is averaged across instances after
clipping k to ``min(k, n_comments)`` per instance, so the binomial
denominator differs per instance and is not recoverable from the
aggregated summary CSV. Computing a CI would require either (a)
returning to the per-comment ``results.csv`` rows and bootstrapping
over instances, or (b) treating per-instance precision values as a
continuous sample and using a normal interval -- neither is in scope
for H-lite Task 2.

## Small-sample caveat

n = 20 is a pilot. At this denominator, Wilson 95% CIs are wide
(roughly +/- 0.15 - 0.20 in the middle of the [0, 1] range and longer
near the ends). Treat hit-rate deltas between reviewers or variants as
direction-of-effect only; do not infer a statistically resolved
ranking from this sample. Full SWE-bench Lite (n = 300) would shrink
the intervals by a factor of ~4x.
"""
    out = H_LITE_DIR / "ci_methodology.md"
    out.write_text(txt, encoding="utf-8")
    return out


def main() -> None:
    H_LITE_DIR.mkdir(parents=True, exist_ok=True)

    r1 = round1_with_ci()
    out1 = H_LITE_DIR / "round1_with_ci.csv"
    pd.DataFrame(r1).to_csv(out1, index=False)
    print(f"wrote {out1} ({len(r1)} rows)")

    r2 = round2_with_ci()
    out2 = H_LITE_DIR / "variant_summary_with_ci.csv"
    pd.DataFrame(r2).to_csv(out2, index=False)
    print(f"wrote {out2} ({len(r2)} rows)")

    oracle = json.loads(
        (ROUND2_DIR / "oracle_index.json").read_text(encoding="utf-8")
    )
    sites_total = sum(int(inst["n_sites"]) for inst in oracle["instances"].values())
    out3 = write_methodology(sites_total)
    print(f"wrote {out3} (sites_total={sites_total})")


if __name__ == "__main__":
    main()
