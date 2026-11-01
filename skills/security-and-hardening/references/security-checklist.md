# Security Review Checklist

Companion reference for `code-review-and-quality`, `security-and-hardening`, and `shipping-and-launch`.

## 1. Authentication, Session & RBAC Boundaries
- [ ] Every protected route/controller verifies both authentication identity and resource-level authorization (no IDOR / missing tenant-scoping `WHERE organizationId = $1`).
- [ ] Session cookies use `HttpOnly`, `Secure`, and `SameSite=Lax` (or `Strict`).
- [ ] JWT validation enforces explicit algorithm whitelisting (`RS256` / `HS256`, never `none`), `exp`, and `iss`.

## 2. Input Validation & Injection Defense
- [ ] All external inputs (`body`, `query`, `params`, `headers`, webhook payloads) are validated against strict runtime schemas (Zod / `class-validator` with `whitelist: true`).
- [ ] Database queries use parameterized statements (`$1`, Prisma/Drizzle typed builders); zero raw string interpolation in SQL or shell commands (`exec` / `spawn`).
- [ ] File uploads validate MIME magic bytes, enforce size limits, and sanitize filenames against path traversal (`../`).

## 3. Secrets, Cryptography & Data Exposure
- [ ] Zero hardcoded API keys, tokens, credentials, or internal IPs in source code, tests, or client bundles (`NEXT_PUBLIC_*` / `VITE_*`).
- [ ] API responses exclude sensitive columns (`passwordHash`, internal tokens, PII) via explicit DTOs or `select` projections.
- [ ] Error handlers return generic safe messages to clients without leaking stack traces or SQL constraint details.
