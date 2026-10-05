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
