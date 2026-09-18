# Changelog

All notable changes to this kit are documented here.

## [0.1.12] - 2026-09-18

### Fixed

- **`rules/core.md` §8 forced cold-start subagent spawns onto Claude Code for ordinary work.** The "Subagent Delegation First" mandate — "ALWAYS delegate to specialized subagents" for feature implementation, bug fixes, tests, and refactors — was written for Antigravity's same-session planner/executor, where a spawned subagent shares context and is cheap. `rules/adapters/claude.md` only added cold-start caveats on top of that mandate; it never actually overrode it, so a Claude Code session applying the merged rule delegated small, single-shot work into subagents that re-derive full context from zero, multiplying token cost several-fold per task (observed: a 5-agent parallel review running 80k–126k tokens per agent, ~500k+ combined, for work a direct edit would have done for a fraction of that). `core.md` §8 now states its own scope ("Antigravity default") and requires per-client adapters to override delegation aggressiveness when their subagent economics differ; `rules/adapters/claude.md` now defaults to working directly in the master session and delegates only for genuinely multi-step/parallelizable work or an explicit user request (`/build auto`, `/code-review ultra`, an opted-into Workflow). Verified with `./scripts/verify.sh` and `./tests/test_harness.sh` (all 10 behavioral tests pass) — this is a rules-text change with no installer logic touched, so no new test coverage was needed.

## [0.1.11] - 2026-09-18

### Fixed

- **Every PreToolUse/Stop hook failed Claude Code's own output schema, on every single invocation.** `guard-new-packages.sh`, `guard-manual-migrations.sh` and `stop-gate.sh` all set a top-level `decision` key to `"allow"`, `"deny"`, `"force_ask"`, or `"continue"` — none of which are valid: the field is deprecated for PreToolUse (the real signal is `hookSpecificOutput.permissionDecision`) and its only valid values, where it applies at all, are `"approve"`/`"block"`. Since `guard-new-packages.sh` fires on every `Bash` call and `guard-manual-migrations.sh` on every `Bash` and `Write` call, this surfaced the expected-schema reminder on effectively every tool use in a live session. Fixed by omitting the top-level `decision` key where a fine-grained `permissionDecision` already carries the real signal, and using `"block"` (the one valid enum value with that meaning) for `stop-gate.sh`'s loop-guarded blocking case.

## [0.1.10] - 2026-09-18

### Fixed

- **`--rollback` left deployed hook scripts behind.** `install_hooks` called `init_receipt` (which only stamps the receipt file into existence) but never `record_receipt_action` for the copied `*.sh` files, so `--rollback` correctly reverted `settings.json`/`hooks.json` while leaving every hook script on disk — undetected by Test 9 because it only checked deployment and merging, never rollback. Found by a real `code-review` pass against merged PR #13, not by self-testing. Each script now gets its own "file" receipt entry (existing action type, no new mechanism), verified empirically: install → rollback now leaves zero scripts behind, and a stashed-fix run of the new harness assertion fails as expected.
- **A sibling directory sharing a name prefix could be misclassified as kit-owned.** `_entry_is_kit_owned` compared commands with a bare `str.startswith(hooks_dir)`, so a hand-placed hook in e.g. `hooks-legacy/` (sharing the `hooks` prefix) would be silently treated as a kit entry and dropped on the next reinstall. Fixed to compare against a separator-terminated prefix. Also found by the same `code-review` pass.

## [0.1.9] - 2026-09-17

### Added

- **Hooks now deploy to Claude Code and Codex.** Four guardrails — lint auto-fix, Prisma schema sync, an unrequested-package block, and a pre-ship gate — were declared `"enabled": true` in an Antigravity-shaped `.agents/hooks.json` that Claude Code never reads: it takes hooks only from `settings.json`, and neither settings file had a `hooks` key. So none of them had ever run. `install.sh` now deploys the scripts to one shared directory and merges the hook block into `<project>/.claude/settings.json` and `~/.codex/hooks.json` — Codex needs no separate definition, since its hooks file already uses the Claude Code schema verbatim. Operator entries survive the merge and the kit's own entries are not duplicated on reinstall (`tests/test_harness.sh` Test 9, proven to fail without the implementation).

### Fixed

- **The hook scripts could not read any other host's payload.** All four parsed Antigravity's shape (`workspacePaths`, `toolCall.args.CommandLine`, `toolCall.args.TargetFile`), so wiring them up unchanged would have produced hooks that fire and do nothing — worse than none, because it looks fixed. Each field now reads through a jq fallback chain, one line per field, and one script serves every host. The output contract differed too: `guard-new-packages.sh` emitted Antigravity's `{"decision":"force_ask"}` where Claude Code and Codex read `.hookSpecificOutput.permissionDecision` with the value `ask`; it now emits both.
- **The pre-ship gate could never fire on any host.** `grep -c` exits 1 on a zero count, so `grep -c … || echo "0"` produced `"0\n0"` and the numeric test aborted with `integer expression expected`, falling through to allow. Rewritten with `grep -q`. Separately, the gate now blocks only on Antigravity, which supplies the `executionNum` loop guard that stops a blocking Stop hook from firing forever; elsewhere it is advisory, surfacing its reminder through `systemMessage` without holding the turn open.

## [0.1.8] - 2026-09-17

### Fixed

- **`opsx` told authors to keep `## Why` short, for a reason that was not true.** The guidance claimed long why-sections "get flagged by `openspec validate`"; the validator (v1.5.0) never inspects the section — it fails only on missing `specs/` deltas and missing `#### Scenario:` blocks, and a change with a long Why validates clean. The invented length limit pushed authors into the shortest thing that fits, which is the code-level diagnosis: real proposals in the workspace open with a symbol name and a stack of failing call sites. Acceptance criteria then get derived from the technical fix instead of the user outcome, so a change ships with a green suite while the original pain is untouched. `## Why` now has to name who is affected in user-facing terms, cite where it was observed (or `[TBD: Need User Input]`, never an invented source), and state the user-visible signal that proves the pain is gone — explicitly not "the tests pass". No new artifact file: the section already existed, it was just being filled with the wrong thing.

## [0.1.7] - 2026-09-17

### Fixed

- **Project rules were written where no tool reads them.** Codex reads `AGENTS.md` at the repository root and walks down to the working directory; `.codex/` is the *global* home (`CODEX_HOME`) only, and Codex never reads a `.codex/AGENTS.md` inside a project. `install_project_index` preferred exactly that path when it existed, so the current pack landed in a file nothing loads while the root `AGENTS.md` that Codex and Antigravity both read went stale — 40 lines behind. Codex and Gemini now share `<project>/AGENTS.md`, the cross-tool file both actually load. Antigravity reads `./GEMINI.md` *and* `./AGENTS.md`, so writing a project `GEMINI.md` as well would have injected this pack twice; the write is marker-scoped, so the second adapter reports "unchanged".
- The Slack webhook is no longer hardcoded in a tracked script. It resolves from `SLACK_WEBHOOK_URL` or `~/.config/agent-harness/secrets.env`.

### Added

- `arena-round-table` and `ponytail`, absorbed from a hand-maintained workspace skill directory. Both are portable — `arena-round-table` carries no project-specific reference, and `ponytail` is MIT-licensed generic guidance. (`ponytail` overlaps the 7-Rung Ladder already in `rules/core.md` section 2; it is kept for its on-demand intensity levels, which the always-on rule does not provide.)
- `check-skill-ownership.sh` now also scans a workspace-root `.agents/skills` directory, not just the service repos. That layer is not a deploy target of `install.sh`, so anything left there is a hand-made copy that drifts unnoticed — it held 40 of them, 3 stale against the kit and 4 duplicating a skill a service repo already owned.

## [0.1.6] - 2026-09-16

### Added

- **`scripts/check-skill-ownership.sh`** — fails when a skill name exists in both the kit and a service repo. Wired into `scripts/verify.sh`; skips silently unless a workspace path is passed or `AGENT_HARNESS_WORKSPACE` is set, so a machine without the workspace still verifies clean. The invariant is **disjointness**, not "the kit must be a superset": the longer copy is usually longer because it is coupled to one repo, so a superset rule would pull service internals up into the global layer.
- **Orphan pruning in `install.sh`.** Deleting a skill from the kit used to leave the deployed link behind on every machine that had installed it, and the stale skill kept applying with nothing reporting it. Only dangling symlinks pointing into this kit are pruned — a foreign link and a real operator directory both survive, and `--mode copy` is left alone because a removed skill is then indistinguishable from a hand-written one. Covered by three assertions in `scripts/test.sh`, verified to fail without the fix.

### Changed

- **Four skills moved out of the kit to the service repo that owns them**: `github-pr-ship`, `postman-api-testing`, `prisma-safe-migration` and `use-constants`. All six duplicated skills had drifted, and in every case the service copy was the richer one — but richer because it hardcodes that service's paths, containers and commands (`prisma-safe-migration` carries `gb_api-db-1`, `greenbull`, `api_shadow`, `prisma/api/...`). Promoting those to the kit would have repeated the 0.1.4 leak one layer down, shipping one service's internals to every project on every machine.
- **`fix-sonarqube` absorbed the richer service copy (23 → 56 lines)** and stays in the kit: its content is generic `sonarjs` rule/fix guidance, and the only repo-specific part — the SonarQube component key — is now `$SONAR_PROJECT_KEY` rather than a hardcoded project name. The duplicate is removed in idx-vn/index-api#442.

## [0.1.5] - 2026-09-16

### Changed

- **The Index workspace profile is now the single source for workspace policy.** `profiles/index/workspace.md` grows from 39 to 119 lines, absorbing the 99-line workspace-root `.agents/AGENTS.md` that had been maintained by hand outside any git repository and outside the installer's reach. The two overlapped: the `index-web` ownership policy was duplicated **byte-for-byte across 8 lines**, the service list in the profile was a thinner subset of the one in `AGENTS.md`, and the 1-Commit Rule appeared at three separate layers. Both files were loaded into every session, because the workspace `CLAUDE.md` imports `@.agents/AGENTS.md` on line 1.
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
