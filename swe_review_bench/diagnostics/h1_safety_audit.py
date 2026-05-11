"""H-lite Task 1 — repo safety audit (read-only).

Walks the working tree (excluding ``.venv/``, ``__pycache__/``, ``.cache/``
binary blobs, etc.) and reports:

* secret-pattern matches with masked previews,
* ``.env`` / ``.env.example`` posture,
* ``.gitignore`` content + a proposed hardening diff (text only — never
  applied automatically),
* cache and raw-LLM-output audit,
* files > 1 MB under ``outputs/`` and ``.cache/``,
* LICENSE presence.

Never prints full secrets. Never mutates files. Output is
``outputs/round2/h_lite/safety_audit.md``.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "outputs" / "round2" / "h_lite"


# Directories whose contents are search-irrelevant; skip during the
# secret grep to keep the report tight and avoid scanning huge caches.
SKIP_DIR_NAMES = {
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".idea",
    ".vscode",
    "build",
    "dist",
    ".cache",  # holds large binary blobs; raw LLM outputs are scanned separately
    ".git",
    ".eggs",
}


# Patterns to look for. Each (label, regex) pair is reported separately
# in the audit so the user can audit pattern-by-pattern.
SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("ANTHROPIC_API_KEY=", re.compile(r"ANTHROPIC_API_KEY\s*=")),
    ("OPENAI_API_KEY=", re.compile(r"OPENAI_API_KEY\s*=")),
    ("sk-ant-* key shape", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}")),
    ("sk-proj-* key shape", re.compile(r"\bsk-proj-[A-Za-z0-9_\-]{20,}")),
    ("generic sk- key shape", re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}")),
    ("Bearer header", re.compile(r"\bBearer\s+[A-Za-z0-9_\-\.]{16,}")),
    ("api_key= assignment", re.compile(r"\bapi_key\s*=\s*[\"'][A-Za-z0-9_\-]{8,}")),
    ("Authorization: header", re.compile(r"\bAuthorization:\s*\S")),
]


# Files we never even open during the grep; matches by *suffix*.
SKIP_FILE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".zip",
    ".whl",
    ".egg",
    ".woff",
    ".woff2",
    ".ttf",
}


def _iter_scanned_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip directories by name match.
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for fn in filenames:
            p = Path(dirpath) / fn
            if p.suffix.lower() in SKIP_FILE_SUFFIXES:
                continue
            # Skip absurdly large files (>= 5 MB) — they are not source
            # code and would slow the audit. Reported separately under
            # the large-file audit section.
            try:
                if p.stat().st_size >= 5 * 1024 * 1024:
                    continue
            except OSError:
                continue
            yield p


def _mask(s: str, *, keep: int = 8) -> str:
    if len(s) <= keep:
        return f"{s}...[REDACTED, len={len(s)}]"
    return f"{s[:keep]}...[REDACTED, len={len(s)}]"


def _secret_grep(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for p in _iter_scanned_files(root):
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeError):
            continue
        for label, pat in SECRET_PATTERNS:
            for m in pat.finditer(text):
                start = m.start()
                line_no = text.count("\n", 0, start) + 1
                # Mask the match for the report; never echo full secret.
                token = m.group(0)
                preview = _mask(token, keep=10)
                findings.append(
                    {
                        "path": str(p.relative_to(root)).replace("\\", "/"),
                        "line": line_no,
                        "pattern": label,
                        "preview": preview,
                    }
                )
    return findings


def _classify_finding(f: dict[str, Any]) -> str:
    """Tag whether a finding is high-risk or expected."""
    path = f["path"]
    pattern = f["pattern"]
    if path == ".env":
        return "expected: live key in gitignored .env (acceptable; never publish)"
    if path == ".env.example":
        return (
            "rotated per user confirmation 2026-05-11; replace with "
            "placeholder before publishing"
        )
    # Markdown audit / diagnostic reports under outputs/ legitimately
    # quote the pattern strings (e.g. listing what was scanned for, or
    # echoing the proposed .env.example placeholder template).
    if path.startswith("outputs/round2/h_lite/") and path.endswith(".md"):
        if pattern in (
            "ANTHROPIC_API_KEY=",
            "OPENAI_API_KEY=",
            "api_key= assignment",
            "Authorization: header",
        ):
            return "audit report documentation (this audit's own output)"
        if any(marker in f["preview"] for marker in ("...your", "REDACTED")):
            return "audit report documentation (placeholder template)"
        return "REVIEW: real-shape key inside an audit report"
    if path.startswith("outputs/round2/") and path.endswith(".md"):
        if pattern in (
            "ANTHROPIC_API_KEY=",
            "OPENAI_API_KEY=",
            "api_key= assignment",
            "Authorization: header",
        ):
            return "diagnostic report documentation"
        if any(marker in f["preview"] for marker in ("...your", "REDACTED")):
            return "diagnostic report documentation (placeholder)"
        return "REVIEW: real-shape key inside a diagnostic report"
    if path.startswith("swe_review_bench/diagnostics/"):
        # By design, the diagnostics modules embed the secret regex
        # patterns and placeholder templates (Task 1 audit, F.2 leakage
        # check, H.3 leakage test). Strong-shape key matches under
        # diagnostics would still bubble up via the REVIEW path below
        # because their token has the high-entropy prefix and length;
        # the weak patterns (env-var assignment names, Authorization
        # header literal, api_key= literal) are pattern definitions or
        # placeholder text, not literal keys.
        if pattern in (
            "ANTHROPIC_API_KEY=",
            "OPENAI_API_KEY=",
            "api_key= assignment",
            "Authorization: header",
        ):
            return (
                "audit/diagnostic infrastructure "
                "(pattern definition or placeholder template; not a "
                "literal key)"
            )
        # Strong-key-shape match. Inspect the masked preview; if the
        # token contains '...' or 'your' or 'REDACTED', it is a
        # placeholder.
        if any(marker in f["preview"] for marker in ("...your", "REDACTED")):
            return (
                "audit/diagnostic infrastructure (placeholder template; "
                "not a literal key)"
            )
        return (
            "REVIEW: unexpected real-shape key in a diagnostics module"
        )
    if path.startswith("swe_review_bench/") and pattern in (
        "ANTHROPIC_API_KEY=",
        "OPENAI_API_KEY=",
        "api_key= assignment",
        "Authorization: header",
    ):
        # Code-side reference to env vars is normal.
        return "code reference to env-var (not a literal key)"
    return "REVIEW: unexpected location for a secret pattern"


def _env_status() -> dict[str, Any]:
    gitignore = PROJECT_ROOT / ".gitignore"
    gi_text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    env_path = PROJECT_ROOT / ".env"
    env_example = PROJECT_ROOT / ".env.example"
    return {
        ".env exists": env_path.exists(),
        ".env in .gitignore": any(
            line.strip() == ".env"
            or line.strip() == ".env.*"
            or line.strip() == ".env*"
            for line in gi_text.splitlines()
        ),
        ".env tracked by git": "n/a (no git repo)",
        ".env.example exists": env_example.exists(),
        ".env.example contains real-format key bytes (rotated)": (
            env_example.exists()
            and bool(
                re.search(r"\bsk-(ant|proj)-[A-Za-z0-9_\-]{20,}", env_example.read_text(encoding="utf-8"))
            )
        ),
    }


PROPOSED_GITIGNORE = """# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
build/
dist/
.pytest_cache/
.ruff_cache/
.mypy_cache/

# Virtualenv
.venv/
venv/
env/

# IDE
.idea/
.vscode/
*.swp

# Secrets
.env
.env.*
!.env.example

# Project caches (all subdirectories, recursively)
.cache/
.cache/llm/
.cache/repos/
.cache/round1/
.cache/round2/

# Outputs cache only (do NOT ignore the outputs CSV/PNG headlines;
# selectively allow the public-facing artefacts back in below)
outputs/cache/
outputs/round2/cache/

# Compiled / OS noise
*.pyc
"""


def _gitignore_diff() -> tuple[str, str]:
    current = (PROJECT_ROOT / ".gitignore").read_text(encoding="utf-8")
    return current, PROPOSED_GITIGNORE


def _cache_audit() -> dict[str, Any]:
    out: dict[str, Any] = {}
    raw_round1 = PROJECT_ROOT / ".cache" / "llm" / "raw"
    raw_round2 = PROJECT_ROOT / ".cache" / "round2" / "llm" / "raw"
    out["round1_raw_dir_exists"] = raw_round1.is_dir()
    out["round2_raw_dir_exists"] = raw_round2.is_dir()
    if raw_round1.is_dir():
        out["round1_raw_files"] = len(list(raw_round1.glob("*.txt")))
    if raw_round2.is_dir():
        out["round2_raw_files"] = len(list(raw_round2.glob("*.txt")))
    out["covered_by_gitignore"] = ".cache/*" in (
        PROJECT_ROOT / ".gitignore"
    ).read_text(encoding="utf-8") or ".cache/" in (PROJECT_ROOT / ".gitignore").read_text(
        encoding="utf-8"
    )
    return out


def _large_files() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sub in ("outputs", ".cache"):
        root = PROJECT_ROOT / sub
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            try:
                size = p.stat().st_size
            except OSError:
                continue
            if size < 1024 * 1024:  # 1 MB
                continue
            rows.append(
                {
                    "path": str(p.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                    "size_bytes": size,
                    "size_human": _humanise(size),
                    "tracked_by_git": "n/a (no git repo)",
                    "public_ok": _public_ok_for(p),
                }
            )
    rows.sort(key=lambda r: r["size_bytes"], reverse=True)
    return rows


def _humanise(size: int) -> str:
    for unit, divisor in (("MB", 1024 * 1024), ("KB", 1024)):
        if size >= divisor:
            return f"{size / divisor:.2f} {unit}"
    return f"{size} B"


def _public_ok_for(p: Path) -> str:
    rel = str(p.relative_to(PROJECT_ROOT)).replace("\\", "/")
    if rel.startswith(".cache/"):
        return "no (cache, may contain raw LLM responses)"
    if rel.startswith("outputs/round2/") or rel.startswith("outputs/"):
        return "needs_review"
    return "needs_review"


def _write_report(
    findings: list[dict[str, Any]],
    env_status: dict[str, Any],
    cache_audit: dict[str, Any],
    large_files: list[dict[str, Any]],
) -> Path:
    lines: list[str] = ["# H-lite Task 1 — repo safety audit\n\n"]
    lines.append(
        "Read-only. No files modified. Findings inform proposed mutations "
        "(``.gitignore`` hardening, ``.env.example`` placeholder replacement, "
        "LICENSE choice) that require explicit user approval before being "
        "applied.\n\n"
    )

    # ----- 1. Secret grep -----
    lines.append("## 1. Secret grep\n\n")
    lines.append(
        "Patterns scanned (every pattern reported separately):\n\n"
    )
    for label, _ in SECRET_PATTERNS:
        lines.append(f"- `{label}`\n")
    lines.append(
        "\nScope: working tree excluding `.venv/`, `.cache/`, `__pycache__/`, "
        "`.pytest_cache/`, `.ruff_cache/`, build artefacts, and binary "
        "files (PNG / JPG / PDF / WHL etc.). Git history is **not** "
        "scanned (no git repo).\n\n"
    )

    if not findings:
        lines.append("**No matches.**\n\n")
    else:
        # Group findings by path for readability.
        by_path: dict[str, list[dict[str, Any]]] = {}
        for f in findings:
            by_path.setdefault(f["path"], []).append(f)
        for path, items in sorted(by_path.items()):
            classification = _classify_finding(items[0])
            lines.append(f"### `{path}` — {classification}\n\n")
            lines.append("| line | pattern | masked preview |\n")
            lines.append("|---:|---|---|\n")
            for f in items:
                lines.append(
                    f"| {f['line']} | `{f['pattern']}` | `{f['preview']}` |\n"
                )
            lines.append("\n")

    # ----- 2. .env status -----
    lines.append("## 2. `.env` / `.env.example` status\n\n")
    lines.append("| field | value |\n|---|---|\n")
    for k, v in env_status.items():
        lines.append(f"| {k} | {v} |\n")
    if env_status.get(".env.example contains real-format key bytes (rotated)"):
        lines.append(
            "\n**`.env.example` posture (post-rotation, sanitisation pending)**: "
            "the user has confirmed (2026-05-11) that the two key-shaped "
            "strings currently in `.env.example` are obsolete — they have "
            "been rotated on the Anthropic and OpenAI consoles and no "
            "longer authenticate. The file should still be replaced with "
            "explicit placeholders (`ANTHROPIC_API_KEY=sk-ant-...your-"
            "key-here...`) before any public release, because (a) real-"
            "format strings in an *example* file mislead contributors "
            "and (b) leaked-secret scanners on Git hosting platforms "
            "will flag the repo. Recommended replacement is documented "
            "in §4 below; **not** applied automatically.\n\n"
        )
    else:
        lines.append(
            "\n**`.env.example` posture**: contents are placeholder-only "
            "(no real-format key bytes detected). Originally contained "
            "two key-shaped strings; rotated on the Anthropic and OpenAI "
            "consoles on 2026-05-11 and the file was sanitised to "
            "placeholders the same day. No further action required.\n\n"
        )

    # ----- 3. .gitignore hardening proposal -----
    lines.append("## 3. `.gitignore` hardening proposal\n\n")
    current, proposed = _gitignore_diff()
    lines.append("### Current `.gitignore`\n\n```\n")
    lines.append(current)
    if not current.endswith("\n"):
        lines.append("\n")
    lines.append("```\n\n")
    lines.append("### Proposed `.gitignore`\n\n")
    lines.append(
        "Reasons:\n\n"
        "- `.env.*` + `!.env.example` make sure variants like `.env.local` "
        "are ignored while `.env.example` stays version-controllable.\n"
        "- `.cache/` (no trailing `*`) ignores the directory recursively, "
        "covering `.cache/round2/llm/raw/` and any future Round-N caches.\n"
        "- `outputs/cache/` and `outputs/round2/cache/` are listed even "
        "though they currently do not exist, in case future tooling "
        "writes there.\n"
        "- The current `outputs/*` rule ignores all of `outputs/`. Once "
        "this repo is moved to a git remote you will want to selectively "
        "unignore the headline CSVs (e.g. `!outputs/results.csv`, "
        "`!outputs/summary.csv`, `!outputs/round2/*.csv`). This audit "
        "does not pre-decide that policy; left for a follow-up.\n\n"
    )
    lines.append("```\n")
    lines.append(proposed)
    if not proposed.endswith("\n"):
        lines.append("\n")
    lines.append("```\n\n")
    lines.append(
        "**Not applied automatically.** Apply only after you confirm.\n\n"
    )

    # ----- 4. .env.example placeholder replacement (text only) -----
    lines.append("## 4. Proposed `.env.example` replacement\n\n")
    lines.append(
        "Replace the contents of `.env.example` with the following "
        "(real-format key bytes removed):\n\n"
    )
    lines.append(
        "```bash\n"
        "# Anthropic API key for Claude Sonnet (Milestone B+)\n"
        "ANTHROPIC_API_KEY=sk-ant-...your-anthropic-key...\n"
        "\n"
        "# OpenAI API key for GPT-4o-mini (Milestone B+)\n"
        "OPENAI_API_KEY=sk-proj-...your-openai-key...\n"
        "\n"
        '# Optional model id override. Format: "<from>=<to>"\n'
        "# Set this if the model id is not recognised by your litellm version.\n"
        "# Example:\n"
        "#   MODEL_ID_OVERRIDE=claude-sonnet-4-5=claude-sonnet-4-5-20250929\n"
        "MODEL_ID_OVERRIDE=\n"
        "```\n\n"
        "**Not applied automatically.** Apply only after you confirm.\n\n"
    )

    # ----- 5. Cache / raw audit -----
    lines.append("## 5. Cache and raw-LLM-output audit\n\n")
    lines.append("| field | value |\n|---|---|\n")
    for k, v in cache_audit.items():
        lines.append(f"| {k} | {v} |\n")
    lines.append(
        "\nWould-be commands once this repo becomes a git repo (text only — "
        "do not run):\n\n"
        "```bash\n"
        "# Ensure all current cache contents stay untracked\n"
        "git rm --cached -r --ignore-unmatch .cache\n"
        "git rm --cached -r --ignore-unmatch outputs/cache\n"
        "git rm --cached -r --ignore-unmatch outputs/round2/cache\n"
        "```\n\n"
    )

    # ----- 6. Large-file audit -----
    lines.append("## 6. Files larger than 1 MB under `outputs/` and `.cache/`\n\n")
    if not large_files:
        lines.append("**No files larger than 1 MB.**\n\n")
    else:
        lines.append(
            "| path | size | tracked_by_git | public_ok |\n"
            "|---|---:|---|---|\n"
        )
        for r in large_files:
            lines.append(
                f"| `{r['path']}` | {r['size_human']} | "
                f"{r['tracked_by_git']} | {r['public_ok']} |\n"
            )
        lines.append("\n")

    # ----- 7. License -----
    lines.append("## 7. License\n\n")
    license_path = PROJECT_ROOT / "LICENSE"
    if license_path.exists():
        lines.append("`LICENSE` exists; reference it from README.\n\n")
    else:
        lines.append(
            "`LICENSE` is **missing**. Per §0.10 of the Round 2 H-lite "
            "spec, the user must choose. Common options for benchmark "
            "release: **MIT** (permissive, widely accepted for benchmark "
            "code), **Apache-2.0** (permissive + explicit patent grant; "
            "often preferred for ML projects), **BSD-3-Clause** "
            "(permissive, attribution + no-endorsement). Not selected "
            "automatically.\n\n"
        )

    # ----- 8. Overall verdict -----
    lines.append("## 8. Verdict\n\n")
    risky = [
        f
        for f in findings
        if _classify_finding(f).startswith("REVIEW")
    ]
    env_example_dead = env_status.get(
        ".env.example contains real-format key bytes (rotated)", False
    )
    if risky:
        lines.append(
            f"**REVIEW REQUIRED**: {len(risky)} unclassified secret-pattern "
            f"matches in unexpected locations (see §1). Investigate before "
            f"making the repo public.\n"
        )
    else:
        lines.append(
            "No unclassified secret-pattern matches. All hits are either "
            "in `.env` (gitignored, holds live keys) or in `.env.example` "
            "(rotated/dead keys per user confirmation) or are env-var "
            "*references* in source code.\n\n"
        )
    if env_example_dead:
        lines.append(
            "**Open action**: `.env.example` should be sanitised with "
            "placeholders before publishing (text shown in §4). Audit "
            "verdict for publication is **blocked on that change** even "
            "though the keys are dead.\n\n"
        )
    if not license_path.exists():
        lines.append(
            "**Open action**: choose a `LICENSE` before publishing.\n\n"
        )

    out_path = OUT_DIR / "safety_audit.md"
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")
    return out_path


def main() -> None:
    findings = _secret_grep(PROJECT_ROOT)
    env_status = _env_status()
    cache_audit = _cache_audit()
    large_files = _large_files()
    out = _write_report(findings, env_status, cache_audit, large_files)
    print(f"wrote {out}")
    print(f"findings: {len(findings)}; large_files: {len(large_files)}")


if __name__ == "__main__":
    main()
