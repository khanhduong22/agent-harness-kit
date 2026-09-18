#!/usr/bin/env bash
set -euo pipefail

kit_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/assert.sh
. "$kit_root/scripts/assert.sh"

test_root="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-test.XXXXXX")"
trap '/bin/rm -rf "$test_root"' EXIT

kit_test_home="$test_root/home"
mock_project="$test_root/projects/index-workspace"
export AGENT_HARNESS_HOME="$kit_test_home"

# Sample real skills instead of hardcoding names, which rot on every rename or
# purge and — before assertions were enforced — did so undetected.
sample_skills=()
while IFS= read -r skill_name; do
  sample_skills+=("$skill_name")
done < <(kit_skill_names "$kit_root")
assert "kit must ship at least 3 skills to sample fixtures from" \
  test "${#sample_skills[@]}" -ge 3
sample_skills=("${sample_skills[0]}" "${sample_skills[1]}" "${sample_skills[2]}")

/bin/mkdir -p "$kit_test_home/.claude" "$kit_test_home/.gemini" "$kit_test_home/.codex"
/bin/mkdir -p "$mock_project/.claude"

printf '# Existing User Claude Rule\n' > "$kit_test_home/.claude/CLAUDE.md"
printf '# Existing User Gemini Rule\n' > "$kit_test_home/.gemini/GEMINI.md"
printf '# Existing User Codex Rule\n' > "$kit_test_home/.codex/AGENTS.md"

printf '# Project Existing Rule\n' > "$mock_project/.claude/CLAUDE.md"
printf '# Project Existing Codex Rule\n' > "$mock_project/AGENTS.md"

printf '=== Test 1: Fresh Core Installation ===\n'
"$kit_root/scripts/install.sh" --targets all --rules >/dev/null

for skill_name in "${sample_skills[@]}"; do
  assert "agents target installed $skill_name" \
    test -L "$kit_test_home/.agents/skills/$skill_name"
  assert "claude target installed $skill_name" \
    test -L "$kit_test_home/.claude/skills/$skill_name"
  assert "gemini target installed $skill_name" \
    test -L "$kit_test_home/.gemini/config/skills/$skill_name"
done

for rule_file in "$kit_test_home/.codex/AGENTS.md" "$kit_test_home/.claude/CLAUDE.md" "$kit_test_home/.gemini/GEMINI.md"; do
  assert "exactly one start marker in $rule_file" \
    test "$(grep -c '<!-- agent-harness-kit:start -->' "$rule_file")" -eq 1
  assert "exactly one end marker in $rule_file" \
    test "$(grep -c '<!-- agent-harness-kit:end -->' "$rule_file")" -eq 1
  refute "Index profile must not leak into global rule $rule_file" \
    grep -q 'agent-harness-kit:index' "$rule_file"
  refute "index-admin-cms must not leak into global rule $rule_file" \
    grep -q 'index-admin-cms' "$rule_file"
done

printf 'Passed: Fresh Core Installation\n'

printf '=== Test 2: Idempotency (Duplicate Prevention) ===\n'
"$kit_root/scripts/install.sh" --targets all --rules > "$test_root/reinstall.log"
assert "reinstall reports unchanged entries" \
  grep -q 'unchanged' "$test_root/reinstall.log"
for rule_file in "$kit_test_home/.codex/AGENTS.md" "$kit_test_home/.claude/CLAUDE.md" "$kit_test_home/.gemini/GEMINI.md"; do
  assert "still exactly one start marker in $rule_file after reinstall" \
    test "$(grep -c '<!-- agent-harness-kit:start -->' "$rule_file")" -eq 1
  assert "still exactly one end marker in $rule_file after reinstall" \
    test "$(grep -c '<!-- agent-harness-kit:end -->' "$rule_file")" -eq 1
done
printf 'Passed: Idempotency check\n'

printf '=== Test 3: Project Pack Injection (Index) ===\n'
"$kit_root/scripts/install.sh" --index --project-path "$mock_project" --targets claude,codex >/dev/null

assert "exactly one index start marker in project CLAUDE.md" \
  test "$(grep -c '<!-- agent-harness-kit:index:start -->' "$mock_project/.claude/CLAUDE.md")" -eq 1
assert "exactly one index end marker in project CLAUDE.md" \
  test "$(grep -c '<!-- agent-harness-kit:index:end -->' "$mock_project/.claude/CLAUDE.md")" -eq 1
assert "project CLAUDE.md carries the Index Platform pack" \
  grep -q 'Index Platform' "$mock_project/.claude/CLAUDE.md"
assert "project CLAUDE.md mentions index-api" \
  grep -q 'index-api' "$mock_project/.claude/CLAUDE.md"
assert "project CLAUDE.md mentions index-admin-cms" \
  grep -q 'index-admin-cms' "$mock_project/.claude/CLAUDE.md"

assert "exactly one index start marker in project AGENTS.md" \
  test "$(grep -c '<!-- agent-harness-kit:index:start -->' "$mock_project/AGENTS.md")" -eq 1
assert "project AGENTS.md preserves the pre-existing operator rule" \
  grep -q 'Project Existing Codex Rule' "$mock_project/AGENTS.md"

for rule_file in "$kit_test_home/.codex/AGENTS.md" "$kit_test_home/.claude/CLAUDE.md" "$kit_test_home/.gemini/GEMINI.md"; do
  refute "Index pack must stay out of global rule $rule_file" \
    grep -q 'agent-harness-kit:index' "$rule_file"
done
printf 'Passed: Project Pack Injection with strict isolation\n'

printf '=== Test 4: Rollback latest ===\n'
assert "install recorded a rollback receipt" \
  test -f "$kit_test_home/.agent-harness-backups/latest/receipt.json"

"$kit_root/scripts/install.sh" --rollback latest >/dev/null

refute "rollback removed the index pack from project CLAUDE.md" \
  grep -q 'agent-harness-kit:index' "$mock_project/.claude/CLAUDE.md"
refute "rollback removed the index pack from project AGENTS.md" \
  grep -q 'agent-harness-kit:index' "$mock_project/AGENTS.md"
assert "rollback restored the original project CLAUDE.md content" \
  grep -q '# Project Existing Rule' "$mock_project/.claude/CLAUDE.md"
assert "rollback restored the original project AGENTS.md content" \
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

assert "project A received its own .mcp.json" test -f "$project_a/.mcp.json"
assert "project A mcp config declares postgres" \
  grep -q '"postgres"' "$project_a/.mcp.json"
assert "project A mcp config points at the local gateway" \
  grep -q '"http://localhost:33000/pg"' "$project_a/.mcp.json"
assert "project A mcp config declares framefit" \
  grep -q '"framefit"' "$project_a/.mcp.json"
assert "project A mcp config references the Figma key by env var" \
  grep -q '"\${FIGMA_API_KEY}"' "$project_a/.mcp.json"
refute "a literal Figma token must never be written to disk" \
  grep -q 'figd_' "$project_a/.mcp.json"

assert "project B .mcp.json is byte-for-byte untouched" \
  test "$(/sbin/md5 -q "$project_b/.mcp.json")" = "$project_b_before"

assert "no .mcp.json leaked into any global harness path" \
  test -z "$(/usr/bin/find "$kit_test_home" -name '.mcp.json')"
printf 'Passed: MCP config written only inside the target project\n'

printf '=== Test 6: MCP tool allowlist merge and idempotency ===\n'
assert "project A received a Claude settings file" \
  test -f "$project_a/.claude/settings.json"
assert "allowlist includes the postgres query tool" \
  grep -q 'mcp__postgres__query' "$project_a/.claude/settings.json"
assert "allowlist includes the framefit layout tool" \
  grep -q 'mcp__framefit__get_layout_spec' "$project_a/.claude/settings.json"
refute "tools deliberately left off the allowlist stay out (get_variables)" \
  grep -q 'mcp__framefit__get_variables' "$project_a/.claude/settings.json"
refute "tools deliberately left off the allowlist stay out (get_libraries)" \
  grep -q 'mcp__framefit__get_libraries' "$project_a/.claude/settings.json"

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

AGENT_HARNESS_BACKUP_DIR="$test_root/backups-mcp" \
  "$kit_root/scripts/install.sh" --index --project-path "$project_a" --targets claude \
  > "$test_root/reinstall-mcp.log"

assert "reinstall reports the mcp config unchanged" \
  grep -q 'mcp config unchanged' "$test_root/reinstall-mcp.log"
assert "reinstall reports the permission config unchanged" \
  grep -q 'permission config unchanged' "$test_root/reinstall-mcp.log"
assert "operator-added allow entry survives reinstall" \
  grep -q 'Bash(git status:\*)' "$project_a/.claude/settings.json"
assert "operator-added deny entry survives reinstall" \
  grep -q 'Bash(rm -rf:\*)' "$project_a/.claude/settings.json"
assert "managed allow entry is not duplicated on reinstall" \
  test "$(grep -c 'mcp__postgres__query' "$project_a/.claude/settings.json")" -eq 1
assert "managed mcp server is not duplicated on reinstall" \
  test "$(grep -c '"postgres"' "$project_a/.mcp.json")" -eq 1
printf 'Passed: Allowlist merged without clobbering or duplicating entries\n'

printf '=== Test 7: MCP dry run and unsupported targets ===\n'
project_c="$test_root/projects/index-data"
/bin/mkdir -p "$project_c"
project_c_real="$(cd "$project_c" && pwd -P)"
AGENT_HARNESS_BACKUP_DIR="$test_root/backups-mcp" \
  "$kit_root/scripts/install.sh" --index --project-path "$project_c" --targets claude --dry-run \
  > "$test_root/dry-run.log"
assert "dry run announces the mcp config it would write" \
  grep -q "would write mcp config: $project_c_real/.mcp.json" "$test_root/dry-run.log"
assert "dry run announces the permission config it would write" \
  grep -q "would write permission config: $project_c_real/.claude/settings.json" "$test_root/dry-run.log"
assert "dry run wrote no .mcp.json" test ! -e "$project_c/.mcp.json"
assert "dry run wrote no settings.json" test ! -e "$project_c/.claude/settings.json"

AGENT_HARNESS_BACKUP_DIR="$test_root/backups-mcp" \
  "$kit_root/scripts/install.sh" --index --project-path "$project_c" --targets codex,gemini \
  > "$test_root/unsupported.log"
assert "codex is reported as an unsupported mcp target" \
  grep -q 'mcp unsupported target: codex' "$test_root/unsupported.log"
assert "gemini is reported as an unsupported mcp target" \
  grep -q 'mcp unsupported target: gemini' "$test_root/unsupported.log"
assert "unsupported targets wrote no .mcp.json" test ! -e "$project_c/.mcp.json"
printf 'Passed: Dry run wrote nothing and unverified targets are explicit\n'

printf '=== Test 8: MCP rollback ===\n'
project_d="$test_root/projects/index-ai"
/bin/mkdir -p "$project_d"
printf '{\n  "mcpServers": {\n    "pre-existing": {\n      "command": "node"\n    }\n  }\n}\n' > "$project_d/.mcp.json"
project_d_before="$(/sbin/md5 -q "$project_d/.mcp.json")"

AGENT_HARNESS_BACKUP_DIR="$test_root/backups-rollback" \
  "$kit_root/scripts/install.sh" --index --project-path "$project_d" --targets claude >/dev/null

assert "install merged postgres into the pre-existing mcp config" \
  grep -q '"postgres"' "$project_d/.mcp.json"
assert "install preserved the pre-existing mcp server entry" \
  grep -q '"pre-existing"' "$project_d/.mcp.json"
assert "install created a Claude settings file for project D" \
  test -f "$project_d/.claude/settings.json"
assert "receipt records the modified file for rollback" \
  grep -q '"type": "file"' "$test_root/backups-rollback/latest/receipt.json"

AGENT_HARNESS_BACKUP_DIR="$test_root/backups-rollback" \
  "$kit_root/scripts/install.sh" --rollback latest >/dev/null

assert "rollback restored .mcp.json byte-for-byte" \
  test "$(/sbin/md5 -q "$project_d/.mcp.json")" = "$project_d_before"
refute "rollback removed the injected postgres entry" \
  grep -q '"postgres"' "$project_d/.mcp.json"
assert "rollback removed the settings file it created" \
  test ! -e "$project_d/.claude/settings.json"
printf 'Passed: Rollback restored .mcp.json and removed created permission config\n'

printf '=== Test 9: Hook deployment and merge ===\n'
project_e="$test_root/projects/index-hooks"
/bin/mkdir -p "$project_e"

AGENT_HARNESS_BACKUP_DIR="$test_root/backups-hooks" \
  "$kit_root/scripts/install.sh" --index --project-path "$project_e" --targets claude >/dev/null

# Resolved, not just absolute: the installer canonicalises the path it writes,
# and on macOS $TMPDIR lives under /var, a symlink to /private/var.
hooks_dir="$(cd "$kit_test_home/.agent-harness/hooks" && pwd -P)"
assert "hook scripts are deployed to the shared directory" \
  test -x "$hooks_dir/guard-new-packages.sh"
assert "the hook block lands in the project settings" \
  grep -q '"PreToolUse"' "$project_e/.claude/settings.json"
assert "hook commands point at the deployed scripts, not the kit checkout" \
  grep -q "$hooks_dir/guard-new-packages.sh" "$project_e/.claude/settings.json"
refute "the {{HOOKS_DIR}} placeholder is never left unsubstituted" \
  grep -q 'HOOKS_DIR' "$project_e/.claude/settings.json"

# An operator adds a hook on an event the kit does not manage, then reinstalls.
/usr/bin/env python3 - "$project_e/.claude/settings.json" <<'PY'
import json, sys
path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    data = json.load(handle)
data["hooks"].setdefault("SessionStart", []).append(
    {"hooks": [{"type": "command", "command": "/opt/operator-own.sh"}]}
)
with open(path, "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
PY

AGENT_HARNESS_BACKUP_DIR="$test_root/backups-hooks" \
  "$kit_root/scripts/install.sh" --index --project-path "$project_e" --targets claude \
  > "$test_root/reinstall-hooks.log"

assert "an operator hook on an unmanaged event survives reinstall" \
  grep -q '/opt/operator-own.sh' "$project_e/.claude/settings.json"
assert "the kit's own hook entry is not duplicated on reinstall" \
  test "$(grep -c "$hooks_dir/guard-new-packages.sh" "$project_e/.claude/settings.json")" -eq 1
assert "a reinstall that changes nothing reports the hook config unchanged" \
  grep -q 'hook config unchanged' "$test_root/reinstall-hooks.log"
printf 'Passed: Hooks deployed, merged, and idempotent\n'

printf '=== Test 10: Hook script rollback ===\n'
# hooks_dir is shared home-wide (~/.agent-harness/hooks), not per-project, so
# by this point Test 9 has already installed into it once — a fresh install
# targeting the same home would find the scripts already present and take the
# "restore from backup" receipt path, not "created", making rollback restore
# rather than remove. Testing "rollback removes a freshly created script"
# needs a home that has never had hooks installed into it: its own
# AGENT_HARNESS_HOME, the way Test 8 isolates its MCP rollback check.
#
# Deployed hook scripts used to have no receipt entries at all: install_hooks
# called init_receipt (which only stamps the receipt file into existence) and
# never record_receipt_action for the copied scripts, so --rollback restored
# settings.json but left every *.sh behind — undetected until a real review
# caught it against a live deployment.
rollback_home="$test_root/home-hooks-rollback"
rollback_project="$test_root/projects/index-hooks-rollback"
/bin/mkdir -p "$rollback_home" "$rollback_project"
AGENT_HARNESS_HOME="$rollback_home" AGENT_HARNESS_BACKUP_DIR="$test_root/backups-hooks-rollback" \
  "$kit_root/scripts/install.sh" --index --project-path "$rollback_project" --targets claude >/dev/null
rollback_hooks_dir="$(cd "$rollback_home/.agent-harness/hooks" && pwd -P)"
AGENT_HARNESS_HOME="$rollback_home" AGENT_HARNESS_BACKUP_DIR="$test_root/backups-hooks-rollback" \
  "$kit_root/scripts/install.sh" --rollback latest >/dev/null
assert "rollback removes the deployed hook scripts, not just the settings entry" \
  test ! -e "$rollback_hooks_dir/guard-new-packages.sh"
printf 'Passed: Rollback removed the hook scripts a fresh install created\n'

printf '\nALL HARNESS BEHAVIORAL TESTS PASSED SUCCESSFULLY!\n'
