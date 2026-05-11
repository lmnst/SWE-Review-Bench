"""E.3 oracle sanity check.

random.seed(42) followed by random.sample(...) picks 3 of the 20 sampled
instance IDs. For each, this script prints side-by-side:

  * The raw fix-patch hunks (from the HF dataset's ``patch`` field).
  * The parsed oracle sites (line ranges from ``build_oracle_sites`` at
    the same ``strict_mode=False`` Round 1 used).
  * Source context ±5 lines around each oracle hunk in the pre-fix file
    (obtained via ``git show <base_commit>:<path>``).

The raw patch text is written ONLY to this diagnostic artefact and is
never exposed to any reviewer.

Output:
  outputs/round2/oracle_sanity.md
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

from unidiff import PatchSet

from ..config import load_config
from ..data.loader import load_instances
from ..data.oracle import build_oracle_sites
from .path_norm import normalise_path
from .source_view import SourceUnavailable, read_source_at, render_lines_window


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUND2_DIR = PROJECT_ROOT / "outputs" / "round2"


MAX_HUNKS_RENDERED = 3


def _instance_sample(all_ids: list[str], n: int = 3, seed: int = 42) -> list[str]:
    rng = random.Random(seed)
    return rng.sample(all_ids, n)


def _render_hunks(patch_text: str, *, max_hunks: int = MAX_HUNKS_RENDERED) -> str:
    """Render the first ``max_hunks`` hunks from each file in the patch."""
    ps = PatchSet(patch_text)
    parts: list[str] = []
    for pfile in ps:
        if pfile.is_binary_file:
            continue
        src = pfile.source_file or ""
        tgt = pfile.target_file or ""
        parts.append(f"#### File: `{src}` -> `{tgt}` ({len(pfile)} hunks)\n\n")
        for i, hunk in enumerate(pfile):
            if i >= max_hunks:
                parts.append(
                    f"(+ {len(pfile) - max_hunks} more hunks not shown)\n\n"
                )
                break
            parts.append("```diff\n")
            parts.append(str(hunk))
            if not str(hunk).endswith("\n"):
                parts.append("\n")
            parts.append("```\n\n")
    return "".join(parts)


def _block_for_instance(
    inst, repos_cache_dir: Path, idx: int
) -> str:
    parts: list[str] = []
    parts.append(f"# Instance {idx}: `{inst.instance_id}`\n\n")
    parts.append("| field | value |\n|---|---|\n")
    parts.append(f"| repo | `{inst.repo}` |\n")
    parts.append(f"| base_commit | `{inst.base_commit}` |\n")
    parts.append(f"| patch length (chars) | {len(inst.patch)} |\n\n")

    parts.append("## Raw fix-patch hunks\n\n")
    parts.append("_Note: raw patch text is in this diagnostic file only; reviewers never see it._\n\n")
    parts.append(_render_hunks(inst.patch))

    parts.append("## Parsed oracle sites (strict_mode=False, Round 1 setting)\n\n")
    sites = build_oracle_sites(inst.patch, strict_mode=False)
    parts.append("| site_id | file | lines |\n|---|---|---|\n")
    for s in sites:
        parts.append(f"| {s.site_id} | {s.file} | {s.line_start}-{s.line_end} |\n")
    parts.append("\n")

    parts.append("## Source context ±5 lines around each oracle hunk\n\n")
    for s in sites[:MAX_HUNKS_RENDERED]:
        rel = normalise_path(s.file)
        try:
            source = read_source_at(
                inst.repo,
                inst.base_commit,
                rel,
                repos_cache_dir=repos_cache_dir,
            )
        except SourceUnavailable as e:
            parts.append(f"### {s.site_id} `{rel}` lines {s.line_start}-{s.line_end}\n\n")
            parts.append(f"**Source unavailable**: {e}\n\n")
            continue
        parts.append(f"### {s.site_id} `{rel}` lines {s.line_start}-{s.line_end}\n\n")
        parts.append("```\n")
        parts.append(
            render_lines_window(
                source,
                lo=s.line_start,
                hi=s.line_end,
                pad=5,
                highlight=(s.line_start, s.line_end),
            )
        )
        parts.append("\n```\n\n")
    if len(sites) > MAX_HUNKS_RENDERED:
        parts.append(
            f"(+ {len(sites) - MAX_HUNKS_RENDERED} more sites not rendered "
            f"in detail; full list above.)\n\n"
        )
    parts.append("---\n\n")
    return "".join(parts)


def main() -> None:
    cfg = load_config()
    ROUND2_DIR.mkdir(parents=True, exist_ok=True)

    instances = load_instances(
        n=20, seed=42, dataset="princeton-nlp/SWE-bench_Lite", split="test"
    )
    all_ids = [inst.instance_id for inst in instances]
    sampled = _instance_sample(all_ids, n=3, seed=42)
    by_id = {inst.instance_id: inst for inst in instances}

    blocks: list[str] = []
    blocks.append("# E.3 Oracle sanity check (3 random instances)\n\n")
    blocks.append(
        f"Sampled from the 20 Round 1 instance IDs with "
        f"``random.Random(42).sample(all_20_ids, 3)``. Selected IDs: "
        f"{sampled}\n\n"
    )
    for i, iid in enumerate(sampled, start=1):
        inst = by_id[iid]
        blocks.append(_block_for_instance(inst, cfg.repos_cache_dir, idx=i))

    out_path = ROUND2_DIR / "oracle_sanity.md"
    out_path.write_text("".join(blocks), encoding="utf-8")
    print(f"wrote {out_path}")
    print("sampled instances:", sampled)


if __name__ == "__main__":
    main()
