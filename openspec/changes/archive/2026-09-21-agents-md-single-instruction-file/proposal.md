# Make AGENTS.md The Single Project Instruction File

## Why

**Who is affected and how.** The operator keeps two files per project that say the same thing — `CLAUDE.md` for Claude Code and `AGENTS.md` for Codex and Antigravity — and has to keep them in step. In the Index workspace they have already drifted: the workspace `CLAUDE.md` and `AGENTS.md` differ by a header paragraph, and the service repos carry a mix of tracked, untracked, and stale copies. Worse, Claude Code reads `AGENTS.md` only when *no* `CLAUDE.md` exists in the working directory or above it, so any leftover `CLAUDE.md` silently hides the rules in the `AGENTS.md` beside it. A teammate who clones a service repo without this machine's local files gets no service rules in Claude at all.

**Where it was observed.** 2026-09-21, working session with the operator: Claude Code 2.1.277 added native `AGENTS.md` reading and the operator asked to make `AGENTS.md` the one file. Confirmed the same day on 2.1.278 against the real workspace (9 headless `claude -p` runs with unique sentinel strings): a service `CLAUDE.md` hides the workspace `AGENTS.md`; with only `AGENTS.md` present, the workspace pack, the `@.agents/AGENTS.md` import, and the service rules all load. The kit's own `rules/adapters/claude.md` still tells Claude that "`AGENTS.md` is not an automatic Claude Code instruction source", which is now false.

**How this will be known to be working.** Launching Claude Code in `~/index` and in each of `index-api`, `index-admin-cms`, `index-data` and `index-signoz` loads the workspace pack and that service's rules from `AGENTS.md`, and `find ~/index -maxdepth 2 -name CLAUDE.md` lists only the two repos deliberately left alone (`index-ai`, `index-web`). `./scripts/install.sh --rollback latest` restores every removed `CLAUDE.md` byte-for-byte.

## What Changes

- **Project packs (`scripts/install.sh`)**: the `claude` adapter writes the project pack to `<project>/AGENTS.md` — the file Codex and Antigravity already share — instead of `<project>/.claude/CLAUDE.md`.
- **Legacy project `CLAUDE.md` migration (`scripts/sync_rules.py`, `scripts/install.sh`)**: when the claude adapter installs a project pack and finds a legacy `<project>/CLAUDE.md` or `<project>/.claude/CLAUDE.md`, it backs the file up under the run's receipt, folds any text outside the kit's marker block into `AGENTS.md` (skipping paragraphs already present), then removes the legacy file. Symlinks are never touched. Everything is reversible with `--rollback`.
- **Global rules stay put**: the installer keeps writing the global Claude rules to `~/.claude/CLAUDE.md`. Claude Code documents no user-level `AGENTS.md`, and testing showed one is only picked up incidentally when Claude is launched under `$HOME`.
- **Adapter rules (`rules/adapters/claude.md`)**: replace the now-false statement with the verified behaviour (precedence, hiding, `.agents/` not read, global file).
- **Kit repo**: remove the duplicate root `CLAUDE.md`; `AGENTS.md` stays as the source.
- **Docs and tests**: README destination table, CHANGELOG, `tests/test_harness.sh` project-pack assertions, and new tests for fold, dedupe, symlink refusal, dry-run, idempotency, failure safety and rollback.
- **Out of scope**: the service repos' own files (handled by their own PRs), `index-ai` and `index-web` (deliberately untouched), skill prose that mentions CLAUDE.md generically (upstream text, no behavioural effect), and any Claude setting changes (the `instructionFiles` setting was considered and rejected — see `design.md`).
