"""Load SWE-bench Lite and deterministically sample N instances.

The ``Instance`` dataclass intentionally retains every field shipped by
HuggingFace so the oracle, the repo cloner, and downstream tooling can each
read what they need. ``Instance`` is NEVER fed to a reviewer — only the
narrowly-scoped ``ReviewerInput`` (see ``reviewers/base.py``) is.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from datasets import load_dataset


@dataclass(frozen=True)
class Instance:
    """One SWE-bench Lite row, with all fields preserved.

    ``problem_statement``, ``patch``, and ``test_patch`` are oracle-only
    fields. They MUST NOT be passed to a reviewer.
    """

    instance_id: str
    repo: str
    base_commit: str
    patch: str
    test_patch: str
    problem_statement: str
    environment_setup_commit: str | None = None
    version: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Instance":
        return cls(
            instance_id=row["instance_id"],
            repo=row["repo"],
            base_commit=row["base_commit"],
            patch=row["patch"],
            test_patch=row.get("test_patch") or "",
            problem_statement=row.get("problem_statement") or "",
            environment_setup_commit=row.get("environment_setup_commit") or None,
            version=row.get("version") or None,
        )


def load_instances(
    n: int,
    *,
    seed: int = 42,
    dataset: str = "princeton-nlp/SWE-bench_Lite",
    split: str = "test",
) -> list[Instance]:
    """Deterministically sample ``n`` instances.

    Sampling uses ``random.Random(seed).sample`` over the dataset's full
    index range, so the result is stable for a fixed dataset version.
    """
    ds = load_dataset(dataset, split=split)
    total = len(ds)
    if n > total:
        raise ValueError(f"Requested n={n} but dataset has only {total} rows.")
    rng = random.Random(seed)
    indices = sorted(rng.sample(range(total), n))
    return [Instance.from_row(ds[i]) for i in indices]
