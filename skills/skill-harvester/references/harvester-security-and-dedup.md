# Harvester Security Gate, Absorbed Registry & Mapping (`skill-harvester`)

Reference companion for `skill-harvester/SKILL.md` and `scripts/harvest_github_skills.py`.

---

## 1. Absorbed Upstream Registry (Already in `agent-harness-kit`)

The following top-starred GitHub repositories have already been audited, distilled, and integrated into `agent-harness-kit`:

| Upstream Repository | Stars | Absorbed Into (`agent-harness-kit/skills/...`) |
|---|---|---|
| `anthropics/skills` | `★ 121k+` | `frontend-ui-engineering`, `code-simplification`, `skill-doctor` |
| `anthropics/knowledge-work-plugins` | `★ 10k+` | `frontend-ui-engineering/references/claude-design-system-and-anti-slop.md` |
| `mattpocock/skills` | `★ 16k+` | `code-simplification/references/deep-modules-and-domain-modeling.md` |
| `garrytan/gstack` | `★ 76k+` | `debugging-and-error-recovery/references/gstack-investigate-and-careful.md` |
| `multica-ai/andrej-karpathy-skills` | `★ 65k+` | `ponytail/references/karpathy-and-caveman-rules.md` |
| `JuliusBrussee/caveman` | `★ 39k+` | `ponytail/references/karpathy-and-caveman-rules.md` |
| `Leonxlnx/taste-skill` | `★ 9.5k+` | `frontend-ui-engineering/references/impeccable-taste-and-polish.md` |
| `pbakaus/impeccable` | `★ 20k+` | `frontend-ui-engineering/references/impeccable-taste-and-polish.md` |
| `blader/humanizer` | `★ 15k+` | `bilingual-engineering-blog/references/humanizer-anti-ai-writing.md` |
| `cloudflare/security-audit-skill` | `★ 1.2k+` | `security-and-hardening/references/cloudflare-trailofbits-audit.md` |
| `trailofbits/skills` | `★ 4.5k+` | `security-and-hardening/references/cloudflare-trailofbits-audit.md` |
| `vercel-labs/agent-skills` | `★ 25k+` | `next-best-practices/vercel-react-19-patterns.md` |
| `supabase/agent-skills` | `★ 4.2k+` | `backend-performance-optimization/references/supabase-postgres-best-practices.md` |
| `coreyhaines31/marketingskills` | `★ 23k+` | `geo-seo` |
| `addyosmani/web-quality-skills` | `★ 6k+` | `frontend-performance-lighthouse` |
| `addyosmani/agent-skills` | `★ 112k+` | `frontend-performance-lighthouse`, `code-review-and-quality/references/pr-head-sha-gate-and-caller-validation.md` |
| `affaan-m/ECC` | `★ 294k+` | `security-and-hardening/references/ecc-agent-runtime-security-hardening.md`, `context-engineering/references/ecc-agent-harness-and-self-debug.md`, `llm-eval-design/references/ecc-head-to-head-agent-eval.md` |
| `msitarzewski/agency-agents` | `★ 165k+` | `frontend-ui-engineering/references/ui-finish-gate-and-design-contract.md` |
| `github/spec-kit` | `★ 145k+` | `spec-driven-development/references/github-spec-kit-constitution.md` |
| `Graphify-Labs/graphify` | `★ 140k+` | `llm-wiki/references/graphify-knowledge-graph-architecture.md` |
| `browser-use/browser-use` | `★ 119k+` | `browser-testing-with-devtools/references/cdp-ax-tree-and-daemon-patterns.md` |
| `paperclipai/paperclip` | `★ 109k+` | `code-review-and-quality/references/pr-head-sha-gate-and-caller-validation.md`, `llm-eval-design/references/ecc-head-to-head-agent-eval.md` |
| `thedotmack/claude-mem` | `★ 109k+` | `context-engineering/references/ecc-agent-harness-and-self-debug.md` |

---

## 2. Domain-to-Skill Absorption Routing Table

When harvesting a new upstream skill, route its rules into the matching existing skill's `references/` folder first:

| Upstream Domain Keywords | Target Existing Skill in `agent-harness-kit` |
|---|---|
| `react`, `nextjs`, `rsc`, `hydration`, `app-router` | `next-best-practices` |
| `lighthouse`, `cwv`, `lcp`, `cls`, `inp`, `tbt`, `bundle` | `frontend-performance-lighthouse` |
| `ui`, `ux`, `design-system`, `tailwind`, `css`, `accessibility`, `a11y`, `taste` | `frontend-ui-engineering` |
| `postgres`, `sql`, `redis`, `caching`, `singleflight`, `prisma`, `drizzle`, `n+1` | `backend-performance-optimization` |
| `cloudflare`, `nginx`, `caddy`, `docker`, `vps`, `sysctl`, `bbr`, `cdn` | `infra-performance-optimization` |
| `security`, `owasp`, `ssrf`, `xss`, `auth`, `rbac`, `audit`, `cve`, `gh-actions` | `security-and-hardening` |
| `nda`, `opsec`, `pii`, `sanitization`, `red-team`, `leak` | `op-nda` |
| `debug`, `investigate`, `root-cause`, `bisect`, `flake`, `error` | `debugging-and-error-recovery` |
| `refactor`, `simplify`, `architecture`, `deep-modules`, `clean-code` | `code-simplification` |
| `test`, `tdd`, `vitest`, `jest`, `unit-test` | `test-driven-development` |
| `playwright`, `e2e`, `browser-test`, `cypress` | `playwright-e2e-testing` |
| `blog`, `writing`, `humanizer`, `copywriting`, `bilingual` | `bilingual-engineering-blog` |
| `seo`, `geo`, `llms.txt`, `json-ld`, `schema`, `serp` | `geo-seo` |
| `diagram`, `svg`, `architecture-animation`, `c4` | `diagram-director` |
| `eval`, `llm-judge`, `rag`, `prompt-eval` | `llm-eval-design` |

---

## 3. The 8-Point Security & Anti-Slop Checklist

Before absorbing any content from an inspected repository:
- [ ] **Check 1 (Zero Pipe-to-Shell RCE)**: No `curl | sh`, `wget | bash`, `irm | iex`, or `eval $(...)`.
- [ ] **Check 2 (Zero Prompt Injection)**: No hidden instructions attempting to override system rules, conceal actions from the user, or auto-approve destructive tool calls.
- [ ] **Check 3 (Zero Credential Harvesting)**: No commands reading `~/.ssh/*`, `~/.aws/*`, `.env`, or browser cookies without explicit user-initiated opt-in.
- [ ] **Check 4 (Zero Unscoped Destructive Commands)**: No `rm -rf` outside safe build caches (`node_modules`, `dist`, `.next`).
- [ ] **Check 5 (Actionable Engineering Density)**: Contains concrete code examples, tables, or deterministic CLI scripts — not generic "act as a senior developer" filler.
- [ ] **Check 6 (Zero Hardcoded User Paths)**: Replace any machine-specific absolute home paths with `~/`.
- [ ] **Check 7 (Self-Contained / Vendor-Neutral)**: Strip proprietary telemetry hooks (e.g., `gstack-skill-start`, `gstack-skill-end`, external analytics pings) before distilling into `references/`.
- [ ] **Check 8 (`/skill-doctor` Verification)**: Run `python3 ~/agent-harness-kit/skills/skill-doctor/scripts/skill_doctor.py` after integration and confirm **`100/100`**.
