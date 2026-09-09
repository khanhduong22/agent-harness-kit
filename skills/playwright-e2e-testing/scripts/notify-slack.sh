#!/usr/bin/env bash
set -euo pipefail

WEBHOOK_URL="https://hooks.slack.com/services/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"

TASK_NAME="${1:-Task Completed}"
PR_URL="${2:-}"
DETAILS="${3:-All tests passed, typecheck clean}"
VIDEO_URL="${4:-}"
ISSUE_INFO="${5:-}"
FLOW_STEPS="${6:-}"

python3 -c '
import sys, json, urllib.request

webhook_url = sys.argv[1]
task_name = sys.argv[2]
pr_url = sys.argv[3]
details = sys.argv[4]
video_url = sys.argv[5]
issue_info = sys.argv[6]
flow_steps = sys.argv[7]

lines = []
if issue_info:
    lines.append(f"📌 *Issue*: {issue_info}")
lines.append(f"✅ *Task Completed*: {task_name}")

if pr_url:
    lines.append(f"• 🔗 *PR*: <{pr_url}|{pr_url}>")

if video_url:
    lines.append(f"• 🎬 *E2E Test Video*: <{video_url}|Xem video kiểm thử trên Google Drive>")

if flow_steps:
    lines.append("• 📋 *Flow Test / Điểm cần xem trong Video*:")
    for step in flow_steps.strip().split("\n"):
        if step.strip():
            lines.append(f"  {step.strip()}")

lines.append(f"• 📊 *Status*: {details}")
lines.append("• 🚀 *Đã sẵn sàng để bro review!*")

payload = {"text": "\n".join(lines)}

req = urllib.request.Request(
    webhook_url,
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)
with urllib.request.urlopen(req) as resp:
    pass

print("Notification sent to Slack successfully.")
' "$WEBHOOK_URL" "$TASK_NAME" "$PR_URL" "$DETAILS" "$VIDEO_URL" "$ISSUE_INFO" "$FLOW_STEPS"
