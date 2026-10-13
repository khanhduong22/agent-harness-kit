#!/bin/bash
# PreCompact hook: preserve session state before context compaction.
# Inspired by affaan-m/ECC state preservation lifecycle.
#
# Extracts in-progress goals, pending tasks, and git worktree status
# into .agents/context/session-handoff.md so the agent can seamlessly
# resume work after context window compaction.
#
# Host compatibility:
#   Claude Code sends: session_id, transcript_path, cwd, trigger ("manual"|"auto").
#   Codex / Antigravity send similar JSON payloads or commandline invocations.
#   All failure paths exit 0 with {} to prevent breaking compaction.

allow() {
  printf '%s\n' '{}'
  exit 0
}

PAYLOAD=$(cat) || allow

command -v jq >/dev/null 2>&1 || allow

# 1. Resolve workspace root
WORKSPACE_DIR=$(printf '%s' "$PAYLOAD" | jq -r '.cwd // .workspacePaths[0] // empty' 2>/dev/null)
[ -n "$WORKSPACE_DIR" ] || WORKSPACE_DIR="$(pwd)"

# 2. Extract metadata
SESSION_ID=$(printf '%s' "$PAYLOAD" | jq -r '.session_id // .sessionId // empty' 2>/dev/null)
TRIGGER=$(printf '%s' "$PAYLOAD" | jq -r '.trigger // "auto"' 2>/dev/null)
TRANSCRIPT_PATH=$(printf '%s' "$PAYLOAD" | jq -r '.transcript_path // .transcriptPath // empty' 2>/dev/null)

# 3. Extract git status and branch
GIT_BRANCH="unknown"
GIT_STATUS=""
if git -C "$WORKSPACE_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  GIT_BRANCH=$(git -C "$WORKSPACE_DIR" branch --show-current 2>/dev/null || echo "detached")
  GIT_STATUS=$(git -C "$WORKSPACE_DIR" status --short 2>/dev/null)
fi

# 4. Extract active goal or recent prompt
LAST_USER_PROMPT=""
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
  # Parse latest user message from transcript JSONL
  LAST_USER_PROMPT=$(jq -r 'select(.type=="user" or .role=="user") | (.text // .content // .message.content // empty) | if type=="array" then .[] | select(.type=="text") | .text else . end' "$TRANSCRIPT_PATH" 2>/dev/null | tail -n 1)
fi
if [ -z "$LAST_USER_PROMPT" ]; then
  LAST_USER_PROMPT=$(printf '%s' "$PAYLOAD" | jq -r '.goal // .prompt // .user_prompt // empty' 2>/dev/null)
fi
[ -n "$LAST_USER_PROMPT" ] || LAST_USER_PROMPT="No explicit user goal captured in payload."

# 5. Extract active or pending tasks from workspace
ACTIVE_TASKS=""
# Search OpenSpec changes for incomplete tasks
if [ -d "$WORKSPACE_DIR/openspec/changes" ]; then
  for task_file in "$WORKSPACE_DIR"/openspec/changes/*/tasks.md; do
    if [ -f "$task_file" ]; then
      change_name=$(basename "$(dirname "$task_file")")
      incomplete=$(grep -E '^\s*-\s*\[ \]' "$task_file" 2>/dev/null | head -n 10 || true)
      if [ -n "$incomplete" ]; then
        ACTIVE_TASKS="${ACTIVE_TASKS}### OpenSpec Change: ${change_name}\n${incomplete}\n\n"
      fi
    fi
  done
fi

# Search root tasks.md or .agents/tasks.md
for root_task in "$WORKSPACE_DIR/tasks.md" "$WORKSPACE_DIR/.agents/tasks.md"; do
  if [ -f "$root_task" ]; then
    incomplete=$(grep -E '^\s*-\s*\[ \]' "$root_task" 2>/dev/null | head -n 15 || true)
    if [ -n "$incomplete" ]; then
      ACTIVE_TASKS="${ACTIVE_TASKS}### $(basename "$root_task")\n${incomplete}\n\n"
    fi
  fi
done

[ -n "$ACTIVE_TASKS" ] || ACTIVE_TASKS="No pending markdown task checklists found in workspace."

# 6. Prepare output handoff file
HANDOFF_DIR="$WORKSPACE_DIR/.agents/context"
mkdir -p "$HANDOFF_DIR" 2>/dev/null || allow
HANDOFF_FILE="$HANDOFF_DIR/session-handoff.md"
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M:%S UTC")

cat <<EOF > "$HANDOFF_FILE"
# Pre-Compaction Session Handoff Snapshot

> Generated automatically by \`pre-compact-dump.sh\` before context window compaction.
> Compaction Trigger: ${TRIGGER} | Timestamp: ${TIMESTAMP}

## Session Metadata
- **Session ID**: ${SESSION_ID:-unknown}
- **Workspace**: ${WORKSPACE_DIR}
- **Git Branch**: ${GIT_BRANCH}

## Active Goal & Objective
${LAST_USER_PROMPT}

## Pending Tasks Checklist
$(printf '%b' "$ACTIVE_TASKS")

## Modified & Untracked Files (\`git status --short\`)
\`\`\`
${GIT_STATUS:-Clean worktree (no uncommitted changes)}
\`\`\`

## Recovery Instructions for Post-Compaction Agent
1. Read this file (\`.agents/context/session-handoff.md\`) immediately after compaction to restore objective and context.
2. Confirm current git status against modified files listed above before making new edits.
3. Resume execution from the pending tasks checklist.
EOF

REASON="💾 Session state preserved before compaction: .agents/context/session-handoff.md"
printf '%s\n' "{\"systemMessage\":\"$REASON\"}"
exit 0
