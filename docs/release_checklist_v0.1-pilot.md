# v0.1-pilot pre-tag checklist

Before running `git tag v0.1-pilot`, verify each item below.

- [ ] `pytest tests/` passes from a clean checkout.
- [ ] `bash repro/run.sh` runs to completion against the existing
      `.cache/` (cache-hit reproduction is the expected path).
- [ ] `CITATION.cff` parses as valid YAML (use
      `cffconvert --validate -i CITATION.cff` if available,
      otherwise `python -c "import yaml; yaml.safe_load(open('CITATION.cff'))"`).
- [ ] `README.md` contains the `## Key finding (pilot, n=20)`
      section, located between `## Motivation` and `## Task definition`.
- [ ] `outputs/round2/h_lite/dataset_revision.json` exists; the
      `hf_commit_sha` field is populated with a non-null commit hash.
- [ ] `git status` is clean (no staged or unstaged changes).
- [ ] `git log --oneline -10` is reviewed; no commit message
      contains co-author trailers, "Generated with...",
      "AI-assisted", em dashes, or marketing filler.
