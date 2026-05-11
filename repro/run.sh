#!/usr/bin/env bash
# repro/run.sh -- SWE-Review-Bench one-command reproduction (cache-safe).
#
# Default behaviour: $0 spend. Runs the leakage pytest suite and prints
# the headline tables and Wilson intervals from the existing pilot
# artefacts. No paid LLM call is issued unless the caller has staged a
# warm cache AND has explicitly opted in via $RUN_PAID_REPLAY=1.
#
# Round 1 + Round 2 LLM cache replay would, with a warm cache, be a 100%
# cache-hit re-run that emits the same CSVs byte-for-byte. The current
# swe_review_bench.run CLI does not expose a fail-on-cache-miss flag, so
# this script does not re-invoke the orchestrator; the headline tables
# are read directly from the frozen CSVs.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${PROJECT_ROOT}"

cyan='\033[36m'; green='\033[32m'; yellow='\033[33m'; red='\033[31m'; nc='\033[0m'

banner() {
    printf "${cyan}== %s ==${nc}\n" "$1"
}

note() {
    printf "${yellow}note:${nc} %s\n" "$1"
}

fail() {
    printf "${red}fail:${nc} %s\n" "$1" >&2
    exit 1
}

# ---------------------------------------------------------------------------
# Step 1: warnings
# ---------------------------------------------------------------------------

banner "SWE-Review-Bench reproduction"
cat <<'EOF'
This script is cache-safe by default.

* A cached reproduction (this default) runs in under a few minutes,
  issues no paid API calls, and prints the existing headline tables.
* An uncached reproduction would re-issue the LLM calls behind
  Round 1 baseline and Round 2 Variants A/B/C. Re-issuing those calls
  is NOT enabled here: the current orchestrator does not expose a
  fail-on-cache-miss flag, so re-invoking it could silently spend
  money.

If you need to bypass the safe-default, set RUN_PAID_REPLAY=1 in your
environment. The script will abort because cache-only replay is not
exposed by the orchestrator; no paid call is issued.
EOF

# ---------------------------------------------------------------------------
# Step 2: environment-variable check
# ---------------------------------------------------------------------------

banner "checking environment variables"
ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}"
OPENAI_API_KEY="${OPENAI_API_KEY:-}"
RUN_PAID_REPLAY="${RUN_PAID_REPLAY:-0}"

if [ -z "${ANTHROPIC_API_KEY}" ] && [ -z "${OPENAI_API_KEY}" ]; then
    note "Neither ANTHROPIC_API_KEY nor OPENAI_API_KEY is set in the shell."
    note "That is fine for the default cache-safe run: the LLM cache and"
    note "the existing CSVs are read directly, and no live call is issued."
else
    note "API keys detected in the shell. They are not used by this script"
    note "in default mode; they would only matter if RUN_PAID_REPLAY=1."
fi

if [ "${RUN_PAID_REPLAY}" = "1" ]; then
    note "RUN_PAID_REPLAY=1 detected, but cache-only replay is not"
    note "exposed by swe_review_bench.run. Aborting before any paid"
    note "call could be made."
    fail "uncached replay not supported; unset RUN_PAID_REPLAY"
fi

# ---------------------------------------------------------------------------
# Step 3: dependencies
# ---------------------------------------------------------------------------

banner "verifying dependencies"
if command -v python >/dev/null 2>&1; then
    PY=python
elif command -v python3 >/dev/null 2>&1; then
    PY=python3
else
    fail "no python on PATH; activate the project venv first"
fi
"${PY}" -c "import sys; print('python', sys.version.split()[0])"

if [ -f "repro/requirements.lock" ]; then
    note "freezing current environment against repro/requirements.lock (no install)..."
    "${PY}" - <<'PY'
import importlib.metadata as im
from pathlib import Path

missing = []
mismatched = []
for line in Path("repro/requirements.lock").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "==" not in line:
        continue
    name, want = line.split("==", 1)
    try:
        got = im.version(name)
    except im.PackageNotFoundError:
        missing.append(name)
        continue
    if got != want:
        mismatched.append((name, want, got))
if missing:
    print(f"missing packages ({len(missing)}): {missing[:10]}{' ...' if len(missing) > 10 else ''}")
if mismatched:
    print(f"version mismatches ({len(mismatched)}): {mismatched[:5]}{' ...' if len(mismatched) > 5 else ''}")
if not missing and not mismatched:
    print("lock file matches current environment")
PY
else
    note "no repro/requirements.lock found; skipping dependency check"
fi

# ---------------------------------------------------------------------------
# Step 4: leakage pytest (free; CPU only)
# ---------------------------------------------------------------------------

banner "running leakage tests"
note "this exercises every (instance, prompt variant) combination in the"
note "20-instance pilot; expected wall time on a warm repo cache is ~45-60 s."
if ! "${PY}" -m pytest -v tests/test_no_leakage.py; then
    fail "leakage tests failed -- repo is NOT safe to publish in current state"
fi

# ---------------------------------------------------------------------------
# Step 5: Round 1 baseline
# ---------------------------------------------------------------------------

banner "Round 1 baseline (cache-replay path)"
note "swe_review_bench.run does not currently support a fail-on-cache-miss"
note "flag, so we do not re-invoke the orchestrator here. The Round 1"
note "headline numbers are read straight from outputs/summary.csv and"
note "outputs/round2/h_lite/round1_with_ci.csv (frozen artefacts)."
"${PY}" - <<'PY'
import pandas as pd
from pathlib import Path

p = Path("outputs/round2/h_lite/round1_with_ci.csv")
if not p.exists():
    print(f"missing {p}; run h-lite Task 2 first")
    raise SystemExit(1)
df = pd.read_csv(p)
print()
print("Round 1 baseline (Wilson 95% CIs)")
for _, r in df.iterrows():
    print(
        f"  {r['reviewer']:>22}  "
        f"instance_hit_rate = {r['instance_hit_n']}/{r['instance_total_n']} "
        f"[{r['instance_hit_rate_ci_low']:.3f}, {r['instance_hit_rate_ci_high']:.3f}]    "
        f"file_level = {r['file_hit_instances_n']}/{r['file_total_instances_n']} "
        f"[{r['file_level_hit_rate_ci_low']:.3f}, {r['file_level_hit_rate_ci_high']:.3f}]"
    )
PY

# ---------------------------------------------------------------------------
# Step 6: Variant B reproduction
# ---------------------------------------------------------------------------

banner "Round 2 prompt-variant sweep (cache-replay path)"
note "Variant B and C cache lives under .cache/round2/llm/ and was"
note "produced by Milestone F.3. As with Round 1 we do not re-invoke the"
note "sweep here; we print the existing summary instead."
"${PY}" - <<'PY'
import pandas as pd
from pathlib import Path

p = Path("outputs/round2/h_lite/variant_summary_with_ci.csv")
if not p.exists():
    print(f"missing {p}; run h-lite Task 2 first")
    raise SystemExit(1)
df = pd.read_csv(p)
print()
print("Round 2 prompt-variant comparison (Wilson 95% CIs)")
for _, r in df.iterrows():
    print(
        f"  variant {r['prompt_variant']}  {r['reviewer']:>22}  "
        f"instance_hit_rate = {r['instance_hit_n']}/{r['instance_total_n']} "
        f"[{r['instance_hit_rate_ci_low']:.3f}, {r['instance_hit_rate_ci_high']:.3f}]"
    )
PY

# ---------------------------------------------------------------------------
# Step 7: done
# ---------------------------------------------------------------------------

banner "done"
printf "${green}reproduction complete; no paid API calls were issued.${nc}\n"
echo
echo "Reports:"
echo "  - docs/preliminary_results.md                       headline tables + figure"
echo "  - outputs/round2/h_lite/round1_with_ci.csv          Round 1 with CIs"
echo "  - outputs/round2/h_lite/variant_summary_with_ci.csv Round 2 variants with CIs"
echo "  - outputs/round2/h_lite/leakage_audit_report.md     last pytest leakage run"
echo "  - outputs/round2/MANIFEST.md                        per-file manifest"
