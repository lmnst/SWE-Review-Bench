"""Parse a fix patch into oracle sites.

Oracle sites locate the buggy code in the PRE-fix version of each file
(the revision at ``base_commit``). Reviewer comments are later compared
against these sites to compute hit / miss metrics.

Two anchoring modes are supported:

* ``strict_mode=False`` (MVP default) -- one site per hunk, line range
  equal to the full hunk source range ``[source_start,
  source_start + source_length - 1]``. Simple and robust against
  pure-addition hunks; slightly generous, mitigated by tolerance N.

* ``strict_mode=True`` -- one site per consecutive run of removed
  (``-``) lines. Pure-addition hunks collapse to a single 1-line site
  anchored at the hunk's source_start, so the site count is comparable
  across modes for ablation experiments.

The single/multi-file classifier filters out test files first.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from unidiff import PatchSet


@dataclass(frozen=True)
class OracleSite:
    """One oracle location in the pre-fix file tree."""

    site_id: str
    file: str
    line_start: int
    line_end: int


def _strip_diff_prefix(path: str) -> str:
    """Strip the leading ``a/`` or ``b/`` prefix used in unified diffs."""
    if path.startswith(("a/", "b/")):
        return path[2:]
    return path


def build_oracle_sites(
    patch_text: str,
    *,
    strict_mode: bool = False,
) -> list[OracleSite]:
    """Extract oracle sites from a fix patch.

    Args:
        patch_text: unified diff body, e.g. the ``patch`` field shipped by
            SWE-bench Lite.
        strict_mode: see module docstring.
    """
    patch = PatchSet(patch_text)
    sites: list[OracleSite] = []
    counter = 0
    for pfile in patch:
        if pfile.is_binary_file:
            continue
        src = pfile.source_file or ""
        if src == "/dev/null" or not src:
            # File added by the fix patch -> no pre-fix lines to point at.
            continue
        file_path = _strip_diff_prefix(src)
        for hunk in pfile:
            if strict_mode:
                ranges = _strict_ranges_for_hunk(hunk)
            else:
                ranges = [(hunk.source_start, hunk.source_start + hunk.source_length - 1)]
            for start, end in ranges:
                if end < start or start <= 0:
                    continue
                counter += 1
                sites.append(
                    OracleSite(
                        site_id=f"site-{counter:04d}",
                        file=file_path,
                        line_start=start,
                        line_end=end,
                    )
                )
    return sites


def _strict_ranges_for_hunk(hunk) -> list[tuple[int, int]]:
    """Return tight ranges of removed (``-``) lines within a hunk.

    Pure-addition hunks collapse to a single 1-line site anchored at the
    hunk's ``source_start`` -- a deterministic, mode-stable choice that
    keeps strict-mode site counts comparable to non-strict mode.
    """
    runs: list[tuple[int, int]] = []
    cur_start: int | None = None
    cur_end: int | None = None
    has_removed = False
    for line in hunk:
        if line.is_removed:
            has_removed = True
            ln = line.source_line_no
            if ln is None:
                continue
            if cur_start is None:
                cur_start = ln
                cur_end = ln
            elif ln == (cur_end or 0) + 1:
                cur_end = ln
            else:
                assert cur_start is not None and cur_end is not None
                runs.append((cur_start, cur_end))
                cur_start = ln
                cur_end = ln
        else:
            if cur_start is not None and cur_end is not None:
                runs.append((cur_start, cur_end))
                cur_start = None
                cur_end = None
    if cur_start is not None and cur_end is not None:
        runs.append((cur_start, cur_end))
    if not has_removed:
        anchor = hunk.source_start
        runs = [(anchor, anchor)] if anchor >= 1 else []
    return runs


# ---------------------------------------------------------------------------
# Test-file filter & single/multi-file bug classifier
# ---------------------------------------------------------------------------

_TEST_FILE_RE = re.compile(
    r"(^|/)(tests?|testing)(/|$)"
    r"|(^|/)(test_[^/]+|[^/]+_test)\.py$"
    r"|(^|/)conftest\.py$",
    re.IGNORECASE,
)


def is_test_file(path: str) -> bool:
    """Heuristic test-file detector.

    Matches paths under a ``tests/``/``testing/`` directory, files named
    ``test_*.py`` or ``*_test.py``, and any ``conftest.py``.
    """
    return _TEST_FILE_RE.search(path) is not None


def oracle_files(sites: list[OracleSite], *, include_tests: bool = False) -> list[str]:
    """Distinct file paths covered by ``sites``, preserving first-seen order."""
    out: list[str] = []
    for site in sites:
        if site.file in out:
            continue
        if not include_tests and is_test_file(site.file):
            continue
        out.append(site.file)
    return out


def is_multi_file_bug(sites: list[OracleSite]) -> bool:
    """True iff the oracle covers two or more non-test files."""
    return len(oracle_files(sites)) >= 2
