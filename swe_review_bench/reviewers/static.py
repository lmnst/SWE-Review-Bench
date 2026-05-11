"""Static-analysis reviewer: union of filtered Ruff and Pylint warnings.

Filters applied (per the agreed MVP scope):

* **Ruff**: ``--select F,E9,B,A --no-fix --output-format=json``
* **Pylint**: ``--disable=C,R,I,import-error,no-name-in-module
  --output-format=json``

Both tools run via ``sys.executable -m <tool>`` so they always use the
project's venv, regardless of shell PATH. Each is fed a tempfile mirroring
the reviewer input (linters take file paths, not stdin, reliably across
versions). Non-Python files return an empty comment list and a single
``UnsupportedFileType`` meta marker -- this reviewer is intentionally
Python-only.

Severity mapping (used by ``precision@k`` only; not by hit/FP):

* Ruff ``F*`` / ``E9*`` / Pylint ``E*`` / Pylint ``F*``  -> high
* Ruff ``B*`` / Pylint ``W*``                            -> medium
* Ruff ``A*`` and everything else                        -> low
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from ..config import Config
from .base import Comment, ReviewMeta, ReviewResult, Reviewer, ReviewerInput


_RUFF_ARGS = ["--select", "F,E9,B,A", "--no-fix", "--output-format=json"]
_PYLINT_ARGS = [
    "--disable=C,R,I,import-error,no-name-in-module",
    "--output-format=json",
    "--score=no",
]


class StaticReviewer(Reviewer):
    """Union of filtered Ruff + Pylint warnings."""

    name = "static"

    def __init__(
        self,
        config: Config,
        *,
        max_comments_per_file: int = 20,
        ruff_timeout: int = 60,
        pylint_timeout: int = 120,
    ) -> None:
        self.config = config
        self.max_comments_per_file = max_comments_per_file
        self.ruff_timeout = ruff_timeout
        self.pylint_timeout = pylint_timeout

    def review(self, inp: ReviewerInput) -> ReviewResult:
        if not inp.file_path.endswith(".py"):
            return ReviewResult(
                comments=[],
                meta=ReviewMeta(
                    latency_seconds=0.0,
                    skipped_reason="UnsupportedFileType",
                ),
            )

        start = time.monotonic()
        # Write content to a tempfile with a ``.py`` suffix. Use
        # ``newline=""`` so Windows text mode does NOT translate '\n' to
        # '\r\n' on write -- otherwise a file that already has CRLF
        # endings becomes '\r\r\n' and pylint flags every line with
        # E2511 (stray carriage-return).
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8", newline=""
        ) as fh:
            fh.write(inp.file_content)
            tmp_path = Path(fh.name)
        try:
            ruff_comments = self._run_ruff(tmp_path, original_path=inp.file_path)
            pylint_comments = self._run_pylint(tmp_path, original_path=inp.file_path)
        finally:
            tmp_path.unlink(missing_ok=True)
        latency = time.monotonic() - start

        merged = self._merge(ruff_comments, pylint_comments)
        return ReviewResult(
            comments=merged,
            meta=ReviewMeta(latency_seconds=latency),
        )

    # ----- ruff --------------------------------------------------------

    def _run_ruff(self, tmp_path: Path, *, original_path: str) -> list[Comment]:
        cmd = [sys.executable, "-m", "ruff", "check", *_RUFF_ARGS, str(tmp_path)]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.ruff_timeout
            )
        except subprocess.TimeoutExpired:
            return []
        # Ruff exits 0 on clean, 1 when issues found, >1 on tool errors.
        if proc.returncode not in (0, 1):
            return []
        try:
            items = json.loads(proc.stdout or "[]")
        except json.JSONDecodeError:
            return []
        out: list[Comment] = []
        for it in items:
            code = it.get("code") or ""
            msg = it.get("message") or ""
            loc = it.get("location") or {}
            end = it.get("end_location") or loc
            row = loc.get("row")
            end_row = end.get("row") or row
            if not row:
                continue
            try:
                out.append(
                    Comment(
                        file=original_path,
                        line_start=int(row),
                        line_end=max(int(row), int(end_row)),
                        severity=_ruff_severity(code),
                        message=f"{code}: {msg}".strip(": "),
                    )
                )
            except Exception:  # noqa: BLE001
                continue
        return out

    # ----- pylint ------------------------------------------------------

    def _run_pylint(self, tmp_path: Path, *, original_path: str) -> list[Comment]:
        cmd = [sys.executable, "-m", "pylint", *_PYLINT_ARGS, str(tmp_path)]
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=self.pylint_timeout
            )
        except subprocess.TimeoutExpired:
            return []
        # Pylint exit code is a bitmask -- never trust the returncode for
        # presence/absence of issues; only trust the JSON body.
        try:
            items = json.loads(proc.stdout or "[]")
        except json.JSONDecodeError:
            return []
        out: list[Comment] = []
        for it in items:
            msg_id = it.get("message-id") or it.get("symbol") or ""
            msg = it.get("message") or ""
            row = it.get("line")
            end_row = it.get("endLine") or row
            if not row:
                continue
            try:
                out.append(
                    Comment(
                        file=original_path,
                        line_start=int(row),
                        line_end=max(int(row), int(end_row)),
                        severity=_pylint_severity(msg_id, it.get("type") or ""),
                        message=f"{msg_id}: {msg}".strip(": "),
                    )
                )
            except Exception:  # noqa: BLE001
                continue
        return out

    # ----- merge -------------------------------------------------------

    def _merge(
        self, ruff_comments: list[Comment], pylint_comments: list[Comment]
    ) -> list[Comment]:
        """Dedupe by ``(line_start, rule_id)`` then sort and cap."""
        seen: set[tuple[int, str]] = set()
        merged: list[Comment] = []
        for c in [*ruff_comments, *pylint_comments]:
            rule_id = c.message.split(":", 1)[0].strip()
            key = (c.line_start, rule_id)
            if key in seen:
                continue
            seen.add(key)
            merged.append(c)
        merged.sort(key=lambda c: (_severity_rank(c.severity), c.line_start))
        return merged[: self.max_comments_per_file]


# ---------------------------------------------------------------------------
# Severity helpers (precision@k ordering only; not hit/FP).
# ---------------------------------------------------------------------------


def _ruff_severity(code: str) -> str:
    if not code:
        return "low"
    if code.startswith("F") or code.startswith("E9"):
        return "high"
    if code.startswith("B"):
        return "medium"
    return "low"


def _pylint_severity(message_id: str, ptype: str) -> str:
    if message_id.startswith(("E", "F")) or ptype in {"error", "fatal"}:
        return "high"
    if message_id.startswith("W") or ptype == "warning":
        return "medium"
    return "low"


def _severity_rank(sev: str) -> int:
    # Sort descending: high first, then medium, then low.
    return {"high": 0, "medium": 1, "low": 2}.get(sev, 3)
