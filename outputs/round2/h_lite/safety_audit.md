# H-lite Task 1 — repo safety audit

Read-only. No files modified. Findings inform proposed mutations (``.gitignore`` hardening, ``.env.example`` placeholder replacement, LICENSE choice) that require explicit user approval before being applied.

## 1. Secret grep

Patterns scanned (every pattern reported separately):

- `ANTHROPIC_API_KEY=`
- `OPENAI_API_KEY=`
- `sk-ant-* key shape`
- `sk-proj-* key shape`
- `generic sk- key shape`
- `Bearer header`
- `api_key= assignment`
- `Authorization: header`

Scope: working tree excluding `.venv/`, `.cache/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, build artefacts, and binary files (PNG / JPG / PDF / WHL etc.). Git history is **not** scanned (no git repo).

### `.env` — expected: live key in gitignored .env (acceptable; never publish)

| line | pattern | masked preview |
|---:|---|---|
| 2 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 5 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 2 | `sk-ant-* key shape` | `sk-ant-api...[REDACTED, len=108]` |
| 5 | `sk-proj-* key shape` | `sk-proj-2_...[REDACTED, len=164]` |
| 2 | `generic sk- key shape` | `sk-ant-api...[REDACTED, len=108]` |
| 5 | `generic sk- key shape` | `sk-proj-2_...[REDACTED, len=164]` |

### `.env.example` — rotated per user confirmation 2026-05-11; replace with placeholder before publishing

| line | pattern | masked preview |
|---:|---|---|
| 2 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 5 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |

### `outputs/round2/h_lite/safety_audit.md` — audit report documentation (this audit's own output)

| line | pattern | masked preview |
|---:|---|---|
| 9 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 24 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 35 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 42 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 43 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 44 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 45 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 46 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 47 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 48 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 49 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 50 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 51 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 52 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 53 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 54 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 55 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 56 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 57 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 58 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 59 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 60 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 61 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 62 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 63 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 64 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 65 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 66 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 67 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 68 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 69 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 70 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 71 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 114 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 115 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 116 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 117 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 118 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 119 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 120 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 143 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 252 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 10 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 25 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 36 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 72 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 73 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 74 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 75 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 76 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 77 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 78 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 79 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 80 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 81 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 82 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 83 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 84 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 85 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 86 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 87 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 88 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 89 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 90 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 91 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 92 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 93 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 94 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 95 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 121 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 122 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 123 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 124 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 125 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 126 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 255 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 16 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 96 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 97 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 98 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 99 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 100 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 101 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 102 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 103 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 104 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 105 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 106 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 107 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 108 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 127 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 128 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 129 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 130 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 131 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |

### `swe_review_bench/diagnostics/h1_safety_audit.py` — audit/diagnostic infrastructure (pattern definition or placeholder template; not a literal key)

| line | pattern | masked preview |
|---:|---|---|
| 52 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 147 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 158 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 177 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 199 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 401 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 459 | `ANTHROPIC_API_KEY=` | `ANTHROPIC_...[REDACTED, len=18]` |
| 53 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 148 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 159 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 178 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 200 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 462 | `OPENAI_API_KEY=` | `OPENAI_API...[REDACTED, len=15]` |
| 59 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 150 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 161 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 180 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |
| 202 | `Authorization: header` | `Authorizat...[REDACTED, len=16]` |

## 2. `.env` / `.env.example` status

| field | value |
|---|---|
| .env exists | True |
| .env in .gitignore | True |
| .env tracked by git | n/a (no git repo) |
| .env.example exists | True |
| .env.example contains real-format key bytes (rotated) | False |

**`.env.example` posture**: contents are placeholder-only (no real-format key bytes detected). Originally contained two key-shaped strings; rotated on the Anthropic and OpenAI consoles on 2026-05-11 and the file was sanitised to placeholders the same day. No further action required.

## 3. `.gitignore` hardening proposal

### Current `.gitignore`

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
build/
dist/
.pytest_cache/
.ruff_cache/
.mypy_cache/

# Virtualenv
.venv/
venv/
env/

# IDE
.idea/
.vscode/
*.swp

# Secrets
.env
.env.*
!.env.example

# Project caches (all subdirectories, recursively)
.cache/
.cache/llm/
.cache/repos/
.cache/round1/
.cache/round2/

# Outputs cache only (do NOT ignore the outputs CSV/PNG headlines;
# selectively allow the public-facing artefacts back in below)
outputs/cache/
outputs/round2/cache/

# Compiled / OS noise
*.pyc
```

### Proposed `.gitignore`

Reasons:

- `.env.*` + `!.env.example` make sure variants like `.env.local` are ignored while `.env.example` stays version-controllable.
- `.cache/` (no trailing `*`) ignores the directory recursively, covering `.cache/round2/llm/raw/` and any future Round-N caches.
- `outputs/cache/` and `outputs/round2/cache/` are listed even though they currently do not exist, in case future tooling writes there.
- The current `outputs/*` rule ignores all of `outputs/`. Once this repo is moved to a git remote you will want to selectively unignore the headline CSVs (e.g. `!outputs/results.csv`, `!outputs/summary.csv`, `!outputs/round2/*.csv`). This audit does not pre-decide that policy; left for a follow-up.

```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
build/
dist/
.pytest_cache/
.ruff_cache/
.mypy_cache/

# Virtualenv
.venv/
venv/
env/

# IDE
.idea/
.vscode/
*.swp

# Secrets
.env
.env.*
!.env.example

# Project caches (all subdirectories, recursively)
.cache/
.cache/llm/
.cache/repos/
.cache/round1/
.cache/round2/

# Outputs cache only (do NOT ignore the outputs CSV/PNG headlines;
# selectively allow the public-facing artefacts back in below)
outputs/cache/
outputs/round2/cache/

# Compiled / OS noise
*.pyc
```

**Not applied automatically.** Apply only after you confirm.

## 4. Proposed `.env.example` replacement

Replace the contents of `.env.example` with the following (real-format key bytes removed):

```bash
# Anthropic API key for Claude Sonnet (Milestone B+)
ANTHROPIC_API_KEY=sk-ant-...your-anthropic-key...

# OpenAI API key for GPT-4o-mini (Milestone B+)
OPENAI_API_KEY=sk-proj-...your-openai-key...

# Optional model id override. Format: "<from>=<to>"
# Set this if the model id is not recognised by your litellm version.
# Example:
#   MODEL_ID_OVERRIDE=claude-sonnet-4-5=claude-sonnet-4-5-20250929
MODEL_ID_OVERRIDE=
```

**Not applied automatically.** Apply only after you confirm.

## 5. Cache and raw-LLM-output audit

| field | value |
|---|---|
| round1_raw_dir_exists | True |
| round2_raw_dir_exists | True |
| round1_raw_files | 40 |
| round2_raw_files | 80 |
| covered_by_gitignore | True |

Would-be commands once this repo becomes a git repo (text only — do not run):

```bash
# Ensure all current cache contents stay untracked
git rm --cached -r --ignore-unmatch .cache
git rm --cached -r --ignore-unmatch outputs/cache
git rm --cached -r --ignore-unmatch outputs/round2/cache
```

## 6. Files larger than 1 MB under `outputs/` and `.cache/`

| path | size | tracked_by_git | public_ok |
|---|---:|---|---|
| `.cache/repos/django__django/.git/objects/pack/pack-edc2232d595b735e8c9da74ac6614112ea4a4885.pack` | 55.33 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/matplotlib__matplotlib/.git/objects/pack/pack-8ba7f0f977dc096c1defaf09a50413562ad1a34d.pack` | 44.86 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/sympy__sympy/.git/objects/pack/pack-0dd464fd51f80809806abba115f954a5ef7a85ce.pack` | 40.38 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/matplotlib__matplotlib/.git/objects/pack/pack-3255583bae294ef860e485cf5cd9345c27ecbe05.pack` | 31.74 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/matplotlib__matplotlib/.git/objects/pack/pack-e560004b3682f29d6225952d331e86652f886db3.pack` | 23.17 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/sphinx-doc__sphinx/.git/objects/pack/pack-47e56c1efdec92f4e85bd920e7bad8765238c500.pack` | 15.82 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/django__django/.git/objects/pack/pack-dc09017e720d5013ba09d36b6d7c6123097cc62b.pack` | 11.47 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/django__django/.git/objects/pack/pack-edc2232d595b735e8c9da74ac6614112ea4a4885.idx` | 10.31 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/sympy__sympy/.git/objects/pack/pack-0dd464fd51f80809806abba115f954a5ef7a85ce.idx` | 8.25 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/django__django/.git/objects/pack/pack-929281b221493a77142c9ca386bfe7d98e6e10be.pack` | 8.05 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/sympy__sympy/.git/objects/pack/pack-4ce4fa1eaa71cd53999f018e206e1188032f59e4.pack` | 7.94 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/matplotlib__matplotlib/.git/objects/pack/pack-8ba7f0f977dc096c1defaf09a50413562ad1a34d.idx` | 6.55 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/django__django/.git/objects/pack/pack-182057802cbf6f913577a3d80ab7ba0d49a4397b.pack` | 6.39 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/django__django/.git/objects/pack/pack-112e89f72f589af44d241cfca0805a5be5c72fb5.pack` | 6.37 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/sympy__sympy/.git/objects/pack/pack-42547f706eab961661e7bd2d744a1a510ed26bb5.pack` | 5.87 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/sphinx-doc__sphinx/.git/objects/pack/pack-5484bffcc0bc8e4f8a395930b45304e14ca9dab3.pack` | 5.64 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/sympy__sympy/.git/objects/pack/pack-164b7dfc6d2d455e5ef5c167d72c3b97017ee02a.pack` | 5.62 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/django__django/.git/objects/pack/pack-a1130a68db452245a2ad6e75df9a6aee10b8e0f1.pack` | 4.07 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/django__django/.git/objects/pack/pack-955b3d7ee9bafadee243ccb92e910ca4cb9aef89.pack` | 3.98 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/django__django/.git/objects/pack/pack-f694c90ceccec4047e8f7a1d6254b92c4b2d9b94.pack` | 3.80 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/matplotlib__matplotlib/.git/objects/pack/pack-ffc69b198eb2a53638d39f391dfd446b0729c70d.pack` | 3.46 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/sympy__sympy/.git/objects/pack/pack-02c0edbcf2f2d2d68fee11615941ff4fa248d83d.pack` | 3.26 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/django__django/.git/objects/pack/pack-44ea2b13e66be0b47ea714f7b1935c8eaebd479b.pack` | 3.02 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/sphinx-doc__sphinx/.git/objects/pack/pack-47e56c1efdec92f4e85bd920e7bad8765238c500.idx` | 2.94 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/sphinx-doc__sphinx/.git/objects/pack/pack-a28e6fb90df1a720c3fcc6a29e1aef4008641a52.pack` | 2.31 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/django__django/.git/objects/pack/pack-ca87e44bfb4009ac439571a13f2b1fc38149ea21.pack` | 2.14 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/django__django/.git/objects/pack/pack-08941b7196ac086180879fab7cf9e9e15f9595e1.pack` | 1.72 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/matplotlib__matplotlib/lib/matplotlib/tests/baseline_images/test_axes/pcolormesh.svg` | 1.69 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/matplotlib__matplotlib/lib/matplotlib/tests/baseline_images/test_backend_ps/type42_without_prep.eps` | 1.49 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |
| `.cache/repos/sympy__sympy/sympy/integrals/rubi/rubi_tests/tests/test_trinomials.py` | 1.44 MB | n/a (no git repo) | no (cache, may contain raw LLM responses) |

## 7. License

`LICENSE` exists; reference it from README.

## 8. Verdict

No unclassified secret-pattern matches. All hits are either in `.env` (gitignored, holds live keys) or in `.env.example` (rotated/dead keys per user confirmation) or are env-var *references* in source code.

