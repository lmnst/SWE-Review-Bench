# E.0.5 Oracle reconstruction log
## Resolution path used
Path **(3) fresh HF-dataset patch parse**: the existing ``swe_review_bench.data.loader.load_instances(n=20, seed=42)`` was called and each instance's ``patch`` field was fed to ``swe_review_bench.data.oracle.build_oracle_sites(strict_mode=False)``. No Round 1 cache file holding oracle structures was found in ``.cache/``; ``.cache/llm/`` contains only per-reviewer-call payloads, and ``.cache/repos/`` only holds shallow git clones.
Because the oracle reconstruction reuses the same deterministic loader, sampling seed, dataset revision, and parsing function as Round 1, the resulting site IDs and ranges are expected to be byte-identical to those Round 1 produced. The cross-check below verifies this against the ``matched_oracle_site_id`` column in ``results.csv``.
## Determinism check
OK: ``build_oracle_sites`` produced identical results across two consecutive calls on every instance.
## Cross-check vs Round 1 results.csv
Hit rows in ``outputs/results.csv``: 12

Disagreements between reconstructed sites and Round 1 hit rows: 0

OK: every Round 1 hit row maps to a reconstructed site with overlap under the recorded tolerance (3).
## Instance summary
| instance_id | repo | n_sites | n_oracle_files | patch_sha256[:12] |
|---|---|---:|---:|---|
| django__django-11099 | django/django | 2 | 1 | cf203df5a90d |
| django__django-11133 | django/django | 1 | 1 | a0fd6d0a4a1c |
| django__django-11283 | django/django | 3 | 1 | 784f820070ee |
| django__django-11422 | django/django | 1 | 1 | 9fb9c9642c89 |
| django__django-12915 | django/django | 2 | 1 | 97ac78319161 |
| django__django-13033 | django/django | 1 | 1 | aa5413fb3771 |
| django__django-13315 | django/django | 1 | 1 | fee7f9e8aebf |
| django__django-13551 | django/django | 2 | 1 | 8f5a82819897 |
| django__django-14382 | django/django | 1 | 1 | c0c9645f081c |
| django__django-15851 | django/django | 1 | 1 | d23e1d4544ee |
| django__django-16408 | django/django | 2 | 1 | 87ea3c7bb991 |
| django__django-16816 | django/django | 1 | 1 | 4a17b8b7b9bd |
| django__django-17087 | django/django | 1 | 1 | 02155d1bb6d5 |
| matplotlib__matplotlib-23476 | matplotlib/matplotlib | 1 | 1 | 0d25d0202773 |
| matplotlib__matplotlib-25498 | matplotlib/matplotlib | 2 | 1 | 815d9d133ced |
| sphinx-doc__sphinx-8282 | sphinx-doc/sphinx | 3 | 1 | 2f37479fcc8b |
| sphinx-doc__sphinx-8474 | sphinx-doc/sphinx | 1 | 1 | 5e40a28ed9b2 |
| sympy__sympy-16792 | sympy/sympy | 3 | 1 | 4c45274d348e |
| sympy__sympy-20442 | sympy/sympy | 2 | 1 | e94292e05aa2 |
| sympy__sympy-21627 | sympy/sympy | 1 | 1 | b5ba97320a3a |
