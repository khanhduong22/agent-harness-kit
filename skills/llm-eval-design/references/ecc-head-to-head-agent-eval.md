# Reproducible Head-to-Head Coding Agent & Runner Evals (`affaan-m/ECC` + `paperclipai/paperclip`)

Distilled from `affaan-m/ECC` (`★ 294k+`, `skills/agent-eval/SKILL.md`) and `paperclipai/paperclip` (`★ 109k+`, `.agents/skills/add-runner-eval/SKILL.md` & `add-product-e2e-eval/SKILL.md`).

---

## 1. Declarative YAML Task Contract (`affaan-m/ECC`)

Every coding agent or prompt-harness benchmark must be defined as a version-controlled, reproducible task fixture pinned to an exact Git commit:

```yaml
name: add-exponential-backoff
description: Add retry logic with jittered exponential backoff to HTTP client
repo: ./target-repo
commit: "a1b2c3d4" # Pin exact commit SHA for deterministic baseline
files:
  - src/lib/http-client.ts
prompt: |
  Add retry logic with exponential backoff and full jitter to all GET requests.
  Max 3 retries, initial delay 500ms, max delay 10s. Preserve existing timeout handling.
judge:
  - type: command
    command: bun test src/lib/http-client.test.ts
  - type: command
    command: bun run typecheck
  - type: grep
    pattern: "Math\\.random|jitter"
    files: src/lib/http-client.ts
```

---

## 2. Git Worktree Isolation Per Trial

Never run competing agents or repeated trials inside a shared working tree:
1. Provision a fresh Git worktree checked out at the pinned `commit` SHA (`git worktree add --detach <tmp-dir> <commit>`) for every `(agent, task, trial_index)` tuple.
2. Execute the agent in headless mode with a hard wall-clock timeout and token/cost capture.
3. Run the deterministic judge suite inside the isolated worktree before tearing it down.

---

## 3. 3-Tier Hybrid Grading Hierarchy

Combine deterministic verification with structural checks before invoking an LLM judge:

| Grader Tier | Mechanism | Role in Verdict |
|---|---|---|
| **1. Deterministic Code/Build Gate** | `pytest`, `bun test`, `tsc --noEmit`, `cargo check` | **Hard Gate**: Any failure immediately marks the trial `FAIL` (`0.0`) |
| **2. Structural / AST / Diff Gate** | `grep` regex, file-touch allowlist, forbidden `@ts-ignore` / `any` check | Verifies the agent solved the problem using the required mechanism without cheating tests |
| **3. Calibrated LLM-as-Judge** | Rubric-scored review of diff readability, edge-case coverage, and architecture alignment | Secondary tie-breaker; must report human-agreement calibration |

---

## 4. Multi-Trial Metrics & Runner Eval Matrix (`paperclipai/paperclip`)

Because coding agents are stochastic, single-run pass rates (`pass@1` on `N=1`) are noisy. Run at least **`3` trials per task** and report the 5-axis comparison table:

| Metric | Definition | Target Gate |
|---|---|---|
| **Pass Rate (`pass@1`)** | Successful trials ÷ total trials (`e.g. 3/3`) | No regression vs baseline harness |
| **Consistency (`pass^k`)** | Probability that all `k` repeated runs pass without flakiness | `100% (3/3)` on core regression suite |
| **Cost per Completed Task** | Total input + output + cache token spend divided by *passing* outcomes | Flag `> 2x` spend increases |
| **Wall-Clock Latency (`p50 / p95`)** | End-to-end execution seconds from prompt dispatch to passing judge | Detect tool-looping regressions |
| **Artifact Completeness** | Presence of required structured outputs, test files, and clean `git status` | Zero untracked scratch files left in repo |
