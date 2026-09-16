#!/usr/bin/env bash
set -euo pipefail

kit_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/assert.sh
. "$kit_root/scripts/assert.sh"

test_root="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-kit.XXXXXX")"
trap '/bin/rm -rf "$test_root"' EXIT

# Sample real skills out of the kit rather than hardcoding names. Hardcoded
# fixtures rot silently every time a skill is renamed or purged.
kit_skills=()
while IFS= read -r skill_name; do
  kit_skills+=("$skill_name")
done < <(kit_skill_names "$kit_root")
assert "kit must ship at least 4 skills to sample fixtures from" \
  test "${#kit_skills[@]}" -ge 4

sample_skills=("${kit_skills[0]}" "${kit_skills[1]}" "${kit_skills[2]}")
# The conflict fixture must not overlap the sampled skills: it is pre-created as
# a real directory, so it is deliberately NOT a symlink after a plain install.
conflict_skill="${kit_skills[3]}"

overlay_skill=""
for overlay_dir in "$kit_root"/overlays/claude/skills/*/; do
  [[ -f "$overlay_dir/SKILL.md" ]] || continue
  overlay_skill="$(basename "$overlay_dir")"
  break
done
assert "claude overlay must ship at least one skill" test -n "$overlay_skill"

kit_test_home="$test_root/home"
export AGENT_HARNESS_HOME="$kit_test_home"
/bin/mkdir -p "$kit_test_home/.claude" "$kit_test_home/.gemini" "$kit_test_home/.codex"
printf '# Existing Claude rule\n' > "$kit_test_home/.claude/CLAUDE.md"
printf '# Existing Gemini rule\n' > "$kit_test_home/.gemini/GEMINI.md"
printf '# Existing Codex rule\n' > "$kit_test_home/.codex/AGENTS.md"
/bin/mkdir -p "$kit_test_home/.claude/skills/$conflict_skill"
printf 'keep me\n' > "$kit_test_home/.claude/skills/$conflict_skill/local.txt"

"$kit_root/scripts/install.sh" --targets all --rules >/dev/null
"$kit_root/scripts/install.sh" --targets all --rules >/dev/null

for skill_name in "${sample_skills[@]}"; do
  assert "agents target installed $skill_name" \
    test -L "$kit_test_home/.agents/skills/$skill_name"
  assert "claude target installed $skill_name" \
    test -L "$kit_test_home/.claude/skills/$skill_name"
  assert "gemini target installed $skill_name" \
    test -L "$kit_test_home/.gemini/config/skills/$skill_name"
done

assert "claude overlay skill $overlay_skill installed for claude" \
  test -L "$kit_test_home/.claude/skills/$overlay_skill"
assert "claude overlay skill $overlay_skill must not leak to agents" \
  test ! -e "$kit_test_home/.agents/skills/$overlay_skill"
assert "claude overlay skill $overlay_skill must not leak to gemini" \
  test ! -e "$kit_test_home/.gemini/config/skills/$overlay_skill"
assert "plain install preserves a pre-existing local skill directory" \
  test -f "$kit_test_home/.claude/skills/$conflict_skill/local.txt"

for rule_file in "$kit_test_home/.codex/AGENTS.md" "$kit_test_home/.claude/CLAUDE.md" "$kit_test_home/.gemini/GEMINI.md"; do
  assert "exactly one managed-block start marker in $rule_file" \
    test "$(grep -c '<!-- agent-harness-kit:start -->' "$rule_file")" -eq 1
  assert "exactly one managed-block end marker in $rule_file" \
    test "$(grep -c '<!-- agent-harness-kit:end -->' "$rule_file")" -eq 1
  assert "pre-existing operator rule preserved in $rule_file" \
    grep -q '^# Existing .* rule$' "$rule_file"
done

"$kit_root/scripts/install.sh" --targets claude,gemini --rules --rules-mode replace >/dev/null
refute "rules-mode replace drops the pre-existing Claude rule" \
  grep -q '^# Existing Claude rule$' "$kit_test_home/.claude/CLAUDE.md"
refute "rules-mode replace drops the pre-existing Gemini rule" \
  grep -q '^# Existing Gemini rule$' "$kit_test_home/.gemini/GEMINI.md"
assert "rules-mode replace leaves untargeted Codex rule intact" \
  grep -q '^# Existing Codex rule$' "$kit_test_home/.codex/AGENTS.md"

"$kit_root/scripts/install.sh" --targets claude --force >/dev/null
assert "--force replaces the conflicting directory with the kit symlink" \
  test -L "$kit_test_home/.claude/skills/$conflict_skill"
assert "--force backs up the displaced local file" \
  test -n "$(/usr/bin/find "$kit_test_home/.agent-harness-backups" -path "*/claude/$conflict_skill/local.txt" -type f)"

# Pruning orphans. A skill deleted from the kit leaves a dangling link behind on
# every machine that already installed it; the stale skill then keeps applying.
# Only kit-owned dangling links may be removed — a foreign link and a real local
# directory must both survive, or pruning would eat the operator's own work.
claude_skills="$kit_test_home/.claude/skills"
/bin/ln -s "$kit_root/skills/__removed_from_kit__" "$claude_skills/__removed_from_kit__"
/bin/ln -s "$test_root/somewhere-else" "$claude_skills/__foreign_link__"
/bin/mkdir -p "$claude_skills/__operator_local__"
printf 'keep me\n' > "$claude_skills/__operator_local__/local.txt"

"$kit_root/scripts/install.sh" --targets claude >/dev/null

assert "a dangling kit link is pruned once its skill leaves the kit" \
  test ! -L "$claude_skills/__removed_from_kit__"
assert "a dangling link pointing outside the kit is left alone" \
  test -L "$claude_skills/__foreign_link__"
assert "an operator's own skill directory is never pruned" \
  test -f "$claude_skills/__operator_local__/local.txt"

printf 'installer integration test passed\n'
