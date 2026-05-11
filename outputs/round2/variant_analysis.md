# F.3 Prompt-variant analysis

Sweep results: 20 instances x {claude-sonnet-4-5, gpt-4o-mini} x {A, B, C} = 120 calls. Static reviewer does not participate in F.3. Total fresh-call cost: $1.9170 (hard cap $5.00). Variant A reuses Round 1's cache (template id ``v1``); B and C have new template ids and missed cache on every call.

## Per-(reviewer, variant) metrics with Wilson 95% CI

| reviewer | variant | n_comments | cpi | instance_hit_rate (CI) | site_recall (CI) | file_level (CI) | FP/inst | p@1 | p@3 | p@5 | cost (USD) |
|---|---|---:|---:|---|---|---|---:|---:|---:|---:|---:|
| claude-sonnet-4-5 | A | 30 | 1.50 | 0.00 [0.00, 0.16] | 0.00 [0.00, 0.11] | 0.80 [0.58, 0.92] | 1.50 | 0.00 | 0.00 | 0.00 | $0.0000 |
| claude-sonnet-4-5 | B | 38 | 1.90 | 0.15 [0.05, 0.36] | 0.12 [0.05, 0.28] | 1.00 [0.84, 1.00] | 1.70 | 0.10 | 0.12 | 0.12 | $0.8869 |
| claude-sonnet-4-5 | C | 90 | 4.50 | 0.25 [0.11, 0.47] | 0.19 [0.09, 0.35] | 1.00 [0.84, 1.00] | 4.10 | 0.20 | 0.17 | 0.15 | $0.9520 |
| gpt-4o-mini | A | 49 | 2.45 | 0.15 [0.05, 0.36] | 0.09 [0.03, 0.24] | 0.65 [0.43, 0.82] | 2.20 | 0.15 | 0.10 | 0.08 | $0.0000 |
| gpt-4o-mini | B | 134 | 6.70 | 0.30 [0.15, 0.52] | 0.19 [0.09, 0.35] | 1.00 [0.84, 1.00] | 6.20 | 0.15 | 0.15 | 0.14 | $0.0393 |
| gpt-4o-mini | C | 113 | 5.65 | 0.35 [0.18, 0.57] | 0.31 [0.18, 0.49] | 1.00 [0.84, 1.00] | 5.00 | 0.15 | 0.15 | 0.17 | $0.0388 |

## Deltas vs Variant A

Wilson 95% intervals on each variant overlap heavily at n=20; the deltas below are point estimates and are NOT formally significant. They are reported descriptively only.

| reviewer | A hit_rate | B hit_rate | C hit_rate | B-A | C-A | A file_lvl | B file_lvl | C file_lvl | B fp/inst | C fp/inst |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| claude-sonnet-4-5 | 0.00 | 0.15 | 0.25 | +0.15 | +0.25 | 0.80 | 1.00 | 1.00 | 1.70 | 4.10 |
| gpt-4o-mini | 0.15 | 0.30 | 0.35 | +0.15 | +0.20 | 0.65 | 1.00 | 1.00 | 6.20 | 5.00 |

## Claude comment distance-bucket distribution by variant

| variant | wrong_file | d=0 | d=1-3 | d=4-10 | d>10 | invalid |
|---|---:|---:|---:|---:|---:|---:|
| A | 0 | 0 | 0 | 1 | 29 | 0 |
| B | 0 | 3 | 1 | 2 | 32 | 0 |
| C | 0 | 6 | 2 | 5 | 77 | 0 |

Reading: ``d=0`` and ``d=1-3`` together are the tolerance=3 hits. Bucket changes across A->B->C show whether the additional comments produced under B and C are landing near oracle hunks or are mostly added in unrelated regions.

## Round 1 <-> Variant A nondeterminism delta

Variant A uses template id ``v1`` (byte-identical to Round 1). Round 1's cache key composition (sha256 of model || template_id || file_path || file_content) means every Variant A call cache-hits Round 1's ``.cache/llm/`` entries; no API call is issued for Variant A.

- Cache hits on Variant A: 20/20 for each of ['claude-sonnet-4-5', 'gpt-4o-mini'] (100%).
- Sorted row equality (LLM reviewers, columns: reviewer, instance_id, file, line_start, line_end, severity, message, is_hit, matched_oracle_site_id): **EQUAL**.
- Per-reviewer comment counts (Round 1 vs Variant A):
  - ``claude-sonnet-4-5``: Round 1 = 30 / Variant A = 30
  - ``gpt-4o-mini``: Round 1 = 49 / Variant A = 49
- Per-reviewer instance-level hits (Round 1 vs Variant A):
  - ``claude-sonnet-4-5``: Round 1 = 0 / Variant A = 0
  - ``gpt-4o-mini``: Round 1 = 3 / Variant A = 3

Delta is 0 across every visible dimension. Variant A is byte-equivalent to Round 1 on the 20-instance set as expected, and the LLM-stochasticity contribution to any observed difference between A and B/C is therefore not confounded with Round 1 nondeterminism.

## Discussion

**Point-estimate movement that the diagnostic is consistent with.** Both reviewers gain on instance hit rate from A -> B and again from B -> C. For Claude the jump is 0.00 -> 0.15 -> 0.25; for GPT 0.15 -> 0.30 -> 0.35. File-level coverage rises to 1.00 for both reviewers under B and C: removing the suppression clause is enough to make both reviewers comment on every one of the 20 instances. The corresponding cost is FP/instance: Claude goes from 1.50 -> 1.70 -> 4.10; GPT 2.20 -> 6.20 -> 5.00.

**Statistical caveats.** Wilson 95% CIs at n=20 are wide. Claude A vs Claude B (0.00 vs 0.15) intervals [0.00, 0.16] and [0.05, 0.36] overlap; the same is true for the other pairwise comparisons. Treat the deltas above as direction-of-effect, not as a statistically resolved comparison. A larger sample (G) would shrink the intervals to ~+/-0.04 - 0.06 pp at n=300.

**Refinement to E.5.** E recommended F partly because prompt suppression could not be ruled out as a contributor to Claude's 0%. The F evidence is consistent with a non-trivial contribution from the suppression clause -- removing it raises Claude's point-estimate instance hit rate to the same value GPT had under Variant A. E's stronger claim that Claude has a real cold-defect-localisation gap is not contradicted: Claude under B/C still trails GPT under B/C by a comparable margin at the point estimate, and Claude's gains are accompanied by an FP increase that is proportionally similar across reviewers. The diagnostic supports a refined picture: **Claude's Round 1 0% reflects both prompt-induced under-emission and a real line-localisation gap**, not one or the other alone.

**No winner picked.** Per F.3 spec, this report does not recommend a final variant. Variant C is diagnostic-only and is not a candidate for the externally reported headline. The choice between Variant A (Round 1 baseline, byte-identical reproducibility) and Variant B (lower-suppression, modestly higher hit rate) is a downstream decision; the right next step is Milestone G with whichever variant is chosen, so the wider CI from G clarifies whether the B-over-A point-estimate delta survives.
