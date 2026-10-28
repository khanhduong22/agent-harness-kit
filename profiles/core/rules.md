# Profile: Company Core

This profile defines company-wide baseline conventions for repositories where no specialized project pack is applied.

## Baseline Standards
- Follow the 7-Rung Ladder before writing code.
- Select the appropriate workflow based on task risk (Bugfix vs Feature vs Maintenance).
- Never execute destructive database commands without explicit user sign-off.
- Always provide test execution evidence before claiming task completion.
- Maintain a single conventional commit per pull request.

## Global MCP Servers & Tool Allowlist
The installer renders `kido-mcp` (backed by `gateway/`) into project MCP configs and tool allowlists.

```toml
mcp_tools = [
  "mcp__kido-mcp__gateway_status",
  "mcp__kido-mcp__postgres__query",
  "mcp__kido-mcp__postgres__list_databases",
  "mcp__kido-mcp__redis__scan",
  "mcp__kido-mcp__redis__get",
  "mcp__kido-mcp__framefit__get_layout_spec",
  "mcp__kido-mcp__framefit__get_metadata",
  "mcp__kido-mcp__framefit__compare_node_to_dom",
]

[mcp.kido-mcp]
command = "node"
args = ["${AGENT_HARNESS_KIT_ROOT}/gateway/dist/src/cli.js", "serve", "--config", "${KIDO_MCP_CONFIG}"]
```
