# Changelog

All notable changes to this kit are documented here.

## [0.1.5] - 2026-09-16

### Changed

- **The Index workspace profile is now the single source for workspace policy.** `profiles/index/workspace.md` grows from 39 to 119 lines, absorbing the 99-line `/Users/kido/index/.agents/AGENTS.md` that had been maintained by hand outside any git repository and outside the installer's reach. The two overlapped: the `index-web` ownership policy was duplicated **byte-for-byte across 8 lines**, the service list in the profile was a thinner subset of the one in `AGENTS.md`, and the 1-Commit Rule appeared at three separate layers. Both files were loaded into every session, because the workspace `CLAUDE.md` imports `@.agents/AGENTS.md` on line 1.
- Section 6 now states the ownership boundary explicitly: this pack is generated from the kit and must never be hand-edited or shadowed by a second copy inside the workspace, while `<service>/.agents/AGENTS.md` and `<service>/.agents/skills/` stay versioned with the code they govern. A rule or skill lives in exactly one of the two.

### Notes

- The thin six-line service list from the old profile was dropped in favour of the detailed descriptions it duplicated; the `Rule Preservation` bullet was reworded to drop its `.agents/AGENTS.md` path reference. No other content differs — verified line-by-line against both sources.

## [0.1.4] - 2026-09-15

### Fixed

- **Test suites asserted nothing.** macOS ships bash 3.2, where `set -e` does not abort on a failing `[[ ... ]]` or a `! cmd` negation — POSIX exempts both. Almost every assertion in `scripts/test.sh` and `tests/test_harness.sh` was written that way, so both suites printed "passed" while their assertions were false: they had been asserting symlinks for `ask-matt`, `writing-for-agents`, `gemini-api-dev` and `triage`, none of which have been in the kit since those skills were purged. Only a single pipeline (`find | grep -q`) was ever enforced. All assertions now route through `assert`/`refute` in the new `scripts/assert.sh`, which exit explicitly and name the failing expectation.
- **`--rollback latest` could not find its receipt.** `install_project_index` calls `sync_rules.py` directly, which writes receipt entries but never creates the `latest` symlink — that only happens in `init_receipt`, which the index path never called. An index install onto an already-provisioned home (nothing left for the skill or rule paths to record) left a stamped receipt that rollback could not resolve. `install_project_index` now calls `init_receipt` first. Surfaced by the assertion fix above.
- Test fixtures now sample real skills from `skills/` instead of hardcoding names, which rot silently on every rename or purge.

### Changed

- **Global rules no longer name Index services.** `rules/core.md` and `rules/adapters/claude.md` referenced `index-api`, `index-admin-cms` and `index-web` in seven places, so every install wrote project-specific policy into every user's global `CLAUDE.md` / `AGENTS.md` / `GEMINI.md`. The harness test asserted this must not happen and had been failing silently. The wording is now generic and defers to the project profile; the Index-specific policy it duplicated already lives in `profiles/index/workspace.md` §4 and `profiles/index/cms.md` §4, so no rule was lost.

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
