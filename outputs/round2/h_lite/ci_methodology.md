# CI methodology (H-lite Task 2)

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
| ``site_recall`` | oracle sites hit (any comment matched site within tolerance=3) | total oracle sites across scored instances (32) |
| ``file_level_hit_rate`` | instances where the reviewer emitted >=1 valid comment on any oracle file (line numbers ignored) | total instances scored (20) |

The site total of 32 is the sum of ``n_sites`` across all
20 instances in ``outputs/round2/oracle_index.json`` (Round 1 used
``strict_mode=False``, one site per hunk). Every reviewer in Round 1
and every (reviewer, variant) pair in Round 2 is scored against the
same 20 instances, so the site denominator is constant per row.

## precision@k

The CI columns for ``precision_at_{1,3,5}`` are marked
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
