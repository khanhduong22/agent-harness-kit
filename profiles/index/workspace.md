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
