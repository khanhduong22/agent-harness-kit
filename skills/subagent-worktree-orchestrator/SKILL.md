---
name: subagent-worktree-orchestrator
description: Orchestrates autonomous multi-agent delegation across split Git worktrees for fullstack tasks (FE + BE). Preserves context via durable OpenSpec artifacts and disk state, verifies integration via browser E2E video recording, and delivers a consolidated result.
---

# Subagent Worktree Orchestrator

This skill defines the operational protocol for a Master Agent to orchestrate sub-agents across multiple repositories/services in parallel Git worktrees for fullstack features (Frontend + Backend), without context loss or conversation bloat.

---

## 1. When to Use

- When a feature spans multiple services (e.g. Backend API service + Frontend Client Web or Admin CMS).
- When a task involves both Frontend and Backend changes that should progress in parallel rather than serialized waiting.
- When working on independent worktrees to prevent branch contamination and dirty working directories.
- When the user asks to "run in parallel", "split FE and BE", or "orchestrate subagents".

---

## 2. The 3 Bridges of Context Preservation

Sub-agents run in separate execution contexts and do not share the master session's in-memory KV cache. To guarantee 100% alignment without context drift:

```
[Master Agent]
      │
      ▼  Bridge 1: Structured Briefing + Spec Pointer (Input)
[OpenSpec Artifacts (Disk: proposal.md / design.md / tasks.md / Gherkin specs)]
      │
      ▼  Bridge 2: Shared Git Worktree State (Disk: schema, DTOs, code)
[Headless Sub-Agents (Backend Subagent & Frontend Subagent)]
      │
      ▼  Bridge 3: Structured Return Payload (Stdout: files, test output, commit hash)
[Master Agent absorbs & cross-verifies contracts]
```

1. **Bridge 1 (Briefing Input)**: Never invoke sub-agents with vague instructions. Always pass:
   - Target worktree path (`--cwd` or explicit path).
   - Exact OpenSpec proposal/design file path.
   - Specific task items from `tasks.md`.
   - Mandatory verification commands and expected evidence format.
2. **Bridge 2 (Durable Disk State)**: All state (Prisma models, DTO files, migrations, component props) lives on disk inside the isolated worktree (`~/.agent-worktrees/<service>/<branch-slug>`).
3. **Bridge 3 (Structured Return)**: Sub-agents run non-interactively and return their structured summary (modified files, passing test counts, commit hash) directly to the master agent.

---

## 3. Execution Workflow

### Step 1: Worktree Isolation
Create or reuse a clean, isolated worktree per service before launching sub-agents:
```bash
git worktree add -b <branch-name> ~/.agent-worktrees/<service>/<branch-name> origin/develop
```

### Step 2: Establish the Contract (OpenSpec)
Create the OpenSpec change proposal in the target repository (`openspec/changes/<change-name>/`):
- `proposal.md`: Problem statement, affected users, and user-visible success criteria.
- `design.md`: Architecture decisions, DTO contracts, request/response schemas, and Mermaid sequence flow.
- `specs/<capability>/spec.md`: Gherkin delta scenarios (`GIVEN / WHEN / THEN / AND`).
- `tasks.md`: Implementation checklist partitioned into Backend and Frontend phases.

### Step 3: Concurrent Sub-Agent Delegation
Dispatch sub-agents concurrently to work in their respective worktrees. Use whichever subagent CLI or agent runner is available in the environment (e.g. `agy -p`, `claude -p`, or native subagents):

```bash
# Backend Subagent: Implement API, DB, and Business Logic
<agent-cli> -p \
  "CONTEXT: Worktree at ~/.agent-worktrees/<backend-service>/<branch-name>
   SPEC: Read openspec/changes/<change-name>/design.md
   TASK: Implement Backend tasks in tasks.md (schema, migrations, DTOs, endpoints).
   VERIFY: Run unit and integration tests ('bun test', 'bun run test:postman').
   OUTPUT: Return modified files, test passing count, and commit hash."

# Frontend Subagent: Implement UI Components, Forms, and State
<agent-cli> -p \
  "CONTEXT: Worktree at ~/.agent-worktrees/<frontend-service>/<branch-name>
   CONTRACT: Align with backend DTOs & design in openspec/changes/<change-name>/design.md
   TASK: Implement Frontend tasks in tasks.md (components, forms, API integration).
   VERIFY: Run typecheck and build ('tsc --noEmit', 'bun run build').
   OUTPUT: Return modified files, build status, and commit hash."
```

Both sub-agents execute in parallel, writing code and running domain verification in their isolated worktrees.

### Step 4: Cross-Verification & Browser E2E Video Gate
Once sub-agents complete their initial tasks, the master agent (or a dedicated E2E verification subagent) MUST verify integration end-to-end:

1. **Schema & DTO Contract Parity**:
   - Compare backend response envelopes against frontend TypeScript types to ensure zero contract mismatch.
   - Verify unit test and build passing status across both services.

2. **Run Playwright E2E Suite with Video Recording**:
   - Cross-worktree fullstack verification is not complete until the UI interacts with the live backend in a real browser session.
   - Execute the browser E2E test suite with video recording enabled (see `playwright-e2e-testing` skill):
     ```bash
     cd ~/.agent-worktrees/<frontend-service>/<branch-name>
     npx playwright test e2e/specs/<domain>/<feature>.spec.ts
     ```
   - **In-Video Visual Telemetry Standard**:
     - Inject floating step banners (`showStepBanner`) at top-center with a 1.5s visual pause between key actions.
     - Inject full-screen audit summary modal (`showSummaryModal`) displaying `✓ 100% VERIFIED` status, database records, and delivery channel statuses for 4.5s before teardown.
   - **Closed-Loop Downstream Verification**:
     - Verify full CRUD lifecycle and downstream side-effects (e.g. Mailpit email, in-app notification bells, public feed reflections) without mocking.

3. **Upload Recording & Obtain Shareable Link**:
   - Upload the recording to cloud storage:
     ```bash
     ./scripts/upload-e2e-video.sh <path-to-video.webm> "<Task-Name>"
     ```
   - Capture the active shareable Google Drive / cloud URL.
   - **Blocking Gate**: A fullstack task CANNOT be handed over without an active, shareable E2E video recording URL proving runtime integration.

### Step 5: Consolidated User Delivery
Do NOT spam the user with raw sub-agent terminal logs or intermediate chatter. Deliver a single high-level report containing:
- **Executive Summary**: Clear breakdown of what was implemented in Frontend and Backend.
- **E2E Video Recording**: Shareable link to the verified video recording demonstrating the live feature.
- **Service PR / Branch Links**: Clickable PR links or branch refs for each service repository.
- **Verification Matrix**: Passing status of Unit tests, Integration tests, and Playwright E2E scenarios.
- **Optional Slack Notification**: Trigger `./scripts/notify-slack.sh` with the PR link and video URL.
