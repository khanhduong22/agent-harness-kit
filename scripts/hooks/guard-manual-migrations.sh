#!/bin/bash
# PreToolUse hook: guard against manual Prisma migration creation.
# Enforces the prisma-safe-migration skill rule:
# "NEVER create manual migration folders or manually constructed .sql files inside migrations/"
# Migrations MUST be generated via the Prisma CLI:
#   bun prisma migrate dev --create-only --name <name>

allow() {
  printf '%s\n' '{"decision":"allow","hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow"}}'
  exit 0
}

deny() {
  local reason="$1"
  printf '%s\n' "{\"decision\":\"deny\",\"reason\":\"$reason\",\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"$reason\"}}"
  exit 0
}

PAYLOAD=$(cat) || allow

command -v jq >/dev/null 2>&1 || allow

WORKSPACE_DIR=$(printf '%s' "$PAYLOAD" | jq -r '.cwd // .workspacePaths[0] // empty' 2>/dev/null)
[ -n "$WORKSPACE_DIR" ] || WORKSPACE_DIR="$(pwd)"

TARGET_FILE=$(printf '%s' "$PAYLOAD" | jq -r '.tool_input.file_path // .toolCall.args.TargetFile // empty' 2>/dev/null)
CMD=$(printf '%s' "$PAYLOAD" | jq -r '.tool_input.command // .toolCall.args.CommandLine // empty' 2>/dev/null)

REASON='🚫 Manual Prisma Migration Blocked: Do NOT manually create migration files or directories in migrations/. You MUST generate migrations using Prisma CLI: bun prisma migrate dev --create-only --name <name> (Refer to prisma-safe-migration skill).'

# 1. Check Write / write_to_file tool targeting a migration file
if [ -n "$TARGET_FILE" ]; then
  case "$TARGET_FILE" in
    */migrations/*/*.sql)
      # Resolve absolute path if relative
      case "$TARGET_FILE" in
        /*) FULL_PATH="$TARGET_FILE" ;;
        *) FULL_PATH="$WORKSPACE_DIR/$TARGET_FILE" ;;
      esac
      # If the file does NOT exist on disk yet, it is a manual creation attempt!
      if [ ! -f "$FULL_PATH" ]; then
        deny "$REASON"
      fi
      ;;
  esac
fi

# 2. Check Bash / run_command tool attempting manual migration creation
if [ -n "$CMD" ]; then
  # Allow genuine prisma CLI commands
  if echo "$CMD" | grep -qE '\bprisma\s+migrate\b'; then
    allow
  fi

  # Block mkdir creating migration folders
  if echo "$CMD" | grep -qE '\bmkdir\b.*migrations/'; then
    deny "$REASON"
  fi

  # Block shell redirections creating migration files: > .../migrations/.../*.sql
  if echo "$CMD" | grep -qE '(>|tee)\s*.*migrations/.*\.sql'; then
    deny "$REASON"
  fi

  # Block touch creating migration files in migrations/
  if echo "$CMD" | grep -qE '\btouch\b.*migrations/.*\.sql'; then
    deny "$REASON"
  fi
fi

allow
