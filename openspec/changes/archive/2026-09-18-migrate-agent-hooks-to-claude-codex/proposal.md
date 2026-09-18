# Migrate Agent Hooks To Claude Code And Codex

## Why

**Who is affected and how.** Every session run through Claude Code or Codex in this workspace silently loses four automated guardrails the operator believes are active: lint is not auto-fixed after edits, Prisma schema edits are not routed through the safe-migration flow, a command that installs an unrequested package is not stopped, and the pre-ship gate never fires when a turn ends. The operator only finds out at review time, when a PR arrives with lint errors or a package nobody asked for — the same class of failure as a test suite that reports green while asserting nothing.

**Where it was observed.** Found while auditing the workspace on 2026-09-17: `.agents/hooks.json` declares all four hooks with `"enabled": true`, but neither `.claude/settings.json` nor `.claude/settings.local.json` contains a `hooks` key — the only place Claude Code reads hooks from. The file is written in Antigravity's schema and was never ported when Claude Code and Codex became the primary drivers.

The gap is deeper than configuration. All four scripts parse **Antigravity's payload shape**, which no other agent sends:

| Script | Reads | Exists in Claude Code / Codex payload? |
|---|---|---|
| `auto-lint-fix.sh` | `.workspacePaths[0]` | no |
| `guard-new-packages.sh` | `.toolCall.args.CommandLine` | no — it is `.tool_input.command` |
| `prisma-auto-flow.sh` | `.workspacePaths[0]`, `.toolCall.args.TargetFile` | no — it is `.tool_input.file_path` |
| `stop-gate.sh` | `.terminationReason`, `.executionNum`, `.transcriptPath` | no |

`prisma-auto-flow.sh` states the coupling outright: *"jq is required to parse the Antigravity hook payload."* So wiring the existing config into `settings.json` unchanged would produce hooks that fire and then do nothing, which is worse than none — it looks fixed.

**How we will know the pain is gone.** Not "the tests pass". Each hook must be observed firing in a real session: edit a file with a lint violation and see it corrected without being asked; attempt an install command and be blocked; touch a `.prisma` file and see the migration flow announce itself. Until an operator sees those three in a live session, this change is unverified.

## What Changes

- **`scripts/hooks/`** (new in the kit): the four hook scripts, with payload extraction rewritten to read whichever shape the host agent sends, so one script serves Antigravity, Claude Code and Codex.
- **`profiles/index/hooks.json`** (new): the hook wiring in the Claude Code schema. `~/.codex/hooks.json` already uses that exact schema — same events, same `matcher` tool names, same `{type, command, timeout}` shape — so one definition covers both hosts.
- **`scripts/install.sh`**: deploy hook scripts and merge the hook block into the target's settings, the way rules and skills are already deployed. Merge, never replace: an operator's existing hooks and permissions must survive.
- **Tool-name translation**, applied once in the new config: `write_to_file` → `Write`, `replace_file_content` / `multi_replace_file_content` → `Edit`, `run_command` → `Bash`.
- **Absolute command paths.** The Antigravity config used `./scripts/*.sh`, which resolves against whatever directory the agent happens to be in. `~/.codex/hooks.json` already uses absolute paths; the deployed config will too.
- `.agents/hooks.json` in the workspace is **NOT retired**. Discovered during verification: `agentapi` runs Antigravity on a real weekday cron schedule (`15 8 * * 1-5`) as an unsupervised autonomous routine that spawns subagents, edits code and opens PRs — `.agents/hooks.json` is its only guardrail config, since `install.sh` has no Antigravity/Gemini hook target (`hook_config_destination` returns unsupported for that adapter). Retiring it would silently strip that routine's lint/package/migration/stop guardrails the next time it runs unattended. This corrects an internal contradiction: this line originally said "retired once observed" while `design.md` Decision 2 already specified the opposite — that Antigravity keeps its own file permanently because its schema differs. `design.md` was right; this line was wrong.

## Scope

Out of scope: adding new hooks, changing what the four scripts do once they have their inputs, and the Antigravity host itself (its existing `.agents/hooks.json` keeps working until retirement).
