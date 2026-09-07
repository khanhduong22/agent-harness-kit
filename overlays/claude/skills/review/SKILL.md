---
name: review
description: Run a full quality/simplification/performance/security review of the current diff before shipping. Use when the user asks for a code review, invokes /review, or when GEMINI.md-style rules call for a "quad-skill" review before ship.
---

# Quad-Axis Review

Phase 5 of the pipeline: `OPENSPEC (/opsx) → PLAN (/plan-sdlc) → BUILD (/build) → VERIFY (/test) → REVIEW (/review) → SHIP (/ship)`.

## Don't reinvent — delegate to Claude Code's own review skills

Claude Code already ships review skills that cover this ground; use them instead of building a review from scratch:

1. Invoke the **`code-review`** skill at `high` effort on the current diff. It covers correctness bugs and reuse/simplification/efficiency findings across the standard multi-dimension pass — this satisfies the "quality" and much of the "performance" axis GEMINI-style rules call for.
2. Invoke the **`simplify`** skill if `code-review` surfaced non-trivial reuse/simplification findings worth a dedicated pass, or if the user specifically wants refactoring/readability cleanup applied, not just identified.
3. For the **security** axis specifically: if a `security-review` skill or equivalent is available, invoke it; otherwise treat this as an explicit OWASP-style pass within `code-review` (injection, auth/authz gaps, secrets, unsafe deserialization, SSRF) — call it out as a distinct finding category in the report even though it ran inside the same tool call.
4. For a **performance** axis beyond what `code-review` already flags (N+1 queries, missing indexes, unnecessary round-trips): note these explicitly if the diff touches data-access code; don't skip this just because `code-review` didn't happen to surface one.

## Output

A single findings report grouped by axis (quality, simplification, performance, security), each finding with file:line and a one-line fix recommendation. If `--fix` behavior is wanted, apply fixes the way `code-review --fix` already does, then re-verify (`/test`) after applying.

## Gate

Stop for confirmation before `/ship` unless running autonomously — a clean review is not itself authorization to ship; the user decides when findings are acceptable to proceed past.
