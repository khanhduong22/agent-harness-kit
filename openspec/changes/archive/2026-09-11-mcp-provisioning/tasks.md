# Tasks

## Phase 1 — Profile MCP declarations rendered per project

- [x] Add a fenced `toml` `[mcp.*]` parser to `scripts/sync_rules.py`, returning a dict per profile; no new third-party dependency
- [x] Implement `render_mcp_config(profile, target)` as a pure function (claude first; codex/gemini return an explicit `NotSupported` marker until Phase 3 verifies them)
- [x] Add `mcp` sections to `profiles/index/api.md` (postgres, redis) and `profiles/index/cms.md` (figma-developer-mcp, framefit)
- [x] Wire the installer to write `<project>/.mcp.json` under `--project-path`, honouring `--dry-run` and `--mode copy|symlink`
- [x] Record every MCP write in `receipt.json` so `--rollback` restores the prior state
- [x] Reject literal secrets in `verify.py` — `${VAR}` references only — reusing the existing machine-specific-path check
- [x] Unit tests for both pure functions, covering an empty `mcp` section and a malformed block
- [x] Extend `tests/test_harness.sh` with an MCP project-isolation case: installing into project A leaves project B untouched
- [x] Extend `tests/test_harness.sh` with an MCP rollback case

## Phase 2 — Tool allowlist

- [x] Parse `mcp_tools` from the same `toml` block
- [x] Implement `render_tool_allowlist(profile, target)` as a pure function
- [x] Write entries into the target's permission config without clobbering existing user entries (merge, never replace)
- [x] Add `mcp_tools` to both index profiles, listing only tools verified to work against the current token/DB scopes
- [x] Unit test the merge: a pre-existing unrelated permission survives a reinstall
- [x] Idempotency test: installing twice produces no duplicate permission entries

## Phase 3 — kido-mcp-gateway

- [x] **Verification gate first**: confirm whether Antigravity and Codex support per-tool MCP filtering and a single HTTP MCP endpoint; record findings in `design.md`. If they do not, scope the gateway to Claude Code and say so explicitly
- [x] Scaffold `gateway/` with `@modelcontextprotocol/sdk`, stdio + HTTP transports
- [x] Implement upstream mounting: spawn/connect each server in `mount`, proxy `tools/list` and `tools/call`
- [x] Implement `export` filtering so only listed upstream tools are re-exported
- [x] Implement environment switching: one `env` parameter selecting the local/dev/staging connection set
- [x] Implement the first composite tool, `verify_ui_against_figma`, spanning framefit and the Playwright output
- [x] Health/status command mirroring `framefit status`: report each mounted upstream as ok/failed
- [x] Integration test: gateway mounts two upstreams, exports a subset, and a call reaches the correct upstream
- [x] Document registration for each supported harness in `README.md`

## Phase 4 — Verification and handover

- [x] `./scripts/verify.sh` passes
- [x] `bash tests/test_harness.sh` passes, including the new MCP cases
- [x] Dry-run proof that installing the index pack touches only the target project
- [x] `openspec validate mcp-provisioning` passes
- [x] `README.md` documents the profile `mcp`/`mcp_tools` contract and the `~/.claude/.mcp.json` trap this change prevents
