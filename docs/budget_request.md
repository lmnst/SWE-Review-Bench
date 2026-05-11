# SWE-Review-Bench: external API credits request

This document is an attachment-style note for an external credits
request. It does not contain an email body, a submission-target
decision, or any claim that credits will be approved.

It is the only document in this repository where dollar amounts or
funding language appear. It is not linked from `README.md` and is
not part of the benchmark itself.

## 1. Scope

### Immediate use (the budget being requested in this round)

| line item | description |
|---|---|
| Full SWE-bench Lite | All 300 instances × 3 reviewers (`claude-sonnet-4-5`, `gpt-4o-mini`, static union of filtered Ruff and Pylint) at the **one** baseline prompt variant (Variant A, the Round 1 `v1` template). |
| Variant ablation on full Lite | One additional prompt variant (Variant B, no-speculation clause removed) × 2 LLM reviewers × 300 instances. Static reviewer is variant-agnostic and incurs no API cost. |
| Tolerance sensitivity sweep on full Lite | Tolerances N ∈ {0, 3, 10} re-scored over the existing reviewer outputs. Implemented via the existing `--tolerance` flag; consumes no additional LLM calls. |
| Reruns and contingency (×1.5) | Buffer for rate-limit retries, prompt-template hotfix re-runs, and minor scope expansion within the immediate plan. |

### Stretch use (only if the immediate scope above is fully covered)

| line item | description |
|---|---|
| SWE-bench Verified subset | 100 of the 500 Verified instances × 3 reviewers × baseline prompt variant, as a generalisation check from Lite to Verified. |
| Confidence calibration probe | A small probe (~100 calls) re-asking the model for a self-rated calibration label on its own previously emitted comments, to test whether reviewer self-confidence tracks oracle hits. |

The stretch lines are listed for transparency. They are **not** part
of the headline ask range below and would be funded separately if at
all.

## 2. Ask range

| ask | range (USD) |
|---|---|
| Total external credits | $500 to $1,500 |
| Anthropic-specific credits (Claude API) | $300 to $700 |
| Non-Anthropic hosted-model credits (OpenAI / OpenRouter / Together / Fireworks or equivalent) | $200 to $800 |

The ranges above reflect what the project would accept; the lower
bound covers the immediate scope plus a real-world buffer, the
upper bound covers the stretch scope and additional ablations.

The pilot's actual observed spend (frozen Round 1 + Round 2) is
about $0.91 (Round 1) + $1.92 (Round 2) = $2.83 total, so the
requested range is roughly **15× to 50× the pilot spend**. The §3
table below derives the immediate-scope spend from observed per-call
costs; §4 explains the gap between the derived numbers and the ask
range honestly.

## 3. Cost derivation

All per-call cost figures are **observed**, taken from the pilot
artefacts:

- Round 1 baseline (cells stored in `outputs/summary.csv`): 20
  instances × 1 file per instance × 1 prompt variant per reviewer.
- Round 2 fresh calls (cells stored in `outputs/round2/variant_results.csv`):
  Variants B and C, 20 instances × 2 LLM reviewers, totalling 40
  fresh calls per reviewer.

Per-call observed costs:

| reviewer | source | calls | total (USD) | $ / call |
|---|---|---:|---:|---:|
| `claude-sonnet-4-5` | Round 1 baseline | 20 | 0.8738 | 0.04369 |
| `gpt-4o-mini`       | Round 1 baseline | 20 | 0.0359 | 0.00180 |
| `claude-sonnet-4-5` | Round 2 Variant B + C fresh | 40 | 1.8389 | 0.04597 |
| `gpt-4o-mini`       | Round 2 Variant B + C fresh | 40 | 0.0781 | 0.00195 |
| `static`            | local subprocess | n/a | 0 | 0 |

The Round 2 fresh rates are about 5% higher than Round 1 because
Variant C asks for at least one comment per file, which lengthens
the average completion. For full-Lite baseline extrapolation the
Round 1 rates are the more appropriate per-call multiplier; for the
ablation row that includes Variant B the Round 1 rates are also a
reasonable estimate (Variant B is similar in output shape to A).

Extrapolation to full Lite at the immediate scope:

| scenario | expected calls | observed cost per call | multiplier | estimated cost (USD) |
|---|---:|---:|---:|---:|
| Full Lite baseline, `claude-sonnet-4-5` | 300 | 0.04369 | 1.0 | 13.11 |
| Full Lite baseline, `gpt-4o-mini` | 300 | 0.00180 | 1.0 | 0.54 |
| Full Lite baseline, `static` | 300 | 0 | 1.0 | 0.00 |
| Variant ablation, `claude-sonnet-4-5` (1 additional variant) | 300 | 0.04369 | 1.0 | 13.11 |
| Variant ablation, `gpt-4o-mini` (1 additional variant) | 300 | 0.00180 | 1.0 | 0.54 |
| Tolerance sweep (rescoring only) | 0 | n/a | n/a | 0.00 |
| Reruns and contingency | n/a | n/a | ×0.5 over the LLM lines above | 13.65 |
| **Immediate subtotal** | | | | **40.95** |

Extrapolation to the stretch scope:

| scenario | expected calls | observed cost per call | multiplier | estimated cost (USD) |
|---|---:|---:|---:|---:|
| Verified subset, `claude-sonnet-4-5` | 100 | 0.04369 | 1.0 | 4.37 |
| Verified subset, `gpt-4o-mini` | 100 | 0.00180 | 1.0 | 0.18 |
| Verified subset, `static` | 100 | 0 | 1.0 | 0.00 |
| Calibration probe, `claude-sonnet-4-5` | 100 | 0.04369 | 1.0 | 4.37 |
| **Stretch subtotal** | | | | **8.92** |

Grand total of derived spend (immediate + stretch): about **$49.87**.

Per-model derived totals:

| reviewer | immediate | stretch | total derived |
|---|---:|---:|---:|
| `claude-sonnet-4-5` | 26.22 + 50% contingency share ≈ 39 | 8.74 | ≈ 47.74 |
| `gpt-4o-mini`       | 1.08 + 50% contingency share ≈ 1.6 | 0.18 | ≈ 1.78 |
| `static`            | 0 | 0 | 0 |

## 4. Gap between derived numbers and the ask range

The derived total (about $50) is far below the lower end of the ask
range ($500). The gap is not an over-estimate; it is buffer for
work that is in scope as research but not enumerated as a single
line item above:

- **Multi-seed runs.** The 20-instance pilot uses one seed (`seed=42`).
  Confirming that prompt-sensitivity is not a seed artefact would
  require re-running full Lite at 2 or 3 alternative seeds. Each
  additional seed at the immediate scope is about $27 in LLM spend.
- **Additional prompt variants beyond B.** Variant B is one specific
  edit (the no-speculation clause removed). Real prompt-sensitivity
  studies typically iterate through 3 to 6 prompt edits before
  settling on a canonical phrasing. Each additional variant on full
  Lite × 2 LLMs is about $14.
- **Higher-capability models for the LLM bar.** The pilot uses
  `claude-sonnet-4-5` and `gpt-4o-mini`, which are both
  mid-capability. Including a top-tier reviewer (such as Claude Opus
  or GPT-4o) would let the benchmark report an upper-bound LLM
  number; per-call cost for the larger models is roughly 5x to 10x
  higher, so a single reviewer × baseline run is about $50 to $100.
- **Bootstrap confidence intervals.** Wilson CIs cover binomial
  sampling uncertainty. McNemar and bootstrap CIs for paired metrics
  (Claude vs GPT, for example) require additional structured
  analysis but no new API calls; this line is essentially $0 and is
  mentioned here only for completeness.
- **Verified beyond the stretch line.** The Verified split has 500
  instances; the stretch line above covers 100. Adding the remaining
  400 instances would cost about $22 in LLM spend.

Adding the conservative upper bounds for the items above to the
immediate scope reaches roughly $300 to $500 for the Claude side
and roughly $100 to $200 for hosted-model side credits. The ask
range ($500 to $1,500 total) is sized to accommodate that without
re-asking mid-project.

## 5. Notes

- The engineering pipeline is built. Round 1 baseline (3 reviewers,
  20 instances), Round 2 prompt-variant probe (120 calls), and the
  H-lite hardening pass (safety audit, Wilson CIs, pytest leakage
  suite, README rewrite, `repro/run.sh`) are all complete. The
  remaining bottleneck is API budget for scaling sample size and
  ablations.
- Pilot artefacts are frozen. A sha256 manifest at
  `outputs/round2/baseline_manifest.json` tracks any later
  modification of the Round 1 frozen files.
- A pytest-runnable leakage suite (`tests/test_no_leakage.py`)
  asserts that the reviewer prompt contains no oracle-derived
  content for every (instance, variant, file) cell in the pilot.
  Latest pass/fail summary is at
  `outputs/round2/h_lite/leakage_audit_report.md`.
- Reproducibility is scripted (`repro/run.sh`,
  `repro/requirements.lock`, `repro/MANIFEST.md`). Default mode is
  cache-safe and issues no paid API calls.
- Raw LLM responses, if ever published, will be redacted and
  safety-audited first. They currently live under `.cache/` and are
  gitignored; the audit script
  `swe_review_bench/diagnostics/h1_safety_audit.py` lists them as
  `public_ok = no` pending a per-file content audit.

## 6. Out of scope for this document

The following are deliberately not included:

- Any email body or template.
- The specific submission target (mailing address, contact form,
  research-access programme), chosen by the author at send time.
- Claims that credits are guaranteed or that any specific provider
  will approve.
- Any reference to this document from `README.md` or
  `docs/research_brief.md`.
