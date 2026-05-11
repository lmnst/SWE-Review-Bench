# H-lite Task 3 — leakage audit report

Pass/fail summary of the latest `pytest tests/test_no_leakage.py`
run. The companion documents are `docs/leakage_statement.md` (the
external-reader statement of the cold-review input policy) and the
test source `tests/test_no_leakage.py`.

## Result

**60 of 60 parametrised cells pass.** No oracle-derived content was
found in any (instance, prompt variant, file) combination in the
20-instance pilot.

Parametrisation matrix:

- 20 instance ids sampled with `seed=42` from
  `princeton-nlp/SWE-bench_Lite`.
- 3 prompt variants: A (Round 1 `v1`), B (no-suppression `v1b`), C
  (force-emit, diagnostic-only, `v1c`).
- 60 = 20 × 3 cells; for each cell, the test loops over every patched
  file (single-file pilot — one file per instance), so each cell may
  evaluate up to N file-level assertions internally.

Captured run summary:

```
============================= test session starts =============================
platform win32 -- Python 3.9.12, pytest-8.4.2, pluggy-1.6.0
collected 60 items

tests\test_no_leakage.py ............................................... [ 78%]
.............                                                            [100%]

====================== 60 passed, 14 warnings in 53.16s =======================
```

Full session log is captured at `outputs/round2/h_lite/_pytest_capture.txt`.

## Whole-suite regression check

Running `pytest tests/` end-to-end (including the existing
`test_matching.py` unit tests):

```
75 passed, 14 warnings in 50.95s
```

(15 matching-layer unit tests + 60 leakage cells = 75. No regressions
from the H-lite Task 1 / Task 2 changes.)

## What the test actually checked

For each (instance, variant, file) tuple, the rendered prompt was
asserted to satisfy:

1. `problem_statement` (whitespace-trimmed, ≥32 chars) is not a
   verbatim substring of the prompt.
2. `hints_text` (≥32 chars) is not a verbatim substring. SWE-bench
   Lite's `Instance` dataclass does not carry a `hints_text` field,
   so this assertion is vacuously true for every cell; it is kept
   for parity with hypothetical future variants.
3. The multiline regex `^(@@|--- a/|\+\+\+ b/)` matches nowhere.
4. `test_patch` (≥32 chars) is not a verbatim substring.
5. For every test name extracted from `test_patch` via
   `def (test_\w+)` / `class (Test\w+)`: the name does not appear in
   the prompt unless the same identifier also exists in the reviewer-
   visible source (legitimate project code, not oracle leakage).
6. For every oracle hunk line number L expanded to [L-2, L+2]: no
   bare integer in that range matches `\bN\b` in the prompt after
   (a) stripping source-line-numbering prefix lines
   (`^\s*\d+\s*[:|]\s` or `^\s*\d+\t`) and (b) masking the known-
   boilerplate substring `1-indexed`.

A test that fails reports the specific (instance, variant, file)
cell and the bytes that matched. Failures are surfaced for manual
investigation per the H-lite spec; the test does not auto-fix
prompts.

## Generic vocabulary explicitly NOT asserted against

The leakage test does not flag occurrences of the following generic
review terms. Banning them would distort ordinary code-review
language and make the benchmark unrepresentative.

```
bug, fix, issue, review, correctness, reliability, defect, error,
failure, test
```

## How to re-run

From the project root:

```
pytest -v tests/test_no_leakage.py
```

The test loads instances via `load_instances(n=20, seed=42)`,
ensures each instance's repo is checked out at its `base_commit`,
prepares reviewer inputs the same way `run.py` does, renders the
three variant prompts, and runs the six assertion families above.
Wall time is dominated by per-instance `git checkout`; cached repos
under `.cache/repos/` make this complete in ~45-60 s on a warm
working tree.
