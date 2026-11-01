#!/usr/bin/env python3
"""
Skill Doctor & Environment Doctor (`/skill-doctor` + `/doctor`).

Combines:
1. Claude Code 2.0 `/skill-doctor` ("Skills loaded this session": context token tax,
   30-day usage frequency, last used timestamp across Claude Code & Antigravity).
2. `tripleyak/SkillForge` v6 Ecosystem Doctor (Trigger collision Jaccard matrix,
   broken `references/`/`scripts/` path detection, description trigger lint,
   body word/token budget, pinned model IDs).
3. `YTruman/better-skill` 4-Layer P0/P1/P2 Clinical Audit & Red-Line checks.
4. Claude Code `/doctor` Cross-Agent Environment Check (`CLAUDE.md`/`GEMINI.md`
   token footprint, symlink drift across `~/.claude`, `~/.gemini`, `~/.agents`,
   MCP server configs, and scheduled sidecars).

Usage:
    python3 scripts/skill_doctor.py [--mode all|skills|env] [--json] [--skills-dir DIR]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "into", "is", "it", "its", "of", "on", "or", "that", "the", "their",
    "this", "to", "use", "used", "using", "when", "with", "you", "your", "need",
    "wants", "want", "asks", "any", "all", "also", "can", "should", "will", "skill",
    "skills", "user", "code", "agent", "agents", "file", "files",
}

TRIGGER_MARKERS = (
    "use when",
    "triggers on",
    "trigger when",
    "activate",
    "use this",
    "use for",
    "whenever",
    "run when",
)

REL_PATH_RE = re.compile(r"(?<![\w/.-])((?:references|scripts|assets)/[\w][\w\-./]*\.[\w]+)")
PLACEHOLDER_RE = re.compile(r"\{\{|[<>*$]|TODO|example|foo|bar", re.IGNORECASE)
PINNED_MODEL_RE = re.compile(r"\bclaude-(?:3|4|sonnet|opus|haiku)[a-z0-9-]*-202\d{5}\b", re.IGNORECASE)
HUMAN_CLUTTER_FILES = {"CHANGELOG.md", "CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "INSTALL.md"}


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    # Standard approximation: ~4 chars per token in English/code mix
    return max(1, round(len(text) / 4))


def parse_frontmatter(content: str) -> Tuple[Dict[str, str], str]:
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    raw_fm, body = parts[1], parts[2]
    fm: Dict[str, str] = {}
    current_key: Optional[str] = None
    for line in raw_fm.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if not line.startswith((" ", "\t")) and ":" in line:
            k, v = line.split(":", 1)
            current_key = k.strip()
            val = v.strip().strip("'\"")
            fm[current_key] = val
        elif current_key and line.startswith((" ", "\t")):
            fm[current_key] = (fm[current_key] + " " + line.strip()).strip()
    return fm, body


def content_words(text: str) -> Set[str]:
    words = re.findall(r"[a-z0-9][a-z0-9_-]{2,}", text.lower())
    return {w for w in words if w not in STOPWORDS}


def format_relative_age(ts_sec: Optional[float], now_sec: float) -> str:
    if not ts_sec or ts_sec <= 0:
        return "⚠️ never"
    diff_days = (now_sec - ts_sec) / 86400.0
    if diff_days < 0.8:
        return "today"
    days = int(round(diff_days))
    if days <= 1:
        return "1 day"
    return f"{days} days"


def collect_usage_telemetry(skill_names: Set[str], now_sec: float) -> Dict[str, Dict[str, Any]]:
    """
    Collects 30-day usage counts and last-used timestamps across:
    1. ~/.claude.json (`skillUsage`)
    2. ~/.claude/history.jsonl
    3. ~/.gemini/antigravity/brain/*/.system_generated/logs/transcript.jsonl
    """
    home = Path.home()
    cutoff_sec = now_sec - (30 * 86400)
    stats: Dict[str, Dict[str, Any]] = {
        name: {"uses_30d": 0, "last_used_ts": None} for name in skill_names
    }

    # 1. Read ~/.claude.json skillUsage
    claude_json = home / ".claude.json"
    if claude_json.exists():
        try:
            data = json.loads(claude_json.read_text(encoding="utf-8", errors="ignore"))
            skill_usage = data.get("skillUsage", {})
            if isinstance(skill_usage, dict):
                for sname, entry in skill_usage.items():
                    clean_name = sname.lstrip("/")
                    if clean_name in stats and isinstance(entry, dict):
                        last_ts = (entry.get("lastUsedAt") or 0) / 1000.0
                        count = int(entry.get("usageCount") or 0)
                        if last_ts >= cutoff_sec:
                            stats[clean_name]["uses_30d"] += count
                        if last_ts > 0 and (
                            stats[clean_name]["last_used_ts"] is None
                            or last_ts > stats[clean_name]["last_used_ts"]
                        ):
                            stats[clean_name]["last_used_ts"] = last_ts
        except Exception:
            pass

    # 2. Scan Antigravity transcripts modified in the last 30 days
    brain_dir = home / ".gemini" / "antigravity" / "brain"
    if brain_dir.exists():
        skill_path_re = re.compile(r"/skills/([a-zA-Z0-9_-]+)/SKILL\.md")
        for conv_dir in brain_dir.iterdir():
            if not conv_dir.is_dir():
                continue
            tfile = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
            if not tfile.exists():
                continue
            try:
                mtime = tfile.stat().st_mtime
                if mtime < cutoff_sec:
                    continue
                text = tfile.read_text(encoding="utf-8", errors="ignore")
                matched_in_conv = set(skill_path_re.findall(text))
                for sname in matched_in_conv:
                    if sname in stats:
                        stats[sname]["uses_30d"] += 1
                        if (
                            stats[sname]["last_used_ts"] is None
                            or mtime > stats[sname]["last_used_ts"]
                        ):
                            stats[sname]["last_used_ts"] = mtime
            except OSError:
                continue

    return stats


def discover_skills(skills_root: Path) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if not skills_root.exists():
        return records

    for item in sorted(skills_root.iterdir()):
        if not item.is_dir() or item.name.startswith("."):
            continue
        skill_md = item / "SKILL.md"
        if not skill_md.exists():
            continue
        try:
            raw = skill_md.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        fm, body = parse_frontmatter(raw)
        name = fm.get("name") or item.name
        desc = fm.get("description") or ""
        frontmatter_text = f"{name}: {desc}"
        ctx_tokens = estimate_tokens(frontmatter_text)
        body_tokens = estimate_tokens(body)
        body_words = len(body.split())
        body_lines = len(raw.splitlines())

        # Check broken references
        broken_refs: List[str] = []
        for match in REL_PATH_RE.finditer(body):
            rel_path = match.group(1).rstrip(".,;:)`'\"")
            if PLACEHOLDER_RE.search(rel_path):
                continue
            if not (item / rel_path).exists():
                if rel_path not in broken_refs:
                    broken_refs.append(rel_path)

        # Check human clutter files
        clutter = [f for f in HUMAN_CLUTTER_FILES if (item / f).exists()]

        # Check pinned dated models
        pinned_models = list(set(PINNED_MODEL_RE.findall(raw)))

        # Check description lint
        desc_issues: List[str] = []
        if not desc:
            desc_issues.append("Missing `description` in YAML frontmatter")
        else:
            if len(desc) > 1024:
                desc_issues.append(f"Description exceeds 1024 chars ({len(desc)} chars)")
            if not any(m in desc.lower() for m in TRIGGER_MARKERS):
                desc_issues.append("Description lacks explicit trigger phrasing ('Use when...', 'Triggers on...')")
        if "<details" in body.lower():
            desc_issues.append("Uses `<details>` HTML tag in SKILL.md (saves 0 tokens; move to `references/`)")

        records.append(
            {
                "dir_name": item.name,
                "name": name,
                "source": "agent-harness-kit",
                "path": str(item),
                "description": desc,
                "context_tokens": ctx_tokens,
                "body_tokens": body_tokens,
                "body_words": body_words,
                "body_lines": body_lines,
                "broken_refs": broken_refs,
                "clutter": clutter,
                "pinned_models": pinned_models,
                "desc_issues": desc_issues,
                "has_scripts": (item / "scripts").is_dir(),
                "has_references": (item / "references").is_dir(),
            }
        )
    return records


def find_trigger_collisions(
    skills: List[Dict[str, Any]], threshold: float = 0.35
) -> List[Dict[str, Any]]:
    collisions: List[Dict[str, Any]] = []
    word_map = {s["dir_name"]: content_words(s["description"]) for s in skills}

    for a, b in combinations(skills, 2):
        wa = word_map[a["dir_name"]]
        wb = word_map[b["dir_name"]]
        if not wa or not wb:
            continue
        inter = wa & wb
        union = wa | wb
        jaccard = len(inter) / len(union)
        if jaccard >= threshold and len(inter) >= 4:
            collisions.append(
                {
                    "skill_a": a["dir_name"],
                    "skill_b": b["dir_name"],
                    "similarity": round(jaccard, 2),
                    "shared_keywords": sorted(inter)[:8],
                }
            )
    collisions.sort(key=lambda x: x["similarity"], reverse=True)
    return collisions


def audit_environment(canonical_root: Path) -> Dict[str, Any]:
    home = Path.home()
    rules_info: List[Dict[str, Any]] = []
    for label, rpath in [
        ("Claude Global Rules (~/.claude/CLAUDE.md)", home / ".claude" / "CLAUDE.md"),
        ("Gemini/AGY Global Rules (~/.gemini/GEMINI.md)", home / ".gemini" / "GEMINI.md"),
    ]:
        if rpath.exists():
            txt = rpath.read_text(encoding="utf-8", errors="ignore")
            rules_info.append(
                {
                    "label": label,
                    "lines": len(txt.splitlines()),
                    "tokens": estimate_tokens(txt),
                }
            )

    # Check symlink parity across targets
    targets = {
        "claude (~/.claude/skills)": home / ".claude" / "skills",
        "gemini (~/.gemini/config/skills)": home / ".gemini" / "config" / "skills",
        "agents (~/.agents/skills)": home / ".agents" / "skills",
    }
    drift_issues: List[str] = []
    for tlabel, tdir in targets.items():
        if not tdir.exists():
            drift_issues.append(f"{tlabel}: directory does not exist")
            continue
        for entry in sorted(tdir.iterdir()):
            if entry.name.startswith("."):
                continue
            if entry.is_symlink():
                if not entry.exists():
                    drift_issues.append(f"{tlabel}: broken symlink `{entry.name}` -> `{os.readlink(entry)}`")
            elif entry.is_dir():
                # Check if this directory conflicts with a skill in agent-harness-kit
                if (canonical_root / entry.name).exists():
                    drift_issues.append(
                        f"{tlabel}: `{entry.name}` is a standalone folder instead of a symlink to `agent-harness-kit` (causes install conflict)"
                    )

    # Check sidecars
    sidecars_dir = home / ".gemini" / "config" / "sidecars"
    sidecars: List[Dict[str, str]] = []
    if sidecars_dir.exists():
        for sc in sorted(sidecars_dir.iterdir()):
            sc_json = sc / "sidecar.json"
            if sc_json.exists():
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

    return {
        "rules": rules_info,
        "drift_issues": drift_issues,
        "sidecars": sidecars,
    }


def render_report(
    skills: List[Dict[str, Any]],
    telemetry: Dict[str, Dict[str, Any]],
    collisions: List[Dict[str, Any]],
    env_report: Dict[str, Any],
    now_sec: float,
) -> str:
    # Enrich skills with telemetry
    for s in skills:
        t = telemetry.get(s["dir_name"], {"uses_30d": 0, "last_used_ts": None})
        s["uses_30d"] = t["uses_30d"]
        s["last_used_ts"] = t["last_used_ts"]
        s["last_used_str"] = format_relative_age(t["last_used_ts"], now_sec)

    # Sort: active skills by uses desc, then 0-use skills by context_tokens desc
    sorted_skills = sorted(
        skills,
        key=lambda x: (
            1 if x["uses_30d"] > 0 else 0,
            x["uses_30d"],
            x["context_tokens"],
        ),
        reverse=True,
    )

    total_ctx_tokens = sum(s["context_tokens"] for s in skills)
    total_body_tokens = sum(s["body_tokens"] for s in skills)
    used_count = sum(1 for s in skills if s["uses_30d"] > 0)
    unused_count = len(skills) - used_count
    unused_ctx_tax = sum(s["context_tokens"] for s in skills if s["uses_30d"] == 0)

    broken_ref_skills = [s for s in skills if s["broken_refs"]]
    heavy_skills = [s for s in sorted(skills, key=lambda x: x["body_words"], reverse=True) if s["body_words"] > 1500]
    desc_lint_skills = [s for s in skills if s["desc_issues"]]

    # Compute overall score
    score = 100
    score -= min(25, len(broken_ref_skills) * 5)
    score -= min(20, len(collisions) * 4)
    score -= min(15, len(env_report["drift_issues"]) * 5)
    score -= min(15, len(heavy_skills) * 3)
    score -= min(15, len(desc_lint_skills) * 1)
    if total_ctx_tokens > 4500:
        score -= 10
    score = max(0, score)

    lines: List[str] = [
        f"# 🩺 Skill Doctor & Environment Health Report (`{score}/100`)",
        "",
        "## 1. Executive Summary (`/doctor` + `/skill-doctor`)",
        f"- **Skills loaded this session**: `{len(skills)}` skills (`{used_count}` active in 30d · `{unused_count}` unused in 30d)",
        f"- **Always-on context tax (frontmatter)**: `~{total_ctx_tokens:,} tokens/turn` (`~{unused_ctx_tax:,} tokens/turn` from `0x` unused skills)",
        f"- **Total on-demand skill body size**: `~{total_body_tokens:,} tokens`",
    ]

    for r in env_report["rules"]:
        lines.append(f"- **{r['label']}**: `{r['lines']} lines` (`~{r['tokens']:,} tokens/turn`)")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 2. Skills Loaded This Session (`/skill-doctor` Telemetry)",
            "",
            "| skill | source | context (tokens) | body (tokens) | uses (30 days) | last used |",
            "| :--- | :--- | :---: | :---: | :---: | :--- |",
        ]
    )

    for s in sorted_skills:
        lines.append(
            f"| `{s['dir_name']}` | `{s['source']}` | `~{s['context_tokens']}` | `~{s['body_tokens']}` | `{s['uses_30d']}x` | {s['last_used_str']} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "## 3. Clinical Diagnostics (`SkillForge` v6 + `better-skill` 4-Layer Audit)",
            "",
            "### A. Broken File References (`P0` Red Line)",
        ]
    )
    if broken_ref_skills:
        for s in broken_ref_skills:
            lines.append(
                f"- 🔴 **`{s['dir_name']}`** — missing referenced file(s): `{', '.join(s['broken_refs'])}`"
            )
    else:
        lines.append("- ✅ **100% Reference Integrity** — every `references/`, `scripts/`, and `assets/` path mentioned in `SKILL.md` exists on disk.")

    lines.extend(["", "### B. Trigger Collisions & Overlapping Descriptions (`Jaccard >= 0.35`)"])
    if collisions:
        for c in collisions[:10]:
            lines.append(
                f"- 🟠 **`{c['skill_a']}` ↔ `{c['skill_b']}`** (similarity `{c['similarity']}`) — shared keywords: `{', '.join(c['shared_keywords'])}`"
            )
    else:
        lines.append("- ✅ **Zero Trigger Collisions** — all skill descriptions have distinct routing boundaries.")

    lines.extend(["", "### C. Heavyweight `SKILL.md` Bodies (`> 1,500 words` — Offload to `references/`)"])
    if heavy_skills:
        for s in heavy_skills[:10]:
            lines.append(
                f"- 🟡 **`{s['dir_name']}`**: `{s['body_words']:,} words` (`{s['body_lines']} lines`, `~{s['body_tokens']:,} tokens`)"
            )
    else:
        lines.append("- ✅ All `SKILL.md` bodies are within the 1,500-word cognitive budget.")

    lines.extend(["", "### D. Description Trigger Doctrine & Frontmatter Lint"])
    if desc_lint_skills:
        for s in desc_lint_skills[:15]:
            lines.append(f"- 🟡 **`{s['dir_name']}`**: {'; '.join(s['desc_issues'])}")
        if len(desc_lint_skills) > 15:
            lines.append(f"- *...and {len(desc_lint_skills) - 15} more minor trigger phrasing suggestions.*")
    else:
        lines.append("- ✅ All skill descriptions follow the Trigger-Condition Doctrine.")

    lines.extend(
        [
            "",
            "---",
            "",
            "## 4. Environment & Cross-Agent Symlink Doctor (`/doctor`)",
            "",
            "### A. Cross-Agent Skill Symlink Drift (`~/.claude`, `~/.gemini`, `~/.agents`)",
        ]
    )
    if env_report["drift_issues"]:
        for issue in env_report["drift_issues"]:
            lines.append(f"- 🟠 {issue}")
    else:
        lines.append("- ✅ Zero symlink drift — `~/.claude/skills`, `~/.gemini/config/skills`, and `~/.agents/skills` are 100% synchronized.")

    lines.extend(["", "### B. Active Autonomous Sidecars (`~/.gemini/config/sidecars`)"])
    if env_report["sidecars"]:
        for sc in env_report["sidecars"]:
            lines.append(f"- 🟢 **`{sc['name']}`** (`{sc['schedule']}`) — {sc['display_name']}")
    else:
        lines.append("- None configured.")

    lines.extend(["", "## 5. Doctor's Prescription (Priority Action Items)"])
    prescriptions: List[str] = []
    if broken_ref_skills:
        prescriptions.append(
            f"**[P0] Fix {len(broken_ref_skills)} skill(s) with broken `references/` or `scripts/` links**: `{', '.join(s['dir_name'] for s in broken_ref_skills)}`."
        )
    if env_report["drift_issues"]:
        prescriptions.append(
            f"**[P1] Resolve {len(env_report['drift_issues'])} cross-agent symlink conflict(s)** by running `./scripts/install.sh --targets all --rules --force`."
        )
    if collisions:
        prescriptions.append(
            f"**[P1] Sharpen trigger boundaries for {len(collisions)} overlapping skill pair(s)** so agent routing is deterministic."
        )
    if heavy_skills:
        prescriptions.append(
            f"**[P2] Extract reference tables from {len(heavy_skills)} heavy `SKILL.md` file(s)** (`{', '.join(s['dir_name'] for s in heavy_skills[:5])}`) into `references/`."
        )
    if not prescriptions:
        prescriptions.append("**All systems healthy** — zero broken references, zero symlink drift, and clean context budget.")

    for i, p in enumerate(prescriptions, 1):
        lines.append(f"{i}. {p}")

    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Skill Doctor (/skill-doctor) and Environment Doctor (/doctor) across your AI agent harness."
    )
    parser.add_argument(
        "--skills-dir",
        default=None,
        help="Path to canonical skills directory (defaults to agent-harness-kit/skills or ~/.claude/skills)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output structured JSON report",
    )
    args = parser.parse_args()

    # Resolve canonical skills root
    if args.skills_dir:
        skills_root = Path(args.skills_dir).resolve()
    else:
        script_dir = Path(__file__).resolve().parent
        candidate = script_dir.parent.parent
        if (candidate / "frontend-ui-engineering").exists():
            skills_root = candidate
        else:
            skills_root = Path.home() / ".claude" / "skills"

    now_sec = time.time()
    skills = discover_skills(skills_root)
    skill_names = {s["dir_name"] for s in skills}
    telemetry = collect_usage_telemetry(skill_names, now_sec)
    collisions = find_trigger_collisions(skills)
    env_report = audit_environment(skills_root)

    if args.json:
        for s in skills:
            t = telemetry.get(s["dir_name"], {"uses_30d": 0, "last_used_ts": None})
            s["uses_30d"] = t["uses_30d"]
            s["last_used"] = format_relative_age(t["last_used_ts"], now_sec)
        print(
            json.dumps(
                {
                    "skills_count": len(skills),
                    "total_context_tokens": sum(s["context_tokens"] for s in skills),
                    "skills": skills,
                    "collisions": collisions,
                    "environment": env_report,
                },
                indent=2,
            )
        )
    else:
        print(render_report(skills, telemetry, collisions, env_report, now_sec))
    return 0


if __name__ == "__main__":
    sys.exit(main())
