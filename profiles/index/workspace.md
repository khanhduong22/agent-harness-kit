# Project Pack: Index Platform (Workspace)

## 1. Monorepo Ecosystem, Ownership & Service Boundaries
- **Services**:
  - **`index-api` (Backend Core)**: NestJS, Prisma, PostgreSQL, Redis, Swagger, Newman E2E (`:3005`). Rules: `index-api/.agents/AGENTS.md`.
  - **`index-admin-cms` (Admin Platform)**: Strapi v5, custom plugins (`community`, `admin-user-role-guard`), React/Vite extensions (`:1337`/`:1338`). Rules: `index-admin-cms/.agents/AGENTS.md`.
  - **`index-data` (Data Ingestion & Crawlers)**: Node/Bun crawlers & market pipelines (crypto/stock/news) -> `index-admin-cms` & `index-api`. Rules: `index-data/.agents/AGENTS.md`.
  - **`index-ai` (AI & Search)**: NestJS instrument search, AI sentiment, vector embeddings (PG + Meilisearch + Qdrant). Rules: `index-ai/AGENTS.md`.
  - **`index-web` (Client Web App — STRICTLY READ-ONLY)**: Next.js App Router (`:3000`). Rules: `index-web/AGENTS.md`.
  - **`index-signoz` (Observability)**: OpenTelemetry Collector & ClickHouse. Rules: `index-signoz/.agents/AGENTS.md`.
- **Cross-Service Data Contracts**: Keep API envelopes (`{ data, meta }`) and `parseApiResponseEnvelope` synchronized across `index-api`, `index-admin-cms`, `index-data`, and `index-web`.
- **Developer Ownership Policy**:
  - **Writable**: Strictly `index-api`, `index-admin-cms`, and `index-data`.
  - **Issue-Repo vs. True Service Owner**: Even if an issue is filed under `index-web`, any DB query, bulk aggregation, or static generation (sitemaps, feeds, cache warming) MUST be implemented in `index-admin-cms` or `index-api`. `index-web` only calls lightweight backend HTTP endpoints.
  - **`index-web` Read-Only & E2E Policy**: **NEVER modify, edit, or commit code in `index-web`**. You ARE authorized to inspect `index-web`, pull `origin/develop`, run it locally (`bun dev` on `:3000`), and run Playwright E2E video tests (`--video=on`) against it.
- **Deployment Topology**:
  - **`app_pro` (`[app_pro]` runner)**: Nginx, shared `/www/wwwroot/sitemaps`, `index-admin-cms` Blue/Green (`:1337`/`:1338` + Redis), `index-web` (`:3006->:3000` + Redis), `index-api` (`:3005`).
  - **`data_pro` (`[data_pro]` runner)**: `index-admin-cms` PostgreSQL (`:5432`, pgBackRest -> Backblaze B2) and `index-data` crawlers.
  - **Dev/Staging (`[self-hosted-stg]` runner)**: Co-located Dev/Staging containers + Nginx.

## 2. OpenSpec & Single-Commit PR Protocol
- **Service-Scoped OpenSpec**: Store active changes in `<service-repo>/openspec/changes/<change-name>/{proposal.md,design.md,tasks.md,specs/<cap>/spec.md}` and specs in `<service-repo>/openspec/specs/<cap>/spec.md` using strict Gherkin (`GIVEN`/`WHEN`/`THEN`/`AND`).
- **No Shipping Steps in `tasks.md`**: `tasks.md` contains code, test, and verification tasks only.
- **1-Commit `/ship` Flow**:
  1. Complete code, tests, and Postman updates.
  2. Run `openspec archive <change-name> -y` BEFORE committing (`--skip-specs` only if no spec deltas).
  3. Checkout `feature/<name>`, `bugfix/<name>`, or `hotfix/<name>`, stage files explicitly, and create **EXACTLY 1 Start-Case Conventional Commit** (`git commit -m "Feat: ..."`).
  4. Verify `git log origin/develop..HEAD --oneline` has 1 commit (if >1, `git reset --soft origin/develop` and re-commit).
  5. Push (`git push -u origin <branch>`) and create PR (`env -u GITHUB_TOKEN gh pr create`).

## 3. MCP Tooling & Codebase Intelligence
- **`codebase-memory-mcp`**: Before modifying shared functions/endpoints (mandatory for breaking changes), trace callers via `get_architecture`, `search_graph`, and `trace_path(direction="inward")`, plus `grep_search` for configs/specs.
- **`postgres` & `redis` (`kido-mcp`)**: Inspect live DB schemas, query plans, and Redis state.
- **`chrome-devtools-mcp` & `framefit` (`figma`)**: Verify live DOM/console and compare against Figma node specs.
- **Arena CLI Roster (`arena-round-table` skill)**: `agy -p --model gemini-2.5-pro` (Auditor) & `claude -p --model claude-fable-5` (Architect).

## 4. Figma Links, Slack Handover & Closed-Loop E2E Video Gate
- **Clickable Figma URLs**: Always format Figma nodes as clickable links (`[Figma Node 12077:253458](https://www.figma.com/design/...-id=12077-253458)`) and include an updated file tree in every PR description.
- **Slack Handover (`.agents/scripts/notify-slack.sh` ONLY)**:
  - Must include clickable PR link, test/tsc status, and touched files.
  - Uses `SLACK_WEBHOOK_URL` from `~/.config/agent-harness/secrets.env` ONLY. **NEVER** grep or curl webhook URLs from `.github/workflows/*.yml` or repo `.env` files (company channels).
- **Closed-Loop E2E Video Gate (`playwright-e2e-testing` skill)**:
  - Mandatory recorded Playwright E2E (`--video=on`) with `showStepBanner` + `showSummaryModal` for all `index-admin-cms` changes and any `index-api` change affecting `index-web` UI.
  - **Downstream Sinks (Never stop at internal toast)**:
    1. *Email/SMTP*: Navigate to Mailpit (`http://localhost:8025`), open the email, and verify HTML body & action link.
    2. *In-App Notifications*: Log into the recipient account on `index-web` (`http://localhost:3000`), verify red badge count on `NotificationBell`, open dropdown, and click to verify unread decrement.
    3. *Public Moderation*: Verify hidden/deleted/locked content is excluded on `index-web` (`/vi/cong-dong`).

## 5. Strapi Content-Type Field & RBAC Permission Gate (`index-admin-cms`)
Adding a field to `schema.json` and `strapi_core_store_settings` does NOT grant permissions to existing Strapi roles (`editor` / `editor-in-chief`) in `admin_permissions` (`properties.fields`). Whenever adding/modifying Strapi fields, execute all 5 steps:
1. **Schema**: Add attribute to `src/api/<name>/content-types/<name>/schema.json`.
2. **View Layout**: Add field to `strapi_core_store_settings` via Knex migration.
3. **Translations**: Add labels in `src/admin/extensions/translations/{vi,en}.json`.
4. **RBAC Backfill (CRITICAL)**: Grant `create`/`read`/`update` in `admin_permissions` (`properties.fields`) for `editor` and `editor-in-chief` via Knex migration or `src/plugins/admin-user-role-guard/`.
5. **Non-SuperAdmin Verification**: Test with an `editor` account/token (never Super Admin alone) to prove field visibility and mutation.
