# Environment Doctor (`/doctor`) — Remediation Playbook

Companion reference for `doctor/SKILL.md`.

## 1. Fixing Global Rules & Symlink Drift
If Layer 2 (Global Rules) or Layer 3 (Skill Symlinks) reports drift, missing symlinks, or standalone directory conflicts:
```bash
cd ~/agent-harness-kit && ./scripts/install.sh --targets all --rules --force
```

## 2. Fixing Stray `$HOME` Rule Shadowing
Claude Code (`>= 2.1.277`) walks ancestor directories from `$PWD` up to `$HOME`. A stray `~/CLAUDE.md` or `~/AGENTS.md` directly in `$HOME` (outside `~/.claude/CLAUDE.md`) shadows project-level `AGENTS.md` files. Run `./scripts/install.sh --targets all --rules` to automatically back up and remove stray `$HOME` root rule files.

## 3. Fixing Broken MCP Server Entrypoints
If Layer 4 reports a missing binary or script path in `~/.gemini/antigravity/mcp_config.json` or `~/.claude.json`:
1. Verify whether the binary (`npx`, `uvx`, `bun`, `node`, or compiled Go/Rust binary) is installed in `/opt/homebrew/bin` or `~/.local/bin`.
2. Prefer absolute binary paths in MCP configs so GUI-launched IDEs (which do not always inherit interactive shell `$PATH`) can spawn the server reliably.

## 4. Pruning Stale Git Worktrees (`~/.agent-worktrees`)
If Layer 6 reports old worktrees under `~/.agent-worktrees/<repo>/<branch>`:
```bash
git -C <repo-path> worktree prune
```
Only remove a worktree directory after verifying that its branch has been merged into `main` and has zero uncommitted changes (`git status --porcelain`).
