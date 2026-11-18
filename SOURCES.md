# Sources and provenance

This repository is a curated snapshot, not a mirror. Local adaptations are committed directly so every harness receives the same reviewed behavior.

## Upstream skills still synced

- `next-best-practices`: <https://github.com/vercel-labs/next-skills> (the only entry in `scripts/sync_upstream.py`)

## Previously bundled, since removed

The 2026-09-07 snapshot also bundled the Matt Pocock skills (<https://github.com/mattpocock/skills>), `find-skills` (<https://github.com/vercel-labs/skills>) and `gemini-api-dev` (<https://github.com/google-gemini/gemini-skills>). They have been pruned from `skills/` and from the sync manifest; the links remain for provenance only.

## Personal collection

Every other common skill was imported from the existing Gemini/Antigravity global collection or authored here. The Claude SDLC adapters in `overlays/claude/skills` were imported from the existing Claude Code personal collection. Their committed contents are authoritative for this kit; upstream provenance was not present in the source directories.

Skill counts drift with every prune — `scripts/verify.sh` prints the live number.

Review each upstream license before changing this repository from private visibility or redistributing its contents.

## Absorbed design / UI review skills (2026-11-18)

Audited with the skill-harvester 8-point gate plus a full-file scan (no scripts, no executables, no remote-code or prompt-injection patterns). Copied as standalone skills so the slash names exist.

- `better-accessibility`, `better-colors`, `better-interface`, `better-layout`, `better-typography`, `better-ui`, `better-writing`: <https://github.com/jakubkrehel/skills> at commit `276449a` (MIT). `better-interface` orchestrates the other six. The sibling `interface-review` (change-scoped review) was not absorbed.
- `anti-ui-slop`: <https://github.com/uizze/uizze/tree/main/skills/anti-ui-slop> at commit `fc401e9` (Apache-2.0; adapts Impeccable by Paul Bakaus, Apache-2.0, and Platform Design Skills, MIT; LICENSE, NOTICE and MODIFICATIONS.md kept). Local edits are listed in its `MODIFICATIONS.md`.
- `accessibility-review`: <https://github.com/anthropics/knowledge-work-plugins/tree/main/design/skills/accessibility-review> at commit `e91a134` (Apache-2.0). Only change: removed the plugin-relative `CONNECTORS.md` pointer.
- Kit edit on the seven `better-*` skills: appended a "Use when ..." trigger sentence to each frontmatter `description` (kit lint requires trigger phrasing). Bodies are unchanged from upstream.
- Not absorbed: the `spacing-audit` found upstream (`Dragoon0x/argus`) is a 13-line stub that fails the substance floor; spacing rules live in `better-layout` (`spacing-and-adaptivity.md`).
