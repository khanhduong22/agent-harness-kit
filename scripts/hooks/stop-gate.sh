#!/bin/bash
# Stop hook: remind the agent to run verify-all before finishing.
# Only fires when MULTIPLE source files were modified but verification was not
# run. Does NOT fire for brainstorming, Q&A, or single-file edits.
#
# Host differences that matter here:
#
#   - Antigravity sends `terminationReason` and `executionNum`. The second is
#     what stops a blocking gate from looping: block, agent continues, stops
#     again, block again. Claude Code and Codex send neither.
#   - So this gate BLOCKS only on Antigravity, where the loop guard exists, and
#     is ADVISORY elsewhere — it surfaces the reminder through `systemMessage`,
#     which every host renders, and never holds the turn open. A gate that can
#     loop forever costs more than the verification run it was protecting.
#   - Transcript key and edit-record field are read through fallback chains.

PAYLOAD=$(cat)

allow() {
  printf '%s\n' '{"decision":"allow"}'
  exit 0
}

command -v jq >/dev/null 2>&1 || allow

TERMINATION_REASON=$(printf '%s' "$PAYLOAD" | jq -r '.terminationReason // empty' 2>/dev/null)
EXECUTION_NUM=$(printf '%s' "$PAYLOAD" | jq -r '.executionNum // empty' 2>/dev/null)
TRANSCRIPT_PATH=$(printf '%s' "$PAYLOAD" | jq -r '.transcript_path // .transcriptPath // empty' 2>/dev/null)

# Antigravity supplies a loop guard, so this gate may block there. Without it,
# stay advisory.
CAN_BLOCK=false
if [ -n "$EXECUTION_NUM" ]; then
  CAN_BLOCK=true
  # Only gate model-initiated stops (not errors, max_steps, etc.)
  [ "$TERMINATION_REASON" = "model_stop" ] || allow
  # Prevent infinite loops: only block on the first stop attempt
  [ "$EXECUTION_NUM" -gt 1 ] && allow
fi

# If no transcript available, allow
[ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ] || allow

# Count distinct source file modifications (only /src/ directory files).
# Threshold: >= 3 distinct edits indicates a build session, not brainstorming.
SRC_MOD_COUNT=$(grep -oE '"(TargetFile|file_path)"[^"]*"[^"]*\/src\/[^"]*"' "$TRANSCRIPT_PATH" 2>/dev/null | sort -u | wc -l | tr -d ' ')

# Below threshold → brainstorming or quick fix, let the agent stop
[ "$SRC_MOD_COUNT" -lt 3 ] && allow

# Significant source modifications detected — check whether verification ran.
# Tested with -q, not -c: `grep -c` exits 1 on a zero count, so the original
# `grep -c ... || echo 0` appended a second 0 and the numeric comparison below
# failed with "integer expression expected", falling through to allow. The gate
# could never fire.
if grep -qE '(verify-all|verify:all|bun run test\b|bun test\b)' "$TRANSCRIPT_PATH" 2>/dev/null; then
  allow
fi

REASON="⚠️ Pre-Ship Gate: ${SRC_MOD_COUNT} source files were modified but verify-all has not been run. Run \`bun run verify:all\` before completing this task, or explicitly confirm the skip."

if [ "$CAN_BLOCK" = true ]; then
  printf '%s\n' "{\"decision\":\"continue\",\"reason\":\"$REASON\",\"systemMessage\":\"$REASON\"}"
else
  printf '%s\n' "{\"systemMessage\":\"$REASON\"}"
fi
