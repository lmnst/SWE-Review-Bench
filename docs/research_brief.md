# SWE-Review-Bench: a benchmark for cold code-review bug finding on SWE-bench Lite

## Research question

Can an LLM-based or static code reviewer locate the buggy code in a
real SWE-bench Lite instance from the source file alone, with no
issue text, no failing tests, and no other oracle hints?

## Why SWE-bench's fix-resolved rate is not a measure of bug finding

SWE-bench measures whether a system can produce a patch that resolves
a reported issue when handed the issue text, the failing tests, and
the surrounding repository. That is a fix-given-issue task: the
system already knows where to look and what symptom to chase. A
pre-commit code review exercises a different skill, "is something
wrong with this file?", and that is the question SWE-Review-Bench
asks. The benchmark reuses SWE-bench Lite's curated bugs so the
oracle is grounded in real merged fixes rather than synthetic
defects.

## Task setup

For each instance the reviewer is given one file: its pre-fix source
content at the recorded `base_commit`, plus the file path and a
generic review instruction. The reviewer emits a JSON array of
comments with `(file, line_start, line_end, severity, message)`
fields. The oracle (line ranges recovered from the fix patch's hunks
under `strict_mode=False`) is read only by the scorer, after the
reviewer has finished. An instance counts as a hit when at least one
comment matches any oracle hunk under a line tolerance N (default
N=3). The cold-review input policy and the pytest assertions that
enforce it are kept under `docs/leakage_statement.md` and
`tests/test_no_leakage.py`, where every (instance, prompt variant,
file) tuple in the 100-instance study is checked for verbatim
problem-statement, hints-text, patch-marker, test-patch, test-name,
and oracle-line-number leakage. The study uses
`princeton-nlp/SWE-bench_Lite`, `split=test`, 100 instances sampled
with `seed=42`. The 100 instances are a strict superset of the
original 20-instance pilot under `seed=42`, so the pilot's cached
reviewer outputs are reused rather than re-billed.

## Preliminary results

At n=100 (default prompt variant A, tolerance N=3), instance hit
rates with Wilson 95% intervals are: Claude Sonnet 4.5 12/100 (0.12,
[0.070, 0.198]); GPT-4o-mini 7/100 (0.07, [0.034, 0.137]); the
static union of filtered Ruff and Pylint warnings 27/100 (0.27,
[0.193, 0.364]). False positives per instance are 1.60, 1.99, and
12.41 respectively: the static union reaches its hit rate only by
emitting far more comments. At the file level (did the reviewer
comment on an oracle file at all, ignoring line numbers) Claude
reaches 0.83 and GPT 0.51.

A controlled prompt sweep varied one clause while holding the model,
tolerance, and oracle constant. Variant A is the baseline. Variant B
removes only the no-speculation clause `"Do not invent issues. If the
code looks correct to you, return an empty list."` from the template
body. Under Variant A versus Variant B, GPT-4o-mini moves from 0.07
to 0.29 and Claude from 0.12 to 0.16. A third variant that forces at
least one comment per file is a diagnostic probe only and was not
scaled past the pilot. The 100 instances are a strict superset of the
original 20-instance pilot, so the pilot's most eye-catching number,
Claude scoring 0/20 under Variant A, is resolved as a small-sample
artefact. Full tables, the tolerance sweep, and per-cell intervals
are in `docs/preliminary_results.md` and `outputs/n100/`.

## Diagnostic finding

The prompt effect is model-specific. A paired McNemar test on the
n=100 A-versus-B contrast moves GPT-4o-mini decisively (22 instances
flip to a hit, 0 flip away, exact p < 0.0001) but does not
significantly move Claude (7 flip in, 3 out, p = 0.34). At n=20 the
effect looked shared, and even looked stronger for Claude, but that
reading was driven by Claude's 0/20 artefact; at n=100 the
sensitivity is specific to GPT-4o-mini. A consequence is that a
single-prompt benchmark reports a prompt-dependent ranking: under
the baseline prompt Claude and GPT are statistically
indistinguishable (p = 0.33), while under Variant B GPT's hit rate
is significantly higher (p = 0.015), though that advantage is
volume-driven (565 comments to Claude's 237). The benchmark does not
support a general model-capability ranking on bug finding and is not
designed to produce one.

A 30-instance hand audit of the oracle puts a construct-validity
ceiling on these rates: only 24 of 48 oracle sites mark an actual
defect (0.50, [0.36, 0.64]), and 10 of 30 instances carry no
cold-reviewable bug, six of them feature or enhancement requests.
Headline rates should be read with that oracle noise in mind. The
method and per-site verdicts are in
`outputs/n100/oracle_validity_report.md`.

## Reproducibility commitment

The n=20 Round 1 and Round 2 artefacts remain frozen; a sha256
manifest (`outputs/round2/baseline_manifest.json`) tracks any later
modification. The n=100 artefacts live under `outputs/n100/`. The
sampling seed is `42`, the headline tolerance is `3`, the prompt
template id is recorded with each cache entry, and the LLM cache is
partitioned so the Round 1 entries stay read-only. The pytest
leakage suite covers all 100 instances across the prompt variants. A
cache-safe reproduction script (`repro/run.sh`) and a per-artefact
manifest are part of the repository.

## About

SWE-Review-Bench is built and maintained by an independent CS
master's student. The current contribution is an evaluation
pipeline, an n=100 preliminary study with frozen artefacts and
paired-comparison statistics, a 30-instance oracle-validity audit,
and a pytest leakage suite, for cold code-review bug finding on
SWE-bench Lite.

- Contact: lmnstzz@gmail.com
- GitHub: github.com/lmnst
- Repository: github.com/lmnst/SWE-Review-Bench
