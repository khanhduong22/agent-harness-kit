# Tasks

## Phase 1 — `pr-review-loop` skill

- [x] Create `overlays/claude/skills/pr-review-loop/SKILL.md`, matching the frontmatter/structure convention of `ship`/`review`/`opsx` in the same directory
- [x] Contract: requires `pr_url` and `repo` as explicit inputs; never calls `gh pr list` or otherwise re-derives which PR to review
- [x] Invokes `Skill(code-review, "<pr_url> --repo <repo>")` at `high` effort explicitly; the skill text states plainly that `ultra` must never be used here (requires the user's own explicit trigger and billing consent per this environment's own constraint)
- [x] Parses/relays `code-review`'s severity output into the Important/Nit split from `design.md`; does not reimplement review dimensions itself — thin orchestration only, per the "don't reinvent" precedent already set in the `review` skill
- [x] Default `comment=false`; document the exact one-line change to flip it, and the reversibility asymmetry from `design.md` Decision 2, directly in the skill text
- [x] On completion: report findings to the caller AND invoke `./scripts/notify-slack.sh` (or the kit's current equivalent path) with the PR link and Important/Nit counts
- [x] State explicitly in the skill text that a review can take ~10+ minutes (observed ~11 min against a real PR) and is advisory — the ship it followed has already completed by the time findings land

## Phase 2 — Wire into `ship`

- [x] Add a new final step to `overlays/claude/skills/ship/SKILL.md` (after the existing step 6, before step 7's "never without go-ahead" list): once the PR is created/updated, spawn `pr-review-loop` as a **background** subagent, passing the exact PR URL captured from step 6's own `gh pr create`/`gh pr edit` output and the resolved `owner/repo`
- [x] State plainly in `ship`'s text that this step does not block ship completion or require the review to finish before reporting the ship as done

## Phase 3 — Verify

- [x] `bash scripts/verify.sh` exits 0 (no machine-specific paths, valid skill frontmatter) — 47 skills counted (was 46), verify.sh exit 0
- [x] Dry-run the skill's own instructions by hand against a real already-merged PR (#15) with `comment` left at its default — **the dry run found the first draft could not actually be followed as written**, not just cosmetic gaps:
  - `high` effort silently did not take effect — `code-review` ran at `xhigh` because `~/.claude/settings.json`'s persisted `effortLevel` overrode the passed argument with no error. The skill's "never `ultra`" guarantee had no real enforcement behind it, only an unverified request.
  - `Skill(code-review, ...)` forks asynchronously; the position the skill's step 2 put the caller in had no documented wait primitive available to a subagent (`sleep` is harness-blocked, `notify_when_idle` is main-conversation-only). The dry-run agent only succeeded because its *external* task brief told it to wait ~11 minutes — nothing in the skill text itself did.
  - No verified path for findings to reach a human unattended: step 4 "report to the caller" reports into a turn `ship` has already closed, and step 5's Slack script needs a repo-relative path a subagent given only `pr_url`+`repo` (per step 1's own isolation rule) has no way to resolve.
  - Step 3's grouping rule was self-contradictory — "just group by `code-review`'s own tags" vs. an independent Important/Nit test — and the dry run hit a real finding where the two disagreed (a `Reuse/Conventions`-tagged finding that named a violated CLAUDE.md rule).
  - Steps 3–6 had no stated scope (whose job are they — the spawned subagent's, or the parent's?).
  - Confirmed independently, not taken on the subagent's word: `~/.claude/settings.json:104` does carry `"effortLevel": "xhigh"`, and `scripts/rollback.py`'s main loop has no try/except around `rollback_action`, matching a separate PR #15 finding from the same run (tracked as its own bugfix, out of this change's scope — see below).
  - **Rewrote `SKILL.md` in response** — collapsed the implicit two-hop design into one flat subagent job (no ambiguous nested spawn), added `notify_script_path` as a required input (operational plumbing, not review context, so it doesn't compromise isolation) so the one subagent that has findings can also reach Slack itself, replaced the self-contradictory grouping rule with one test that also states which side wins when `code-review`'s own tag disagrees, and made effort-level verification the caller's own job (read `code-review`'s self-reported level back; treat `ultra` specifically as a stop-and-report-immediately condition) rather than trusting the requested argument.
- [x] Confirm `code-review ultra` is never invoked anywhere in the new skill text (`grep -n ultra` the new file — should only appear in the explicit prohibition sentence, not as a call) — 1 occurrence, in the prohibition sentence; zero in ship's own text
- [x] `openspec validate add-pr-review-loop` passes (re-validated after the rewrite)

## Phase 4 — Ship

- [ ] `openspec archive add-pr-review-loop -y`
- [ ] One commit, PR, merge — following the same lifecycle every other kit change in this session has used

## Out of scope, tracked separately — PR #15 residual findings

The same dry run also reviewed already-merged PR #15 itself (a different, already-shipped objective) and found it had not fully closed its own bug class, plus smaller issues. Not folded into this change; tracked as its own bugfix cycle:
- Hook-script rollback still breaks under a relative `AGENT_HARNESS_HOME` (different trigger than what #15 fixed).
- `install_hooks`'s `[[ -f "$hook_dest" ]]` misreports a pre-existing directory/dangling symlink as absent; the resulting `unlink()` on a directory raises `IsADirectoryError`, and `rollback.py`'s main loop has no try/except around `rollback_action` — one bad action aborts the rest of that receipt's rollback, confirmed by direct code reading.
- `_entry_is_kit_owned`'s prefix is derived from the *current* run's `hooks_dir`; entries from a different `AGENT_HARNESS_HOME` are misclassified as operator-owned and survive `merge_hooks` instead of being replaced.
- `backup_stamp` has only second-granularity; two installs in the same UTC second silently overwrite each other's backup of pre-existing content.
- PR #15's own `_entry_is_kit_owned` fix used hand-rolled `rstrip`+`startswith` instead of `pathlib.Path.is_relative_to()`, which this codebase already uses for the identical check at `scripts/verify.py:61` — confirmed by direct reading, a real rung-2 miss in the PR that was itself about closing an ownership-boundary bug.
- `init_receipt`'s `$0 $*` is always empty inside the function, so `receipt.json`'s audit `command` field is always wrong.
