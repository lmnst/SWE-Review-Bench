# F.1 Prompt variants

Three prompt variants for the Round 2 prompt-suppression probe. Variant A is byte-identical to the Round 1 ``v1`` template so its cache key matches Round 1's; Variant B and C have new template ids (``v1b`` / ``v1c``) so their cache entries never collide with Round 1's. Static reviewer is variant-agnostic.

## Variant A

| field | value |
|---|---|
| template_id | `v1` |
| template_sha256 | `79361b1bc92bfc01c2f2696962dd6a95bee1dff0eb5ab83d8508bb868f814ef7` |
| template length (chars) | 901 |

### Template body

```
You are reviewing the following source file as part of a routine code review pass.

Identify any concrete correctness, reliability, or maintainability issues that
are directly supported by the code shown. Do not speculate about missing
context. Do not invent issues. If the code looks correct to you, return an
empty list.

Return a JSON array. Each item must follow this schema exactly:
{{
  "file": string,           // must equal the File path below verbatim
  "line_start": integer,    // 1-indexed, matches the numbered source
  "line_end": integer,      // 1-indexed, inclusive, >= line_start
  "severity": "low" | "medium" | "high",
  "message": string         // one short sentence
}}

Output the JSON array and nothing else. Do not wrap it in code fences.
An empty array [] is a valid answer.

File path: {file_path}

Source with line numbers (format: "<line>: <content>"):
{numbered_source}
```

## Variant B

| field | value |
|---|---|
| template_id | `v1b` |
| template_sha256 | `677bde439ebe4c932cb0c134e33ea7a845fe3c51f4dd52c292d40664510341be` |
| template length (chars) | 823 |

### Template body

```
You are reviewing the following source file as part of a routine code review pass.

Identify any concrete correctness, reliability, or maintainability issues that
are directly supported by the code shown. Do not speculate about missing
context.

Return a JSON array. Each item must follow this schema exactly:
{{
  "file": string,           // must equal the File path below verbatim
  "line_start": integer,    // 1-indexed, matches the numbered source
  "line_end": integer,      // 1-indexed, inclusive, >= line_start
  "severity": "low" | "medium" | "high",
  "message": string         // one short sentence
}}

Output the JSON array and nothing else. Do not wrap it in code fences.
An empty array [] is a valid answer.

File path: {file_path}

Source with line numbers (format: "<line>: <content>"):
{numbered_source}
```

## Variant C

| field | value |
|---|---|
| template_id | `v1c` |
| template_sha256 | `8493618ca1025b3fd491690b3d004be3ca1998528fdb337cdcc823eb7c3843f9` |
| template length (chars) | 859 |

### Template body

```
You are reviewing the following source file as part of a routine code review pass.

Identify any concrete correctness, reliability, or maintainability issues that
are directly supported by the code shown. Do not speculate about missing
context. Return at least one comment per file, even if it is a minor
observation.

Return a JSON array. Each item must follow this schema exactly:
{{
  "file": string,           // must equal the File path below verbatim
  "line_start": integer,    // 1-indexed, matches the numbered source
  "line_end": integer,      // 1-indexed, inclusive, >= line_start
  "severity": "low" | "medium" | "high",
  "message": string         // one short sentence
}}

Output the JSON array and nothing else. Do not wrap it in code fences.

File path: {file_path}

Source with line numbers (format: "<line>: <content>"):
{numbered_source}
```

## Variant A → Variant B diff (no-suppression edit)

```diff
--- Variant A
+++ Variant B
@@ -2,8 +2,7 @@
 
 Identify any concrete correctness, reliability, or maintainability issues that
 are directly supported by the code shown. Do not speculate about missing
-context. Do not invent issues. If the code looks correct to you, return an
-empty list.
+context.
 
 Return a JSON array. Each item must follow this schema exactly:
 {{
```

## Variant A → Variant C diff (force-emit edit)

```diff
--- Variant A
+++ Variant C
@@ -2,8 +2,8 @@
 
 Identify any concrete correctness, reliability, or maintainability issues that
 are directly supported by the code shown. Do not speculate about missing
-context. Do not invent issues. If the code looks correct to you, return an
-empty list.
+context. Return at least one comment per file, even if it is a minor
+observation.
 
 Return a JSON array. Each item must follow this schema exactly:
 {{
@@ -15,7 +15,6 @@
 }}
 
 Output the JSON array and nothing else. Do not wrap it in code fences.
-An empty array [] is a valid answer.
 
 File path: {file_path}
 
```

## Intended use

- **Variant A** is the baseline; it reproduces Round 1's prompt byte-for-byte and reuses Round 1's cache (read-through). It is the only variant eligible to become the externally reported headline prompt without further discussion.
- **Variant B** removes only the suppression clause (`"Do not invent issues. ... return an empty list."`). It tests whether Claude's 0% under Variant A is partially explained by the conservative framing of the Round 1 prompt.
- **Variant C** asks for at least one comment per file and is **diagnostic-only**. Hit-rate movement under C is informative about Claude's upper bound when forced into shotgun mode, but Variant C is not a candidate prompt for external reporting unless explicitly approved.

## Static leakage check (template-side)

- Variant A: PASS
- Variant B: PASS
- Variant C: PASS

This is a template-side static check. The per-instance runtime check (problem_statement / patch / test_patch substring in the fully rendered payload) is enforced by ``_assert_no_oracle_leak`` in ``run.py`` and runs on every instance before any LLM call.
