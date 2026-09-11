# MCP Provisioning

## Why

The kit provisions rules and skills but never touches MCP. `grep -rniE "mcp" scripts/install.sh scripts/sync_rules.py` returns nothing. Three costs follow:

- **Every developer configures MCP by hand, and gets it wrong.** A real instance: seven servers sat in `~/.claude/.mcp.json` for months while Claude Code read none of them — it reads `.mcp.json` from a *project root*, not from `~/.claude/`. Two of those servers (`postgres`, `redis`) are named in workspace `AGENTS.md` as tools agents must use. Agents were instructed to use tools that were never loaded.
- **MCP config is per-harness, so it is maintained three times.** Claude Code, Antigravity, and Codex each read a different file in a different shape. The kit exists to collapse exactly this kind of duplication for rules; MCP is the remaining half.
- **Tool bloat re-enters context silently.** MCP tools default to on. An upstream release that adds five tools re-inflates every session with no signal. A blacklist loses this race by construction; only an allowlist holds.

## What Changes

- **`mcp-provisioning` (new capability)**: profiles gain an `mcp` section declaring the servers a project needs; the installer renders it to each harness's native MCP config, scoped to the target project and recorded in the install receipt for rollback.
- **`mcp-provisioning` (new capability)**: profiles gain an `mcp_tools` allowlist; the installer renders it to `permissions.allow` entries so unlisted tools stay out of context as upstream servers grow.
- **`mcp-gateway` (new capability)**: a `kido-mcp-gateway` MCP server that mounts upstream servers as children and re-exports a curated subset under one endpoint, adding environment switching (local/dev/staging), composite tools that span servers, and a single registration line that every harness can point at.
- **`tiered-harness` (modified)**: the project-pack isolation requirement extends to MCP artifacts, so an MCP config written into one project never leaks into another.
