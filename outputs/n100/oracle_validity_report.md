# Oracle construct-validity report

LLM-assisted draft, human-confirmed. Audit of a 30-instance stratified sample from the n=100 study; this is construct-validity evidence on the sample, not a proportion estimate over full SWE-bench Lite.

Sites audited: 48  (unfilled rows skipped: 0)

## Site-level

- bug: 24
- related: 7
- unrelated: 17
- site-level oracle validity (bug-site fraction): 24/48 = 0.500 Wilson95 [0.364, 0.636]

## Instance-level

- instances audited: 30
- with at least one bug site: 20/30 = 0.667
- with no bug site: 10/30 = 0.333 Wilson95 [0.192, 0.512]

## Audited-subset sensitivity (20 confirmed bug instances)

Instance hit rate restricted to the confirmed bug subset. This is a sensitivity check on a small subset, NOT a replacement for the n=100 headline.

- claude-sonnet-4-5 A: 2/20 = 0.100
- claude-sonnet-4-5 B: 4/20 = 0.200
- gpt-4o-mini A: 2/20 = 0.100
- gpt-4o-mini B: 6/20 = 0.300
