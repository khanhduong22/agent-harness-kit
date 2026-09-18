#!/bin/bash
# PreToolUse hook: guard against unrequested package installations.
# Enforces 7-Rung Ladder Rule #5: "Already-installed dependency solves it?"
#
# This hook can refuse a command, so every failure path below allows it. A
# guard that blocks on its own parse error costs more than the install it was
# meant to catch.
#
# This script is deployed to Claude Code and Codex only (never Antigravity —
# see install.sh's hook_config_destination). The permission signal is carried
# entirely by hookSpecificOutput.permissionDecision: "allow"|"deny"|"ask".
# A top-level `decision` key is a DIFFERENT, deprecated-for-PreToolUse field
# whose only valid values are "approve"|"block" — "allow"/"ask"/"force_ask"
# are not in that enum. Setting it to a value outside that enum fails Claude
# Code's own hook-output schema validation on every single Bash call, which
# is silent-but-visible (the expected-schema reminder resurfaces constantly).
# Omit it entirely; permissionDecision alone is sufficient and correct.

allow() {
  printf '%s\n' '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
}

PAYLOAD=$(cat) || allow

command -v jq >/dev/null 2>&1 || allow

CMD=$(printf '%s' "$PAYLOAD" | jq -r '.tool_input.command // .toolCall.args.CommandLine // empty' 2>/dev/null) || allow
[ -n "$CMD" ] || allow

# Check if the command is a package install
if echo "$CMD" | grep -qE '\b(npm install|npm i |npx -y|bun add|bun install|yarn add|pnpm add|pnpm install)\b'; then
  # Allow install commands that are just restoring from lockfile (no package name)
  if echo "$CMD" | grep -qE '(npm install|bun install|pnpm install|yarn install)$'; then
    allow
  fi
  REASON='🚫 7-Rung Ladder Rule #5: New package install detected. Confirm this dependency is not already in package.json and cannot be replaced by a few lines of code.'
  printf '%s\n' "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"ask\",\"permissionDecisionReason\":\"$REASON\"}}"
  exit 0
fi

allow
