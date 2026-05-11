"""E.0.5 oracle index reconstruction.

Reconstructs the per-instance oracle site index that Round 1 used,
re-running the existing ``build_oracle_sites`` on the exact same 20-instance
sample (seed=42). Cross-checks the resulting site IDs against the
``matched_oracle_site_id`` column in Round 1's results.csv so we have
explicit evidence the reconstruction is consistent with Round 1.

Writes:
  outputs/round2/oracle_index.json
  outputs/round2/oracle_reconstruction_log.md

Determinism check: runs ``build_oracle_sites`` twice on each patch and
compares; halts loudly if any disagreement is found.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pandas as pd

from ..data.loader import Instance, load_instances
from ..data.oracle import OracleSite, build_oracle_sites, is_test_file


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUND2_DIR = PROJECT_ROOT / "outputs" / "round2"


def _site_to_dict(s: OracleSite) -> dict[str, Any]:
    return {
        "site_id": s.site_id,
        "file": s.file,
        "line_start": s.line_start,
        "line_end": s.line_end,
        "is_test_file": is_test_file(s.file),
    }


def _patch_fingerprint(patch_text: str) -> str:
    return hashlib.sha256(patch_text.encode("utf-8")).hexdigest()


def reconstruct() -> tuple[dict, list[str]]:
    instances: list[Instance] = load_instances(
        n=20, seed=42, dataset="princeton-nlp/SWE-bench_Lite", split="test"
    )

    per_instance: dict[str, dict[str, Any]] = {}
    determinism_failures: list[str] = []

    for inst in instances:
        sites_a = build_oracle_sites(inst.patch, strict_mode=False)
        sites_b = build_oracle_sites(inst.patch, strict_mode=False)
        if sites_a != sites_b:
            determinism_failures.append(inst.instance_id)
        per_instance[inst.instance_id] = {
            "instance_id": inst.instance_id,
            "repo": inst.repo,
            "base_commit": inst.base_commit,
            "patch_sha256": _patch_fingerprint(inst.patch),
            "n_sites": len(sites_a),
            "sites": [_site_to_dict(s) for s in sites_a],
            "oracle_files": sorted({s.file for s in sites_a}),
        }

    return (
        {
            "dataset": "princeton-nlp/SWE-bench_Lite",
            "split": "test",
            "seed": 42,
            "n_requested": 20,
            "strict_oracle_mode": False,
            "instances": per_instance,
        },
        determinism_failures,
    )


def cross_check_with_results_csv(index: dict) -> dict[str, Any]:
    """For each row in results.csv with a non-empty matched_oracle_site_id,
    assert that (instance_id, site_id) exists in the reconstructed index
    and that the row's (file, line_start, line_end) is consistent with the
    matcher under tolerance=3.
    """
    df = pd.read_csv(PROJECT_ROOT / "outputs" / "results.csv")
    df["matched_oracle_site_id"] = df["matched_oracle_site_id"].fillna("")
    hit_rows = df[df["matched_oracle_site_id"] != ""]
    findings: list[dict[str, Any]] = []
    for _, row in hit_rows.iterrows():
        iid = row["instance_id"]
        site_id = row["matched_oracle_site_id"]
        inst = index["instances"].get(iid)
        if inst is None:
            findings.append({"instance_id": iid, "site_id": site_id, "issue": "instance not in reconstructed index"})
            continue
        site = next((s for s in inst["sites"] if s["site_id"] == site_id), None)
        if site is None:
            findings.append({"instance_id": iid, "site_id": site_id, "issue": "site_id not found in reconstructed sites"})
            continue
        # Sanity-check the hit holds under tolerance=3.
        tol = int(row["tolerance"])
        c_start = int(row["line_start"])
        c_end = int(row["line_end"])
        s_start = site["line_start"] - tol
        s_end = site["line_end"] + tol
        overlap = (c_end >= s_start) and (c_start <= s_end)
        same_file = row["file"] == site["file"]
        if not (overlap and same_file):
            findings.append(
                {
                    "instance_id": iid,
                    "site_id": site_id,
                    "issue": "hit recomputation disagrees with results.csv",
                    "comment_file": row["file"],
                    "comment_lines": [c_start, c_end],
                    "site_file": site["file"],
                    "site_lines": [site["line_start"], site["line_end"]],
                    "tolerance": tol,
                }
            )
    return {
        "n_hit_rows": int(len(hit_rows)),
        "n_disagreements": len(findings),
        "disagreements": findings,
    }


def write_log(
    index: dict,
    determinism_failures: list[str],
    cross_check: dict,
) -> str:
    lines: list[str] = []
    lines.append("# E.0.5 Oracle reconstruction log\n")
    lines.append("## Resolution path used\n")
    lines.append(
        "Path **(3) fresh HF-dataset patch parse**: the existing "
        "``swe_review_bench.data.loader.load_instances(n=20, seed=42)`` was "
        "called and each instance's ``patch`` field was fed to "
        "``swe_review_bench.data.oracle.build_oracle_sites(strict_mode=False)``. "
        "No Round 1 cache file holding oracle structures was found in ``.cache/``; "
        "``.cache/llm/`` contains only per-reviewer-call payloads, and "
        "``.cache/repos/`` only holds shallow git clones.\n"
    )
    lines.append(
        "Because the oracle reconstruction reuses the same deterministic loader, "
        "sampling seed, dataset revision, and parsing function as Round 1, the "
        "resulting site IDs and ranges are expected to be byte-identical to those "
        "Round 1 produced. The cross-check below verifies this against the "
        "``matched_oracle_site_id`` column in ``results.csv``.\n"
    )
    lines.append("## Determinism check\n")
    if determinism_failures:
        lines.append(
            f"FAIL: ``build_oracle_sites`` returned different sites on two "
            f"calls for instances: {determinism_failures}.\n"
        )
    else:
        lines.append(
            "OK: ``build_oracle_sites`` produced identical results across two "
            "consecutive calls on every instance.\n"
        )
    lines.append("## Cross-check vs Round 1 results.csv\n")
    lines.append(
        f"Hit rows in ``outputs/results.csv``: {cross_check['n_hit_rows']}\n\n"
        f"Disagreements between reconstructed sites and Round 1 hit rows: "
        f"{cross_check['n_disagreements']}\n"
    )
    if cross_check["disagreements"]:
        lines.append("\n### Disagreement details\n")
        for d in cross_check["disagreements"]:
            lines.append(f"- {d}\n")
    else:
        lines.append(
            "\nOK: every Round 1 hit row maps to a reconstructed site with "
            "overlap under the recorded tolerance (3).\n"
        )
    lines.append("## Instance summary\n")
    lines.append("| instance_id | repo | n_sites | n_oracle_files | patch_sha256[:12] |\n")
    lines.append("|---|---|---:|---:|---|\n")
    for iid, inst in index["instances"].items():
        lines.append(
            f"| {iid} | {inst['repo']} | {inst['n_sites']} | "
            f"{len(inst['oracle_files'])} | {inst['patch_sha256'][:12]} |\n"
        )
    return "".join(lines)


def main() -> None:
    ROUND2_DIR.mkdir(parents=True, exist_ok=True)
    index, determinism_failures = reconstruct()
    cross_check = cross_check_with_results_csv(index)

    out_index = ROUND2_DIR / "oracle_index.json"
    out_index.write_text(
        json.dumps(index, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {out_index} ({len(index['instances'])} instances)")

    log = write_log(index, determinism_failures, cross_check)
    out_log = ROUND2_DIR / "oracle_reconstruction_log.md"
    out_log.write_text(log, encoding="utf-8")
    print(f"wrote {out_log}")

    if determinism_failures:
        raise SystemExit(
            f"HALT: oracle reconstruction not deterministic for "
            f"{determinism_failures}. Cannot proceed to E.1."
        )
    if cross_check["n_disagreements"]:
        print(
            f"WARNING: {cross_check['n_disagreements']} cross-check "
            f"disagreements (see {out_log.name})."
        )


if __name__ == "__main__":
    main()
