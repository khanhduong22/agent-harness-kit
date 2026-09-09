{{CORE_RULES}}

## Claude Code compatibility

- Treat `/opsx`, `/build`, `/test`, `/review`, and `/ship` as skills when installed. Claude's built-in `/plan` remains reserved; use the installed planning skill or follow the planning phase directly.
- `AGENTS.md` is not an automatic Claude Code instruction source. A project `CLAUDE.md` or isolated worktree root must import or summarize any required `AGENTS.md` guidance (e.g. `@/Users/kido/index/.agents/AGENTS.md`).
- **Mandatory Playwright E2E for UI/CMS**: For any changes touching `index-admin-cms`, Claude Code must execute `npx playwright test` with video recording enabled, upload the video via `./scripts/upload-e2e-video.sh`, and embed the Google Drive URL in the PR description before shipping.
