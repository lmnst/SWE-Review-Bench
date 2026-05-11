"""E.0 baseline integrity manifest.

Computes sha256 / size / mtime for the five frozen Round 1 artefacts so
that any later accidental modification is detectable.

Run:
    python -m swe_review_bench.diagnostics.baseline_manifest
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROUND1_FILES: tuple[str, ...] = (
    "outputs/results.csv",
    "outputs/summary.csv",
    "outputs/hit_fp_bar_chart.png",
    "outputs/run_meta.json",
    "outputs/run_log.txt",
)


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _iso_utc(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_manifest(project_root: Path) -> dict:
    entries: list[dict] = []
    missing: list[str] = []
    for rel in ROUND1_FILES:
        p = project_root / rel
        if not p.is_file():
            missing.append(rel)
            entries.append(
                {
                    "path": rel,
                    "exists": False,
                    "sha256": None,
                    "file_size": None,
                    "mtime_utc": None,
                }
            )
            continue
        st = p.stat()
        entries.append(
            {
                "path": rel,
                "exists": True,
                "sha256": _sha256_file(p),
                "file_size": st.st_size,
                "mtime_utc": _iso_utc(st.st_mtime),
            }
        )
    return {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project_root": str(project_root),
        "files": entries,
        "missing": missing,
    }


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    manifest = build_manifest(project_root)
    out_path = project_root / "outputs" / "round2" / "baseline_manifest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"wrote {out_path}")
    if manifest["missing"]:
        print(f"WARNING: missing files: {manifest['missing']}")


if __name__ == "__main__":
    main()
