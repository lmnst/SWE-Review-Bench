# E.5 Round 2 diagnostic summary

**Status:** Milestone E (read-only diagnostic probe) complete. No Round 1
artefact was modified or overwritten; all Round 2 outputs are under
`outputs/round2/`. No API calls were made. Estimated cost so far: **$0**.

---

## Headline finding

Round 1's 0% / 15% / 15% ranking is consistent with what the diagnostic
shows, but the interpretation of "0% for Claude" needs revision before
external reporting:

| reviewer          | line-level hit rate (Round 1) | file-level hit rate (diag) | gap |
|---|---:|---:|---:|
| claude-sonnet-4-5 | **0.00** [0.00, 0.16]         | **0.80** [0.58, 0.92]      | +0.80 |
| gpt-4o-mini       | 0.15 [0.05, 0.36]             | 0.65 [0.43, 0.82]          | +0.50 |
| static            | 0.15 [0.05, 0.36]             | 0.75 [0.53, 0.89]          | +0.60 |

Claude is **not silent** and is **not pointing at wrong files** — it
points at the right file at the highest rate of the three reviewers
(0.80 vs GPT 0.65 vs static 0.75). What Claude is failing at is
*line-localising* within the right file: 29 of 30 Claude comments
landed >10 lines away from any oracle hunk in the same file, and the
remaining 1 was 4 lines away (outside the Round 1 tolerance=3).

Round 1 reviewer inputs are restricted to the patched files only (see
`run.py:_patched_files_from_patch`), so a "wrong file" comment is
structurally impossible — the parser also overrides any deviating
`file` field back to the prompt's expected path. This means the
``file_level_hit_rate`` ceiling is driven by whether the reviewer
emitted **any** comment at all on a non-empty instance, not by file
selection. Claude's higher file-level number reflects its higher
non-empty-instance rate (16/20 vs GPT's 13/20).

---

## Evidence by hypothesis

The first reply listed three hypotheses for the Round 1 0% / 15% / 15%
ranking. Evidence per hypothesis:

### H1 — Round 1 prompt suppressed Claude's output

**Evidence does not support H1 as the dominant cause.**

- Claude emitted 30 comments across 16/20 instances (mean 1.5/instance,
  max 5). GPT-4o-mini emitted 49 across 13/20 (mean 2.45). Same order
  of magnitude — Claude is not output-suppressed.
- Distribution: p10=0, p50=1, p90=2, max=5. Claude does produce
  multiple comments per instance when it has something to say.
- Source: `outputs/round2/diagnostic_comment_distribution.md`,
  per-reviewer summary table.

A weaker form of H1 still cannot be ruled out: Variant B (no
suppression clause) might raise Claude's comment count further. That is
exactly what F is designed to test, but the evidence below suggests
volume is unlikely to convert into line-level hits.

### H2 — Reviewer protocol or scoring artefact

**Evidence does not support H2.**

- Oracle reconstruction (E.0.5) is deterministic across two
  `build_oracle_sites` calls per instance. Cross-check against
  Round 1's 12 hit rows in `results.csv`: 0 disagreements; every
  recorded hit re-computes as a true overlap under tolerance=3.
  Source: `outputs/round2/oracle_reconstruction_log.md`.
- Path normalisation (`a/`, `b/`, `\\`, `./`) is symmetric between
  comment paths and oracle paths. All 321 comments in `results.csv`
  resolved to a normalised file that matches an oracle file for that
  instance (zero `wrong_file` bucket entries). Source:
  `outputs/round2/diagnostic_comment_distribution.md`.
- All 12 hit traces (5 GPT + 7 static) reproduce the overlap
  calculation step-by-step; ranges and computations are internally
  consistent. Source: `outputs/round2/hit_traces.md`.
- Round 1 used pre-fix line numbers throughout: the prompt feeds
  pre-fix source, `build_oracle_sites` uses `hunk.source_start /
  source_length` (pre-fix domain), and `matching.py` compares them
  directly. No domain mismatch.
- No truncation: `results.csv` contains 321 rows over 19 unique
  instance IDs. The 20th sampled instance is `django__django-15851`
  (postgresql/client.py); inspection of `results.csv` confirms all
  three reviewers emitted zero comments for it. Static returning
  empty on `client.py` is a real Round 1 outcome, not a row drop.
  Worth investigating in F or G if revisited, but not a scoring bug.
- Cache key composition: `sha256(model, "v1", file_path,
  file_content)` per `swe_review_bench/reviewers/cache.py`. The
  template id "v1" is constant in Round 1, so Round 1's cache key is
  prompt-template-version-aware but not prompt-hash-aware. Implication
  for F.1 noted below.

### H3 — Real cold-bug-localisation gap

**Evidence supports H3 in a refined form.**

- File-level: Claude leads (0.80 file-level hit rate). The reviewer is
  scanning the right files.
- Line-level: Claude's comments land far from oracle hunks. Bucket
  distribution for Claude:
  - right-file, distance 0: 0/30
  - right-file, distance 1-3: 0/30
  - right-file, distance 4-10: 1/30
  - right-file, distance >10: **29/30**
- Tolerance sensitivity is therefore limited: tolerance=10 would
  promote at most 1 Claude comment (3% hit rate, still 0 instance-level
  hits under the "≥1 comment hit" criterion since that one comment is
  alone in its instance). The dominant failure mode is "right file,
  wrong region", not "right region, just outside tolerance".
- Claude's comment content (theme classification in
  `diagnostic_comment_distribution.md`) shows the comments are mostly
  substantive correctness observations — not style/maintenance. 9/30
  match correctness keywords directly (off-by-one, AttributeError on
  None deref, IndexError on regex without check, etc.); most "other"
  entries are also correctness observations the regex did not pattern-
  match (e.g. `is` vs `==` for string comparison, duplicate event
  handler binding, deprecated module usage). Claude is finding
  plausible-looking bugs in surrounding code — they are simply not the
  specific bugs the issue reporter targeted.

How GPT and static get to 0.15: both fire substantially more
shots per non-empty instance (GPT 3.8 comments per non-empty
instance; static 16.1) and benefit from the fact that the oracle hunks
under `strict_mode=False` cover the full source range of each hunk
(often spanning 5-20 lines), giving high-recall reviewers a wider
target. Static's bucket distribution: 3 hits at d=0, 4 at d=1-3, 4 at
d=4-10, 231 at d>10. Eleven of 242 comments are within or near the
oracle — a hit-by-shotgun pattern, not a high-precision detection.

---

## What remains ambiguous

1. **Whether removing "do not invent issues" from the prompt would
   raise Claude's hit rate at all.** Evidence suggests Claude's
   bottleneck is locating the *specific* defect among many plausible
   issues, not output volume — but F (Variant B) is the only way to
   confirm or refute this directly.
2. **Whether static's 15% is replicable on a wider sample.** With
   only 3 hits in 20 instances and Wilson CI [0.05, 0.36], the
   confidence interval is broad. G addresses this.
3. **Why the static reviewer produced zero comments on
   `django__django-15851` (postgresql/client.py).** Possible causes:
   pylint/ruff returning empty under the current rule filters,
   pylint/ruff erroring on the file, or no static-detectable issues at
   the chosen rule set. Not investigated in E (would require
   re-running the static reviewer, which is outside read-only scope).
4. **Whether tolerance=10 changes the picture for GPT and static.**
   E.4 only swept tolerance implicitly via the bucket counts;
   tolerance_sensitivity.csv is a G deliverable.

---

## Recommendation on Milestone F

**Recommend running F.** Rationale:

- F is bounded ($5 hard cap, ~$2.5 projected) and the evidence does
  not conclusively answer whether prompt phrasing is contributing to
  Claude's 0%. Even if F shows little movement, that is itself a
  useful result: it converts "prompt may have suppressed Claude" from
  a live hypothesis into a refuted one for the externally reportable
  number.
- The diagnostic does not show an obvious oracle/scoring/path bug, so
  entry condition (a) is satisfied.
- Caveat from E.0.5: Round 1's cache key includes `PROMPT_TEMPLATE_ID
  = "v1"`, not a prompt hash. F.1 must mint a new template id (`v1b`,
  `v1c`) per variant. Variant A re-runs Round 1's "v1" key and should
  be a 100% cache hit on the 20-instance set — no cost surprise for
  A. Variants B and C will cache-miss everywhere and pay the projected
  ~$2.5 in full.

**Expectations to test in F:**
- Variant B: Claude comments-per-instance may rise (5-10 extra
  comments total across 20 instances). Hit rate change unlikely to
  exceed +5 pp on a 20-instance set given the 4-10 bucket has only 1
  Claude comment in Round 1.
- Variant C ("at least one comment per file"): comment count rises
  notably; precision drops; hit rate may rise slightly via shotgun
  effect on Claude (matching GPT/static's coincidental-hit dynamic).
  Treat strictly as a diagnostic probe.

---

## Generated artefacts

All Round 2 outputs are under `outputs/round2/`.

| path | purpose |
|---|---|
| `baseline_manifest.json` | sha256/size/mtime for the 5 frozen Round 1 files (E.0). |
| `oracle_index.json` | per-instance oracle sites + repo + base_commit + patch sha256 (E.0.5). |
| `oracle_reconstruction_log.md` | reconstruction path used + determinism check + cross-check vs `results.csv` (E.0.5). |
| `diagnostic_comment_distribution.csv` | per-comment rows with file/line normalisation, distance bucket, hit flag (E.1). |
| `diagnostic_comment_distribution.md` | per-reviewer summary + Claude theme classification + classifier rules note (E.1). |
| `hit_traces.md` | full step-by-step trace for every Round 1 hit (E.2). |
| `near_miss_traces.md` | full Claude non-hit listing with nearest-oracle context (E.2). |
| `oracle_sanity.md` | raw patch hunks + parsed sites + pre-fix source for 3 random instances (E.3). |
| `file_level_metrics.csv` | file-level vs line-level hit rates, Wilson 95% CIs, gap (E.4). |
| `file_level_metrics.md` | same as CSV with a reading note (E.4). |
| `diagnostic_summary.md` | this file (E.5). |

Diagnostic source code lives under `swe_review_bench/diagnostics/`
(read-only with respect to the rest of the package).

**Halt.** Awaiting explicit approval before entering Milestone F.
