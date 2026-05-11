# E.4 File-level hit rate (diagnostics-only)

An instance is a *file-level hit* for a reviewer iff the reviewer produced ≥1 comment on any oracle file for that instance, regardless of line numbers. The denominator is N=20 (every Round 1 instance, including those for which the reviewer emitted no comments). This metric is diagnostic only; it is not merged into the official scoring module.

| reviewer | line_hits | line_hit_rate (95% CI) | file_hits | file_hit_rate (95% CI) | gap | n_comments | cpi |
|---|---:|---|---:|---|---:|---:|---:|
| claude-sonnet-4-5 | 0 | 0.00 [0.00, 0.16] | 16 | 0.80 [0.58, 0.92] | +0.80 | 30 | 1.50 |
| gpt-4o-mini | 3 | 0.15 [0.05, 0.36] | 13 | 0.65 [0.43, 0.82] | +0.50 | 49 | 2.45 |
| static | 3 | 0.15 [0.05, 0.36] | 15 | 0.75 [0.53, 0.89] | +0.60 | 242 | 12.10 |

## Reading note

- ``line_hit_rate`` is the same as ``instance_hit_rate`` in ``summary.csv`` (line-level matching under tolerance=3).
- ``file_hit_rate`` ignores line numbers; it measures whether the reviewer pointed at the right file at all.
- ``gap`` = ``file_hit_rate - line_hit_rate``. Large gap = reviewer is on the correct file but tolerance=3 / line number is what's failing.
- The Round 1 reviewer-input filter only feeds files that appear in the fix patch into reviewers, so a comment can be on a wrong file only if a reviewer hallucinates a different file path (the parser overrides the JSON ``file`` field back to the input file, so this is structurally impossible in Round 1).
