---
name: skill-doctor
description: "Use when auditing AI agent skills, diagnosing context token bloat, checking 30-day skill usage telemetry, finding trigger collisions or broken references, or running an environment health check across Claude Code, Antigravity, and Codex. Triggers on '/skill-doctor', '/doctor', 'skill doctor', 'audit skills', 'context tax', or 'unused skills'."
---

# Skill Doctor & Environment Doctor (`/skill-doctor` & `/doctor`)

## Overview

Audit your AI coding agent skill library and harness environment like production infrastructure. Combines:
1. **Claude Code 2.0 `/skill-doctor`**: Measures the **Always-On Context Tax (`context (tokens)`)** of every loaded skill, tracks **30-day invocation frequency (`uses (30 days)`)**, and flags dormant "dead-weight" skills (`⚠️ never`).
2. **`SkillForge` v6 & `better-skill` Clinical Auditor**: Detects **Trigger Collisions** (overlapping descriptions with Jaccard similarity `>= 0.35`), **Broken File References** (`references/`, `scripts/`, `assets/` paths that do not exist), **Heavyweight `SKILL.md` Bodies** (`> 1,500 words`), and **Description Trigger Violations**.
3. **Environment `/doctor`**: Verifies cross-agent symlink parity (`~/.claude/skills`, `~/.gemini/config/skills`, `~/.agents/skills`), global rule token budgets (`CLAUDE.md`, `GEMINI.md`), and autonomous sidecars.

## When to Use

- Running `/skill-doctor` or `/doctor` to inspect which skills are burning context tokens every turn without being used
- Auditing a new or existing skill before committing to `agent-harness-kit`
- Diagnosing why an agent failed to trigger the right skill (trigger collision or weak description)
- Checking cross-agent symlink drift across Claude Code, Antigravity, and Codex

## Clinical Modes & Workflow

### Step 1: Run Deterministic Diagnostic Scan (`Read-Only`)
Always start by executing the deterministic scanner before proposing any edits:

```bash
python3 scripts/skill_doctor.py
```

For structured JSON output (or to scan a custom skills folder):

```bash
python3 scripts/skill_doctor.py --json
python3 scripts/skill_doctor.py --skills-dir path/to/skills
```

### Step 2: Interpret the 4 Diagnostic Tables

1. **Skills Loaded This Session (`/skill-doctor` Telemetry Table)**:
   - Displays `skill | source | context (tokens) | body (tokens) | uses (30 days) | last used`.
   - Aggregates real usage across `~/.claude.json` (`skillUsage`) and Antigravity conversation transcripts over the rolling 30-day window.
   - Identifies high-tax skills (`> 100 tokens/turn`) with `0x` uses (`⚠️ never`).
2. **Broken File References (`P0` Red Line)**:
   - Every `references/...`, `scripts/...`, or `assets/...` path mentioned inside a `SKILL.md` MUST exist on disk. Fix broken links immediately by creating the missing reference file or correcting the path.
3. **Trigger Collisions (`Jaccard >= 0.35`)**:
   - When two skills share `>= 35%` of their content keywords in `description`, the router can misfire. Sharpen each skill's `description` to state distinct `Use when...` / `Triggers on...` boundaries, or merge redundant skills.
4. **Cross-Agent Symlink Drift (`/doctor`)**:
   - Flags standalone directories in `~/.claude/skills` or `~/.gemini/config/skills` that block `./scripts/install.sh` symlink propagation.

### Step 3: Targeted Prescription (`Str-Replace` Only)
Never rewrite an entire skill from scratch without a diagnostic finding. Follow the standards in `references/skill-doctor-standards.md`:
- **Description Doctrine**: Write descriptions as **trigger conditions + symptom keywords** (`"Use when..."`, `"Triggers on..."`), never workflow summaries that tempt the LLM to skip reading `SKILL.md`.
- **Cognitive Budget**: Keep `SKILL.md` under `1,500 words` (`< 400 lines`). Offload deep lookup tables, templates, and schemas into `references/`.
- **Agent Harness Lifecycle**: After fixing any skill in `agent-harness-kit`, run `./scripts/verify.sh && bash tests/test_harness.sh`, commit, push, and propagate via `./scripts/install.sh --targets all --rules`.

### Step 4: Empirical 60/40 Train/Test Trigger Optimization & Paired A/B Eval
When a skill exhibits routing misfires or needs empirical validation after edits, run the `skill-creator` evaluation suite bundled in [`self-improving-distiller`](../self-improving-distiller/SKILL.md):
```bash
cd skills/self-improving-distiller
python3 -m scripts.run_loop \
  --eval-set /tmp/trigger-eval.json \
  --skill-path ../<skill-name> \
  --model claude-sonnet-4 \
  --max-iterations 5 \
  --verbose
```

## See Also

- `references/skill-doctor-standards.md` — Detailed 4-Layer `P0/P1/P2` Audit Matrix, Description Trigger Doctrine, Always-On Context Token Budgets, and 10 Forbidden Red Lines.
- `scripts/skill_doctor.py` — Deterministic CLI scanner for `/skill-doctor` telemetry and `/doctor` environment health.
- [`self-improving-distiller`](../self-improving-distiller/SKILL.md) — Paired `with_skill` vs `without_skill` subagent evaluation, assertion grading, and 60/40 train/test description optimizer.
