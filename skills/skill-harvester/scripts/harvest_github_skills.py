#!/usr/bin/env python3
"""
GitHub Skill Harvester & 8-Point Security Inspector for agent-harness-kit.
Scans 500–2,000+ GitHub repositories across sharded star bands (bypassing GitHub's
1,000-result search ceiling), deduplicates against already-absorbed skills, and
audits candidate SKILL.md files for prompt injection, RCE, and slop.
"""

from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

KIT_ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = KIT_ROOT / "skills"

# Repositories already absorbed into agent-harness-kit (upstream -> kit target)
ABSORBED_REPOS: dict[str, str] = {
    "anthropics/skills": "frontend-ui-engineering, code-simplification, skill-doctor",
    "anthropics/knowledge-work-plugins": "frontend-ui-engineering/references/claude-design-system-and-anti-slop.md",
    "anthropics/claude-plugins-official": "code-simplification",
    "mattpocock/skills": "code-simplification/references/deep-modules-and-domain-modeling.md",
    "garrytan/gstack": "debugging-and-error-recovery/references/gstack-investigate-and-careful.md",
    "multica-ai/andrej-karpathy-skills": "ponytail/references/karpathy-and-caveman-rules.md",
    "juliusbrussee/caveman": "ponytail/references/karpathy-and-caveman-rules.md",
    "dietrichgebert/ponytail": "ponytail",
    "leonxlnx/taste-skill": "frontend-ui-engineering/references/impeccable-taste-and-polish.md",
    "pbakaus/impeccable": "frontend-ui-engineering/references/impeccable-taste-and-polish.md",
    "blader/humanizer": "bilingual-engineering-blog/references/humanizer-anti-ai-writing.md",
    "cloudflare/security-audit-skill": "security-and-hardening/references/cloudflare-trailofbits-audit.md",
    "trailofbits/skills": "security-and-hardening/references/cloudflare-trailofbits-audit.md",
    "vercel-labs/agent-skills": "next-best-practices/vercel-react-19-patterns.md",
    "supabase/agent-skills": "backend-performance-optimization/references/supabase-postgres-best-practices.md",
    "coreyhaines31/marketingskills": "geo-seo",
    "addyosmani/web-quality-skills": "frontend-performance-lighthouse",
    "nextlevelbuilder/ui-ux-pro-max-skill": "ui-ux-pro-max",
    "obra/superpowers": "test-driven-development, debugging-and-error-recovery, planning-and-task-breakdown",
    "remotion-dev/skills": "tech-reel-factory",
}

# Popular repos that match "skills" queries but are awesome-lists, GUI apps, or non-skill tools
NON_SKILL_REPOS: set[str] = {
    "sindresorhus/awesome",
    "vinta/awesome-python",
    "avelino/awesome-go",
    "trimstray/the-book-of-secret-knowledge",
    "kamranahmedse/developer-roadmap",
    "donnemartin/system-design-primer",
    "EbookFoundation/free-programming-books",
    "jwasham/coding-interview-university",
    "codecrafters-io/build-your-own-x",
    "public-apis/public-apis",
    "patrickjs/awesome-cursorrules",
    "hesreallyhim/awesome-claude-code",
    "travisvn/awesome-claude-skills",
    "composiohq/awesome-claude-skills",
    "behisecc/awesome-claude-skills",
    "voltagent/awesome-agent-skills",
    "heilcheng/awesome-agent-skills",
}

# Domain routing table for recommending zero-tax references/ merges
DOMAIN_ROUTING: list[tuple[list[str], str]] = [
    (["react", "nextjs", "next.js", "rsc", "app-router"], "next-best-practices"),
    (["lighthouse", "cwv", "web-vitals", "lcp", "cls", "inp"], "frontend-performance-lighthouse"),
    (["design-system", "ui", "ux", "tailwind", "css", "a11y", "accessibility", "taste", "figma"], "frontend-ui-engineering"),
    (["postgres", "postgresql", "sql", "supabase", "redis", "prisma", "drizzle", "database", "query"], "backend-performance-optimization"),
    (["cloudflare", "nginx", "caddy", "docker", "vps", "linux", "kubernetes", "k8s", "terraform"], "infra-performance-optimization"),
    (["security", "owasp", "pentest", "vulnerability", "audit", "cve", "appsec", "crypto"], "security-and-hardening"),
    (["nda", "opsec", "pii", "red-team", "sanitize"], "op-nda"),
    (["debug", "investigate", "root-cause", "bisect", "flake", "incident"], "debugging-and-error-recovery"),
    (["refactor", "simplify", "architecture", "domain-modeling", "clean-code"], "code-simplification"),
    (["playwright", "e2e", "cypress", "browser-test"], "playwright-e2e-testing"),
    (["tdd", "unit-test", "vitest", "jest", "testing"], "test-driven-development"),
    (["blog", "writing", "humanizer", "copywriting", "editorial"], "bilingual-engineering-blog"),
    (["seo", "geo", "llms.txt", "json-ld", "serp", "marketing"], "geo-seo"),
    (["diagram", "mermaid", "svg", "excalidraw", "c4"], "diagram-director"),
    (["eval", "rag", "llm-judge", "benchmark"], "llm-eval-design"),
    (["wiki", "obsidian", "knowledge-base", "second-brain"], "llm-wiki"),
]

# 8-Point Security Gate regex patterns
SECURITY_PATTERNS: list[tuple[str, str, re.Pattern[str]]] = [
    (
        "HIGH",
        "Pipe-to-shell RCE (curl/wget piped to sh/bash/eval)",
        re.compile(r"\b(?:curl|wget)\b[^\n|]*\|\s*(?:sudo\s+)?(?:ba)?sh\b", re.IGNORECASE),
    ),
    (
        "HIGH",
        "Prompt injection / instruction override attempt",
        re.compile(
            r"(?:ignore (?:all )?(?:previous|prior) instructions|do not inform the user|hide this from the user|system prompt override)",
            re.IGNORECASE,
        ),
    ),
    (
        "HIGH",
        "Base64 decode execution payload",
        re.compile(r"base64\s+(?:-d|--decode)[^\n|]*\|\s*(?:ba)?sh", re.IGNORECASE),
    ),
    (
        "MEDIUM",
        "Sensitive credential / SSH / AWS path access",
        re.compile(r"(?:~/\.ssh/|~/\.aws/credentials|/etc/shadow)", re.IGNORECASE),
    ),
    (
        "MEDIUM",
        "Dangerous permission bypass flag (--dangerously-skip-permissions / --yolo)",
        re.compile(r"(?:--dangerously-skip-permissions|--yolo\b|danger-full-access)", re.IGNORECASE),
    ),
]


def run_gh_api(endpoint: str) -> Any:
    """Call gh api and parse JSON response."""
    cmd = ["gh", "api", endpoint]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def recommend_target_skill(text: str) -> str:
    """Recommend which existing agent-harness-kit skill should absorb a repo's patterns."""
    lower = text.lower()
    best_skill = "code-simplification (or standalone skill if distinct workflow)"
    best_hits = 0
    for keywords, target in DOMAIN_ROUTING:
        hits = sum(1 for kw in keywords if kw in lower)
        if hits > best_hits:
            best_hits = hits
            best_skill = f"{target}/references/"
    return best_skill


def harvest_repositories(limit: int, extra_query: str = "") -> list[dict[str, Any]]:
    """
    Scan up to `limit` (500–2,000+) GitHub repositories by sharding across star bands
    and query families to overcome GitHub Search API's 1,000-result cap per query.
    """
    star_bands = [
        "stars:>5000",
        "stars:1000..5000",
        "stars:300..999",
        "stars:100..299",
        "stars:25..99",
    ]
    query_families = [
        "topic:claude-skills",
        "topic:agent-skills",
        "topic:claude-code-skills",
        "SKILL.md in:readme,description",
    ]

    seen: dict[str, dict[str, Any]] = {}
    q_suffix = f"+{extra_query}" if extra_query else ""

    for band in star_bands:
        if len(seen) >= limit:
            break
        for family in query_families:
            if len(seen) >= limit:
                break
            raw_q = f"{family}+{band}{q_suffix}".replace(" ", "+")
            # Fetch up to 2 pages (200 items) per (band, family) shard
            for page in (1, 2):
                if len(seen) >= limit:
                    break
                endpoint = f"search/repositories?q={raw_q}&sort=stars&order=desc&per_page=100&page={page}"
                data = run_gh_api(endpoint)
                if not data or not isinstance(data, dict):
                    break
                items = data.get("items") or []
                if not items:
                    break
                for item in items:
                    full_name = item.get("full_name", "")
                    key = full_name.lower()
                    if not full_name or key in seen:
                        continue
                    if key in NON_SKILL_REPOS or "awesome-" in key:
                        continue
                    desc = (item.get("description") or "").strip()
                    topics = item.get("topics") or []
                    stars = int(item.get("stargazers_count", 0))
                    status = "absorbed" if key in ABSORBED_REPOS else "candidate"
                    target = (
                        ABSORBED_REPOS[key]
                        if status == "absorbed"
                        else recommend_target_skill(f"{full_name} {desc} {' '.join(topics)}")
                    )
                    seen[key] = {
                        "full_name": full_name,
                        "stars": stars,
                        "status": status,
                        "target": target,
                        "description": desc[:110],
                        "topics": topics[:5],
                        "url": item.get("html_url", f"https://github.com/{full_name}"),
                    }
                if len(items) < 100:
                    break

    ranked = sorted(seen.values(), key=lambda r: r["stars"], reverse=True)
    return ranked[:limit]


def inspect_repository(repo: str) -> dict[str, Any]:
    """Inspect all SKILL.md files in a GitHub repository and run the 8-Point Security Gate."""
    meta = run_gh_api(f"repos/{repo}")
    if not meta:
        return {"error": f"Could not fetch repository metadata for {repo}"}

    default_branch = meta.get("default_branch", "main")
    tree_data = run_gh_api(f"repos/{repo}/git/trees/{default_branch}?recursive=1")
    tree = (tree_data or {}).get("tree", [])

    skill_paths = [
        item["path"]
        for item in tree
        if item.get("type") == "blob" and item.get("path", "").endswith("SKILL.md")
    ]

    inspected_files: list[dict[str, Any]] = []
    for path in skill_paths[:8]:  # Inspect up to 8 SKILL.md files per repo
        blob = run_gh_api(f"repos/{repo}/contents/{path}")
        if not blob or "content" not in blob:
            continue
        try:
            content = base64.b64decode(blob["content"]).decode("utf-8", errors="replace")
        except Exception:
            continue

        lines = content.splitlines()
        findings: list[dict[str, str]] = []
        for severity, label, pattern in SECURITY_PATTERNS:
            for match in pattern.finditer(content):
                findings.append({"severity": severity, "rule": label, "match": match.group(0)[:80]})

        if len(lines) < 35:
            findings.append(
                {
                    "severity": "LOW",
                    "rule": "Low-substance stub (<35 lines)",
                    "match": f"{len(lines)} lines",
                }
            )

        inspected_files.append(
            {
                "path": path,
                "lines": len(lines),
                "security_findings": findings,
                "passed_gate": not any(f["severity"] == "HIGH" for f in findings),
                "recommended_target": recommend_target_skill(f"{repo} {path} {content[:500]}"),
            }
        )

    return {
        "repo": repo,
        "stars": meta.get("stargazers_count", 0),
        "license": (meta.get("license") or {}).get("spdx_id", "UNKNOWN"),
        "already_absorbed_into": ABSORBED_REPOS.get(repo.lower()),
        "total_skill_files_found": len(skill_paths),
        "inspected_skills": inspected_files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="GitHub Skill Harvester & Security Inspector")
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Maximum number of repositories to scan across star bands (e.g. 300, 500, 1000, 2000)",
    )
    parser.add_argument("--query", type=str, default="", help="Optional domain keyword filter")
    parser.add_argument("--inspect", type=str, default="", help="Deep-inspect a specific owner/repo")
    parser.add_argument("--top", type=int, default=35, help="Number of top candidates to print in table")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    if args.inspect:
        report = inspect_repository(args.inspect)
        if args.json:
            print(json.dumps(report, indent=2))
            return 0
        if "error" in report:
            print(f"ERROR: {report['error']}", file=sys.stderr)
            return 1
        print("=" * 100)
        print(
            f"SKILL HARVESTER INSPECTOR: {report['repo']} "
            f"(★ {report['stars']:,} | License: {report['license']} | SKILL.md files: {report['total_skill_files_found']})"
        )
        if report["already_absorbed_into"]:
            print(f"STATUS: ALREADY ABSORBED -> {report['already_absorbed_into']}")
        print("=" * 100)
        for item in report["inspected_skills"]:
            gate = "PASS (✓)" if item["passed_gate"] else "BLOCKED (✗)"
            print(f"- {item['path']} ({item['lines']} lines) | Gate: {gate} | Target: {item['recommended_target']}")
            for f in item["security_findings"]:
                print(f"    [{f['severity']}] {f['rule']}: {f['match']}")
        return 0

    repos = harvest_repositories(limit=args.limit, extra_query=args.query)
    absorbed = [r for r in repos if r["status"] == "absorbed"]
    candidates = [r for r in repos if r["status"] == "candidate"]

    if args.json:
        print(
            json.dumps(
                {
                    "scanned_total": len(repos),
                    "absorbed_count": len(absorbed),
                    "new_candidates_count": len(candidates),
                    "absorbed": absorbed,
                    "top_candidates": candidates[: args.top],
                },
                indent=2,
            )
        )
        return 0

    print("=" * 110)
    print(
        f"GITHUB SKILL HARVESTER — Scanned: {len(repos)} repos | "
        f"Already Absorbed: {len(absorbed)} | Unabsorbed Candidates: {len(candidates)}"
    )
    print("=" * 110)
    print(f"{'Rank':<5} {'Repository':<38} {'Stars':>9} {'Status':<11} {'Recommended Kit Target'}")
    print("-" * 110)
    for idx, r in enumerate(repos[: args.top], 1):
        star_str = f"★ {r['stars']:,}"
        status_str = "ABSORBED ✓" if r["status"] == "absorbed" else "CANDIDATE"
        print(f"{idx:<5} {r['full_name'][:37]:<38} {star_str:>9} {status_str:<11} {r['target'][:42]}")
    print("-" * 110)
    print("Tip: Run `--inspect <owner/repo>` to audit SKILL.md files with the 8-Point Security Gate.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
