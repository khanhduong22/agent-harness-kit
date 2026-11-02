# Agent Harness Construction, Progressive Recall & Self-Debug (`affaan-m/ECC` + `thedotmack/claude-mem`)

Distilled from `affaan-m/ECC` (`★ 294k+`, `agent-harness-construction` & `agent-introspection-debugging`) and `thedotmack/claude-mem` (`★ 109k+`, `mem-search` & `agent-cost-report`).

---

## 1. Action Space & Tool Granularity Model (`affaan-m/ECC`)

Agent reliability is governed by four pillars: **Action Space Quality**, **Observation Quality**, **Recovery Quality**, and **Context Budget Quality**.

| Tool Tier | Target Operations | Design Contract |
|---|---|---|
| **Micro-Tools** | High-risk mutations (deploy, DB migration, RBAC/permissions) | Narrow schema-first inputs, explicit pre-condition flags, single side effect |
| **Medium-Tools** | Core coding loops (`read`, `edit`, `grep`, `test`) | Deterministic output shapes, bounded line/byte windows |
| **Macro-Tools** | Multi-step batch pipelines where IPC/round-trip latency dominates | Idempotent execution, structured phase summary output |

### Observation & Error Recovery Contracts
Every tool response and error path should provide deterministic structure so the model never guesses next steps:
- **Observation Shape**: `status` (`success | warning | error`), `summary` (1-line outcome), `next_actions` (actionable follow-ups), and `artifacts` (file paths / IDs).
- **Error Recovery Shape**: `root_cause_hint`, `safe_retry_instruction`, and `explicit_stop_condition` (when to stop retrying and escalate).

---

## 2. 3-Layer Progressive Memory Recall (`thedotmack/claude-mem`)

Never dump full session transcripts or raw observation timelines into the active prompt window. Retrieve historical context in three progressive layers:

1. **Layer 1 — Compact Index (`Search`)**: Query for lightweight index metadata only (`id`, `title`, `type`, `timestamp`, `token_estimate`).
2. **Layer 2 — Narrow Anchor Window (`Timeline`)**: Expand timeline context *only* around specific anchor IDs where causal sequence is unclear.
3. **Layer 3 — Evidence Fetch (`Observations`)**: Load full observation bodies strictly for the filtered IDs cited as direct evidence for the current task.

---

## 3. 4-Phase Agent Self-Introspection Debugging Loop (`affaan-m/ECC`)

When an agent run loops on the same tool, hits token/turn pressure, or fails a fix repeatedly, stop blind retries and execute the 4-Phase Self-Debug Loop:

### Phase 1: Failure Capture
Record before changing any code or retrying:
- Last successful step vs last failed tool/command and exact error output.
- Repeated tool-call pattern observed in the last `N` turns.
- Environment assumptions to verify (`cwd`, git branch/worktree, running ports, file existence).

### Phase 2: Pattern-Matched Root-Cause Diagnosis

| Observed Symptom | Primary Root Cause | Discriminating Check |
|---|---|---|
| Repeated identical tool calls | No-exit observer loop or ignored error output | Inspect last `N` tool calls; restate objective in 1 sentence |
| Degraded reasoning / lost constraints | Context bloat from pasted logs or duplicate plans | Compact at phase boundary; keep only goal, blockers, and evidence |
| `ECONNREFUSED` / timeout | Service down, wrong port, or container network alias mismatch | Check process/container health and port bindings directly |
| `429` / rate-limit storm | Missing exponential backoff or parallel fan-out spike | Count call frequency and serialize or batch requests |
| File missing after write / stale diff | Wrong `cwd`, worktree mismatch, or branch drift | Run `pwd`, `git status -sb`, and check file path on disk |
| Test still fails after "fix" | Patched symptom instead of root cause | Isolate the single failing test and trace callers end-to-end |

### Phase 3: Contained Recovery
Apply the **smallest reversible action** that tests the diagnosis:
1. Restate the real objective in one sentence.
2. Verify actual disk/process state instead of trusting conversation memory.
3. Shrink scope to **one failing command, one file, or one test**.
4. Run one discriminating check before modifying code.

---

## 4. Agent Outcome Economics & Waste Taxonomy (`thedotmack/claude-mem`)

Measure agent efficiency by **Cost per Completed Outcome** (`Σ attributed cost for shipped/completed items ÷ completed item count`), never cost per raw turn.

- **Work Categories**: `Feature` · `Bug fix` · `Incident` · `Maintenance` · `Investigation` · `Experiment`.
- **Rework Lock Invariant**: `Rework` is strictly a `failure_type`, never a work category. Keep the work category as the intended job and tag `failure_type` from the 16-pattern waste taxonomy:
  - *Execution Waste*: `Looping`, `Hedging` (adding caveats when the answer is already verifiable in code), `Wrong turn`, `Premature completion` (claiming done before running verification gates).
  - *Context & Routing Waste*: `Context re-read`, `Model thrash` (using a heavyweight model for trivial lookups), `Fan-out waste` (overlapping subagents), `Duplicate work`.
  - *Quality & Governance Waste*: `Rework`, `Regression`, `Missed requirement`, `Unauthorized action`, `Unnecessary escalation`.
