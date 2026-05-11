"""E.4 file-level hit metric (diagnostics only).

Computes the diagnostics-only ``file_level_hit_rate`` per reviewer:
an instance counts as a file-level hit iff the reviewer produced at
least one valid comment on any oracle file for that instance, regardless
of line numbers. The denominator is the full Round 1 instance set
(N=20). Reviewers with zero comments for an instance still count toward
the denominator.

This metric is intentionally NOT merged into ``swe_review_bench.scoring``
in this milestone. It is a diagnostic that exposes the gap between
"reviewer pointed at the right file" and "reviewer pointed at the right
file AND right lines under tolerance".

Outputs:
  outputs/round2/file_level_metrics.csv
  outputs/round2/file_level_metrics.md
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .path_norm import normalise_path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUND2_DIR = PROJECT_ROOT / "outputs" / "round2"


def _wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - margin), min(1.0, centre + margin)


def compute() -> list[dict[str, Any]]:
    df = pd.read_csv(PROJECT_ROOT / "outputs" / "results.csv")
    df["skipped_reason"] = df["skipped_reason"].fillna("")
    df["matched_oracle_site_id"] = df["matched_oracle_site_id"].fillna("")
    df["file"] = df["file"].fillna("")

    oracle_index = json.loads(
        (ROUND2_DIR / "oracle_index.json").read_text(encoding="utf-8")
    )
    all_instance_ids = list(oracle_index["instances"].keys())
    n_total = len(all_instance_ids)

    reviewers = sorted(df["reviewer"].dropna().unique())
    rows: list[dict[str, Any]] = []
    for reviewer in reviewers:
        sub = df[(df["reviewer"] == reviewer) & (df["skipped_reason"] == "")]
        file_level_hits = 0
        line_level_hits = 0
        n_comments = 0
        for iid in all_instance_ids:
            oracle_files = {
                normalise_path(s["file"])
                for s in oracle_index["instances"][iid]["sites"]
            }
            inst_rows = sub[sub["instance_id"] == iid]
            inst_rows_real = inst_rows[inst_rows["line_start"].notna()]
            n_comments += len(inst_rows_real)
            if len(inst_rows_real) == 0:
                continue
            # File-level: any valid comment on any oracle file (file match
            # after symmetric normalisation).
            comment_files = {
                normalise_path(f) for f in inst_rows_real["file"].tolist()
            }
            if oracle_files & comment_files:
                file_level_hits += 1
            # Line-level: at least one is_hit row.
            if (inst_rows_real["is_hit"].astype(str).str.lower() == "true").any():
                line_level_hits += 1
        line_lo, line_hi = _wilson_ci(line_level_hits, n_total)
        file_lo, file_hi = _wilson_ci(file_level_hits, n_total)
        rows.append(
            {
                "reviewer": reviewer,
                "n_instances": n_total,
                "line_level_hit_count": line_level_hits,
                "line_level_hit_rate": line_level_hits / n_total if n_total else 0.0,
                "line_level_hit_rate_wilson_lo": line_lo,
                "line_level_hit_rate_wilson_hi": line_hi,
                "file_level_hit_count": file_level_hits,
                "file_level_hit_rate": file_level_hits / n_total if n_total else 0.0,
                "file_level_hit_rate_wilson_lo": file_lo,
                "file_level_hit_rate_wilson_hi": file_hi,
                "gap_file_to_line": (
                    (file_level_hits - line_level_hits) / n_total if n_total else 0.0
                ),
                "n_comments": n_comments,
                "comments_per_instance": (
                    n_comments / n_total if n_total else 0.0
                ),
            }
        )
    return rows


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    pd.DataFrame(rows).to_csv(path, index=False)


def write_md(rows: list[dict[str, Any]], path: Path) -> None:
    lines: list[str] = ["# E.4 File-level hit rate (diagnostics-only)\n\n"]
    lines.append(
        "An instance is a *file-level hit* for a reviewer iff the reviewer "
        "produced ≥1 comment on any oracle file for that instance, "
        "regardless of line numbers. The denominator is N=20 (every Round 1 "
        "instance, including those for which the reviewer emitted no "
        "comments). This metric is diagnostic only; it is not merged into "
        "the official scoring module.\n\n"
    )
    lines.append(
        "| reviewer | line_hits | line_hit_rate (95% CI) | file_hits | "
        "file_hit_rate (95% CI) | gap | n_comments | cpi |\n"
    )
    lines.append("|---|---:|---|---:|---|---:|---:|---:|\n")
    for r in rows:
        lines.append(
            f"| {r['reviewer']} | "
            f"{r['line_level_hit_count']} | "
            f"{r['line_level_hit_rate']:.2f} "
            f"[{r['line_level_hit_rate_wilson_lo']:.2f}, "
            f"{r['line_level_hit_rate_wilson_hi']:.2f}] | "
            f"{r['file_level_hit_count']} | "
            f"{r['file_level_hit_rate']:.2f} "
            f"[{r['file_level_hit_rate_wilson_lo']:.2f}, "
            f"{r['file_level_hit_rate_wilson_hi']:.2f}] | "
            f"{r['gap_file_to_line']:+.2f} | "
            f"{r['n_comments']} | "
            f"{r['comments_per_instance']:.2f} |\n"
        )
    lines.append("\n## Reading note\n\n")
    lines.append(
        "- ``line_hit_rate`` is the same as ``instance_hit_rate`` in "
        "``summary.csv`` (line-level matching under tolerance=3).\n"
        "- ``file_hit_rate`` ignores line numbers; it measures whether the "
        "reviewer pointed at the right file at all.\n"
        "- ``gap`` = ``file_hit_rate - line_hit_rate``. Large gap = "
        "reviewer is on the correct file but tolerance=3 / line number is "
        "what's failing.\n"
        "- The Round 1 reviewer-input filter only feeds files that appear in "
        "the fix patch into reviewers, so a comment can be on a wrong file "
        "only if a reviewer hallucinates a different file path (the parser "
        "overrides the JSON ``file`` field back to the input file, so this "
        "is structurally impossible in Round 1).\n"
    )
    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    ROUND2_DIR.mkdir(parents=True, exist_ok=True)
    rows = compute()
    csv_path = ROUND2_DIR / "file_level_metrics.csv"
    md_path = ROUND2_DIR / "file_level_metrics.md"
    write_csv(rows, csv_path)
    write_md(rows, md_path)
    print(f"wrote {csv_path}")
    print(f"wrote {md_path}")
    for r in rows:
        print(
            f"  {r['reviewer']}: line={r['line_level_hit_rate']:.2f} "
            f"file={r['file_level_hit_rate']:.2f} "
            f"gap={r['gap_file_to_line']:+.2f}"
        )


if __name__ == "__main__":
    main()
