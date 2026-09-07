{{CORE_RULES}}

## Claude Code compatibility

- Treat `/opsx`, `/build`, `/test`, `/review`, and `/ship` as skills when installed. Claude's built-in `/plan` remains reserved; use the installed planning skill or follow the planning phase directly.
- `AGENTS.md` is not an automatic Claude Code instruction source. A project `CLAUDE.md` must import or summarize any required `AGENTS.md` guidance.
