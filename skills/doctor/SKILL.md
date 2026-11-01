---
name: doctor
description: "Run a comprehensive AI Agent Environment, Toolchain, Rules Sync, MCP Server, Worktree & Hook Health Check across Claude Code, Antigravity (Gemini), and Codex. Use when diagnosing agent environment issues, checking CLI/MCP/symlink drift, auditing worktree disk usage, or running `/doctor`."
---

# AI Agent Environment & Runtime Doctor (`/doctor`)

Provides a deterministic, zero-dependency 7-layer health check of the entire local AI coding environment across **Claude Code (`~/.claude`)**, **Antigravity / Gemini (`~/.gemini`)**, and **Codex (`~/.codex` & `~/.agents`)**, paired with a summary bridge to `/skill-doctor`.

---

## 1. Quick Execution (Mandatory First Step)

Whenever the user invokes `/doctor`, asks *"bạn đã doctor chưa"*, or reports environment/MCP/hook/rule anomalies, immediately run the bundled CLI scanner:

```bash
# Full Markdown diagnostic report (Environment + Toolchain + MCP + Symlinks + Skill Health Bridge)
python3 ~/.claude/skills/doctor/scripts/env_doctor.py

# Machine-readable JSON output
python3 ~/.claude/skills/doctor/scripts/env_doctor.py --json
```

*(Or from inside the `agent-harness-kit` repository via `./scripts/install.sh --doctor` or `python3 skills/doctor/scripts/env_doctor.py`).*

---

## 2. The 7 Diagnostic Layers

Read [`references/doctor-checks.md`](references/doctor-checks.md) for the complete remediation playbook across all 7 layers:

1. **Layer 1 — Core CLI & Agent Binary Versions**: Verifies presence and versions of `claude`, `codex`, `git`, `gh`, `node`, `bun`, `python3`, `docker`, and `rclone`.
2. **Layer 2 — Global Rules Sync & Shadow File Detection**: Verifies `<!-- agent-harness-kit:start -->` managed blocks in `~/.claude/CLAUDE.md`, `~/.gemini/GEMINI.md`, and `~/.codex/AGENTS.md`, and checks for stray `~/CLAUDE.md` or `~/AGENTS.md` files at `$HOME` root that would shadow project rules.
3. **Layer 3 — Cross-Agent Skill Symlink Parity**: Audits `~/.claude/skills`, `~/.gemini/config/skills`, and `~/.agents/skills` for broken symlinks, missing kit skills, or standalone directory conflicts.
4. **Layer 4 — MCP Server Binary & Config Audit**: Inspects `~/.gemini/antigravity/mcp_config.json` and `~/.claude.json` to ensure configured MCP server commands and script entrypoints exist on disk.
5. **Layer 5 — Hook Scripts & Autonomous Sidecars**: Checks executable permissions (`+x`) in `~/.agent-harness/hooks` and lists active cron schedules in `~/.gemini/config/sidecars`.
6. **Layer 6 — Git Worktree Disk & Orphan Audit (`~/.agent-worktrees`)**: Counts active isolated worktrees and flags stale directories so disk space stays clean.
7. **Layer 7 — Skill Doctor Bridge (`/skill-doctor`)**: Summarizes skill health score (`0–100`), always-on frontmatter context tax (`tokens/turn`), and 30-day active vs unused skill counts.
