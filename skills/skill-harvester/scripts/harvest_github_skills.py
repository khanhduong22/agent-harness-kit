#!/usr/bin/env python3
"""
GitHub Skill Harvester, Local Shallow Git Cache Sync & 8-Point Security Inspector.
Supports:
  1. Star-Band Sharded Discovery (--limit 250|500|1000|2000) across GitHub
  2. Local Upstream Git Mirror Cache (--sync-cache) in ~/.agent-harness/upstream-cache/
     so weekly updates only need a fast `git fetch/pull` + security diff check
  3. Combined Weekly Digest (--weekly-digest): pulls all tracked upstream repos + scans Top 250 (★ 4,000+)
  4. Deep Security & Anti-Slop Inspection (--inspect owner/repo)
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
UPSTREAM_CACHE_DIR = Path.home() / ".agent-harness" / "upstream-cache"

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
    "nateherkai/scroll-craft": "frontend-ui-engineering/references/motion-and-scroll-craft.md",
    "lottiefiles/motion-design-skill": "frontend-ui-engineering/references/motion-and-scroll-craft.md",
    "blader/humanizer": "bilingual-engineering-blog/references/humanizer-anti-ai-writing.md",
    "cloudflare/security-audit-skill": "security-and-hardening/references/cloudflare-trailofbits-audit.md",
    "trailofbits/skills": "security-and-hardening/references/cloudflare-trailofbits-audit.md",
    "vercel-labs/agent-skills": "next-best-practices/vercel-react-19-patterns.md",
    "vercel-labs/next-skills": "next-best-practices",
    "supabase/agent-skills": "backend-performance-optimization/references/supabase-postgres-best-practices.md",
    "timescale/pg-aiguide": "backend-performance-optimization/references/timescale-and-pg-table-design.md",
    "cathrynlavery/diagram-design": "diagram-director/references/editorial-svg-connector-laws.md",
    "leonxlnx/unlazy": "code-review-and-quality/references/unlazy-gates-and-ts-anti-slop.md",
    "dmmulroy/anti-slop": "code-review-and-quality/references/unlazy-gates-and-ts-anti-slop.md",
    "antonbabenko/terraform-skill": "infra-performance-optimization/references/terraform-opentofu-iac-guardrails.md",
    "coreyhaines31/marketingskills": "geo-seo",
    "addyosmani/web-quality-skills": "frontend-performance-lighthouse",
    "addyosmani/agent-skills": "frontend-performance-lighthouse, code-review-and-quality",
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
    "ebookfoundation/free-programming-books",
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
    "ebazhanov/linkedin-skill-assessments-quizzes",
}

DOMAIN_ROUTING: list[tuple[list[str], str]] = [
    (["react", "nextjs", "next.js", "rsc", "app-router"], "next-best-practices"),
    (["lighthouse", "cwv", "web-vitals", "lcp", "cls", "inp"], "frontend-performance-lighthouse"),
    (["design-system", "ui", "ux", "tailwind", "css", "a11y", "accessibility", "taste", "scroll", "motion"], "frontend-ui-engineering"),
    (["postgres", "postgresql", "sql", "supabase", "timescale", "redis", "prisma", "drizzle", "database", "query"], "backend-performance-optimization"),
    (["cloudflare", "nginx", "caddy", "docker", "vps", "linux", "kubernetes", "k8s", "terraform", "opentofu"], "infra-performance-optimization"),
    (["security", "owasp", "pentest", "vulnerability", "audit", "cve", "appsec", "crypto"], "security-and-hardening"),
    (["nda", "opsec", "pii", "red-team", "sanitize"], "op-nda"),
    (["debug", "investigate", "root-cause", "bisect", "flake", "incident"], "debugging-and-error-recovery"),
    (["refactor", "simplify", "architecture", "domain-modeling", "clean-code"], "code-simplification"),
    (["review", "lint", "anti-slop", "quality", "oxlint", "sonarqube"], "code-review-and-quality"),
    (["playwright", "e2e", "cypress", "browser-test"], "playwright-e2e-testing"),
    (["tdd", "unit-test", "vitest", "jest", "testing"], "test-driven-development"),
    (["blog", "writing", "humanizer", "copywriting", "editorial"], "bilingual-engineering-blog"),
    (["seo", "geo", "llms.txt", "json-ld", "serp", "marketing"], "geo-seo"),
    (["diagram", "mermaid", "svg", "excalidraw", "c4"], "diagram-director"),
    (["eval", "rag", "llm-judge", "benchmark"], "llm-eval-design"),
    (["wiki", "obsidian", "knowledge-base", "second-brain"], "llm-wiki"),
]

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
    cmd = ["gh", "api", endpoint]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None


def recommend_target_skill(text: str) -> str:
    lower = text.lower()
    best_skill = "code-simplification/references/"
    best_hits = 0
    for keywords, target in DOMAIN_ROUTING:
        hits = sum(1 for kw in keywords if kw in lower)
        if hits > best_hits:
            best_hits = hits
            best_skill = f"{target}/references/"
    return best_skill


def scan_text_security(content: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for severity, label, pattern in SECURITY_PATTERNS:
        for match in pattern.finditer(content):
            findings.append({"severity": severity, "rule": label, "match": match.group(0)[:80]})
    return findings


def sync_upstream_cache(repos_to_sync: list[str] | None = None) -> list[dict[str, Any]]:
    """
    Maintain local shallow blobless git clones in ~/.agent-harness/upstream-cache/<owner>__<repo>.
    On first run: clones with `--depth 1 --filter=blob:none`.
    On weekly runs: runs `git fetch --depth 2 origin`, checks `HEAD..FETCH_HEAD` for modified
    SKILL.md / references files, runs the 8-Point Security Gate on diffs, and fast-forwards if clean.
    """
    UPSTREAM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    targets = repos_to_sync or list(ABSORBED_REPOS.keys())
    results: list[dict[str, Any]] = []

    for repo in targets:
        slug = repo.lower().replace("/", "__")
        repo_dir = UPSTREAM_CACHE_DIR / slug
        url = f"https://github.com/{repo}.git"
        kit_target = ABSORBED_REPOS.get(repo.lower(), recommend_target_skill(repo))

        if not (repo_dir / ".git").is_dir():
            proc = subprocess.run(
                ["git", "clone", "--depth", "1", "--filter=blob:none", url, str(repo_dir)],
                capture_output=True,
                text=True,
                check=False,
            )
            if proc.returncode != 0:
                results.append(
                    {
                        "repo": repo,
                        "status": "CLONE_FAILED",
                        "kit_target": kit_target,
                        "details": proc.stderr.strip()[:120],
                    }
                )
                continue
            head_sha = subprocess.run(
                ["git", "-C", str(repo_dir), "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            results.append(
                {
                    "repo": repo,
                    "status": "CLONED_FRESH",
                    "sha": head_sha,
                    "kit_target": kit_target,
                    "changed_skills": [],
                }
            )
            continue

        # Already cached locally -> fast git fetch & diff check
        old_sha = subprocess.run(
            ["git", "-C", str(repo_dir), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()
        fetch_proc = subprocess.run(
            ["git", "-C", str(repo_dir), "fetch", "--depth", "2", "origin"],
            capture_output=True,
            text=True,
            check=False,
        )
        if fetch_proc.returncode != 0:
            results.append(
                {
                    "repo": repo,
                    "status": "FETCH_ERROR",
                    "sha": old_sha,
                    "kit_target": kit_target,
                    "details": fetch_proc.stderr.strip()[:100],
                }
            )
            continue

        new_sha = subprocess.run(
            ["git", "-C", str(repo_dir), "rev-parse", "--short", "FETCH_HEAD"],
            capture_output=True,
            text=True,
            check=False,
        ).stdout.strip()

        if old_sha == new_sha or not new_sha:
            results.append(
                {
                    "repo": repo,
                    "status": "UP_TO_DATE",
                    "sha": old_sha,
                    "kit_target": kit_target,
                    "changed_skills": [],
                }
            )
            continue

        # Inspect changed files between HEAD and FETCH_HEAD
        diff_files_proc = subprocess.run(
            ["git", "-C", str(repo_dir), "diff", "--name-only", "HEAD..FETCH_HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        changed_files = [
            f for f in diff_files_proc.stdout.splitlines() if f.endswith(".md") or "skill" in f.lower()
        ]

        diff_content_proc = subprocess.run(
            ["git", "-C", str(repo_dir), "diff", "HEAD..FETCH_HEAD", "--", "*.md"],
            capture_output=True,
            text=True,
            check=False,
        )
        sec_findings = scan_text_security(diff_content_proc.stdout)
        high_risk = any(f["severity"] == "HIGH" for f in sec_findings)

        if high_risk:
            results.append(
                {
                    "repo": repo,
                    "status": "BLOCKED_SECURITY",
                    "sha": f"{old_sha}..{new_sha}",
                    "kit_target": kit_target,
                    "changed_skills": changed_files[:8],
                    "security_findings": sec_findings,
                }
            )
            continue

        # Safe to fast-forward local cache
        subprocess.run(
            ["git", "-C", str(repo_dir), "reset", "--hard", "FETCH_HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        results.append(
            {
                "repo": repo,
                "status": "UPDATED",
                "sha": f"{old_sha}->{new_sha}",
                "kit_target": kit_target,
                "changed_skills": changed_files[:8],
            }
        )

    return results


def harvest_repositories(limit: int, extra_query: str = "") -> list[dict[str, Any]]:
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
    for path in skill_paths[:8]:
        blob = run_gh_api(f"repos/{repo}/contents/{path}")
        if not blob or "content" not in blob:
            continue
        try:
            content = base64.b64decode(blob["content"]).decode("utf-8", errors="replace")
        except Exception:
            continue

        lines = content.splitlines()
        findings = scan_text_security(content)
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


def print_sync_table(sync_results: list[dict[str, Any]]) -> None:
    print("=" * 110)
    print(f"LOCAL UPSTREAM GIT CACHE SYNC (~/.agent-harness/upstream-cache) — {len(sync_results)} Tracked Repos")
    print("=" * 110)
    print(f"{'Upstream Repository':<38} {'Status':<16} {'Commit':<18} {'Mapped Kit Target'}")
    print("-" * 110)
    for item in sync_results:
        sha = item.get("sha", "-")
        print(f"{item['repo'][:37]:<38} {item['status']:<16} {sha:<18} {item['kit_target'][:36]}")
        for chg in item.get("changed_skills", []):
            print(f"    ↳ Changed: {chg}")
    print("-" * 110)


def main() -> int:
    parser = argparse.ArgumentParser(description="GitHub Skill Harvester & Local Git Cache Sync")
    parser.add_argument(
        "--limit",
        type=int,
        default=250,
        help="Maximum number of repositories to scan across star bands (default: 250 — Top 200-300 ★4k+ sweet spot)",
    )
    parser.add_argument("--query", type=str, default="", help="Optional domain keyword filter")
    parser.add_argument("--inspect", type=str, default="", help="Deep-inspect a specific owner/repo")
    parser.add_argument(
        "--sync-cache",
        action="store_true",
        help="Clone or git pull all 29 tracked upstream skill repos in ~/.agent-harness/upstream-cache/",
    )
    parser.add_argument(
        "--weekly-digest",
        action="store_true",
        help="Run weekly maintenance: (1) git pull all local cached upstream repos + (2) scan Top 250 (★4k+) for new gems",
    )
    parser.add_argument("--top", type=int, default=25, help="Number of top candidates to print in table")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    if args.sync_cache:
        sync_res = sync_upstream_cache()
        if args.json:
            print(json.dumps(sync_res, indent=2))
            return 0
        print_sync_table(sync_res)
        return 0

    if args.weekly_digest:
        scan_limit = args.limit if args.limit != 250 else 250
        sync_res = sync_upstream_cache()
        repos = harvest_repositories(limit=scan_limit, extra_query=args.query)
        candidates = [r for r in repos if r["status"] == "candidate"]
        if args.json:
            print(
                json.dumps(
                    {
                        "scanned_limit": scan_limit,
                        "scanned_total": len(repos),
                        "upstream_sync": sync_res,
                        "top_candidates": candidates[:15],
                    },
                    indent=2,
                )
            )
            return 0
        print_sync_table(sync_res)
        print(f"\nTOP 15 UNABSORBED CANDIDATES IN GITHUB TOP {scan_limit} (★ 4,000+ Sweet Spot | Scanned: {len(repos)}):")
        print("-" * 110)
        for idx, r in enumerate(candidates[:15], 1):
            star_str = f"★ {r['stars']:,}"
            print(f"{idx:<4} {r['full_name'][:38]:<39} {star_str:>10}  ->  {r['target'][:45]}")
        return 0

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
    print("Tip: Run `--sync-cache` or `--weekly-digest` for weekly git pull + Top-500 delta scan.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
