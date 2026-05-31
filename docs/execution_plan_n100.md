# SWE-Review-Bench: n=100 preliminary study, execution plan

Status: DRAFT for review. No code changes and no API spend happen until
the gates in section 0 are signed off.

This plan extends the frozen n=20 pilot to a self-funded n=100
preliminary study at a fixed dataset revision and seed. It does not
replace the credit-funded full-Lite plan in `docs/budget_request.md`; it
is the intermediate step between the pilot and any externally funded
n=300 run, and it needs no external credits. It is also the written PRD
update that the project's working rules require before scaling sample
size or adding the paired-comparison and tolerance-sweep analyses.

## 0. Decision gates

Two points need explicit sign-off. Everything else follows mechanically.

- Gate 1 (scope and budget, before any code). Which prompt variants are
  scaled to n=100.
  - Recommended: scale Variant A (`v1`, suppression clause) and Variant
    B (`v1b`, no suppression) to n=100; keep Variant C at n=20 as a
    diagnostic probe. This preserves the A-vs-B prompt-sensitivity
    contrast, which is the pilot's central finding, at the larger sample.
    Estimated LLM spend $7 to $9; hard cap $10.
  - Cheaper alternative: scale only Variant B to n=100 as the single
    canonical headline; leave Variant A at n=20 as the historical Round 1
    baseline. Estimated spend $4 to $5; hard cap $6. The A-vs-B contrast
    then exists only at n=20.
- Gate 2 (spend authorization, after the zero-cost dry run). Confirm the
  dry-run call count and projected cost before the first paid Claude
  call. The runner also aborts itself at 0.9 x hard cap.

## 1. Objective and scope

Objective: raise the pilot from n=20 to n=100 so the headline rates carry
Wilson intervals roughly half as wide, the prompt-sensitivity contrast (A
vs B) is measured on a non-trivial sample, and the small-sample artefact
of Claude scoring exactly 0/20 under Variant A is resolved. SWE-bench Lite
is a single-file-fix subset: the n=100 dry run confirms all 100 sampled
instances touch exactly one non-test file, so this study does not add a
multi-file breakdown. That would need full SWE-bench or the Verified
split, which stay out of scope.

In scope:
- n=100 run of {`claude-sonnet-4-5`, `gpt-4o-mini`, `static`} at the
  canonical variant(s) chosen in Gate 1.
- Wilson intervals (existing), paired McNemar comparison (new, zero API),
  tolerance sweep N in {0, 3, 10} by offline rescoring (new, zero API).
- Leakage suite extended to cover all 100 instances.
- Updated `docs/preliminary_results.md`, the figure, and `run_meta`.

Out of scope, deferred to the credit-funded plan with no work here: full
Lite (n=300), additional models, prompt variants beyond A/B/C, multi-seed
robustness, the Verified split, confidence calibration. These stay as
written in `docs/budget_request.md`.

## 2. Frozen configuration

| field | value |
|---|---|
| dataset | `princeton-nlp/SWE-bench_Lite` |
| dataset revision | pinned in `outputs/round2/h_lite/dataset_revision.json` (`hf_commit_sha`) |
| split | `test` |
| seed | 42 |
| n | 100 |
| tolerance (headline) | 3 |
| max_comments_per_file | 20 |
| oracle | `strict_mode=False` |
| reviewers | `claude-sonnet-4-5`, `gpt-4o-mini`, `static` |
| variants | per Gate 1 (recommended A + B) |
| python | 3.9.12 (pinned) |
| litellm | 1.83.9 (`repro/requirements.lock`) |

Subset guarantee (verified): under Python 3.9.12 at this dataset
revision, `Random(42).sample(range(300), 20)` is an exact subset of
`...sample(range(300), 100)`, all 20 of 20. The pilot instances are a
strict subset of the 100, so their cached reviewer outputs are reused,
not re-billed.

Precondition: the guarantee depends on the CPython 3.9.12 `random.sample`
implementation and on the dataset still having 300 rows at the pinned
revision. The run must use the pinned venv and revision; a Python or
revision change can silently change the sample and turn cache hits into
paid misses. Step 6.0 asserts the 20 ids are present in the 100 before
any spend.

## 3. Prompt variant decision (Gate 1 detail)

| variant | template | role | scale to 100 |
|---|---|---|---|
| A | `v1`, keeps "Do not invent issues / return an empty list" | Round 1 baseline; suppresses Claude to 0/20 at the line level | recommended yes |
| B | `v1b`, suppression clause removed, nothing else changed | neutral prompt; the honest comparison point | recommended yes |
| C | `v1c`, B plus "return at least one comment per file" | force-emit diagnostic upper bound | no, stays n=20 |

The pilot's finding is prompt sensitivity, not a model ranking;
`docs/research_brief.md` states the benchmark is not designed to rank
model capability. That finding lives in the A-vs-B gap, so both A and B
should reach n=100 for the contrast to be reportable. C is a probe by
construction and must not be scaled or used as a headline.

## 4. Cache and cost model

Cache partitioning (confirmed in `reviewers/llm.py`): every variant reads
`.cache/round2/llm/` first; Variant A additionally reads through to the
read-only Round 1 cache `.cache/llm/`. All writes go to
`.cache/round2/llm/`; the Round 1 cache is never written. The cache key
is `sha256(resolved_model, template_id, file_path, file_content)` and
does not include the instance id, so a reused instance hits as long as
its file content is byte-identical, which it is because the instance
fixes the `base_commit`.

Observed per-call costs from pilot artefacts; one call is one reviewed
file:

| reviewer | variant A ($/call) | variant B ($/call) |
|---|---:|---:|
| `claude-sonnet-4-5` | 0.04369 | 0.04597 |
| `gpt-4o-mini` | 0.00180 | 0.00195 |
| `static` | 0 | 0 |

Projection for the recommended A+B scope, reusing the 20 cached instances
and billing only the 80 new ones:

| line | new calls | est. cost |
|---|---:|---:|
| Claude, variant A, 80 new instances | 80 | $3.50 |
| Claude, variant B, 80 new instances | 80 | $3.68 |
| GPT, variants A + B, 160 new instances | 160 | $0.30 |
| static, all | n/a | $0 |
| total | | $7.47 |

The n=100 dry run confirms all 100 instances touch exactly one non-test
file (SWE-bench Lite is a single-file-fix subset), so the call count
equals the instance count and these figures are near-exact rather than
loose upper bounds; the only downward adjustment is a file occasionally
missing at base_commit or binary, which a checkout skips. The hard cap is
$10 for the recommended scope, $6 for the B-only scope, enforced by the
runner's abort-at-0.9x-cap mechanism.

## 5. Engineering changes, each with an acceptance test

5.1 Parameterise the runner. Add parameters to `diagnostics/f3_runner.run()`:
`n=20`, `variants=("A","B","C")`, `reviewers=LLM_REVIEWERS`,
`output_dir=ROUND2_DIR`, `hard_cap=5.0`. Defaults reproduce today's
behaviour byte for byte. Expose them through an argparse CLI. Add a
`--dry-run` mode that loads instances, builds oracle sites, counts
reviewer-input files, asserts the 20-id subset, and prints the projected
call count and cost with no API call. Static is not added to this
LLM-only runner; it is produced separately in step 6.1.
  - Acceptance: re-running with defaults reproduces
    `outputs/round2/variant_summary.csv` unchanged against the frozen
    manifest; a forced-low-cap unit test still triggers the abort.

5.2 Extend the leakage suite to n=100. `tests/test_no_leakage.py`
hard-codes 20 ids and loads `n=20`. Move the fixtures to `n=100`,
regenerate `outputs/round2/oracle_index.json` for 100 instances, and
either extend `INSTANCE_IDS` to the 100 ids or assert `len == 100`
dynamically. Hard safety gate: no Claude call on a new instance until its
prompt has passed the no-leak assertions.
  - Acceptance: `pytest tests/test_no_leakage.py` passes for all 100
    instances, every scaled variant, every file.

5.3 Paired comparison, new, zero API. Add `diagnostics/paired_comparison.py`:
from the n=100 `variant_results.csv`, reduce to a per-(reviewer, variant,
instance) hit boolean, then run McNemar's exact test for the reviewer
contrast (Claude vs GPT within a variant) and the prompt contrast (A vs B
within a reviewer). The exact two-sided p-value is computed directly from
the binomial null, with no external statistics dependency.
  - Acceptance: a unit test on a hand-built 2x2 table matches a known
    McNemar p-value.

5.4 Tolerance sweep, new, zero API. Add `diagnostics/tolerance_sweep.py`:
re-score the stored per-comment line ranges against rebuilt oracle sites
at N in {0, 3, 10} using the existing `scoring.matching.match_comments`,
with no re-billing. Emit one table per tolerance.
  - Acceptance: at N=3 the swept numbers reproduce the headline
    `instance_hit_rate` from the n=100 summary exactly.

## 6. Execution sequence, cheap to expensive, gated

0. Dry run, no spend.
   `python -m swe_review_bench.diagnostics.f3_runner --dry-run --n 100 --variants A,B`
   Asserts the 20-id subset, prints exact projected call counts and cost.
   Input to Gate 2.
1. static, n=100. Cost $0. static is variant-agnostic, one pass.
   `python -m swe_review_bench.run --n 100 --reviewers static --output-dir outputs/n100/static`
2. GPT-4o-mini, n=100, variants A+B. A few cents. Validates the runner
   end to end on the cheap model and warms the GPT cache.
   `python -m swe_review_bench.diagnostics.f3_runner --n 100 --variants A,B --reviewers gpt-4o-mini --output-dir outputs/n100 --hard-cap 1`
3. Leakage suite at n=100 (5.2). Must pass. Hard gate before any Claude
   call. `pytest tests/test_no_leakage.py`
4. Gate 2 here. Then Claude plus GPT, n=100, variants A+B; GPT is all
   cache hits from step 2, so this bills only Claude. Hard cap $10; the
   runner aborts at $9 and preserves partial rows.
   `python -m swe_review_bench.diagnostics.f3_runner --n 100 --variants A,B --reviewers claude-sonnet-4-5,gpt-4o-mini --output-dir outputs/n100 --hard-cap 10`
5. Stats, zero API: Wilson (existing), McNemar (5.3), tolerance sweep
   (5.4).
6. Update `docs/preliminary_results.md`, the figure, `run_meta`, and the
   manifest. Re-freeze.

## 7. Definition of done

- [ ] `outputs/n100/` holds results.csv, summary.csv with Wilson CIs, and
      run_meta.json for {claude, gpt, static} x {A, B}.
- [ ] `pytest tests/` is green, including the n=100 leakage suite.
- [ ] McNemar tables (reviewer and prompt contrasts) and tolerance-sweep
      tables are written under `outputs/n100/`.
- [ ] `docs/preliminary_results.md` is updated to n=100 with intervals;
      the "n=20 pilot" framing is replaced by "n=100 preliminary study";
      an honest note records that reviewer differences may stay
      non-significant.
- [ ] Round 1 and Round 2 n=20 frozen artefacts are unchanged, verified
      against `baseline_manifest.json`.
- [ ] Actual spend is recorded and under the hard cap.
- [ ] `git log` is clean of co-author trailers, AI-assisted mentions, em
      dashes, and marketing filler.

## 8. Artefacts

New and regenerable: everything under `outputs/n100/`, the updated
`docs/preliminary_results.md` and figure.

Untouched and frozen: `outputs/summary.csv`, `outputs/results.csv`,
`outputs/round2/*` at n=20, and the `.cache/llm/` Round 1 cache. The
n=100 LLM cache accumulates under `.cache/round2/llm/`, append-only:
existing entries are reused, not rewritten.

## 9. Risks and rollback

- Silent paid miss from environment drift: mitigated by the step-0 subset
  assertion and the pinned venv and revision.
- Cost overrun on multi-file instances: mitigated by the dry-run exact
  projection and the runner's hard cap and abort file.
- Frozen-artefact clobber: mitigated by writing everything new under
  `outputs/n100/` and never reusing the Round 1 or Round 2 output paths;
  verified post-run against the manifest.
- Reviewer differences stay non-significant at n=100: an acceptable
  scientific outcome, reported honestly. The robust results (the
  false-positive and precision gaps, the multi-file breakdown, the
  prompt-sensitivity direction) do not depend on a significant
  Claude-vs-GPT gap.
- Rollback: the run only adds files under `outputs/n100/` and cache
  entries under `.cache/round2/llm/`; deleting `outputs/n100/` returns
  the repo to its pilot state.

## 10. What this plan does not do

No new reviewer models. No RAG. No confidence calibration. No Verified
split. No multi-seed run. No prompt variant beyond A/B/C. No change to
the oracle, the matcher, the scoring math, or the leakage policy. No
backwards-compatibility shims. Those items are either future scope in
`docs/budget_request.md` or explicitly excluded here.
