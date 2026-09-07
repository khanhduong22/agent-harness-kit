---
name: plan-sdlc
description: Break an OpenSpec change (or any non-trivial task) into a bite-sized, phase-ordered task checklist in tasks.md. Use after /opsx, or whenever the user asks to plan/break down work before coding. Named plan-sdlc (not plan) because /plan is Claude Code's own reserved plan-mode command.
---

# SDLC Task Planning

Phase 2 of the pipeline: `OPENSPEC (/opsx) → PLAN (/plan-sdlc) → BUILD (/build) → VERIFY (/test) → REVIEW (/review) → SHIP (/ship)`.

Note the name: this is deliberately **not** `/plan` — that's Claude Code's built-in plan-mode command (`EnterPlanMode`) and can't be shadowed by a custom skill. If the user says "plan this" in an SDLC context, this skill is what they mean; if they want Claude Code's native plan mode instead, use `EnterPlanMode`.

## What this produces

`openspec/changes/<change-name>/tasks.md` (or, if there's no active OpenSpec change, a plain task list in the response) organized into phases matching the natural build order — e.g. types/contracts first, then orchestration, then service wiring, then verification. Each task:

- Starts `- [ ]`, is scoped to roughly one sitting's worth of work, and names the concrete file(s) it touches.
- Is TDD-shaped where it makes sense: a task to write the failing test, a task to make it pass — don't collapse both into one line if the work is non-trivial.
- Ends with a **Verification** phase whose tasks are the actual commands to run (`bun test`, `npx tsc --noEmit`, the project's e2e suite, `bun run build`) — not vague "test everything" items.

## Before writing

1. Read `design.md` (if this follows `/opsx`) for the interfaces/contracts already decided — the task list should implement *that* design, not re-derive it.
2. Grep the codebase for existing helpers, patterns, and conventions the tasks should reuse rather than reinvent (repo's own "lazy senior dev" rule: don't write a task for something that's a few files over already).

## Gate

Stop and show the task list for approval before moving to `/build`, unless the user has asked for an autonomous run.
