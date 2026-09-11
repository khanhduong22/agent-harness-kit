# Agent Harness Kit

One versioned source of truth for company-wide AI agent standards, risk-based workflows, reusable skills, and modular project packs across Codex, Claude Code, Gemini, and Google Antigravity.

The repository contains:
- **Company Core (`rules/core.md`)**: Shared mindset (7-Rung ladder), strict autonomy boundaries, and tiered risk-based workflow routing (Bugfix vs Feature/Module vs Maintenance with risk-based gates).
- **Portable Skills (`skills/`)**: 69 modular skills plus Claude-specific SDLC command overlays.
- **Native Harness Manifests & Marketplaces**: Standards-compliant manifests and marketplace catalogs for Claude Code (`.claude-plugin/`), OpenAI Codex & Agent tools (`.codex-plugin/`, `.agents/plugins/marketplace.json`).
- **Idempotent Installer & Rollback**: Safe installation, project-level pack injection without global pollution, conflict backups, and atomic receipt-based rollback (`receipt.json`).

## Supported harnesses

| Target | Skills | Global rules | Project pack injection |
| --- | --- | --- | --- |
| Codex | `~/.agents/skills/` | `~/.codex/AGENTS.md` | `<project>/AGENTS.md` |
| Claude Code | `~/.claude/skills/` | `~/.claude/CLAUDE.md` | `<project>/.claude/CLAUDE.md` |
| Gemini / Antigravity | `~/.gemini/config/skills/` | `~/.gemini/GEMINI.md` | `<project>/.gemini/GEMINI.md` |

Antigravity uses the Gemini target because both products share the same global skill and rule locations.

## Install

Clone the repository into a stable path (e.g., `~/.agent-harness-kit`):

```bash
git clone git@github.com:khanhduong22/agent-harness-kit.git ~/.agent-harness-kit
cd ~/.agent-harness-kit
```

### 1. Global Core Installation
Installs company-wide skills and core rules (without project-specific packs):

```bash
./scripts/install.sh --targets all --rules
```

### 2. Project Pack Installation (e.g. Index Platform)
Injects project-specific context (workspace overview, API, CMS) directly into the target project repository without polluting other projects or global configs:

```bash
./scripts/install.sh --index --project-path /path/to/index --targets claude,codex
```

### 3. Preview (Dry-Run)
```bash
./scripts/install.sh --index --project-path /path/to/index --dry-run
```

### 4. Rollback
Reverts the changes made by an installation run using its recorded `receipt.json`:

```bash
# Rollback latest run
./scripts/install.sh --rollback latest

# Rollback specific timestamp
./scripts/install.sh --rollback 20260907T152000Z
```

### 5. Other Useful Variants
```bash
# Skills only, selected harnesses
./scripts/install.sh --targets codex,claude

# Copy instead of symlink
./scripts/install.sh --targets all --mode copy --rules

# Replace a legacy global rule file after backing it up
./scripts/install.sh --targets claude,gemini --rules --rules-mode replace
```

## Update & Upstream Sync

### Update local harness & rules
```bash
cd ~/.agent-harness-kit
./scripts/update.sh --targets all --rules
```

### Sync skills from upstream repositories
Inspect or pull latest prompts and skills from upstream repositories (Matt Pocock, Vercel Labs, Google Gemini):

```bash
# Check if upstreams have updates
./scripts/sync-upstream.sh --check

# Fetch and apply upstream updates to skills/
./scripts/sync-upstream.sh --apply
```

## Safety & Autonomy Model

- **Company Core Boundaries**: The agent works independently on scoped edits, tests, and linter fixes. It **MUST STOP and ask** before database migrations, destructive commands, public API breaking changes, or pushing commits to git remotes.
- **Tiered Risk-Based Workflows**:
  - **Bugfix**: Reproduce -> Root-cause fix -> Native regression test -> Review. Lightweight fixes are never forced into heavy OpenSpec pipelines.
  - **Feature / Module**: Requirements -> OpenSpec design/plan -> TDD implement -> Integration test -> Review.
  - **Maintenance**: Invariant behaviors -> Scoped changes -> Compatibility test -> Review.
  - **Risk Gates**: DB schema, auth/RBAC, and public API changes trigger mandatory confirmation.
- **Strict Project Isolation**: Project packs are injected strictly into the target project repository (`--project-path`). Unrelated projects only see Company Core.
- **Idempotency & Rollback**: Every install run records actions in `receipt.json` under `~/.agent-harness-backups/<timestamp>/`. Reinstallations detect unchanged links/blocks without duplicates. `--rollback` restores files and removes created symlinks.
- **Zero Secrets**: No credentials, tokens, MCP credentials, or machine-specific absolute paths are stored in this repo.
- Run `./scripts/verify.sh` and `./tests/test_harness.sh` before publishing any change.

## MCP Provisioning

Profiles declare the MCP servers a project needs, and the installer renders them
into each harness's native, **project-scoped** config.

### Where MCP config actually goes

Claude Code reads `.mcp.json` from a **project root**. It does **not** read
`~/.claude/.mcp.json` — a file there is inert, and a server declared in it will
never load, with no error to tell you so. User-scope servers belong in
`~/.claude.json` (`claude mcp add -s user …`). Check what is actually live with
`claude mcp list`, which prints a health check per server. This trap cost real
debugging time; the installer now writes to the project root so nobody repeats it.

### Declaring servers in a profile

Profiles are Markdown. MCP declarations live in a fenced `toml` block, parsed
with the `tomllib` stdlib module — no third-party dependency:

````markdown
```toml
mcp_tools = [
  "mcp__postgres__query",
  "mcp__framefit__get_layout_spec",
]

[mcp.postgres]
type = "http"
url = "http://localhost:33000/pg"

[mcp.framefit]
command = "npx"
args = ["-y", "framefit"]
env = { FIGMA_TOKEN = "${FIGMA_API_KEY}" }
```
````

Declare `mcp_tools` **above** the `[mcp.*]` tables. In toml a bare key after a
table header binds to that table; the parser rejects it with that hint rather
than silently swallowing the allowlist.

### `mcp_tools` is an allowlist, not a blacklist

MCP tools default to on, so a deny list has to name every tool an upstream will
ever add — it loses that race by construction. Only tools named in `mcp_tools`
are written to `permissions.allow`; anything else stays out of context as
upstream servers grow. Entries merge with existing permissions and never
duplicate on reinstall.

### Secrets

Profiles may contain `${VAR}` references only. `scripts/verify.sh` fails on a
literal credential — in an `env` value, an argument, or embedded in a URL — and
names the offending profile and key.

### Target support

`claude` renders `{"mcpServers": {…}}` to `<project>/.mcp.json`. `codex` and
`gemini` return an explicit unsupported marker rather than a guessed config
shape; see "Phase 3 verification findings" in the change's `design.md` for what
was and was not confirmed about each harness.

## MCP Gateway (`kido-mcp-gateway`)

Per-project `.mcp.json` (Layer 1) and the `mcp_tools` allowlist (Layer 2) are
native and cover most needs. `gateway/` is Layer 3, and it exists only for the
three things the native configs cannot do: switching environment by parameter,
tools that span more than one server, and one registration line every harness
can point at.

### Build and check

```bash
cd gateway
npm install
npm run build
npm test

# Mount every upstream and report health; exits non-zero if any mount failed.
node dist/src/cli.js status --config gateway.config.example.json
```

### Configuration

`gateway.config.example.json` is the full shape. Secrets are never literals —
only `${VAR}` references, resolved from the environment at mount time.

| Key | Meaning |
| --- | --- |
| `mount` | Upstream servers, keyed by the name used in `export`. `command`/`args`/`env` for stdio, `url`/`headers` for streamable HTTP. |
| `export` | Allowlist of `"<mount>:<tool>"`. `tools/list` returns these and nothing else; the gateway advertises them as `<mount>__<tool>`. |
| `env` | Named connection sets (`local`, `dev`, `staging`). Their presence adds an `environment` parameter to every exported tool. |
| `defaultEnvironment` | Environment used when a call omits the parameter. Defaults to the first key of `env`. |
| `composite.verify_ui_against_figma` | Wires the composite tool to the design-QA upstream tools and the Playwright JSON report. |

An unknown `environment` is refused with an error naming the configured
environments, and no upstream call is made. A mount that fails to start is
reported — in `tools/list` `_meta` under `kido-mcp-gateway/mounts`, through the
`gateway_status` tool, and by the `status` command's non-zero exit — while tools
from healthy upstreams stay callable.

### Registration per harness

All three harnesses were verified on a real machine (see the Phase 3 findings in
`openspec/changes/mcp-provisioning/design.md`). Register the gateway once per
harness; the `export` allowlist is enforced inside the gateway, so it holds even
on a harness with no per-tool filtering of its own.

```bash
# Claude Code
claude mcp add kido-gateway -- node /path/to/gateway/dist/src/cli.js serve --config /path/to/gateway.config.json

# Codex
codex mcp add kido-gateway -- node /path/to/gateway/dist/src/cli.js serve --config /path/to/gateway.config.json

# Antigravity
agy mcp add kido-gateway node /path/to/gateway/dist/src/cli.js serve --config /path/to/gateway.config.json
```

Per-tool filtering support in the harnesses themselves differs — Claude Code
(`permissions.allow`) and Codex (`enabled_tools`) were confirmed; Antigravity was
**not**. That asymmetry is why the allowlist lives in the gateway rather than in
each harness's config.

## Repository Layout

```text
.agents/plugins/marketplace.json Codex & Agent catalog
.claude-plugin/
  plugin.json                   Claude Code native manifest
  marketplace.json              Claude Code marketplace catalog
.codex-plugin/plugin.json       Codex native manifest
profiles/
  core/rules.md             Core company baseline profile
  index/
    workspace.md            Index multi-repo workspace architecture & constraints
    api.md                  Index API sub-profile (NestJS, Prisma, Vitest, Newman)
    cms.md                  Index CMS sub-profile (Strapi v5, Jest, content types)
rules/
  core.md                   Global core rules and autonomy matrix
  adapters/                 Harness-specific wrappers
skills/                     Portable Agent Skills (SKILL.md plus resources)
overlays/claude/skills/     Claude-specific SDLC command adapters
scripts/
  install.sh                Idempotent multi-harness & project installer
  sync_rules.py             Rule & profile merge engine
  rollback.py               Atomic receipt-based rollback engine
  update.sh                 Pull and reinstall
  verify.py                 Structural, manifest, profile, and portability checks
  verify.sh                 Linter and validator runner
gateway/                    kido-mcp-gateway (Layer 3 MCP aggregator)
  src/config.ts             GatewayConfig contract, parsing and validation
  src/upstream.ts           Mount registry: per-environment upstream connections
  src/gateway.ts            tools/list filtering and tools/call routing
  src/composite.ts          verify_ui_against_figma composite tool
  src/cli.ts                serve | status commands
  test/                     Integration tests with local stub upstreams
tests/
  test_harness.sh           Comprehensive behavioral and integration test suite
```

## Sources

See [SOURCES.md](SOURCES.md). Bundled third-party material remains subject to its upstream license.
