"""Round 2 prompt variants A / B / C.

Variant A is byte-identical to the Round 1 prompt template (``v1``) so
its cache key matches Round 1's. B removes the output-suppressing clause;
C adds a force-emit clause on top of B for diagnostic upper-bound probing.

Hard rules retained across all variants:
    * No "find the bug" language, no mention of issues / patches / tests,
      no oracle line numbers.
    * JSON schema is pinned identically across all variants.
    * Empty arrays are still a valid answer for A and B (C asks the
      model to emit at least one comment per file).

Each variant has its own template id so the LLM cache key
(``sha256(model, template_id, file_path, file_content)``) cleanly
separates the three variants.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .base import PROMPT_TEMPLATE, PROMPT_TEMPLATE_ID, number_lines


@dataclass(frozen=True)
class PromptVariant:
    name: str          # "A" | "B" | "C"
    template_id: str   # cache-key contribution
    template: str      # ``str.format(file_path=..., numbered_source=...)``-able

    @property
    def template_sha256(self) -> str:
        return hashlib.sha256(self.template.encode("utf-8")).hexdigest()


# Variant A = Round 1 v1. Reuse the constant by reference so any future
# edit to the base template propagates here.
VARIANT_A = PromptVariant(
    name="A",
    template_id=PROMPT_TEMPLATE_ID,
    template=PROMPT_TEMPLATE,
)


# Variant B removes ONLY the suppression clause. The diff vs A is the
# deletion of "Do not invent issues." and "If the code looks correct to
# you, return an empty list." -- nothing else changes (schema, framing,
# code-fence prohibition, line-number instructions all intact).
VARIANT_B_TEMPLATE = """You are reviewing the following source file as part of a routine code review pass.

Identify any concrete correctness, reliability, or maintainability issues that
are directly supported by the code shown. Do not speculate about missing
context.

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

VARIANT_B = PromptVariant(
    name="B",
    template_id="v1b",
    template=VARIANT_B_TEMPLATE,
)


# Variant C adds the force-emit clause on top of B. Diagnostic-only.
VARIANT_C_TEMPLATE = """You are reviewing the following source file as part of a routine code review pass.

Identify any concrete correctness, reliability, or maintainability issues that
are directly supported by the code shown. Do not speculate about missing
context. Return at least one comment per file, even if it is a minor
observation.

Return a JSON array. Each item must follow this schema exactly:
{{
  "file": string,           // must equal the File path below verbatim
  "line_start": integer,    // 1-indexed, matches the numbered source
  "line_end": integer,      // 1-indexed, inclusive, >= line_start
  "severity": "low" | "medium" | "high",
  "message": string         // one short sentence
}}

Output the JSON array and nothing else. Do not wrap it in code fences.

File path: {file_path}

Source with line numbers (format: "<line>: <content>"):
{numbered_source}
"""

VARIANT_C = PromptVariant(
    name="C",
    template_id="v1c",
    template=VARIANT_C_TEMPLATE,
)


VARIANTS: dict[str, PromptVariant] = {
    "A": VARIANT_A,
    "B": VARIANT_B,
    "C": VARIANT_C,
}


def get_variant(name: str) -> PromptVariant:
    name = (name or "A").strip().upper()
    if name not in VARIANTS:
        raise ValueError(
            f"Unknown prompt variant {name!r}; expected one of "
            f"{sorted(VARIANTS)}"
        )
    return VARIANTS[name]


def render_prompt(variant: PromptVariant, file_path: str, file_content: str) -> str:
    """Render the chosen variant for a given file."""
    return variant.template.format(
        file_path=file_path,
        numbered_source=number_lines(file_content),
    )
