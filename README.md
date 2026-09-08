# Agent Harness Kit

One versioned source of truth for company-wide AI agent standards, risk-based workflows, reusable skills, and modular project packs across Codex, Claude Code, Gemini, and Google Antigravity.

The repository contains:
- **Company Core (`rules/core.md`)**: Shared mindset (7-Rung ladder), strict autonomy boundaries, and tiered risk-based workflow routing (Bugfix vs Feature/Module vs Maintenance with risk-based gates).
- **Portable Skills (`skills/`)**: 67 modular skills plus Claude-specific SDLC command overlays.
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
tests/
  test_harness.sh           Comprehensive behavioral and integration test suite
```

## Sources

See [SOURCES.md](SOURCES.md). Bundled third-party material remains subject to its upstream license.
