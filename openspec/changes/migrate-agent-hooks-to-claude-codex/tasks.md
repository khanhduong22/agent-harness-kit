# Tasks

## Phase 1 — Make the scripts host-agnostic

- [x] Copy the four scripts from the workspace `.agents/scripts/` into `scripts/hooks/` in the kit
- [x] `auto-lint-fix.sh`: replace the `.workspacePaths[0]` read with `.cwd // .workspacePaths[0] // empty` — the `$PWD` fallback was already present
- [x] `guard-new-packages.sh`: replace `.toolCall.args.CommandLine` with `.tool_input.command // .toolCall.args.CommandLine // empty`
- [x] `guard-new-packages.sh`: make every internal error path exit 0, so a parse failure never blocks the operator's command
- [x] **Not in the plan — the OUTPUT contract differs too.** The script emitted `{"decision":"force_ask"}`, which is Antigravity's shape; Claude Code and Codex read `.hookSpecificOutput.permissionDecision` and the value is `ask`, not `force_ask`. It now emits both keys in one object, so each host reads its own and ignores the other.
- [x] `prisma-auto-flow.sh`: replace `.toolCall.args.TargetFile` with `.tool_input.file_path // .toolCall.args.TargetFile // empty`, and the workspace read as above
- [x] `prisma-auto-flow.sh`: drop the error message naming Antigravity as the only supported payload
- [x] ~~`stop-gate.sh`: run its gate unconditionally~~ — **the plan was wrong and unsafe.** `executionNum` is not decoration: it is the loop guard that stops a blocking Stop hook from firing forever (block → agent continues → stops again → block). Claude Code and Codex send no equivalent. The gate now BLOCKS only on Antigravity, where the guard exists, and is ADVISORY elsewhere — it emits `systemMessage`, which every host renders, and never holds the turn open. Transcript key and edit-record field read through fallback chains.
- [x] **Not in the plan — the gate was also logically broken.** `grep -c` exits 1 on a zero count, so the original `grep -c … || echo "0"` produced `"0\n0"` and the numeric test failed with `integer expression expected`, falling through to allow. The gate could never fire on any host. Rewritten with `grep -q`.
- [x] Pipe-test each script against a synthesized Claude Code payload and confirm the side effect, not just the exit code — 4/4 for `guard-new-packages` (install blocked, normal command allowed, malformed JSON fails open, Antigravity shape still works), 2/2 for `prisma-auto-flow`, 4/4 for `stop-gate`

## Phase 2 — Hook definition

- [x] Write `profiles/index/hooks.json` in the Claude Code schema, translating tool names: `write_to_file` → `Write`, `replace_file_content|multi_replace_file_content` → `Edit`, `run_command` → `Bash`
- [x] Give the `Stop` entry the `{ "hooks": [...] }` wrapper Claude Code requires — Antigravity's flat form is rejected
- [x] Use absolute command paths — via a `{{HOOKS_DIR}}` placeholder that `install.sh` substitutes, matching the existing `{{CORE_RULES}}` convention, so one profile works on any machine
- [x] Set a `statusMessage` per hook so a slow or failing hook is identifiable in the UI
- [x] The two `PostToolUse` scripts share one `Write|Edit` matcher entry rather than two, since Antigravity's separate named hooks collapse to the same event and matcher

## Phase 3 — Deployment

- [x] `install.sh`: deploy `scripts/hooks/` to one shared directory (`~/.agent-harness/hooks`) used by every host, and record it in the receipt
- [x] `install.sh`: merge the hook block into `<project>/.claude/settings.json` and `~/.codex/hooks.json`, preserving every operator entry and not duplicating kit entries on reinstall
- [x] `install.sh`: reports `hook config unchanged` on a no-op reinstall, matching the existing rule and MCP paths
- [x] **Reused `sync_rules.py` rather than writing `sync_hooks.py`** (rung 2): it already had JSON merge, backup, receipt and unchanged-reporting. Added a `--hooks` mode, three flags and two functions instead of a new script.
- [x] Kit-owned hook entries are identified by command path, since the schema has nowhere to put a marker. They are dropped and re-added on each merge, so a reinstall cannot duplicate them and a hook removed from the kit disappears on the next install.

## Phase 4 — Verification

- [x] `tests/test_harness.sh` Test 9: scripts deployed and executable, hook block lands in project settings, commands point at the deployed scripts, `{{HOOKS_DIR}}` never left unsubstituted
- [x] `tests/test_harness.sh` Test 9: an operator hook on an unmanaged event survives reinstall, the kit entry is not duplicated, and a no-op reinstall reports unchanged — mirroring the Test 6 allowlist contract
- [x] Proved the new assertions fail without the implementation: stashed `install.sh` and `sync_rules.py`, harness exited 1 at Test 9, restored and it passes
- [x] The first run of Test 9 caught a real path bug — the installer canonicalises the path it writes, and on macOS `$TMPDIR` sits under `/var`, a symlink to `/private/var`, so the assertion had to compare resolved paths
- [x] `scripts/verify.sh`, `scripts/test.sh`, `AGENT_HARNESS_WORKSPACE=… verify.sh` and `openspec validate` all exit 0
- [ ] **Operator-only, cannot be self-verified**: observe each hook firing in a live session — a lint violation corrected unasked, an install command blocked, a `.prisma` edit announcing the migration flow. `.agents/hooks.json` stays in place until then.
