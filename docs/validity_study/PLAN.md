# Measurement-Validity Study — Master Plan

- Owner: Zhuangyu Zhou
- Created: 2026-07-08 (Phase 0)
- Target venue: MSR 2027 technical track (deadline ~Jan 2027); arXiv preprint once the core numbers are in (gate: [D-10])
- Governing rules: repo-root `CLAUDE.md` (API ban, frozen artifacts, stop protocol, reproducibility)
- Research decisions requiring owner sign-off are ONLY recorded in the Decision Ledger (section 7). Body text references Ledger IDs and never pre-empts an OPEN decision.

## 1. Background and pivot

This repo currently holds a cold code-review benchmark pilot on SWE-bench Lite: an evaluation pipeline, an n=100 study (2 LLM reviewers x prompt variants A/B, plus a static-analysis union), and a 30-instance hand audit of the patch-derived oracle (`README.md`, `outputs/n100/`).

After external review, the direction changed from "publish a benchmark" (the 2025-2026 space is crowded; no novelty) to a **measurement-validity paper**. The pilot artifacts stop being the product and become the *evidence base*: the benchmark we built is the instrument whose measurement error we now characterize.

## 2. Core claim

The **patch-derived oracle** — treating a fix patch's hunk line ranges as ground truth for where a defect is — is widely inherited across code-review and fault-localization evaluation, and has never been validated. Its measurement error decomposes into three layers, and the combined error is large enough to swamp the signal being measured:

1. **Label layer** — the oracle sites themselves are often not defects. Pilot audit: 24/48 sites (0.50, Wilson95 [0.36, 0.64]) mark an actual defect; 10/30 instances (0.33) carry no cold-reviewable bug at all (`outputs/n100/oracle_validity_report.md`).
2. **Scoring layer** — line-range overlap is neither sufficient (a hit can be a *lucky hit*: right lines, wrong diagnosis) nor necessary evidence of a real finding (a non-overlapping comment is an *undecidable* FP — it may flag a real defect fixed later: a *vindicated FP*).
3. **Instrument layer** — the measurement is unstable under semantics-preserving instrument perturbation: removing one prompt clause moves GPT-4o-mini's hit rate 0.07 -> 0.29 (McNemar exact p < 1e-6) while Claude stays flat, flipping the model comparison from "indistinguishable" (variant A, p = 0.33) to "GPT significantly higher" (variant B, p = 0.015) (`outputs/n100/paired_comparison.csv`).

Logical chain of the paper: **wrong labels -> wrong scores -> wrong conclusions.**

## 3. Research questions

- **RQ1 (label layer).** What fraction of patch-derived oracle sites mark a real, cold-reviewable defect, and what is the taxonomy of the invalid remainder? Method: scale the 30-instance audit per [D-02], dual annotation with Cohen's kappa per [D-03], taxonomy finalized per [D-01].
- **RQ2 (scoring layer).** Among line-range *hits*, what fraction are lucky hits (message does not describe the fixed defect — semantic judge per [D-06])? Among scored *FPs*, what fraction are vindicated by future fixes (future-fix mining, prototype in Phase 3, expansion per [D-09])?
- **RQ3 (conclusion layer).** Do benchmark conclusions survive oracle cleaning and instrument perturbation? Sub-analyses: (a) clean-subset vs full-set conclusion flips; (b) no-enrichment test — hit rates are not elevated on audited true-bug instances (formalized in Phase 1); (c) ranking stability across prompt perturbations per [D-07] and models per [D-04].

## 4. Preliminary signals (identified in analysis discussion; not yet recorded in any repo report)

These two observations motivated the pivot and are formalized in Phase 1 / WP4. Until then they are descriptive.

**S1 — Hit sets of the two models are nearly disjoint under variant A.**
`outputs/n100/paired_comparison.csv` (reviewer contrast, variant A): Claude 12 hits, GPT 7 hits, both-hit = **1/100** (discordant 11/6). Jaccard overlap = 1/18 ≈ 0.056. If hits reflected detection of the actual defect, the two models' hits should concentrate on the same (true-bug) instances; near-orthogonal hit sets are what random line coverage under differing comment-volume/placement styles would produce. (Under variant B: both-hit = 10, driven by GPT's volume increase — to be included in the full overlap matrix, Phase 1.3.)

**S2 — No enrichment of hits on audited true-bug instances.**
`outputs/n100/oracle_validity_report.md` (final section): on the 20 audited instances with a confirmed bug site, claude-A hits 2/20 = 0.10 vs 0.12 on the full n=100; gpt-A 0.10 vs 0.07; claude-B 0.20 vs 0.16; gpt-B 0.30 vs 0.29. If the benchmark measured bug detection, hits should concentrate in the ~2/3 of instances that actually contain a bug (naive expectation ≈ rate/0.67 ≈ 1.5x on the subset); no cell shows anything close. Caveat: n=30 audit is pilot-sized; Phase 1 runs the Fisher exact test at this n and flags it as underpowered; the definitive version reruns after WP1 scale-up.

## 5. Work packages

Constraints that apply to every WP: no LLM API call without explicit owner approval (CLAUDE.md rule 1); `outputs/round2/` and `outputs/n100/` are read-only (rule 2); new code under `swe_review_bench/validity/`, new outputs under `outputs/validity_study/` (rule 3); every reported number recomputable by an in-repo script from CSVs, scripts carry minimal pytest, statistical claims report test name + n + effect size + CI (rule 4).

### WP0 — Literature and positioning

- **Goal:** substantiate "widely inherited, never validated" and position against the closest work (benchmark-validity critiques, SWE-bench contamination/quality studies, SWE-bench Verified, fault-localization oracle papers, LLM-reviewer benchmarks 2024-2026).
- **Tasks:** systematic-ish search; extraction table per paper: task, oracle construction, granularity/tolerance, any validation performed (Y/N + how); 3-5 closest works each with a one-paragraph differentiation.
- **Deliverables:** `docs/validity_study/related_work.md` + machine-readable extraction table `outputs/validity_study/lit/papers.csv`.
- **Acceptance:** >= 15 primary papers tabulated; the "never validated" claim either survives with citations or is explicitly weakened to what the evidence supports; MSR-fit argument written down.
- **Depends on:** nothing. Zero API cost.

### WP1 — Label layer: audit expansion (RQ1)

- **Goal:** oracle validity rate with defensible measurement quality (dual annotation, kappa) at the scale per [D-02], plus a finalized noise taxonomy per [D-01].
- **Tasks:**
  1. Freeze taxonomy ([D-01]) — pilot 3-way scheme (`bug` / `related` / `unrelated`) plus subtype candidates observed in the pilot: feature/enhancement insertion, import-only hunk, refactor, spec-dependent (cold review cannot decide), insertion-context lines.
  2. Generate annotation cards for the expansion sample (new sampling code in `validity/`; reuse `diagnostics/oracle_validity.py` conventions without modifying it).
  3. Dual annotation per [D-03]; compute Cohen's kappa site-level (and instance-level); adjudication log for disagreements.
  4. Validity rates with Wilson CIs, per-repo and per-taxonomy-category breakdowns; compare against the pilot 30 as a consistency check.
- **Deliverables:** `outputs/validity_study/audit/` (labels CSV, kappa report, adjudication log), `docs/validity_study/taxonomy.md`, analysis script + tests in `validity/`.
- **Acceptance:** kappa reported pre-adjudication with n; every category in the final taxonomy has a definition + >= 2 real examples; validity rate with CI; zero edits to `outputs/n100/`.
- **Depends on:** [D-01], [D-02], [D-03]. Zero API cost unless [D-03] selects LLM-assisted drafting (then spend-gated).

### WP2 — Evaluation expansion (feeds RQ2/RQ3; spend-gated)

- **Goal:** enough (model x prompt-perturbation x condition) cells to test conclusion stability, plus the post-fix control condition.
- **Tasks:**
  1. Post-fix control: reviewers see the *fixed* file; persistent flags at the oracle location expose location-insensitive commenting. Phase 2 delivers code + dry-run cost only; real calls per [D-08].
  2. Prompt-perturbation set per [D-07] (semantics-preserving edits beyond the existing A/B pair).
  3. Model set per [D-04].
  4. Every sub-experiment: dry-run call/token/cost projection -> owner approval -> capped run; caches isolated from the frozen round1/round2 caches.
- **Deliverables:** runner extensions under `validity/`, per-sub-experiment dry-run reports, run artifacts + run_meta under `outputs/validity_study/`.
- **Acceptance:** no real call without an approved dry-run report; per-run metadata (resolved model ids, spend, cache stats) recorded; frozen caches untouched.
- **Depends on:** [D-04], [D-07], [D-08]. **Environment fact:** the historical LLM cache was NOT migrated to this machine (`.cache/llm/` empty, `.cache/round2/llm/` has 1 entry), so cost projections must assume 100% fresh calls.

### WP3 — Scoring layer (RQ2)

- **Goal:** quantify lucky-hit rate among hits and vindicated-FP rate among scored FPs.
- **Tasks:**
  1. Semantic judge per [D-06]: for each hit, does the comment message describe the defect the patch fixed? Human double-check on a subsample (>= 30 hits) with agreement reported. Spend-gated.
  2. Future-fix mining (zero API): Phase 3 prototype on django — bugfix commits within 24 months after base_commit touching the same file + function as an FP comment ("Fixed #NNNNN" Trac pattern); function-level alignment via AST to sidestep line drift. Expansion per [D-09].
  3. Combine: corrected "true finding" accounting = hits - lucky hits + vindicated FPs; propagate to RQ3.
- **Deliverables:** `validity/semantic_judge.py` (+ judge prompt + agreement report), `validity/future_fix.py`, `outputs/validity_study/future_fix_prototype.md`, rates with CIs.
- **Acceptance:** judge-human agreement reported on the double-checked subsample; every vindicated-FP candidate has a review card (comment text + later commit + diff excerpt); rates carry CIs and denominators.
- **Depends on:** [D-06], [D-09]. Phase 3 part is zero-API; judge part is spend-gated.

### WP4 — Analysis: conclusion layer (RQ3) and integration

- **Goal:** the "wrong labels -> wrong scores -> wrong conclusions" quantitative chain.
- **Tasks:**
  1. No-enrichment test (Phase 1; pilot n=30): per (model, variant) 2x2 [instance has valid bug site x instance hit], two-sided Fisher exact, OR + 95% CI; Haldane-Anscombe sensitivity on zero cells; no pooling of the four non-independent tables — pooled view uses the single any-reviewer-hit 2x2. Rerun at WP1 scale.
  2. Hit-overlap matrix (Phase 1): all reviewer x variant pairs, raw counts + Jaccard, n=100.
  3. Clean vs full oracle: recompute headline metrics and paired McNemar contrasts on the audited-valid subset vs the full set; conclusion-flip table (which claims survive?).
  4. Ranking stability: across WP2 perturbation cells (rank flips, Kendall tau if >= 3 models per [D-04]).
  5. Power notes for every underpowered pilot test, with the n needed.
- **Deliverables:** `validity/enrichment.py` (+ overlap), `outputs/validity_study/no_enrichment_report.md`, later `conclusion_flip_report.md`; all with tests.
- **Acceptance:** every test reports name, n, effect size, CI (rule 4); explicit statement of what each result means for RQ3 framing.
- **Depends on:** Phase 1 has no dependencies (data already frozen); items 3-5 depend on WP1/WP2.

### WP5 — Writing and release

- **Goal:** MSR 2027 submission; arXiv preprint at the [D-10] gate.
- **Tasks:** paper skeleton keyed to RQ1-3; threats-to-validity section applying our own critique to our own instrument (audit sample size, single-benchmark scope, judge reliability); artifact package (scripts + labels + frozen CSVs); repo README re-pivot at the end (not now).
- **Deliverables:** paper draft (separate dir/repo per owner preference), artifact README, submission checklist.
- **Acceptance:** every number in the draft traces to a repo script output; limitations section covers the layers we could NOT measure.
- **Depends on:** WP0-WP4.

## 6. Near-term execution phases (owner-approved sequence, 2026-07-08)

Each phase ends with: pytest -> acceptance report (Chinese) -> `git diff --stat` shown -> STOP for owner approval before commit and before the next phase.

- **Phase 0 (this):** repo read-through; this plan; project `CLAUDE.md`; `.gitignore` gaps. No analysis.
- **Phase 1 (zero API):** WP4 items 1-2 at pilot scale. Step 1 is data-source identification for the 30-instance labels with an explicit STOP for owner confirmation before analysis code is written.
- **Phase 2 (zero API; code + dry-run only):** WP2 item 1 up to the dry-run cost report (2 models x variant A x 20 audited instances). Real calls are a separate approval ([D-08]).
- **Phase 3 (zero API):** WP3 item 2 prototype, django only. Pre-check first: is the local django clone's history sufficient (not shallow; covers base_commit + 24 months)? If not — STOP and report, do not mine a truncated history.

## 7. Decision Ledger

Rules: research decisions live HERE and nowhere else. `OPEN` = owner has not decided; nothing in this plan or in code may assume an outcome. Recommendations are input, not decisions.

| ID | Decision point | Options | Recommendation | Status |
|----|----------------|---------|----------------|--------|
| D-00 | Target venue + preprint strategy | (fixed by owner) | — | DECIDED 2026-07-08: MSR 2027; arXiv when core numbers land (see D-10 for the gate) |
| D-01 | RQ1 noise taxonomy (final categories) | (a) keep pilot 3-way (bug/related/unrelated); (b) flat fine-grained set (~6-8 categories); (c) two-level: pilot 3-way + subtype within non-bug | (c) — preserves comparability with the pilot 30 while adding the analytic depth RQ1 needs | OPEN |
| D-02 | Audit expansion scope | (a) 300 = full SWE-bench Lite test split; (b) 150 stratified; (c) 100 = the evaluated instances only | (a) — "we audited the entire benchmark" is a categorically stronger claim and ~480 sites gives tight CIs; fall back to (b) only if annotator hours bind | OPEN |
| D-03 | Second annotator + agreement protocol | (a) second human annotator, independent, kappa pre-adjudication, consensus adjudication; (b) owner re-annotates after washout (weak, same-rater bias); (c) LLM second rater + human adjudication (must be disclosed; review risk) | (a) — kappa between independent humans is what reviewers will demand for a validity paper | OPEN |
| D-04 | Model set for evaluation expansion | (a) keep the 2 pilot models; (b) add 1 top-tier + 1 open-weights model (4 total); (c) 5+ models | (b) — ranking-stability claims (RQ3c) are weak with 2 models; 4 keeps spend bounded | OPEN |
| D-05 | SWE-bench Verified control group | (a) skip; (b) audit 50-100 Verified instances under the same protocol, as a "does human filtering fix the oracle?" contrast | (b) if annotation budget survives D-02 — it directly tests the community's assumed remedy | OPEN |
| D-06 | Semantic judge design (lucky-hit) | (a) one strong LLM judge + human double-check on >= 30 hits; (b) 2-judge ensemble + tie-break; (c) all-human judging | (a) — hit counts are small (12-29 per cell), so the human-check subsample covers a large fraction anyway | OPEN |
| D-07 | Prompt-perturbation set (instrument layer) | (a) existing A/B only; (b) A/B + 3-4 semantics-preserving perturbations (paraphrase, section order, schema wording, severity wording); (c) larger factorial design | (b) — enough to show instability is systematic, not a one-clause fluke | OPEN |
| D-08 | Post-fix control: approve real API calls | approve / modify / reject after Phase 2 dry-run report | defer until the dry-run numbers exist (note: no warm cache on this machine — assume 100% fresh calls) | OPEN |
| D-09 | Future-fix mining beyond django | approve / reject expansion after Phase 3 prototype (signal strength vs per-repo mining cost; blob:none clones lazy-fetch file contents over the network) | defer until the prototype report | OPEN |
| D-10 | arXiv timing gate | (a) after RQ1 scale-up only; (b) after RQ1 + Phase-1-grade RQ3 evidence (no-enrichment + flip table); (c) after full RQ2 | (b) — "labels are wrong AND conclusions flip" is the minimal complete story worth staking priority on | OPEN |

## 8. Backlog (not scheduled; promote via Ledger if picked up)

- Strict-mode oracle ablation: does `strict_mode=True` site construction change validity rates? (site-definition sensitivity for RQ1)
- Tolerance-as-instrument: fold the existing 0/3/10 sweep into the instrument-layer analysis.
- Static-reviewer FP taxonomy (12.41 FP/instance — what are they? complements RQ2).
- Verified-split contrast (tied to [D-05]).
- Full SWE-bench / multi-file generalization of the audit.
- Release the clean-label subset as a community artifact alongside the paper.
- Quantify LLM-draft-vs-human agreement from the pilot audit workflow as a side note on annotation methodology.
- Cross-task check: line-level fault-localization benchmarks inherit the same oracle construction (Defects4J-style); a small replication would widen the claim.

## 9. Environment facts recorded at Phase 0 (2026-07-08)

- Repo moved machines: `outputs/n100/variant_results.csv` `raw_output_path` points at `D:\Jet_brains\SWE-Review-Bench-MVP\...`; the current checkout is `D:\Code\Demo\SWE-Review-Bench`.
- LLM caches restored 2026-07-09 from the owner's USB copy: `.cache/llm/` = 40 entries + 40 raw (Round 1: 20 instances x 2 models), `.cache/round2/llm/` = 401 entries + 401 raw (Round 2 pilot + n=100 extension). Raw model outputs referenced by the frozen CSVs are locally available again (at new paths; the CSVs' recorded `raw_output_path` still points at the old machine's absolute paths — join via the sha256 basename).
- Repo clones: only `django__django` present under `.cache/repos/`; partial clone (`blob:none` filter), NOT shallow, 28,885 commits reachable from the current checkout. Commit metadata is local; file contents lazy-fetch from GitHub on demand (relevant to Phase 3 runtime and network use). Coverage of "base_commit + 24 months" per instance is a Phase 3 pre-check, not yet verified.
- The full pytest suite's `tests/test_no_leakage.py` loads the HF dataset and checks out 100 instances across 10 repos; on this machine that would trigger ~9 fresh clones (network-heavy, no LLM API). Fast local-only tests: `tests/test_matching.py`, `tests/test_analyses.py`.
- Current venv is Python 3.13.3 (17/17 local tests pass); the frozen n=100 run recorded Python 3.9.12. Not an issue for CSV-based analysis; note it if any behavior differs when re-running pipeline components.
