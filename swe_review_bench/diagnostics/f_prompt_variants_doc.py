"""Emit ``outputs/round2/prompt_variants.md``: the canonical record of
the three Round 2 prompt variants, their template ids, and their sha256
template hashes.

Each variant carries:
    * Full template body (so a reviewer can audit the exact text).
    * ``template_id`` (cache-key contribution).
    * ``template_sha256`` (so any future drift is detectable).
    * Diff vs Variant A so reviewers can see exactly which lines moved.
    * Intended use note.

Also confirms the leakage check that template-level strings are free of
oracle-derived content. The runtime per-instance leakage assertion still
lives in ``run.py`` (``_assert_no_oracle_leak``); this file documents
the static template-side check.
"""

from __future__ import annotations

import difflib
from pathlib import Path

from ..reviewers.prompt_variants import VARIANT_A, VARIANT_B, VARIANT_C


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROUND2_DIR = PROJECT_ROOT / "outputs" / "round2"


def _diff_block(a_lines: list[str], b_lines: list[str], a_name: str, b_name: str) -> str:
    diff = list(
        difflib.unified_diff(
            a_lines, b_lines, fromfile=a_name, tofile=b_name, lineterm=""
        )
    )
    return "\n".join(diff)


def main() -> None:
    ROUND2_DIR.mkdir(parents=True, exist_ok=True)

    a_lines = VARIANT_A.template.splitlines()
    b_lines = VARIANT_B.template.splitlines()
    c_lines = VARIANT_C.template.splitlines()

    diff_a_b = _diff_block(a_lines, b_lines, "Variant A", "Variant B")
    diff_a_c = _diff_block(a_lines, c_lines, "Variant A", "Variant C")

    lines: list[str] = []
    lines.append("# F.1 Prompt variants\n\n")
    lines.append(
        "Three prompt variants for the Round 2 prompt-suppression probe. "
        "Variant A is byte-identical to the Round 1 ``v1`` template so its "
        "cache key matches Round 1's; Variant B and C have new template ids "
        "(``v1b`` / ``v1c``) so their cache entries never collide with "
        "Round 1's. Static reviewer is variant-agnostic.\n\n"
    )

    for variant in (VARIANT_A, VARIANT_B, VARIANT_C):
        lines.append(f"## Variant {variant.name}\n\n")
        lines.append("| field | value |\n|---|---|\n")
        lines.append(f"| template_id | `{variant.template_id}` |\n")
        lines.append(f"| template_sha256 | `{variant.template_sha256}` |\n")
        lines.append(f"| template length (chars) | {len(variant.template)} |\n\n")
        lines.append("### Template body\n\n")
        lines.append("```\n")
        lines.append(variant.template)
        if not variant.template.endswith("\n"):
            lines.append("\n")
        lines.append("```\n\n")

    lines.append("## Variant A → Variant B diff (no-suppression edit)\n\n")
    lines.append("```diff\n")
    lines.append(diff_a_b)
    lines.append("\n```\n\n")

    lines.append("## Variant A → Variant C diff (force-emit edit)\n\n")
    lines.append("```diff\n")
    lines.append(diff_a_c)
    lines.append("\n```\n\n")

    lines.append("## Intended use\n\n")
    lines.append(
        "- **Variant A** is the baseline; it reproduces Round 1's prompt "
        "byte-for-byte and reuses Round 1's cache (read-through). It is "
        "the only variant eligible to become the externally reported "
        "headline prompt without further discussion.\n"
        "- **Variant B** removes only the suppression clause "
        '(`"Do not invent issues. ... return an empty list."`). It tests '
        "whether Claude's 0% under Variant A is partially explained by "
        "the conservative framing of the Round 1 prompt.\n"
        "- **Variant C** asks for at least one comment per file and is "
        "**diagnostic-only**. Hit-rate movement under C is informative "
        "about Claude's upper bound when forced into shotgun mode, but "
        "Variant C is not a candidate prompt for external reporting unless "
        "explicitly approved.\n\n"
    )

    lines.append("## Static leakage check (template-side)\n\n")
    for variant in (VARIANT_A, VARIANT_B, VARIANT_C):
        # Conservative check: search for attention-directing phrases that
        # would tip the model off about the specific instance. Generic
        # vocabulary like "bug", "issue", "fix", "error", "correctness"
        # remains allowed per §0.5.
        forbidden_phrases = [
            "find the bug",
            "find the defect",
            "a defect was reported",
            "a bug was reported",
            "this file has a bug",
            "this file has a defect",
            "fix the bug",
            "fix the issue",
            "locate the bug",
            "locate the defect",
            "problem_statement",
            "test_patch",
            "@@ -",
            "@@ +",
            "--- a/",
            "+++ b/",
        ]
        hits = [
            phrase
            for phrase in forbidden_phrases
            if phrase.lower() in variant.template.lower()
        ]
        verdict = "PASS" if not hits else f"FAIL: matched phrases {hits}"
        lines.append(f"- Variant {variant.name}: {verdict}\n")
    lines.append(
        "\nThis is a template-side static check. The per-instance runtime "
        "check (problem_statement / patch / test_patch substring in the "
        "fully rendered payload) is enforced by "
        "``_assert_no_oracle_leak`` in ``run.py`` and runs on every "
        "instance before any LLM call.\n"
    )

    out = ROUND2_DIR / "prompt_variants.md"
    out.write_text("".join(lines), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
