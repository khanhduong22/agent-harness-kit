#!/usr/bin/env bash
set -euo pipefail

kit_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
kit_home_root="${AGENT_HARNESS_HOME:-${HOME}}"
target_csv="all"
install_mode="symlink"
install_rules=false
rules_mode="merge"
force_conflicts=false
dry_run=false
install_index=false
project_path=""
rollback_target=""
backup_stamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_root="${AGENT_HARNESS_BACKUP_DIR:-${kit_home_root}/.agent-harness-backups}/${backup_stamp}"
receipt_file="${backup_root}/receipt.json"
receipt_initialized=false

usage() {
  /bin/cat <<'EOF'
Usage: ./scripts/install.sh [options]

Options:
  --targets all|codex,claude,gemini,antigravity
  --mode symlink|copy
  --rules       Merge the managed global-rule block
  --rules-mode merge|replace
                Preserve other rule content (merge) or back it up and replace it
  --index       Install the Index project pack
  --project-path <path>
                Target directory for project-level pack injection (default: $PWD)
  --rollback [latest|<timestamp>]
                Rollback a previous installation run using its receipt
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
    --rules-mode)
      rules_mode="${2:?--rules-mode requires a value}"
      shift 2
      ;;
    --index)
      install_index=true
      shift
      ;;
    --project-path)
      project_path="${2:?--project-path requires a value}"
      shift 2
      ;;
    --rollback)
      if [[ $# -ge 2 && "$2" != --* ]]; then
        rollback_target="$2"
        shift 2
      else
        rollback_target="latest"
        shift 1
      fi
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

if [[ -n "$rollback_target" ]]; then
  backup_base_dir="${AGENT_HARNESS_BACKUP_DIR:-${kit_home_root}/.agent-harness-backups}"
  rollback_args=(
    --backup-root "$backup_base_dir"
    --target "$rollback_target"
  )
  if [[ "$dry_run" == true ]]; then
    rollback_args+=(--dry-run)
  fi
  /usr/bin/env python3 "$kit_root/scripts/rollback.py" "${rollback_args[@]}"
  exit $?
fi

case "$install_mode" in
  symlink|copy) ;;
  *)
    printf 'Unsupported install mode: %s\n' "$install_mode" >&2
    exit 2
    ;;
esac

case "$rules_mode" in
  merge|replace) ;;
  *)
    printf 'Unsupported rules mode: %s\n' "$rules_mode" >&2
    exit 2
    ;;
esac

if [[ "$target_csv" == "all" ]]; then
  target_csv="codex,claude,gemini"
fi

if [[ "$install_index" == true ]]; then
  project_path="${project_path:-$PWD}"
  if [[ ! -d "$project_path" ]]; then
    printf 'Error: target project directory does not exist: %s\n' "$project_path" >&2
    exit 2
  fi
  project_path="$(cd "$project_path" && pwd)"
fi

init_receipt() {
  if [[ "$dry_run" == true || "$receipt_initialized" == true ]]; then
    return
  fi
  /bin/mkdir -p "$backup_root"
  /usr/bin/env python3 -c '
import json, sys, os
receipt_file, timestamp, cmd = sys.argv[1:4]
if not os.path.exists(receipt_file):
    data = {
        "timestamp": timestamp,
        "command": cmd,
        "actions": []
    }
    with open(receipt_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
' "$receipt_file" "$backup_stamp" "$0 $*"
  
  local backup_base_dir="$(dirname "$backup_root")"
  /bin/ln -sfn "$backup_root" "$backup_base_dir/latest"
  receipt_initialized=true
}

record_receipt_action() {
  local action_type="$1"
  local destination="$2"
  local existed="$3"
  local backup_path="${4:-}"
  if [[ "$dry_run" == true ]]; then
    return
  fi
  /usr/bin/env python3 -c '
import json, sys
receipt_file, action_type, destination, existed, backup_path = sys.argv[1:6]
try:
    with open(receipt_file, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    data = {"actions": []}
data.setdefault("actions", []).append({
    "type": action_type,
    "destination": destination,
    "existed": existed == "true",
    "backup_path": backup_path if backup_path else None
})
with open(receipt_file, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
' "$receipt_file" "$action_type" "$destination" "$existed" "$backup_path"
}

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
  local skill_name destination_skill backup_skill current_target existed
  skill_name="${source_skill##*/}"
  destination_skill="${destination_root}/${skill_name}"
  existed=false

  if [[ -L "$destination_skill" ]]; then
    current_target="$(readlink "$destination_skill")"
    if [[ "$install_mode" == "symlink" && "$current_target" == "$source_skill" ]]; then
      printf 'unchanged: %s\n' "$destination_skill"
      return
    fi
  elif [[ ! -e "$destination_skill" ]]; then
    current_target=""
  fi

  backup_skill=""
  if [[ -e "$destination_skill" || -L "$destination_skill" ]]; then
    existed=true
    if [[ "$force_conflicts" != true ]]; then
      printf 'skipped conflict: %s (use --force to back up and replace)\n' "$destination_skill" >&2
      return
    fi
    backup_skill="${backup_root}/${label}/${skill_name}"
    if [[ "$dry_run" == true ]]; then
      printf 'would back up: %s -> %s\n' "$destination_skill" "$backup_skill"
    else
      init_receipt
      /bin/mkdir -p "$(dirname "$backup_skill")"
      /bin/mv "$destination_skill" "$backup_skill"
      printf 'backed up: %s -> %s\n' "$destination_skill" "$backup_skill"
    fi
  fi

  if [[ "$dry_run" == true ]]; then
    printf 'would install (%s): %s -> %s\n' "$install_mode" "$source_skill" "$destination_skill"
    return
  fi

  init_receipt
  /bin/mkdir -p "$destination_root"
  if [[ "$install_mode" == "symlink" ]]; then
    /bin/ln -s "$source_skill" "$destination_skill"
  else
    /bin/cp -R "$source_skill" "$destination_skill"
  fi
  printf 'installed (%s): %s\n' "$install_mode" "$destination_skill"
  record_receipt_action "symlink" "$destination_skill" "$existed" "$backup_skill"
}

# Remove destination entries this kit installed whose source skill no longer
# exists. Without this, deleting a skill from the kit leaves the deployed link
# behind on every machine that already installed it, and the stale skill keeps
# applying — silently, because nothing reports it.
#
# Only dangling symlinks pointing into this kit are pruned. A real directory is
# never touched: under `--mode copy` a removed skill is indistinguishable from
# one the operator wrote by hand, so copies are left for manual cleanup.
prune_orphan_skills() {
  local destination_root="$1"
  local entry target
  [[ -d "$destination_root" ]] || return 0
  for entry in "$destination_root"/*; do
    [[ -L "$entry" ]] || continue
    target="$(readlink "$entry")"
    case "$target" in
      "$kit_root"/skills/*|"$kit_root"/overlays/*) ;;
      *) continue ;;
    esac
    [[ -e "$target" ]] && continue
    if [[ "$dry_run" == true ]]; then
      printf 'would prune orphan: %s -> %s\n' "$entry" "$target"
    else
      /bin/rm -f "$entry"
      printf 'pruned orphan: %s (source no longer in kit)\n' "$entry"
    fi
  done
}

install_target() {
  local target="$1"
  local destination_root adapter destination_rule source_skill overlay_skill
  if ! destination_root="$(skill_destination "$target")"; then
    printf 'Unsupported target: %s\n' "$target" >&2
    exit 2
  fi
  adapter="$(adapter_name "$target")"

  # Core installation does not run skills install if only --index without skills requested,
  # but standard install installs portable common skills
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

  prune_orphan_skills "$destination_root"

  if [[ "$install_rules" == true ]]; then
    init_receipt
    destination_rule="$(rule_destination "$target")"
    rule_args=(
      --core "$kit_root/rules/core.md"
      --adapter "$kit_root/rules/adapters/${adapter}.md"
      --destination "$destination_rule"
      --backup-dir "$backup_root"
      --label "$adapter"
      --marker "agent-harness-kit"
      --receipt-file "$receipt_file"
    )
    if [[ "$dry_run" == true ]]; then
      rule_args+=(--dry-run)
    fi
    if [[ "$rules_mode" == "replace" ]]; then
      rule_args+=(--replace)
    fi
    /usr/bin/env python3 "$kit_root/scripts/sync_rules.py" "${rule_args[@]}"
  fi

  if [[ "$install_index" == true ]]; then
    install_project_index "$target" "$project_path"
  fi
}

install_project_index() {
  local target="$1"
  local project_dir="$2"
  local adapter proj_dest_rule
  adapter="$(adapter_name "$target")"

  case "$adapter" in
    claude)
      if [[ -f "${project_dir}/.claude/CLAUDE.md" ]]; then
        proj_dest_rule="${project_dir}/.claude/CLAUDE.md"
      elif [[ -f "${project_dir}/CLAUDE.md" ]]; then
        proj_dest_rule="${project_dir}/CLAUDE.md"
      else
        proj_dest_rule="${project_dir}/.claude/CLAUDE.md"
      fi
      ;;
    # Codex reads AGENTS.md at the repository root and walks down to the working
    # directory. `.codex/` is the *global* home only (CODEX_HOME) — Codex never
    # reads a `.codex/AGENTS.md` inside a project, so writing there produced a
    # file no tool loads while the real one went stale.
    #
    # Antigravity loads ~/.gemini/GEMINI.md, then ./GEMINI.md, then ./AGENTS.md,
    # then ./.agents/rules/*.md — so it reads the same root AGENTS.md. Writing a
    # project GEMINI.md as well would inject this pack into Antigravity twice,
    # so both adapters deliberately share the one cross-tool file. The write is
    # marker-scoped and idempotent, so the second adapter reports "unchanged".
    codex|gemini)
      proj_dest_rule="${project_dir}/AGENTS.md"
      ;;
    *) return 1 ;;
  esac

  # sync_rules.py writes its own receipt entries, but only init_receipt creates
  # the `latest` symlink that `--rollback latest` resolves. Without this call an
  # index install onto an already-provisioned home (nothing left for the skill
  # or rule paths to record) leaves a stamped receipt no rollback can find.
  init_receipt

  rule_args=(
    --content "$kit_root/profiles/index/workspace.md"
    --destination "$proj_dest_rule"
    --backup-dir "$backup_root"
    --label "${adapter}-index"
    --marker "agent-harness-kit:index"
    --receipt-file "$receipt_file"
  )
  if [[ "$dry_run" == true ]]; then
    rule_args+=(--dry-run)
  fi
  /usr/bin/env python3 "$kit_root/scripts/sync_rules.py" "${rule_args[@]}"

  mcp_args=(
    --mcp
    --profile "$kit_root/profiles/index/api.md,$kit_root/profiles/index/cms.md"
    --project-path "$project_dir"
    --target "$adapter"
    --backup-dir "$backup_root"
    --label "${adapter}-index-mcp"
    --receipt-file "$receipt_file"
    --install-mode "$install_mode"
  )
  if [[ "$dry_run" == true ]]; then
    mcp_args+=(--dry-run)
  fi
  /usr/bin/env python3 "$kit_root/scripts/sync_rules.py" "${mcp_args[@]}"

  install_hooks "$adapter" "$project_dir"
}

# Where the hook scripts land. One copy, shared by every host, so a fix to a
# hook is a fix everywhere — the same reason skills have a single home.
hooks_destination() {
  printf '%s\n' "${kit_home_root}/.agent-harness/hooks"
}

# Which file the host reads its hooks from. Claude Code takes project-scoped
# hooks from the project's settings.json; Codex reads ~/.codex/hooks.json.
# Gemini/Antigravity has its own schema and is not written here.
hook_config_destination() {
  local adapter="$1" project_dir="$2"
  case "$adapter" in
    claude) printf '%s\n' "${project_dir}/.claude/settings.json" ;;
    codex) printf '%s\n' "${CODEX_HOME:-${kit_home_root}/.codex}/hooks.json" ;;
    *) return 1 ;;
  esac
}

install_hooks() {
  local adapter="$1" project_dir="$2"
  local hooks_dir destination hook_args

  if ! destination="$(hook_config_destination "$adapter" "$project_dir")"; then
    printf 'hooks unsupported target: %s (no config written)\n' "$adapter"
    return 0
  fi

  hooks_dir="$(hooks_destination)"

  if [[ "$dry_run" == true ]]; then
    printf 'would install hook scripts: %s\n' "$hooks_dir"
  else
    init_receipt
    /bin/mkdir -p "$hooks_dir"
    local hook_script hook_dest hook_existed hook_backup
    for hook_script in "$kit_root"/scripts/hooks/*.sh; do
      hook_dest="${hooks_dir}/$(basename "$hook_script")"
      hook_existed=false
      hook_backup=""
      if [[ -f "$hook_dest" ]]; then
        hook_existed=true
        hook_backup="${backup_root}/${adapter}-hooks-scripts/$(basename "$hook_script")"
        /bin/mkdir -p "$(dirname "$hook_backup")"
        /bin/cp "$hook_dest" "$hook_backup"
      fi
      /bin/cp "$hook_script" "$hook_dest"
      /bin/chmod +x "$hook_dest"
      record_receipt_action "file" "$hook_dest" "$hook_existed" "$hook_backup"
    done
    printf 'installed hook scripts: %s\n' "$hooks_dir"
  fi

  hook_args=(
    --hooks
    --hooks-profile "$kit_root/profiles/index/hooks.json"
    --hooks-dir "$hooks_dir"
    --destination "$destination"
    --backup-dir "$backup_root"
    --label "${adapter}-hooks"
    --receipt-file "$receipt_file"
  )
  if [[ "$dry_run" == true ]]; then
    hook_args+=(--dry-run)
  fi
  /usr/bin/env python3 "$kit_root/scripts/sync_rules.py" "${hook_args[@]}"
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
