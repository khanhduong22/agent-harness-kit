# Adversarial Review Orchestration Patterns

Companion reference for `doubt-driven-development/SKILL.md`.

## 1. Fresh-Context Challenger Pattern
- Spawn a read-only verifier subagent (`research` or `self` with zero prior reasoning history from the authoring thread).
- Pass only:
  1. The user's original requirement or task contract.
  2. The git diff (`git diff`) or candidate artifact path.
  3. An explicit instruction to find concrete failure modes (race conditions, null/empty inputs, schema mismatches, auth bypasses, silent catch blocks) rather than stylistic nitpicks.

## 2. Three-Question Gate for Findings
Before accepting or rejecting a challenger's finding:
1. **Is it reproducible?** Can we construct a concrete input or concurrency sequence that triggers it?
2. **What is the blast radius?** Does it corrupt state, leak data, crash rendering, or violate the API contract?
3. **What is the minimal root-cause fix?** Fix at the shared source boundary rather than layering defensive wrappers at every call site.
