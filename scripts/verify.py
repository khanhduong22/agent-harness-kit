#!/usr/bin/env python3
"""Validate skill structure and cross-machine portability."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ABSOLUTE_USER_RE = re.compile(r"/(?:Users|home)/[^/]+/")


def frontmatter(skill_file: Path) -> dict[str, str]:
    lines = skill_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening frontmatter delimiter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("missing closing frontmatter delimiter") from exc
    values: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", line)
        if match:
            values[match.group(1)] = match.group(2).strip("'\"")
    return values


def skill_roots() -> list[Path]:
    roots = [SKILLS]
    overlay_root = ROOT / "overlays"
    if overlay_root.is_dir():
        roots.extend(sorted(overlay_root.glob("*/skills")))
    return roots


def main() -> int:
    errors: list[str] = []
    names: dict[str, Path] = {}
    skill_dirs = sorted(
        path
        for skill_root in skill_roots()
        for path in skill_root.iterdir()
        if path.is_dir()
    )
    for skill_dir in skill_dirs:
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"{skill_dir}: missing SKILL.md")
            continue
        try:
            metadata = frontmatter(skill_file)
        except ValueError as exc:
            errors.append(f"{skill_file}: {exc}")
            continue
        name = metadata.get("name", "")
        description = metadata.get("description", "")
        if not NAME_RE.fullmatch(name):
            errors.append(f"{skill_file}: invalid name {name!r}")
        if name != skill_dir.name:
            errors.append(f"{skill_file}: name must match folder {skill_dir.name!r}")
        if not description:
            errors.append(f"{skill_file}: missing description")
        if name in names:
            errors.append(f"{skill_file}: duplicate name also used by {names[name]}")
        names[name] = skill_file

    for candidate in ROOT.rglob("*"):
        if not candidate.is_file() or ".git" in candidate.parts:
            continue
        try:
            content = candidate.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if ABSOLUTE_USER_RE.search(content):
            errors.append(f"{candidate}: contains a machine-specific home path")

    # Validate native manifests and marketplace catalogs
    manifest_files = [
        ROOT / ".agents" / "plugins" / "marketplace.json",
        ROOT / ".claude-plugin" / "plugin.json",
        ROOT / ".claude-plugin" / "marketplace.json",
        ROOT / ".codex-plugin" / "plugin.json",
    ]
    import json
    for mf in manifest_files:
        if not mf.is_file():
            errors.append(f"missing required manifest: {mf.relative_to(ROOT)}")
            continue
        try:
            mdata = json.loads(mf.read_text(encoding="utf-8"))
            if not mdata.get("name"):
                errors.append(f"{mf.relative_to(ROOT)}: missing or empty 'name' field")
        except json.JSONDecodeError as exc:
            errors.append(f"{mf.relative_to(ROOT)}: invalid JSON ({exc})")

    # Validate profiles
    profile_dir = ROOT / "profiles"
    if not profile_dir.is_dir():
        errors.append("missing profiles/ directory")
    else:
        for req_profile in ["core/rules.md", "index/workspace.md", "index/api.md", "index/cms.md"]:
            if not (profile_dir / req_profile).is_file():
                errors.append(f"missing profile document: profiles/{req_profile}")

    if errors:
        print("verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"verified {len(skill_dirs)} skills, manifests, and profiles; checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
