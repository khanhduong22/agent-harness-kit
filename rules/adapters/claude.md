{{CORE_RULES}}

## Claude Code compatibility

- Treat `/opsx`, `/build`, `/test`, `/review`, and `/ship` as skills when installed. Claude's built-in `/plan` remains reserved; use the installed planning skill or follow the planning phase directly.
- `AGENTS.md` is not an automatic Claude Code instruction source. A project `CLAUDE.md` or isolated worktree root must import or summarize any required `AGENTS.md` guidance (e.g. `@<repo-root>/.agents/AGENTS.md`).
- **Browser E2E video gate**: Where the project profile defines one, Claude Code must run that suite with video recording enabled, publish the recording, and embed its URL in the PR description before shipping — never defer it to manual QA.

## Claude Code subagent mechanics (delegation-first)

Delegation-first still applies: prefer spawning a subagent over coding in the
master session. Claude Code subagents differ from Antigravity's planner/executor
in one decisive way — **they start cold**. A subagent inherits no conversation,
no files you already read, and no prior tool results; it returns only its final
message. Delegate accordingly:

- **Self-contained briefs**: every delegation prompt MUST carry absolute paths,
  the OpenSpec artifact pointers (`proposal.md`, `design.md`, `tasks.md`, delta
  specs), the exact commands to run, and the structured payload to return.
  Never reference "the file we discussed" or "the plan above" — the subagent
  cannot see it.
- **Use the named subagents** in `~/.claude/agents/` (`sdlc-implementer`,
  `e2e-playwright-recorder`, `newman-api-tester`, `lint-typecheck-fixer`,
  `codebase-tracer`) rather than the generic `general-purpose` agent, so the
  role prompt and tool scope are already loaded.
- **Naming convention placement**: `[HH:mm | #<issue>] <Descriptive Role>` goes
  in the Agent tool's `description` argument. The `name:` frontmatter field must
  stay lowercase-with-hyphens — Claude Code rejects other formats.
- **Worktree isolation**: for independent parallel changes, delegate to a
  subagent declaring `isolation: worktree` instead of manually creating
  `~/.agent-worktrees/...`.
- **Background by default**: leave subagents in the background so the user can
  interject; only block when the very next step depends on the result.
- **Trust nothing, verify on disk**: a subagent's summary is a claim, not
  evidence. The master session MUST confirm it against `git diff`, real test
  output, or the artifact on disk before reporting completion.

### Do NOT delegate

Spawning costs a cold re-derivation of context, so keep these in the master
session: single-file edits, config/rule changes, reading a file to answer a
question, and any task where the brief would be longer than the work.

### Two failure modes seen in practice

- **Brief subagents to write to disk early and often.** Claude Code subagents are
  killed by a no-progress watchdog. Two agents in a row were lost after long
  silent stretches of planning that produced no file writes; the identical task
  succeeded once the brief demanded incremental writes. State this in every
  delegation brief for work larger than a single file.
- **Never read `$?` after a pipe.** `cmd | tail; echo $?` reports the exit code
  of `tail`, not of `cmd`. This produced a false "exit code bug" report against a
  script that was correct, and nearly passed a gateway that looked like it
  ignored failed mounts. Capture the status without a pipe, or use
  `${PIPESTATUS[0]}`, whenever an exit code is the evidence.
