# Validity Diagnostics for Cold Code-Review Evaluation on SWE-bench Lite

Status: **preliminary study, frozen.** This report summarizes what the
n=100 cold code-review pilot on SWE-bench Lite can and cannot support as
a measurement instrument. It is a diagnostic write-up, not a claim of a
model-capability ranking. Every number traces to a committed CSV and an
in-repo script (see [Reproducibility](#reproducibility)).

<!-- OWNER REVIEW: interpretation strength throughout is deliberately conservative.
     The factual/number paragraphs are final; the reading paragraphs marked
     "Reading" are drafts at the lowest defensible strength for you to confirm or
     sharpen when you pick this up. No causal/strong claims were inserted on your
     behalf. -->

## 1. Task and setup

The instrument is a *cold code-review* task: a reviewer sees only the
pre-fix source of one file at its `base_commit` plus a generic review
instruction, and emits structured `(file, line_start, line_end, severity,
message)` comments. It never sees the issue text, hints, fix patch, test
patch, or oracle line numbers (leakage assertions in
`tests/test_no_leakage.py`). A scorer then matches each comment against
oracle hunks recovered from the fix patch under a line tolerance `N`
(default 3); an instance is a **hit** if any comment matched any oracle
hunk.

- Dataset: `princeton-nlp/SWE-bench_Lite`, split `test`, deterministic
  100-instance sample (`random.Random(42).sample`, superset of the
  20-instance pilot).
- Reviewers: `claude-sonnet-4-5` and `gpt-4o-mini` (via `litellm`), plus
  a Python-only static union (Ruff ∪ Pylint). Two prompt variants: **A**
  (`v1`, baseline) and **B** (`v1b`, identical but with the
  no-speculation clause removed).

## 2. Headline results (n=100, tolerance N=3)

| reviewer / variant | instance hit rate | file-level | site recall | FP / inst |
|---|---|---|---|---:|
| claude-sonnet-4-5 A | 12/100 = 0.12 [0.070, 0.198] | 0.83 | 0.081 | 1.60 |
| gpt-4o-mini A | 7/100 = 0.07 [0.034, 0.137] | 0.51 | 0.047 | 1.99 |
| claude-sonnet-4-5 B | 16/100 = 0.16 [0.101, 0.244] | 1.00 | 0.114 | 2.20 |
| gpt-4o-mini B | 29/100 = 0.29 [0.210, 0.385] | 0.97 | 0.201 | 5.15 |
| static | 27/100 = 0.27 [0.193, 0.364] | n/a | 0.208 | 12.41 |

Brackets are Wilson 95% intervals. Two properties of the instrument are
visible directly in this table and are the load-bearing observations of
this report.

**2.1 Prompt sensitivity is model-specific.** Removing one clause (the
no-speculation instruction) moves GPT-4o-mini's instance hit rate from
0.07 to 0.29 but barely moves Claude (0.12 to 0.16). Paired McNemar
exact tests (same instances, discordant pairs only):

| reviewer | A | B | discordant (B-only / A-only) | McNemar exact p |
|---|---:|---:|---|---|
| claude-sonnet-4-5 | 0.12 | 0.16 | 7 / 3 | 0.34 |
| gpt-4o-mini | 0.07 | 0.29 | 22 / 0 | < 0.0001 |

**2.2 Precision, not hit rate, separates the LLMs from static analysis.**
The static union reaches a comparable 0.27 hit rate but at 12.41
false positives per instance, against Claude-A's 1.60. GPT-B's higher
hit rate is volume-driven (565 comments vs Claude-B's 237).

**2.3 The model comparison is prompt-dependent.** Paired McNemar,
Claude vs GPT:

| variant | Claude | GPT | discordant (Claude-only / GPT-only) | McNemar exact p |
|---|---:|---:|---|---|
| A | 0.12 | 0.07 | 11 / 6 | 0.33 |
| B | 0.16 | 0.29 | 6 / 19 | 0.015 |

Under the baseline prompt the two reviewers are statistically
indistinguishable (p = 0.33); under variant B, GPT is significantly
higher (p = 0.015). The same instrument yields opposite conclusions
depending on a single prompt clause.

**2.4 Tolerance sensitivity** (re-scoring stored comments, zero
additional cost): hit rates rise monotonically with `N`, and the GPT-B >
Claude-B ordering holds across N ∈ {0, 3, 10}.

## 3. Oracle construct validity (30-instance audit)

The instrument assumes a fix patch's hunk ranges mark the buggy code a
reviewer should flag. A stratified 30-instance sample (all 10 repos)
was hand-audited: each reconstructed oracle site was labelled `bug`,
`related`, or `unrelated`.

- Site-level bug-site fraction: **24/48 = 0.50, Wilson 95% [0.36, 0.64]**.
- Instances with ≥1 bug site: 20/30 = 0.67.
- Instances with no bug site: 10/30 = 0.33 [0.19, 0.51]; 6 of the 10 are
  explicit feature/enhancement requests where the pre-fix code has no
  defect and the oracle marks an insertion point.

**Provenance.** Labels were LLM-drafted and then confirmed by the repo
owner on 2026-07-25; the owner's review left every label unchanged. This
is construct-validity evidence on a 30-instance sample with a wide
interval, **not** a proportion estimate over full SWE-bench Lite.

**Reading (conservative, draft).** On this sample about half of the
oracle sites are not defects a cold reviewer should flag, so headline
hit rates understate per-*bug* detection by an unknown amount and should
be read with oracle noise in mind. The size of that gap is not estimated
here.

## Appendix A — Hit-set overlap (exploratory)

Marginal hit rates (Section 2) say how *often* a cell hits; they do not
say *which* instances it hits. For every pair of (reviewer, variant)
cells, the Jaccard overlap of the two hit sets over the 100 instances:

| pair | both hit | x-only / y-only | Jaccard |
|---|---:|---|---:|
| claude A vs claude B (same model, prompt change) | 9 | 3 / 7 | 0.474 |
| gpt A vs gpt B (same model, prompt change) | 7 | 0 / 22 | 0.241 |
| claude A vs gpt A (same prompt, model change) | 1 | 11 / 6 | **0.056** |
| claude B vs gpt B (same prompt, model change) | 10 | 6 / 19 | 0.286 |
| claude A vs gpt B | 6 | 6 / 23 | 0.171 |
| claude B vs gpt A | 3 | 13 / 4 | 0.150 |

Observations (descriptive): cross-model overlap is lower than
same-model / cross-prompt overlap; under variant A the two models are
nearly orthogonal (both-hit = 1); GPT's A→B change is a pure expansion
(every A hit is retained in B, x-only = 0).

**Reading (exploratory, draft).** If a hit reflected detection of the
same underlying defect, the two models' hit sets would be expected to
concentrate on the same instances. The near-orthogonal variant-A hit
sets are at least consistent with hits tracking comment
placement/volume rather than a shared detected defect. This is a
descriptive pattern on n=100, not a formal test.

## Appendix B — No-enrichment on the audited subset (exploratory)

If the instrument measured bug detection, hits should concentrate on the
20/30 audited instances that carry a confirmed bug site. For each cell,
the 2×2 table [has bug site × reviewer hit] over the 30 audited
instances, with Fisher's exact two-sided p and a Woolf 95% CI on the
odds ratio (Haldane-Anscombe corrected on zero cells):

| cell | hit rate, bug instances | hit rate, no-bug instances | odds ratio [95% CI] | Fisher exact p |
|---|---|---|---|---:|
| claude A | 2/20 = 0.10 | 1/10 = 0.10 | 1.00 [0.08, 12.6] | 1.00 |
| claude B | 4/20 = 0.20 | 1/10 = 0.10 | 2.25 [0.22, 23.3] | 0.64 |
| gpt A | 2/20 = 0.10 | 1/10 = 0.10 | 1.00 [0.08, 12.6] | 1.00 |
| gpt B | 6/20 = 0.30 | 2/10 = 0.20 | 1.71 [0.28, 10.6] | 0.68 |
| any-cell (max-power view) | 8/20 = 0.40 | 3/10 = 0.30 | 1.56 [0.31, 7.9] | 0.70 |

The four per-cell tables are not independent (the same instances recur),
so they are not pooled; the `any-cell` row (hit if any cell hit) is a
descriptive maximum-power view, not a fifth test.

**Reading (exploratory, underpowered — draft).** No cell shows a
statistically significant concentration of hits on the bug-carrying
instances (all Fisher p > 0.6; all odds-ratio intervals include 1). This
is **an absence of detected enrichment at n=30, not evidence of no
enrichment**: with single-digit hit counts per cell the intervals cannot
exclude a moderate effect. A powered version would require scaling the
audit (out of scope for this frozen preliminary study).

## Limitations

- **Preliminary sample.** n=100 is a third of SWE-bench Lite; the audit
  is n=30. Wilson/Fisher intervals are wide throughout.
- **Single-file review.** One file per instance (SWE-bench Lite is
  single-file by construction); no cross-file or retrieval reasoning.
- **Oracle noise, unquantified gap.** ~half the audited sites are not
  cold-reviewable defects; the exact effect on headline rates is not
  estimated.
- **Underpowered appendices.** Appendices A and B are exploratory; B in
  particular cannot separate "no enrichment" from "enrichment we lacked
  the power to detect".
- **Two models, two prompt variants.** No top-tier upper bound, no
  multi-seed robustness, no perturbations beyond A/B at this scale.
- **No formal model ranking.** The instrument is not designed to produce
  one; Section 2.3 shows why a single-prompt ranking would be unstable.

## Reproducibility

Every figure is recomputable from a committed CSV by an in-repo script.
Frozen `outputs/n100/` artifacts are read-only inputs; the appendix
scripts write only to `outputs/validity_study/`.

| section | source CSV | script |
|---|---|---|
| §2 headline | `outputs/n100/variant_summary.csv` | frozen pipeline |
| §2.1 / §2.3 McNemar | `outputs/n100/paired_comparison.csv` | `diagnostics/paired_comparison.py` |
| §2.4 tolerance | `outputs/n100/tolerance_sweep.csv` | `diagnostics/tolerance_sweep.py` |
| §3 audit | `outputs/n100/oracle_validity_{report,template}.csv/.md` | `diagnostics/oracle_validity.py` |
| App. A | `outputs/validity_study/hit_overlap_matrix.csv` | `validity/hit_overlap.py` |
| App. B | `outputs/validity_study/no_enrichment.csv` | `validity/no_enrichment.py` |

Tests: `tests/test_validity.py` (8 tests; App. A/B cross-checked against
`paired_comparison.csv` and the audit report). Run:

```bash
python -m pytest tests/test_validity.py -q
python -m swe_review_bench.validity.hit_overlap
python -m swe_review_bench.validity.no_enrichment
```
