{{CORE_RULES}}

## Claude Code compatibility

- Treat `/opsx`, `/build`, `/test`, `/review`, and `/ship` as skills when installed. Claude's built-in `/plan` remains reserved; use the installed planning skill or follow the planning phase directly.
- `AGENTS.md` is not an automatic Claude Code instruction source. A project `CLAUDE.md` or isolated worktree root must import or summarize any required `AGENTS.md` guidance (e.g. `@<repo-root>/.agents/AGENTS.md`).
- **Mandatory Playwright E2E for UI/CMS**: For any changes touching `index-admin-cms`, Claude Code must execute `npx playwright test` with video recording enabled, upload the video via `./scripts/upload-e2e-video.sh`, and embed the Google Drive URL in the PR description before shipping.

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
