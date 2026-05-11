"""Reviewer-facing data structures and the ``Reviewer`` abstract base class.

This module is the single source of truth for the unified comment schema.
Every reviewer (LLM-based or static) emits ``Comment`` objects with
identical shape so the scoring layer can treat them uniformly.

The prompt template lives here too; its identifier (``PROMPT_TEMPLATE_ID``)
participates in the LLM cache key so prompt edits invalidate the cache
deterministically.

Hard rules baked into the template:
    * It never says "find the bug", never mentions issues/patches/tests.
    * It allows an explicit empty-list answer to suppress invented findings.
    * It pins the JSON schema and forbids code fences.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ---------------------------------------------------------------------------
# ReviewerInput -- the only oracle-free payload visible to a reviewer.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReviewerInput:
    """The complete payload a reviewer sees for a single file.

    Intentionally does NOT include: instance_id, repo name, base commit,
    issue title or ``problem_statement``, fix patch, test patch, failing
    test names, or oracle line numbers.
    """

    file_path: str
    file_content: str

    def serialised(self) -> str:
        """Flat serialisation used for substring-based leakage checks."""
        return f"{self.file_path}\n{self.file_content}"


# ---------------------------------------------------------------------------
# Comment schema -- unified across LLM and static reviewers.
# ---------------------------------------------------------------------------


Severity = Literal["low", "medium", "high"]


class Comment(BaseModel):
    """One reviewer finding, uniformly shaped across all reviewers."""

    model_config = ConfigDict(frozen=True)

    file: str
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    severity: Severity
    message: str

    @model_validator(mode="after")
    def _check_range(self) -> "Comment":
        if self.line_end < self.line_start:
            raise ValueError(
                f"line_end ({self.line_end}) must be >= line_start ({self.line_start})"
            )
        return self


# ---------------------------------------------------------------------------
# Review metadata and result.
# ---------------------------------------------------------------------------


class ReviewMeta(BaseModel):
    """Per-call metadata: latency, tokens, cost, and failure flags."""

    model_config = ConfigDict(frozen=True)

    latency_seconds: float = 0.0
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost_usd: float | None = None
    cache_hit: bool = False
    raw_output_path: str | None = None
    parse_error: bool = False
    skipped_reason: str | None = None  # e.g. "TokenLimitExceeded", "UnsupportedFileType"
    estimated_input_tokens: int | None = None  # pre-call estimate (for TokenLimitExceeded)


class ReviewResult(BaseModel):
    """Bundle of comments + metadata returned by ``Reviewer.review``."""

    model_config = ConfigDict(frozen=True)

    comments: list[Comment]
    meta: ReviewMeta


# ---------------------------------------------------------------------------
# Reviewer ABC.
# ---------------------------------------------------------------------------


class Reviewer(ABC):
    """Abstract base for every reviewer."""

    #: Stable display name; used as the ``reviewer`` column in ``results.csv``.
    name: str

    @abstractmethod
    def review(self, inp: ReviewerInput) -> ReviewResult:
        """Review a single file. Must never raise on a parse / cost error;
        such failures are surfaced via ``ReviewMeta`` fields instead."""


# ---------------------------------------------------------------------------
# Prompt template (v1).
# ---------------------------------------------------------------------------


PROMPT_TEMPLATE_ID = "v1"

PROMPT_TEMPLATE = """You are reviewing the following source file as part of a routine code review pass.

Identify any concrete correctness, reliability, or maintainability issues that
are directly supported by the code shown. Do not speculate about missing
context. Do not invent issues. If the code looks correct to you, return an
empty list.

Return a JSON array. Each item must follow this schema exactly:
{{
  "file": string,           // must equal the File path below verbatim
  "line_start": integer,    // 1-indexed, matches the numbered source
  "line_end": integer,      // 1-indexed, inclusive, >= line_start
  "severity": "low" | "medium" | "high",
  "message": string         // one short sentence
}}

Output the JSON array and nothing else. Do not wrap it in code fences.
An empty array [] is a valid answer.

File path: {file_path}

Source with line numbers (format: "<line>: <content>"):
{numbered_source}
"""


def number_lines(content: str) -> str:
    """Prefix each line with its 1-indexed line number.

    Uses ``splitlines()`` so the result is independent of trailing-newline
    quirks. Always emits at least one line for non-empty content.
    """
    if not content:
        return ""
    lines = content.splitlines()
    return "\n".join(f"{i}: {line}" for i, line in enumerate(lines, start=1))


def build_prompt(file_path: str, file_content: str) -> str:
    """Render the prompt template for a given file."""
    return PROMPT_TEMPLATE.format(
        file_path=file_path,
        numbered_source=number_lines(file_content),
    )
