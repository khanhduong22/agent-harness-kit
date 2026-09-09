---
name: test
description: Run the repo's test/typecheck/build verification suite and report real pass/fail results with actual command output as evidence. Use after /build, when the user asks to run tests or fix a failing suite, or invokes /test.
---

# Verify

Phase 4 of the pipeline: `OPENSPEC (/opsx) → PLAN (/plan-sdlc) → BUILD (/build) → VERIFY (/test) → REVIEW (/review) → SHIP (/ship)`.

## Evidence rule (non-negotiable)

Never claim something passes without having actually run it in this turn and seen the output. "Should pass" or "this looks correct" is not evidence. If a command can't be run (missing infra, no network, etc.), say so explicitly rather than assuming success.

## What to run

Check the target repo for what's actually available, don't assume a fixed toolchain:

1. Unit/integration tests — look for `bun test`, `npm test`, `pytest`, etc. in `package.json`/`Makefile`. Prefer the project's own `test` script over ad-hoc test-runner invocations.
2. Typecheck — `tsc --noEmit` for TypeScript repos, or the language's equivalent.
3. Build — the project's build script, to catch anything a typecheck alone misses (e.g. `nest build`, `next build`).
4. If the repo has a combined pre-ship script (e.g. `verify-all.ts`, `verify:all`), that's the authoritative gate list — check what it actually runs and whether any step is marked skippable/optional versus a hard blocker, and report which is which rather than treating "the script exited 0" as the whole story if some steps silently downgrade failures to warnings.
5. e2e/API suites (Postman/Newman, Cypress, Playwright) — these usually need a live server + database. Check what's already running (`lsof`, `docker ps`) before spinning up new infrastructure; prefer reusing an already-running dev DB over starting a fresh stack. For `index-admin-cms` (UI/CMS), `npx playwright test` with video recording enabled is a mandatory blocking gate — run headless Playwright tests with video on and verify 100% pass before proceeding.

## Investigating failures

Before reporting a failure as "caused by this change": check whether it's pre-existing (stale build artifacts like a gitignored `dist/` polluting test discovery, a failure that reproduces identically on the base branch, an external service dependency that's simply not running locally). Distinguish clearly in the report between "this change broke X" and "X is broken independently of this change" — don't blur the two, and don't silently fix or paper over something outside the current change's scope without flagging it.

## OpenSpec cross-check

If working against an OpenSpec change, verify every Gherkin `Scenario:` in its spec deltas has real coverage (a unit test, or better, a live/e2e check) — not just that some tests pass, but that the scenarios the spec actually promises are the ones being exercised.

## Report format

A pass/fail table or list per check, with the real command and real result — not a prose summary that hides which specific command actually ran.

## Gate

Stop for confirmation before `/review` unless running autonomously.
