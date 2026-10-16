---
name: maximum-parallel-subagents
description: Operational protocol for maximum-speed parallel subagent swarms. Decomposes complex multi-faceted tasks into isolated, non-overlapping work streams (Spec, Frontend, Backend, DevOps, QA) and dispatches them concurrently in a single batch tool call.
---

# ⚡ Maximum Parallel Subagents & Swarm Orchestration

This skill guides the **Master Agent** in orchestrating maximum-concurrency subagent swarms when speed is the primary objective or when multi-faceted tasks span several separable domains.

> [!IMPORTANT]
> **Core Principle: Speed Over Token Conservation**
> - When the maintainer requests speed (*"ASAP"*, *"spawn maximum sub agent"*, *"nhanh nhất"*, *"max speed"*, *"parallel"*), token pinching is explicitly forbidden.
> - Do NOT perform serial back-and-forth turns when tasks can be cleanly partitioned into concurrent streams.
> - Dispatch the entire swarm in a **single batch `invoke_subagent` call**.

---

## 1. When to Use This Skill
- User explicitly triggers high-velocity / parallel execution.
- Complex feature delivery or new product prototypes spanning:
  1. **Specification & Architecture** (SRS, OpenSpec, Mermaid diagrams, API contracts)
  2. **Backend Services & Data Foundation** (Prisma models, seed telemetry, REST/GraphQL endpoints)
  3. **Frontend Client Applications** (SPAs, PWAs, views, state management, design tokens)
  4. **DevOps & Infrastructure** (Dockerfiles, Docker Compose, Nginx, deployment scripts, CI/CD)
  5. **Verification & QA** (End-to-end user journey simulation, contract parity tests, performance benchmarks)

---

## 2. The 5-Domain Swarm Decomposition Matrix
Before calling `invoke_subagent`, the Master Agent must strictly partition the target workspace into independent, non-overlapping boundaries:

| Domain | Role Naming Standard | Scoped Work Boundary | Strict Isolation Boundary |
| :--- | :--- | :--- | :--- |
| **1. Spec & Architecture** | `[YYYY-MM-DD HH:mm \| #spec] <Topic> OpenSpec Architect` | `docs/`, `openspec/`, `README.md` | Must NOT touch application source code. |
| **2. Backend & Data** | `[YYYY-MM-DD HH:mm \| #be] <Topic> Backend Specialist` | `apps/api/`, `packages/db/`, `packages/shared/` | Must NOT touch frontend client code. |
| **3. Frontend Client** | `[YYYY-MM-DD HH:mm \| #fe] <Topic> UI Specialist` | `apps/web/`, `apps/admin-spa/`, `apps/staff-pwa/` | Must NOT touch backend server routes. |
| **4. DevOps & Infra** | `[YYYY-MM-DD HH:mm \| #devops] <Topic> Deployment Specialist` | `Dockerfile*`, `docker-compose.yml`, `scripts/deploy*` | Must NOT modify core application business logic. |
| **5. QA & Simulation** | `[YYYY-MM-DD HH:mm \| #qa] <Topic> E2E Verification Specialist` | `tests/`, `e2e/`, test scripts in `package.json` | Must NOT alter production logic to make tests pass. |

---

## 3. Single-Batch Dispatch Pattern & Model Tiering
- **Master Agent**: Runs on **Argon 4 High** (`pro` High).
- **Standard Execution Subagents (`Model: "flash"` — Flash 3.8 High)**: Default for Frontend UI, scoped Backend routes, DevOps/CI monitoring, QA/E2E tests, and docs. Do **NOT** leave `Model` as `"inherit"` (Argon 4) for standard subagents.
- **Complex Architecture Subagents (`Model: "pro"` — Argon 4 High)**: Reserved only for deep system design, reusable core packages (`packages/*`), or intricate concurrency/distributed algorithms.

Always invoke all subagents concurrently in a single `invoke_subagent` call with explicit `Model` routing:

```json
{
  "Subagents": [
    {
      "TypeName": "self",
      "Model": "flash",
      "Role": "[YYYY-MM-DD HH:mm | #fe] Frontend UI Specialist",
      "Prompt": "Task: Build client UI in apps/web...",
      "Workspace": "inherit"
    },
    {
      "TypeName": "self",
      "Model": "pro",
      "Role": "[YYYY-MM-DD HH:mm | #spec] Core Architecture Specialist",
      "Prompt": "Task: Design distributed concurrency package in packages/...",
      "Workspace": "inherit"
    },
    {
      "TypeName": "self",
      "Model": "flash",
      "Role": "[YYYY-MM-DD HH:mm | #devops] DevOps Specialist",
      "Prompt": "Task: Create Dockerfiles and monitor CI/CD...",
      "Workspace": "inherit"
    },
    {
      "TypeName": "self",
      "Model": "flash",
      "Role": "[YYYY-MM-DD HH:mm | #qa] E2E Simulation Specialist",
      "Prompt": "Task: Write automated E2E journey tests...",
      "Workspace": "inherit"
    }
  ]
}
```

---

## 4. Live Maintainer Telemetry Standard
Immediately after dispatching the swarm, provide real-time telemetry in clear, friendly Vietnamese:
1. **Đang làm gì**: Bảng ma trận phân công cụ thể từng subagent và phạm vi file cách ly.
2. **Sắp làm gì**: Kế hoạch tổng hợp kết quả và verification gate sau khi swarm hoàn tất.
3. **Mức độ rủi ro**: Đánh giá rủi ro (`Thấp` / `Trung bình` / `Cao`).

---

## 5. Synthesis & Verification Gate
When subagents complete their missions:
1. Master Agent inspects return payloads and git commits.
2. Runs the consolidated test suite (`pnpm test`, `pnpm test:e2e`).
3. Verifies zero drift across modified files.
4. Delivers an executive handover summary with live endpoints and test evidence.
