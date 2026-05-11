# F.2 Prompt leakage check + cost projection

This report runs before any Round 2 LLM API call. If any FAIL appears, F.3 is blocked.

## (1) Template-level static check

Forbidden phrases (any match aborts F.3): ['find the bug', 'find the defect', 'a defect was reported', 'a bug was reported', 'this file has a bug', 'this file has a defect', 'fix the bug', 'fix the issue', 'locate the bug', 'locate the defect']

Patch markers (regex ``^(@@|--- a/|+++ b/)`` on any line) aborts F.3 if found in the template body.

| variant | template_id | template_sha256[:12] | forbidden_phrase_matches | patch_marker_matches | verdict |
|---|---|---|---|---|---|
| A | `v1` | `79361b1bc92b` | [] | [] | **PASS** |
| B | `v1b` | `677bde439ebe` | [] | [] | **PASS** |
| C | `v1c` | `8493618ca102` | [] | [] | **PASS** |

## (2) Per-instance runtime check

For every instance, each of A/B/C is rendered on each patched file. The fully rendered prompt is then searched for verbatim ``problem_statement`` / ``hints_text`` / ``patch`` / ``test_patch`` substrings, patch markers, and test names whose definitions appear in ``test_patch`` but **not** in the file the reviewer sees.

Allowed generic vocabulary (NOT flagged): ``bug, fix, issue, review, correctness, reliability, defect, error``.

| instance | files | variant | problem_statement | hints | patch | test_patch | patch_marker | orphan_test_names | verdict |
|---|---:|---|---|---|---|---|---|---|---|
| django__django-11099 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-11099 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-11099 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-11133 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-11133 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-11133 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-11283 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-11283 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-11283 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-11422 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-11422 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-11422 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-12915 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-12915 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-12915 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-13033 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-13033 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-13033 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-13315 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-13315 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-13315 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-13551 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-13551 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-13551 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-14382 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-14382 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-14382 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-15851 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-15851 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-15851 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-16408 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-16408 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-16408 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-16816 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-16816 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-16816 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-17087 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-17087 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| django__django-17087 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| matplotlib__matplotlib-23476 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| matplotlib__matplotlib-23476 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| matplotlib__matplotlib-23476 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| matplotlib__matplotlib-25498 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| matplotlib__matplotlib-25498 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| matplotlib__matplotlib-25498 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| sphinx-doc__sphinx-8282 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| sphinx-doc__sphinx-8282 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| sphinx-doc__sphinx-8282 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| sphinx-doc__sphinx-8474 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| sphinx-doc__sphinx-8474 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| sphinx-doc__sphinx-8474 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| sympy__sympy-16792 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| sympy__sympy-16792 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| sympy__sympy-16792 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| sympy__sympy-20442 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| sympy__sympy-20442 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| sympy__sympy-20442 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |
| sympy__sympy-21627 | 1 | A | ok | ok | ok | ok | ok | - | **PASS** |
| sympy__sympy-21627 | 1 | B | ok | ok | ok | ok | ok | - | **PASS** |
| sympy__sympy-21627 | 1 | C | ok | ok | ok | ok | ok | - | **PASS** |

## (3) Cache-key composition and cost projection

Round 1 cache key composition (from ``swe_review_bench/reviewers/cache.py``):

```
cache_key(model, prompt_template_id, file_path, file_content)
        = sha256(model || NUL || template_id || NUL || file_path || NUL || file_content)
```

Implication for Round 2: the cache key incorporates the template id (``v1`` / ``v1b`` / ``v1c``), **not** a full prompt-content hash. Variant A's template id is ``v1`` -- byte-identical to Round 1's. Therefore Variant A's cache key is identical to Round 1's for every (model, instance, file) tuple, and Round 1's existing cache files (``.cache/llm/<key>.json``) hit on read-through. Variants B and C use new template ids, so every B/C call cache-misses.

| variant | model | projected cost (USD) | cache mode |
|---|---|---:|---|
| A | sonnet | 0.0000 | round1 read-through (expected 100% hit) |
| A | gpt-4o-mini | 0.0000 | round1 read-through (expected 100% hit) |
| B | sonnet | 0.3840 | round2 fresh (always miss on first run) |
| B | gpt-4o-mini | 0.0195 | round2 fresh |
| C | sonnet | 0.3840 | round2 fresh |
| C | gpt-4o-mini | 0.0195 | round2 fresh |
| **total** |  | **0.8070** |  |
| hard cap |  | 5.0000 |  |

## Verdict

**PASS.** No oracle-derived content found in any template or rendered prompt. Projected total cost $0.8070 is under the $5.00 hard cap. F.3 may proceed.
