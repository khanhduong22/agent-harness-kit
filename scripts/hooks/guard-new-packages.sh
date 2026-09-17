#!/bin/bash
# PreToolUse hook: guard against unrequested package installations.
# Enforces 7-Rung Ladder Rule #5: "Already-installed dependency solves it?"
#
# This hook can refuse a command, so every failure path below allows it. A
# guard that blocks on its own parse error costs more than the install it was
# meant to catch.
#
# Input and output shapes differ per host, so both are emitted at once:
# Antigravity reads `.decision`; Claude Code and Codex read
# `.hookSpecificOutput.permissionDecision`, where the value is `ask`, not
# `force_ask`. Each host ignores the other's key.

allow() {
  printf '%s\n' '{"decision":"allow","hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
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
  printf '%s\n' "{\"decision\":\"force_ask\",\"reason\":\"$REASON\",\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"ask\",\"permissionDecisionReason\":\"$REASON\"}}"
  exit 0
fi

allow
