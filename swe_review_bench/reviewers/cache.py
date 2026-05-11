"""Disk cache for LLM reviewer calls.

A cache key is sha256 of ``(model, prompt_template_id, file_path,
file_content)`` -- four explicit components rather than the fully-rendered
prompt, so prompt edits that change formatting without changing template
version do not invalidate the cache, and conversely a template version
bump invalidates everything.

The cached payload is the JSON-serialised ``ReviewResult``. The raw model
output lives separately under ``.cache/llm/raw/`` so it survives a cache
schema change.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..utils.hashing import sha256_text
from .base import ReviewResult


def cache_key(
    model: str,
    prompt_template_id: str,
    file_path: str,
    file_content: str,
) -> str:
    """Compute the cache key as a hex sha256."""
    return sha256_text(model, prompt_template_id, file_path, file_content)


def cache_path(cache_dir: Path, key: str) -> Path:
    return cache_dir / f"{key}.json"


def raw_path(raw_dir: Path, key: str) -> Path:
    return raw_dir / f"{key}.txt"


def read_cached(cache_dir: Path, key: str) -> ReviewResult | None:
    """Return the cached ``ReviewResult`` for ``key``, or ``None`` on miss."""
    p = cache_path(cache_dir, key)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return ReviewResult.model_validate(data)
    except Exception:
        # Corrupt cache entry -- treat as miss; will overwrite on next call.
        return None


def write_cached(cache_dir: Path, key: str, result: ReviewResult) -> None:
    """Persist a ``ReviewResult`` to disk."""
    p = cache_path(cache_dir, key)
    p.write_text(result.model_dump_json(indent=2), encoding="utf-8")


def write_raw(raw_dir: Path, key: str, raw_text: str) -> Path:
    """Persist the raw model output. Returns the written path."""
    p = raw_path(raw_dir, key)
    p.write_text(raw_text, encoding="utf-8")
    return p
