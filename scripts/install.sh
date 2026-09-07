#!/usr/bin/env bash
set -euo pipefail

kit_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
kit_home_root="${AGENT_HARNESS_HOME:-${HOME}}"
target_csv="all"
install_mode="symlink"
install_rules=false
force_conflicts=false
dry_run=false
backup_stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_root="${AGENT_HARNESS_BACKUP_DIR:-${kit_home_root}/.agent-harness-backups}/${backup_stamp}"

usage() {
  /bin/cat <<'EOF'
Usage: ./scripts/install.sh [options]

Options:
  --targets all|codex,claude,gemini,antigravity
  --mode symlink|copy
  --rules       Merge the managed global-rule block
  --force       Back up and replace conflicting skill entries
  --dry-run     Print changes without writing
  -h, --help
EOF
}

while (($#)); do
  case "$1" in
    --targets)
      target_csv="${2:?--targets requires a value}"
      shift 2
      ;;
    --mode)
      install_mode="${2:?--mode requires a value}"
      shift 2
      ;;
    --rules)
      install_rules=true
      shift
      ;;
    --force)
      force_conflicts=true
      shift
      ;;
    --dry-run)
      dry_run=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf 'Unknown option: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "$install_mode" in
  symlink|copy) ;;
  *)
    printf 'Unsupported install mode: %s\n' "$install_mode" >&2
    exit 2
    ;;
esac

if [[ "$target_csv" == "all" ]]; then
  target_csv="codex,claude,gemini"
fi

skill_destination() {
  case "$1" in
    codex|agents) printf '%s\n' "${kit_home_root}/.agents/skills" ;;
    claude) printf '%s\n' "${CLAUDE_CONFIG_DIR:-${kit_home_root}/.claude}/skills" ;;
    gemini|antigravity) printf '%s\n' "${kit_home_root}/.gemini/config/skills" ;;
    *) return 1 ;;
  esac
}

rule_destination() {
  case "$1" in
    codex|agents) printf '%s\n' "${CODEX_HOME:-${kit_home_root}/.codex}/AGENTS.md" ;;
    claude) printf '%s\n' "${CLAUDE_CONFIG_DIR:-${kit_home_root}/.claude}/CLAUDE.md" ;;
    gemini|antigravity) printf '%s\n' "${kit_home_root}/.gemini/GEMINI.md" ;;
    *) return 1 ;;
  esac
}

adapter_name() {
  case "$1" in
    agents) printf 'codex\n' ;;
    antigravity) printf 'gemini\n' ;;
    *) printf '%s\n' "$1" ;;
  esac
}

install_one_skill() {
  local source_skill="$1"
  local destination_root="$2"
  local label="$3"
  local skill_name destination_skill backup_skill current_target
  skill_name="${source_skill##*/}"
  destination_skill="${destination_root}/${skill_name}"

  if [[ -L "$destination_skill" ]]; then
    current_target="$(readlink "$destination_skill")"
    if [[ "$install_mode" == "symlink" && "$current_target" == "$source_skill" ]]; then
      printf 'unchanged: %s\n' "$destination_skill"
      return
    fi
  elif [[ ! -e "$destination_skill" ]]; then
    current_target=""
  fi

  if [[ -e "$destination_skill" || -L "$destination_skill" ]]; then
    if [[ "$force_conflicts" != true ]]; then
      printf 'skipped conflict: %s (use --force to back up and replace)\n' "$destination_skill" >&2
      return
    fi
    backup_skill="${backup_root}/${label}/${skill_name}"
    if [[ "$dry_run" == true ]]; then
      printf 'would back up: %s -> %s\n' "$destination_skill" "$backup_skill"
    else
      /bin/mkdir -p "$(dirname "$backup_skill")"
      /bin/mv "$destination_skill" "$backup_skill"
      printf 'backed up: %s -> %s\n' "$destination_skill" "$backup_skill"
    fi
  fi

  if [[ "$dry_run" == true ]]; then
    printf 'would install (%s): %s -> %s\n' "$install_mode" "$source_skill" "$destination_skill"
    return
  fi

  /bin/mkdir -p "$destination_root"
  if [[ "$install_mode" == "symlink" ]]; then
    /bin/ln -s "$source_skill" "$destination_skill"
  else
    /bin/cp -R "$source_skill" "$destination_skill"
  fi
  printf 'installed (%s): %s\n' "$install_mode" "$destination_skill"
}

install_target() {
  local target="$1"
  local destination_root adapter destination_rule source_skill overlay_skill
  if ! destination_root="$(skill_destination "$target")"; then
    printf 'Unsupported target: %s\n' "$target" >&2
    exit 2
  fi
  adapter="$(adapter_name "$target")"

  for source_skill in "$kit_root"/skills/*; do
    [[ -d "$source_skill" && -f "$source_skill/SKILL.md" ]] || continue
    install_one_skill "$source_skill" "$destination_root" "$adapter"
  done

  if [[ -d "$kit_root/overlays/${adapter}/skills" ]]; then
    for overlay_skill in "$kit_root"/overlays/"${adapter}"/skills/*; do
      [[ -d "$overlay_skill" && -f "$overlay_skill/SKILL.md" ]] || continue
      install_one_skill "$overlay_skill" "$destination_root" "${adapter}-overlay"
    done
  fi

  if [[ "$install_rules" == true ]]; then
    destination_rule="$(rule_destination "$target")"
    rule_args=(
      --core "$kit_root/rules/core.md"
      --adapter "$kit_root/rules/adapters/${adapter}.md"
      --destination "$destination_rule"
      --backup-dir "$backup_root"
      --label "$adapter"
    )
    if [[ "$dry_run" == true ]]; then
      rule_args+=(--dry-run)
    fi
    /usr/bin/env python3 "$kit_root/scripts/sync_rules.py" "${rule_args[@]}"
  fi
}

seen_adapters="," 
IFS=',' read -r -a requested_targets <<< "$target_csv"
for requested_target in "${requested_targets[@]}"; do
  requested_target="${requested_target//[[:space:]]/}"
  [[ -n "$requested_target" ]] || continue
  normalized_adapter="$(adapter_name "$requested_target")"
  if [[ "$seen_adapters" == *",${normalized_adapter},"* ]]; then
    continue
  fi
  seen_adapters+="${normalized_adapter},"
  install_target "$requested_target"
done
