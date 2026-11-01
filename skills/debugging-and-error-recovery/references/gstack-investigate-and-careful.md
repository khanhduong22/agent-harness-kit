# gstack `/investigate` & `/careful` Production Guardrails (`garrytan/gstack`)

Synthesized from [`garrytan/gstack`](https://github.com/garrytan/gstack) (`★ 138k+` — `investigate` & `careful`). Use this reference alongside `SKILL.md` for root-cause debugging, flaky/order-dependent test isolation, blast-radius gating, and destructive command protection.

---

## 1. The Iron Law of `/investigate`

> **NO FIXES WITHOUT ROOT-CAUSE INVESTIGATION FIRST.**
> Fixing symptoms creates whack-a-mole debugging. Every patch that masks a symptom without proving the root cause makes the next outage twice as hard to diagnose.

### Critical Investigation Heuristics
1. **The "Identical Helper" Trap**:
   - Before declaring two queries, helpers, or code paths "duplicates" and merging them during a bugfix, **read all of their call sites**.
   - What looks identical at first glance often differs in a caller's transaction boundary, tenant guard, or null-handling scope — and the "duplicate" is the one preserving the invariant.
2. **Git Index Refresh Before Timing / Bisect**:
   - Before timing any command or test that invokes `git` inside a fresh worktree or `git bisect` step, run `git update-index --refresh`. A stale git index forces the first `git status`/`git diff` to pay a full stat scan and distorts benchmark numbers.
3. **Recurring Bugs in the Same File = Architectural Smell**:
   - Run `git log --oneline -20 -- <affected-file>`. If the same file has been "fixed" 3+ times in recent history, stop patching conditionals and redesign the module seam.

---

## 2. Specialized Failure Recipes (Flakes, Polluters & Races)

Never "fix" a failing test by adding `.skip`, increasing timeouts blindly, or rerunning CI until green.

| Failure Signature | Classification | Mandatory Diagnostic Recipe |
|---|---|---|
| Fails intermittently or only in CI | **Flake (`flake`)** | Check wall-clock/timezone assumptions (`new Date()`), unseeded randoms, unawaited async promises, port collisions, or floating-point rounding (`Math.floor` lower bounds) |
| Passes alone (`vitest run a.spec.ts`), fails in full suite | **State Polluter (`polluter`)** | Bisect the test files that run *before* `a.spec.ts` in the same worker shard (`--bail` / binary search file list) to find which prior test mutates a singleton, module-level `Map`, `process.env`, or Redis/DB table without cleanup |
| Corrupted shared state under concurrent requests | **Race Condition (`race`)** | Trace read-modify-write gaps (`SELECT` then `UPDATE` without `FOR UPDATE` or atomic `ON CONFLICT`), or missing Singleflight lock around cache hydration |

---

## 3. Scope Lock & The 3-Strike Escalation Rule

### Scope Lock (Preventing Debug Scope Creep)
Once a root-cause hypothesis is formed (e.g., *"Root cause hypothesis: `src/auth/session.ts` drops `Set-Cookie` on token refresh"*), **lock edits strictly to the affected module directory**.
- Never mix unrelated formatting, variable renames, or feature changes into a bugfix diff.
- **Blast Radius Gate (`> 5 Files`)**: If a bugfix requires modifying more than 5 files, pause and verify whether you are fixing the shared root source or patching symptoms across multiple callers.

### The 3-Strike Rule (Stop Guessing)
If **3 distinct hypotheses** have been instrumented, tested, and falsified:
1. **STOP writing code patches.**
2. Two fixes that shared one underlying premise and failed the same gate prove the premise is false — write the premise down in one sentence and discard it.
3. Escalate with a structured summary of the 3 falsified hypotheses and propose either:
   - **(A)** A deeper architectural investigation across service boundaries, or
   - **(B)** Targeted production telemetry/logging to capture the exact state transition on next occurrence.

---

## 4. Structured Debug Report Format

Conclude non-trivial root-cause investigations with a crisp evidence block:

```text
DEBUG REPORT
════════════════════════════════════════════════════════════
Symptom:         [Exact error / user-observed failure]
Root Cause:      [Exact file:line and mechanism]
Fix:             [Minimal change applied at shared root source]
Evidence:        [Reproduction command + before/after output]
Regression Test: [file:line of test that fails before, passes after]
Status:          DONE | DONE_WITH_CONCERNS | BLOCKED
════════════════════════════════════════════════════════════
```

---

## 5. `/careful` — Destructive Command Guardrails

Treat the following command classes as **High-Risk Boundaries** requiring explicit user intent before execution:

| Risk Tier | Pattern | Why It Is Guarded |
|---|---|---|
| **HARD DENY** | `rm -rf /`, `rm -rf ~`, `rm -rf $HOME`, `git push --force origin main/master` | Catastrophic irreversible loss of workspace or shared branch history |
| **ESCALATE FIRST** | `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, `prisma migrate reset` | Permanent data destruction |
| **ESCALATE FIRST** | `git reset --hard`, `git checkout -- .`, `git clean -fd` | Destroys uncommitted local work in dirty worktrees |
| **ESCALATE FIRST** | `docker system prune -a`, `docker volume rm`, `kubectl delete` | Wipes runtime state, volumes, or active workloads |
| **SAFE EXCEPTIONS** | `rm -rf node_modules`, `.next`, `dist`, `build`, `.turbo`, `coverage`, `__pycache__` | Deterministic build artifacts safely regenerable from source |
