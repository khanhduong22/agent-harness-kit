---
name: pr-review-loop
description: Spawn a genuinely independent subagent to review a just-shipped PR — one that never saw the implementing session's reasoning, unlike the pre-ship /review phase which runs in the same context that wrote the code. Use as ship's own final step, or on demand against any PR URL.
---

# PR Review Loop

Post-ship phase, spawned by `ship`'s own final step — not one of the six numbered pipeline phases, since it runs *after* `SHIP` completes, not before it.

## Why this exists, and how it differs from `/review`

`/review` (Phase 5, pre-ship) already delegates to Claude Code's bundled `code-review` skill — but it runs inside the same session that implemented the change, with full access to that session's own reasoning for why the diff is correct. That is the author re-reading their own work having already decided it is fine, not independent review.

This skill's entire job is to be the thing `/review` cannot be: a subagent that starts cold, with **only** a PR URL, a repo, and the operational details below — no conversation history, no implementation rationale, no access to why any decision was made. It is not a replacement for `/review`; it is the separation-of-duties half the pre-ship phase structurally cannot provide (`academy.claude.com/courses/ai-native-sdlc-playbook/ai-in-the-pr-review-loop`: "the agent that wrote the code has no way to approve it").

Evidence this matters, not just theory: a manual run of this exact pattern against merged PR #13 in this kit found two real, verified bugs that had passed the implementing session's own extensive self-testing. Fixed in PR #15. A **dry run of this very skill**, against merged PR #15 itself, then found that PR #15's own fixes hadn't fully closed either bug class — a cold reviewer catching that a fix-PR didn't close its own bug is exactly the outcome this skill exists to produce, and it is also what forced this rewrite: the first draft of this skill had real structural gaps, caught the same way.

## Contract

Required inputs, passed explicitly by the caller — **never re-derived**:

- `pr_url` — the exact PR URL, captured from the `gh pr create`/`gh pr edit` output that created or updated it.
- `repo` — `owner/name`, resolved by the caller, not guessed.
- `notify_script_path` — absolute path to `notify-slack.sh` (or the deployment's equivalent). This is operational plumbing, not review context — a script path carries no opinion about whether the code is good, so handing it over does not compromise independence the way a PR summary or implementation rationale would. Without it, the reviewer has no way to report anywhere once it finishes, since by the time it has findings the caller (`ship`) has already returned control and cannot relay them.

**Never call `gh pr list` or any other lookup to figure out "which PR."** The instant more than one PR is open in a repo (the normal state of `index-admin-cms`, which routinely has dozens open), a re-derived guess picks wrong. This session alone shipped three PRs in a row more than once during one conversation.

One optional input:

- `comment` — boolean, **default `false`**. See "Auto-commenting" below.

What the caller must NOT provide: a summary of what the PR does, why it was written, or any framing of what "correct" looks like. That is the line between operational plumbing (fine) and review context (forbidden) — a reviewer primed with the implementer's own story is not independent.

## What the spawned subagent does — one continuous job, no hidden hop

Everything below is **one agent's job**, start to finish. There is no second, further-nested subagent spawn inside this skill — the first draft assumed one implicitly (by scoping only "call code-review" to "the subagent" and leaving steps afterward unscoped), and a dry run showed that ambiguity made the skill unfollowable as written. There is exactly one spawn: `ship` spawns this agent once; this agent does everything through to notifying Slack itself.

1. **Run the review.** Invoke `Skill(code-review, "<pr_url> --repo <repo>")`. Once it loads, its own instructions will show the exact syntax for requesting a specific effort level — follow that syntax, targeting `high`. **Never `ultra`** (see below) — if the loaded instructions show no way to pin a level below `ultra` explicitly, proceed at whatever `code-review` selects and report the actual level used in step 4; do not attempt to force a level through an unverified argument guess.

2. **`code-review` forks asynchronously — wait for real completion, don't report a fork as done.** A dry run confirmed the call returns immediately ("launched, running in the background") while the actual review continues for **10–16 minutes**. There is no `notify_when_idle`-style primitive available to a subagent (that tool is main-conversation-only) and blind `sleep` is harness-blocked. What worked empirically: poll for the fork's completion (e.g. a bounded background-and-check loop, or whatever monitoring primitive your environment documents for a spawned agent/task) until you have the fork's real structured findings — not a "still running" status. Do not synthesize or guess at findings while waiting; do not return early.

3. **Verify the effort level actually used — never silently trust the argument you passed.** `code-review`'s fork self-reports the level it's running at (a dry run saw it announce "Running xhigh effort..." unprompted, because a persisted `effortLevel` in this machine's settings silently overrode the requested `high`). Read that self-report:
   - If it says `ultra` anywhere: **stop, do not let the review proceed to completion if avoidable, and report this as an Important finding on its own** — an automated post-ship step must never run `ultra` (cloud-billed, requires the user's own explicit trigger and consent in-turn), and a config default silently selecting it is a genuine violation the operator needs to know about immediately, separate from whatever the PR's own diff contains.
   - If it says anything else but `high` (e.g. `xhigh`, from the same silent-override mechanism): let the review complete — it is not the prohibited case — but state the actual level used verbatim in your final report. Don't claim "reviewed at high" when it wasn't.

4. **Classify every finding as Important or Nit — one rule, not two competing ones.** `code-review` returns its own severity/category tags (e.g. `High/CONFIRMED`, `Medium/PLAUSIBLE`, `Efficiency`, `Reuse/Conventions`). Use those tags as a signal, but the actual test is always this one, applied by you:
   - **Important** — would break behavior, leak data, or breach a policy. This includes a finding `code-review` tagged as a style/efficiency category if its own text names a specific violated policy (a project's CLAUDE.md/AGENTS.md rule, a named security requirement) — a `Reuse/Conventions`-tagged finding that says "violates this repo's own rung-2 rule" is Important under this test even though its tool-assigned category alone would read as Nit. When `code-review`'s tag and this test disagree, this test wins, always — don't leave it to the tag.
   - **Nit** — everything else, including large, stable-count, pre-existing findings unrelated to this diff (e.g. lint debt the PR didn't introduce). Don't let a big pre-existing count read as a red flag on every future PR that touches the same file — that trains the reader to stop looking at this report at all, the exact failure this split exists to prevent.

5. **Report.** Produce a findings summary grouped Important / Nit, each with file:line, and the actual effort level used (step 3). This is your subagent's own final output — the caller sees it directly once you finish; there is nothing further to "send back into the conversation."

6. **Notify Slack — your job too, using the path you were given.** Invoke `notify_script_path` with the PR link and the Important/Nit counts. If `comment=true` was explicitly passed, also invoke `code-review`'s own `--comment` path first, so findings land as inline PR comments (matching the course's "findings... logged in the PR history" model) — otherwise skip that entirely; do not post anything to the PR by default.

## Never `ultra` — and don't just take a passed argument's word for it

`ultra`-level review is cloud-billed and requires the user's own explicit trigger and consent in that turn. An automated post-ship step has neither. This constraint is enforced by step 3's read-back, not by the argument you pass in step 1 — a dry run showed a requested level can be silently overridden by persisted config with zero error or warning, so trusting the request alone is not a real guarantee.

## Auto-commenting defaults off

This kit deploys into shared repos (`idx-vn/*`) with other team members. `comment=true` by default would mean unattended comments, from the operator's own GitHub identity, on teammates' PRs, on every future ship, forever, starting the moment this skill exists. That is a materially different authorization than the operator's own Slack channel. Flipping it on is a one-line change at the call site (`ship`'s spawn step). Flipping it back off *after* comments have already landed on someone else's PR is not a code change at all — it's an apology. Default stays `false` until the operator explicitly asks for `true`.

## What "working" looks like

Not "the review ran and found nothing." A reviewer that reports zero findings on every PR, forever, is not evidence of quality — it's evidence something about the isolation broke (wrong PR reviewed, `code-review` failed silently, the subagent got context it shouldn't have and just agreed with the implementer). The PR #13 trial and the PR #15 dry run are the baseline: a correctly-isolated reviewer sometimes finds real things the implementing session missed — including, in the PR #15 case, that a fix-PR hadn't fully fixed its own bug class. If a run never finds anything, that's worth investigating, not celebrating.
