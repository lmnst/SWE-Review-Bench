"""Deterministic theme classifier for Claude review messages.

Used by E.1 to label Claude's per-comment messages with one tag from the
fixed Q1 label set. Pure keyword/regex rules so the classification is
auditable and reproducible without any LLM call.

Collision policy: ``possible_correctness_bug`` wins over style/maintenance
labels when both fire on the same message (the spec explicitly requires
this so high-signal messages aren't buried as "style").

Order matters in ``LABEL_RULES``: the first match wins UNLESS that match is
overridden by a stronger correctness signal later in the list. The
``_classify_one`` function implements this two-pass logic.
"""

from __future__ import annotations

import re
from typing import Iterable

# Label order is the public Q1 fixed label set.
LABELS: tuple[str, ...] = (
    "hardcoded_value",
    "missing_validation",
    "error_handling",
    "style_or_readability",
    "docstring_or_comment",
    "typing_or_api_contract",
    "resource_or_state_management",
    "performance",
    "test_or_debug_artifact",
    "possible_correctness_bug",
    "other",
)


# Each entry: (label, regex_pattern). Compiled with IGNORECASE.
# Rules are intentionally conservative; the unmatched fallback is
# ``other``.
RULES: tuple[tuple[str, str], ...] = (
    # ----- correctness signals (highest priority on collision) -----
    (
        "possible_correctness_bug",
        r"\b(off[- ]by[- ]one|race condition|deadlock|incorrect|wrong "
        r"(result|behaviour|behavior|value|output)|may (fail|crash|raise|throw|"
        r"return wrong|return incorrect|produce incorrect|lead to incorrect|"
        r"break)|could (fail|crash|raise|throw|break)|will (fail|crash|raise)|"
        r"causes? .* (error|failure|crash|exception)|invalid (result|behaviour|"
        r"behavior|output|condition|state)|logic (bug|error|flaw|mistake)|"
        r"infinite (loop|recursion)|attributeerror|typeerror|keyerror|valueerror|"
        r"unboundlocalerror|nameerror|indexerror|zerodivisionerror|"
        r"divide by zero|missing (case|branch|condition|return|guard)|"
        r"edge case|null pointer|None .*(deref|access|attribute)|"
        r"(does not|doesn't) handle (None|null|empty)|"
        r"unreachable|never (true|false|executes)|"
        r"order of operations|short[- ]circuit|"
        r"mutation of .*(argument|parameter|default)|"
        r"mutable default|shared mutable)\b",
    ),
    (
        "hardcoded_value",
        r"\b(hard[- ]?cod(ed|ing)|magic (number|constant|string)|"
        r"literal (value|string)|use of (a )?literal)\b",
    ),
    (
        "missing_validation",
        r"\b(validat(e|ion|or)|sanitiz(e|ation)|input check|"
        r"(should|must) (validate|check|verify) (the |that )?(input|argument|"
        r"parameter)|range check|bounds check|out of bounds|"
        r"out-of-bounds|(no |missing |lack of )(input |argument |parameter "
        r")?(validation|check)|guard against)\b",
    ),
    (
        "error_handling",
        r"\b(exception handling|except clause|bare except|catching .* general "
        r"exception|swallow(s|ed|ing)? .*(exception|error)|raise .* (from|None)|"
        r"re[- ]?raise|silently (ignore|fail|swallow)|broad except|"
        r"try .* except|missing (exception|error) handler)\b",
    ),
    (
        "typing_or_api_contract",
        r"\b(type (hint|annotation)|return (type|annotation)|"
        r"Optional\[|Union\[|isinstance|annotated as|"
        r"signature (mismatch|change|differs)|api (contract|signature)|"
        r"keyword argument before|positional[- ]only)\b",
    ),
    (
        "resource_or_state_management",
        r"\b(resource leak|file (not |is not )?closed|"
        r"context manager|with statement|"
        r"connection leak|cursor (not )?closed|memory leak|"
        r"global state|module[- ]level state|"
        r"attribute (defined|assigned) outside __init__|"
        r"defined outside __init__)\b",
    ),
    (
        "performance",
        r"\b(performance (issue|problem|concern)|O\(n\^?2\)|O\(n\*\*?2\)|"
        r"quadratic|inefficient|optimi[sz]ation|slow(er)?|hot path|"
        r"redundant (call|computation|work)|repeated (call|computation))\b",
    ),
    (
        "test_or_debug_artifact",
        r"\b(print statement|debug(ging)? (output|print|statement)|"
        r"TODO|FIXME|XXX|left[- ]?over|temporary code|"
        r"breakpoint|pdb\.|set_trace)\b",
    ),
    (
        "docstring_or_comment",
        r"\b(docstring|missing doc|missing documentation|inline comment|"
        r"comment is (missing|stale|outdated|wrong)|doc(s|umentation) "
        r"(missing|outdated|stale|wrong))\b",
    ),
    (
        "style_or_readability",
        r"\b(readab(le|ility)|naming (convention|style)|rename|"
        r"better name|unclear name|magic name|PEP[- ]?8|"
        r"f[- ]?string|formatting|indentation|spacing|"
        r"long line|line length|line too long)\b",
    ),
)


_COMPILED: list[tuple[str, re.Pattern[str]]] = [
    (label, re.compile(pat, re.IGNORECASE)) for label, pat in RULES
]


def classify_message(message: str) -> str:
    """Return one label from ``LABELS`` for ``message``.

    Two-pass logic so ``possible_correctness_bug`` always wins over
    weaker tags when both fire.
    """
    if not message:
        return "other"
    # First pass: collect all firing labels.
    fired: list[str] = []
    for label, pat in _COMPILED:
        if pat.search(message):
            fired.append(label)
    if not fired:
        return "other"
    if "possible_correctness_bug" in fired:
        return "possible_correctness_bug"
    return fired[0]


def classify_many(messages: Iterable[str]) -> list[str]:
    return [classify_message(m) for m in messages]
