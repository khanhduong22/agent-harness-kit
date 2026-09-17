---
name: arena-round-table
description: >-
  Multi-agent "Arena - Discuss Round Table" workflow. Orchestrates Claude Code
  and AGY CLIs in structured debate rounds to solve complex problems. Use when
  facing high-complexity decisions, architecture tradeoffs, or when you need
  adversarial review from multiple "expert" perspectives. Triggers on
  "arena", "round table", "debate this", "multi-agent discuss".
---

# Arena — Discuss Round Table

Structured multi-agent debate protocol for high-complexity decisions.
The orchestrating agent invokes other CLI agents as "experts" in a
structured round-table discussion with evidence-based claims.

---

## Roster

| Seat | CLI | Model | Strength | Role |
|---|---|---|---|---|
| **Architect** | `claude -p --model <fable/opus>` | Fable 5 / Opus 5 | Enterprise structure, research breakthroughs, UX | Proposes architecture, challenges feasibility |
| **Auditor** | Current session (AGY) | Gemini | Logic, audit, scanning, fact-checking | Verifies claims, finds gaps, runs evidence checks |

> The orchestrating agent (whoever the user is talking to) always plays **Auditor**.
> The other CLI is invoked as **Architect** via shell command.
>
> If Codex CLI is available, it takes **Auditor** and AGY becomes **Workhorse**
> (bulk scanning, multi-solution cooking, document grinding).

---

## Invocation Protocol

### Calling Claude Code from AGY
```bash
claude -p \
  --model claude-fable-5 \
  --output-format text \
  --max-budget-usd 0.50 \
  "CONTEXT: <shared_context>

   ROLE: You are the Architect in a Round Table debate.
   QUESTION: <debate_question>
   CONSTRAINTS: <locked_decisions_and_limits>
   PRIOR_CLAIMS: <previous_round_claims>

   Respond with:
   1. POSITION: Your stance (1-2 sentences)
   2. CLAIMS: Numbered list of specific, falsifiable claims
   3. EVIDENCE: For each claim, cite source (doc, code, benchmark, or reasoning)
   4. RISKS: What could go wrong with your approach
   5. CHALLENGE: One question for the Auditor"
```

### Calling AGY from Claude Code
```bash
agy -p \
  --model gemini-2.5-pro \
  "CONTEXT: <shared_context>
   ROLE: You are the Auditor in a Round Table debate.
   ..."
```

---

## Round Structure

```
Round 0: CONTEXT SYNC
  → Orchestrator writes shared_context.md (locked decisions, evidence, constraints)
  → All agents receive identical context

Round 1: OPENING POSITIONS
  → Each agent states position + claims + evidence
  → Orchestrator collects into claims_matrix.md

Round 2: CROSS-EXAMINATION
  → Each agent challenges the other's claims
  → Must cite specific evidence to refute (not just "I disagree")
  → Orchestrator verifies checkable claims (grep, test, benchmark)

Round 3: SYNTHESIS (optional, if no consensus after Round 2)
  → Orchestrator proposes merged solution
  → Each agent rates: ACCEPT / ACCEPT_WITH_MODIFICATIONS / REJECT
  → If REJECT, must provide specific counter-evidence

FINAL: VERDICT
  → Orchestrator writes verdict.md with:
     - Winning position (or merged)
     - Evidence summary
     - Locked decisions
     - Open risks acknowledged
```

**Max rounds: 3** (prevent infinite debate). If no consensus → Orchestrator
(human's current agent) makes the call and documents dissent.

---

## Evidence Rules

### Claims must be one of:

| Type | Example | Verification |
|---|---|---|
| **Code Evidence** | "Function X already handles this" | `grep_search` or `view_file` to verify |
| **Doc Evidence** | "Official docs say..." | URL + quote |
| **Benchmark** | "Approach A is 3x faster" | Must show numbers or cite source |
| **Reasoning** | "This violates SRP because..." | Logical argument, falsifiable |
| **Experience** | "In production, this pattern causes..." | Accepted but weighted lower |

### Prohibited:
- ❌ Vague claims: "This is better" (better HOW? measured HOW?)
- ❌ Appeal to authority: "Best practice says..." (WHOSE best practice? WHERE documented?)
- ❌ Hallucinated evidence: Making up benchmark numbers or fake URLs
- ❌ Scope creep: Introducing new requirements not in shared_context

---

## Artifacts

All debate artifacts go in `openspec/arena/<topic>/`:

```
openspec/arena/<topic>/
├── shared_context.md     # Round 0: locked decisions, constraints, evidence
├── claims_matrix.md      # Round 1-2: all claims + verification status
└── verdict.md            # Final: winning position + rationale + risks
```

### claims_matrix.md format:
```markdown
| # | Agent | Claim | Evidence Type | Verified? | Notes |
|---|---|---|---|---|---|
| 1 | Architect | "Prisma doesn't support..." | Doc Evidence | ✅ Confirmed | URL: ... |
| 2 | Auditor | "Existing helper covers this" | Code Evidence | ❌ Refuted | Helper only handles X, not Y |
```

---

## Orchestrator Checklist

When the user triggers an Arena session:

1. **[ ] Identify the question** — What specific decision needs debate?
2. **[ ] Write shared_context.md** — Locked decisions, constraints, prior evidence
3. **[ ] Choose models** — Fable for research/architecture, Opus for UX/design
4. **[ ] Run Round 0** — Sync context to all agents
5. **[ ] Run Round 1** — Collect opening positions
6. **[ ] Build claims_matrix.md** — Log all claims
7. **[ ] Run Round 2** — Cross-examination + evidence verification
8. **[ ] Verify checkable claims** — Use grep/test/docs to fact-check
9. **[ ] Run Round 3 if needed** — Synthesis attempt
10. **[ ] Write verdict.md** — Document decision + dissent + risks

---

## Budget Guidelines

| Phase | Expected cost | Notes |
|---|---|---|
| Round 0 (context sync) | ~$0.00 | Local file, no API call |
| Round 1 (opening) | ~$0.20-0.50 per agent | One prompt each |
| Round 2 (cross-exam) | ~$0.20-0.50 per agent | One prompt each |
| Round 3 (synthesis) | ~$0.10-0.20 per agent | Short accept/reject |
| **Total per Arena** | **~$1.00-2.00** | Pre-implement phase, cheap |

> As bro says: "sự phối hợp chỉ nằm ở các phase pre-implement — không tốn
> nhiều tokens so với implement phases."
