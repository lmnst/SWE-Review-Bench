"""Deterministic hashing helpers used for LLM cache keys."""

from __future__ import annotations

import hashlib


def sha256_text(*parts: str) -> str:
    """Hash a sequence of UTF-8 strings with NUL separators to avoid collisions."""
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
