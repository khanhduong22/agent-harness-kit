#!/bin/bash
# PostToolUse hook: run ESLint & SonarQube lint --fix after file edits.
#
# Hosts send different payload shapes for the same fact, so each field is read
# through a fallback chain: Claude Code and Codex send `cwd`, Antigravity sends
# `workspacePaths`. Adding a host means adding one more `//` term.

# Read JSON payload from stdin
PAYLOAD=$(cat)

# Navigate to project workspace root.
if command -v jq >/dev/null 2>&1; then
  WORKSPACE_DIR=$(printf '%s' "$PAYLOAD" | jq -r '.cwd // .workspacePaths[0] // empty')
else
  WORKSPACE_DIR=""
  echo "[Lint Hook] WARNING: jq not found; falling back to current directory" >&2
fi

if [ -z "$WORKSPACE_DIR" ]; then
  WORKSPACE_DIR="$(pwd)"
fi

LINT_STATUS=0

# Run lint --fix in index-api (includes eslint-plugin-sonarjs)
if [ -d "$WORKSPACE_DIR/index-api" ]; then
  if (
    cd "$WORKSPACE_DIR/index-api" || exit 1
    if command -v bun >/dev/null 2>&1; then
      echo "[Lint Hook] Running lint in index-api..." >&2
      bun run lint >&2
    else
      echo "[Lint Hook] WARNING: bun not found, skipping lint" >&2
    fi
  ); then
    LINT_STATUS=0
  else
    LINT_STATUS=$?
  fi
elif [ -f "$WORKSPACE_DIR/package.json" ]; then
  if (
    cd "$WORKSPACE_DIR" || exit 1
    if command -v bun >/dev/null 2>&1; then
      echo "[Lint Hook] Running lint in $WORKSPACE_DIR..." >&2
      bun run lint >&2
    else
      echo "[Lint Hook] WARNING: bun not found, skipping lint" >&2
    fi
  ); then
    LINT_STATUS=0
  else
    LINT_STATUS=$?
  fi
fi

if [ $LINT_STATUS -ne 0 ]; then
  echo "[Lint Hook] ⚠️ Linting completed with warnings/errors (exit code: $LINT_STATUS)" >&2
else
  echo "[Lint Hook] ✓ Linting passed" >&2
fi

# Return required empty JSON object to stdout
echo "{}"
exit "$LINT_STATUS"
