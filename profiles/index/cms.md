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
- **E2E Browser Tests**: `npx playwright test` (Runs Playwright E2E suite with video recording enabled).
- **Video Upload to Google Drive**: `bash ./scripts/upload-e2e-video.sh <video-path.webm> "<Task Name>"`.
- **Slack Handover Notification**: `bash ./scripts/notify-slack.sh "<Task Name>" "<PR URL>" "<Status Details>" "<Video URL>" "<Issue Info>" "<Flow Steps>"`.

## 3. Strict Coding & Operation Conventions
- **Schema & Content Types**: Content types are managed under `src/api/*/content-types/`. Any schema alteration must be accompanied by corresponding migration scripts.
- **Permissions Hygiene**: Do not alter editor or community permissions arbitrarily; use existing seed scripts (`seed:community-permission`, `seed:audit-log-permission`).
- **Audit Logs**: Preserve telemetry and audit log tracking for all administrative actions.
- **Unknown Specifications**: `[TBD: Need User Input]` Strapi Cloud syncing schedules and custom plugin release gates.

## 4. Mandatory E2E Quality Gate
- **Headless Playwright Suite**: Every feature, bugfix, or UI change touching `index-admin-cms` MUST execute Playwright E2E tests (`npx playwright test`) with video recording mode enabled (`video: { mode: 'on' }`).
- **File Download & CSV Verification**: For any export/download flows (e.g. CSV analytics export):
  1. Intercept download via `page.waitForEvent('download')`.
  2. Verify file encoding (first 3 bytes must be UTF-8 BOM `0xEF, 0xBB, 0xBF` for Vietnamese Excel compatibility).
  3. Inject on-screen modal preview via `page.evaluate(...)` rendering parsed table with Vietnamese headers directly into browser canvas.
  4. Wait at least 4 seconds (`await page.waitForTimeout(4000);`) so the video recording captures the table clearly.
- **Cloud Verification & Handover**:
  1. Upload video to Google Drive using `./scripts/upload-e2e-video.sh`.
  2. Embed Google Drive video URL directly in the PR checklist table.
  3. Dispatch Slack notification using `./scripts/notify-slack.sh`.
  4. **Strict Prohibition**: Skipping browser E2E or deferring to manual QA in PR descriptions is strictly prohibited.
