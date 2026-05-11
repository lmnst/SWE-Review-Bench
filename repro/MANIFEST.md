# `repro/` manifest

This directory holds everything needed to reproduce the SWE-Review-Bench
20-instance pilot without spending money. `run.sh` is the entry point;
the lock file pins every Python dependency to the exact version used
to produce the pilot artefacts.

## Files

| path | description | step in `run.sh` |
|---|---|---|
| `repro/run.sh` | One-command cache-safe reproduction. By default issues no paid API calls; aborts cleanly if uncached LLM replay is requested but unsupported. | (this file) |
| `repro/requirements.lock` | `pip freeze` of the project's Python environment at the time of the pilot (Python 3.9.12, 92 packages). | step 3 (dependency verification) |
| `repro/MANIFEST.md` | This file. | n/a |

## Step → output map

`run.sh` proceeds in 7 steps. Steps 1–4 cost nothing and produce no
new files; they are diagnostics that confirm the environment and the
leakage policy. Steps 5–6 read frozen artefacts. Step 7 prints a
report locator. No step writes into `outputs/`, `outputs/round2/`,
`outputs/round2/h_lite/`, `docs/`, or `tests/`.

| step | action | reads | writes |
|---|---|---|---|
| 1 | print banner, document budget posture | n/a | stdout |
| 2 | check `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `RUN_PAID_REPLAY` | environment | stdout |
| 3 | check `repro/requirements.lock` against current environment | `repro/requirements.lock` | stdout |
| 4 | `pytest -v tests/test_no_leakage.py` (60 cells, all-pass on frozen artefacts) | `tests/test_no_leakage.py`, `swe_review_bench/`, `.cache/repos/`, `outputs/round2/oracle_index.json` | stdout, possibly `.pytest_cache/` |
| 5 | print Round 1 baseline summary with Wilson CIs | `outputs/round2/h_lite/round1_with_ci.csv` | stdout |
| 6 | print Round 2 variant comparison with Wilson CIs | `outputs/round2/h_lite/variant_summary_with_ci.csv` | stdout |
| 7 | print follow-on report locator | n/a | stdout |

## What `run.sh` does NOT do

- It does **not** re-invoke `python -m swe_review_bench.run` to
  reproduce Round 1's CSVs, because the orchestrator does not
  expose a fail-on-cache-miss flag. Re-invoking it could silently
  spend money on any cache miss.
- It does **not** re-invoke `python -m swe_review_bench.diagnostics.f3_runner`
  for the same reason: Variant B / C cache hits would replay
  byte-identically, but a cache-busted run would issue paid calls.
- It does **not** modify any artefact under `outputs/`. The frozen
  pilot is single-source-of-truth.
- It does **not** install dependencies. Step 3 only **checks**.
  Run `pip install -r repro/requirements.lock` separately if needed.

## Recovering the pilot from scratch (with paid calls)

A complete fresh reproduction (warm cache: free; cold cache: paid)
is:

```bash
# 0. Sanity (free)
bash repro/run.sh

# 1. Round 1 baseline (free if cache is warm; ~$0.91 if cold)
python -m swe_review_bench.run --n 20 --seed 42 --tolerance 3 \
    --reviewers claude-sonnet-4-5,gpt-4o-mini,static

# 2. Round 2 variant sweep (free if cache is warm; ~$1.92 if cold)
python -m swe_review_bench.diagnostics.f3_runner

# 3. Round 2 derived analyses (free; CPU only)
python -m swe_review_bench.diagnostics.baseline_manifest
python -m swe_review_bench.diagnostics.oracle_index
python -m swe_review_bench.diagnostics.comment_distribution
python -m swe_review_bench.diagnostics.traces
python -m swe_review_bench.diagnostics.oracle_sanity
python -m swe_review_bench.diagnostics.file_level_metrics
python -m swe_review_bench.diagnostics.f_prompt_variants_doc
python -m swe_review_bench.diagnostics.f_leakage_check
python -m swe_review_bench.diagnostics.f3_chart
python -m swe_review_bench.diagnostics.f3_analysis

# 4. H-lite hardening (free; CPU only)
python -m swe_review_bench.diagnostics.h1_safety_audit
python -m swe_review_bench.diagnostics.h2_wilson_ci
python -m swe_review_bench.diagnostics.h6_preliminary_results
pytest -v tests/test_no_leakage.py
```

These steps produce every file in `outputs/round2/MANIFEST.md`
(except `outputs/round2/diagnostic_summary.md`, which is
hand-authored).

## Determinism caveats

- The LLM cache (`.cache/llm/` for Round 1, `.cache/round2/llm/` for
  Round 2) makes every reviewer call byte-identical to the frozen
  pilot. Without the cache, individual LLM responses are stochastic.
  Variant A cache key matches Round 1's byte-for-byte (same template
  id `v1`); Variants B and C have new template ids `v1b` / `v1c`.
- The git-clone-and-checkout step (`ensure_repo_at_commit`) requires
  network access to GitHub for an initial clone. Cached repos under
  `.cache/repos/` make subsequent runs offline.
- HuggingFace `datasets` caches the dataset locally on first
  `load_dataset(...)` call; subsequent runs hit the local cache.
- The dataset revision is not pinned at Round 1 load time. If
  `princeton-nlp/SWE-bench_Lite` is re-released with different
  instance content, this script's leakage tests would still pass but
  the seed-42 instance set could shift. Treat this as a known
  fragility; documenting the revision is a follow-up to the Lite
  pinning gap noted in `README.md`.
