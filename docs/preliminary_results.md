# Preliminary results (SWE-Review-Bench, n=100 study)

Headline numbers from the SWE-Review-Bench n=100 preliminary study. The
sample is `princeton-nlp/SWE-bench_Lite`, `split=test`, `seed=42`, oracle
`strict_mode=False`, default tolerance N=3. The 100 instances are a strict
superset of the original 20-instance pilot (the pilot ids are a
deterministic subset under seed 42), so the pilot's cached reviewer
outputs are reused rather than re-billed. Wilson 95% intervals are given
for every instance-hit-rate cell. All 100 instances touch exactly one
non-test file: SWE-bench Lite is a single-file-fix subset, so there is no
multi-file breakdown at this scale.

## Reviewers and prompt variants

Three reviewers: `claude-sonnet-4-5`, `gpt-4o-mini`, and `static` (a
filtered union of Ruff and Pylint warnings). Two prompt variants are
scaled to n=100: Variant A (`v1`, the Round 1 baseline, which keeps the
clause "Do not invent issues. If the code looks correct to you, return an
empty list.") and Variant B (`v1b`, identical except that clause is
removed). The `static` reviewer is variant-agnostic. Variant C
(force-emit) is a diagnostic probe and was not scaled past the pilot.

## Headline (tolerance N=3)

| reviewer / variant | instance hit rate | file-level hit rate | site recall | FP / instance |
|---|---|---|---|---:|
| `claude-sonnet-4-5` A | 12/100 = 0.12 [0.070, 0.198] | 0.83 | 0.081 | 1.60 |
| `gpt-4o-mini` A | 7/100 = 0.07 [0.034, 0.137] | 0.51 | 0.047 | 1.99 |
| `claude-sonnet-4-5` B | 16/100 = 0.16 [0.101, 0.244] | 1.00 | 0.114 | 2.20 |
| `gpt-4o-mini` B | 29/100 = 0.29 [0.210, 0.385] | 0.97 | 0.201 | 5.15 |
| `static` | 27/100 = 0.27 [0.193, 0.364] | n/a | 0.208 | 12.41 |

File-level and site-recall Wilson intervals are in
`outputs/n100/variant_summary.csv`. The `static` reviewer's file-level
rate was not computed in this pass.

## What n=100 changes versus the pilot

The pilot's most eye-catching number, Claude scoring 0/20 at the line
level under Variant A, was a small-sample artefact. At n=100 Claude-A
scores 12/100 = 0.12 [0.070, 0.198]. GPT-4o-mini under Variant A moves the
other way, from the pilot's 0.15 to 0.07 [0.034, 0.137], the small sample
correcting in the opposite direction. The Variant B point estimates are
stable from pilot to n=100 (Claude 0.15 to 0.16, GPT 0.30 to 0.29).

## Prompt sensitivity (A vs B), paired McNemar

| reviewer | A | B | discordant (B-only / A-only) | McNemar exact p |
|---|---:|---:|---|---|
| `claude-sonnet-4-5` | 0.12 | 0.16 | 7 / 3 | 0.34 |
| `gpt-4o-mini` | 0.07 | 0.29 | 22 / 0 | < 0.0001 |

Removing the no-speculation clause moves GPT-4o-mini decisively (22
instances flip to a hit, none flip away) but does not significantly move
Claude. This refines the pilot reading: at n=100 the prompt-sensitivity
effect is specific to GPT-4o-mini, not a shared property of both
reviewers.

## Model comparison (Claude vs GPT), paired McNemar

| variant | Claude | GPT | discordant (Claude-only / GPT-only) | McNemar exact p |
|---|---:|---:|---|---|
| A | 0.12 | 0.07 | 11 / 6 | 0.33 |
| B | 0.16 | 0.29 | 6 / 19 | 0.015 |

Under the baseline prompt the two reviewers are statistically
indistinguishable. Under Variant B, GPT-4o-mini's instance hit rate is
significantly higher, but it emits 565 comments (5.15 FP/instance) against
Claude's 237 (2.20 FP/instance): the advantage is volume-driven. The
benchmark does not claim a model-capability ranking.

## False positives

The robust separation is precision, not hit rate. Claude under the
baseline prompt emits 1.60 FP/instance, GPT-A 1.99, and the static union
12.41. The static reviewer reaches its 0.27 hit rate only by
carpet-bombing every instance with warnings.

## Tolerance sensitivity (zero additional API cost)

Re-scoring the stored comments at three tolerances, with the oracle and
matcher held fixed:

| N | claude A | gpt A | claude B | gpt B |
|---:|---:|---:|---:|---:|
| 0 | 0.10 | 0.06 | 0.14 | 0.20 |
| 3 | 0.12 | 0.07 | 0.16 | 0.29 |
| 10 | 0.18 | 0.12 | 0.24 | 0.40 |

Hit rates rise monotonically with tolerance, as expected. The GPT-B over
Claude-B ordering holds across all three.

## Oracle construct validity (30-instance audit)

The benchmark assumes a fix patch's hunk source ranges mark the buggy code
a reviewer should flag. To test that assumption a stratified 30-instance
sample (all 10 repos) from the n=100 study was audited by hand: each
reconstructed oracle site was labelled `bug` (the lines are the defect a
reviewer should flag), `related` (part of the fix but not the core defect),
or `unrelated` (refactor, import, test, or a feature insertion point).
Labels were drafted with LLM assistance and human-confirmed; the method and
per-site verdicts are in `outputs/n100/oracle_validity_*`.

On this sample:

- site-level oracle validity (bug-site fraction): 24/48 = 0.50, Wilson 95% [0.36, 0.64]
- instances with at least one bug site: 20/30 = 0.67
- instances with no bug site: 10/30 = 0.33, Wilson 95% [0.19, 0.51]

The 10 instances with no bug site are the main source of oracle noise. Six
are explicit feature or enhancement requests (for example "Improve default
logging format", "Expose warm_start", "--collect-only needs a shortcut"),
where the pre-fix code has no defect and the oracle marks a feature
insertion point; the rest are insertion-point oracles for a missing method
or a reworded warning. This is construct-validity evidence on a 30-instance
sample, not a proportion estimate over full SWE-bench Lite, and the interval
is wide.

### Audited-subset sensitivity

Restricting the instance hit rate to the 20 confirmed bug instances does not
cleanly raise it, and a 20-instance subset has very wide intervals, so this
is a sensitivity check, not a headline:

| reviewer / variant | n=100 headline | bug-only subset (n=20) |
|---|---|---|
| `claude-sonnet-4-5` A | 0.12 | 2/20 = 0.10 |
| `gpt-4o-mini` A | 0.07 | 2/20 = 0.10 |
| `claude-sonnet-4-5` B | 0.16 | 4/20 = 0.20 |
| `gpt-4o-mini` B | 0.29 | 6/20 = 0.30 |

A bug-only headline would require auditing all 100 instances. The audit here
only licenses the claim that oracle noise is real and is dominated by
feature/enhancement and insertion-point oracles.

## Cost

| stage | spend |
|---|---:|
| Round 1 pilot (frozen) | $0.91 |
| Round 2 variant probe (frozen) | $1.92 |
| n=100 extension, GPT (variants A+B) | $0.27 |
| n=100 extension, Claude (variants A+B) | $6.43 |
| total | $9.53 |

The n=100 extension reused the 20 pilot instances as cache hits and billed
only the 80 new instances per variant. The Claude run carried a $10 hard
cap with an automatic abort at $9; actual spend was $6.43.

## Figure

![Prompt-variant comparison, n=100](figures/variant_comparison_n100.png)

*n=100; error bars are Wilson 95% CIs. Variant A is the Round 1 baseline
prompt; Variant B removes the no-speculation clause.*

## Framing

n=100 narrows the Wilson intervals to roughly half the pilot's width and
resolves the pilot's 0/20 artefact. The defensible findings are: a large,
stable precision gap between the LLM reviewers and the static union; a
prompt-sensitivity effect that is significant for GPT-4o-mini and not for
Claude; and no significant model-capability ranking under the baseline
prompt. SWE-bench Lite's single-file nature and the cold-review input
policy are unchanged. Full SWE-bench or the Verified split would be needed
for any multi-file generalisation. A 30-instance oracle audit (section
above) puts the site-level bug-site fraction at 0.50 [0.36, 0.64] and finds
about a third of audited instances carry no cold-reviewable bug, mostly
feature or enhancement requests, so the headline rates should be read with
that oracle noise in mind.
