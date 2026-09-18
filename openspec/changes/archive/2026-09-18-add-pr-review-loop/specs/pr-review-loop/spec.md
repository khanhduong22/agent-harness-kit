# PR Review Loop

## ADDED Requirements

### Requirement: The reviewer SHALL receive the PR identity explicitly, never re-derive it

`pr-review-loop` SHALL require an explicit PR URL and `owner/repo` from its caller. It SHALL NOT call `gh pr list` or any other mechanism to guess which PR to review.

#### Scenario: Multiple PRs are open in the same repo

- **GIVEN** more than one PR is open in the target repository
- **WHEN** `ship` spawns `pr-review-loop` after creating a PR
- **THEN** the reviewer reviews exactly the PR whose URL was passed to it
- **AND** it performs no lookup of "which PR is current" on its own

### Requirement: The reviewer SHALL run at `high` effort, never `ultra`

`ultra`-level review requires the user's own explicit trigger and billing consent. An automated post-ship step SHALL NOT invoke it.

#### Scenario: A post-ship review is spawned automatically

- **GIVEN** `ship` has just created a PR and spawns `pr-review-loop`
- **WHEN** the reviewer invokes `code-review`
- **THEN** it runs at `high` effort
- **AND** no code path in the skill can select `ultra`

### Requirement: The review SHALL run in the background and SHALL NOT gate ship completion

`ship` SHALL spawn `pr-review-loop` as a background task and SHALL NOT wait for it to finish before reporting completion. The PR has already been created by the time review is spawned; the review is advisory only.

#### Scenario: Ship completes before the review finishes

- **GIVEN** `ship`'s PR-creation step has succeeded
- **WHEN** `pr-review-loop` is spawned
- **THEN** `ship` reports the task as shipped without waiting for the review's findings
- **AND** the review continues independently, reporting findings whenever it completes

### Requirement: Findings SHALL be gated by severity before being surfaced

Findings SHALL be split into Important (would break behavior, leak data, or breach a policy) and Nit (everything else), per the course's own model. The kit's own pre-existing lint findings (a known, large, stable-count Nit source) SHALL NOT be surfaced as undifferentiated noise on every review.

#### Scenario: A review surfaces both Important and Nit findings

- **GIVEN** `code-review` returns findings of mixed severity
- **WHEN** `pr-review-loop` reports them
- **THEN** Important and Nit findings are reported as separate, labeled groups
- **AND** the report is not simply the raw, unsorted `code-review` output

### Requirement: Inline PR comments SHALL default to off

`pr-review-loop` SHALL NOT post inline comments to the PR unless explicitly invoked with `comment=true`.

#### Scenario: `ship` spawns the reviewer without specifying `comment`

- **GIVEN** `ship` calls `pr-review-loop` with only `pr_url` and `repo`
- **WHEN** the reviewer completes
- **THEN** no comment is posted to the PR
- **AND** findings are reported to the session and via the kit's Slack notification path instead

#### Scenario: `comment=true` is explicitly passed

- **GIVEN** a caller explicitly sets `comment=true`
- **WHEN** the reviewer completes
- **THEN** findings are posted as inline PR comments, in addition to the session/Slack report
