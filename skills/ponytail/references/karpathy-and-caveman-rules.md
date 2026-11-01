# Karpathy's 4 LLM Coding Pillars & Caveman Compression (`andrej-karpathy-skills` + `caveman`)

Synthesized from [`multica-ai/andrej-karpathy-skills`](https://github.com/multica-ai/andrej-karpathy-skills) (`★ 227k+`) and [`JuliusBrussee/caveman`](https://github.com/JuliusBrussee/caveman) (`★ 116k+`). These rules reinforce the 7-Rung Ponytail Ladder to eliminate LLM over-engineering, unrequested code churn, and verbose chat ceremony.

---

## 1. Andrej Karpathy's 4 Pillars of LLM Coding Hygiene

### Pillar 1: Think Before Coding (No Silent Assumptions)
- State your assumptions explicitly. If an instruction has two materially different interpretations, surface the trade-off in 2 lines before writing 500 lines of the wrong architecture.
- If a simpler approach exists (Rung 1–6 of the Ponytail Ladder), push back and propose it immediately.

### Pillar 2: Simplicity First (Minimum Code That Solves the Problem)
- **Zero speculative features**: Do not build configuration flags, plugin hooks, or strategy classes for a single concrete requirement.
- **Self-Check**: *"Would a senior engineer on 3am on-call say this 200-line abstraction should have been a 15-line function?"* If yes, rewrite it as the 15-line function.

### Pillar 3: Surgical Changes (Touch Only What You Must)
When editing existing files:
- **Do NOT "improve" adjacent code, comments, or formatting** outside the task's blast radius.
- **Do NOT delete pre-existing unrelated dead code** without asking (if you notice it, mention it in 1 line at the end).
- **Do clean up 100% of the orphans your own change creates** (unused imports, dead variables, obsolete helper parameters resulting from your edit).
- **The Line-Trace Test**: Every changed line in `git diff` must trace directly to the user's request or a required type/lint fix caused by it.

### Pillar 4: Goal-Driven Execution (`[Step] -> verify: [check]`)
Convert vague imperatives into deterministic verification loops:
- *"Fix the bug"* $\to$ Write failing repro test $\to$ Fix root cause at shared caller source $\to$ Verify test + full suite green.
- *"Refactor module"* $\to$ Verify test baseline before $\to$ Decompose into `< 400 line` cohesive slices $\to$ Verify 100% backward-compatible exports and passing tests after.

---

## 2. Caveman Token & Output Compression (`JuliusBrussee/caveman`)

Apply surgical brevity to both code diffs and technical communication (`~65–75% fewer output tokens` with `100% technical precision`):

### 2.1 Answer-First Structure
```text
[Component / File:Line] [Root Cause / Action] [Concrete Reason / Metric]. [Next Step / Verification].
```
- ❌ **Bloated**: *"I took a close look at the authentication middleware and noticed that there was an issue where the session token wasn't being awaited properly, which could potentially lead to race conditions..."*
- ✅ **Surgical**: *"`src/middleware/auth.ts:42` — Missing `await` on `verifySession()` returned an unresolved Promise, letting unauthenticated requests pass the truthy check. Fixed + added regression test in `auth.spec.ts`."*

### 2.2 What to Drop vs What stays 100% Verbatim
- **DROP**:
  - Hedging (`perhaps`, `it might be worth considering`, `basically`, `just`).
  - Pleasantries and throat-clearing (`Sure! I'd be happy to help with that.`, `Let's dive into...`).
  - Restating the user's prompt back to them before answering.
- **KEEP 100% VERBATIM (Never Compress Away)**:
  - Code blocks, SQL queries, CLI commands, file paths, line numbers, git SHAs, and error messages.
  - Mandatory Architectural Comparison Tables (`Option | Pros | Cons | Performance & Complexity | Recommendation`) and Mermaid diagrams when proposing 2+ architectures.
  - Security warnings, irreversible action confirmations, and handover verification outputs.
