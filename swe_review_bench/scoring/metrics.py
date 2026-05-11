"""Aggregation metrics over instance-level match outcomes.

Per-instance: ``score_instance`` produces an ``InstanceScore`` from the
matching outcome plus the original comment list (needed only for
precision@k ordering, which is severity-aware).

Across instances: ``summarise_reviewer`` averages over instances to
yield a ``ReviewerSummary``. Single-file and multi-file bug splits use
the ``is_multi_file_bug`` classifier (test files filtered out before
counting), per the agreed refinement.

Severity participates ONLY in precision@k ordering. Hit-rate, site
recall, and FP counts are severity-blind by construction (the matcher
sees ``MatchableComment``, not ``Comment``).
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from ..data.oracle import OracleSite, is_multi_file_bug
from ..reviewers.base import Comment, Severity
from .matching import MatchOutcome, match_comments, to_matchable_list


# ---------------------------------------------------------------------------
# Per-instance score
# ---------------------------------------------------------------------------


PRECISION_KS: tuple[int, ...] = (1, 3, 5)


@dataclass(frozen=True)
class InstanceScore:
    """Scoring outcome for one (instance, reviewer) pair."""

    instance_id: str
    reviewer: str
    n_comments: int
    n_sites: int
    n_sites_hit: int
    n_hits: int
    n_fp: int
    has_hit: bool
    precision_at: dict[int, float] = field(default_factory=dict)
    is_multi_file_bug: bool = False
    outcome: MatchOutcome | None = None


def _severity_rank(sev: Severity) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(sev, 3)


def _rank_comments(comments: list[Comment]) -> list[tuple[int, Comment]]:
    """Return ``(original_index, comment)`` pairs ordered by severity desc
    then ``line_start`` asc. Stable sort preserves input order on ties."""
    indexed = list(enumerate(comments))
    indexed.sort(key=lambda ic: (_severity_rank(ic[1].severity), ic[1].line_start))
    return indexed


def _precision_at_k(
    ranked_indices: list[int],
    comment_to_site: tuple[str | None, ...],
    ks: tuple[int, ...],
) -> dict[int, float]:
    """Compute precision@k for each k in ``ks``.

    Convention:
        * If the reviewer emitted zero comments, ``p@k = 0`` for every k.
        * Otherwise ``p@k = (#hits within top min(k, n)) / min(k, n)``.
        * "Top k" is taken after the severity-desc / line-asc rank.
    """
    n = len(ranked_indices)
    out: dict[int, float] = {}
    for k in ks:
        if n == 0:
            out[k] = 0.0
            continue
        denom = min(k, n)
        hits = sum(
            1 for idx in ranked_indices[:denom] if comment_to_site[idx] is not None
        )
        out[k] = hits / denom
    return out


def score_instance(
    *,
    instance_id: str,
    reviewer: str,
    comments: list[Comment],
    sites: list[OracleSite],
    tolerance: int,
) -> InstanceScore:
    """Score one (instance, reviewer) pair."""
    matchables = to_matchable_list(comments)
    outcome = match_comments(matchables, sites, tolerance=tolerance)
    n_comments = len(comments)
    n_sites = len(sites)
    n_sites_hit = sum(1 for v in outcome.site_hit.values() if v)
    n_hits = sum(1 for v in outcome.comment_to_site if v is not None)
    n_fp = n_comments - n_hits
    has_hit = n_sites_hit > 0
    ranked = _rank_comments(comments)
    ranked_indices = [i for i, _ in ranked]
    precisions = _precision_at_k(ranked_indices, outcome.comment_to_site, PRECISION_KS)
    return InstanceScore(
        instance_id=instance_id,
        reviewer=reviewer,
        n_comments=n_comments,
        n_sites=n_sites,
        n_sites_hit=n_sites_hit,
        n_hits=n_hits,
        n_fp=n_fp,
        has_hit=has_hit,
        precision_at=precisions,
        is_multi_file_bug=is_multi_file_bug(sites),
        outcome=outcome,
    )


# ---------------------------------------------------------------------------
# Across-instance summary
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReviewerSummary:
    """One row of ``summary.csv``: aggregate metrics for a single reviewer."""

    reviewer: str
    n_instances: int
    instance_hit_rate: float
    site_recall: float
    fp_per_instance_mean: float
    fp_per_instance_median: float
    precision_at: dict[int, float]
    # Single/multi-file bug breakdown (test files filtered before classification).
    n_instances_single_file: int
    n_instances_multi_file: int
    instance_hit_rate_single_file: float
    instance_hit_rate_multi_file: float


def _safe_mean(xs: list[float]) -> float:
    return statistics.fmean(xs) if xs else 0.0


def _safe_median(xs: list[float]) -> float:
    return statistics.median(xs) if xs else 0.0


def summarise_reviewer(
    reviewer: str, scores: list[InstanceScore]
) -> ReviewerSummary:
    """Aggregate per-instance scores into one reviewer summary row.

    The single-file / multi-file split is over the SAME instances the
    reviewer scored (no resampling) -- a reviewer that produced an empty
    comment list still contributes to the denominator.
    """
    n = len(scores)
    if n == 0:
        return ReviewerSummary(
            reviewer=reviewer,
            n_instances=0,
            instance_hit_rate=0.0,
            site_recall=0.0,
            fp_per_instance_mean=0.0,
            fp_per_instance_median=0.0,
            precision_at={k: 0.0 for k in PRECISION_KS},
            n_instances_single_file=0,
            n_instances_multi_file=0,
            instance_hit_rate_single_file=0.0,
            instance_hit_rate_multi_file=0.0,
        )

    total_sites = sum(s.n_sites for s in scores)
    total_sites_hit = sum(s.n_sites_hit for s in scores)
    fps = [float(s.n_fp) for s in scores]
    hits = [1.0 if s.has_hit else 0.0 for s in scores]

    precision_at: dict[int, float] = {}
    for k in PRECISION_KS:
        precision_at[k] = _safe_mean([s.precision_at.get(k, 0.0) for s in scores])

    single = [s for s in scores if not s.is_multi_file_bug]
    multi = [s for s in scores if s.is_multi_file_bug]

    return ReviewerSummary(
        reviewer=reviewer,
        n_instances=n,
        instance_hit_rate=sum(hits) / n,
        site_recall=(total_sites_hit / total_sites) if total_sites else 0.0,
        fp_per_instance_mean=_safe_mean(fps),
        fp_per_instance_median=_safe_median(fps),
        precision_at=precision_at,
        n_instances_single_file=len(single),
        n_instances_multi_file=len(multi),
        instance_hit_rate_single_file=(
            sum(1 for s in single if s.has_hit) / len(single) if single else 0.0
        ),
        instance_hit_rate_multi_file=(
            sum(1 for s in multi if s.has_hit) / len(multi) if multi else 0.0
        ),
    )
