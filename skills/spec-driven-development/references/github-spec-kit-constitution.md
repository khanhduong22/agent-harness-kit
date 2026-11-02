# Spec-Driven Development Constitution & Governance Gates (`github/spec-kit`)

Distilled from `github/spec-kit` (`★ 145k+`, `.specify/memory/constitution.md` & SDD workflow playbooks). Use when establishing architectural governance, validating implementation plans against project invariants (`Constitution Check`), or designing modular CLI/plugin registries.

---

## 1. The 5 Binding Principles of a Project Constitution

In Spec-Driven Development (`SDD`), the project constitution defines non-negotiable architectural invariants evaluated at plan time before a single line of implementation code is written:

| Principle | Architectural Invariant | Verification Gate |
|---|---|---|
| **I. Layered & Registry-Driven Architecture** | Separate CLI/HTTP transport surfaces from importable domain logic. Wire extensions through a single canonical registry (`register_builtins()`); reject duplicate keys loudly. | Zero transport decorators (`@app.command`, `@Controller`) inside core domain modules. |
| **II. Test-Backed Change & Parity Invariants** | Every behavioral change ships with automated tests. Parametrized parity tests assert that every registered plugin/route has a matching config and test module. | `100%` offline-runnable unit suite (all outbound HTTP stubbed/mocked). |
| **III. Surface & Verb Vocabulary Consistency** | Reuse a closed verb vocabulary (`list`, `add`, `remove`, `search`, `info`, `update`, `verify`). When `--json` is passed, emit strict JSON to `stdout` and route logs to `stderr`. | Destructive actions preview changes before confirmation; "already present" exits `0` idempotently. |
| **IV. Offline-First & Cheap Startup Discipline** | Core scaffolding and `--help` must execute offline with zero eager heavy imports at module load time. Network fetches require explicit timeouts and 1h local cache fallback. | Import-time profiling and stale-cache fallback tests under simulated network failure. |
| **V. Minimal Dependencies & Hash-Tracked Writes** | Zero new runtime dependencies unless stdlib and existing `package.json`/`pyproject.toml` packages are proven insufficient. Track generated files via SHA-256 manifests. | Never overwrite user-modified files silently; reject path traversal and symlink escapes (`Path.is_relative_to`). |

---

## 2. Pre-Implementation `Constitution Check` Gate

Every feature plan (`plan.md` / `design.md`) must include an explicit **Constitution Check** table evaluated before task breakdown:

```markdown
## Constitution Check (Pre-Implementation Gate)
- [ ] **Transport / Domain Separation**: Business logic is testable without spinning up the HTTP/CLI server.
- [ ] **Zero Speculative Dependencies**: Uses existing codebase helpers and stdlib; any new dependency is justified below.
- [ ] **Idempotency & Path Containment**: File writes and DB mutations are idempotent and confined to validated boundaries.
- [ ] **Offline Deterministic Tests**: Test plan stubs all external network calls and covers error/edge paths.
```

> **Governance Rule**: Any conflict between a proposed feature design and a `MUST` principle in the Constitution is classified as **CRITICAL** and blocks implementation until the spec/plan is revised. Never dilute a principle to pass a convenience shortcut.
