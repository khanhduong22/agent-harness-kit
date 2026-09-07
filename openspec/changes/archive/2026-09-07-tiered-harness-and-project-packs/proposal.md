# Proposal: Tiered Harness & Modular Project Packs (Core + Index)

## Why
The initial `agent-harness-kit` bundled 67 skills and enforced a rigid 6-phase OpenSpec pipeline with mandatory Newman integration tests for every single task. This caused heavy overhead on lightweight bugfixes and maintenance tasks. Furthermore, project-specific context (such as for `Index`) was either missing or risked leaking into global configuration across unrelated projects.

## What Changes
1. **Refactor Core (`rules/core.md`)**:
   - Company Core remains small, authoritative, and focused on boundaries and principles (data protection, scope containment, git hygiene, evidence before assertions).
   - Clear autonomy matrix: what AI can do autonomously, when AI MUST ask, and strictly forbidden actions.
   - Tiered risk-based workflow selection:
     - Bugfix: Reproduce -> Fix root cause -> Native test -> Review.
     - Feature/Module: Clarify -> Plan (OpenSpec) -> Implement -> Verify -> Review.
     - Maintenance: Invariant check -> Modify -> Regression test -> Review.
     - Risk Gates: Schema migrations, auth/permission, breaking public APIs trigger mandatory confirmation.
2. **Modular Project Packs (`profiles/`)**:
   - Starting with `Index`: workspace-level context, plus specific sub-repo guidelines for `api` (NestJS/Prisma/Vitest/Newman) and `cms` (Strapi v5/Jest).
   - Unknown information is explicitly marked as `[TBD: Need User Input]` without speculation.
3. **Native Plugin Manifests & Catalogs**:
   - Manifests placed at root and catalog locations: `.agents/plugins/marketplace.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`.
4. **Enhanced Idempotent Installer (`scripts/install.sh`)**:
   - Support `--index` with `--project-path <dir>` for safe project-level injection into `<repo>/.claude/` and `<repo>/AGENTS.md`.
   - Prevent duplicate rules/skills.
   - Save atomic `receipt.json` in backups.
   - Support `--rollback [latest|<stamp>]` to undo changes and restore previous state cleanly.
5. **Comprehensive Behavioral Test Suite (`tests/`)**:
   - Automated tests for core global installation, project pack injection, idempotency, and rollback.
