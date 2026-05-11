# Leakage statement (cold code review setup)

SWE-Review-Bench evaluates reviewers in a **cold** code-review setup:
the reviewer sees the buggy source file and a generic review
instruction, and nothing else. This document is the canonical record
of what is and is not allowed in the reviewer's input, so that the
benchmark's "the reviewer found the bug" claim is unambiguous.

The pytest-runnable counterpart of this document is
`tests/test_no_leakage.py`, which checks every (instance, prompt
variant, file) combination in the 20-instance pilot.

## 1. Cold-review input policy

### Reviewer input MAY include

- The buggy source file (pre-fix content at the instance's
  `base_commit`), exposed as `file_path` and `file_content` via the
  `ReviewerInput` dataclass.
- A generic code-review instruction (the prompt template body).
- The output JSON schema description.

That is the entire input surface.

### Reviewer input MUST NOT include

- `problem_statement`: the issue title or body shipped with each
  SWE-bench Lite instance.
- `hints_text`: auxiliary hints (SWE-bench Lite usually has no such
  field; the assertion still runs).
- The fix patch (`patch`) or any rendering of it (diff hunks,
  patch-marker lines).
- The test patch (`test_patch`) or any rendering of it.
- Names of failing tests, extracted from `test_patch` via
  `def (test_\w+)` or `class (Test\w+)`, **unless** the same name also
  appears in the reviewer-visible source (a legitimate code reference,
  not oracle leakage).
- Ground-truth line numbers from the oracle hunks. The Round 1 / 2
  prompt template body provably contains no such numbers; the test
  detects any future variant that accidentally introduces them.
- Attention-directing language tied to the specific instance, for
  example "this file has a bug", "find the defect", "a bug was
  reported".

## 2. Explicitly allowed generic vocabulary

The following words are explicitly **allowed** in reviewer input and
are not flagged by the leakage test. Banning them would distort
ordinary code-review language and make the benchmark unrepresentative
of real reviewer-tool interactions:

```
bug, fix, issue, review, correctness, reliability, defect,
error, failure, test
```

The distinction the leakage policy enforces is "generic review
vocabulary" vs. "oracle-derived content tied to this specific
instance". A neutral framing like "identify any concrete correctness
issues" is allowed; "find the bug at line 173" is not. The test in
§6 of this document operationalises this boundary.

## 3. Prompt variants

All three Round 2 prompt variants are listed below verbatim. Each
variant is a single Python `str.format`-able template that takes two
substitutions: `{file_path}` and `{numbered_source}`. The numbered
source is `"<line>: <content>"` for each line of the file at the
instance's `base_commit`, the format that the test's source-line-
number-rendering exclusion regex (`^\s*\d+\s*[:|]\s` or `^\s*\d+\t`)
recognises.

### Variant A: Round 1 baseline (template id `v1`)

```
You are reviewing the following source file as part of a routine code review pass.

Identify any concrete correctness, reliability, or maintainability issues that
are directly supported by the code shown. Do not speculate about missing
context. Do not invent issues. If the code looks correct to you, return an
empty list.

Return a JSON array. Each item must follow this schema exactly:
{
  "file": string,           // must equal the File path below verbatim
  "line_start": integer,    // 1-indexed, matches the numbered source
  "line_end": integer,      // 1-indexed, inclusive, >= line_start
  "severity": "low" | "medium" | "high",
  "message": string         // one short sentence
}

Output the JSON array and nothing else. Do not wrap it in code fences.
An empty array [] is a valid answer.

File path: {file_path}

Source with line numbers (format: "<line>: <content>"):
{numbered_source}
```

### Variant B: no-speculation clause relaxed (template id `v1b`)

```
You are reviewing the following source file as part of a routine code review pass.

Identify any concrete correctness, reliability, or maintainability issues that
are directly supported by the code shown. Do not speculate about missing
context.

Return a JSON array. Each item must follow this schema exactly:
{
  "file": string,           // must equal the File path below verbatim
  "line_start": integer,    // 1-indexed, matches the numbered source
  "line_end": integer,      // 1-indexed, inclusive, >= line_start
  "severity": "low" | "medium" | "high",
  "message": string         // one short sentence
}

Output the JSON array and nothing else. Do not wrap it in code fences.
An empty array [] is a valid answer.

File path: {file_path}

Source with line numbers (format: "<line>: <content>"):
{numbered_source}
```

### Variant C: diagnostic-only probe (template id `v1c`)

Variant C forces the reviewer to emit at least one comment per file.
It is used only for upper-bound probing and is **not** a candidate for
external headline reporting.

```
You are reviewing the following source file as part of a routine code review pass.

Identify any concrete correctness, reliability, or maintainability issues that
are directly supported by the code shown. Do not speculate about missing
context. Return at least one comment per file, even if it is a minor
observation.

Return a JSON array. Each item must follow this schema exactly:
{
  "file": string,           // must equal the File path below verbatim
  "line_start": integer,    // 1-indexed, matches the numbered source
  "line_end": integer,      // 1-indexed, inclusive, >= line_start
  "severity": "low" | "medium" | "high",
  "message": string         // one short sentence
}

Output the JSON array and nothing else. Do not wrap it in code fences.

File path: {file_path}

Source with line numbers (format: "<line>: <content>"):
{numbered_source}
```

The canonical templates live in
`swe_review_bench/reviewers/prompt_variants.py`. Variant A is also
re-exported from `swe_review_bench/reviewers/base.py` for Round 1
backward compatibility.

## 4. Scoring separation

Oracle-derived information is read only **after** the reviewer has
emitted its output, by the scoring module
(`swe_review_bench/scoring/matching.py`,
`swe_review_bench/scoring/metrics.py`). The scoring layer compares
each comment's `(file, line_start, line_end)` against the oracle hunks
recovered from the fix patch (under tolerance N, default 3). Neither
the matcher nor the per-instance scorer reads `problem_statement`,
`hints_text`, `patch`, or `test_patch`.

## 5. Variants and cache isolation

Variant A's cache key is byte-identical to Round 1's (template id
`v1`). Variant B and C use new template ids (`v1b`, `v1c`) so their
cache entries never collide with Round 1's. Round 1's cache directory
(`.cache/llm/`) is read-only for Round 2; Round 2 writes only to
`.cache/round2/llm/`.

## 6. Tested checks (mirrored in `tests/test_no_leakage.py`)

The pytest module asserts the following on every (instance, variant,
file) combination in the 20-instance pilot:

1. `problem_statement` (whitespace-trimmed, ≥32 chars) is not a
   verbatim substring of the rendered prompt.
2. `hints_text` (≥32 chars) is not a verbatim substring. SWE-bench
   Lite's Instance dataclass does not carry this field; the assertion
   is kept for parity with future variants.
3. The multiline regex `^(@@|--- a/|\+\+\+ b/)` matches **nowhere** in
   the prompt.
4. `test_patch` (≥32 chars) is not a verbatim substring.
5. For every test name extracted from `test_patch` via
   `def (test_\w+)` and `class (Test\w+)`: the name does not appear in
   the prompt **unless** it also appears in the reviewer-visible
   source (legitimate project code).
6. For every oracle hunk line number L (range expanded by ±2): no bare
   integer in [L-2, L+2] appears in the prompt after (a) stripping
   lines that match the source-line-numbering format
   `^\s*\d+\s*[:|]\s` or `^\s*\d+\t`, and (b) masking the
   known-boilerplate substring `1-indexed` which contains a `1`
   token by template design.

A test that fails reports the (instance, variant, file) cell and the
specific oracle bytes that leaked. Failures are not auto-fixed; they
are surfaced for manual investigation per the H-lite spec.

Pass/fail summary of the latest run is recorded in
`outputs/round2/h_lite/leakage_audit_report.md`.
