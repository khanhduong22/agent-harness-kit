# Cloudflare Trust-Boundary & Trail of Bits Differential Audit (`cloudflare/security-audit-skill` + `trailofbits/skills`)

Synthesized from [`cloudflare/security-audit-skill`](https://github.com/cloudflare/security-audit-skill) (`★ 55k+`) and [`trailofbits/skills`](https://github.com/trailofbits/skills) (`differential-review` & `agentic-actions-auditor`). Use this reference when conducting deep security reviews, PR differential audits, or CI/CD AI workflow hardening.

---

## 1. Cloudflare's Trust-Boundary Proof Requirement

Never report a speculative pattern match as a confirmed vulnerability. Every security finding must trace **all 5 elements of a real trust-boundary crossing**:

| Element | Required Proof (`file:line`) |
|---|---|
| **1. Lower-Trust Principal** | Who controls the input? (Unauthenticated internet user, tenant B user, external webhook sender, fork PR author, or untrusted LLM output) |
| **2. Accepted Input** | Exact parameter, header, body field, or file path where the input enters (`req.body.orgId`, `${{ github.event.issue.body }}`) |
| **3. Intended Control** | Which validation, RBAC guard, signature check, or escaping step was supposed to stop or scope it — and why it is missing or bypassed |
| **4. Crossed Boundary** | Which higher-trust sink is reached (PostgreSQL query, Redis key namespace, internal VPC `fetch`, shell exec, or cross-tenant state) |
| **5. Concrete Result** | Exact attacker achievement (reads Tenant A's invoices, executes arbitrary bash in CI with `GITHUB_TOKEN`, forged webhook credits balance) |

### Strict Separation: `confirmed` vs `needs_validation`
- **`confirmed`**: Full source-to-sink path traced in code with zero blocking middleware in between (or reproduced locally in an isolated test/sandbox).
- **`needs_validation`**: Plausible issue where runtime/infra enforcement (e.g., Cloudflare WAF rule, API gateway JWT authorizer, DB RLS policy not in repo) could block exploitation. State the exact single verification command needed to confirm or dismiss it.

### 10 Cloudflare Audit Anti-Patterns (Never Flag Without Proof)
1. Do not flag `innerHTML` or `dangerouslySetInnerHTML` when the source is a hardcoded compile-time constant.
2. Do not flag SQL string interpolation when the interpolated variable is a validated enum/allowlist table name.
3. Do not flag missing rate-limiting on internal-only healthchecks or idempotent static asset routes.
4. Do not flag test fixtures, mock tokens, or `.env.example` placeholders as leaked secrets.
5. Do not flag SSRF when the URL host is strictly pinned to a constant internal config and only a validated UUID path segment is appended.
6. Do not flag `Math.random()` used purely for UI animation jitter or cache TTL jitter (only flag when used for tokens, nonces, IDs, or crypto).
7. Do not flag ReDoS without providing a concrete input string that causes catastrophic backtracking within the endpoint's body-size limit.
8. Do not flag client-side route guards as "broken access control" if the backing API endpoints enforce full server-side RBAC.
9. Do not inflate severity when exploitation requires an already-compromised superadmin account.
10. Do not run exploit payloads against production or shared staging services — reproduce only in local tests or OS sandboxes.

---

## 2. Trail of Bits Differential PR Security Review (`differential-review`)

When auditing a commit, PR, or branch diff (`git diff main...HEAD`), follow the **Risk-First Differential Protocol**:

### Phase 1: Git Blame & Regression Check on Deleted Lines
Attackers and rushed refactors frequently re-introduce vulnerabilities by deleting a 2-line guard added in an earlier security fix.
```bash
# Always inspect git log / blame on lines REMOVED in security-sensitive files:
git log -S "<removed_guard_or_function>" -p -n 5 -- <file_path>
```
**Immediate Red-Flag Escalation Triggers:**
- Code removed from a commit whose message mentions `security`, `CVE`, `auth`, `sanitize`, `fix`, or `permission`.
- Validation, `.trim()`, `.safeParse()`, or tenant `WHERE organization_id = ...` clauses removed during a refactor.
- Visibility widened (`private`/`internal` $\to$ `public`/exported route).

### Phase 2: Quantitative Blast Radius Calculation
Before approving a change to a shared helper, middleware, serializer, or DB repository:
1. Count direct and transitive callers across the workspace (`grep` / LSP references).
2. Classify Blast Radius:
   - **LOW (`1–5 callers`)**: Inspect all callers directly.
   - **MEDIUM (`6–30 callers`)**: Verify caller assumptions (nullability, auth pre-conditions, transaction scope).
   - **HIGH (`30+ callers`)**: Require backward-compatible signature + dedicated regression tests covering boundary inputs.

---

## 3. GitHub Actions AI Agent Security Audit (`agentic-actions-auditor`)

When a repository uses AI agents in `.github/workflows/*.yml` (`anthropics/claude-code-action`, `google-github-actions/run-gemini-cli`, `openai/codex-action`, `actions/ai-inference`), audit against **9 CI/CD Prompt-Injection & Sandbox Attack Vectors**:

| Vector | Pattern to Detect | Fix |
|---|---|---|
| **A. Env Var Intermediary** | `env: ISSUE_BODY: ${{ github.event.issue.body }}` passed into an AI prompt without untrusted framing | Never treat `env:` as sanitization; wrap untrusted data in strict XML/JSON data tags and restrict tools to read-only |
| **B. Direct Expression Injection** | `${{ github.event.pull_request.title }}` or `${{ github.event.comment.body }}` interpolated directly inside `prompt:` | Move untrusted text to a read-only file and instruct the agent to treat it strictly as data |
| **C. CLI Data Fetch in Prompt** | Prompt instructs agent to run `gh issue view` or `gh pr view` on external untrusted PRs/issues | Scope agent permissions to `contents: read` and block bash execution when processing untrusted issues |
| **D. `pull_request_target` + Untrusted Checkout** | `on: pull_request_target` combined with `actions/checkout` of `github.event.pull_request.head.sha` | Never check out untrusted PR code inside `pull_request_target` (which has base-repo secrets and write token) |
| **E. CI Error Log Injection** | Passing raw failed test logs from a fork PR directly into an auto-fix AI agent with write permissions | Split untrusted PR test runs from privileged agent workflows |
| **F. Subshell Expansion in Allowed Tools** | Allowing shell commands that evaluate `$()` or backticks on untrusted strings | Use explicit tool allowlists without arbitrary `Bash(*)` |
| **G. Eval of AI Output** | Downstream step runs `eval "${{ steps.ai.outputs.result }}"` or `sh -c` on model output | Parse structured JSON output with `jq` and validate against an allowlist |
| **H. Dangerous Sandbox Flags** | `--yolo`, `danger-full-access`, `--dangerously-skip-permissions`, or `Bash(*)` in CI | Enforce least-privilege tool allowlists (`Read,Grep,Glob`) in CI |
| **I. Wildcard User Allowlists** | `allowed_non_write_users: "*"` or `allow-users: "*"` on public repos | Restrict trigger permissions to `OWNER`, `MEMBER`, or `COLLABORATOR` |
