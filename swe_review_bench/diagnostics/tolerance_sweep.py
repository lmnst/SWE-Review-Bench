"""Tolerance sensitivity sweep for the n=100 study (zero API).

Re-scores the stored reviewer comments against the reconstructed oracle
sites at several line tolerances, issuing no new model calls. The matcher,
oracle, and instance denominator are the same as the main run, so at N=3
the swept ``instance_hit_rate`` reproduces the headline numbers exactly.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..data.oracle import OracleSite
from ..scoring.matching import MatchableComment, match_comments


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TOLERANCES = (0, 3, 10)


def load_comments(
    results_csv: Path,
) -> dict[tuple[str, str, str], list[MatchableComment]]:
    """(reviewer, variant, instance) -> emitted comments with a line range.

    Placeholder rows (skipped files) carry no line range and are ignored.
    """
    out: dict[tuple[str, str, str], list[MatchableComment]] = defaultdict(list)
    with results_csv.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            ls = (row.get("line_start") or "").strip()
            le = (row.get("line_end") or "").strip()
            if ls in ("", "None") or le in ("", "None"):
                continue
            key = (row["reviewer"], row["prompt_variant"], row["instance_id"])
            out[key].append(
                MatchableComment(
                    file=row["file"], line_start=int(ls), line_end=int(le)
                )
            )
    return out


def load_oracle(oracle_index_json: Path) -> tuple[dict[str, list[OracleSite]], int]:
    """Return per-instance oracle sites and the total instance count.

    The total count (the hit-rate denominator) includes instances with no
    oracle sites, matching the main run's ``n_instances``.
    """
    data = json.loads(oracle_index_json.read_text(encoding="utf-8"))
    sites_by_inst: dict[str, list[OracleSite]] = {}
    for iid, inst in data["instances"].items():
        sites_by_inst[iid] = [
            OracleSite(
                site_id=s["site_id"],
                file=s["file"],
                line_start=int(s["line_start"]),
                line_end=int(s["line_end"]),
            )
            for s in inst.get("sites", [])
        ]
    return sites_by_inst, len(data["instances"])


def sweep(
    results_csv: Path,
    oracle_index_json: Path,
    output_dir: Path,
    tolerances: tuple[int, ...] = DEFAULT_TOLERANCES,
) -> list[dict[str, Any]]:
    comments = load_comments(results_csv)
    sites_by_inst, n_total = load_oracle(oracle_index_json)
    rev_var = sorted({(r, v) for (r, v, _) in comments})

    rows: list[dict[str, Any]] = []
    for tol in tolerances:
        for rev, var in rev_var:
            n_hits = 0
            for iid, sites in sites_by_inst.items():
                if not sites:
                    continue
                cs = comments.get((rev, var, iid))
                if not cs:
                    continue
                outcome = match_comments(cs, sites, tolerance=tol)
                if any(outcome.site_hit.values()):
                    n_hits += 1
            rate = (n_hits / n_total) if n_total else 0.0
            rows.append(
                {
                    "tolerance": tol,
                    "reviewer": rev,
                    "prompt_variant": var,
                    "instance_hits": n_hits,
                    "n_instances": n_total,
                    "instance_hit_rate": rate,
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    out = output_dir / "tolerance_sweep.csv"
    if rows:
        with out.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    for r in rows:
        print(
            f"  N={r['tolerance']:>2} {r['reviewer']:>22}/{r['prompt_variant']}: "
            f"{r['instance_hits']}/{r['n_instances']} = {r['instance_hit_rate']:.3f}"
        )
    print(f"wrote {out}")
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description="Tolerance sweep for the n=100 study (zero API).")
    p.add_argument(
        "--results-csv",
        default=str(PROJECT_ROOT / "outputs" / "n100" / "variant_results.csv"),
    )
    p.add_argument(
        "--oracle-index",
        default=str(PROJECT_ROOT / "outputs" / "n100" / "oracle_index.json"),
    )
    p.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "outputs" / "n100"),
    )
    args = p.parse_args()
    sweep(Path(args.results_csv), Path(args.oracle_index), Path(args.output_dir))


if __name__ == "__main__":
    main()
