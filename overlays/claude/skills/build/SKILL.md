---
name: build
description: Execute an OpenSpec change's tasks.md checklist task-by-task, checking each item off as it's completed. Use when the user says to start/continue coding a planned change, or invokes /build (optionally "/build auto" for autonomous execution).
---

# Incremental Implementation

Phase 3 of the pipeline: `OPENSPEC (/opsx) → PLAN (/plan-sdlc) → BUILD (/build) → VERIFY (/test) → REVIEW (/review) → SHIP (/ship)`.

## Before starting

1. Load `openspec/changes/<change-name>/tasks.md` and `design.md`. If neither exists, there's nothing to execute against `/build` mode — fall back to a normal implementation conversation instead of pretending there's a checklist.
2. Check `git status` and the current branch against `parallel-worktree-isolation`'s classification — confirm this worktree is actually assigned to this change before editing.

## Execution loop

For each unchecked task, in order:

1. Implement it — reuse existing helpers/types/patterns before writing new ones (the codebase's "7-rung ladder": does this need to exist, is it already here, does stdlib/a native feature/an installed dep already solve it, before writing new code).
2. If the task is a test-first pair (write failing test → make it pass), actually run the test in between so "red" is confirmed before writing the fix, not just implied.
3. Mark the task `- [x]` in `tasks.md` and, if the task's real-world outcome differs from what was originally written (a design assumption turned out wrong, a field didn't exist, an extra fix was needed), edit the task line to say what actually happened — don't leave a stale description next to a checked box.
4. Move to the next task. Don't batch unrelated tasks into one commit-worthy chunk if they're independently useful checkpoints — but do keep momentum; this loop isn't a stop-and-ask-every-task exercise.

## Mid-flight discoveries

If implementing a task reveals a bug, gap, or missing scenario the plan didn't anticipate (a real vulnerability, a missing check, scattered logic that should route through something you're already centralizing): fix it if it's in the same objective, add a task for it, and note it in the final summary — don't silently skip it, and don't silently expand scope into a genuinely different objective without flagging it first.

## `/build auto`

Only run the entire remaining checklist through to `/test` without stopping for per-phase approval when the user explicitly asked for autonomous execution (`/build auto`, "chạy hết đến phase cuối", "tự động làm từ A đến Z", or equivalent). Otherwise stop after `/build` for confirmation before `/test`.
