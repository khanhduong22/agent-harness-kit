---
name: pre-ship-checklist
description: >-
  Mandatory pre-ship quality and security gate checklist. Execute before declaring
  any task/feature complete or inviting user review. Activated during /ship phase
  or when running final verification gates.
---

# Pre-Ship Mandatory Checklist

Before inviting user review or declaring any task/feature complete, you MUST execute the appropriate verification suite (`bun scripts/verify-all.ts`, `bun run verify:all`, or service-specific test commands) and output the following verification checklist with runtime evidence:

## Gate Checklist

1. `[x] Secret Leak Audit`: `gitleaks detect` (0 exposed credentials / tokens).
2. `[x] SAST & OWASP Security Audit`: `semgrep scan --config "p/owasp-top-ten" --config "p/typescript"` (0 security violations).
3. `[x] Dead Code & Dependency Audit`: `bun run lint:knip` / `bun x knip` (0 unused exports, unreferenced files, or redundant packages).
4. `[x] Package CVE Vulnerability Scan`: `trivy fs --scanners vuln --severity HIGH,CRITICAL` (0 HIGH/CRITICAL vulnerabilities).
5. `[x] Unit Tests`: `bun test src/<module>` (All unit tests pass 100%).
6. `[x] Postman E2E (API Services)`: `bun run test:postman` (All Newman integration assertions pass 100%, 1-to-1 mapped with OpenSpec Gherkin scenarios).
7. `[x] Playwright E2E & Cloud Video Verification (UI/CMS)`: For `index-admin-cms`, `npx playwright test` passes 100% with video recording enabled, video uploaded to Google Drive via `./scripts/upload-e2e-video.sh`, and link embedded in PR checklist.
8. `[x] Production Build & Type Safety`: `bun run build` passes cleanly with zero lint/type errors.

## Additional Quality Gates (run separately)

9. `[x] Quad-Skill Review Audit`: Execute `code-review-and-quality`, `code-simplification`, `performance-optimization`, `security-and-hardening`.
10. `[x] SonarQube Quality Gate`: `bun scripts/scan-sonar.ts` (Status OK, Reliability A, Maintainability A).
11. `[x] Slack Handover Notification`: `./scripts/notify-slack.sh` dispatched with PR URL, Google Drive video link, and flow steps.

## Workflow

1. Run service verification — e.g. `bun run verify:all` or `npx playwright test`.
2. If any gate FAILS, fix the root cause and re-run.
3. For file/CSV downloads in UI/CMS: ensure UTF-8 BOM (0xEF, 0xBB, 0xBF) is verified and visual table preview modal is injected for >= 4 seconds so the recording captures table content clearly.
4. Run the Quad-Skill Review via `/review` command.
5. Run SonarQube scan via `bun run scan:sonar` (or `bun scripts/scan-sonar.ts`).
6. Only after ALL gates pass, proceed to commit and push.

> **IMPORTANT**: Playwright E2E and video recording for UI/CMS (`index-admin-cms`) are **hard blocking gates**. Skipping browser E2E or deferring to manual QA is strictly prohibited.
