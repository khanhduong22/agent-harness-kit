# Project Sub-Profile: Index Admin CMS (`index-admin-cms`)

## 1. Service Overview & Architecture
- **Framework**: Strapi v5 Headless CMS with custom plugins and admin dashboard.
- **Database**: PostgreSQL with custom database backup and restore scripts.
- **Cache**: Redis cache provider (`@strapi-community/provider-rest-cache-redis`).

## 2. Real Verification & Execution Commands
All commands run from within `index-admin-cms/`:
- **Development Server**: `strapi develop` or `bun dev` (or `yarn develop`).
- **Tests**: `yarn test` or `jest`.
- **Database Backup**: `bash ./scripts/dump-db.sh backup`.
- **Database Info**: `bash ./scripts/dump-db.sh info`.
- **Database Verification**: `bash ./scripts/verify-backup.sh`.
- **Seed Scripts**: `node ./scripts/seed.js` (Use `--force` only with user confirmation).
- **OpenAPI Generation**: `node scripts/generate-openapi.js`.

## 3. Strict Coding & Operation Conventions
- **Schema & Content Types**: Content types are managed under `src/api/*/content-types/`. Any schema alteration must be accompanied by corresponding migration scripts.
- **Permissions Hygiene**: Do not alter editor or community permissions arbitrarily; use existing seed scripts (`seed:community-permission`, `seed:audit-log-permission`).
- **Audit Logs**: Preserve telemetry and audit log tracking for all administrative actions.
- **Unknown Specifications**: `[TBD: Need User Input]` Strapi Cloud syncing schedules and custom plugin release gates.
