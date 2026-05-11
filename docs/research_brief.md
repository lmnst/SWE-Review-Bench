# SWE-Review-Bench: a pilot benchmark for cold code-review bug finding on SWE-bench Lite

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
file) tuple in the 20-instance pilot is checked for verbatim
problem-statement, hints-text, patch-marker, test-patch, test-name,
and oracle-line-number leakage. The pilot uses
`princeton-nlp/SWE-bench_Lite`, `split=test`, 20 instances sampled
with `seed=42`.

## Preliminary results

Round 1 baseline (default prompt, tolerance N=3) gives the following
instance-hit-rate point estimates with Wilson 95% intervals: Claude
Sonnet 4.5 hits 0/20 instances (0%, [0.000, 0.161]); GPT-4o-mini
hits 3/20 (15%, [0.052, 0.360]); the static union of filtered Ruff
and Pylint warnings also hits 3/20 (15%, [0.052, 0.360]). False
positives per instance are 1.50, 2.20, and 11.75 respectively. At
the file level (did the reviewer say anything at all on an oracle
file, regardless of line numbers) the ordering inverts: Claude hits
16/20 (80%, [0.584, 0.919]), GPT 13/20 (65%, [0.433, 0.819]),
static 15/20 (75%, [0.531, 0.888]). Claude is the most willing of
the three to put a comment on the right file, but its comments under
Round 1's prompt land far enough from the actual fix region that
none of them count at tolerance 3.

A controlled Round 2 sweep on the same 20 instances varied the
prompt while holding the model, tolerance, and oracle constant.
Variant A is the Round 1 baseline. Variant B removes only the
no-speculation clause `"Do not invent issues. If the code looks
correct to you, return an empty list."` from the template body.
Under Variant A versus Variant B, Claude moves from 0/20 (0%,
[0.000, 0.161]) to 3/20 (15%, [0.052, 0.360]), and GPT-4o-mini from
3/20 (15%, [0.052, 0.360]) to 6/20 (30%, [0.145, 0.519]). The
Wilson intervals for A and B overlap at n=20, so the deltas are
direction-of-effect rather than statistically resolved comparisons.
A third variant that forces at least one comment per file is
treated as a diagnostic probe only and is not used as a headline
result.

## Diagnostic finding

The combination of Claude's 0/20 line-level rate and its 16/20
file-level rate, together with the Variant A versus Variant B
movement, is consistent with a prompt-sensitivity effect rather
than a model inability. Under the Round 1 prompt the no-speculation
clause appears to suppress Claude's output rate and to push its
comments away from the actual fix region; relaxing that clause
raises its pilot instance hit rate to the same point estimate that
GPT-4o-mini held under the original prompt. The same change raises
GPT-4o-mini in absolute terms but does not collapse the
prompt-sensitivity gap between the two reviewers. The conservative
reading is that Claude in the cold-review setting is more sensitive
to hedge or no-speculation instructions than GPT-4o-mini, and that
externally reportable headline numbers for either model depend on
the prompt variant chosen as canonical. The pilot does not support
a general model-capability ranking on bug finding, and the
benchmark is not designed to produce one.

## Reproducibility commitment

Round 1 and Round 2 artefacts are frozen; a sha256 manifest
(`outputs/round2/baseline_manifest.json`) tracks any later
modification. The sampling seed is `42`, the tolerance is `3`, the
prompt template id is recorded with each cache entry, and the LLM
cache is partitioned by round so Round 1 entries remain read-only
during Round 2 experiments. A pytest leakage suite covers all 60
(instance, variant) cells in the pilot. A one-command reproduction
script (`repro/run.sh`) and a per-artefact manifest are part of the
repository.

## About

SWE-Review-Bench is built and maintained by an independent CS
master's student. The current contribution is an evaluation
pipeline and a 20-instance pilot study for cold code-review bug
finding on SWE-bench Lite.

- Contact: lmnstzz@gmail.com
- GitHub: github.com/lmnst
- Repository: github.com/lmnst/SWE-Review-Bench
