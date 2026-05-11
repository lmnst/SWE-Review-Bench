"""Line-range matching of reviewer comments against oracle sites.

The matching layer is intentionally severity-blind. ``MatchableComment``
carries only the three fields needed for hit/miss decisions; severity is
the metrics layer's concern (precision@k ordering). This separation is a
hard project rule -- matching must NEVER read the severity field, so the
hit/FP scores stay independent of any severity quirks across reviewers.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..data.oracle import OracleSite
from ..reviewers.base import Comment


@dataclass(frozen=True)
class MatchableComment:
    """Minimal projection of ``Comment`` used by the matcher.

    Deliberately omits ``severity`` and ``message`` so the matcher
    physically cannot use them. A comment is just a file path and a
    line range as far as hit/miss is concerned.
    """

    file: str
    line_start: int
    line_end: int


def to_matchable(c: Comment) -> MatchableComment:
    """Project a full ``Comment`` down to the matchable subset."""
    return MatchableComment(
        file=c.file, line_start=c.line_start, line_end=c.line_end
    )


def to_matchable_list(cs: list[Comment]) -> list[MatchableComment]:
    return [to_matchable(c) for c in cs]


def ranges_overlap(
    a_start: int, a_end: int, b_start: int, b_end: int
) -> bool:
    """True iff closed ranges ``[a_start, a_end]`` and ``[b_start, b_end]``
    have non-empty intersection."""
    return a_end >= b_start and a_start <= b_end


def comment_hits_site(
    c: MatchableComment, s: OracleSite, *, tolerance: int
) -> bool:
    """True iff ``c`` and ``s`` are in the same file and the comment range
    overlaps the site range expanded by ``tolerance`` on each side."""
    if c.file != s.file:
        return False
    if tolerance < 0:
        raise ValueError(f"tolerance must be >= 0, got {tolerance}")
    return ranges_overlap(
        c.line_start, c.line_end, s.line_start - tolerance, s.line_end + tolerance
    )


def find_matching_site(
    c: MatchableComment, sites: list[OracleSite], *, tolerance: int
) -> OracleSite | None:
    """Return the first site that ``c`` hits, in input order, or ``None``."""
    for s in sites:
        if comment_hits_site(c, s, tolerance=tolerance):
            return s
    return None


@dataclass(frozen=True)
class MatchOutcome:
    """Result of matching a comment list against a site list.

    Attributes:
        comment_to_site: for each comment (by input index), the matched
            site_id or ``None``.
        site_hit: for each site_id, whether at least one comment hit it.
    """

    comment_to_site: tuple[str | None, ...]
    site_hit: dict[str, bool]


def match_comments(
    comments: list[MatchableComment],
    sites: list[OracleSite],
    *,
    tolerance: int,
) -> MatchOutcome:
    """Match each comment to at most one site (first match wins) and
    record which sites had any hit."""
    site_hit: dict[str, bool] = {s.site_id: False for s in sites}
    out: list[str | None] = []
    for c in comments:
        matched = find_matching_site(c, sites, tolerance=tolerance)
        if matched is None:
            out.append(None)
        else:
            out.append(matched.site_id)
            site_hit[matched.site_id] = True
    return MatchOutcome(comment_to_site=tuple(out), site_hit=site_hit)
