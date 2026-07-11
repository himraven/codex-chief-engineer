#!/usr/bin/env bash
# Model-pinned, transcript-isolated chief-engineer worker launcher.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ce-dispatch.sh --role <scout|mechanic|worker|senior|reviewer> \
  --cwd <git-repository> --brief <brief.md> --result-dir <directory> \
  [--approval-file <approval.md>] [--fallback]

The launcher refuses Sol workers, broad or unapproved working directories, and
oversized briefs. It runs an isolated `codex exec --ephemeral` process with a
pinned model, reasoning effort, and sandbox.
USAGE
}

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    printf 'Missing SHA-256 utility: install shasum or sha256sum.\n' >&2
    return 1
  fi
}

role=""
cwd=""
brief=""
result_dir=""
approval_file=""
fallback=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --role) role="${2:-}"; shift 2 ;;
    --cwd) cwd="${2:-}"; shift 2 ;;
    --brief) brief="${2:-}"; shift 2 ;;
    --result-dir) result_dir="${2:-}"; shift 2 ;;
    --approval-file) approval_file="${2:-}"; shift 2 ;;
    --fallback) fallback=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 64 ;;
  esac
done

if [[ -z "$role" || -z "$cwd" || -z "$brief" || -z "$result_dir" ]]; then
  usage >&2
  exit 64
fi

case "$role" in
  scout)
    model="gpt-5.6-luna"; effort="low"; sandbox="read-only"; tool_budget=15; final_budget_bytes=12000
    ;;
  mechanic)
    model="gpt-5.6-luna"; effort="low"; sandbox="workspace-write"; tool_budget=20; final_budget_bytes=16000
    ;;
  worker)
    model="gpt-5.6-terra"; effort="medium"; sandbox="workspace-write"; tool_budget=25; final_budget_bytes=24000
    ;;
  senior)
    model="gpt-5.6-terra"; effort="high"; sandbox="workspace-write"; tool_budget=35; final_budget_bytes=30000
    ;;
  reviewer)
    model="gpt-5.6-terra"; effort="high"; sandbox="read-only"; tool_budget=25; final_budget_bytes=24000
    ;;
  sol|chief|*)
    printf 'Refusing worker role %q. Sol is chief-only; use a non-Sol worker role.\n' "$role" >&2
    exit 65
    ;;
esac

if [[ "$fallback" == true ]]; then
  case "$role" in
    scout|mechanic) model="gpt-5.4-mini" ;;
    worker|senior|reviewer) model="gpt-5.4" ;;
  esac
fi

[[ -f "$brief" ]] || { printf 'Brief does not exist: %s\n' "$brief" >&2; exit 66; }
brief_bytes=$(wc -c < "$brief" | tr -d '[:space:]')
max_brief_bytes="${CE_MAX_BRIEF_BYTES:-48000}"
if (( brief_bytes > max_brief_bytes )); then
  printf 'Brief is %s bytes; ceiling is %s. Reslice it or record an explicit exception.\n' \
    "$brief_bytes" "$max_brief_bytes" >&2
  exit 67
fi
brief_sha=$(sha256_file "$brief")

approval_sha=""
approved_by=""
if [[ "$sandbox" == "workspace-write" ]]; then
  if [[ -z "$approval_file" || ! -f "$approval_file" ]]; then
    printf 'Write roles require --approval-file with a matching approval record.\n' >&2
    exit 71
  fi
  approval_file=$(cd "$(dirname "$approval_file")" && pwd -P)/$(basename "$approval_file")
  approval_state=$(awk -F ': *' '$1 == "approval" {print tolower($2); exit}' "$approval_file")
  approval_brief_sha=$(awk -F ': *' '$1 == "brief_sha256" {print $2; exit}' "$approval_file")
  approved_by=$(awk -F ': *' '$1 == "approved_by" {print $2; exit}' "$approval_file")
  if [[ "$approval_state" != "approved" || "$approval_brief_sha" != "$brief_sha" || -z "$approved_by" ]]; then
    printf 'Approval record must declare approval: approved, a matching brief_sha256, and approved_by.\n' >&2
    exit 71
  fi
  approval_sha=$(sha256_file "$approval_file")
fi

[[ -d "$cwd" ]] || { printf 'Working directory does not exist: %s\n' "$cwd" >&2; exit 68; }
cwd=$(cd "$cwd" && pwd -P)
repo_root=$(git -C "$cwd" rev-parse --show-toplevel 2>/dev/null) || {
  printf 'Workers must run in a narrow Git repository: %s\n' "$cwd" >&2
  exit 69
}
repo_root=$(cd "$repo_root" && pwd -P)
script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
approved_roots_file="${CE_APPROVED_REPO_ROOTS:-$script_dir/../references/approved-repo-roots.local.txt}"
if [[ ! -f "$approved_roots_file" ]]; then
  printf 'Local repository-root policy is missing: %s\n' "$approved_roots_file" >&2
  printf 'Copy approved-repo-roots.example.txt, add one narrow Git root, and retry.\n' >&2
  exit 70
fi

approved_root=false
while IFS= read -r allowed_root || [[ -n "$allowed_root" ]]; do
  [[ -z "$allowed_root" || "$allowed_root" == \#* ]] && continue
  allowed_root=$(cd "$allowed_root" 2>/dev/null && pwd -P) || continue
  if [[ "$repo_root" == "$allowed_root" || "$repo_root" == "$allowed_root/.worktrees/"* ]]; then
    approved_root=true
    break
  fi
done < "$approved_roots_file"
if [[ "$approved_root" != true ]]; then
  printf 'Refusing unapproved repository root: %s\n' "$repo_root" >&2
  exit 70
fi

write_lock_dir=""
if [[ "$sandbox" == "workspace-write" ]]; then
  if [[ ! -f "$repo_root/.git" || "$repo_root" != "$allowed_root/.worktrees/"* ]]; then
    printf 'Write roles require a dedicated linked worktree under %s/.worktrees/.\n' "$allowed_root" >&2
    exit 72
  fi
  git_dir=$(git -C "$repo_root" rev-parse --git-dir)
  if [[ "$git_dir" != /* ]]; then
    git_dir="$repo_root/$git_dir"
  fi
  git_dir=$(cd "$git_dir" && pwd -P)
  write_lock_dir="$git_dir/chief-engineer-write.lock"
  if ! mkdir "$write_lock_dir" 2>/dev/null; then
    printf 'Write worktree is busy: %s\n' "$repo_root" >&2
    exit 72
  fi
  cleanup_write_lock() { rmdir "$write_lock_dir" 2>/dev/null || true; }
  trap cleanup_write_lock EXIT
fi

if [[ -n "${CODEX_HOME:-}" ]]; then
  codex_home="$CODEX_HOME"
elif [[ -n "${HOME:-}" ]]; then
  codex_home="$HOME/.codex"
else
  printf 'Set CODEX_HOME because HOME is unavailable.\n' >&2
  exit 71
fi

mkdir -p "$result_dir"
result_dir=$(cd "$result_dir" && pwd -P)
stamp=$(date -u +%Y%m%dT%H%M%SZ)
if command -v uuidgen >/dev/null 2>&1; then
  suffix=$(uuidgen)
else
  suffix=$(python3 -c 'import uuid; print(uuid.uuid4())')
fi
run_id="${stamp}-${role}-${suffix}"
events="$result_dir/${run_id}.events.jsonl"
final="$result_dir/${run_id}.final.md"
manifest="$result_dir/${run_id}.manifest.json"
run_home="${CE_RUN_HOME:-$codex_home/chief-engineer-runs}"
index_dir="$run_home/$(date +%F)"
index_manifest="$index_dir/${run_id}.manifest.json"
mkdir -p "$index_dir"

start_epoch=$(date +%s)
set +e
{
  printf '%s\n' "You are the ${role} executor in a chief-engineer workflow."
  printf '%s\n' ''
  printf '%s\n' 'Obey the standalone brief exactly. Do not delegate or expand scope.'
  printf '%s\n' "You have a tool budget of ${tool_budget}; if evidence is insufficient at the"
  printf '%s\n' 'limit, stop and report the smallest remaining uncertainty.'
  printf '%s\n' "Return only the brief's requested structured result."
  printf '%s\n' ''
  printf '%s\n' '--- BEGIN STANDALONE BRIEF ---'
  cat "$brief"
  printf '%s\n' '--- END STANDALONE BRIEF ---'
} | codex -a never exec --ephemeral --json \
  -C "$cwd" \
  -m "$model" \
  -c "model_reasoning_effort=\"$effort\"" \
  -s "$sandbox" \
  -o "$final" \
  - > "$events"
status=$?
set -e
end_epoch=$(date +%s)

observed_model=$(jq -r '[.model?, .payload.model?, .payload.thread_settings.model?] | .[]? | select(type == "string" and length > 0)' "$events" 2>/dev/null | head -1 || true)
if [[ -z "${observed_model:-}" ]]; then
  observed_model=null
  model_provenance="CLI model pin; JSONL did not expose an observed model field"
else
  observed_model=$(printf '%s' "$observed_model" | jq -R .)
  model_provenance="CLI model pin plus JSONL model field"
fi

usage=$(jq -s '[.[] | select(.type == "turn.completed") | (.usage // {})] | last // {}' "$events" 2>/dev/null || printf '{}')
tool_calls=$(jq -s '[.[] | select(.type == "item.started" and .item.type == "command_execution")] | length' "$events" 2>/dev/null || printf '0')
final_bytes=0
if [[ -f "$final" ]]; then
  final_bytes=$(wc -c < "$final" | tr -d '[:space:]')
fi
budget_state="within_budget"
gate_status=$status
if (( tool_calls > tool_budget )); then
  budget_state="tool_budget_exceeded"
  gate_status=72
elif (( final_bytes > final_budget_bytes )); then
  budget_state="final_output_byte_ceiling_exceeded"
  gate_status=73
fi

jq -n \
  --arg run_id "$run_id" --arg role "$role" --arg requested_model "$model" \
  --arg routing_mode "$([[ "$fallback" == true ]] && printf fallback || printf primary)" \
  --arg effort "$effort" --arg sandbox "$sandbox" --arg cwd "$cwd" \
  --arg repo_root "$repo_root" --arg brief "$brief" --arg brief_sha256 "$brief_sha" \
  --arg events "$events" --arg final "$final" --arg index_manifest "$index_manifest" \
  --arg approval_file "$approval_file" --arg approval_sha256 "$approval_sha" --arg approved_by "$approved_by" \
  --arg model_provenance "$model_provenance" --argjson observed_model "$observed_model" \
  --argjson usage "$usage" --argjson status "$status" --argjson gate_status "$gate_status" \
  --argjson started_at "$start_epoch" --argjson finished_at "$end_epoch" \
  --argjson tool_budget "$tool_budget" --argjson actual_tool_calls "$tool_calls" \
  --argjson final_budget_bytes "$final_budget_bytes" --argjson final_bytes "$final_bytes" \
  --arg budget_state "$budget_state" \
  '{run_id: $run_id, role: $role, requested_model: $requested_model, routing_mode: $routing_mode, observed_model: $observed_model, reasoning_effort: $effort, sandbox: $sandbox, cwd: $cwd, repo_root: $repo_root, brief: $brief, brief_sha256: $brief_sha256, approval_file: $approval_file, approval_sha256: $approval_sha256, approved_by: $approved_by, event_log: $events, final_message: $final, index_manifest: $index_manifest, model_provenance: $model_provenance, usage: $usage, codex_exit_status: $status, exit_status: $gate_status, started_at_epoch: $started_at, finished_at_epoch: $finished_at, tool_budget: $tool_budget, actual_tool_calls: $actual_tool_calls, final_output_budget_bytes: $final_budget_bytes, final_output_bytes: $final_bytes, budget_state: $budget_state}' > "$manifest"
cp -p "$manifest" "$index_manifest"

printf 'run_id=%s\nmanifest=%s\nindex_manifest=%s\nfinal=%s\nevents=%s\nrequested_model=%s\nobserved_model=%s\ncodex_exit_status=%s\nbudget_state=%s\nexit_status=%s\n' \
  "$run_id" "$manifest" "$index_manifest" "$final" "$events" "$model" "${observed_model}" "$status" "$budget_state" "$gate_status"
exit "$gate_status"
