# CLAUDE.md — SWE-Review-Bench (measurement-validity study)

Project context: this repo pivoted from "publish a code-review benchmark" to a
measurement-validity study of patch-derived oracles. The master plan, research
questions, and all pending research decisions live in
`docs/validity_study/PLAN.md` (see its Decision Ledger). The n=100 benchmark
artifacts are now the study's evidence base, not the product.

## Hard rules (owner-mandated, 2026-07-08)

1. **LLM API ban.** Never execute any command that could trigger an LLM API
   call — `litellm` invocations, the orchestrator (`swe_review_bench.run`),
   or tests that might send requests — without the owner's explicit approval
   in the current conversation. If it is uncertain whether a command can
   trigger an API call, treat it as if it does. Violating this rule is task
   failure. (Non-LLM network access such as `git clone`/HF dataset downloads
   is not covered by this ban, but heavy network operations should still be
   flagged before running.)
2. **Frozen artifacts.** `outputs/round2/` and `outputs/n100/` are read-only.
   Never modify, regenerate, or "fix" anything inside them.
3. **No pipeline refactors.** Do not restructure the existing pipeline. New
   code goes in `swe_review_bench/validity/`; new outputs go in
   `outputs/validity_study/`.
4. **Reproducibility.** Every number that enters any report must be
   recomputable by an in-repo script from CSVs. Analysis scripts ship with
   minimal pytest coverage. Statistical claims must state the test name, n,
   effect size, and confidence interval — never a bare p-value.
5. **Stop protocol.** After each phase: produce an acceptance report in
   Chinese (what was done / key numbers / uncertainties / suggested next
   steps), then STOP. Do not start the next phase without explicit owner
   approval.
6. **Git.** At each phase end: run pytest, show `git diff --stat`, and wait
   for owner review before committing. Never push. Never commit `.cache/`,
   `.env`, large files under `outputs/`, or temporary files. Commit messages
   in English.
7. **Language.** Communicate with the owner in Chinese. Code, comments,
   documentation, and commit messages are in English.
8. **Ask, don't fabricate.** When data contradicts expectations or a research
   judgement is required: stop and ask. Slower is acceptable; invented
   results are not.
