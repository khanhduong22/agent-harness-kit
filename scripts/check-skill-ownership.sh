#!/usr/bin/env bash
# Enforce the ownership boundary: a skill lives in exactly one home — this kit,
# or a service repo — never both.
#
# Two homes for the same skill name means two copies that drift apart with
# nothing to reconcile them, because neither side's tooling can see the other.
# It has happened: six skills were duplicated across the kit and the index
# service repos, and all six had drifted, with the service copy the richer one.
#
# Which home is correct depends on blast radius, not on which copy is longer:
#   - portable across projects  -> the kit
#   - tied to one service's paths, containers, commands, or domain enums
#     -> that service's own <repo>/.agents/skills/
#
# Usage:
#   scripts/check-skill-ownership.sh [workspace-path ...]
#
# With no argument it reads AGENT_HARNESS_WORKSPACE, and skips (exit 0) when
# that is unset, so the kit's own checks stay green on a machine that has no
# workspace checked out.
set -euo pipefail

kit_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

workspaces=("$@")
if [[ ${#workspaces[@]} -eq 0 ]]; then
  if [[ -n "${AGENT_HARNESS_WORKSPACE:-}" ]]; then
    workspaces=("$AGENT_HARNESS_WORKSPACE")
  else
    printf 'skill ownership: no workspace given (pass a path or set AGENT_HARNESS_WORKSPACE); skipped\n'
    exit 0
  fi
fi

kit_skill_home() {
  local name="$1"
  [[ -f "$kit_root/skills/$name/SKILL.md" ]] && { printf '%s\n' "$kit_root/skills/$name/SKILL.md"; return 0; }
  local overlay
  for overlay in "$kit_root"/overlays/*/skills/"$name"/SKILL.md; do
    [[ -f "$overlay" ]] && { printf '%s\n' "$overlay"; return 0; }
  done
  return 1
}

line_count() { /usr/bin/wc -l < "$1" | /usr/bin/tr -d ' '; }

violations=0
checked=0
for workspace in "${workspaces[@]}"; do
  if [[ ! -d "$workspace" ]]; then
    printf 'skill ownership: workspace not found: %s\n' "$workspace" >&2
    exit 2
  fi
  # Two layers: each service repo's own skills, and a workspace-root
  # `.agents/skills` directory. The latter is not a deploy target of
  # install.sh, so anything left there is a hand-made copy that drifts
  # silently — it once held 40 of them, 3 stale and 4 duplicating a service.
  for repo_skill in "$workspace"/*/.agents/skills/*/SKILL.md \
                    "$workspace"/.agents/skills/*/SKILL.md; do
    [[ -f "$repo_skill" ]] || continue
    checked=$((checked + 1))
    skill_dir="$(dirname "$repo_skill")"
    name="$(basename "$skill_dir")"
    if kit_copy="$(kit_skill_home "$name")"; then
      violations=$((violations + 1))
      printf '\nVIOLATION: skill "%s" exists in two homes\n' "$name"
      printf '  kit  : %s (%s lines)\n' "$kit_copy" "$(line_count "$kit_copy")"
      printf '  repo : %s (%s lines)\n' "$repo_skill" "$(line_count "$repo_skill")"
      if /usr/bin/diff -q "$kit_copy" "$repo_skill" >/dev/null 2>&1; then
        printf '  status: identical today — still a violation, they will drift\n'
      else
        printf '  status: ALREADY DRIFTED\n'
      fi
    fi
  done
done

printf '\nskill ownership: checked %s service-repo skills across %s workspace(s)\n' \
  "$checked" "${#workspaces[@]}"

if [[ "$violations" -gt 0 ]]; then
  printf '%s skill(s) live in two homes. Decide one owner per skill and delete the other copy:\n' "$violations" >&2
  printf '  portable across projects        -> keep the kit copy\n' >&2
  printf '  tied to one service repo        -> keep the repo copy, delete it from the kit\n' >&2
  exit 1
fi

printf 'skill ownership: no duplicates\n'
