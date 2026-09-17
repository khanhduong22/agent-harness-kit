# Project Pack: Index Platform (Workspace)

## 1. Product Objectives & Current Priorities
- **Product Overview**: The Index platform is a multi-service financial & community information ecosystem serving Vietnamese market insights, analytics, content management, and community interactions.
- **Current Priorities**:
  - Stabilizing API endpoints and database query performance.
  - Hardening CMS administrative flows and editorial permissions.
  - Ensuring telemetry and observability with OpenTelemetry and Signoz.
- **What NOT To Do Yet**:
  - Do NOT modify public API signatures without explicit backward compatibility review.
  - Do NOT perform ad-hoc schema migrations without approval.
  - Do NOT introduce unverified external dependencies.
  - `[TBD: Need User Input]` Future external payment/gateway integrations remain pending formal specifications.

================================================================================
CATEGORY A: MONOREPO TOPOLOGY & CROSS-SERVICE ARCHITECTURE
================================================================================

## 2. Monorepo Ecosystem & Service Boundaries
- **`index-api` (Backend Core)**: NestJS, Prisma ORM, PostgreSQL, Redis, Swagger API, Newman E2E tests. Implements core domain logic, data models, and high-performance querying. (See `index-api/.agents/AGENTS.md` for NestJS & Prisma rules).
- **`index-admin-cms` (Admin Platform)**: Strapi v5, Custom Admin Plugins (`community`, `admin-user-role-guard`), React/Vite admin extensions, Custom UI Hooks. Consumes Index API and manages administrative workflows. (See `index-admin-cms/.agents/AGENTS.md` for UI/UX & Strapi rules).
- **`index-data` (Data Ingestion & Crawlers)**: Node/Bun crawlers, market data extractors, and automated data ingestion pipelines (crypto/stock/news) feeding normalized content into `index-admin-cms` and `index-api`. (See `index-data/.agents/AGENTS.md` for Prisma dual-DB, TimescaleDB, and logical-replication rules).
- **`index-ai` (AI & Search Platform)**: NestJS financial data platform — instrument search, AI sentiment analysis, vector embeddings (PostgreSQL + Meilisearch + Qdrant). (See `index-ai/CLAUDE.md` for architecture & conventions).
- **`index-web` (Client Web Application)**: Next.js App Router, public community feeds, and user-facing web experiences. (See `index-web/CLAUDE.md` for conventions).
- **`index-signoz` (Observability & Telemetry)**: Customized SigNoz deployment (OpenTelemetry Collector, ClickHouse) providing distributed tracing, metrics, and centralized log auditing across monorepo services. (See `index-signoz/.agents/AGENTS.md` for collector/ClickHouse operational rules).
- **Cross-Service Data Contracts**: API response envelopes (`{ data, meta }`) and data schemas MUST remain strictly synchronized across services. When changing response structures in `index-api`, verify and update parsers (`parseApiResponseEnvelope`) in `index-admin-cms`, `index-data`, and `index-web`.
- **Developer Service Ownership & Policy (Khánh Dương / khanhduong22)**:
  - **Owned & Active Codebases (Full Modification Rights)**: Strictly `index-api`, `index-admin-cms`, and `index-data`.
  - **`index-web` Service Policy (Read-Only Analysis & E2E Video Verification Gate)**:
    - `index-web` source code belongs to other frontend team members. **STRICTLY DO NOT MODIFY, EDIT, OR COMMIT CODE IN `index-web`**.
    - **Authorized & Encouraged Actions**: Agents are fully authorized to:
      1. Inspect and analyze `index-web` components, API envelope parsers, and client routes.
      2. Pull latest `develop` branch of `index-web` (`git pull origin develop`).
      3. Start `index-web` locally (`next dev` / `bun run dev` on port 3000) connected to backend services.
      4. Execute Playwright browser E2E test runs against `index-web` to record verification videos (`--video=on`) demonstrating backend API fixes on the live web UI, upload recordings to Google Drive, and embed active links in PR handovers and Slack.

## 3. Platform Boundaries & Constraints
- **Database Safety**: Never run `prisma migrate reset` or drop databases. Database backups (`scripts/dump-db.sh`) must be taken before major schema operations.
- **Service Isolation**: Each service runs independently. Communication between services must follow documented HTTP/REST or queue protocols.
- **Secrets Management**: All secrets must remain in `.env` files; never commit credentials or production URLs.
- **Unknown Specifications**: Any unspecified domain rule or logic must be marked `[TBD: Need User Input]` and confirmed with the team lead.

## 4. OpenSpec Multi-Service Directory Standard
- **Target Service Scope**: Store active change proposals in the target sub-repository (`<service-repo>/openspec/changes/<change-name>/`, e.g. `index-api/openspec/changes/<change-name>/` or `index-admin-cms/openspec/changes/<change-name>/`). Permanent capabilities live in `<service-repo>/openspec/specs/<capability>/spec.md`.
- **Change Folder Artifacts**: Each active change proposal MUST include `proposal.md`, `design.md`, `tasks.md`, and `specs/<capability>/spec.md` (delta diffs using `+` / `-` requirement headers).
- **Scope of `tasks.md` (No Meta/Shipping Tasks)**: `tasks.md` MUST strictly focus on code implementation, tests, and domain verification steps. **DO NOT include shipping, archiving (`openspec archive`), git commit, PR creation, or Slack notification steps in `tasks.md`** — those are harness lifecycle operations and do not belong in specification tasks.
- **Mandatory Gherkin Syntax**: All capability specs (`openspec/specs/<capability>/spec.md`) and delta specs (`specs/<capability>/spec.md`) MUST use strict Gherkin syntax (`GIVEN` / `WHEN` / `THEN` / `AND`).
- **Automated CLI Archiving**: During `/ship`, MUST run `openspec archive <change-name> -y` before the final commit so merged spec deltas and archived proposal files are included in that commit. Use `--skip-specs` only when the change intentionally has no spec deltas. Do NOT manually move files.

================================================================================
CATEGORY B: CODEBASE INTELLIGENCE & MCP ECOSYSTEM
================================================================================

## 5. MCP Tooling & Multi-Agent Intelligence
### CLI Agent Roster (Arena Round Table)
This machine has the following CLI agents installed for multi-agent collaboration:
- **AGY (Antigravity)**: `agy -p --model gemini-2.5-pro "prompt"` — Auditor role. Logic, scanning, fact-checking, evidence verification.
- **Claude Code**: `claude -p --model claude-fable-5 "prompt"` — Architect role. Enterprise architecture, research breakthroughs, UX design.
- **Workflow**: See `arena-round-table` skill for structured debate protocol.

### MCP Servers
Utilize the integrated MCP servers for proactive codebase analysis and runtime verification:
- **`codebase-memory-mcp` (Pre-Change Analysis)**: Before modifying any shared function, repository method, service, or API endpoint, you SHOULD trace its full call graph and all upstream consumers (MUST for breaking changes — e.g. signature changes, export removal, schema migration):
  1. `get_architecture(project=...)` -> Understand project structure, module boundaries, entry points, hotspots.
  2. `search_graph(name_pattern=...)` -> Locate all related functions, classes, and controller routes.
  3. `trace_path(function_name=..., direction="inward")` -> Trace every upstream caller of the function to detect blast radius.
  4. `grep_search` fallback -> Verify non-code usages (configs, env, postman collections, markdown specs).
- **`postgres` & `redis`**: Inspect live database tables, check query performance, and verify cache state during feature development and debugging.
- **`chrome-devtools-mcp`**: Inspect real runtime DOM, console errors, and visual layouts when building or debugging Strapi CMS or Web components.
- **`figma`**: Inspect UI designs, extract exact node specs, and verify pixel-perfect layout alignment.

## 6. Agent Rule Maintenance & Preservation Policy
- **Single Source**: This workspace pack is generated from `agent-harness-kit/profiles/index/workspace.md` and injected between the `agent-harness-kit:index` markers by `scripts/install.sh`. Edit the kit and redeploy — never hand-edit the injected block, and never create a second copy of this policy inside the workspace, because the installer cannot see or reconcile one.
- **Rule Preservation**: Always preserve existing workspace and sub-project rules intact. Never delete or strip rules without explicit user approval.
- **Service-Scoped Rules Stay In Their Repo**: `<service>/.agents/AGENTS.md` and `<service>/.agents/skills/` are versioned with the code they govern and are NOT managed by the kit. Anything specific to one service belongs there; anything portable across projects belongs in the kit. A rule or skill must live in exactly one of the two.
- **Harness Change Lifecycle**: Any modification to harness rules, skills, profiles, or configurations MUST follow the strict lifecycle:
  `Change in agent-harness-kit -> Local verification (scripts/verify.sh) -> Commit & Push to remote -> Apply back to local machine (scripts/install.sh)`. Never edit workspace rule files directly.

================================================================================
CATEGORY C: WORKSPACE QUALITY GATES & PR PROTOCOL
================================================================================

## 7. Single Commit per Pull Request Policy (STRICT 1-COMMIT RULE)
- **1-Commit Rule**: Every PR MUST contain EXACTLY ONE single commit. NO EXCEPTIONS.
- **Sequential Execution Workflow during `/ship`**:
  1. Complete code changes, unit tests, and Postman collection updates.
  2. Execute `openspec archive <change-name> -y` BEFORE making the final commit so merged spec deltas and archived proposal files are included in the single commit. Use `--skip-specs` only when the change intentionally has no spec deltas.
  3. Create/checkout the target branch (`feature/<name>`, `bugfix/<name>`, or `hotfix/<name>`).
  4. Stage specific modified and archived files explicitly (`git add <file1> <file2> ...`).
  5. Create **ONE SINGLE COMMIT** using Start-Case Conventional Commits (`git commit -m "Feat: Add New Feature"`).
  6. Verify commit count with `git log origin/develop..HEAD --oneline`. If > 1 commit, run `git reset --soft origin/develop` and re-commit into 1 single commit BEFORE pushing.
  7. Push to origin (`git push -u origin <branch>`) and create GitHub PR (`env -u GITHUB_TOKEN gh pr create`). An explicit `/ship` invocation authorizes this push; outside `/ship`, ask first.

## 8. Mandatory Clickable Figma Link & Folder Structure Standard
- **Clickable Figma URLs**: Always format Figma node references with clickable URLs (e.g., `[Figma Node 12077:253458](https://www.figma.com/design/...-id=12077-253458)`). Never use plain text node IDs.
- **List All UI Nodes & Folder Structure**: Every PR description MUST list all clickable Figma UI nodes provided by the user and include an updated folder/file tree map.

## 9. Mandatory Slack Handover Notification with Direct PR Link
- **Mandatory PR Link in Slack**: Whenever completing a task/PR and notifying the user via the configured Slack webhook, the notification MUST include:
  1. Direct clickable GitHub PR link (e.g. `• 🔗 PR: <https://github.com/idx-vn/<repo>/pull/<id>>`).
  2. Summary of verification status (unit test pass count, TypeScript 0 errors).
  3. Touched files scope.

## 10. Cross-Service UI E2E Video Recording & Closed-Loop Verification Gate
- **CMS Admin Gate (`index-admin-cms`)**: Playwright E2E testing with video recording is mandatory for every CMS feature or bugfix before PR completion.
- **Client Web UI Verification Gate (`index-web`)**: Whenever an API change in `index-api` affects data displayed on the user-facing web interface (e.g. topic rankings, stock tags, moderation state):
  1. Pull latest `develop` on `index-web` (`git pull origin develop`).
  2. Run `index-web` locally (`bun dev` / `next dev` on port 3000) pointing to local API (`http://localhost:3005`).
  3. Execute Playwright browser test with video recording (`--video=on`) to verify API changes on the live client web UI.
- **Closed-Loop Downstream Verification Gate (Strictly Prohibit Stopping at Internal Toast)**:
  - *Email / SMTP Sink*: Whenever a CMS action or API endpoint triggers an email (e.g. password reset, moderation notice, system warning, ban alert), the E2E test MUST navigate directly to Mailpit (`http://localhost:8025`), assert email arrival, open the email body, and verify the branded HTML layout and token/action link. Stopping at an internal CMS toast or mocking the SMTP delivery is strictly prohibited.
  - *In-App Notification & Real Bell Sink*: Whenever an action emits an in-app user notification, the E2E test MUST log into the recipient/victim account on `index-web` (`http://localhost:3000`), confirm the red badge count on `NotificationBell`, open the dropdown panel, and click the notification item to verify navigation and unread status decrement.
  - *Public Feed State Reflection*: Whenever an admin action moderates content (hiding/deleting/locking posts or topics), the E2E test MUST navigate to `index-web` public feed (`/vi/cong-dong`) and verify that moderated content is completely excluded from public view.
- **In-Video Visual Telemetry Standard**: Every Playwright E2E recording MUST implement:
  - *Floating On-Screen Step Banners (`showStepBanner`)*: Injected at top-center (`STEP X: [ACTION]`) with distinct badge color, clear context subtitle, and 1.5s visual pause.
  - *End-of-Run Audit Summary Modal (`showSummaryModal`)*: Injected full-screen frosted glass card displaying verified task ID, `✓ 100% VERIFIED` status, persisted database records, and delivery channel statuses, paused for 4.5s before browser teardown.
  *Note: `index-web` source code remains strictly read-only. Never modify or commit code in `index-web`.*

> **Note**: The Master Agent operating model (Executive Assistant, subagent
> delegation-first, subagent naming convention) is defined once in the global
> harness rules and is not repeated here.
