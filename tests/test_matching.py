"""Unit tests for ``scoring.matching``.

Covers the six cases agreed for Milestone C:
    1. Exact-line hit at tolerance 0.
    2. Hit at the tolerance boundary (+/- N).
    3. Miss one line outside the tolerance boundary.
    4. Wrong file -> no hit even with overlapping lines.
    5. Empty comment list -> no hit, FP = 0.
    6. Multiple hunks -> partial coverage (one site hit, one missed).
"""

from __future__ import annotations

import pytest

from swe_review_bench.data.oracle import OracleSite
from swe_review_bench.scoring.matching import (
    MatchableComment,
    comment_hits_site,
    match_comments,
)


def _site(site_id: str, file: str, start: int, end: int) -> OracleSite:
    return OracleSite(site_id=site_id, file=file, line_start=start, line_end=end)


def _c(file: str, start: int, end: int | None = None) -> MatchableComment:
    return MatchableComment(file=file, line_start=start, line_end=end or start)


FILE_A = "pkg/mod.py"
FILE_B = "pkg/other.py"


# ---------------------------------------------------------------------------
# 1. Exact-line hit (tolerance 0).
# ---------------------------------------------------------------------------


def test_exact_line_hit_at_tolerance_zero():
    site = _site("s1", FILE_A, 50, 50)
    comment = _c(FILE_A, 50)
    assert comment_hits_site(comment, site, tolerance=0)
    outcome = match_comments([comment], [site], tolerance=0)
    assert outcome.comment_to_site == ("s1",)
    assert outcome.site_hit == {"s1": True}


# ---------------------------------------------------------------------------
# 2. Tolerance boundary (+/- 3).
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("offset", [-3, -1, 0, 1, 3])
def test_inside_tolerance_boundary_hits(offset: int):
    site = _site("s1", FILE_A, 50, 50)
    comment = _c(FILE_A, 50 + offset)
    assert comment_hits_site(comment, site, tolerance=3), (
        f"offset={offset} should hit with tolerance=3"
    )


# ---------------------------------------------------------------------------
# 3. Miss outside tolerance.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("offset", [-4, 4, -10, 10])
def test_outside_tolerance_misses(offset: int):
    site = _site("s1", FILE_A, 50, 50)
    comment = _c(FILE_A, 50 + offset)
    assert not comment_hits_site(comment, site, tolerance=3), (
        f"offset={offset} should miss with tolerance=3"
    )


# ---------------------------------------------------------------------------
# 4. Wrong file -> no hit even with overlapping lines.
# ---------------------------------------------------------------------------


def test_wrong_file_misses_even_with_overlap():
    site = _site("s1", FILE_A, 50, 60)
    comment = _c(FILE_B, 55)  # same line range, different file
    assert not comment_hits_site(comment, site, tolerance=3)
    outcome = match_comments([comment], [site], tolerance=3)
    assert outcome.comment_to_site == (None,)
    assert outcome.site_hit == {"s1": False}


# ---------------------------------------------------------------------------
# 5. Empty comment list -> no hit, FP = 0.
# ---------------------------------------------------------------------------


def test_empty_comment_list():
    site = _site("s1", FILE_A, 50, 60)
    outcome = match_comments([], [site], tolerance=3)
    assert outcome.comment_to_site == ()
    assert outcome.site_hit == {"s1": False}
    # FP is computed at the metrics layer as len(comments) - n_hits,
    # which is 0 - 0 = 0 here; verified directly:
    assert len(outcome.comment_to_site) == 0


# ---------------------------------------------------------------------------
# 6. Multiple hunks -> partial coverage.
# ---------------------------------------------------------------------------


def test_multiple_hunks_partial_coverage():
    sites = [
        _site("s1", FILE_A, 10, 12),
        _site("s2", FILE_A, 100, 110),
    ]
    # Two comments: one inside s1 with tolerance, one far from both sites.
    comments = [
        _c(FILE_A, 11),     # hits s1
        _c(FILE_A, 200),    # FP
    ]
    outcome = match_comments(comments, sites, tolerance=3)
    assert outcome.comment_to_site == ("s1", None)
    assert outcome.site_hit == {"s1": True, "s2": False}


# ---------------------------------------------------------------------------
# Bonus assertions specifically required by the spec contract.
# ---------------------------------------------------------------------------


def test_negative_tolerance_rejected():
    site = _site("s1", FILE_A, 50, 50)
    comment = _c(FILE_A, 50)
    with pytest.raises(ValueError):
        comment_hits_site(comment, site, tolerance=-1)


def test_first_match_wins_when_comment_overlaps_multiple_sites():
    # Two overlapping sites; matcher should attribute to the first one
    # (input order) so the result is stable and deterministic.
    sites = [
        _site("first", FILE_A, 50, 60),
        _site("second", FILE_A, 55, 65),
    ]
    comment = _c(FILE_A, 57)
    outcome = match_comments([comment], sites, tolerance=0)
    assert outcome.comment_to_site == ("first",)
    assert outcome.site_hit == {"first": True, "second": False}
