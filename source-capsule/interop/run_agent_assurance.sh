#!/usr/bin/env bash
set -u

root="$(cd "$(dirname "$0")/.." && pwd)"
run="${1:-/tmp/claim-commons-agent-assurance}"
inspect_cmd="${INSPECT_CMD:-inspect}"
promptfoo_cmd="${PROMPTFOO_CMD:-promptfoo}"

mkdir -p "$run/inspect" "$run/inspect-data" "$run/inspect-cache" "$run/promptfoo-config" "$run/normalized"

set +e
env XDG_DATA_HOME="$run/inspect-data" XDG_CACHE_HOME="$run/inspect-cache" \
  "$inspect_cmd" eval "$root/interop/agent_assurance_inspect.py" \
  --log-format=json --log-dir "$run/inspect" --display=none \
  >"$run/inspect.stdout" 2>"$run/inspect.stderr"
inspect_exit=$?

env PROMPTFOO_CONFIG_DIR="$run/promptfoo-config" \
  "$promptfoo_cmd" eval -c "$root/interop/agent_assurance_promptfoo.yaml" \
  -o "$run/promptfoo.jsonl" --no-cache \
  >"$run/promptfoo.stdout" 2>"$run/promptfoo.stderr"
promptfoo_exit=$?
set -e

printf '%s\n' "$inspect_exit" >"$run/inspect.exit"
printf '%s\n' "$promptfoo_exit" >"$run/promptfoo.exit"

python3 "$root/interop/normalize_agent_assurance_outputs.py" \
  --inspect-dir "$run/inspect" \
  --promptfoo "$run/promptfoo.jsonl" \
  --inspect-out "$run/normalized/inspect.json" \
  --promptfoo-out "$run/normalized/promptfoo.jsonl"

env PYTHONPATH="$root/src" python3 "$root/interop/build_agent_assurance_report.py" \
  --inspect-dir "$run/normalized" \
  --promptfoo "$run/normalized/promptfoo.jsonl" \
  --out "$run/report.json"

printf 'Inspect exit: %s\nPromptfoo exit: %s\nReport: %s\n' \
  "$inspect_exit" "$promptfoo_exit" "$run/report.json"
