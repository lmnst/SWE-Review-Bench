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
| astropy__astropy-14995 | astropy/astropy | 1 | 1 | 370b3ff97b3a |
| django__django-11001 | django/django | 1 | 1 | ad6b8e8ed785 |
| django__django-11049 | django/django | 1 | 1 | 50a0b98d3563 |
| django__django-11099 | django/django | 2 | 1 | cf203df5a90d |
| django__django-11133 | django/django | 1 | 1 | a0fd6d0a4a1c |
| django__django-11179 | django/django | 1 | 1 | a1896338de07 |
| django__django-11283 | django/django | 3 | 1 | 784f820070ee |
| django__django-11422 | django/django | 1 | 1 | 9fb9c9642c89 |
| django__django-11564 | django/django | 3 | 1 | 85742264db3f |
| django__django-11583 | django/django | 1 | 1 | 4725ae0dfda5 |
| django__django-11630 | django/django | 2 | 1 | 8b3ff50fedb2 |
| django__django-11797 | django/django | 1 | 1 | cfde8b687291 |
| django__django-11905 | django/django | 3 | 1 | 270d9b4ea721 |
| django__django-12708 | django/django | 1 | 1 | 03645a06338c |
| django__django-12747 | django/django | 2 | 1 | ff171b34d328 |
| django__django-12908 | django/django | 1 | 1 | b5fde7040e07 |
| django__django-12915 | django/django | 2 | 1 | 97ac78319161 |
| django__django-13033 | django/django | 1 | 1 | aa5413fb3771 |
| django__django-13220 | django/django | 2 | 1 | 9d9ec8f21fbf |
| django__django-13315 | django/django | 1 | 1 | fee7f9e8aebf |
| django__django-13321 | django/django | 1 | 1 | e1d3c892ea86 |
| django__django-13448 | django/django | 2 | 1 | cafd7a8b842c |
| django__django-13551 | django/django | 2 | 1 | 8f5a82819897 |
| django__django-13590 | django/django | 1 | 1 | ba7ed1d4001a |
| django__django-13658 | django/django | 1 | 1 | 667081efc6e0 |
| django__django-13757 | django/django | 1 | 1 | b6be4919dd2d |
| django__django-13768 | django/django | 3 | 1 | d0e765aea3be |
| django__django-14017 | django/django | 1 | 1 | 15c067a3f0ff |
| django__django-14155 | django/django | 1 | 1 | 61d14e3a2a18 |
| django__django-14382 | django/django | 1 | 1 | c0c9645f081c |
| django__django-14580 | django/django | 1 | 1 | b86a035653ee |
| django__django-14752 | django/django | 2 | 1 | 53ef09b36c3c |
| django__django-14787 | django/django | 1 | 1 | 96d2dfb54416 |
| django__django-14855 | django/django | 1 | 1 | d3030b5f4fad |
| django__django-14997 | django/django | 1 | 1 | 2711bd52ea19 |
| django__django-15347 | django/django | 1 | 1 | 17762e80dbf2 |
| django__django-15498 | django/django | 1 | 1 | 34ae3ea20a53 |
| django__django-15695 | django/django | 1 | 1 | 7d0932bd7b42 |
| django__django-15789 | django/django | 2 | 1 | 101ff0884f63 |
| django__django-15851 | django/django | 1 | 1 | d23e1d4544ee |
| django__django-15902 | django/django | 1 | 1 | 0bfbeb2d8f82 |
| django__django-16400 | django/django | 1 | 1 | 8c31b8511a83 |
| django__django-16408 | django/django | 2 | 1 | 87ea3c7bb991 |
| django__django-16527 | django/django | 1 | 1 | ec7af453a8f6 |
| django__django-16816 | django/django | 1 | 1 | 4a17b8b7b9bd |
| django__django-16873 | django/django | 1 | 1 | 2257e76c384a |
| django__django-17051 | django/django | 1 | 1 | 5b8368267020 |
| django__django-17087 | django/django | 1 | 1 | 02155d1bb6d5 |
| matplotlib__matplotlib-23476 | matplotlib/matplotlib | 1 | 1 | 0d25d0202773 |
| matplotlib__matplotlib-25079 | matplotlib/matplotlib | 1 | 1 | 9fc331cd517d |
| matplotlib__matplotlib-25311 | matplotlib/matplotlib | 2 | 1 | ee3099538e20 |
| matplotlib__matplotlib-25498 | matplotlib/matplotlib | 2 | 1 | 815d9d133ced |
| matplotlib__matplotlib-26020 | matplotlib/matplotlib | 2 | 1 | 3b4449b50f15 |
| pallets__flask-4045 | pallets/flask | 2 | 1 | 6c4055e1cb35 |
| psf__requests-1963 | psf/requests | 1 | 1 | deb8b9018ea0 |
| psf__requests-863 | psf/requests | 1 | 1 | 1fe8ef6f1596 |
| pylint-dev__pylint-6506 | pylint-dev/pylint | 1 | 1 | d998b15278fc |
| pylint-dev__pylint-7080 | pylint-dev/pylint | 1 | 1 | f908ad1f6d4b |
| pylint-dev__pylint-7228 | pylint-dev/pylint | 2 | 1 | 8b6796ff816c |
| pytest-dev__pytest-5103 | pytest-dev/pytest | 3 | 1 | 5b621eb0099e |
| pytest-dev__pytest-5227 | pytest-dev/pytest | 1 | 1 | e8193ea0dee0 |
| pytest-dev__pytest-5413 | pytest-dev/pytest | 1 | 1 | 34f5b421e92c |
| pytest-dev__pytest-5692 | pytest-dev/pytest | 2 | 1 | b5c39d27ceb0 |
| pytest-dev__pytest-6116 | pytest-dev/pytest | 1 | 1 | 2d80109efb3a |
| pytest-dev__pytest-7168 | pytest-dev/pytest | 1 | 1 | 6461134e72dd |
| pytest-dev__pytest-7432 | pytest-dev/pytest | 1 | 1 | fe1bcec84608 |
| pytest-dev__pytest-7490 | pytest-dev/pytest | 2 | 1 | 88a7af7e1236 |
| pytest-dev__pytest-9359 | pytest-dev/pytest | 1 | 1 | 2d9598fe2b5e |
| scikit-learn__scikit-learn-10508 | scikit-learn/scikit-learn | 2 | 1 | 7664039eb8b6 |
| scikit-learn__scikit-learn-10949 | scikit-learn/scikit-learn | 2 | 1 | aa168cdbc587 |
| scikit-learn__scikit-learn-13496 | scikit-learn/scikit-learn | 3 | 1 | 01a911f7883e |
| scikit-learn__scikit-learn-13497 | scikit-learn/scikit-learn | 2 | 1 | 05b8e713181a |
| scikit-learn__scikit-learn-13779 | scikit-learn/scikit-learn | 1 | 1 | 6faf85c3ffaa |
| scikit-learn__scikit-learn-14087 | scikit-learn/scikit-learn | 2 | 1 | 819cd93cf36a |
| scikit-learn__scikit-learn-14092 | scikit-learn/scikit-learn | 3 | 1 | b5a75a0010d0 |
| sphinx-doc__sphinx-8273 | sphinx-doc/sphinx | 3 | 1 | 6bc8c98f2c69 |
| sphinx-doc__sphinx-8282 | sphinx-doc/sphinx | 3 | 1 | 2f37479fcc8b |
| sphinx-doc__sphinx-8474 | sphinx-doc/sphinx | 1 | 1 | 5e40a28ed9b2 |
| sphinx-doc__sphinx-8595 | sphinx-doc/sphinx | 1 | 1 | e49e0193e868 |
| sphinx-doc__sphinx-8721 | sphinx-doc/sphinx | 1 | 1 | b280454dbde6 |
| sympy__sympy-12454 | sympy/sympy | 2 | 1 | 49c926cd1a82 |
| sympy__sympy-13177 | sympy/sympy | 1 | 1 | 394d8cd19e30 |
| sympy__sympy-13437 | sympy/sympy | 1 | 1 | e4bd63feda4a |
| sympy__sympy-13480 | sympy/sympy | 1 | 1 | 41082dc7d705 |
| sympy__sympy-13895 | sympy/sympy | 2 | 1 | 2ce04f2aef48 |
| sympy__sympy-14817 | sympy/sympy | 1 | 1 | 2629d8f07e58 |
| sympy__sympy-16792 | sympy/sympy | 3 | 1 | 4c45274d348e |
| sympy__sympy-17655 | sympy/sympy | 1 | 1 | 3e395e2082ba |
| sympy__sympy-18087 | sympy/sympy | 2 | 1 | 07c2e75f11ef |
| sympy__sympy-19007 | sympy/sympy | 2 | 1 | 38129c208a31 |
| sympy__sympy-19254 | sympy/sympy | 1 | 1 | 404fa50ef899 |
| sympy__sympy-20212 | sympy/sympy | 1 | 1 | 07d36687d22f |
| sympy__sympy-20322 | sympy/sympy | 2 | 1 | 5399fa26e0af |
| sympy__sympy-20442 | sympy/sympy | 2 | 1 | e94292e05aa2 |
| sympy__sympy-21627 | sympy/sympy | 1 | 1 | b5ba97320a3a |
| sympy__sympy-22005 | sympy/sympy | 1 | 1 | 10762dbd420f |
| sympy__sympy-22714 | sympy/sympy | 1 | 1 | 1e50cdf5a6d2 |
| sympy__sympy-23117 | sympy/sympy | 3 | 1 | 05baa345b3ee |
| sympy__sympy-23191 | sympy/sympy | 1 | 1 | 82f40a995830 |
| sympy__sympy-23262 | sympy/sympy | 1 | 1 | cdb5c722cb72 |
