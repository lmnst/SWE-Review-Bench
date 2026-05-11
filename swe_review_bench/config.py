"""Runtime configuration: paths, API keys, and the optional model id override.

API keys are loaded only from the project-root ``.env`` file. They are never
echoed to logs or written to output artefacts.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Config:
    """Resolved configuration for a single run."""

    project_root: Path
    cache_dir: Path
    output_dir: Path
    repos_cache_dir: Path
    llm_cache_dir: Path
    llm_raw_cache_dir: Path
    # Round 2 cache lives under .cache/round2/ so Round 1 cache files
    # under .cache/llm/ are never overwritten. Round 2 variants A/B/C
    # write here; Variant A may additionally READ-THROUGH to the
    # Round 1 cache dir for byte-identical-prompt cache hits.
    llm_cache_dir_round2: Path
    llm_raw_cache_dir_round2: Path
    anthropic_api_key: str | None
    openai_api_key: str | None
    model_id_override: dict[str, str] = field(default_factory=dict)

    def resolve_model_id(self, requested: str) -> str:
        """Return the override target if one is set for ``requested``, else ``requested``."""
        return self.model_id_override.get(requested, requested)

    def has_override(self, requested: str) -> bool:
        return requested in self.model_id_override


def _parse_override(raw: str) -> dict[str, str]:
    raw = (raw or "").strip()
    if not raw:
        return {}
    if "=" not in raw:
        raise ValueError(
            f"MODEL_ID_OVERRIDE must be of form '<from>=<to>', got: {raw!r}"
        )
    src, dst = raw.split("=", 1)
    src, dst = src.strip(), dst.strip()
    if not src or not dst:
        raise ValueError(
            f"MODEL_ID_OVERRIDE has empty source or target: {raw!r}"
        )
    return {src: dst}


def load_config(project_root: Path | None = None) -> Config:
    """Load environment variables from ``.env`` and resolve all paths.

    The ``.env`` file is optional in Milestone A (no API calls happen yet);
    ``load_dotenv`` is a no-op when the file is missing.
    """
    root = project_root or PROJECT_ROOT
    load_dotenv(dotenv_path=root / ".env", override=False)

    cache_dir = root / ".cache"
    output_dir = root / "outputs"
    repos_cache_dir = cache_dir / "repos"
    llm_cache_dir = cache_dir / "llm"
    llm_raw_cache_dir = llm_cache_dir / "raw"
    llm_cache_dir_round2 = cache_dir / "round2" / "llm"
    llm_raw_cache_dir_round2 = llm_cache_dir_round2 / "raw"
    for d in (
        cache_dir,
        output_dir,
        repos_cache_dir,
        llm_cache_dir,
        llm_raw_cache_dir,
        llm_cache_dir_round2,
        llm_raw_cache_dir_round2,
    ):
        d.mkdir(parents=True, exist_ok=True)

    return Config(
        project_root=root,
        cache_dir=cache_dir,
        output_dir=output_dir,
        repos_cache_dir=repos_cache_dir,
        llm_cache_dir=llm_cache_dir,
        llm_raw_cache_dir=llm_raw_cache_dir,
        llm_cache_dir_round2=llm_cache_dir_round2,
        llm_raw_cache_dir_round2=llm_raw_cache_dir_round2,
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY") or None,
        openai_api_key=os.environ.get("OPENAI_API_KEY") or None,
        model_id_override=_parse_override(os.environ.get("MODEL_ID_OVERRIDE", "")),
    )
