---
name: ship
description: Verify all quality gates, archive any active OpenSpec change, create or update a PR for the current work, following the repo's own commit/branch conventions. Use when the user asks to ship, commit and push, open a PR, or invokes /ship.
---

# Ship

Final phase of the pipeline: `OPENSPEC (/opsx) → PLAN (/plan-sdlc) → BUILD (/build) → VERIFY (/test) → REVIEW (/review) → SHIP (/ship)`.

Invoking this skill is explicit authorization to push the current task branch and open/update its PR, once gates pass — but only for the scope actually worked on this session. It is not blanket authorization to push unrelated branches or force-push over a PR the user hasn't reviewed.

## 1. Is there already an open PR for this exact objective?

Before creating anything new: `gh pr list --state open` and check whether an open PR already covers the same task/objective as the current work (not just the same repo). If yes — **push to that PR's branch, don't open a new one.** Opening a second PR for the same objective while one is already open is the default mistake to avoid here.

## 2. The repo's actual commit convention — check, don't assume

Some repos enforce **exactly one commit per PR** via a `commit-msg`/`pre-push` hook (check `.husky/`, `.git/hooks/`, or CI config) or written team convention. If so:

- Never `git commit --amend` blindly across unrelated work; instead, when updating an existing PR's branch with new changes, `git reset --soft <merge-base-with-target>` (compute the real merge-base, don't guess — `git merge-base HEAD <target>`) then recommit everything as one commit with an updated message covering the full scope.
- If the base branch has moved forward since the PR's branch was created (another PR merged in the meantime) and touches files this branch also touches, `git reset --soft` alone can silently *revert* that other merged work in the new commit — rebase onto the new base first (`git rebase origin/<target>`), resolve/verify no unintended conflicts, then squash. Verify the resulting file content (not just diff stat) still contains both sets of changes before committing.
- If a hook enforces a branch-name prefix (e.g. must start with `feature/`, `bugfix/`, or `hotfix/`), check it *before* trying to push (read the hook script directly, don't guess the allowed prefixes) and rename the local branch to comply rather than fighting the hook.
- Stage files explicitly by path; don't use `git add -A`/`git add .` for a commit meant to represent one deliberate, reviewable change.

If no such convention exists, use normal judgment — a coherent commit per logical unit of work is fine.

## 3. One worktree, one objective

If this task is a genuine continuation of an already-open PR's objective (not a new independent change), don't create a new stacked branch for it — go back to that PR's branch directly (step 2 covers the recommit mechanics). Reserve a new branch/PR for work that's actually independent, or that must build on a *prerequisite* PR that hasn't merged yet (in which case: load `parallel-worktree-isolation`, target the prerequisite's branch as base, and say plainly in the PR description that it's stacked and which PR to merge first).

## 4. Run every gate for real

Don't report a gate as passed without having run it this turn. If the repo has a combined verify script, run it (or its constituent steps if running the whole thing needs infra not available here — say explicitly what was skipped and why, e.g. "e2e needs a live server; started one and ran it" versus "e2e needs a live server that isn't available, skipped"). Distinguish pre-existing/unrelated failures from ones this change introduced — see the `test` skill for how.

For UI/CMS changes (`index-admin-cms`), skipping browser E2E testing or leaving unchecked manual QA items in the PR description is strictly prohibited. The full Playwright E2E suite (`npx playwright test`) must pass with video recording enabled.

If a gate genuinely can't run in this environment (missing external service, no docker, etc.), say so plainly rather than silently marking it done, and let the user decide whether to accept partial verification or provide the missing piece.

## 5. Archive the OpenSpec change (if one was used)

`openspec archive <change-name> -y` before the final commit, so the archive move and spec updates are part of the same commit as the code. If `openspec archive` fails on a header mismatch for a `MODIFIED` requirement, fix the delta's header to match the existing spec's exact text (see the `opsx` skill) — don't force past validation errors.

## 6. Commit, push, PR

Apply the commit convention from step 2, push (`--force-with-lease`, never bare `--force`, when updating an existing branch — this fails safely if someone else pushed in the meantime instead of silently clobbering it), and create or update the PR with a summary (what changed, why) and a test-plan checklist reflecting what was actually verified in step 4, including any known pre-existing issues found along the way that are out of scope for this PR. For UI/CMS (`index-admin-cms`), the PR test checklist table MUST include the Google Drive video URL, and you must invoke `./scripts/notify-slack.sh` with the video link and flow steps.

## 7. Spawn the post-ship reviewer (background — does not block completion)

Once step 6 has actually created or updated the PR: spawn `pr-review-loop` as a **background** subagent with exactly three inputs — the exact PR URL from step 6's own `gh pr create`/`gh pr edit` output, the resolved `owner/repo`, and the absolute path to `notify-slack.sh` in this checkout. Never let it re-derive "which PR" itself, and never hand it anything beyond those three — no summary of the change, no rationale for why it's correct.

This does not gate anything and does not delay reporting the task as shipped. The PR already exists by the time this fires; a real review takes 10–16 minutes, arriving well after this conversation has moved on. Report the ship as done without waiting for it — the spawned reviewer notifies Slack itself once it finishes, since `ship` will have already returned by then.

Skip this step only if `pr-review-loop` isn't installed in this deployment (a workspace running an older kit version) — say so plainly rather than silently omitting it.

## 8. Never take these actions without the user's go-ahead in this conversation

Deleting branches (local or remote) that aren't scratch branches you created this session, closing other PRs, or force-pushing to a branch with review activity from someone other than you. Offer these as follow-ups instead of doing them silently.
