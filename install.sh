#!/usr/bin/env bash
# Install Chief Engineer without overwriting existing Codex configuration.
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./install.sh [--dry-run]

Installs the skill and optional custom agents into CODEX_HOME (default:
~/.codex). The installer refuses to overwrite existing targets.
USAGE
}

dry_run=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) dry_run=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown argument: %s\n' "$1" >&2; usage >&2; exit 64 ;;
  esac
done

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
if [[ -n "${CODEX_HOME:-}" ]]; then
  codex_home="$CODEX_HOME"
elif [[ -n "${HOME:-}" ]]; then
  codex_home="$HOME/.codex"
else
  printf 'Set CODEX_HOME because HOME is unavailable.\n' >&2
  exit 65
fi

skill_src="$repo_root/skill/chief-engineer"
agents_src="$repo_root/agents"

[[ -f "$skill_src/SKILL.md" ]] || { printf 'Skill source is missing.\n' >&2; exit 66; }
[[ -d "$agents_src" ]] || { printf 'Agent source is missing.\n' >&2; exit 66; }

skill_dst="$codex_home/skills/chief-engineer"
agents_dst="$codex_home/agents"
targets=("$skill_dst")
for source in "$agents_src"/*.toml; do
  [[ -f "$source" ]] || continue
  targets+=("$agents_dst/$(basename "$source")")
done
for target in "${targets[@]}"; do
  if [[ -e "$target" || -L "$target" ]]; then
    printf 'Refusing to overwrite existing target: %s\n' "$target" >&2
    exit 67
  fi
done

if [[ "$dry_run" == true ]]; then
  printf 'Would install skill to %s\n' "$skill_dst"
  printf 'Would install custom agents to %s\n' "$agents_dst"
  printf 'Would create an empty local repository allowlist after installation.\n'
  exit 0
fi

mkdir -p "$codex_home/skills" "$agents_dst"
codex_home=$(cd "$codex_home" && pwd -P)
skills_parent=$(cd "$codex_home/skills" && pwd -P)
agents_parent=$(cd "$codex_home/agents" && pwd -P)
case "$skills_parent" in "$codex_home"/*) ;; *) printf 'Refusing skills parent outside CODEX_HOME.\n' >&2; exit 68 ;; esac
case "$agents_parent" in "$codex_home"/*) ;; *) printf 'Refusing agents parent outside CODEX_HOME.\n' >&2; exit 68 ;; esac
skill_dst="$skills_parent/chief-engineer"
agents_dst="$agents_parent"
cp -R "$skill_src" "$skill_dst"
for source in "$agents_src"/*.toml; do
  [[ -f "$source" ]] || continue
  cp "$source" "$agents_dst/$(basename "$source")"
done
cp "$skill_dst/references/approved-repo-roots.example.txt" \
  "$skill_dst/references/approved-repo-roots.local.txt"
chmod +x "$skill_dst/scripts/ce-dispatch.sh" "$skill_dst/scripts/ce-token-report.py"

printf 'Installed Chief Engineer to %s\n' "$skill_dst"
printf 'Next: add approved Git roots to %s\n' \
  "$skill_dst/references/approved-repo-roots.local.txt"
