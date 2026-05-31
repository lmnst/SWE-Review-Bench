"""Paired significance tests for the n=100 study (zero API).

Reduces ``variant_results.csv`` to a per-(reviewer, variant, instance) hit
boolean and runs McNemar's exact test for two contrasts:

* reviewer contrast: Claude vs GPT within each variant
* prompt contrast: variant A vs B within each reviewer

McNemar is the right test because every reviewer sees the same instances,
so the hits are paired; only the discordant pairs (b, c) drive the
p-value. The exact two-sided p-value is computed directly from the
binomial null (no external statistics dependency).
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from math import comb
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_hits(results_csv: Path) -> dict[tuple[str, str], dict[str, bool]]:
    """Map (reviewer, variant) -> {instance_id: hit}.

    A cell is a hit if any emitted comment for that (reviewer, variant,
    instance) matched an oracle site (the ``is_hit`` column).
    """
    hits: dict[tuple[str, str], dict[str, bool]] = defaultdict(dict)
    with results_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["reviewer"], row["prompt_variant"])
            iid = row["instance_id"]
            is_hit = str(row["is_hit"]).strip().lower() == "true"
            hits[key][iid] = hits[key].get(iid, False) or is_hit
    return hits


def mcnemar_exact_p(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value from discordant counts b and c.

    Under H0 the b + c discordant pairs split 50/50, so the smaller count
    is Binomial(b + c, 0.5). The two-sided exact p doubles the smaller
    tail, capped at 1.
    """
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


def paired_test(
    hits_x: dict[str, bool],
    hits_y: dict[str, bool],
    universe: set[str] | None = None,
) -> dict[str, Any]:
    """McNemar contingency counts and exact p for two paired hit maps.

    ``universe`` is the full set of paired instances; an instance absent
    from a hit map is treated as a miss. Defaults to the union of the two
    maps. The p-value depends only on the discordant counts (b, c), so the
    universe choice affects the reported n but not significance.
    """
    instances = sorted(universe) if universe is not None else sorted(set(hits_x) | set(hits_y))
    a = b = c = d = 0
    for i in instances:
        x = hits_x.get(i, False)
        y = hits_y.get(i, False)
        if x and y:
            a += 1
        elif x and not y:
            b += 1
        elif (not x) and y:
            c += 1
        else:
            d += 1
    return {
        "n": len(instances),
        "x_hits": a + b,
        "y_hits": a + c,
        "both_hit": a,
        "x_only": b,
        "y_only": c,
        "neither": d,
        "p_value": mcnemar_exact_p(b, c),
    }


def run(
    results_csv: Path, output_dir: Path, oracle_index_json: Path | None = None
) -> list[dict[str, Any]]:
    hits = load_hits(results_csv)
    universe: set[str] | None = None
    if oracle_index_json is not None:
        data = json.loads(Path(oracle_index_json).read_text(encoding="utf-8"))
        universe = set(data["instances"].keys())
    variants = sorted({v for (_, v) in hits})
    reviewers = sorted({r for (r, _) in hits})

    rows: list[dict[str, Any]] = []

    # Reviewer contrast: Claude vs GPT within each variant.
    if "claude-sonnet-4-5" in reviewers and "gpt-4o-mini" in reviewers:
        for v in variants:
            x = hits.get(("claude-sonnet-4-5", v))
            y = hits.get(("gpt-4o-mini", v))
            if not x or not y:
                continue
            rows.append(
                {
                    "contrast": "reviewer",
                    "group_x": f"claude-sonnet-4-5/{v}",
                    "group_y": f"gpt-4o-mini/{v}",
                    **paired_test(x, y, universe),
                }
            )

    # Prompt contrast: variant A vs B within each reviewer.
    if "A" in variants and "B" in variants:
        for r in reviewers:
            x = hits.get((r, "A"))
            y = hits.get((r, "B"))
            if not x or not y:
                continue
            rows.append(
                {
                    "contrast": "prompt",
                    "group_x": f"{r}/A",
                    "group_y": f"{r}/B",
                    **paired_test(x, y, universe),
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "paired_comparison.csv"
    if rows:
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    for r in rows:
        print(
            f"  [{r['contrast']}] {r['group_x']} vs {r['group_y']}: "
            f"x={r['x_hits']} y={r['y_hits']} discordant b={r['x_only']} "
            f"c={r['y_only']} p={r['p_value']:.4f} (n={r['n']})"
        )
    print(f"wrote {out}")
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description="Paired McNemar tests for the n=100 study.")
    p.add_argument(
        "--results-csv",
        default=str(PROJECT_ROOT / "outputs" / "n100" / "variant_results.csv"),
    )
    p.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "outputs" / "n100"),
    )
    p.add_argument(
        "--oracle-index",
        default=str(PROJECT_ROOT / "outputs" / "n100" / "oracle_index.json"),
        help="Oracle index whose instance ids define the paired universe.",
    )
    args = p.parse_args()
    run(Path(args.results_csv), Path(args.output_dir), Path(args.oracle_index))


if __name__ == "__main__":
    main()
