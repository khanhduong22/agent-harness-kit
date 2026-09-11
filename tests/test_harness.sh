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

printf '=== Test 5: MCP project isolation ===\n'
project_a="$test_root/projects/index-api"
project_b="$test_root/projects/index-admin-cms"
/bin/mkdir -p "$project_a" "$project_b"
printf '{\n  "mcpServers": {\n    "project-b-only": {\n      "command": "node"\n    }\n  }\n}\n' > "$project_b/.mcp.json"
project_b_before="$(/sbin/md5 -q "$project_b/.mcp.json")"

AGENT_HARNESS_BACKUP_DIR="$test_root/backups-mcp" \
  "$kit_root/scripts/install.sh" --index --project-path "$project_a" --targets claude >/dev/null

# Project A received its own MCP config at the project root
[[ -f "$project_a/.mcp.json" ]]
grep -q '"postgres"' "$project_a/.mcp.json"
grep -q '"http://localhost:33000/pg"' "$project_a/.mcp.json"
grep -q '"framefit"' "$project_a/.mcp.json"
grep -q '"\${FIGMA_API_KEY}"' "$project_a/.mcp.json"
! grep -q 'figd_' "$project_a/.mcp.json"

# Project B is byte-for-byte untouched
[[ "$(/sbin/md5 -q "$project_b/.mcp.json")" == "$project_b_before" ]]

# No MCP config leaked into any global harness path
! /usr/bin/find "$kit_test_home" -name '.mcp.json' | grep -q .
printf 'Passed: MCP config written only inside the target project\n'

printf '=== Test 6: MCP tool allowlist merge and idempotency ===\n'
[[ -f "$project_a/.claude/settings.json" ]]
grep -q 'mcp__postgres__query' "$project_a/.claude/settings.json"
grep -q 'mcp__framefit__get_layout_spec' "$project_a/.claude/settings.json"
# Tools deliberately left off the allowlist stay out
! grep -q 'mcp__framefit__get_variables' "$project_a/.claude/settings.json"
! grep -q 'mcp__framefit__get_libraries' "$project_a/.claude/settings.json"

# An operator adds an unrelated permission by hand, then reinstalls
/usr/bin/env python3 - "$project_a/.claude/settings.json" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    data = json.load(handle)
data["permissions"]["allow"].insert(0, "Bash(git status:*)")
data["permissions"]["deny"] = ["Bash(rm -rf:*)"]
with open(path, "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
PY

reinstall_mcp_output="$(AGENT_HARNESS_BACKUP_DIR="$test_root/backups-mcp" \
  "$kit_root/scripts/install.sh" --index --project-path "$project_a" --targets claude)"

echo "$reinstall_mcp_output" | grep -q 'mcp config unchanged'
echo "$reinstall_mcp_output" | grep -q 'permission config unchanged'
grep -q 'Bash(git status:\*)' "$project_a/.claude/settings.json"
grep -q 'Bash(rm -rf:\*)' "$project_a/.claude/settings.json"
[[ "$(grep -c 'mcp__postgres__query' "$project_a/.claude/settings.json")" -eq 1 ]]
[[ "$(grep -c '"postgres"' "$project_a/.mcp.json")" -eq 1 ]]
printf 'Passed: Allowlist merged without clobbering or duplicating entries\n'

printf '=== Test 7: MCP dry run and unsupported targets ===\n'
project_c="$test_root/projects/index-data"
/bin/mkdir -p "$project_c"
project_c_real="$(cd "$project_c" && pwd -P)"
dry_run_output="$(AGENT_HARNESS_BACKUP_DIR="$test_root/backups-mcp" \
  "$kit_root/scripts/install.sh" --index --project-path "$project_c" --targets claude --dry-run)"
echo "$dry_run_output" | grep -q "would write mcp config: $project_c_real/.mcp.json"
echo "$dry_run_output" | grep -q "would write permission config: $project_c_real/.claude/settings.json"
[[ ! -e "$project_c/.mcp.json" ]]
[[ ! -e "$project_c/.claude/settings.json" ]]

unsupported_output="$(AGENT_HARNESS_BACKUP_DIR="$test_root/backups-mcp" \
  "$kit_root/scripts/install.sh" --index --project-path "$project_c" --targets codex,gemini)"
echo "$unsupported_output" | grep -q 'mcp unsupported target: codex'
echo "$unsupported_output" | grep -q 'mcp unsupported target: gemini'
[[ ! -e "$project_c/.mcp.json" ]]
printf 'Passed: Dry run wrote nothing and unverified targets are explicit\n'

printf '=== Test 8: MCP rollback ===\n'
project_d="$test_root/projects/index-ai"
/bin/mkdir -p "$project_d"
printf '{\n  "mcpServers": {\n    "pre-existing": {\n      "command": "node"\n    }\n  }\n}\n' > "$project_d/.mcp.json"
project_d_before="$(/sbin/md5 -q "$project_d/.mcp.json")"

AGENT_HARNESS_BACKUP_DIR="$test_root/backups-rollback" \
  "$kit_root/scripts/install.sh" --index --project-path "$project_d" --targets claude >/dev/null

grep -q '"postgres"' "$project_d/.mcp.json"
grep -q '"pre-existing"' "$project_d/.mcp.json"
[[ -f "$project_d/.claude/settings.json" ]]
/usr/bin/grep -q '"type": "file"' "$test_root/backups-rollback/latest/receipt.json"

AGENT_HARNESS_BACKUP_DIR="$test_root/backups-rollback" \
  "$kit_root/scripts/install.sh" --rollback latest >/dev/null

# Pre-existing file restored byte-for-byte, created file removed
[[ "$(/sbin/md5 -q "$project_d/.mcp.json")" == "$project_d_before" ]]
! grep -q '"postgres"' "$project_d/.mcp.json"
[[ ! -e "$project_d/.claude/settings.json" ]]
printf 'Passed: Rollback restored .mcp.json and removed created permission config\n'

printf '\nALL HARNESS BEHAVIORAL TESTS PASSED SUCCESSFULLY!\n'
