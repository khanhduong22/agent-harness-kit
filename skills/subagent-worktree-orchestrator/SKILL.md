---
name: subagent-worktree-orchestrator
description: >-
  Orchestrates autonomous multi-agent delegation across split Git worktrees (e.g.
  Frontend in index-admin-cms and Backend in index-api). Preserves context across
  agents via durable OpenSpec artifacts and disk state instead of chat memory,
  invokes headless CLI agents (agy or claude), and yields only the unified final result.
---

# Subagent Worktree Orchestrator

This skill defines the operational protocol for a Master Agent session to orchestrate
sub-agents across multiple repositories/services in parallel Git worktrees without
context loss or conversation bloat.

---

## 1. When to Use

- When a feature spans multiple services (e.g., Backend `index-api` + Admin CMS `index-admin-cms` + Client Web `index-web`).
- When a task requires deep concurrent engineering (e.g., implementing DB migrations & REST APIs while building multi-screen UI).
- When a conversation approaches context saturation (>100k tokens) and sub-tasks should be delegated to fresh agent sessions.
- When the user asks to "run in parallel", "split FE/BE", or "orchestrate subagents".

---

## 2. The 3 Bridges of Context Preservation

Sub-agents (whether `claude` or `agy`) do not share the master session's in-memory KV cache.
To guarantee 100% context alignment without context rot:

```
[Master Agent]
      │
      ▼  Bridge 1: Structured Briefing + Spec Pointer (Input)
[OpenSpec Artifacts (Disk: proposal.md / design.md / tasks.md / Gherkin specs)]
      │
      ▼  Bridge 2: Shared Git Worktree State (Disk: schema, DTOs, code)
[Headless Sub-Agent CLI (`claude -p` / `agy -p`)]
      │
      ▼  Bridge 3: Structured Return Payload (Stdout: files, test output, commit hash)
[Master Agent absorbs & cross-verifies contracts]
```

1. **Bridge 1 (Briefing Input)**: Never invoke sub-agents with vague instructions. Always pass:
   - Target worktree path (`--cwd` or explicit path).
   - Exact OpenSpec proposal/design file path.
   - Specific task numbers from `tasks.md`.
   - Mandatory verification commands and expected evidence format.
2. **Bridge 2 (Durable Disk State)**: All state (Prisma models, DTO files, migrations, component props) lives on disk inside the isolated worktree (`~/.agent-worktrees/<repo>/<branch-slug>`).
3. **Bridge 3 (Structured Return)**: Sub-agents run non-interactively (`-p`) and return their summary directly to the master agent's context.

---

## 3. Execution Workflow

### Step 1: Worktree Isolation
Create or reuse a clean worktree per service before launching sub-agents:
```bash
git worktree add -b <branch-name> ~/.agent-worktrees/<service>/<branch-name> origin/develop
```

### Step 2: Establish the Contract (OpenSpec)
Create the OpenSpec change proposal in the target repository:
- `openspec/changes/<change-name>/proposal.md`
- `openspec/changes/<change-name>/design.md` (with DTO contracts & Mermaid flow)
- `openspec/changes/<change-name>/specs/<capability>/spec.md` (Gherkin delta)
- `openspec/changes/<change-name>/tasks.md`

### Step 3: Sub-Agent Delegation Matrix
Select the optimal CLI engine based on the domain:

| Seat | CLI Command | Model | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| **Architect / BE Worker** | `claude -p --model claude-fable-5` | Claude Fable / Opus | NestJS modules, Prisma migrations, complex algorithms, business logic |
| **Auditor / FE Worker** | `agy -p --model gemini-2.5-pro` | Gemini Pro | React/Vite UI, Strapi plugins, styling, verification, fact-checking |

#### Example Headless Invocations:
```bash
# Invoking Claude for Backend in dedicated worktree
claude -p \
  --output-format text \
  "CONTEXT: Worktree at ~/.agent-worktrees/index-api/feature-group-rules
   SPEC: Read openspec/changes/group-rules/design.md
   TASK: Implement tasks 1 to 4 in tasks.md.
   VERIFY: Run 'bun test' and 'bun run test:postman'.
   REQUIREMENT: Return modified file list and passing test counts."

# Invoking AGY for Frontend in dedicated worktree
agy -p \
  --model gemini-2.5-pro \
  "CONTEXT: Worktree at ~/.agent-worktrees/index-admin-cms/feature-group-admin-ui
   CONTRACT: Align with backend DTOs in ~/.agent-worktrees/index-api/feature-group-rules/...
   TASK: Implement UI components and hook matching Figma specs.
   VERIFY: Run 'tsc --noEmit -p admin/tsconfig.json' and 'strapi-plugin build'."
```

### Step 4: Cross-Verification
Before completing the orchestration, the master agent verifies:
1. **Schema & DTO Parity**: Compare backend response envelopes against frontend TypeScript types.
2. **Runtime Verification**: Verify unit tests and Newman integration test logs.
3. **OpenSpec Consistency**: Ensure all Gherkin scenarios are mapped to tests.

### Step 5: Consolidated User Delivery
Do NOT spam the user with raw sub-agent logs. Deliver a single high-level report containing:
- Summary of FE and BE implementations.
- Clickable PR links for each service.
- Verification matrix (test counts, build status).
