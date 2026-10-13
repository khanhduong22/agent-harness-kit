#!/usr/bin/env bash
# promote-skill.sh: Validate and promote a draft skill from skills/drafts/ into skills/
# Part of the Closed Learning Loop (self-improving-distiller).
set -euo pipefail

kit_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  printf 'Usage: %s [--validate-only] [--force] <skill-name>\n' "$(basename "$0")" >&2
  printf 'Options:\n' >&2
  printf '  --validate-only   Only run validation checks on the draft skill without promoting\n' >&2
  printf '  --force           Overwrite existing skill in skills/<skill-name> if it already exists\n' >&2
  exit 1
}

validate_only=false
force=false
skill_name=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --validate-only)
      validate_only=true
      shift
      ;;
    --force)
      force=true
      shift
      ;;
    -h|--help)
      usage
      ;;
    *)
      if [[ -z "$skill_name" ]]; then
        skill_name="$1"
      else
        printf 'Error: unexpected argument: %s\n' "$1" >&2
        usage
      fi
      shift
      ;;
  esac
done

if [[ -z "$skill_name" ]]; then
  printf 'Error: missing required <skill-name>\n' >&2
  usage
fi

# 1. Validate name format (kebab-case)
if ! printf '%s' "$skill_name" | grep -qE '^[a-z0-9]+(-[a-z0-9]+)*$'; then
  printf 'Error: skill name "%s" is invalid. Must be lowercase kebab-case (e.g. "my-useful-skill").\n' "$skill_name" >&2
  exit 1
fi

draft_dir="$kit_root/skills/drafts/$skill_name"
target_dir="$kit_root/skills/$skill_name"
skill_file="$draft_dir/SKILL.md"

# 2. Check draft existence
if [[ ! -d "$draft_dir" ]]; then
  printf 'Error: draft skill directory not found: %s\n' "$draft_dir" >&2
  exit 1
fi

if [[ ! -f "$skill_file" ]]; then
  printf 'Error: draft skill is missing SKILL.md: %s\n' "$skill_file" >&2
  exit 1
fi

# 3. Validate frontmatter in SKILL.md
if ! head -n 1 "$skill_file" | grep -q '^---$'; then
  printf 'Error: %s is missing opening "---" YAML frontmatter delimiter.\n' "$skill_file" >&2
  exit 1
fi

# Check closing frontmatter
if ! tail -n +2 "$skill_file" | grep -q '^---$'; then
  printf 'Error: %s is missing closing "---" YAML frontmatter delimiter.\n' "$skill_file" >&2
  exit 1
fi

# Extract name and description from frontmatter
frontmatter_name=$(sed -n '2,/^---$/p' "$skill_file" | grep -E '^name:[[:space:]]*' | head -n 1 | sed -E 's/^name:[[:space:]]*//' | tr -d '\r"' | sed -E 's/^[[:space:]]*//; s/[[:space:]]*$//' || true)
frontmatter_desc=$(sed -n '2,/^---$/p' "$skill_file" | grep -E '^description:[[:space:]]*' | head -n 1 | sed -E 's/^description:[[:space:]]*//' | tr -d '\r"' | sed -E 's/^[[:space:]]*//; s/[[:space:]]*$//' || true)

if [[ -z "$frontmatter_name" ]]; then
  printf 'Error: %s frontmatter missing "name:" field.\n' "$skill_file" >&2
  exit 1
fi

if [[ "$frontmatter_name" != "$skill_name" ]]; then
  printf 'Error: frontmatter name "%s" does not match directory name "%s".\n' "$frontmatter_name" "$skill_name" >&2
  exit 1
fi

if [[ -z "$frontmatter_desc" ]]; then
  printf 'Error: %s frontmatter missing "description:" field.\n' "$skill_file" >&2
  exit 1
fi

# 4. Check for machine-specific absolute home paths
if grep -rE '/(Users|home)/[^/]+/' "$draft_dir" >/dev/null 2>&1; then
  printf 'Error: draft skill contains machine-specific absolute home paths matching /(Users|home)/:\n' >&2
  grep -rnE '/(Users|home)/[^/]+/' "$draft_dir" >&2 || true
  exit 1
fi

# 5. Check target collision
if [[ -d "$target_dir" && "$force" != true ]]; then
  printf 'Error: target skill directory already exists: %s\n' "$target_dir" >&2
  printf 'Use --force to overwrite an existing production skill.\n' >&2
  exit 1
fi

if [[ "$validate_only" == true ]]; then
  printf '✓ Draft skill "%s" passed all validation checks.\n' "$skill_name"
  exit 0
fi

# 6. Perform promotion
printf 'Promoting draft skill "%s" into production skills/...\n' "$skill_name"

backup_target=""
if [[ -d "$target_dir" ]]; then
  backup_target=$(mktemp -d "${TMPDIR:-/tmp}/promote-backup.XXXXXX")
  cp -r "$target_dir" "$backup_target/$skill_name"
  rm -rf "$target_dir"
fi

cp -r "$draft_dir" "$target_dir"

# 7. Run kit verification to ensure integrity
printf 'Running verification suite...\n'
if ! "$kit_root/scripts/verify.sh"; then
  printf 'Error: verify.sh failed after promotion! Rolling back changes...\n' >&2
  rm -rf "$target_dir"
  if [[ -n "$backup_target" && -d "$backup_target/$skill_name" ]]; then
    mv "$backup_target/$skill_name" "$target_dir"
    rm -rf "$backup_target"
  fi
  exit 1
fi

# Clean up backup and remove draft on success
if [[ -n "$backup_target" && -d "$backup_target" ]]; then
  rm -rf "$backup_target"
fi
rm -rf "$draft_dir"

printf '✓ Skill "%s" successfully promoted to skills/%s\n' "$skill_name" "$skill_name"
printf '  To deploy across all local harnesses, run:\n'
printf '    ./scripts/install.sh --targets all --rules\n'
