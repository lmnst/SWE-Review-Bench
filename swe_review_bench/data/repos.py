"""Shallow git clone + checkout helpers.

The only network access in this project is ``git clone`` / ``git fetch``
to GitHub. We never call the GitHub API and never download release
tarballs. One clone per repo is reused across instances of that repo by
switching commits with ``git checkout``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..utils.paths import repo_cache_path


class RepoUnavailable(Exception):
    """Raised when a repo cannot be cloned or its base commit cannot be checked out.

    Caught at the orchestration layer and recorded as an expected failure in
    ``outputs/failures.jsonl``. The main loop continues with the next instance.
    """


def ensure_repo_at_commit(
    repo: str,
    base_commit: str,
    *,
    repos_cache_dir: Path,
    clone_timeout: int = 600,
    checkout_timeout: int = 120,
) -> Path:
    """Ensure ``repo`` is cloned and its working tree is at ``base_commit``.

    Returns the local repo path. Reuses an existing clone if present.

    Strategy:
        1. Clone with ``--filter=blob:none`` if the cache directory does not exist.
        2. ``git checkout <base_commit>``. If the commit is not in the local
           history (rare but possible for commits on dropped branches), fetch
           it explicitly and retry. GitHub allows fetching arbitrary commits.
    """
    repo_path = repo_cache_path(repos_cache_dir, repo)
    if not repo_path.exists():
        _clone(repo, repo_path, timeout=clone_timeout)
    _checkout(repo_path, base_commit, fetch_timeout=clone_timeout, checkout_timeout=checkout_timeout)
    return repo_path


def _clone(repo: str, dest: Path, *, timeout: int) -> None:
    url = f"https://github.com/{repo}.git"
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            ["git", "clone", "--filter=blob:none", url, str(dest)],
            check=True,
            capture_output=True,
            timeout=timeout,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        stderr = _decode_stderr(e)
        raise RepoUnavailable(f"git clone failed for {url}: {stderr}") from e


def _checkout(
    repo_path: Path,
    commit: str,
    *,
    fetch_timeout: int,
    checkout_timeout: int,
) -> None:
    # First attempt: assume the commit is already reachable.
    if _try_checkout(repo_path, commit, timeout=checkout_timeout):
        return
    # Second attempt: fetch the specific commit, then retry.
    try:
        subprocess.run(
            ["git", "fetch", "--depth=1", "origin", commit],
            cwd=repo_path,
            check=True,
            capture_output=True,
            timeout=fetch_timeout,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        stderr = _decode_stderr(e)
        raise RepoUnavailable(
            f"git fetch of {commit} failed in {repo_path}: {stderr}"
        ) from e
    if not _try_checkout(repo_path, commit, timeout=checkout_timeout):
        raise RepoUnavailable(
            f"git checkout of {commit} still failed after fetch in {repo_path}"
        )


def _try_checkout(repo_path: Path, commit: str, *, timeout: int) -> bool:
    try:
        subprocess.run(
            ["git", "checkout", "--quiet", commit],
            cwd=repo_path,
            check=True,
            capture_output=True,
            timeout=timeout,
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return False


def _decode_stderr(err: Exception) -> str:
    raw = getattr(err, "stderr", None)
    if isinstance(raw, bytes):
        return raw.decode("utf-8", errors="replace").strip()
    return str(raw or err)


def read_file_bytes(repo_path: Path, rel_path: str) -> bytes:
    """Read a file from the repo working tree at its currently checked-out commit."""
    full = repo_path / rel_path
    if not full.is_file():
        raise FileNotFoundError(f"{rel_path!r} not found under {repo_path}")
    return full.read_bytes()


def try_decode_utf8(data: bytes) -> str | None:
    """Decode bytes as UTF-8. Returns None for binary content."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None
