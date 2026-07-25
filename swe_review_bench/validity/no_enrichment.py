"""No-enrichment test on the 30-instance audited subset (zero API, exploratory).

If the benchmark measured bug detection, reviewer hits should concentrate
on the instances that actually contain a cold-reviewable defect. This
module builds, for each (reviewer, variant) cell, the 2x2 table

                       reviewer hit    reviewer miss
    has bug site            a               b
    no bug site             c               d

over the 30 hand-audited instances, and reports Fisher's exact two-sided
p, the odds ratio with a Woolf 95% CI (Haldane-Anscombe corrected on
zero cells), and the per-stratum hit rates with Wilson intervals.

The four per-cell tables are NOT independent (the same instances recur
across reviewers and variants), so they are never pooled into one test.
A single ``any-cell`` row -- an instance counts as a hit if any
(reviewer, variant) cell hit it -- is reported separately as the
maximum-power view, and read as descriptive, not as a fifth independent
test.

Inputs are the frozen ``variant_results.csv`` (per-comment hits) and
``oracle_validity_template.csv`` (per-site bug/related/unrelated
verdicts). Both are read, never modified; output goes to
``outputs/validity_study/`` only.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from swe_review_bench.diagnostics.paired_comparison import load_hits
from swe_review_bench.validity.stats import (
    fisher_exact_two_sided,
    odds_ratio_ci,
    wilson_ci,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
N100_DIR = PROJECT_ROOT / "outputs" / "n100"


def load_bug_site_flags(template_csv: Path) -> dict[str, bool]:
    """Map audited instance_id -> has at least one ``bug`` oracle site.

    An instance is a confirmed-bug instance iff at least one of its
    reconstructed oracle sites was labelled ``bug`` in the hand audit;
    ``related`` and ``unrelated`` sites do not qualify. Instances present
    in the template define the audited universe.
    """
    flags: dict[str, bool] = {}
    with template_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iid = row["instance_id"]
            is_bug = row["verdict"].strip().lower() == "bug"
            flags[iid] = flags.get(iid, False) or is_bug
    return flags


def _table(
    audited: list[str], has_bug: dict[str, bool], hit: dict[str, bool]
) -> dict[str, Any]:
    """2x2 counts + Fisher/OR/Wilson for one hit map over audited instances."""
    a = b = c = d = 0
    for i in audited:
        bug = has_bug[i]
        h = hit.get(i, False)
        if bug and h:
            a += 1
        elif bug and not h:
            b += 1
        elif (not bug) and h:
            c += 1
        else:
            d += 1
    bug_lo, bug_hi = wilson_ci(a, a + b)
    nobug_lo, nobug_hi = wilson_ci(c, c + d)
    orci = odds_ratio_ci(a, b, c, d)
    return {
        "n_audited": a + b + c + d,
        "n_bug": a + b,
        "n_nobug": c + d,
        "hit_bug": a,
        "miss_bug": b,
        "hit_nobug": c,
        "miss_nobug": d,
        "hit_rate_bug": a / (a + b) if (a + b) else None,
        "hit_rate_bug_ci_low": bug_lo,
        "hit_rate_bug_ci_high": bug_hi,
        "hit_rate_nobug": c / (c + d) if (c + d) else None,
        "hit_rate_nobug_ci_low": nobug_lo,
        "hit_rate_nobug_ci_high": nobug_hi,
        "odds_ratio": orci["odds_ratio"],
        "or_ci_low": orci["ci_low"],
        "or_ci_high": orci["ci_high"],
        "haldane_applied": orci["haldane_applied"],
        "fisher_exact_p": fisher_exact_two_sided(a, b, c, d),
    }


def run(
    results_csv: Path, template_csv: Path, output_dir: Path
) -> list[dict[str, Any]]:
    hits = load_hits(results_csv)
    has_bug = load_bug_site_flags(template_csv)
    audited = sorted(has_bug)

    rows: list[dict[str, Any]] = []
    for (reviewer, variant) in sorted(hits):
        rows.append(
            {
                "group": f"{reviewer}/{variant}",
                **_table(audited, has_bug, hits[(reviewer, variant)]),
            }
        )

    # Maximum-power descriptive view: hit if ANY cell hit the instance.
    any_hit = {i: any(m.get(i, False) for m in hits.values()) for i in audited}
    rows.append({"group": "any-cell", **_table(audited, has_bug, any_hit)})

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "no_enrichment.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        rb = "n/a" if r["hit_rate_bug"] is None else f"{r['hit_rate_bug']:.3f}"
        rn = "n/a" if r["hit_rate_nobug"] is None else f"{r['hit_rate_nobug']:.3f}"
        print(
            f"  {r['group']:<24} bug={r['hit_bug']}/{r['n_bug']} ({rb}) "
            f"nobug={r['hit_nobug']}/{r['n_nobug']} ({rn}) "
            f"OR={r['odds_ratio']:.2f} [{r['or_ci_low']:.2f},{r['or_ci_high']:.2f}] "
            f"fisher_p={r['fisher_exact_p']:.3f}"
        )
    print(f"wrote {out}")
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description="No-enrichment test on the audited subset.")
    p.add_argument("--results-csv", default=str(N100_DIR / "variant_results.csv"))
    p.add_argument("--template-csv", default=str(N100_DIR / "oracle_validity_template.csv"))
    p.add_argument(
        "--output-dir", default=str(PROJECT_ROOT / "outputs" / "validity_study")
    )
    args = p.parse_args()
    run(Path(args.results_csv), Path(args.template_csv), Path(args.output_dir))


if __name__ == "__main__":
    main()
