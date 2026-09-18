#!/bin/bash
# PostToolUse hook: regenerate the Prisma client for the edited schema's project.
#
# Each field is read through a fallback chain so one script serves every host:
# Claude Code and Codex send `tool_input.file_path` and `cwd`, Antigravity sends
# `toolCall.args.TargetFile` and `workspacePaths`.

# Read JSON payload from stdin
PAYLOAD=$(cat)

finish() {
  local status=${1:-0}
  echo "{}"
  exit "$status"
}

if ! command -v jq >/dev/null 2>&1; then
  echo "[Prisma Hook] ERROR: jq is required to parse the hook payload." >&2
  finish 1
fi

# Extract workspace root and the file changed by the edit tool.
WORKSPACE_DIR=$(printf '%s' "$PAYLOAD" | jq -r '.cwd // .workspacePaths[0] // empty' 2>/dev/null)
TARGET_FILE=$(printf '%s' "$PAYLOAD" | jq -r '.tool_input.file_path // .toolCall.args.TargetFile // empty' 2>/dev/null)

if [ -z "$WORKSPACE_DIR" ]; then
  WORKSPACE_DIR="$(pwd)"
fi

# PostToolUse payloads for unrelated edits, and lifecycle hooks without a
# TargetFile, must not trigger generation.
case "$TARGET_FILE" in
  *.prisma) ;;
  *) finish 0 ;;
esac

case "$TARGET_FILE" in
  /*) ;;
  *) TARGET_FILE="$WORKSPACE_DIR/$TARGET_FILE" ;;
esac

# Find the nearest package root so schemas in index-api and index-data run the
# correct project's generate script.
PROJECT_DIR=$(dirname "$TARGET_FILE")
while [ "$PROJECT_DIR" != "/" ] && [ ! -f "$PROJECT_DIR/package.json" ]; do
  PROJECT_DIR=$(dirname "$PROJECT_DIR")
done

if [ ! -f "$PROJECT_DIR/package.json" ]; then
  echo "[Prisma Hook] WARNING: no package.json found for $TARGET_FILE; skipping generation." >&2
  finish 0
fi

echo "[Prisma Hook] Detected edited schema: $TARGET_FILE" >&2
echo "[Prisma Hook] Schema changed. Generate migrations via: 'bun prisma migrate dev --create-only --name <name>' (refer to prisma-safe-migration skill)." >&2

if ! command -v bun >/dev/null 2>&1; then
  echo "[Prisma Hook] ERROR: bun not found. Cannot generate Prisma client." >&2
  finish 1
fi

echo "[Prisma Hook] Running 'bun run generate' in $PROJECT_DIR..." >&2
GENERATE_STATUS=0
(
  cd "$PROJECT_DIR" || exit 1
  bun run generate >&2
) || GENERATE_STATUS=$?

if [ "$GENERATE_STATUS" -ne 0 ]; then
  echo "[Prisma Hook] ERROR: Failed to regenerate Prisma client. Fix the schema errors and try again." >&2
else
  echo "[Prisma Hook] ✓ Prisma client types regenerated successfully." >&2
fi

finish "$GENERATE_STATUS"
