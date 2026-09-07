---
name: parallel-worktree-isolation
description: Isolate concurrent or switched software changes into safe Git worktrees and branches before files from independent tasks can mix. Use when an active task, OpenSpec change, or agent work may overlap another change stream.
---

# Parallel Worktree Isolation

## Invariant

One worktree owns one active change stream:

- one task objective;
- one branch;
- one active OpenSpec change, when OpenSpec is used; and
- one eventual pull request.

Do not start or continue a second **independent** change in that worktree.

## Classify before editing

Before editing, inspect the current branch, `git status`, relevant commits/diff, and active change/spec records. Then classify the requested work:

- **Same objective:** continue in the current worktree.
- **Dependent change:** use a stacked branch after its prerequisite has a stable commit, or wait for the prerequisite to merge. Do not pretend it can safely branch from the integration base.
- **Independent change:** create a dedicated feature branch and worktree from the repository's agreed integration base before editing files.

When the relationship is unclear, stop and ask one focused question. Never solve ambiguity by committing both changes together or by staging only part of an uninspected mixed diff.

## Independent-change workflow

1. Identify the target repository, integration base, and short branch name.
2. Keep the current worktree assigned to its existing change.
3. Create the worktree under the global agent-managed root. Use the repository name and a slash-free branch slug so the retention sweeper can discover it:

   ```bash
   git fetch origin
   mkdir -p ~/.agent-worktrees/<repo-name>
   git worktree add -b feature/<change-name> \
     ~/.agent-worktrees/<repo-name>/feature-<change-name> \
     origin/<integration-branch>
   git worktree lock --reason agent-active \
     ~/.agent-worktrees/<repo-name>/feature-<change-name>
   ```

4. Work only on that change in the new directory; run its tests and create its PR independently.
5. After `/ship` creates/updates the PR and the worktree is clean, unlock it with `git worktree unlock <managed-path>`. A global sweeper removes it only after the PR is merged, its HEAD still matches the merged PR head, and the merge grace period has elapsed.

## Existing mixed state

Never assume a clean-looking UI means changes are safely separable. Inspect Git and the active specs first.

- If the independent work is already in commits, create its branch/worktree from the correct base and cherry-pick only the verified commits.
- If work is uncommitted and mixed, first inspect the diff and identify ownership. Ask before state-moving operations such as `git stash`, `git reset`, `git rebase`, or cherry-pick conflict resolution.
- If one change needs unfinished code from the other, keep it as a dependency rather than forcing an independent branch.

## Guardrails

- Do not create a worktree merely because a model is slow; create it when there are concurrent, switched, or isolated change streams.
- Never place a manually managed worktree under `~/.agent-worktrees`; everything below that root is eligible for automatic retention cleanup.
- Do not use the integration worktree for feature edits. Reserve it for sync, review, integration, and merge work.
- Do not force-push, discard, or rewrite another change stream to create isolation.
- Use the repository's branch naming, base branch, commit, and PR rules when they are more specific.
