"""Oracle construct-validity sampling and reporting.

The benchmark assumes the reconstructed oracle (a fix patch's hunk source
ranges) marks the buggy code a reviewer should flag. That assumption is
not free: a fix patch can also touch peripheral lines (added guards,
refactors, call-site edits) that are not the defect. This module supports
a human audit of that assumption.

``sample``: stratified sample of N instances from the n=100 study; emit
one annotation card per instance (problem statement, fix patch,
reconstructed oracle sites with an is_test flag, and the pre-fix source at
each site) plus a blank verdict CSV.

``report``: read the filled verdict CSV and summarise site-level and
instance-level validity.

Verdict per oracle site:
    bug       - the oracle lines are the defect a reviewer should flag
    related   - part of the fix but not the core defect (peripheral edit)
    unrelated - refactor, test-only, or otherwise not the defect
"""

from __future__ import annotations

import argparse
import csv
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..config import load_config
from ..data.loader import Instance, load_instances
from ..data.oracle import build_oracle_sites, is_test_file
from ..data.repos import RepoUnavailable, ensure_repo_at_commit


PROJECT_ROOT = Path(__file__).resolve().parents[2]
N100_DIR = PROJECT_ROOT / "outputs" / "n100"

DATASET = "princeton-nlp/SWE-bench_Lite"
SPLIT = "test"
STUDY_N = 100
STUDY_SEED = 42

VERDICTS = ("bug", "related", "unrelated")
TEMPLATE_COLUMNS = (
    "instance_id",
    "repo",
    "site_id",
    "file",
    "line_start",
    "line_end",
    "is_test_file",
    "verdict",
    "note",
)


def stratified_sample(instances: list[Instance], n: int, seed: int) -> list[Instance]:
    """Round-robin over repos (each shuffled by seed) so every repo is
    covered and larger repos contribute proportionally more."""
    by_repo: dict[str, list[Instance]] = defaultdict(list)
    for inst in instances:
        by_repo[inst.repo].append(inst)
    rng = random.Random(seed)
    for repo in by_repo:
        by_repo[repo].sort(key=lambda i: i.instance_id)
        rng.shuffle(by_repo[repo])
    order = sorted(by_repo, key=lambda r: (-len(by_repo[r]), r))
    idx = {r: 0 for r in order}
    picked: list[Instance] = []
    while len(picked) < n:
        progressed = False
        for r in order:
            if idx[r] < len(by_repo[r]):
                picked.append(by_repo[r][idx[r]])
                idx[r] += 1
                progressed = True
                if len(picked) >= n:
                    break
        if not progressed:
            break
    return picked


def _source_snippet(repo_path: Path, file: str, line_start: int, line_end: int, ctx: int = 3) -> str:
    p = repo_path / file
    try:
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return "(source unavailable)"
    lo = max(1, line_start - ctx)
    hi = min(len(lines), line_end + ctx)
    out = []
    for ln in range(lo, hi + 1):
        marker = ">>" if line_start <= ln <= line_end else "  "
        out.append(f"{marker} {ln:>5}: {lines[ln - 1]}")
    return "\n".join(out)


def _card(inst: Instance, sites: list, repo_path: Path | None, problem_chars: int) -> str:
    lines: list[str] = []
    lines.append(f"## {inst.instance_id}  ({inst.repo})\n")
    ps = (inst.problem_statement or "").strip()
    if len(ps) > problem_chars:
        ps = ps[:problem_chars] + "\n[... truncated ...]"
    lines.append("### Issue (problem_statement)\n")
    lines.append(ps if ps else "(none)")
    lines.append("\n### Fix patch\n")
    lines.append("```diff")
    lines.append(inst.patch.strip())
    lines.append("```\n")
    lines.append("### Reconstructed oracle sites\n")
    for s in sites:
        flag = " [TEST FILE]" if is_test_file(s.file) else ""
        lines.append(f"- `{s.site_id}`  {s.file}:{s.line_start}-{s.line_end}{flag}")
        if repo_path is not None:
            snippet = _source_snippet(repo_path, s.file, s.line_start, s.line_end)
            lines.append("  ```")
            lines.append(snippet)
            lines.append("  ```")
    lines.append("")
    return "\n".join(lines)


def cmd_sample(n: int, seed: int, output_dir: Path) -> None:
    cfg = load_config()
    instances = load_instances(n=STUDY_N, seed=STUDY_SEED, dataset=DATASET, split=SPLIT)
    sample = stratified_sample(instances, n, seed)

    output_dir.mkdir(parents=True, exist_ok=True)
    cards_path = output_dir / "oracle_validity_cards.md"
    template_path = output_dir / "oracle_validity_template.csv"

    card_blocks: list[str] = []
    template_rows: list[dict[str, Any]] = []
    repo_counts: dict[str, int] = defaultdict(int)

    header = [
        "# Oracle construct-validity audit cards\n",
        f"Stratified sample of {len(sample)} instances (sub-seed {seed}) from the "
        f"n={STUDY_N} study (seed {STUDY_SEED}).\n",
        "For each oracle site, record a verdict in "
        "`oracle_validity_template.csv`:\n",
        "- `bug`: the marked lines are the defect a reviewer should flag.\n"
        "- `related`: part of the fix but not the core defect.\n"
        "- `unrelated`: refactor, test-only, or not the defect.\n",
        "`>>` in the source snippet marks the oracle lines.\n",
    ]

    for inst in sample:
        repo_counts[inst.repo] += 1
        sites = build_oracle_sites(inst.patch, strict_mode=False)
        try:
            repo_path = ensure_repo_at_commit(
                inst.repo, inst.base_commit, repos_cache_dir=cfg.repos_cache_dir
            )
        except RepoUnavailable:
            repo_path = None
        card_blocks.append(_card(inst, sites, repo_path, problem_chars=2000))
        for s in sites:
            template_rows.append(
                {
                    "instance_id": inst.instance_id,
                    "repo": inst.repo,
                    "site_id": s.site_id,
                    "file": s.file,
                    "line_start": s.line_start,
                    "line_end": s.line_end,
                    "is_test_file": is_test_file(s.file),
                    "verdict": "",
                    "note": "",
                }
            )

    cards_path.write_text("\n".join(header) + "\n" + "\n".join(card_blocks), encoding="utf-8")
    with template_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(TEMPLATE_COLUMNS))
        w.writeheader()
        w.writerows(template_rows)

    print(f"wrote {cards_path}")
    print(f"wrote {template_path} ({len(template_rows)} sites over {len(sample)} instances)")
    print("repo coverage:")
    for r in sorted(repo_counts):
        print(f"  {r:>28}  {repo_counts[r]}")


def _wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if not n:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, centre - margin), min(1.0, centre + margin)


def _subset_hit_rates(
    variant_results: Path, subset: set[str]
) -> list[tuple[str, str, int, int]]:
    """Instance hit rate on ``subset``, per (reviewer, variant)."""
    hits: dict[tuple[str, str], dict[str, bool]] = defaultdict(lambda: defaultdict(bool))
    with variant_results.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            key = (r["reviewer"], r["prompt_variant"])
            hits[key][r["instance_id"]] |= str(r["is_hit"]).strip().lower() == "true"
    out: list[tuple[str, str, int, int]] = []
    for key in sorted(hits):
        h = sum(1 for i in subset if hits[key].get(i, False))
        out.append((key[0], key[1], h, len(subset)))
    return out


def cmd_report(csv_path: Path, output_dir: Path, variant_results: Path | None = None) -> None:
    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    filled = [r for r in rows if (r.get("verdict") or "").strip() in VERDICTS]
    unfilled = len(rows) - len(filled)
    counts = {v: sum(1 for r in filled if r["verdict"].strip() == v) for v in VERDICTS}
    n_sites = len(filled)
    site_validity = (counts["bug"] / n_sites) if n_sites else 0.0
    s_lo, s_hi = _wilson(counts["bug"], n_sites)

    by_inst: dict[str, list[str]] = defaultdict(list)
    for r in filled:
        by_inst[r["instance_id"]].append(r["verdict"].strip())
    n_inst = len(by_inst)
    bug_instances = sorted(i for i, vs in by_inst.items() if "bug" in vs)
    inst_valid = len(bug_instances)
    n_invalid = n_inst - inst_valid
    inv_lo, inv_hi = _wilson(n_invalid, n_inst)

    lines = [
        "# Oracle construct-validity report\n",
        "LLM-assisted draft, human-confirmed. Audit of a 30-instance stratified "
        "sample from the n=100 study; this is construct-validity evidence on the "
        "sample, not a proportion estimate over full SWE-bench Lite.\n",
        f"Sites audited: {n_sites}  (unfilled rows skipped: {unfilled})\n",
        "## Site-level\n",
        f"- bug: {counts['bug']}",
        f"- related: {counts['related']}",
        f"- unrelated: {counts['unrelated']}",
        f"- site-level oracle validity (bug-site fraction): "
        f"{counts['bug']}/{n_sites} = {site_validity:.3f} "
        f"Wilson95 [{s_lo:.3f}, {s_hi:.3f}]\n",
        "## Instance-level\n",
        f"- instances audited: {n_inst}",
        f"- with at least one bug site: {inst_valid}/{n_inst} = {inst_valid / n_inst:.3f}",
        f"- with no bug site: {n_invalid}/{n_inst} = {n_invalid / n_inst:.3f} "
        f"Wilson95 [{inv_lo:.3f}, {inv_hi:.3f}]\n",
    ]
    if variant_results is not None and variant_results.exists():
        subset = set(bug_instances)
        lines.append(
            f"## Audited-subset sensitivity ({len(subset)} confirmed bug instances)\n"
        )
        lines.append(
            "Instance hit rate restricted to the confirmed bug subset. This is a "
            "sensitivity check on a small subset, NOT a replacement for the n=100 "
            "headline.\n"
        )
        for rev, var, h, ntot in _subset_hit_rates(variant_results, subset):
            lines.append(f"- {rev} {var}: {h}/{ntot} = {h / ntot:.3f}")
        lines.append("")

    out = output_dir / "oracle_validity_report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out}")
    print(
        f"site-level validity {site_validity:.3f} [{s_lo:.3f},{s_hi:.3f}] "
        f"({counts['bug']}/{n_sites}); no-bug-site {n_invalid}/{n_inst} "
        f"[{inv_lo:.3f},{inv_hi:.3f}]"
    )
    if unfilled:
        print(f"note: {unfilled} site rows have no verdict yet")


def main() -> None:
    p = argparse.ArgumentParser(description="Oracle construct-validity audit.")
    sub = p.add_subparsers(dest="cmd", required=True)

    ps = sub.add_parser("sample", help="Sample instances and emit annotation cards.")
    ps.add_argument("--n", type=int, default=30)
    ps.add_argument("--seed", type=int, default=7)
    ps.add_argument("--output-dir", default=str(N100_DIR))

    pr = sub.add_parser("report", help="Summarise a filled verdict CSV.")
    pr.add_argument("--csv", default=str(N100_DIR / "oracle_validity_template.csv"))
    pr.add_argument("--output-dir", default=str(N100_DIR))
    pr.add_argument(
        "--variant-results",
        default=str(N100_DIR / "variant_results.csv"),
        help="If present, add an audited-subset hit-rate sensitivity table.",
    )

    args = p.parse_args()
    if args.cmd == "sample":
        cmd_sample(args.n, args.seed, Path(args.output_dir))
    elif args.cmd == "report":
        vr = Path(args.variant_results) if args.variant_results else None
        cmd_report(Path(args.csv), Path(args.output_dir), vr)


if __name__ == "__main__":
    main()
