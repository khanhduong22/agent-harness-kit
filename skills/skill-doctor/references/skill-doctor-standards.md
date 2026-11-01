# Skill Doctor & Environment Doctor — Reference Standards

Distilled from:
1. **Claude Code 2.0 `/skill-doctor` & `/doctor`** (Always-On Context Token Tax, 30-Day Usage Telemetry, Environment/MCP/Symlink Diagnostics)
2. **`tripleyak/SkillForge` v6** (`skillforge_doctor.py` & `validate_skill.py` — Trigger Collision Jaccard Matrix, Stale Reference Detection, Description Trigger Doctrine)
3. **`YTruman/better-skill`** (Audited 332 official skills — 4-Layer `P0/P1/P2` Skill Clinic & 21 Execution Red Lines)
4. **`xigua-wang/skill-doctor` & `evilstar2016/skill-doctor`** (Cross-Agent Precedence, Conflict & Security Risk Analysis)

---

## 1. The "Skills Soup" & Always-On Context Tax Problem

Every installed skill injects its YAML frontmatter (`name` + `description`) into the system prompt on **every single conversational turn**, even when never invoked.
- **Per-Skill Frontmatter Budget**: Keep `name + description` under **`~60–120 tokens`** (`<= 450 characters` ideal, `1024 characters` hard ceiling).
- **Total Always-On Skill Tax Ceiling**: Keep total frontmatter tokens across all active skills under **`~4,500 tokens/turn`**.
- **Body Budget (`SKILL.md`)**: Keep `SKILL.md` under **`1,500 words` (`~2,000 tokens`)**. Move deep tables, API schemas, and long templates into `references/` so they are loaded only on demand.
- **`<details>` Anti-Pattern**: HTML `<details>` tags inside `SKILL.md` save **zero tokens** when read by an LLM. Never use `<details>` for "progressive disclosure" — split into `references/` files instead.

---

## 2. Description Trigger Doctrine (SkillForge v6 Standard)

> **Critical Discovery**: When a skill's `description` summarizes *how the workflow operates*, the LLM often relies on that summary and **skips reading `SKILL.md` entirely**.

- **DO**: Write descriptions as **trigger conditions + symptom keywords** in third person (`"Use when..."`, `"Triggers on..."`).
- **DON'T**: Summarize the internal step-by-step recipe inside `description`.
- **Trigger Collision Gate**: No two skills should have a content-word Jaccard similarity `>= 0.35` in their `description`. If two skills collide, either merge them or sharpen their boundary triggers.

---

## 3. Four-Layer `P0 / P1 / P2` Clinical Audit (`better-skill` Standard)

| Layer | Priority | Check | Pass Criterion |
|---|---|---|---|
| **L1: Frontmatter & Routing** | **P0** | Valid YAML (`name`, `description`), `name` matches folder (`kebab-case <= 64 chars`), `description` has explicit trigger phrases | Zero frontmatter parse errors; unambiguous routing |
| **L2: Cognitive Load & Structure** | **P1** | `SKILL.md` `< 500 lines` / `< 1,500 words`; phased workflow with explicit exit gates; verification checklist at end | Agent never loses attention mid-execution |
| **L3: Deterministic Tooling** | **P0** | Non-trivial parsing, auditing, math, or binary work is encapsulated in `scripts/` (`--help` / `--json`) rather than prose instructions | Deterministic execution instead of LLM guessing |
| **L4: Offline Reference Library** | **P1** | Every `references/...`, `scripts/...`, and `assets/...` path mentioned in `SKILL.md` exists on disk; zero orphan links | 100% reference integrity |

---

## 4. The 10 Forbidden Red Lines (`Not-To-Do`)

1. **[P0] No Broken Relative Paths**: Never reference `references/foo.md` or `scripts/bar.py` in `SKILL.md` unless the file exists inside the skill folder.
2. **[P0] No Hardcoded User Home Paths**: Never hardcode machine-specific OS user directories inside portable skills; always use `~` or `$HOME`.
3. **[P0] No Pinned Dated Model IDs**: Never hardcode `claude-3-5-sonnet-20241022` or dated model snapshots in skill prompts; use semantic tiers (`pro`, `flash`, `inherit`).
4. **[P0] No Untrusted Shell Execution (`curl | bash`)**: Never instruct the agent to pipe remote URLs directly into a shell.
5. **[P1] No Human-Only Repo Clutter Inside Skill Folders**: Do not add `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, or `INSTALL.md` inside individual `skills/<name>/` directories.
6. **[P1] No Workflow Spoilers in `description`**: Keep `description` focused on *when* to trigger, not a mini-tutorial that tempts the model to skip reading `SKILL.md`.
7. **[P1] No Vague Aesthetic Adjectives**: Replace *"make it modern/beautiful/clean"* with falsifiable numeric rules (`4.5:1 contrast`, `1px solid border`, `0ms TBT`).
8. **[P1] No Monolithic `SKILL.md` (`> 500 lines`)**: Extract long schemas and lookup tables into `references/`.
9. **[P2] No Dead-Weight Skills (`0 uses in 30 days` + high token tax)**: Archive, merge, or tighten descriptions of skills that burn `> 100 tokens/turn` with `0` invocations over 30 days.
10. **[P2] No Unsynced Cross-Agent Drift**: Ensure `~/.claude/skills`, `~/.gemini/config/skills`, and `~/.agents/skills` point cleanly to the canonical harness repository without broken symlinks or stale copies.
