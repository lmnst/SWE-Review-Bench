# v0.1-pilot

Released 2026-05-12

## Scope

This pilot release covers a 20-instance evaluation drawn from
SWE-bench Lite's 300-instance test split. Three reviewers are scored
under the cold-review input policy: Claude Sonnet 4.5, GPT-4o-mini,
and a static union of Ruff and Pylint. The release also includes the
Round 2 prompt-variant probe (variants A, B, and C across the two
LLM reviewers) and the H-lite hardening pass that adds Wilson 95%
confidence intervals, a parametrised pytest leakage suite, and a
post-hoc dataset revision snapshot.

## Contents

- Pipeline source under `swe_review_bench/`
- Frozen Round 1 outputs at `outputs/`
- Frozen Round 2 diagnostic outputs at `outputs/round2/`
- H-lite derived outputs at `outputs/round2/h_lite/`
- Reproducibility shell at `repro/run.sh`
- Pytest leakage suite at `tests/test_no_leakage.py`

## Headline numbers

- Claude Sonnet 4.5 file-level hit rate: 16 / 20 = 80% [0.584, 0.919] (`outputs/round2/h_lite/round1_with_ci.csv`).
- Claude Sonnet 4.5 instance hit rate: 0 / 20 = 0% [0.000, 0.161] (same CSV).
- GPT-4o-mini instance hit rate: 3 / 20 = 15% [0.052, 0.360] (same CSV).
- Static union instance hit rate: 3 / 20 = 15% [0.052, 0.360] (same CSV).
- Variant B vs Variant A delta for both LLM reviewers: +15 percentage points (`outputs/round2/h_lite/variant_summary_with_ci.csv`).

## Reproducibility

The dataset revision snapshot is recorded at
`outputs/round2/h_lite/dataset_revision.json`. The sampling seed is
`42`, the canonical prompt template id is `v1` (Variant A), and
Round 1 LLM responses live under `.cache/llm/` as read-only inputs
consumed by Round 2 (which writes to `.cache/round2/llm/`).

## Known limitations

See the Limitations section of `README.md` for the full list.

## Not in this release

- Full SWE-bench Lite scaling (planned next phase)
- SWE-bench Verified
- Cross-file or retrieval-augmented review
- Hybrid LLM plus static reviewer
- Calibration or self-critique experiments
