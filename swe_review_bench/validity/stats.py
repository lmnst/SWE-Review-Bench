"""Small-sample statistics for the validity-diagnostics analyses (zero API).

Self-contained implementations so the validity module has no external
statistics dependency, matching the convention in
``diagnostics/paired_comparison.py`` (which hand-rolls McNemar's exact
test). The Wilson interval is imported from the frozen H-lite helper
rather than re-derived, so every rate in this study uses one formula.
"""

from __future__ import annotations

from math import comb, exp, log, sqrt

from swe_review_bench.diagnostics.h2_wilson_ci import Z_95, wilson_ci

__all__ = ["wilson_ci", "Z_95", "fisher_exact_two_sided", "odds_ratio_ci"]


def _hypergeom_pmf(a: int, r1: int, r2: int, c1: int) -> float:
    """P(top-left cell == a) for a 2x2 table with fixed margins.

    r1, r2 are the row totals; c1 is the first column total; the total n
    is r1 + r2. Under fixed margins the top-left cell follows the
    hypergeometric law C(r1, a) * C(r2, c1 - a) / C(n, c1).
    """
    n = r1 + r2
    return comb(r1, a) * comb(r2, c1 - a) / comb(n, c1)


def fisher_exact_two_sided(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p-value for the 2x2 table [[a, b], [c, d]].

    Holds all four margins fixed and sums the probability of every table
    at least as extreme as the observed one, where "at least as extreme"
    means "hypergeometric probability <= that of the observed table"
    (the conventional two-sided definition, matching
    ``scipy.stats.fisher_exact``). A small relative tolerance guards the
    boundary comparison against floating-point noise.
    """
    if min(a, b, c, d) < 0:
        raise ValueError("cell counts must be non-negative")
    r1, r2 = a + b, c + d
    c1 = a + c
    n = r1 + r2
    if n == 0 or r1 == 0 or r2 == 0 or c1 == 0 or (b + d) == 0:
        # A degenerate table (an empty row or column) carries no
        # association signal; the exact test returns 1.0.
        return 1.0
    p_obs = _hypergeom_pmf(a, r1, r2, c1)
    lo = max(0, c1 - r2)
    hi = min(r1, c1)
    total = 0.0
    for x in range(lo, hi + 1):
        px = _hypergeom_pmf(x, r1, r2, c1)
        if px <= p_obs * (1 + 1e-7):
            total += px
    return min(1.0, total)


def odds_ratio_ci(
    a: int, b: int, c: int, d: int, *, z: float = Z_95
) -> dict[str, float | bool]:
    """Odds ratio and log-normal (Woolf) 95% CI for [[a, b], [c, d]].

    Returns the raw odds ratio (a*d)/(b*c) when every cell is positive.
    When any cell is zero the raw OR is undefined or infinite, so a
    Haldane-Anscombe 0.5 continuity correction is applied to all four
    cells for both the point estimate and the interval, and
    ``haldane_applied`` is set True. The CI is the Woolf interval
    exp(logOR +/- z * SE) with SE = sqrt(sum 1/cell).
    """
    haldane = min(a, b, c, d) == 0
    fa, fb, fc, fd = (a + 0.5, b + 0.5, c + 0.5, d + 0.5) if haldane else (a, b, c, d)
    orr = (fa * fd) / (fb * fc)
    se = sqrt(1 / fa + 1 / fb + 1 / fc + 1 / fd)
    log_or = log(orr)
    return {
        "odds_ratio": orr,
        "ci_low": exp(log_or - z * se),
        "ci_high": exp(log_or + z * se),
        "haldane_applied": haldane,
    }
