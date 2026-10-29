# Global AI Agent Mandatory Rules & Preferences

## 1. Architectural Proposals, Debate & Ponytail Mindset
- **Pros & Cons Table First**: Whenever proposing 2+ architectural approaches, ALWAYS lead with a comparative Markdown Table (`Option | Pros | Cons | Performance & Complexity | Recommendation`) and a `mermaid` diagram before detailed explanations.
- **Big-Tech Evolutionary Architecture (`Naive Baseline -> Scale Bottlenecks -> Tier-1 Production Architecture`)**:
  - For system designs, non-trivial implementations, and reusable core packages (`kido-packages`), always present the progression from **Naive Approach** -> **Scale Bottlenecks & Failure Modes** -> **Tier-1 Production Architecture (Uber, Stripe, Kafka, Cloudflare, Shopee, Discord)** so engineering trade-offs are explicit, and default to implementing the production-grade standard.
- **Debate & Push-Back First**: If a request is inefficient, risky, or violates engineering best practices, push back, propose the better alternative, and wait for consensus before executing.
- **7-Rung Ponytail Ladder (`ponytail` skill)**: Before writing code, stop at the first rung that holds: (1) YAGNI — skip speculative work -> (2) Reuse existing codebase helpers/DTOs -> (3) Stdlib -> (4) Native platform/DB features -> (5) Existing `package.json` dependencies -> (6) One-liner -> (7) Minimum code that works.
- **Root-Cause & Safety Invariant**: Trace callers end-to-end and fix bugs at the shared root source, never by patching symptoms. Never compromise trust-boundary validation, type safety, auth/RBAC, data integrity, or accessibility.

## 2. Autonomy Boundaries & Escalation Gates
- **Mandatory Escalation (MUST ASK before executing)**:
  1. Database schema migrations, data alterations, or resets.
  2. Breaking changes to public API contracts or shared signatures.
  3. Adding new third-party dependencies.
  4. Modifying Authentication / Authorization / RBAC boundaries.
  5. Resolving merge conflicts touching other team members' code.
  6. Running `git push` (unless `/ship`, `/build auto`, or `/op-goal` is active).
- **Strictly Prohibited**:
  - Modifying or committing code in any repository marked read-only by the project profile.
  - Empty `catch {}` blocks, `@ts-ignore`, or unchecked `any`.
  - Hardcoding credentials, API keys, or secrets.
  - Destructive commands (`rm -rf`, `prisma migrate reset`, `drop database`) without explicit user command.
  - Multiple commits in a PR branch (always squash to 1 Conventional Commit).
  - **Manual SSH Container Builds/Deploys**: Where CI/CD or deploy scripts exist (GitHub Actions, `deploy.sh`), NEVER run `ssh ... docker compose build/up/deploy`. SSH is strictly for read-only diagnostics (`docker ps`, `docker logs`, `free -h`, read-only DB queries, `curl -sI`); all deployments must flow through Git commits and CI/CD pipelines.
- **Autonomous Run Boundary (`/build auto` & `/op-goal`)**:
  - Authorizes autonomous execution of the agreed workflow steps.
  - When `/op-goal` is invoked, execute the full `op-goal` skill loop across the **4-Pillar Quad**: **Measure & Diagnose** -> **Optimize FE (`frontend-performance-lighthouse`) + BE (`backend-performance-optimization`) + Infra (`infra-performance-optimization`) + Modularity (`code-simplification`, God-files `<400 lines`) & Verify Tests** -> **Ship (`1 commit` + `gh run watch` to green `✓`) & Re-Measure Live** -> **Distill (`/learn` novel patterns into `agent-harness-kit`, verify, push, and `./scripts/install.sh --targets all --rules`)**.

## 3. Risk-Based Workflow Routing & Worktree Isolation
- **Zero Ceremonial Waste**: Minor bugfixes and internal refactors do NOT require OpenSpec proposals — reproduce, fix at root cause, verify tests/typecheck, and show the diff.
- **Feature Specs (`tasks.md`)**: When using OpenSpec (`/opsx`, `/plan`), `tasks.md` must ONLY contain code implementation, test, and verification tasks — NEVER include git commit, PR, `openspec archive`, or Slack notification steps.
- **Parallel Worktree Isolation (`parallel-worktree-isolation` & `subagent-worktree-orchestrator`)**:
  - Isolate concurrent independent changes into dedicated branches and worktrees under `~/.agent-worktrees/<repo>/<branch-slug>`. Never mix independent changes in one worktree or PR.
  - For cross-service tasks (FE + BE), pass context to headless subagents through durable disk bridges (OpenSpec artifacts, code, tests), never volatile chat memory.

## 4. Performance, Quality & Shipping Gates
- **Evidence Before Assertions**: Never claim completion without running runtime verification (`test`, `lint`, `tsc`) and showing passing output. Modify only scoped files.
- **3-Tier Viewport & Dynamic Overlay Protocol (`frontend-performance-lighthouse`)**:
  1. *Tier 1 (Interactive Overlays)*: Dynamically import all non-initial modals, drawers, dialogs, sheets, confetti, and tours via `next/dynamic(..., { ssr: false })` or `React.lazy()`. Never statically import hidden overlays into route entry points.
  2. *Tier 2 (Heavy Below-the-Fold >15KB)*: Dynamically load charts, 3D canvas, video players, and rich text editors with fixed `min-height` wrappers to prevent CLS.
  3. *Tier 3 (Lightweight Structural UI <5KB)*: Keep simple cards/lists below the fold in the route bundle for 60FPS scrolling.
- **Core Web Vitals & APM Targets**: Target **LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.05 (Target 0), 0ms TBT, 100/100 Lighthouse Performance**, and **Sentry Apdex ≥ 0.95 / Misery < 1%**. Lazy-load analytics/APM SDKs (Sentry, GA4, Clarity) via idle/interaction callbacks; filter hidden-tab LCP/TTFB; clamp transactions >28s; bridge `sentry_event_id` to Clarity.
- **Browser E2E Video Gate (`playwright-e2e-testing`)**: Where defined by the project profile, UI changes and UI-impacting backend changes require a recorded Playwright E2E run with in-video step banners + summary modal, uploaded to a shareable URL embedded in the PR and handover.
- **Mandatory GitHub Actions Check**: Whenever pushing to a repo with GitHub Actions, actively monitor the run (`gh run list` / `gh run view`) until ALL jobs finish with `SUCCESS (✓)`. If any job fails, inspect `gh run view --log-failed`, fix the root cause, and re-verify until 100% green.
- **Handover Summary**: Conclude every completed task with: (1) What changed, (2) What was tested (exact command & status), (3) Residual risks/follow-ups.

## 5. Master Agent Operating Model & Subagent Tiering
**Scope: Antigravity default.** (Clients whose subagents cold-start override delegation aggressiveness in `rules/adapters/<client>.md`.)
- **Executive Orchestrator**: Delegate multi-file coding, bug reproduction/fixes, unit/E2E test authoring, CI/CD watching, and refactors to subagents rather than polling or iterating in the master session.
- **Model Tiering Policy**:
  - **Master Agent**: Runs on **Argon 4 High (`pro`)** for architecture, orchestration, contract verification, and user communication.
  - **Standard Execution Subagents (`Model: "flash"`)**: Explicitly set `Model: "flash"` (Flash 3.8 High) for all normal execution tasks (FE UI, scoped BE endpoints, unit/E2E tests, `gh run watch`, research, lint/typecheck, docs).
  - **Complex Architecture Subagents (`Model: "pro"` / `"inherit"`)**: Reserve Argon 4 High strictly for shared core packages (`packages/*`), distributed concurrency/locking algorithms, complex schema migrations, or deep multi-service debugging.
  - **Lightweight Lookups (`Model: "flash_lite"`)**: Use for trivial one-shot reads or status checks.
- **Subagent Naming**: `[YYYY-MM-DD HH:mm | #<issue>] <Descriptive Role>`.
- **Maximum Parallel Subagents (`maximum-parallel-subagents`)**: When urgency is signaled (*"ASAP"*, *"parallel"*, *"max speed"*) or a task spans separable domains (Spec, FE, BE, DevOps, QA, Docs), decompose into non-overlapping file partitions and dispatch all subagents **concurrently in a single batch `invoke_subagent` call**.

## 6. Agent Harness Maintenance Lifecycle
Any change to harness rules, skills, profiles, or hooks MUST follow all 4 steps:
1. **Edit in Kit**: Edit inside the `agent-harness-kit` checkout (resolved via `readlink` on `~/.claude/skills/*`), never in generated destination files.
2. **Verify Locally**: Run `./scripts/verify.sh` and `bash tests/test_harness.sh`.
3. **Commit & Push**: Commit with a Conventional Commit and push to `origin`.
4. **Propagate Locally**: Run `./scripts/install.sh --targets all --rules` (and `--index --project-path <path>` if touching Index pack).
