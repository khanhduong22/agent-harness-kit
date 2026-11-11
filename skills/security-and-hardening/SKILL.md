---
name: security-and-hardening
description: "Audits and hardens production applications, APIs, CI/CD workflows, distributed concurrency paths, and AI/LLM features against security vulnerabilities and race conditions. Use when reviewing auth/RBAC, untrusted input, webhooks, payments/idempotency, SSRF, supply chain lockfiles, PR security diffs, or LLM/agent tool boundaries."
---

# Production Security, Concurrency & Differential Audit

High-signal security and production-readiness invariants beyond baseline framework defaults. Apply during feature design, differential PR audits, and pre-launch hardening.

---

## 1. Trust Boundaries, Auth & Data Exposure

1. **Resource-Level Authorization (Anti-IDOR)**: Every read, mutation, and batch endpoint must scope queries by authenticated `userId` / `organizationId` at the repository/SQL layer (`WHERE id = $1 AND tenant_id = $2`), never solely by route middleware or UI visibility.
2. **Strict Schema Whitelisting**: Validate `body`, `query`, `params`, and webhook payloads at the transport boundary (`zod` / `class-validator` with `whitelist: true, forbidNonWhitelisted: true`) to block mass-assignment and prototype pollution.
3. **SSRF & Outbound Fetch Containment**: Never fetch user-supplied or webhook-supplied URLs directly; enforce protocol allowlists (`https:` only), resolve DNS once, and block RFC1918/loopback/link-local metadata ranges (`127.0.0.0/8`, `10.0.0.0/8`, `169.254.169.254`, `::1`).
4. **Token, Cookie & Webhook Hygiene**:
   - Store refresh/session tokens in `HttpOnly; Secure; SameSite=Lax|Strict` cookies; whitelist JWT algorithms explicitly (`RS256`/`ES256`/`HS256`, never `none`).
   - Verify third-party webhook HMAC signatures against the **raw unparsed request body** using constant-time comparison (`crypto.timingSafeEqual`) + timestamp replay window (`<= 300s`).
   - Redact credentials, `Authorization` headers, cookies, and PII from structured logs and client error envelopes. If a secret ever hits git history, **rotate/revoke immediately** before rewriting history.

---

## 2. Distributed Concurrency, Race Conditions & Idempotency (Tier-1 PRR)

Whenever code mutates balances, inventory, subscriptions, state machines, or external side-effects:
1. **Distributed Idempotency Keys**: Require a client-supplied `Idempotency-Key` (`UUIDv4`/`ULID`) on mutating `POST`/`PATCH` endpoints; claim keys atomically (`INSERT ... ON CONFLICT DO NOTHING` or `SET key NX EX 86400`) so network retries and double-clicks replay cached responses without duplicate side-effects.
2. **Atomic State Transitions & Locking**: Prevent TOCTOU check-then-act races via single-statement conditional updates (`UPDATE accounts SET balance = balance - $1 WHERE id = $2 AND balance >= $1`), `SELECT ... FOR UPDATE SKIP LOCKED`, or bounded TTL distributed locks with fencing tokens.
3. **Transactional Outbox & Bounded I/O**: Never publish irreversible external webhooks/emails inside an uncommitted DB transaction without an outbox or idempotent reconciliation step. Enforce explicit `AbortSignal.timeout(...)`, bounded retries with jitter, and dead-letter handling on all external calls.

---

## 3. Securing AI, RAG & Agentic Features (OWASP LLM Top 10)

1. **LLM01 (Prompt Injection)**: System prompts are NOT security boundaries. Enforce tenant isolation, RBAC, and destructive-action gates deterministically in host code, never by asking the model to obey rules.
2. **LLM05 (Untrusted Model Output)**: Never pass LLM output into `eval`, raw SQL, shell strings (`exec`), `innerHTML`, or unvalidated file paths. Parse structured JSON via strict schemas (`CommandSchema.parse(...)`) and dispatch only allowlisted actions.
3. **LLM02 / LLM08 (Cross-Tenant & RAG Leakage)**: Keep secrets and cross-tenant records out of prompt contexts; partition vector/BM25 queries strictly by authenticated `tenant_id` filter before similarity ranking.
4. **LLM06 / LLM10 (Excessive Agency & Unbounded Cost)**: Scope agent tools to least privilege, pass CLI arguments as argv arrays (never shell-interpolated strings), cap token/iteration budgets, and require explicit human confirmation before irreversible operations.

---

## 4. Supply Chain & CI/CD Hardening

- Commit a single authoritative lockfile and enforce frozen installs in CI (`bun install --frozen-lockfile` / `npm ci`).
- Audit reachable `HIGH`/`CRITICAL` CVEs (`trivy fs`, `semgrep`, `gitleaks`) and block untrusted PR branches from `pull_request_target` secret exposure or unescaped `${{ github.event.* }}` shell interpolation in GitHub Actions.

---

## 5. Deep Audit References (`references/`)

- [`references/cloudflare-trailofbits-audit.md`](references/cloudflare-trailofbits-audit.md) — Cloudflare 5-Element Trust-Boundary Proof (`confirmed` vs `needs_validation`), Trail of Bits differential PR security review (`git log -S` on deleted guards + blast-radius tracing), and 9 GitHub Actions AI Agent CI/CD attack vectors.
- [`references/ecc-agent-runtime-security-hardening.md`](references/ecc-agent-runtime-security-hardening.md) — AI agent runtime trust boundaries, CLI `argv` separation, portable filesystem containment, and pre-log secret redaction.
- [`references/pr-head-sha-gate-and-caller-validation.md`](references/pr-head-sha-gate-and-caller-validation.md) — Caller/guard validation before reporting findings, pinning bot/CI checks to exact `$HEAD_SHA`, and GitHub GraphQL batch thread resolution.
- [`references/security-checklist.md`](references/security-checklist.md) — Pre-commit & pre-release security gate checklist.
