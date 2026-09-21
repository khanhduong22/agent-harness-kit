# Tasks

## Phase 1 — Tests first (each must fail before its implementation phase)

- [x] `tests/test_harness.sh`: repoint the project-pack assertions from `mock_project/.claude/CLAUDE.md` to `mock_project/AGENTS.md` (exactly one start and one end marker, `Index Platform`, `index-api`, `index-admin-cms`) and assert no `.claude/CLAUDE.md` or `CLAUDE.md` remains after a claude install
- [x] Fold test: a pre-existing `.claude/CLAUDE.md` containing `# Project Existing Rule` ends up in `AGENTS.md` exactly once, and a byte-identical backup exists in the run's backup dir
- [x] Dedupe test: legacy paragraphs already present in `AGENTS.md` are not appended a second time
- [x] Both-locations test: `.claude/CLAUDE.md` and root `CLAUDE.md` together migrate without a backup-name collision
- [x] Symlink test: a legacy `CLAUDE.md` that is a symlink is left untouched and a warning is printed
- [x] Dry-run test: `--dry-run` reports the migration and creates or removes nothing
- [x] Idempotency test: a second install changes nothing and adds no backups
- [x] Rollback test: `--rollback latest` restores the legacy file byte-for-byte and returns `AGENTS.md` to its prior state (or removes it if the run created it)
- [x] Failure-safety test: when `AGENTS.md` cannot be written, the legacy file is still in place
- [x] Global-path test: the global Claude rule still lands at `<home>/.claude/CLAUDE.md` and no `<home>/.claude/AGENTS.md` is created
- [x] Adapter-text test: the rendered Claude rule no longer contains "AGENTS.md is not an automatic Claude Code instruction source" and states that `CLAUDE.md` takes precedence over `AGENTS.md`
- [x] Python unit tests for `fold_legacy` next to `tests/test_mcp_render.py`: marker block stripped, operator text kept, duplicate paragraph dropped, empty remainder returns the input unchanged, incomplete marker raises `ValueError`

## Phase 2 — `scripts/sync_rules.py`

- [x] Add the pure `fold_legacy(agents_text, legacy_text, marker_prefix)` function
- [x] Add repeatable `--migrate-legacy` option; skip symlinks with a warning; back up each legacy file under `<label>/legacy/<flattened relative path>`
- [x] Write `AGENTS.md`, re-read it and verify the folded text is present, and only then remove each legacy file
- [x] Append the `file` receipt action for each removed legacy file after the `rule` action for `AGENTS.md`
- [x] Honour `--dry-run` for the migration and report `unchanged` on a repeat run

## Phase 3 — `scripts/install.sh`

- [x] In `install_project_index`, let the `claude` adapter share the `codex|gemini` arm so its project destination is `<project>/AGENTS.md`; delete the `.claude/CLAUDE.md` / `CLAUDE.md` probing
- [x] Pass `--migrate-legacy` for `<project>/.claude/CLAUDE.md` and `<project>/CLAUDE.md` when the adapter is `claude`
- [x] Update the comment block above that arm, and add a comment at `rule_destination` recording why the global Claude rule stays `~/.claude/CLAUDE.md` (no documented user-level `AGENTS.md`; test 4 vs 5)

## Phase 4 — Rules, docs, spec

- [x] `rules/adapters/claude.md`: replace the false `AGENTS.md` bullet with the verified behaviour — read only when no `CLAUDE.md` exists in the working directory or above, `CLAUDE.md` wins when both exist, anything under `.agents/` is never read (import it), the global file stays `~/.claude/CLAUDE.md`
- [x] `README.md`: change the Claude Code project-rule destination to `<project>/AGENTS.md`
- [x] Remove the duplicate root `CLAUDE.md` from the kit and confirm nothing else references it
- [x] `CHANGELOG.md`: add the 0.1.15 entry

## Phase 5 — Verification

- [x] `./scripts/verify.sh`, `./scripts/test.sh`, `bash tests/test_harness.sh`, and the Python tests all pass
- [x] Read-only `--dry-run` of the installer against the real `~/index` reports exactly which files would change
- [x] Headless `claude -p` sentinel check on a migrated fixture project: the kit pack and the migrated text both load from `AGENTS.md`
