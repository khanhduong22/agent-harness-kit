#!/usr/bin/env bash
set -euo pipefail

kit_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-test.XXXXXX")"
trap '/bin/rm -rf "$test_root"' EXIT

kit_test_home="$test_root/home"
mock_project="$test_root/projects/index-workspace"
export AGENT_HARNESS_HOME="$kit_test_home"

/bin/mkdir -p "$kit_test_home/.claude" "$kit_test_home/.gemini" "$kit_test_home/.codex"
/bin/mkdir -p "$mock_project/.claude"

printf '# Existing User Claude Rule\n' > "$kit_test_home/.claude/CLAUDE.md"
printf '# Existing User Gemini Rule\n' > "$kit_test_home/.gemini/GEMINI.md"
printf '# Existing User Codex Rule\n' > "$kit_test_home/.codex/AGENTS.md"

printf '# Project Existing Rule\n' > "$mock_project/.claude/CLAUDE.md"
printf '# Project Existing Codex Rule\n' > "$mock_project/AGENTS.md"

printf '=== Test 1: Fresh Core Installation ===\n'
"$kit_root/scripts/install.sh" --targets all --rules >/dev/null

for skill_name in ask-matt writing-for-agents gemini-api-dev; do
  [[ -L "$kit_test_home/.agents/skills/$skill_name" ]]
  [[ -L "$kit_test_home/.claude/skills/$skill_name" ]]
  [[ -L "$kit_test_home/.gemini/config/skills/$skill_name" ]]
done

for rule_file in "$kit_test_home/.codex/AGENTS.md" "$kit_test_home/.claude/CLAUDE.md" "$kit_test_home/.gemini/GEMINI.md"; do
  [[ "$(grep -c '<!-- agent-harness-kit:start -->' "$rule_file")" -eq 1 ]]
  [[ "$(grep -c '<!-- agent-harness-kit:end -->' "$rule_file")" -eq 1 ]]
  # Ensure Index profile is NOT leaked to global rules
  ! grep -q 'agent-harness-kit:index' "$rule_file"
  ! grep -q 'index-admin-cms' "$rule_file"
done

printf 'Passed: Fresh Core Installation\n'

printf '=== Test 2: Idempotency (Duplicate Prevention) ===\n'
reinstall_output="$("$kit_root/scripts/install.sh" --targets all --rules)"
echo "$reinstall_output" | grep -q 'unchanged'
for rule_file in "$kit_test_home/.codex/AGENTS.md" "$kit_test_home/.claude/CLAUDE.md" "$kit_test_home/.gemini/GEMINI.md"; do
  [[ "$(grep -c '<!-- agent-harness-kit:start -->' "$rule_file")" -eq 1 ]]
  [[ "$(grep -c '<!-- agent-harness-kit:end -->' "$rule_file")" -eq 1 ]]
done
printf 'Passed: Idempotency check\n'

printf '=== Test 3: Project Pack Injection (Index) ===\n'
"$kit_root/scripts/install.sh" --index --project-path "$mock_project" --targets claude,codex >/dev/null

# Verify project rules received Index pack
[[ "$(grep -c '<!-- agent-harness-kit:index:start -->' "$mock_project/.claude/CLAUDE.md")" -eq 1 ]]
[[ "$(grep -c '<!-- agent-harness-kit:index:end -->' "$mock_project/.claude/CLAUDE.md")" -eq 1 ]]
grep -q 'Index Platform' "$mock_project/.claude/CLAUDE.md"
grep -q 'index-api' "$mock_project/.claude/CLAUDE.md"
grep -q 'index-admin-cms' "$mock_project/.claude/CLAUDE.md"

[[ "$(grep -c '<!-- agent-harness-kit:index:start -->' "$mock_project/AGENTS.md")" -eq 1 ]]
grep -q 'Project Existing Codex Rule' "$mock_project/AGENTS.md"

# Verify global rules STILL do NOT have Index pack
for rule_file in "$kit_test_home/.codex/AGENTS.md" "$kit_test_home/.claude/CLAUDE.md" "$kit_test_home/.gemini/GEMINI.md"; do
  ! grep -q 'agent-harness-kit:index' "$rule_file"
done
printf 'Passed: Project Pack Injection with strict isolation\n'

printf '=== Test 4: Rollback latest ===\n'
# Ensure receipt.json was recorded
[[ -f "$kit_test_home/.agent-harness-backups/latest/receipt.json" ]]

# Rollback project installation
"$kit_root/scripts/install.sh" --rollback latest >/dev/null

# Verify project file was restored to pre-index state
! grep -q 'agent-harness-kit:index' "$mock_project/.claude/CLAUDE.md"
! grep -q 'agent-harness-kit:index' "$mock_project/AGENTS.md"
grep -q '# Project Existing Rule' "$mock_project/.claude/CLAUDE.md"
grep -q '# Project Existing Codex Rule' "$mock_project/AGENTS.md"

printf 'Passed: Rollback restored original project state\n'

printf '\nALL HARNESS BEHAVIORAL TESTS PASSED SUCCESSFULLY!\n'
