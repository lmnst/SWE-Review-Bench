"""Hit-set overlap matrix for the n=100 study (zero API, exploratory).

For every pair of (reviewer, prompt_variant) cells, report how many
instances both cells hit, how many each hit alone, and the Jaccard
overlap of the two hit sets. This is a descriptive companion to the
paired McNemar tests: McNemar asks whether the *marginal* hit rates
differ; the Jaccard here asks whether the two cells hit the *same*
instances. Two cells can share a marginal rate yet hit disjoint
instances, which is the pattern this table surfaces.

Reuses ``diagnostics.paired_comparison.load_hits`` for the
per-(reviewer, variant, instance) hit reduction and the frozen n=100
``variant_results.csv`` as input. Writes to ``outputs/validity_study/``
only; the frozen ``outputs/n100/`` artifacts are read, never modified.
"""

from __future__ import annotations

import argparse
import csv
import json
from itertools import combinations
from pathlib import Path
from typing import Any

from swe_review_bench.diagnostics.paired_comparison import load_hits

PROJECT_ROOT = Path(__file__).resolve().parents[2]
N100_DIR = PROJECT_ROOT / "outputs" / "n100"


def overlap_rows(
    hits: dict[tuple[str, str], dict[str, bool]],
    universe: set[str] | None = None,
) -> list[dict[str, Any]]:
    """One row per unordered pair of (reviewer, variant) cells.

    ``universe`` is the full paired instance set; an instance absent from
    a cell's map counts as a miss. Jaccard is |A and B| / |A or B| over
    the hit sets; a pair where neither cell hits anything has an empty
    union and reports ``jaccard = None`` (0/0 is undefined, not zero).
    """
    cells = sorted(hits)
    if universe is not None:
        instances = sorted(universe)
    else:
        instances: list[str] = sorted({i for m in hits.values() for i in m})

    rows: list[dict[str, Any]] = []
    for (rx, vx), (ry, vy) in combinations(cells, 2):
        hx, hy = hits[(rx, vx)], hits[(ry, vy)]
        both = x_only = y_only = neither = 0
        for i in instances:
            a, b = hx.get(i, False), hy.get(i, False)
            if a and b:
                both += 1
            elif a:
                x_only += 1
            elif b:
                y_only += 1
            else:
                neither += 1
        union = both + x_only + y_only
        rows.append(
            {
                "cell_x": f"{rx}/{vx}",
                "cell_y": f"{ry}/{vy}",
                "n": len(instances),
                "x_hits": both + x_only,
                "y_hits": both + y_only,
                "both_hit": both,
                "x_only": x_only,
                "y_only": y_only,
                "neither": neither,
                "union": union,
                "jaccard": (both / union) if union > 0 else None,
            }
        )
    return rows


def run(results_csv: Path, oracle_index_json: Path, output_dir: Path) -> list[dict[str, Any]]:
    hits = load_hits(results_csv)
    universe = set(json.loads(oracle_index_json.read_text(encoding="utf-8"))["instances"].keys())
    rows = overlap_rows(hits, universe)

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "hit_overlap_matrix.csv"
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        j = "n/a" if r["jaccard"] is None else f"{r['jaccard']:.3f}"
        print(
            f"  {r['cell_x']} vs {r['cell_y']}: both={r['both_hit']} "
            f"x_only={r['x_only']} y_only={r['y_only']} jaccard={j} (n={r['n']})"
        )
    print(f"wrote {out}")
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description="Hit-set overlap matrix for the n=100 study.")
    p.add_argument("--results-csv", default=str(N100_DIR / "variant_results.csv"))
    p.add_argument("--oracle-index", default=str(N100_DIR / "oracle_index.json"))
    p.add_argument(
        "--output-dir", default=str(PROJECT_ROOT / "outputs" / "validity_study")
    )
    args = p.parse_args()
    run(Path(args.results_csv), Path(args.oracle_index), Path(args.output_dir))


if __name__ == "__main__":
    main()
