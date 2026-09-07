#!/usr/bin/env bash
set -euo pipefail

kit_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test_root="$(mktemp -d "${TMPDIR:-/tmp}/agent-harness-kit.XXXXXX")"
trap '/bin/rm -rf "$test_root"' EXIT

kit_test_home="$test_root/home"
export AGENT_HARNESS_HOME="$kit_test_home"
/bin/mkdir -p "$kit_test_home/.claude" "$kit_test_home/.gemini" "$kit_test_home/.codex"
printf '# Existing Claude rule\n' > "$kit_test_home/.claude/CLAUDE.md"
printf '# Existing Gemini rule\n' > "$kit_test_home/.gemini/GEMINI.md"
printf '# Existing Codex rule\n' > "$kit_test_home/.codex/AGENTS.md"
/bin/mkdir -p "$kit_test_home/.claude/skills/triage"
printf 'keep me\n' > "$kit_test_home/.claude/skills/triage/local.txt"

"$kit_root/scripts/install.sh" --targets all --rules >/dev/null
"$kit_root/scripts/install.sh" --targets all --rules >/dev/null

for skill_name in ask-matt writing-for-agents gemini-api-dev; do
  [[ -L "$kit_test_home/.agents/skills/$skill_name" ]]
  [[ -L "$kit_test_home/.claude/skills/$skill_name" ]]
  [[ -L "$kit_test_home/.gemini/config/skills/$skill_name" ]]
done

[[ -L "$kit_test_home/.claude/skills/build" ]]
[[ ! -e "$kit_test_home/.agents/skills/build" ]]
[[ ! -e "$kit_test_home/.gemini/config/skills/build" ]]
[[ -f "$kit_test_home/.claude/skills/triage/local.txt" ]]

for rule_file in "$kit_test_home/.codex/AGENTS.md" "$kit_test_home/.claude/CLAUDE.md" "$kit_test_home/.gemini/GEMINI.md"; do
  [[ "$(grep -c '<!-- agent-harness-kit:start -->' "$rule_file")" -eq 1 ]]
  [[ "$(grep -c '<!-- agent-harness-kit:end -->' "$rule_file")" -eq 1 ]]
  grep -q '^# Existing .* rule$' "$rule_file"
done

"$kit_root/scripts/install.sh" --targets claude --force >/dev/null
[[ -L "$kit_test_home/.claude/skills/triage" ]]
/usr/bin/find "$kit_test_home/.agent-harness-backups" -path '*/claude/triage/local.txt' -type f | grep -q .

printf 'installer integration test passed\n'
