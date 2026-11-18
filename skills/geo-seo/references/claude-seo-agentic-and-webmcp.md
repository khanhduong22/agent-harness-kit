# Agentic Browsing, WebMCP, Discovery & Markdown Playbook

Distilled from `AgriciDaniel/claude-seo` (`skills/seo-agentic/` + 6 references, MIT). Strips plugin/SaaS lock-in and serves as the deterministic operational reference alongside `scripts/agentic_and_schema_check.py`.

> **Core Framing**: Agent readiness is **accessibility + performance + deliberate access policy**, with a Markdown and discovery layer on top. WebMCP is a progressive enhancement for sites with forms or transactions, never a substitute for semantic HTML and a clean accessibility tree (WebKit opposes WebMCP; Mozilla is neutral; only ChatGPT desktop's built-in browser calls imperative tools by default).

---

## 1. Priority Order & Honest-Reporting Guardrails

Fix strictly in **P0 → P1 → P2 → P3** order. Never recommend lower-priority additions while a measured P0 fails.

| Priority | Requirement | Inspection Signal |
|---|---|---|
| **P0** | Accessible names, valid ARIA roles, zero interactive elements hidden from accessibility tree | Lighthouse `agent-accessibility-tree` |
| **P0** | Visual stability: `CLS <= 0.1` (`score >= 0.9`) | Lighthouse `cumulative-layout-shift` |
| **P0** | Primary content present in initial HTML without JS execution | `words_without_js >= 150`, no empty JS shell |
| **P0** | `robots.txt` reachable (never `5xx` or unguarded `429`), explicit AI groups by purpose | `robots-reachable`, `robots-ai-groups` |
| **P0** | WAF allows verified bots & signed agents (IP ranges / Web Bot Auth); zero CAPTCHAs on content pages | WAF logs + unverified UA matrix |
| **P1** | Auth-protect private paths (`/checkout/`, `/account/`) — never rely on `robots.txt` | `robots-user-agents` |
| **P1** | `Content-Signal` repeated inside every relevant `User-agent` group (RFC 9309 scoping) | `content-signal` |
| **P1** | `/llms.txt` valid if published; unknown paths return real `404` (never catch-all `200` HTML) | `llms-txt`, `http-404` |
| **P1** | Markdown via `Accept: text/markdown` + `Vary: Accept`, `.md` URL, or `<link rel="alternate">` | `markdown-delivery` |
| **P1** | Visible, persistent confirmation states; zero hover-only menus or focus traps | Manual UI/DOM check |
| **P1 / P2** | Imperative WebMCP tools (`document.modelContext`) bound to UI handlers; P1 if transactional + tool safety audit | `webmcp-tools`, `webmcp-entry-point` |
| **P2 / P3** | RFC 9727 API Catalog, RFC 9728/8414 OAuth metadata, A2A `agent-card.json`, ARD `ai-catalog.json`, UCP | `well-known:*`, `ard-catalog` |

**Honest-Reporting Rules**:
- Never promise ranking, citation, or traffic gains from `llms.txt`, `Content-Signal`, `Google-Extended`, Markdown negotiation, or WebMCP.
- Never claim Google Search reads `llms.txt` or `Content-Signal` (Google ignores both).
- Never cite vendor-claimed WebMCP or Cloudflare Markdown "token efficiency" percentages as independent benchmarks.
- Always label `Content-Signal`, WebMCP, ARD, MCP Server Card, and Web Bot Auth as **draft/proposal** with verification date (`2026-09-23` baseline; refresh if >60 days old).

---

## 2. Lighthouse Agentic Browsing Category (`13.5.0`)

Executed via PSI v5 (`category=AGENTIC_BROWSING`) or `npx lighthouse@latest <url> --only-categories=agentic-browsing --output=json` (lab-only; never in CrUX).

### Fraction Scoring Math (`X/N`, Never `%`)
- `categoryScoreDisplayMode: "fraction"` — report **`X/N`**, never convert to `%` and never assume `N`.
- Skips `hidden`, `manual`, and `notApplicable` audits; `informative` audits never count in `N`.
- Every remaining audit adds `1` to `N` (`max N = 6`) and passes at `score >= 0.9`.

| Audit ID | Scoring Rule | Key Details |
|---|---|---|
| `agent-accessibility-tree` | Binary (`0` or `1`) | Fails if any of 33 axe rules fail (`button-name`, `label`, `link-name`, `select-name`, `document-title`, `aria-*`, `duplicate-id-aria`, `tabindex`, `svg-img-alt`, etc.). Contrast/landmarks excluded. |
| `cumulative-layout-shift` | Binary (`score >= 0.9`) | Numeric lab CLS (`<= 0.1` target). |
| `llms-txt` | `4xx`=N/A; `5xx`/err=`0`; else `1`/`0` | Requires H1 (`^\s*#\s+.+`), >=1 Markdown link (`[..](..)`), and `>= 50` chars. HTML `200` catch-all fails in practice. |
| `ard-schema` | N/A unless signalled or `200` | Errors=`0`; warnings only=`0.9` (pass). Validates ARD `ai-catalog.json`. |
| `webmcp-registered-tools` | Always `informative` (N/A if unsupported) | Lists runtime imperative + declarative tools (including 3rd-party scripts). |
| `webmcp-schema-validity` | `0` error / `0.5` warn (fails) / `1` clean | Error: missing tool name/desc or required param name. Warn: param missing title/desc. |
| `webmcp-form-coverage` | Informative until 100% forms annotated, then `1` | Annotating one form triggers `webmcp-schema-validity` into `N` — annotate completely or omit. |

### Page-Level Accessibility Criteria
1. **Native HTML First**: `<button>` for actions, `<a href>` for links, native `<input>`/`<select>` (avoid `<div onclick>` or `contenteditable` hacks).
2. **Accessible Names & Target Size**: Every control needs `<label for>`, `aria-label`, or `aria-labelledby`; hit targets `>= 24x24` CSS px (WCAG 2.2 AA; `44x44` preferred).
3. **Zero Transparent Overlays**: Vision models discard elements covered by full-card wrappers, persistent cookie portals, or `position: absolute; inset: 0` trackers.
4. **Layout & Selector Stability**: `cursor: pointer` only on actionable controls; preserve landmarks (`<main>`, `<nav>`, `<article>`) and semantic `data-*` attributes; eliminate hover-only menus, infinite scroll without paginated links, closed shadow DOM, and brief toast-only confirmations.

---

## 3. WebMCP (`W3C Web Machine Learning CG Draft`)

Status: Origin trial in Chrome/Edge (`M149–M156`); **not** a W3C Standards Track spec (`WebKit: oppose #670`, `Mozilla: neutral #1412`).

- **Entry Point**: Prefer `document.modelContext` (secure contexts), feature-detecting legacy `navigator.modelContext`:
  ```js
  const mc = document.modelContext ?? navigator.modelContext;
  if (mc?.registerTool) {
    const ctrl = new AbortController();
    await mc.registerTool({
      name: "search_articles",
      description: "Search published articles by keyword. Returns titles and URLs.",
      inputSchema: {
        type: "object",
        properties: { query: { type: "string", description: "Search keywords" } },
        required: ["query"]
      },
      annotations: { readOnlyHint: true },
      async execute({ query }) {
        const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        return { content: [{ type: "text", text: JSON.stringify(await res.json()) }] };
      }
    }, { signal: ctrl.signal });
  }
  ```
- **Declarative Attributes (Chrome only)**: `toolname`, `tooldescription`, `toolautosubmit` on `<form>`, `toolparamdescription` on controls; distinguish agent runs via `SubmitEvent.agentInvoked` and `respondWith(Promise)`.
- **Mandatory Tool Safety Rules**:
  1. Bind every tool to the **exact same UI endpoint, validation, and auth** — zero privileged back doors.
  2. Set `consequentialHint: true` on purchases/sends/deletes **and** keep explicit human confirmation.
  3. Set `untrustedContentHint: true` when returning user/third-party content (prompt-injection defense).
  4. Never wildcard `exposedTo`; keep consequential tools out of cross-origin iframes (`allow="tools"`).
  5. **P1 Security Red Flag**: Never write tool descriptions instructing the agent to skip confirmation (e.g., *"no need to confirm with the user"*).

---

## 4. Discovery Protocols, `llms.txt` & Content Negotiation

### Standards Status & Discovery Order
- **ARD `ai-catalog.json` (1.0)**: Discovered in order: (1) `robots.txt` `Agentmap: <url>`, (2) `<link rel="ai-catalog">`, (3) HTTP `Link: <...>; rel="ai-catalog"`, (4) `/.well-known/ai-catalog.json`. Requires `specVersion: "1.0"`, `entries` array (`identifier: urn:air:<publisher>[:ns]:<name>`, `displayName`, `type`, exactly one of `url` or `data`, 2–5 `representativeQueries`), and **no** top-level `collections`.
- **MCP Discovery**: `/.well-known/mcp.json` (SEP-1649) was **closed**; SEP-2127 proposes MCP Server Cards at `<mcp-endpoint>/server-card` referenced inside `ai-catalog.json` (`type: "application/mcp-server-card+json"`).
- **Published `/.well-known/` Endpoints (only if service exists)**:
  - `/.well-known/api-catalog` (RFC 9727, `application/linkset+json`)
  - `/.well-known/oauth-protected-resource` (RFC 9728) & `/.well-known/oauth-authorization-server` (RFC 8414)
  - `/.well-known/agent-card.json` (A2A) & `/.well-known/ucp` (UCP commerce)
  - **Soft-404 Trap**: Any `/.well-known/*` or `/llms.txt` returning `200 text/html` misleads discovery clients and fails Lighthouse `ard-schema`/`llms-txt`. Return a real HTTP `404`.

### `llms.txt` Proposal Hygiene (`llmstxt.org`)
- Required: `# Site Name` H1 first line. Recommended: `> One-sentence summary` directly below H1, `## Section` groups with `- [Title](https://full-url): Brief note` (`## Optional` for skippable links), `< 100 KB`, served as `text/plain` or `text/markdown`.

### `Accept: text/markdown` & RFC 8288 `Link` Headers
- Serve Markdown on the same URL when `Accept: text/markdown` is sent, **always** paired with `Vary: Accept` (prevents CDN cache poisoning between browsers and agents) and `Content-Type: text/markdown; charset=utf-8`.
- Alternatively expose `.md` sibling URLs (`/page.md`) advertised via `<link rel="alternate" type="text/markdown" href="...">` or `Link: </page.md>; rel="alternate"; type="text/markdown"`. Keep Markdown content-equivalent to HTML to avoid cloaking concerns.

---

## 5. AI Crawler Access Matrix, RFC 9309, `Content-Signal` & Web Bot Auth

### AI Crawler Tokens by Role (Report Training, Search & User-Triggered Separately)
| Token | Vendor | Role | Honors `robots.txt`? | Verification |
|---|---|---|---|---|
| `GPTBot` / `OAI-SearchBot` | OpenAI | Training / Search index | Yes | `openai.com/gptbot.json`, `searchbot.json` |
| `ChatGPT-User` | OpenAI | User-triggered fetch/action | "May not apply" | `chatgpt-user.json`, Web Bot Auth |
| `ClaudeBot` / `Claude-SearchBot` / `Claude-User` | Anthropic | Training / Search / User fetch | Yes (all 3) | `claude.com/crawling/bots.json` |
| `PerplexityBot` / `Perplexity-User` | Perplexity | Search index / User fetch | Yes (`Bot`) / No (`User`) | `perplexitybot.json`, `perplexity-user.json` |
| `Google-Extended` | Google | Gemini/GenAI training control | Yes (never Search) | Control token only |
| `Google-Agent` | Google | User-triggered browser agent | Generally ignored | `user-triggered-agents.json`, `agent.bot.goog` |
| `Applebot-Extended` | Apple | Apple Intelligence training | Yes (never Siri/Safari) | Control token only |
| `CCBot` | Common Crawl | Open pretraining dataset | Yes | — |

### Critical `robots.txt` & `Content-Signal` Rules
1. **RFC 9309 Exact Group Selection**: A crawler matching a named `User-agent: GPTBot` group **completely ignores `User-agent: *`**. Never place `Content-Signal` only in `*` if named AI groups exist — repeat `Content-Signal` inside every named group.
2. **Product Token Grammar**: Bare tokens (`[A-Za-z_-]+`) only; avoid `GPTBot/1.1` or `ClaudeBot*`.
3. **HTTP Status Semantics**: `5xx` = full site disallow; `429` = inconclusive server-overload signal (never treat as "all allowed"); `4xx` (non-429) = no restrictions.
4. **IETF `Content-Signal`**: Syntax `Content-Signal: search=yes, ai-input=yes, ai-train=no` (optional experimental Cloudflare `use=immediate|reference|full`). Individual draft `draft-romm-aipref-contentsignals` expired `2026-04-04`; AIPREF WG vocabulary unratified — state as preference signal only.
5. **WAF & Web Bot Auth (`draft-ietf-webbotauth-httpsig-protocol-00`)**: Allowlist verified bots by RFC 9421 Ed25519 `Signature-Agent: sig1="https://..."` (`tag="web-bot-auth"`, `/.well-known/http-message-signatures-directory`) or published IP ranges — never by spoofable `User-Agent` strings. An unverified `--ua-matrix` challenge is expected WAF defense.

### Vendor Grounding Matrix (`2026-09-23`, Grade: `P`=Primary, `S`=Secondary)
- **OpenAI ChatGPT Desktop**: Reads accessibility tree (**P**); calls **imperative WebMCP only** in top-level doc (**P**); signs with Web Bot Auth.
- **Google Gemini in Chrome**: Reads DOM/screen positions (**S**); no public WebMCP consumption (**P**); `Google-Agent` testing Web Bot Auth (`https://agent.bot.goog`, **P**).
- **Anthropic Claude in Chrome / Desktop**: Reads DOM, text, network/console, screenshots (**S**); no WebMCP discovery (**S**).
- **Perplexity Comet**: Reads accessibility tree + screenshots (**S**); no public WebMCP signal.
- **Edge / Brave**: Dev testing / Nightly flag only; **Apple WebKit**: Opposes WebMCP (**P**); **Firefox**: Neutral (**P**).
