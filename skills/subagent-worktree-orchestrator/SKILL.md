---
name: subagent-worktree-orchestrator
description: "Orchestrates parallel subagent swarms and isolated Git worktrees across multi-domain or fullstack tasks (Spec, FE, BE, DevOps, QA). Use when running parallel subagents in a single batch call, isolating concurrent change streams in ~/.agent-worktrees, or coordinating FE + BE services via durable OpenSpec disk bridges. Triggers on 'parallel', 'ASAP', 'max speed', 'spawn subagents', 'split FE and BE', or 'worktree'."
---

# Subagent Swarm & Worktree Orchestrator

Defines the operational protocol for a **Master Agent** to dispatch concurrent, file-partitioned subagent swarms and isolate parallel multi-service (`FE + BE`) workstreams across Git worktrees without branch contamination or context loss.

---

## 1. Worktree Isolation Invariant

One worktree owns **one active objective, one branch, one OpenSpec change (if used), and one pull request**:
- **Same objective**: Continue in the current worktree.
- **Dependent change**: Stack from the prerequisite commit/branch explicitly and note the merge order in the PR.
- **Independent or cross-service change**: Isolate into `~/.agent-worktrees/<service>/<branch-slug>` before editing:
  ```bash
  git worktree add -b <branch-name> ~/.agent-worktrees/<service>/<branch-name> origin/develop
  ```

---

## 2. Single-Batch Swarm Decomposition & Model Tiering

When urgency is signaled (*"ASAP"*, *"parallel"*, *"max speed"*) or work spans separable domains, partition files strictly with **zero overlap** and dispatch all subagents concurrently in a **single batch `invoke_subagent` call**:

| Domain | Role Naming Standard | Scoped Work Boundary | Isolation Rule |
| :--- | :--- | :--- | :--- |
| **1. Spec & Contracts** | `[YYYY-MM-DD HH:mm \| #spec] <Topic> OpenSpec Architect` | `docs/`, `openspec/` | Never touch app source code. |
| **2. Backend & Data** | `[YYYY-MM-DD HH:mm \| #be] <Topic> Backend Specialist` | `apps/api/`, `packages/db/`, `packages/shared/` | Never touch frontend UI code. |
| **3. Frontend Client** | `[YYYY-MM-DD HH:mm \| #fe] <Topic> UI Specialist` | `apps/web/`, `apps/admin-spa/` | Never touch backend routes. |
| **4. DevOps & Infra** | `[YYYY-MM-DD HH:mm \| #devops] <Topic> Infra Specialist` | `Dockerfile*`, `docker-compose.yml`, `scripts/deploy*` | Never alter domain business logic. |
| **5. QA & E2E** | `[YYYY-MM-DD HH:mm \| #qa] <Topic> E2E Specialist` | `tests/`, `e2e/` | Never weaken production assertions to pass. |

- **Model Routing**:
  - `Model: "flash"` — Default for scoped FE UI, BE endpoints, unit/E2E tests, DevOps, lint/typecheck, and `gh run watch`.
  - `Model: "pro"` — Reserved strictly for shared core packages (`packages/*`), distributed concurrency/locking algorithms, or complex multi-service debugging.
  - `Model: "flash_lite"` — Lightweight read-only lookups or status checks.

---

## 3. The 3 Bridges of Cross-Service Context Preservation

Headless subagents do not share the Master Agent's in-memory conversation state. Guarantee contract parity via three durable disk bridges:

1. **Bridge 1 — Self-Contained Briefing Input**: Pass exact absolute worktree paths, OpenSpec artifact paths (`openspec/changes/<change-name>/{proposal,design,tasks}.md`), scoped checklist items, and exact verification commands. Never write *"the file we discussed"*.
2. **Bridge 2 — Durable Worktree Disk State**: Schemas, Prisma models, DTO contracts, and migrations live on disk inside `~/.agent-worktrees/<service>/<branch-slug>`.
3. **Bridge 3 — Structured Return Payload**: Subagents return modified file paths, exact test pass/fail counts, and commit hashes (`git diff` and test exit codes are verified on disk by the Master Agent before claiming completion).

---

## 4. Cross-Verification & Browser E2E Video Gate

1. **Contract Parity Check**: Verify backend response envelopes (`{ data, meta }`) match frontend TypeScript types/schemas and confirm unit/integration builds pass across all touched worktrees (`bun test`, `bun run test:postman`, `tsc --noEmit`, `bun run build`).
2. **Fullstack Browser E2E Gate**: Where UI or UI-impacting backend behavior changed, run recorded Playwright E2E verification against the live stack per [`playwright-e2e-testing`](../playwright-e2e-testing/SKILL.md) (`npx playwright test`, upload recording via `./scripts/upload-e2e-video.sh`, and embed the shareable URL in the consolidated handover).
