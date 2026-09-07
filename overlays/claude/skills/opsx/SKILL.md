---
name: opsx
description: Create an OpenSpec change proposal (proposal.md, design.md, tasks.md, spec deltas) for a new feature or fix, following the repo's Gherkin spec standard. Use when the user wants to start planning a new change, asks for a spec, or invokes /opsx.
---

# OpenSpec Change Proposal

Phase 1 of the SDLC pipeline: `OPENSPEC (/opsx) → PLAN (/plan-sdlc) → BUILD (/build) → VERIFY (/test) → REVIEW (/review) → SHIP (/ship)`.

## Preconditions

1. Confirm the target repo actually uses OpenSpec: `ls openspec/` at the repo root. If it doesn't exist, ask whether to `openspec init` it or skip the openspec layer entirely for this task.
2. Check `openspec list` for an already-active change with an overlapping name or scope. If one exists and isn't yours, load the `parallel-worktree-isolation` skill before proceeding — don't silently start a second change in the same worktree.

## What to produce

Under `openspec/changes/<change-name>/`:

- **`proposal.md`** — `## Why` (the problem, in plain terms — keep it tight, long why-sections get flagged by `openspec validate`) and `## What Changes` (a bullet list of concrete deltas, one per capability/module touched).
- **`design.md`** — architectural decisions worth recording: a pros/cons table when there were 2+ real options, sequence/flow diagrams (Mermaid) for non-trivial interactions, and concrete interface/contract sketches (type signatures, function shapes) for anything Phase 2 (`/build`) will implement against.
- **`tasks.md`** — bite-sized checklist grouped into phases, each item starting `- [ ]`. This is what `/plan-sdlc` will expand on, and what `/build`/`/ship` check off and validate against. Don't write implementation code here — just the task list.
- **`specs/<capability>/spec.md`** — one file per capability this change touches, using strict Gherkin:

  ```markdown
  ## ADDED REQUIREMENTS   (or MODIFIED REQUIREMENTS / REMOVED REQUIREMENTS)

  ### Requirement: <Title>
  The system SHALL <capability statement>.

  #### Scenario: <Descriptive title>
  - **GIVEN** <initial context>
  - **WHEN** <event / API call>
  - **THEN** <expected outcome>
  - **AND** <additional constraint, optional>
  ```

  For a `MODIFIED` delta, the `### Requirement:` header text must match an existing header in `openspec/specs/<capability>/spec.md` **exactly** — `openspec archive` diffs by header string. Check with `grep -n "^### Requirement" openspec/specs/<capability>/spec.md` before writing the delta, don't invent a merged/renamed title.

## After writing

Run `openspec validate <change-name>` and fix anything it flags before considering this phase done.

## Gate

Per the SDLC pipeline's mandatory stop-between-phases rule: present the proposal and stop for approval before moving to `/plan-sdlc`, unless the user has explicitly asked for an autonomous end-to-end run.
