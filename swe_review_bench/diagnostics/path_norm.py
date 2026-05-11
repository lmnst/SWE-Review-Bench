"""Shared path normalisation for the Round 2 diagnostics.

Applied symmetrically to comment paths (from results.csv) and oracle file
paths (from oracle_index.json) so any mismatch is purely a content
difference, not a normalisation artefact.

Rules (no case folding -- POSIX repos are case-sensitive):
    1. Replace ``\\`` with ``/``.
    2. Strip a single leading ``a/`` or ``b/`` (unified-diff prefix).
    3. Strip a single leading ``./``.
    4. ``str.strip()`` whitespace.
"""

from __future__ import annotations


def normalise_path(p: str | None) -> str:
    if p is None:
        return ""
    s = str(p).strip()
    if not s:
        return ""
    s = s.replace("\\", "/")
    if s.startswith(("a/", "b/")):
        s = s[2:]
    if s.startswith("./"):
        s = s[2:]
    return s
