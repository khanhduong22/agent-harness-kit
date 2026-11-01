# Testing Patterns & Anti-Fragile Suite Design

Companion reference for `test-driven-development/SKILL.md`.

## 1. Behavior Over Implementation Details
- Assert observable outputs, state transitions, HTTP responses, and DOM semantics (`getByRole`, `getByLabelText`) rather than internal private method calls or fragile CSS class names.
- Follow **Arrange -> Act -> Assert (AAA)** with one clear behavioral assertion group per test.

## 2. Boundary & Edge-Case Matrix
- **Empty / Null / Zero**: `[]`, `""`, `null`, `0`, `NaN`.
- **Boundary Thresholds**: `min - 1`, `min`, `max`, `max + 1` (use `Math.floor` / `Math.ceil` on jittered TTL bounds to prevent floating-point flakiness).
- **Concurrency & Idempotency**: Duplicate webhook/submission delivery (`Promise.all([submit(), submit()])`) asserts exactly one state transition or side effect.
- **Error & Recovery**: Upstream timeout, HTTP 429/500, or malformed JSON returns deterministic fallback or typed error.

## 3. Mocking Discipline
- Prefer real in-memory/test-container databases or pure domain functions over deep mock chains.
- Mock only external I/O boundaries (third-party HTTP APIs, payment gateways, clock/timers, email/push dispatchers).
