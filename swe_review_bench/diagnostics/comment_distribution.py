"""E.1 comment landing distribution analyzer.

Reads Round 1's ``outputs/results.csv`` and the reconstructed oracle index
(E.0.5 output), assigns each comment a distance-from-oracle bucket, and
emits:

  outputs/round2/diagnostic_comment_distribution.csv  -- per-comment rows
  outputs/round2/diagnostic_comment_distribution.md   -- per-reviewer summary

Path normalisation is applied symmetrically to both sides; see ``path_norm``.

Distance:
    * 0 if the comment range and any oracle hunk range overlap.
    * Otherwise the minimum line-gap to any hunk in the same (normalised)
      file.

Distance buckets:
    wrong_file, right_file_distance_0, right_file_distance_1_to_3,
    right_file_distance_4_to_10, right_file_distance_gt_10,
    invalid_line_or_file.

Claude comments get a deterministic theme label from ``classify.classify_message``.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import pandas as pd

from .classify import LABELS, classify_message
from .path_norm import normalise_path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUND2_DIR = PROJECT_ROOT / "outputs" / "round2"


BUCKETS = (
    "wrong_file",
    "right_file_distance_0",
    "right_file_distance_1_to_3",
    "right_file_distance_4_to_10",
    "right_file_distance_gt_10",
    "invalid_line_or_file",
)


def _range_distance(
    c_start: int, c_end: int, o_start: int, o_end: int
) -> int:
    """Return 0 if [c_start,c_end] overlaps [o_start,o_end]; else the gap."""
    if c_end >= o_start and c_start <= o_end:
        return 0
    if c_end < o_start:
        return o_start - c_end
    return c_start - o_end


def _bucket_for(file_match: bool, distance: int | None) -> str:
    if not file_match:
        return "wrong_file"
    if distance is None:
        return "invalid_line_or_file"
    if distance == 0:
        return "right_file_distance_0"
    if 1 <= distance <= 3:
        return "right_file_distance_1_to_3"
    if 4 <= distance <= 10:
        return "right_file_distance_4_to_10"
    return "right_file_distance_gt_10"


def _wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson 95% CI for a binomial proportion."""
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = (
        z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    )
    return max(0.0, centre - margin), min(1.0, centre + margin)


def load_oracle_index() -> dict[str, Any]:
    return json.loads(
        (ROUND2_DIR / "oracle_index.json").read_text(encoding="utf-8")
    )


def load_results_csv() -> pd.DataFrame:
    df = pd.read_csv(PROJECT_ROOT / "outputs" / "results.csv")
    df["skipped_reason"] = df["skipped_reason"].fillna("")
    df["matched_oracle_site_id"] = df["matched_oracle_site_id"].fillna("")
    df["message"] = df["message"].fillna("")
    df["severity"] = df["severity"].fillna("")
    df["file"] = df["file"].fillna("")
    return df


def build_per_comment_rows(
    df: pd.DataFrame, oracle_index: dict
) -> list[dict[str, Any]]:
    """Build per-comment diagnostic rows (only real comments; skipped placeholders excluded)."""
    rows: list[dict[str, Any]] = []
    # Order per (instance, reviewer) preserves results.csv row order so
    # comment_idx is meaningful.
    comment_counters: dict[tuple[str, str], int] = {}

    for _, r in df.iterrows():
        if r["skipped_reason"]:
            # Skipped (reviewer, file) placeholder -- not a real comment.
            continue
        # Some rows may legitimately have no line_start (none in Round 1,
        # but be defensive).
        try:
            line_start = int(r["line_start"]) if pd.notna(r["line_start"]) else None
            line_end = int(r["line_end"]) if pd.notna(r["line_end"]) else None
        except (TypeError, ValueError):
            line_start = line_end = None

        instance_id = r["instance_id"]
        reviewer = r["reviewer"]
        key = (instance_id, reviewer)
        comment_counters[key] = comment_counters.get(key, 0) + 1
        comment_idx = comment_counters[key]

        inst = oracle_index["instances"].get(instance_id) or {}
        oracle_sites = inst.get("sites", [])
        oracle_files_normalised = {
            normalise_path(s["file"]) for s in oracle_sites
        }

        file_original = str(r["file"])
        file_normalised = normalise_path(file_original)
        file_match = file_normalised in oracle_files_normalised

        if line_start is None or line_end is None:
            distance = None
            site_id = None
        elif not file_match:
            distance = None
            site_id = None
        else:
            best_d = None
            best_site = None
            for s in oracle_sites:
                if normalise_path(s["file"]) != file_normalised:
                    continue
                d = _range_distance(
                    line_start, line_end, int(s["line_start"]), int(s["line_end"])
                )
                if best_d is None or d < best_d:
                    best_d = d
                    best_site = s["site_id"]
            distance = best_d
            site_id = best_site

        bucket = _bucket_for(file_match, distance)

        msg = (r["message"] or "")[:180]
        is_hit = bool(r["is_hit"]) if isinstance(r["is_hit"], (bool,)) else (
            str(r["is_hit"]).strip().lower() in ("true", "1")
        )

        rows.append(
            {
                "reviewer": reviewer,
                "instance_id": instance_id,
                "comment_idx": comment_idx,
                "file_original": file_original,
                "file_normalized": file_normalised,
                "line_start": line_start,
                "line_end": line_end,
                "severity": r["severity"],
                "message_truncated": msg,
                "nearest_oracle_file_match": file_match,
                "nearest_oracle_site_id": site_id or "",
                "nearest_oracle_distance_lines": distance if distance is not None else "",
                "distance_bucket": bucket,
                "is_round1_hit": is_hit,
            }
        )
    return rows


def summarise(per_comment: list[dict[str, Any]], oracle_index: dict) -> dict[str, dict[str, Any]]:
    """Per-reviewer summary metrics."""
    reviewers = sorted({r["reviewer"] for r in per_comment})
    all_instance_ids = list(oracle_index["instances"].keys())
    n_instances_total = len(all_instance_ids)

    out: dict[str, dict[str, Any]] = {}
    for reviewer in reviewers:
        rows = [r for r in per_comment if r["reviewer"] == reviewer]
        n_comments = len(rows)
        instances_with_comments = {r["instance_id"] for r in rows}
        per_instance_counts: dict[str, int] = {iid: 0 for iid in all_instance_ids}
        for r in rows:
            per_instance_counts[r["instance_id"]] = per_instance_counts.get(r["instance_id"], 0) + 1
        counts_sorted = sorted(per_instance_counts.values())

        def _q(q: float) -> float:
            if not counts_sorted:
                return 0.0
            idx = max(0, min(len(counts_sorted) - 1, int(round(q * (len(counts_sorted) - 1)))))
            return counts_sorted[idx]

        bucket_counts = {b: 0 for b in BUCKETS}
        for r in rows:
            bucket_counts[r["distance_bucket"]] = bucket_counts.get(r["distance_bucket"], 0) + 1

        def _rate(k: int) -> tuple[float, tuple[float, float]]:
            if n_comments == 0:
                return 0.0, (0.0, 0.0)
            return k / n_comments, _wilson_ci(k, n_comments)

        bucket_rates = {b: _rate(bucket_counts[b]) for b in BUCKETS}

        out[reviewer] = {
            "n_comments": n_comments,
            "n_instances_with_comments": len(instances_with_comments),
            "n_instances_total": n_instances_total,
            "comments_per_instance_mean": (
                sum(per_instance_counts.values()) / n_instances_total
                if n_instances_total else 0.0
            ),
            "comments_per_instance_median": (
                counts_sorted[len(counts_sorted) // 2]
                if counts_sorted else 0
            ),
            "comments_per_instance_p10": _q(0.10),
            "comments_per_instance_p90": _q(0.90),
            "comments_per_instance_max": counts_sorted[-1] if counts_sorted else 0,
            "comments_per_instance_min": counts_sorted[0] if counts_sorted else 0,
            "bucket_counts": bucket_counts,
            "bucket_rates": bucket_rates,
        }
    return out


def claude_theme_table(per_comment: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply classify_message to every Claude comment."""
    out = []
    for r in per_comment:
        if r["reviewer"] != "claude-sonnet-4-5":
            continue
        out.append(
            {
                **r,
                "theme": classify_message(r["message_truncated"]),
            }
        )
    return out


def write_csv(per_comment: list[dict[str, Any]], path: Path) -> None:
    pd.DataFrame(per_comment).to_csv(path, index=False)


def write_md(
    summary: dict[str, dict[str, Any]],
    claude_themed: list[dict[str, Any]],
    path: Path,
) -> None:
    lines: list[str] = ["# E.1 Comment landing distribution\n\n"]

    lines.append("## Per-reviewer summary (Round 1, N=20 instances)\n\n")
    lines.append(
        "| reviewer | n_comments | n_inst_with_comments | mean_cpi | median_cpi | p10 | p90 | min | max |\n"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for rev, s in summary.items():
        lines.append(
            f"| {rev} | {s['n_comments']} | "
            f"{s['n_instances_with_comments']}/{s['n_instances_total']} | "
            f"{s['comments_per_instance_mean']:.2f} | "
            f"{s['comments_per_instance_median']} | "
            f"{s['comments_per_instance_p10']} | "
            f"{s['comments_per_instance_p90']} | "
            f"{s['comments_per_instance_min']} | "
            f"{s['comments_per_instance_max']} |\n"
        )

    lines.append("\n## Distance-from-oracle bucket distribution\n\n")
    lines.append(
        "Rates are over each reviewer's own comment population; Wilson 95% CI in brackets.\n\n"
    )
    lines.append(
        "| reviewer | wrong_file | right_d0 | right_d1-3 | right_d4-10 | right_d>10 | invalid |\n"
    )
    lines.append("|---|---|---|---|---|---|---|\n")
    for rev, s in summary.items():
        cells = []
        for b in BUCKETS:
            rate, (lo, hi) = s["bucket_rates"][b]
            count = s["bucket_counts"][b]
            cells.append(f"{count} ({rate:.0%}, [{lo:.2f},{hi:.2f}])")
        lines.append(f"| {rev} | " + " | ".join(cells) + " |\n")

    lines.append("\n### Reading note\n\n")
    lines.append(
        "- ``wrong_file``: comment's file does not match any oracle file for "
        "the instance after symmetric path normalisation.\n"
        "- ``right_file_distance_0``: comment range overlaps an oracle hunk "
        "range (would be a hit at tolerance=0).\n"
        "- ``right_file_distance_1_to_3``: file matches and minimum line "
        "gap is 1-3 inclusive (would be a hit at tolerance=3, the Round 1 "
        "setting).\n"
        "- ``right_file_distance_4_to_10``: file matches but tolerance=3 "
        "cuts these off; tolerance=10 would catch them.\n"
        "- ``right_file_distance_gt_10``: file matches, lines far from "
        "any oracle hunk.\n"
        "- ``invalid_line_or_file``: line_start/line_end missing or unparseable.\n"
    )

    lines.append("\n## Claude theme classification (full listing)\n\n")
    if not claude_themed:
        lines.append("(No Claude comments found.)\n")
    else:
        # Theme counts.
        theme_counts: dict[str, int] = {label: 0 for label in LABELS}
        for r in claude_themed:
            theme_counts[r["theme"]] = theme_counts.get(r["theme"], 0) + 1
        lines.append("### Theme counts\n\n")
        lines.append("| theme | count |\n|---|---:|\n")
        for label in LABELS:
            lines.append(f"| {label} | {theme_counts.get(label, 0)} |\n")

        lines.append("\n### Per-comment listing\n\n")
        lines.append(
            "| instance | idx | file | lines | bucket | nearest_site | dist | theme | message |\n"
        )
        lines.append("|---|---:|---|---:|---|---|---:|---|---|\n")
        for r in claude_themed:
            line_disp = (
                f"{r['line_start']}-{r['line_end']}"
                if r["line_start"] != r["line_end"]
                else str(r["line_start"])
            )
            msg = (r["message_truncated"] or "").replace("|", "\\|")
            lines.append(
                f"| {r['instance_id']} | {r['comment_idx']} | "
                f"{r['file_normalized']} | {line_disp} | "
                f"{r['distance_bucket']} | "
                f"{r['nearest_oracle_site_id'] or '-'} | "
                f"{r['nearest_oracle_distance_lines']} | "
                f"{r['theme']} | {msg} |\n"
            )

    lines.append("\n## Classifier rules\n\n")
    lines.append(
        "Classification is deterministic regex over the message text; the rule "
        "table lives in ``swe_review_bench/diagnostics/classify.py``. "
        "``possible_correctness_bug`` wins over weaker tags when both fire on "
        "the same message; ``other`` is the unmatched fallback. No LLM is "
        "used; classification does not affect scoring.\n"
    )

    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    ROUND2_DIR.mkdir(parents=True, exist_ok=True)
    oracle_index = load_oracle_index()
    df = load_results_csv()
    per_comment = build_per_comment_rows(df, oracle_index)

    csv_path = ROUND2_DIR / "diagnostic_comment_distribution.csv"
    write_csv(per_comment, csv_path)
    print(f"wrote {csv_path} ({len(per_comment)} rows)")

    summary = summarise(per_comment, oracle_index)
    claude_themed = claude_theme_table(per_comment)
    md_path = ROUND2_DIR / "diagnostic_comment_distribution.md"
    write_md(summary, claude_themed, md_path)
    print(f"wrote {md_path}")

    # quick stdout sanity table
    for rev, s in summary.items():
        print(
            f"  {rev}: n_comments={s['n_comments']} "
            f"buckets="
            + ", ".join(
                f"{b}={s['bucket_counts'][b]}" for b in BUCKETS if s['bucket_counts'][b]
            )
        )


if __name__ == "__main__":
    main()
