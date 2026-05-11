# SWE-Review-Bench

A pilot benchmark for **cold code-review bug finding** on SWE-bench Lite.

## Motivation

SWE-bench measures whether a system can resolve a known issue when
given the issue text, the failing tests, and the surrounding repo.
That is a *fix-given-issue* task: the system already knows where to
look. A different and arguably harder question is whether a system
can **locate** a defect from the source alone, without an issue
report or failing tests to anchor on. The skill exercised in a real
pre-commit code review, "is something wrong with this file?", is
not what SWE-bench fix-resolved rate measures.

SWE-Review-Bench evaluates LLM-based and static reviewers under the
cold-review setup: the reviewer is shown only the buggy file at its
pre-fix commit and asked to flag concrete correctness, reliability,
or maintainability issues in a structured JSON format. The oracle
(the fix patch's line ranges) is read **only** by the scorer, after
the reviewer has emitted its output.

## Task definition

For each instance in the dataset, the reviewer's input is exactly:

- `file_path`: relative path of one file touched by the fix patch.
- `file_content`: full pre-fix source content of that file, at the
  instance's `base_commit`.
- A generic review instruction (the prompt template body).
- The output JSON schema.

The reviewer's output is a JSON array of comments matching:

```json
{
  "file": "django/http/response.py",
  "line_start": 173,
  "line_end": 173,
  "severity": "low | medium | high",
  "message": "one short sentence"
}
```

The scorer then matches each comment's `(file, line_start, line_end)`
against oracle hunks recovered from the fix patch, under a line
tolerance `N` (default `N = 3`). An instance counts as a **hit** if
at least one comment matched any oracle hunk on that instance.

The cold-review input policy and the corresponding pytest assertions
are documented in `docs/leakage_statement.md` and
`tests/test_no_leakage.py`. The reviewer's input never contains
`problem_statement`, `hints_text`, `patch`, `test_patch`, test names
extracted from `test_patch`, or oracle line numbers.

## Dataset

- Source: [`princeton-nlp/SWE-bench_Lite`](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Lite), `split=test`.
- Sampling: `random.Random(42).sample(range(len(ds)), 20)`, a
  deterministic 20-instance pilot.
- Dataset revision: not pinned at Round 1 load time; recorded in
  `outputs/run_meta.json` is the load timestamp (2026-05-11) and the
  `litellm` and `datasets` versions used.

This is a 20-instance pilot drawn from SWE-bench Lite's 300-instance
test split. All headline numbers below carry Wilson 95% confidence
intervals to make the small-sample uncertainty visible.

## Reviewers

Round 1 evaluated three reviewers:

| reviewer       | id (resolved) | source                                  |
|---|---|---|
| Claude Sonnet  | `claude-sonnet-4-5`  | Anthropic API via `litellm` 1.83.9 |
| GPT-4o-mini    | `gpt-4o-mini`        | OpenAI API via `litellm` 1.83.9    |
| Static union   | `static`             | Ruff (`F,E9,B,A`) ∪ Pylint (default minus `C,R,I,import-error,no-name-in-module`) |

Static reviewer is intentionally Python-only and runs locally; both
LLM reviewers are accessed through `litellm` so the same client code
handles both providers. Static comments are capped at
`--max-comments-per-file 20` to keep the false-positive count
bounded. Round 2 prompt-variant experiments evaluate only the two
LLM reviewers; the static baseline is variant-agnostic.

## Metrics

Reviewer outputs are scored under `--tolerance N` (default 3) against
oracle hunks built with `swe_review_bench.data.oracle.build_oracle_sites`
in `strict_mode=False` (one site per hunk, line range covering the
full hunk source range).

| metric                  | definition                                                                                          |
|---|---|
| `instance_hit_rate`     | instances where the reviewer hit ≥1 oracle hunk under tolerance N, over total instances scored (20). |
| `site_recall`           | oracle sites hit, over total oracle sites across scored instances (32 in the pilot).                |
| `file_level_hit_rate`   | instances where the reviewer emitted ≥1 valid comment on any oracle file, ignoring line numbers.    |
| `false_positives_per_instance_mean` | mean of `n_comments - n_hits` across instances.                                            |
| `precision@k`           | mean over instances of `(#hits within top-k by severity-desc then line-asc) / min(k, n_comments)`.  |

`precision@k` confidence intervals are not reported in this pilot
because the denominator differs per instance (clipped to `min(k,
n_comments)`); a CI would require either bootstrapping over instances
on the per-comment data or a different aggregation. The CSV column
order in `outputs/round2/h_lite/round1_with_ci.csv` marks these CI
columns `unavailable`.

### Tolerance sensitivity

Hit-rate under three tolerance values, derived post-hoc from the
Round 1 per-comment distances (numerator: instances with ≥1 comment
whose minimum line-gap to an oracle hunk in the same file is ≤ N;
denominator: 20). Wilson 95% CIs in brackets:

| reviewer          | t = 0          | t = 3 (default)            | t = 10         |
|---|---|---|---|
| `claude-sonnet-4-5` | 0/20 = 0% [0.000, 0.161] | 0/20 = 0% [0.000, 0.161] | 1/20 = 5% [0.009, 0.236] |
| `gpt-4o-mini`       | 2/20 = 10% [0.028, 0.301] | 3/20 = 15% [0.052, 0.360] | 4/20 = 20% [0.081, 0.416] |
| `static`            | 2/20 = 10% [0.028, 0.301] | 3/20 = 15% [0.052, 0.360] | 5/20 = 25% [0.112, 0.469] |

`t = 3` is the default; `t = 10` raises every reviewer by at most a
couple of instances. The dominant failure mode for Claude in Round 1
is **not** "right region, just outside tolerance"; it is "right
file, wrong region by tens of lines". See §Diagnostic Round.

## Preliminary results

Round 1 baseline, all three reviewers, default prompt `v1`,
`tolerance = 3`. Rate cells show `count / 20` (or `/ 32` for
`site_recall`) followed by the Wilson 95% interval.

| reviewer          | instance hit rate           | file-level hit rate         | site recall                  | FP / instance |
|---|---|---|---|---:|
| `claude-sonnet-4-5` | 0 / 20 = 0% [0.000, 0.161]  | 16 / 20 = 80% [0.584, 0.919] | 0 / 32 = 0% [0.000, 0.107]   | 1.50 |
| `gpt-4o-mini`       | 3 / 20 = 15% [0.052, 0.360] | 13 / 20 = 65% [0.433, 0.819] | 3 / 32 = 9% [0.032, 0.242]   | 2.20 |
| `static`            | 3 / 20 = 15% [0.052, 0.360] | 15 / 20 = 75% [0.531, 0.888] | 4 / 32 = 13% [0.050, 0.281]  | 11.75 |

Because this is a 20-instance pilot, confidence intervals are wide
and the results should not be interpreted as a conclusive model
ranking.

The numerator and denominator counts above are emitted in machine-
readable form at `outputs/round2/h_lite/round1_with_ci.csv`. The
Wilson formula, denominators, and the deliberate omission of
continuity correction are documented in
`outputs/round2/h_lite/ci_methodology.md`.

## Diagnostic round: prompt sensitivity

Round 2 swept three prompt variants on the same 20-instance pilot
for the two LLM reviewers only:

- **Variant A**: Round 1 baseline (`v1`); byte-identical, reused
  Round 1's cache so cost was $0.
- **Variant B**: same body with the no-speculation clause removed
  (`v1b`). The deleted sentence is `"Do not invent issues. If the
  code looks correct to you, return an empty list."`
- **Variant C**: Variant B plus `"Return at least one comment per
  file, even if it is a minor observation."` (`v1c`). **Variant C is
  a diagnostic-only probe that forces ≥1 comment per file; it is not
  used as a headline result.**

Comparison of Variant A and Variant B for the two LLM reviewers:

| reviewer            | A: instance hit rate         | B: instance hit rate         | B vs A |
|---|---|---|---:|
| `claude-sonnet-4-5` | 0 / 20 = 0% [0.000, 0.161]   | 3 / 20 = 15% [0.052, 0.360] | +15 pp |
| `gpt-4o-mini`       | 3 / 20 = 15% [0.052, 0.360]  | 6 / 20 = 30% [0.145, 0.519] | +15 pp |

Under the Round 1 prompt, Claude's output rate and hit rate are more
sensitive to hedge/no-speculation instructions than GPT-4o-mini's;
relaxing the no-speculation clause raises Claude's pilot instance
hit rate from 0% to 15% with the Wilson interval shown above. Note
that the Wilson intervals for A and B overlap at n = 20, so the
point-estimate deltas are direction-of-effect only and not a
statistically resolved comparison. The companion artefact for these
numbers is `outputs/round2/h_lite/variant_summary_with_ci.csv`; the
qualitative analysis is in `outputs/round2/variant_analysis.md`.

Variant C and an extended per-bucket discussion live in
`outputs/round2/diagnostic_summary.md` and
`outputs/round2/variant_analysis.md`.

## Reproducibility

One-command reproduction:

```bash
bash repro/run.sh
```

Key fingerprint values:

| field                | value                                       |
|---|---|
| dataset              | `princeton-nlp/SWE-bench_Lite`, split `test` |
| sampling seed        | `42`                                        |
| `n_requested`        | 20                                          |
| `tolerance`          | 3                                           |
| `max_comments_per_file` | 20                                       |
| `prompt_template_id` (Variant A) | `v1`                            |
| Variant B / C template ids | `v1b` / `v1c`                         |
| `strict_oracle_mode` | `false`                                     |
| `litellm` version    | `1.83.9`                                    |
| Python               | `3.9.12`                                    |

Cache behaviour: Round 1 LLM responses live under `.cache/llm/` and
are read-only for Round 2. Round 2 writes to `.cache/round2/llm/`.
Variant A's cache key matches Round 1's (same `template_id`); a
re-run under Variant A is a 100% cache hit. Variants B and C miss
the cache on first run and cost about $1.9 in aggregate for the 20-
instance pilot. The full `run_meta.json` records the resolved model
ids, wall time, and run timestamp.

## Leakage prevention

The cold-review input policy is documented in
`docs/leakage_statement.md`. The corresponding pytest assertions are
in `tests/test_no_leakage.py` (60 parametrised cells = 20 instances ×
3 variants); the latest pass/fail summary is at
`outputs/round2/h_lite/leakage_audit_report.md`.

To re-run the leakage tests:

```bash
pytest -v tests/test_no_leakage.py
```

## Limitations

- **Small sample.** `n = 20` is a pilot; Wilson 95% intervals are
  wide and pairwise deltas overlap at this size. Headline numbers
  should be read as direction-of-effect, not as a conclusive
  ranking.
- **Single-file review only.** Each reviewer is shown one file per
  instance (the file touched by the fix patch). Cross-file
  reasoning, retrieval, or multi-file context is out of scope for
  the pilot.
- **Tolerance sensitivity not exhaustively swept.** Only `t ∈ {0,
  3, 10}` was evaluated post-hoc.
- **Dataset composition.** SWE-bench Lite is itself a curated subset
  of SWE-bench and skews toward a handful of large Python projects;
  the 20-instance pilot inherits any such bias.
- **Static baseline filtering.** Ruff is invoked with
  `--select F,E9,B,A`; Pylint is invoked with
  `--disable=C,R,I,import-error,no-name-in-module`. These choices
  are documented in `swe_review_bench/reviewers/static.py` and were
  picked to keep the FP count tractable while preserving most
  correctness-flavoured warnings.
- **Prompt sensitivity.** The Diagnostic Round shows the Round 1
  prompt suppresses LLM output rates; reported headline numbers
  depend on the prompt variant chosen as canonical.
- **No formal model ranking.** This benchmark does not claim
  "model X is better than model Y at code review". The pilot metric
  comparisons surface prompt-sensitivity and FP/recall trade-offs
  only.

## License

MIT, see [`LICENSE`](LICENSE).

## About

SWE-Review-Bench is built and maintained by an independent CS
master's student. The pilot in this repository is the current
contribution: an evaluation pipeline, a 20-instance run with
frozen artefacts, a prompt-variant probe, and a pytest leakage
suite.

- Contact: lmnstzz@gmail.com
- GitHub: github.com/lmnst
- Repository: github.com/lmnst/SWE-Review-Bench

Reference this work by citing the repository.
