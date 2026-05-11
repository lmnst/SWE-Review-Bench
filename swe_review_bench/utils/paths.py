"""Filesystem path helpers shared across modules."""

from __future__ import annotations

from pathlib import Path


def repo_slug(repo: str) -> str:
    """Convert ``owner/repo`` into a filesystem-safe directory name."""
    return repo.replace("/", "__")


def repo_cache_path(repos_cache_dir: Path, repo: str) -> Path:
    """Return the cache directory for a given repo."""
    return repos_cache_dir / repo_slug(repo)
