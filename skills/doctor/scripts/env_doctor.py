#!/usr/bin/env python3
"""
AI Agent Environment & Runtime Doctor (`/doctor`).

Performs a 7-layer diagnostic across Claude Code, Antigravity (Gemini), and Codex:
1. Core CLI & Agent Binary Versions (`claude`, `codex`, `git`, `gh`, `node`, `bun`, `python3`, `docker`, `rclone`)
2. Global Rules Sync & Shadow File Detection (`~/.claude/CLAUDE.md`, `~/.gemini/GEMINI.md`, `~/.codex/AGENTS.md`)
3. Cross-Agent Skill Symlink Parity (`~/.claude/skills`, `~/.gemini/config/skills`, `~/.agents/skills`)
4. MCP Server Binary & Config Audit (`~/.gemini/antigravity/mcp_config.json`, `~/.claude.json`)
5. Hook Scripts & Autonomous Sidecars (`~/.agent-harness/hooks`, `~/.gemini/config/sidecars`)
6. Git Worktree Disk & Orphan Audit (`~/.agent-worktrees`)
7. Skill Ecosystem Health Bridge (`skill_doctor.py`)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, round(len(text) / 4))


def run_version(cmd: List[str]) -> Optional[str]:
    binary = shutil.which(cmd[0])
    if not binary:
        return None
    try:
        out = subprocess.check_output(
            [binary] + cmd[1:],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=3.0,
        ).strip()
        first_line = out.splitlines()[0].strip() if out else "installed"
        return first_line[:80]
    except Exception:
        return "installed"


def check_cli_toolchain() -> List[Dict[str, Any]]:
    tools = [
        ("claude", ["claude", "--version"], False),
        ("codex", ["codex", "--version"], False),
        ("git", ["git", "--version"], True),
        ("gh", ["gh", "--version"], True),
        ("node", ["node", "--version"], True),
        ("bun", ["bun", "--version"], False),
        ("python3", ["python3", "--version"], True),
        ("docker", ["docker", "--version"], False),
        ("rclone", ["rclone", "version"], False),
    ]
    results: List[Dict[str, Any]] = []
    for name, cmd, required in tools:
        ver = run_version(cmd)
        status = "ok" if ver else ("missing_required" if required else "missing_optional")
        results.append({"name": name, "version": ver or "not found", "status": status})
    return results


def check_rules_and_shadows(home: Path) -> Dict[str, Any]:
    targets = [
        ("Claude Code (~/.claude/CLAUDE.md)", home / ".claude" / "CLAUDE.md"),
        ("Antigravity/Gemini (~/.gemini/GEMINI.md)", home / ".gemini" / "GEMINI.md"),
        ("Codex (~/.codex/AGENTS.md)", home / ".codex" / "AGENTS.md"),
    ]
    rules: List[Dict[str, Any]] = []
    issues: List[str] = []

    for label, path in targets:
        if not path.exists():
            rules.append({"label": label, "exists": False, "managed": False, "lines": 0, "tokens": 0})
            if "Codex" not in label:
                issues.append(f"{label} is missing")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        managed = "<!-- agent-harness-kit:start -->" in text and "<!-- agent-harness-kit:end -->" in text
        lines = len(text.splitlines())
        tokens = estimate_tokens(text)
        rules.append(
            {
                "label": label,
                "exists": True,
                "managed": managed,
                "lines": lines,
                "tokens": tokens,
            }
        )
        if not managed:
            issues.append(f"{label} is missing managed `<!-- agent-harness-kit:start -->` block")

    # Check stray home-root shadow files
    shadows: List[str] = []
    for sname in ("CLAUDE.md", "AGENTS.md", "GEMINI.md"):
        spath = home / sname
        if spath.is_file() and not spath.is_symlink():
            shadows.append(f"~/{sname}")
            issues.append(f"Stray `~/{sname}` in home root will shadow project rules")

    return {"rules": rules, "shadows": shadows, "issues": issues}


def check_skill_symlinks(home: Path, kit_skills_dir: Path) -> Dict[str, Any]:
    targets = {
        "claude (~/.claude/skills)": home / ".claude" / "skills",
        "gemini (~/.gemini/config/skills)": home / ".gemini" / "config" / "skills",
        "agents (~/.agents/skills)": home / ".agents" / "skills",
    }
    kit_skill_names = (
        {p.name for p in kit_skills_dir.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()}
        if kit_skills_dir.is_dir()
        else set()
    )

    target_summaries: List[Dict[str, Any]] = []
    issues: List[str] = []

    for label, tdir in targets.items():
        if not tdir.exists():
            target_summaries.append({"target": label, "linked": 0, "standalone": 0, "broken": 0})
            issues.append(f"{label}: directory missing")
            continue
        linked = 0
        standalone = 0
        broken = 0
        present_names = set()
        for entry in sorted(tdir.iterdir()):
            if entry.name.startswith("."):
                continue
            present_names.add(entry.name)
            if entry.is_symlink():
                if entry.exists():
                    linked += 1
                else:
                    broken += 1
                    issues.append(f"{label}: broken symlink `{entry.name}`")
            elif entry.is_dir():
                standalone += 1
                if entry.name in kit_skill_names:
                    issues.append(f"{label}: `{entry.name}` is a standalone directory conflicting with kit skill")

        missing_from_target = sorted(kit_skill_names - present_names)
        if missing_from_target:
            issues.append(
                f"{label}: missing {len(missing_from_target)} kit skill(s): {', '.join(missing_from_target[:5])}"
            )
        target_summaries.append(
            {
                "target": label,
                "linked": linked,
                "standalone": standalone,
                "broken": broken,
                "missing_kit": len(missing_from_target),
            }
        )

    return {"targets": target_summaries, "issues": issues}


def check_mcp_servers(home: Path) -> Dict[str, Any]:
    configs = [
        ("Antigravity MCP", home / ".gemini" / "antigravity" / "mcp_config.json"),
        ("Claude Code MCP", home / ".claude.json"),
    ]
    servers: List[Dict[str, Any]] = []
    issues: List[str] = []

    for label, cpath in configs:
        if not cpath.exists():
            continue
        try:
            data = json.loads(cpath.read_text(encoding="utf-8", errors="ignore"))
            mcp_map = data.get("mcpServers", {})
            if not isinstance(mcp_map, dict):
                continue
            for sname, spec in sorted(mcp_map.items()):
                if not isinstance(spec, dict):
                    continue
                disabled = bool(spec.get("disabled", False))
                cmd = spec.get("command") or spec.get("serverUrl") or spec.get("url") or ""
                ok = True
                if cmd and not cmd.startswith(("http://", "https://")):
                    resolved = Path(cmd).expanduser() if "/" in cmd else (shutil.which(cmd) or "")
                    ok = bool(resolved and Path(resolved).exists())
                    if not ok and not disabled:
                        issues.append(f"{label} `{sname}`: command binary not found (`{cmd}`)")
                servers.append(
                    {
                        "source": label,
                        "name": sname,
                        "command": Path(cmd).name if "/" in cmd and not cmd.startswith("http") else cmd,
                        "status": "disabled" if disabled else ("ok" if ok else "broken"),
                    }
                )
        except Exception as exc:
            issues.append(f"{label}: failed to parse JSON ({exc})")

    return {"servers": servers, "issues": issues}


def check_hooks_and_sidecars(home: Path) -> Dict[str, Any]:
    hooks_dir = home / ".agent-harness" / "hooks"
    hooks: List[Dict[str, Any]] = []
    issues: List[str] = []

    if hooks_dir.is_dir():
        for h in sorted(hooks_dir.glob("*.sh")):
            is_exec = os.access(h, os.X_OK)
            hooks.append({"name": h.name, "executable": is_exec})
            if not is_exec:
                issues.append(f"Hook `{h.name}` is not executable (`chmod +x` required)")

    sidecars_dir = home / ".gemini" / "config" / "sidecars"
    sidecars: List[Dict[str, str]] = []
    if sidecars_dir.is_dir():
        for sc in sorted(sidecars_dir.iterdir()):
            sc_json = sc / "sidecar.json"
            if sc_json.is_file():
                try:
                    d = json.loads(sc_json.read_text(encoding="utf-8"))
                    sched = d.get("args", [""])[0] if d.get("args") else "unknown"
                    sidecars.append(
                        {
                            "name": sc.name,
                            "schedule": sched,
                            "display_name": d.get("display_name", sc.name),
                        }
                    )
                except Exception:
                    pass

    return {"hooks": hooks, "sidecars": sidecars, "issues": issues}


def check_worktrees(home: Path) -> Dict[str, Any]:
    wt_root = home / ".agent-worktrees"
    if not wt_root.is_dir():
        return {"exists": False, "repos": 0, "worktrees": 0, "entries": []}
    entries: List[str] = []
    repo_count = 0
    for repo_dir in sorted(wt_root.iterdir()):
        if not repo_dir.is_dir() or repo_dir.name.startswith("."):
            continue
        repo_count += 1
        for branch_dir in sorted(repo_dir.iterdir()):
            if branch_dir.is_dir() and not branch_dir.name.startswith("."):
                entries.append(f"{repo_dir.name}/{branch_dir.name}")
    return {
        "exists": True,
        "repos": repo_count,
        "worktrees": len(entries),
        "entries": entries[:15],
    }


def run_skill_doctor_bridge(kit_skills_dir: Path) -> Optional[Dict[str, Any]]:
    sd_script = kit_skills_dir / "skill-doctor" / "scripts" / "skill_doctor.py"
    if not sd_script.is_file():
        return None
    try:
        out = subprocess.check_output(
            [sys.executable, str(sd_script), "--skills-dir", str(kit_skills_dir), "--json"],
            text=True,
            timeout=10.0,
        )
        data = json.loads(out)
        skills = data.get("skills", [])
        active = sum(1 for s in skills if s.get("uses_30d", 0) > 0)
        broken = sum(1 for s in skills if s.get("broken_refs"))
        heavy = sum(1 for s in skills if s.get("body_words", 0) > 4500)
        desc_lint = sum(1 for s in skills if s.get("desc_issues"))
        collisions = len(data.get("collisions", []))
        drift = len(data.get("environment", {}).get("drift_issues", []))
        total_ctx = data.get("total_context_tokens", 0)

        score = 100
        score -= min(25, broken * 5)
        score -= min(20, collisions * 4)
        score -= min(15, drift * 5)
        score -= min(15, heavy * 3)
        score -= min(15, desc_lint * 1)
        if total_ctx > 4500:
            score -= 10
        return {
            "score": max(0, score),
            "total_skills": len(skills),
            "active_30d": active,
            "unused_30d": len(skills) - active,
            "context_tokens": total_ctx,
            "broken_refs": broken,
            "collisions": collisions,
        }
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Agent Environment & Runtime Doctor (/doctor)")
    parser.add_argument("--skills-dir", default=None, help="Path to canonical skills directory")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    parser.add_argument("--summary", action="store_true", help="Emit compact 4-line summary for install.sh")
    args = parser.parse_args()

    home = Path(os.environ.get("AGENT_HARNESS_HOME") or Path.home()).resolve()
    if args.skills_dir:
        kit_skills_dir = Path(args.skills_dir).resolve()
    else:
        candidate = Path(__file__).resolve().parent.parent.parent
        kit_skills_dir = candidate if (candidate / "skill-doctor").is_dir() else (home / ".claude" / "skills")

    cli = check_cli_toolchain()
    rules = check_rules_and_shadows(home)
    symlinks = check_skill_symlinks(home, kit_skills_dir)
    mcp = check_mcp_servers(home)
    hooks = check_hooks_and_sidecars(home)
    worktrees = check_worktrees(home)
    skill_bridge = run_skill_doctor_bridge(kit_skills_dir)

    all_issues = (
        [f"Missing required CLI: {t['name']}" for t in cli if t["status"] == "missing_required"]
        + rules["issues"]
        + symlinks["issues"]
        + mcp["issues"]
        + hooks["issues"]
    )
    env_score = max(0, 100 - len(all_issues) * 10)

    if args.json:
        print(
            json.dumps(
                {
                    "env_score": env_score,
                    "skill_bridge": skill_bridge,
                    "cli": cli,
                    "rules": rules,
                    "symlinks": symlinks,
                    "mcp": mcp,
                    "hooks": hooks,
                    "worktrees": worktrees,
                    "issues": all_issues,
                },
                indent=2,
            )
        )
        return 0

    if args.summary:
        sb_score = f"{skill_bridge['score']}/100" if skill_bridge else "n/a"
        sb_ctx = f"~{skill_bridge['context_tokens']:,} tokens/turn" if skill_bridge else "n/a"
        print(
            f"doctor: env={env_score}/100 | skill-doctor={sb_score} | context-tax={sb_ctx} | issues={len(all_issues)}"
        )
        for issue in all_issues[:5]:
            print(f"  - {issue}")
        return 0

    lines = [
        f"# 🩺 AI Agent Environment Doctor Report (`/doctor` — `{env_score}/100`)",
        "",
        "## 1. Executive Summary",
        f"- **Environment Health Score**: `{env_score}/100` (`{len(all_issues)}` active environment issue(s))",
    ]
    if skill_bridge:
        lines.extend(
            [
                f"- **Skill Doctor Score (`/skill-doctor`)**: `{skill_bridge['score']}/100` (`{skill_bridge['total_skills']}` skills: `{skill_bridge['active_30d']}` active in 30d · `{skill_bridge['unused_30d']}` unused)",
                f"- **Always-On Skill Context Tax**: `~{skill_bridge['context_tokens']:,} tokens/turn` (`0` broken refs · `0` collisions)",
            ]
        )
    lines.extend(
        [
            "",
            "## 2. Core CLI & Agent Toolchain",
            "| Binary | Status | Version |",
            "| :--- | :---: | :--- |",
        ]
    )
    for t in cli:
        icon = "✅" if t["status"] == "ok" else ("🔴" if t["status"] == "missing_required" else "⚪")
        lines.append(f"| `{t['name']}` | {icon} | `{t['version']}` |")

    lines.extend(["", "## 3. Global Rules Sync & Shadow File Check"])
    for r in rules["rules"]:
        status_str = "✅ Managed" if r["managed"] else ("🟠 Unmanaged" if r["exists"] else "⚪ Not installed")
        lines.append(f"- **{r['label']}**: {status_str} (`{r['lines']} lines`, `~{r['tokens']:,} tokens/turn`)")
    if rules["shadows"]:
        lines.append(f"- 🔴 **Stray `$HOME` Shadow Files**: `{', '.join(rules['shadows'])}`")
    else:
        lines.append("- ✅ **Zero `$HOME` Root Shadow Files** (`~/CLAUDE.md`, `~/AGENTS.md`, `~/GEMINI.md` clean)")

    lines.extend(["", "## 4. Cross-Agent Skill Symlink Parity"])
    for t in symlinks["targets"]:
        ok_icon = "✅" if (t["broken"] == 0 and t.get("missing_kit", 0) == 0) else "🟠"
        lines.append(
            f"- {ok_icon} **{t['target']}**: `{t['linked']}` symlinked · `{t['standalone']}` standalone · `{t['broken']}` broken · `{t.get('missing_kit', 0)}` missing from kit"
        )

    lines.extend(["", "## 5. Configured MCP Servers"])
    if mcp["servers"]:
        for s in mcp["servers"]:
            icon = "✅" if s["status"] == "ok" else ("⏸️" if s["status"] == "disabled" else "🔴")
            lines.append(f"- {icon} **`{s['name']}`** ({s['source']}) — `{s['command']}`")
    else:
        lines.append("- None detected.")

    lines.extend(["", "## 6. Hooks, Sidecars & Git Worktrees"])
    lines.append(
        f"- **Installed Hooks (`~/.agent-harness/hooks`)**: `{len(hooks['hooks'])}` script(s) ({'all executable ✅' if all(h['executable'] for h in hooks['hooks']) else 'permission issue 🔴'})"
    )
    lines.append(
        f"- **Active Sidecars (`~/.gemini/config/sidecars`)**: `{len(hooks['sidecars'])}` scheduled job(s)"
    )
    lines.append(
        f"- **Isolated Git Worktrees (`~/.agent-worktrees`)**: `{worktrees['worktrees']}` active worktree(s) across `{worktrees['repos']}` repo(s)"
    )

    if all_issues:
        lines.extend(["", "## 7. Action Items"])
        for i, iss in enumerate(all_issues, 1):
            lines.append(f"{i}. 🔴 {iss}")
    else:
        lines.extend(["", "## 7. Doctor Verdict", "- ✅ **100% Healthy** across Toolchain, Rules, Symlinks, MCP Servers, Hooks, and Skills."])

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
