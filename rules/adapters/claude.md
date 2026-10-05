{{CORE_RULES}}

## Claude Code compatibility

- Treat `/opsx`, `/build`, `/test`, `/review`, and `/ship` as skills when installed. Claude's built-in `/plan` remains reserved; use the installed planning skill or follow the planning phase directly.
- **Project instructions**: Claude Code (≥ 2.1.277) reads a project's `AGENTS.md` only when no `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` exists in the working directory or any directory above it. When one does, `CLAUDE.md` takes precedence over `AGENTS.md` and the `AGENTS.md` is ignored — a leftover `CLAUDE.md` in a service silently hides the workspace `AGENTS.md`. Nothing under `.agents/` is read on its own; import it from `AGENTS.md` (e.g. `@.agents/AGENTS.md`). This global file stays `~/.claude/CLAUDE.md` (Claude Code documents no user-level `AGENTS.md`) and does not count as a `CLAUDE.md` for that check.

## Claude Code subagent mechanics (delegation-first override)

Claude Code subagents **start cold**: they inherit no conversation, no files you
already read, and no prior tool results, and return only their final message.
Re-deriving that context is what costs the tokens. So core.md §8's "delegation
first" does not apply here — **default to working directly in the master
session.** Delegate only when one of these holds:

- The task is genuinely multi-step or parallelizable (independent review
  angles, cross-service work, isolated worktree changes).
- The user explicitly asks for delegation, a heavy/parallel review, or invokes
  an autonomous or multi-agent mode (`/build auto`, `/code-review ultra`, a
  Workflow the user opted into).
- The self-contained brief is genuinely shorter than doing the work directly.

Never delegate single-file edits, config/rule changes, reading a file to answer
a question, or any task where the brief would be longer than the work.

When delegating:

- **Self-contained briefs**: carry absolute paths, the OpenSpec artifact pointers
  (`proposal.md`, `design.md`, `tasks.md`, delta specs), the exact commands to run,
  and the structured payload to return. Never say "the file we discussed" — the
  subagent cannot see it.
- **Use the named subagents** in `~/.claude/agents/` (`sdlc-implementer`,
  `e2e-playwright-recorder`, `newman-api-tester`, `lint-typecheck-fixer`,
  `codebase-tracer`) rather than `general-purpose`, so the role prompt and tool
  scope are already loaded.
- **Naming placement**: `[HH:mm | #<issue>] <Descriptive Role>` goes in the Agent
  tool's `description` argument. The `name:` frontmatter field must stay
  lowercase-with-hyphens — Claude Code rejects other formats.
- **Worktree isolation**: for independent parallel changes, delegate to a subagent
  declaring `isolation: worktree` instead of manually creating `~/.agent-worktrees/...`.
- **Background by default** so the user can interject; block only when the very
  next step depends on the result.
- **Write to disk early and often**: Claude Code subagents are killed by a
  no-progress watchdog; agents were lost after long silent planning with no file
  writes, and the same task succeeded once the brief demanded incremental writes.
  State this in every brief for work larger than a single file.
- **Trust nothing, verify on disk**: a subagent's summary is a claim, not evidence.
  Confirm it against `git diff`, real test output, or the artifact before reporting
  completion.

Shell gotcha: `cmd | tail; echo $?` reports `tail`'s exit code, not `cmd`'s.
Capture the status without a pipe, or use `${PIPESTATUS[0]}`, whenever an exit
code is the evidence.
