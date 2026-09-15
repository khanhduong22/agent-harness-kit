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

## 2. Multi-Service Architecture
The workspace contains the following core services:
- **`index-api`**: Main backend service built on NestJS and Prisma ORM.
- **`index-admin-cms`**: Headless CMS administration built on Strapi v5.
- **`index-web`**: Next.js user-facing web application.
- **`index-ai`**: AI/LLM integration and processing pipeline.
- **`index-data`**: Data ingestion, scraping, and processing service.
- **`index-signoz`**: Observability, metrics, and tracing stack.

## 3. Platform Boundaries & Constraints
- **Database Safety**: Never run `prisma migrate reset` or drop databases. Database backups (`scripts/dump-db.sh`) must be taken before major schema operations.
- **Service Isolation**: Each service runs independently. Communication between services must follow documented HTTP/REST or queue protocols.
- **Secrets Management**: All secrets must remain in `.env` files; never commit credentials or production URLs.
- **Unknown Specifications**: Any unspecified domain rule or logic must be marked `[TBD: Need User Input]` and confirmed with the team lead.

## 4. Developer Service Ownership & `index-web` Policy (Khánh Dương / khanhduong22)
- **Owned & Active Codebases (Full Modification Rights)**: Strictly `index-api`, `index-admin-cms`, and `index-data`.
- **`index-web` Service Policy (Read-Only Analysis & E2E Video Verification Gate)**:
  - `index-web` source code belongs to other frontend team members. **STRICTLY DO NOT MODIFY, EDIT, OR COMMIT CODE IN `index-web`**.
  - **Authorized & Encouraged Actions**: Agents are fully authorized to:
    1. Inspect and analyze `index-web` components, API envelope parsers, and client routes.
    2. Pull latest `develop` branch of `index-web` (`git pull origin develop`).
    3. Start `index-web` locally (`next dev` / `bun run dev` on port 3000) connected to backend services.
    4. Execute Playwright browser E2E test runs against `index-web` to record verification videos (`--video=on`) demonstrating backend API fixes on the live web UI, upload recordings to Google Drive, and embed active links in PR handovers and Slack.

