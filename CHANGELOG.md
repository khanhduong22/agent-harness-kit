# Changelog

All notable changes to this kit are documented here.

## [0.1.3] - 2026-09-15

### Added

- `playwright-e2e-testing`: Closed-Loop Downstream Verification Gate — mandatory Side-Effect Discovery step (§2) that traces `COMMUNITY_EVENTS` → `@OnEvent` listeners → `SmtpService` before a spec is written, plus a Sink Inventory table that must be filled in and attached to the PR. Previously the downstream rule was conditional ("if the action sends mail…") with no way to discover whether a sink existed, so agents skipped it and ticked N/A honestly.

### Changed

- `playwright-e2e-testing`: Reduced from 1164 to 286 lines. Removed ~790 lines of duplicated `playwright.config.ts` / `base.page.ts` / fixtures / POM / helper source that already exists as working code in `index-admin-cms/`; replaced with a pointer table to the real files. The embedded copies had drifted badly — documented method names (`expectToast`, `confirmAlertDialog`, `verifyCsvAndShowPreview`) no longer matched the real exports (`waitForToast`, `confirmModal`, `validateAndPreviewCsv`), the fixture list was missing 4 of 11 entries, and the CSV preview snippet carried 6 backslash-escaped `${}` interpolations that render as literal text.

### Fixed

- `playwright-e2e-testing`: Removed a hardcoded admin password from the auth setup example, deduplicated the `4.8` heading and the repeated directory tree.

## [0.1.2] - 2026-09-09

### Added

- `playwright-e2e-testing`: Full lifecycle E2E browser testing workflow with Playwright, form validation guardrails, video recording, Google Drive upload via rclone, and instant Slack notifications.
- `subagent-worktree-orchestrator`: Multi-agent cross-worktree orchestration rule and delegation skill for headless agents.

## [0.1.1] - 2026-09-07

### Added

- Explicit `--rules-mode replace` migration path for legacy global rule files, with automatic backup before replacement.

## [0.1.0] - 2026-09-07

### Added

- Portable snapshot of 67 common Agent Skills and six Claude-specific SDLC adapters.
- User-level adapters for Codex, Claude Code, Gemini, and Antigravity.
- Safe symlink/copy installer with conflict backups and managed global-rule blocks.
- Structural, portability, and isolated installation tests.
