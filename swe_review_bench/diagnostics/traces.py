"""E.2 hit and near-miss traces.

Generates two markdown documents:

  outputs/round2/hit_traces.md
      One block per Round 1 hit comment (is_hit=True in results.csv).
      Each block records reviewer / instance / comment file & lines /
      oracle site id / oracle file & lines / step-by-step distance and
      overlap calculation / truncated message / source context windows
      around both the comment range and the oracle hunk range.

  outputs/round2/near_miss_traces.md
      One block per non-hit Claude comment whose file_normalized matches
      some oracle file in the instance. If empty, the file states so
      verbatim.

Source is fetched with ``git show <base_commit>:<path>`` so the cached
repos' working trees are not disturbed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ..config import load_config
from .path_norm import normalise_path
from .source_view import (
    SourceUnavailable,
    read_source_at,
    render_lines_window,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUND2_DIR = PROJECT_ROOT / "outputs" / "round2"


def _range_distance(c_start, c_end, o_start, o_end) -> int:
    if c_end >= o_start and c_start <= o_end:
        return 0
    if c_end < o_start:
        return o_start - c_end
    return c_start - o_end


def _ranges_overlap(c_start, c_end, o_start, o_end) -> bool:
    return c_end >= o_start and c_start <= o_end


def _safe_source(
    repo: str,
    base_commit: str,
    rel_path: str,
    repos_cache_dir: Path,
) -> tuple[str | None, str | None]:
    try:
        return read_source_at(
            repo, base_commit, rel_path, repos_cache_dir=repos_cache_dir
        ), None
    except SourceUnavailable as e:
        return None, str(e)


def _format_hit_block(
    *,
    row: pd.Series,
    site: dict[str, Any],
    repos_cache_dir: Path,
    block_idx: int,
) -> str:
    reviewer = row["reviewer"]
    instance_id = row["instance_id"]
    repo = row["repo"]
    base_commit = row["base_commit"]
    file_original = str(row["file"])
    file_normalised = normalise_path(file_original)
    c_start = int(row["line_start"])
    c_end = int(row["line_end"])
    tolerance = int(row["tolerance"])
    o_start = int(site["line_start"])
    o_end = int(site["line_end"])
    o_start_pad = o_start - tolerance
    o_end_pad = o_end + tolerance
    distance = _range_distance(c_start, c_end, o_start, o_end)
    overlap_padded = _ranges_overlap(c_start, c_end, o_start_pad, o_end_pad)

    parts: list[str] = []
    parts.append(f"## Hit {block_idx}: {reviewer}  /  {instance_id}\n\n")
    parts.append("| field | value |\n|---|---|\n")
    parts.append(f"| repo | `{repo}` |\n")
    parts.append(f"| base_commit | `{base_commit}` |\n")
    parts.append(f"| comment file (original) | `{file_original}` |\n")
    parts.append(f"| comment file (normalised) | `{file_normalised}` |\n")
    parts.append(f"| comment lines | {c_start}-{c_end} |\n")
    parts.append(f"| matched oracle site | `{site['site_id']}` |\n")
    parts.append(f"| oracle file | `{site['file']}` |\n")
    parts.append(f"| oracle lines | {o_start}-{o_end} |\n")
    parts.append(f"| tolerance (Round 1) | {tolerance} |\n")
    parts.append(f"| oracle range padded | {o_start_pad}-{o_end_pad} |\n")
    parts.append(
        f"| comment range overlaps padded oracle? | "
        f"{'YES' if overlap_padded else 'NO'} |\n"
    )
    parts.append(f"| raw distance (lines) | {distance} |\n")
    parts.append(f"| is_hit in results.csv | {bool(row['is_hit'])} |\n")
    parts.append(f"\n**Message**: {row['message']}\n\n")

    parts.append("### Distance / overlap calculation\n\n")
    parts.append(
        f"```\ncomment range [{c_start}, {c_end}]\n"
        f"oracle  range [{o_start}, {o_end}]\n"
        f"padded  range [{o_start_pad}, {o_end_pad}] (tolerance={tolerance})\n"
        f"overlap = (comment.end >= padded.start) AND (comment.start <= padded.end)\n"
        f"        = ({c_end} >= {o_start_pad}) AND ({c_start} <= {o_end_pad})\n"
        f"        = {c_end >= o_start_pad} AND {c_start <= o_end_pad}\n"
        f"        = {overlap_padded}\n```\n\n"
    )

    source, err = _safe_source(repo, base_commit, file_normalised, repos_cache_dir)
    if source is None:
        parts.append(f"**Source unavailable**: {err}\n\n")
        return "".join(parts)

    parts.append("### Source context (±5 lines around comment range)\n\n")
    parts.append("```\n")
    parts.append(
        render_lines_window(
            source, lo=c_start, hi=c_end, pad=5, highlight=(c_start, c_end)
        )
    )
    parts.append("\n```\n\n")

    parts.append("### Source context (±5 lines around oracle hunk)\n\n")
    parts.append("```\n")
    parts.append(
        render_lines_window(
            source, lo=o_start, hi=o_end, pad=5, highlight=(o_start, o_end)
        )
    )
    parts.append("\n```\n\n---\n\n")
    return "".join(parts)


def _format_near_miss_block(
    *,
    row: pd.Series,
    sites_for_instance: list[dict[str, Any]],
    repos_cache_dir: Path,
    block_idx: int,
) -> str:
    reviewer = row["reviewer"]
    instance_id = row["instance_id"]
    repo = row["repo"]
    base_commit = row["base_commit"]
    file_original = str(row["file"])
    file_normalised = normalise_path(file_original)
    c_start = int(row["line_start"])
    c_end = int(row["line_end"])
    tolerance = int(row["tolerance"])

    # Find the nearest oracle site within the same file.
    best_d = None
    best_site = None
    for s in sites_for_instance:
        if normalise_path(s["file"]) != file_normalised:
            continue
        d = _range_distance(
            c_start, c_end, int(s["line_start"]), int(s["line_end"])
        )
        if best_d is None or d < best_d:
            best_d = d
            best_site = s

    parts: list[str] = []
    parts.append(f"## Near-miss {block_idx}: {reviewer}  /  {instance_id}\n\n")
    parts.append("| field | value |\n|---|---|\n")
    parts.append(f"| repo | `{repo}` |\n")
    parts.append(f"| base_commit | `{base_commit}` |\n")
    parts.append(f"| comment file (original) | `{file_original}` |\n")
    parts.append(f"| comment file (normalised) | `{file_normalised}` |\n")
    parts.append(f"| comment lines | {c_start}-{c_end} |\n")
    if best_site is not None:
        parts.append(f"| nearest oracle site | `{best_site['site_id']}` |\n")
        parts.append(
            f"| oracle file | `{best_site['file']}` |\n"
        )
        parts.append(
            f"| oracle lines | {best_site['line_start']}-{best_site['line_end']} |\n"
        )
        parts.append(f"| distance (lines) | {best_d} |\n")
    else:
        parts.append("| nearest oracle site | (none — file does not match any oracle file) |\n")
    parts.append(f"| tolerance (Round 1) | {tolerance} |\n")
    parts.append(f"| is_hit in results.csv | {bool(row['is_hit'])} |\n")
    parts.append(f"| severity | {row['severity']} |\n")
    parts.append(f"\n**Message**: {row['message']}\n\n")

    source, err = _safe_source(repo, base_commit, file_normalised, repos_cache_dir)
    if source is None:
        parts.append(f"**Source unavailable**: {err}\n\n---\n\n")
        return "".join(parts)

    parts.append("### Source context (±5 lines around comment range)\n\n")
    parts.append("```\n")
    parts.append(
        render_lines_window(
            source, lo=c_start, hi=c_end, pad=5, highlight=(c_start, c_end)
        )
    )
    parts.append("\n```\n\n")
    if best_site is not None:
        parts.append("### Source context (±5 lines around oracle hunk)\n\n")
        parts.append("```\n")
        parts.append(
            render_lines_window(
                source,
                lo=int(best_site["line_start"]),
                hi=int(best_site["line_end"]),
                pad=5,
                highlight=(int(best_site["line_start"]), int(best_site["line_end"])),
            )
        )
        parts.append("\n```\n\n")
    parts.append("---\n\n")
    return "".join(parts)


def main() -> None:
    cfg = load_config()
    ROUND2_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(PROJECT_ROOT / "outputs" / "results.csv")
    df["skipped_reason"] = df["skipped_reason"].fillna("")
    df["matched_oracle_site_id"] = df["matched_oracle_site_id"].fillna("")
    df["message"] = df["message"].fillna("")
    df["severity"] = df["severity"].fillna("")
    df["file"] = df["file"].fillna("")

    oracle_index = json.loads(
        (ROUND2_DIR / "oracle_index.json").read_text(encoding="utf-8")
    )

    # ----- hit_traces.md -----
    hits = df[
        (df["skipped_reason"] == "")
        & (df["matched_oracle_site_id"] != "")
        & (df["is_hit"].astype(str).str.lower() == "true")
    ].reset_index(drop=True)

    lines: list[str] = []
    lines.append("# E.2 Round 1 hit traces\n\n")
    lines.append(
        f"Every row in ``outputs/results.csv`` with ``is_hit=True`` and a "
        f"non-empty ``matched_oracle_site_id`` (N={len(hits)}). Each block "
        f"recomputes the overlap calculation from the recorded "
        f"``(line_start, line_end, tolerance)`` and the oracle site ranges "
        f"reconstructed in E.0.5, so any mismatch with Round 1 would be "
        f"visible here.\n\n"
    )
    for i, row in hits.iterrows():
        site = next(
            (
                s
                for s in oracle_index["instances"][row["instance_id"]]["sites"]
                if s["site_id"] == row["matched_oracle_site_id"]
            ),
            None,
        )
        if site is None:
            lines.append(
                f"## Hit {i+1}: {row['reviewer']} / {row['instance_id']}\n"
                f"ERROR: matched oracle site `{row['matched_oracle_site_id']}` "
                f"not found in reconstructed oracle index.\n\n---\n\n"
            )
            continue
        lines.append(
            _format_hit_block(
                row=row,
                site=site,
                repos_cache_dir=cfg.repos_cache_dir,
                block_idx=int(i) + 1,
            )
        )
    (ROUND2_DIR / "hit_traces.md").write_text("".join(lines), encoding="utf-8")
    print(f"wrote hit_traces.md ({len(hits)} hits)")

    # ----- near_miss_traces.md (Claude only, file-matched non-hits) -----
    non_hits = df[
        (df["skipped_reason"] == "")
        & (df["reviewer"] == "claude-sonnet-4-5")
        & (df["is_hit"].astype(str).str.lower() == "false")
    ].reset_index(drop=True)

    on_oracle_file: list[pd.Series] = []
    for _, row in non_hits.iterrows():
        oracle_files = {
            normalise_path(s["file"])
            for s in oracle_index["instances"][row["instance_id"]]["sites"]
        }
        if normalise_path(str(row["file"])) in oracle_files:
            on_oracle_file.append(row)

    lines = ["# E.2 Claude near-miss traces\n\n"]
    if not on_oracle_file:
        lines.append("No Claude comments landed on any oracle file.\n")
    else:
        lines.append(
            f"All Claude non-hit comments whose file matches an oracle file for "
            f"the instance (N={len(on_oracle_file)}). Each block lists the "
            f"comment, the nearest oracle hunk in the same file, and source "
            f"context windows around both.\n\n"
        )
        for i, row in enumerate(on_oracle_file):
            sites = oracle_index["instances"][row["instance_id"]]["sites"]
            lines.append(
                _format_near_miss_block(
                    row=row,
                    sites_for_instance=sites,
                    repos_cache_dir=cfg.repos_cache_dir,
                    block_idx=i + 1,
                )
            )
    (ROUND2_DIR / "near_miss_traces.md").write_text("".join(lines), encoding="utf-8")
    print(f"wrote near_miss_traces.md ({len(on_oracle_file)} near-miss blocks)")


if __name__ == "__main__":
    main()
