#!/usr/bin/env bash
# macOS/Linux: link a repository skill into user-level client discovery paths.
set -euo pipefail
task_script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
task_user_root="${HOME:?HOME is required}"
if [[ "${1:-}" == "--user-root" ]]; then
  [[ $# -ge 2 ]] || { echo "Missing --user-root value" >&2; exit 1; }
  task_user_root="$2"
  shift 2
fi
if [[ $# -eq 0 ]]; then
  set -- "$task_script_dir/../onsite-audit-https"
fi
for task_skill_path in "$@"; do
  task_source="$(cd -- "$task_skill_path" && pwd -P)"
  [[ -f "$task_source/SKILL.md" ]] || { echo "Missing SKILL.md: $task_source" >&2; exit 1; }
  task_name="${task_source##*/}"
  [[ "$task_name" =~ ^[a-z0-9][a-z0-9-]{0,63}$ ]] || { echo "Invalid skill folder: $task_name" >&2; exit 1; }
  for task_root in "$task_user_root/.agents/skills" "$task_user_root/.claude/skills"; do
    mkdir -p -- "$task_root"
    task_destination="$task_root/$task_name"
    if [[ -L "$task_destination" ]] && [[ "$(readlink "$task_destination")" == "$task_source" ]]; then
      echo "Already linked: $task_destination"
    elif [[ -e "$task_destination" || -L "$task_destination" ]]; then
      echo "Existing skill preserved: $task_destination. Resolve the conflict manually." >&2
      exit 1
    else
      ln -s -- "$task_source" "$task_destination"
      cmp -s "$task_source/SKILL.md" "$task_destination/SKILL.md"
      echo "Linked: $task_destination"
    fi
  done
done
