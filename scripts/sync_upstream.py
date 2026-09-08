#!/usr/bin/env python3
"""Sync vendored skills from upstream repositories with check and apply modes."""

from __future__ import annotations

import argparse
import filecmp
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"

SOURCES = {
    "mattpocock": {
        "url": "https://github.com/mattpocock/skills.git",
        "branch": "main",
        "target_skills": [
            "ask-matt",
            "code-review",
            "codebase-design",
            "diagnosing-bugs",
            "domain-modeling",
            "grill-me",
            "grill-with-docs",
            "grilling",
            "handoff",
            "implement",
            "improve-codebase-architecture",
            "prototype",
            "research",
            "resolving-merge-conflicts",
            "setup-matt-pocock-skills",
            "tdd",
            "teach",
            "to-questionnaire",
            "to-spec",
            "to-tickets",
            "triage",
            "wait-what",
            "wayfinder",
            "wizard",
            "writing-for-agents",
        ],
    },
    "vercel-skills": {
        "url": "https://github.com/vercel-labs/skills.git",
        "branch": "main",
        "target_skills": ["find-skills"],
    },
    "vercel-next": {
        "url": "https://github.com/vercel-labs/next-skills.git",
        "branch": "main",
        "target_skills": ["next-best-practices"],
    },
    "gemini-skills": {
        "url": "https://github.com/google-gemini/gemini-skills.git",
        "branch": "main",
        "target_skills": ["gemini-api-dev"],
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync skills from upstream repositories.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="Check for available upstream updates without modifying files")
    group.add_argument("--apply", action="store_true", help="Fetch and apply upstream updates")
    parser.add_argument("--source", default="all", choices=["all", *SOURCES.keys()], help="Specific upstream source to sync")
    return parser.parse_args()


def clone_repo(url: str, branch: str, target_dir: Path) -> bool:
    cmd = [
        "git",
        "clone",
        "--depth",
        "1",
        "--branch",
        branch,
        url,
        str(target_dir),
    ]
    res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"Error cloning {url}: {res.stderr.strip()}", file=sys.stderr)
        return False
    return True


def find_skills_in_repo(repo_dir: Path) -> dict[str, Path]:
    discovered: dict[str, Path] = {}
    for skill_file in repo_dir.rglob("SKILL.md"):
        skill_dir = skill_file.parent
        discovered[skill_dir.name] = skill_dir
    return discovered


def compare_skill_dirs(local_dir: Path, upstream_dir: Path) -> tuple[list[str], list[str], list[str]]:
    """Returns (modified, added_in_upstream, removed_in_upstream)"""
    modified = []
    added = []
    removed = []

    local_files = {p.relative_to(local_dir): p for p in local_dir.rglob("*") if p.is_file()}
    upstream_files = {p.relative_to(upstream_dir): p for p in upstream_dir.rglob("*") if p.is_file()}

    for rel_path, u_path in upstream_files.items():
        if rel_path not in local_files:
            added.append(str(rel_path))
        else:
            l_path = local_files[rel_path]
            if not filecmp.cmp(l_path, u_path, shallow=False):
                modified.append(str(rel_path))

    for rel_path in local_files:
        if rel_path not in upstream_files:
            removed.append(str(rel_path))

    return modified, added, removed


def sync_source(name: str, config: dict, mode: str, tmp_base: Path) -> dict[str, str]:
    print(f"\n--- Checking source: {name} ({config['url']}) ---")
    source_tmp = tmp_base / name
    if not clone_repo(config["url"], config["branch"], source_tmp):
        return {"status": "error"}

    upstream_skills = find_skills_in_repo(source_tmp)
    target_skills = config.get("target_skills", list(upstream_skills.keys()))

    results = {}
    for skill_name in target_skills:
        local_skill_dir = SKILLS_DIR / skill_name
        if skill_name not in upstream_skills:
            print(f"  [LOCAL / PINNED] {skill_name} (no upstream match)")
            results[skill_name] = "local_pinned"
            continue

        upstream_skill_dir = upstream_skills[skill_name]
        if not local_skill_dir.is_dir():
            if mode == "check":
                print(f"  [NEW SKILL AVAILABLE] {skill_name}")
                results[skill_name] = "new"
            else:
                shutil.copytree(upstream_skill_dir, local_skill_dir)
                print(f"  [INSTALLED NEW SKILL] {skill_name}")
                results[skill_name] = "installed"
            continue

        modified, added, removed = compare_skill_dirs(local_skill_dir, upstream_skill_dir)
        has_diff = bool(modified or added or removed)

        if not has_diff:
            print(f"  [UP TO DATE] {skill_name}")
            results[skill_name] = "up_to_date"
        else:
            diff_summary = []
            if modified:
                diff_summary.append(f"{len(modified)} modified")
            if added:
                diff_summary.append(f"{len(added)} new upstream files")
            if removed:
                diff_summary.append(f"{len(removed)} local only")

            summary_str = ", ".join(diff_summary)
            if mode == "check":
                print(f"  [UPDATE AVAILABLE] {skill_name} ({summary_str})")
                results[skill_name] = "update_available"
            else:
                # Apply: copy upstream files into local skill dir
                for rel_path_str in modified + added:
                    src_file = upstream_skill_dir / rel_path_str
                    dst_file = local_skill_dir / rel_path_str
                    dst_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_file, dst_file)
                print(f"  [UPDATED] {skill_name} ({summary_str})")
                results[skill_name] = "updated"

    return results


def main() -> int:
    args = parse_args()
    mode = "check" if args.check else "apply"

    sources_to_sync = (
        SOURCES.items()
        if args.source == "all"
        else [(args.source, SOURCES[args.source])]
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_base = Path(tmp_dir)
        for name, config in sources_to_sync:
            sync_source(name, config, mode, tmp_base)

    if mode == "apply":
        print("\nValidating updated skills against portability rules...")
        verify_cmd = [sys.executable, str(ROOT / "scripts" / "verify.py")]
        res = subprocess.run(verify_cmd)
        if res.returncode != 0:
            print("Warning: verify.py failed on updated skills!", file=sys.stderr)
            return 1
        print("All skill integrity and portability checks passed.")
        print("Run './scripts/install.sh --targets all' to refresh installed symlinks.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
