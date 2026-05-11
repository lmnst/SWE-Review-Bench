# E.1 Comment landing distribution

## Per-reviewer summary (Round 1, N=20 instances)

| reviewer | n_comments | n_inst_with_comments | mean_cpi | median_cpi | p10 | p90 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| claude-sonnet-4-5 | 30 | 16/20 | 1.50 | 1 | 0 | 2 | 0 | 5 |
| gpt-4o-mini | 49 | 13/20 | 2.45 | 3 | 0 | 5 | 0 | 6 |
| static | 242 | 15/20 | 12.10 | 20 | 0 | 20 | 0 | 20 |

## Distance-from-oracle bucket distribution

Rates are over each reviewer's own comment population; Wilson 95% CI in brackets.

| reviewer | wrong_file | right_d0 | right_d1-3 | right_d4-10 | right_d>10 | invalid |
|---|---|---|---|---|---|---|
| claude-sonnet-4-5 | 0 (0%, [0.00,0.11]) | 0 (0%, [0.00,0.11]) | 0 (0%, [0.00,0.11]) | 1 (3%, [0.01,0.17]) | 29 (97%, [0.83,0.99]) | 0 (0%, [0.00,0.11]) |
| gpt-4o-mini | 0 (0%, [0.00,0.07]) | 2 (4%, [0.01,0.14]) | 3 (6%, [0.02,0.17]) | 1 (2%, [0.00,0.11]) | 43 (88%, [0.76,0.94]) | 0 (0%, [0.00,0.07]) |
| static | 0 (0%, [0.00,0.02]) | 3 (1%, [0.00,0.04]) | 4 (2%, [0.01,0.04]) | 4 (2%, [0.01,0.04]) | 231 (95%, [0.92,0.97]) | 0 (0%, [0.00,0.02]) |

### Reading note

- ``wrong_file``: comment's file does not match any oracle file for the instance after symmetric path normalisation.
- ``right_file_distance_0``: comment range overlaps an oracle hunk range (would be a hit at tolerance=0).
- ``right_file_distance_1_to_3``: file matches and minimum line gap is 1-3 inclusive (would be a hit at tolerance=3, the Round 1 setting).
- ``right_file_distance_4_to_10``: file matches but tolerance=3 cuts these off; tolerance=10 would catch them.
- ``right_file_distance_gt_10``: file matches, lines far from any oracle hunk.
- ``invalid_line_or_file``: line_start/line_end missing or unparseable.

## Claude theme classification (full listing)

### Theme counts

| theme | count |
|---|---:|
| hardcoded_value | 0 |
| missing_validation | 2 |
| error_handling | 0 |
| style_or_readability | 0 |
| docstring_or_comment | 0 |
| typing_or_api_contract | 0 |
| resource_or_state_management | 0 |
| performance | 0 |
| test_or_debug_artifact | 0 |
| possible_correctness_bug | 9 |
| other | 19 |

### Per-comment listing

| instance | idx | file | lines | bucket | nearest_site | dist | theme | message |
|---|---:|---|---:|---|---|---:|---|---|
| django__django-11133 | 1 | django/http/response.py | 173 | right_file_distance_gt_10 | site-0001 | 56 | other | Should use datetime.datetime.utcnow() instead of expires.utcnow() which is invalid. |
| django__django-11133 | 2 | django/http/response.py | 199 | right_file_distance_gt_10 | site-0001 | 30 | missing_validation | samesite validation excludes 'none' which is a valid SameSite value. |
| django__django-11422 | 1 | django/utils/autoreload.py | 563 | right_file_distance_gt_10 | site-0001 | 443 | other | setDaemon() is deprecated; use daemon property or daemon parameter in Thread constructor instead. |
| django__django-11422 | 2 | django/utils/autoreload.py | 77 | right_file_distance_gt_10 | site-0001 | 37 | possible_correctness_bug | Exception constructor call may fail if the original exception requires arguments. |
| django__django-12915 | 1 | django/contrib/staticfiles/handlers.py | 77-79 | right_file_distance_gt_10 | site-0002 | 20 | other | ASGIStaticFilesHandler.__init__ does not call super().__init__(), unlike StaticFilesHandler which does. |
| django__django-13033 | 1 | django/db/models/sql/compiler.py | 390 | right_file_distance_gt_10 | site-0001 | 337 | possible_correctness_bug | Potential IndexError if regex search returns None or has no groups. |
| django__django-13033 | 2 | django/db/models/sql/compiler.py | 403 | right_file_distance_gt_10 | site-0001 | 324 | possible_correctness_bug | Potential IndexError if regex search returns None or has no groups. |
| django__django-13315 | 1 | django/forms/models.py | 1357 | right_file_distance_gt_10 | site-0001 | 1251 | missing_validation | Filter result is created but never used, making the validation ineffective. |
| django__django-13551 | 1 | django/contrib/auth/tokens.py | 104 | right_file_distance_4_to_10 | site-0002 | 4 | other | datetime.now() returns naive datetime which may cause issues when comparing with timezone-aware last_login field. |
| django__django-14382 | 1 | django/core/management/templates.py | 1 | right_file_distance_gt_10 | site-0001 | 72 | other | The 'cgi' module is deprecated since Python 3.11 and removed in Python 3.13. |
| django__django-14382 | 2 | django/core/management/templates.py | 270 | right_file_distance_gt_10 | site-0001 | 189 | other | Using string split on path assumes Unix-style separators but should use os.path.basename. |
| django__django-16408 | 1 | django/db/models/sql/compiler.py | 470 | right_file_distance_gt_10 | site-0001 | 804 | possible_correctness_bug | Regex search result is accessed without checking if match exists, will raise AttributeError if no match found. |
| django__django-16408 | 2 | django/db/models/sql/compiler.py | 483 | right_file_distance_gt_10 | site-0001 | 791 | possible_correctness_bug | Regex search result is accessed without checking if match exists, will raise AttributeError if no match found. |
| django__django-16816 | 1 | django/contrib/admin/checks.py | 1000 | right_file_distance_gt_10 | site-0001 | 76 | possible_correctness_bug | Using issubclass without _issubclass wrapper can raise TypeError if item is not a class. |
| django__django-17087 | 1 | django/db/migrations/serializer.py | 291 | right_file_distance_gt_10 | site-0001 | 117 | other | Empty set serialization produces 'set()' but _format returns string with '%s' placeholder that expects content, resulting in 'set([])' instead of 'set()'. |
| matplotlib__matplotlib-23476 | 1 | lib/matplotlib/figure.py | 2383 | right_file_distance_gt_10 | site-0001 | 640 | other | Duplicate connection of 'key_release_event' handler at line 2383 (already connected at line 2382). |
| matplotlib__matplotlib-23476 | 2 | lib/matplotlib/figure.py | 404-405 | right_file_distance_gt_10 | site-0001 | 2618 | other | Dictionary key 'rotation_mode' is added to info dict but not used in _suplabels method. |
| sphinx-doc__sphinx-8282 | 1 | sphinx/ext/autodoc/__init__.py | 1932-1933 | right_file_distance_gt_10 | site-0003 | 44 | possible_correctness_bug | Off-by-one error: checks `len(sig.parameters) == 1` but accesses `params[1]`, which would cause IndexError. |
| sphinx-doc__sphinx-8282 | 2 | sphinx/ext/autodoc/__init__.py | 1285-1286 | right_file_distance_gt_10 | site-0001 | 39 | other | Inconsistent early return check: returns early if `len(sig.parameters) == 0` but similar function at line 1932 checks for `== 1`. |
| sphinx-doc__sphinx-8474 | 1 | sphinx/domains/std.py | 236 | right_file_distance_gt_10 | site-0001 | 616 | other | Using first ID from signode['ids'] list which may be empty or contain wrong ID after multiple IDs were appended in lines 224-229. |
| sphinx-doc__sphinx-8474 | 2 | sphinx/domains/std.py | 245 | right_file_distance_gt_10 | site-0001 | 607 | other | Using first ID from signode['ids'] list which may be empty or contain wrong ID after multiple IDs were appended in lines 224-229. |
| sphinx-doc__sphinx-8474 | 3 | sphinx/domains/std.py | 541 | right_file_distance_gt_10 | site-0001 | 311 | possible_correctness_bug | Checking title[0] without verifying title is non-empty could raise IndexError. |
| sphinx-doc__sphinx-8474 | 4 | sphinx/domains/std.py | 667-668 | right_file_distance_gt_10 | site-0001 | 184 | possible_correctness_bug | Tuple unpacking assumes objects dictionary values are 2-tuples, but could fail if data is corrupted. |
| sphinx-doc__sphinx-8474 | 5 | sphinx/domains/std.py | 870 | right_file_distance_gt_10 | site-0001 | 11 | other | String 'number' checked with 'in' operator but should be '{number}' to match format string pattern. |
| sympy__sympy-16792 | 1 | sympy/utilities/codegen.py | 277 | right_file_distance_gt_10 | site-0001 | 418 | other | Identity comparison 'is' used instead of equality '==' for string comparison. |
| sympy__sympy-16792 | 2 | sympy/utilities/codegen.py | 279 | right_file_distance_gt_10 | site-0001 | 416 | other | Identity comparison 'is' used instead of equality '==' for string comparison. |
| sympy__sympy-16792 | 3 | sympy/utilities/codegen.py | 958 | right_file_distance_gt_10 | site-0003 | 213 | other | CodeGen is called as a function but it's a class, should be CodeGenError. |
| sympy__sympy-16792 | 4 | sympy/utilities/codegen.py | 964 | right_file_distance_gt_10 | site-0003 | 219 | other | Typo in error message: 'variabels' should be 'variables'. |
| sympy__sympy-20442 | 1 | sympy/physics/units/util.py | 134 | right_file_distance_gt_10 | site-0002 | 98 | other | Dictionary comprehension iterates over the same set it's building from, causing undefined behavior. |
| sympy__sympy-21627 | 1 | sympy/functions/elementary/complexes.py | 1232 | right_file_distance_gt_10 | site-0001 | 620 | other | Method 'eval' is a classmethod but uses 'self' instead of 'cls' as first parameter. |

## Classifier rules

Classification is deterministic regex over the message text; the rule table lives in ``swe_review_bench/diagnostics/classify.py``. ``possible_correctness_bug`` wins over weaker tags when both fire on the same message; ``other`` is the unmatched fallback. No LLM is used; classification does not affect scoring.
