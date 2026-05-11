"""Read source content at a specific commit from a cached git repo.

Uses ``git show <commit>:<path>`` so the cached repo's working tree is
left untouched (Round 1 checked out the last instance's base_commit; we
must not disturb that state).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ..utils.paths import repo_cache_path


class SourceUnavailable(RuntimeError):
    pass


def read_source_at(
    repo: str, base_commit: str, rel_path: str, *, repos_cache_dir: Path
) -> str:
    """Return the file content as a string, decoded UTF-8 (errors='replace').

    Raises ``SourceUnavailable`` if the repo clone is missing or git fails.
    """
    repo_path = repo_cache_path(repos_cache_dir, repo)
    if not repo_path.exists():
        raise SourceUnavailable(f"repo clone missing: {repo_path}")
    cmd = ["git", "show", f"{base_commit}:{rel_path}"]
    try:
        proc = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired as e:
        raise SourceUnavailable(f"git show timed out: {cmd}") from e
    if proc.returncode != 0:
        raise SourceUnavailable(
            f"git show failed (rc={proc.returncode}): {proc.stderr.decode('utf-8', errors='replace').strip()}"
        )
    return proc.stdout.decode("utf-8", errors="replace")


def render_lines_window(
    content: str, *, lo: int, hi: int, pad: int = 5, highlight: tuple[int, int] | None = None
) -> str:
    """Return a numbered code window covering lines [lo-pad, hi+pad].

    1-indexed. ``highlight`` is an inclusive range whose lines are
    prefixed with '>' instead of ' '.
    """
    lines = content.splitlines()
    n = len(lines)
    lo_w = max(1, lo - pad)
    hi_w = min(n, hi + pad)
    width = max(4, len(str(hi_w)))
    out: list[str] = []
    for i in range(lo_w, hi_w + 1):
        prefix = ">" if (highlight and highlight[0] <= i <= highlight[1]) else " "
        line = lines[i - 1] if 1 <= i <= n else ""
        out.append(f"{prefix} {i:>{width}}: {line}")
    return "\n".join(out)
