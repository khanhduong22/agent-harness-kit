# Tasks

## Phase 1 — Make the scripts host-agnostic

- [ ] Copy the four scripts from the workspace `.agents/scripts/` into `scripts/hooks/` in the kit
- [ ] `auto-lint-fix.sh`: replace the `.workspacePaths[0]` read with `.cwd // .workspacePaths[0] // empty`, falling back to `$PWD`
- [ ] `guard-new-packages.sh`: replace `.toolCall.args.CommandLine` with `.tool_input.command // .toolCall.args.CommandLine // empty`
- [ ] `guard-new-packages.sh`: make every internal error path exit 0, so a parse failure never blocks the operator's command
- [ ] `prisma-auto-flow.sh`: replace `.toolCall.args.TargetFile` with `.tool_input.file_path // .toolCall.args.TargetFile // empty`, and the workspace read as above
- [ ] `prisma-auto-flow.sh`: drop the error message naming Antigravity as the only supported payload
- [ ] `stop-gate.sh`: run its gate unconditionally instead of keying off `.terminationReason` / `.executionNum` / `.transcriptPath`, which no Claude Code or Codex Stop payload carries
- [ ] Pipe-test each script against a synthesized Claude Code payload and confirm the side effect, not just the exit code

## Phase 2 — Hook definition

- [ ] Write `profiles/index/hooks.json` in the Claude Code schema, translating tool names: `write_to_file` → `Write`, `replace_file_content|multi_replace_file_content` → `Edit`, `run_command` → `Bash`
- [ ] Give the `Stop` entry the `{ "hooks": [...] }` wrapper Claude Code requires — Antigravity's flat form is rejected
- [ ] Use absolute command paths, matching what `~/.codex/hooks.json` already does
- [ ] Set a `statusMessage` per hook so a slow or failing hook is identifiable in the UI

## Phase 3 — Deployment

- [ ] `install.sh`: deploy `scripts/hooks/` to the target machine and record the action in the receipt so `--rollback` can undo it
- [ ] `install.sh`: merge the hook block into `.claude/settings.json` and `~/.codex/hooks.json`, preserving every operator entry and not duplicating kit entries on reinstall
- [ ] `install.sh`: report `hooks unchanged` on a reinstall that changes nothing, matching the existing rule and MCP paths

## Phase 4 — Verification

- [ ] `tests/test.sh`: assert the hook block lands in the target settings file
- [ ] `tests/test_harness.sh`: assert an operator-added hook on a different event survives a reinstall, and that the kit's own entry is not duplicated — mirroring the Test 6 allowlist contract
- [ ] Prove the new assertions fail without the implementation, the way the prune assertions were checked
- [ ] `scripts/check-skill-ownership.sh` and `scripts/verify.sh` still exit 0
- [ ] Observe each hook firing in a live session: a lint violation corrected unasked, an install command blocked, a `.prisma` edit announcing the migration flow
