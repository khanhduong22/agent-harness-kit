#!/usr/bin/env bash
set -euo pipefail

kit_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-test.XXXXXX")"
trap '/bin/rm -rf "$test_root"' EXIT

kit_test_home="$test_root/home"
mock_project="$test_root/projects/index-workspace"
export AGENT_HARNESS_HOME="$kit_test_home"

/bin/mkdir -p "$kit_test_home/.claude" "$kit_test_home/.gemini" "$kit_test_home/.codex"
/bin/mkdir -p "$mock_project/.claude" "$mock_project/.gemini"

printf '# Existing User Claude Rule\n' > "$kit_test_home/.claude/CLAUDE.md"
printf '# Existing User Gemini Rule\n' > "$kit_test_home/.gemini/GEMINI.md"
printf '# Existing User Codex Rule\n' > "$kit_test_home/.codex/AGENTS.md"

printf '# Project Existing Rule\n' > "$mock_project/.claude/CLAUDE.md"
printf '# Project Existing Gemini Rule\n' > "$mock_project/.gemini/GEMINI.md"
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

printf '=== Test 3: Project Pack Injection (Index: Claude, Gemini, Codex) ===\n'
# 3a: Dry-run check: verify nothing modified
"$kit_root/scripts/install.sh" --index --project-path "$mock_project" --targets claude,gemini,codex --dry-run >/dev/null
! grep -q 'agent-harness-kit:index' "$mock_project/.claude/CLAUDE.md"
! grep -q 'agent-harness-kit:index' "$mock_project/.gemini/GEMINI.md"
! grep -q 'agent-harness-kit:index' "$mock_project/AGENTS.md"
[[ ! -e "$mock_project/.claude/rules" ]]
[[ ! -e "$mock_project/.agents" ]]
[[ ! -e "$mock_project/index-api" ]]
[[ ! -e "$mock_project/index-admin-cms" ]]

# 3b: Real installation
"$kit_root/scripts/install.sh" --index --project-path "$mock_project" --targets claude,gemini,codex >/dev/null

# Verify root project rule files only contain workspace.md (no leaked cms/api inline)
for root_rule in "$mock_project/.claude/CLAUDE.md" "$mock_project/.gemini/GEMINI.md" "$mock_project/AGENTS.md"; do
  [[ "$(grep -c '<!-- agent-harness-kit:index:start -->' "$root_rule")" -eq 1 ]]
  [[ "$(grep -c '<!-- agent-harness-kit:index:end -->' "$root_rule")" -eq 1 ]]
  grep -q 'Index Platform (Workspace)' "$root_rule"
  ! grep -q 'Project Sub-Profile: Index API' "$root_rule"
  ! grep -q 'Project Sub-Profile: Index Admin CMS' "$root_rule"
done

grep -q 'Project Existing Rule' "$mock_project/.claude/CLAUDE.md"
grep -q 'Project Existing Gemini Rule' "$mock_project/.gemini/GEMINI.md"
grep -q 'Project Existing Codex Rule' "$mock_project/AGENTS.md"

# Verify Claude scoped rules (.claude/rules/*.md with paths frontmatter)
[[ -f "$mock_project/.claude/rules/index-api.md" ]]
grep -q 'paths:' "$mock_project/.claude/rules/index-api.md"
grep -q 'index-api/\*\*' "$mock_project/.claude/rules/index-api.md"
grep -q 'Project Sub-Profile: Index API' "$mock_project/.claude/rules/index-api.md"

[[ -f "$mock_project/.claude/rules/index-admin-cms.md" ]]
grep -q 'paths:' "$mock_project/.claude/rules/index-admin-cms.md"
grep -q 'index-admin-cms/\*\*' "$mock_project/.claude/rules/index-admin-cms.md"
grep -q 'Project Sub-Profile: Index Admin CMS' "$mock_project/.claude/rules/index-admin-cms.md"

# Verify Gemini / Antigravity scoped rules (.agents/rules/*.md with trigger: glob frontmatter)
[[ -f "$mock_project/.agents/rules/index-api.md" ]]
grep -q 'trigger: glob' "$mock_project/.agents/rules/index-api.md"
grep -q 'globs:' "$mock_project/.agents/rules/index-api.md"
grep -q 'index-api/\*\*' "$mock_project/.agents/rules/index-api.md"
grep -q 'Project Sub-Profile: Index API' "$mock_project/.agents/rules/index-api.md"

[[ -f "$mock_project/.agents/rules/index-admin-cms.md" ]]
grep -q 'trigger: glob' "$mock_project/.agents/rules/index-admin-cms.md"
grep -q 'globs:' "$mock_project/.agents/rules/index-admin-cms.md"
grep -q 'index-admin-cms/\*\*' "$mock_project/.agents/rules/index-admin-cms.md"
grep -q 'Project Sub-Profile: Index Admin CMS' "$mock_project/.agents/rules/index-admin-cms.md"

# Verify Codex scoped rules (<dir>/AGENTS.md direct native hierarchy, no frontmatter)
[[ -f "$mock_project/index-api/AGENTS.md" ]]
! grep -q 'paths:' "$mock_project/index-api/AGENTS.md"
! grep -q 'trigger: glob' "$mock_project/index-api/AGENTS.md"
grep -q 'Project Sub-Profile: Index API' "$mock_project/index-api/AGENTS.md"

[[ -f "$mock_project/index-admin-cms/AGENTS.md" ]]
! grep -q 'paths:' "$mock_project/index-admin-cms/AGENTS.md"
! grep -q 'trigger: glob' "$mock_project/index-admin-cms/AGENTS.md"
grep -q 'Project Sub-Profile: Index Admin CMS' "$mock_project/index-admin-cms/AGENTS.md"

# Verify Claude project-scoped MCP configs (.mcp.json)
[[ -f "$mock_project/index-api/.mcp.json" ]]
python3 -c '
import json, sys
data = json.load(open(sys.argv[1]))
servers = data.get("mcpServers", {})
assert servers["postgres"] == {"type": "http", "url": "http://localhost:33000/pg"}
assert servers["redis"] == {"type": "http", "url": "http://localhost:33000/redis"}
assert servers["prisma"]["command"] == "npx"
assert servers["prisma"]["args"] == ["-y", "prisma", "mcp"]
assert servers["prisma"]["disabledTools"] == ["migrate-reset"]
assert "serverUrl" not in servers["postgres"]
assert "serverUrl" not in servers["redis"]
' "$mock_project/index-api/.mcp.json"

[[ -f "$mock_project/index-admin-cms/.mcp.json" ]]
python3 -c '
import json, sys
data = json.load(open(sys.argv[1]))
servers = data.get("mcpServers", {})
assert servers["figma"] == {"type": "http", "url": "http://127.0.0.1:3845/mcp"}
assert servers["chrome-devtools-mcp"]["command"] == "npx"
assert servers["chrome-devtools-mcp"]["args"] == ["-y", "chrome-devtools-mcp@latest"]
assert "serverUrl" not in servers["figma"]
' "$mock_project/index-admin-cms/.mcp.json"

# Verify Antigravity / Gemini project-scoped MCP configs (.agents/mcp_config.json)
[[ -f "$mock_project/index-api/.agents/mcp_config.json" ]]
python3 -c '
import json, sys
data = json.load(open(sys.argv[1]))
servers = data.get("mcpServers", {})
assert servers["postgres"] == {"serverUrl": "http://localhost:33000/pg"}
assert servers["redis"] == {"serverUrl": "http://localhost:33000/redis"}
assert servers["prisma"]["command"] == "npx"
assert servers["prisma"]["args"] == ["-y", "prisma", "mcp"]
assert servers["prisma"]["disabledTools"] == ["migrate-reset"]
assert "type" not in servers["postgres"]
assert "url" not in servers["postgres"]
assert "type" not in servers["redis"]
assert "url" not in servers["redis"]
' "$mock_project/index-api/.agents/mcp_config.json"

[[ -f "$mock_project/index-admin-cms/.agents/mcp_config.json" ]]
python3 -c '
import json, sys
data = json.load(open(sys.argv[1]))
servers = data.get("mcpServers", {})
assert servers["figma"] == {"serverUrl": "http://127.0.0.1:3845/mcp"}
assert servers["chrome-devtools-mcp"]["command"] == "npx"
assert servers["chrome-devtools-mcp"]["args"] == ["-y", "chrome-devtools-mcp@latest"]
assert "type" not in servers["figma"]
assert "url" not in servers["figma"]
' "$mock_project/index-admin-cms/.agents/mcp_config.json"

# 3c: Idempotency check for project pack injection
reindex_output="$("$kit_root/scripts/install.sh" --index --project-path "$mock_project" --targets claude,gemini,codex)"
echo "$reindex_output" | grep -q 'unchanged'
echo "$reindex_output" | grep -q 'mcp unchanged'

# Verify global rules STILL do NOT have Index pack
for rule_file in "$kit_test_home/.codex/AGENTS.md" "$kit_test_home/.claude/CLAUDE.md" "$kit_test_home/.gemini/GEMINI.md"; do
  ! grep -q 'agent-harness-kit:index' "$rule_file"
done
printf 'Passed: Project Pack Injection with strict isolation, path-specific rules & scoped MCP\n'

printf '=== Test 4: Rollback latest ===\n'
# Ensure receipt.json was recorded
[[ -f "$kit_test_home/.agent-harness-backups/latest/receipt.json" ]]

# Rollback project installation
"$kit_root/scripts/install.sh" --rollback latest >/dev/null

# Verify project root rule files were restored to pre-index state
! grep -q 'agent-harness-kit:index' "$mock_project/.claude/CLAUDE.md"
! grep -q 'agent-harness-kit:index' "$mock_project/.gemini/GEMINI.md"
! grep -q 'agent-harness-kit:index' "$mock_project/AGENTS.md"
grep -q '# Project Existing Rule' "$mock_project/.claude/CLAUDE.md"
grep -q '# Project Existing Gemini Rule' "$mock_project/.gemini/GEMINI.md"
grep -q '# Project Existing Codex Rule' "$mock_project/AGENTS.md"

# Verify all created scoped rules and MCP configs were cleanly deleted
[[ ! -f "$mock_project/.claude/rules/index-api.md" ]]
[[ ! -f "$mock_project/.claude/rules/index-admin-cms.md" ]]
[[ ! -f "$mock_project/.agents/rules/index-api.md" ]]
[[ ! -f "$mock_project/.agents/rules/index-admin-cms.md" ]]
[[ ! -f "$mock_project/index-api/AGENTS.md" ]]
[[ ! -f "$mock_project/index-admin-cms/AGENTS.md" ]]
[[ ! -f "$mock_project/index-api/.mcp.json" ]]
[[ ! -f "$mock_project/index-admin-cms/.mcp.json" ]]
[[ ! -f "$mock_project/index-api/.agents/mcp_config.json" ]]
[[ ! -f "$mock_project/index-admin-cms/.agents/mcp_config.json" ]]
[[ ! -d "$mock_project/index-api/.agents" ]]
[[ ! -d "$mock_project/index-admin-cms/.agents" ]]

printf 'Passed: Rollback restored original project state and cleaned up scoped rules and MCP configs\n'

printf '\nALL HARNESS BEHAVIORAL TESTS PASSED SUCCESSFULLY!\n'

