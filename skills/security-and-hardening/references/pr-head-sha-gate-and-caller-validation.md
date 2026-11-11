# Caller-Validated Review Findings & PR Head-SHA Freshness Gates (`addyosmani/agent-skills` + `paperclipai/paperclip`)

Distilled from `addyosmani/agent-skills` (`★ 112k+`, PR `#736` caller/baseline validation) and `paperclipai/paperclip` (`★ 109k+`, `.agents/skills/check-pr/SKILL.md`).

---

## 1. Caller, Guard & Baseline Validation Gate (`addyosmani/agent-skills`)

Before reporting any code review finding, validate it against the real execution graph:

1. **Trace Callers, Guards & Tests First**: Inspect the upstream callers, middleware/type guards, and unit/integration tests that reach the changed lines. **Drop the finding immediately** if an upstream guard or caller invariant already rules out the hypothetical bug.
2. **Separate Base Defects from PR Regressions**: Distinguish defects that already existed on the base branch (`Pre-existing / Base`) from regressions introduced by the current diff (`Regression`). Never block a focused PR on unrelated legacy code unless the diff directly touches and worsens that path.
3. **Zero Findings Is a First-Class Verdict**: If all invariants hold and tests pass, report **Zero actionable findings**. Never invent nitpicks or speculative hypotheticals just to look thorough.

---

## 2. PR Head-SHA Review Freshness Gate (`paperclipai/paperclip`)

When inspecting a Pull Request (GitHub `gh` or GitLab `glab`) before merge:

1. **Pin to Exact Current `headRefOid`**:
   ```bash
   HEAD_SHA=$(gh pr view <PR_NUMBER> --json headRefOid -q .headRefOid)
   ```
   Never treat a prior bot review (Greptile, CodeRabbit, SonarQube, CodeQL) or CI check as passing unless its check-run is explicitly attached to `$HEAD_SHA` with `status == "completed"` and `conclusion IN ("success", "neutral")`. Any review on an older commit SHA is **stale** after a new push.
2. **Inspect Edited-in-Place Issue Comments (`updated_at`)**:
   GitHub PRs store general bot summaries on the `issues/<PR_NUMBER>/comments` endpoint and often edit a single comment in place on each push. Always sort by `updated_at` descending and inspect the latest summary body in addition to inline `pulls/<PR_NUMBER>/comments`.

---

## 3. GraphQL Batch Review Thread Resolution

After fixing actionable inline review comments and verifying green CI on the new `HEAD_SHA`, query and batch-resolve addressed review threads via GitHub GraphQL:

```bash
# 1. List unresolved review thread IDs
gh api graphql -f query='
query($owner: String!, $repo: String!, $pr: Int!) {
  repository(owner: $owner, name: $repo) {
    pullRequest(number: $pr) {
      reviewThreads(first: 100) {
        nodes {
          id
          isResolved
          comments(first: 1) { nodes { path body } }
        }
      }
    }
  }
}' -f owner="OWNER" -f repo="REPO" -F pr=PR_NUMBER

# 2. Batch-resolve addressed threads in a single GraphQL mutation using aliases
gh api graphql -f query='
mutation {
  t1: resolveReviewThread(input: {threadId: "PRRT_kwDO..."}) { thread { isResolved } }
  t2: resolveReviewThread(input: {threadId: "PRRT_kwDO..."}) { thread { isResolved } }
}'
```
