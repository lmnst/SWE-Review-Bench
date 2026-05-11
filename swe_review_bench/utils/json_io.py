"""Robust JSON array extraction for LLM outputs.

Models occasionally wrap the requested JSON in markdown code fences or
prepend a short prose preamble despite explicit instructions. We try
several strategies in order; on total failure we return ``None`` and the
caller logs a ``parse_error`` event.
"""

from __future__ import annotations

import json
import re
from typing import Any

_FENCE_RE = re.compile(r"```(?:json|JSON)?\s*(\[.*?\])\s*```", re.DOTALL)


def extract_json_array(text: str) -> list[Any] | None:
    """Try to recover a top-level JSON array from arbitrary text.

    Strategies, applied in order:
        1. ``json.loads`` on the whole stripped text.
        2. Look for a ``` ... ``` fenced array.
        3. Slice from the first ``[`` to the last ``]``.

    Returns the parsed list, or ``None`` if every strategy fails.
    """
    if text is None:
        return None
    s = text.strip()
    if not s:
        return None

    try:
        v = json.loads(s)
        if isinstance(v, list):
            return v
    except json.JSONDecodeError:
        pass

    m = _FENCE_RE.search(s)
    if m:
        try:
            v = json.loads(m.group(1))
            if isinstance(v, list):
                return v
        except json.JSONDecodeError:
            pass

    start = s.find("[")
    end = s.rfind("]")
    if start != -1 and end > start:
        try:
            v = json.loads(s[start : end + 1])
            if isinstance(v, list):
                return v
        except json.JSONDecodeError:
            pass

    return None
