#!/usr/bin/env python3
"""Validate skill structure and cross-machine portability."""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_rules import parse_profile_mcp  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ABSOLUTE_USER_RE = re.compile(r"/(?:Users|home)/[^/]+/")
SECRET_KEY_RE = re.compile(r"KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|AUTH", re.IGNORECASE)
VAR_REF_RE = re.compile(r"^\$\{[A-Za-z_][A-Za-z0-9_]*\}$")
EMBEDDED_CREDENTIAL_RE = re.compile(r"://[^/\s:@]++:([^/\s@]++)@")


def _secret_finding(key_path: str, leaf_key: str, value: str) -> str | None:
    if SECRET_KEY_RE.search(leaf_key) and not VAR_REF_RE.fullmatch(value):
        return f"{key_path} holds a literal secret; use a ${{VAR}} reference"
    embedded = EMBEDDED_CREDENTIAL_RE.search(value)
    if embedded and not VAR_REF_RE.fullmatch(embedded.group(1)):
        return f"{key_path} embeds a literal credential; use a ${{VAR}} reference"
    return None


def literal_secret_errors(profile: dict) -> list[str]:
    """Return `key: reason` findings for MCP values holding a literal secret.

    Profiles may reference credentials only as `${VAR}`. A secret-ish key
    (TOKEN, KEY, SECRET, PASSWORD, ...) must hold exactly a `${VAR}` reference,
    and no value may embed `user:password@` credentials in a URL.
    """
    findings: list[str] = []

    def walk(key_path: str, leaf_key: str, value: object) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                walk(f"{key_path}.{key}", str(key), item)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(f"{key_path}[{index}]", leaf_key, item)
        elif isinstance(value, str):
            finding = _secret_finding(key_path, leaf_key, value)
            if finding:
                findings.append(finding)

    for name, spec in (profile.get("mcp") or {}).items():
        walk(f"mcp.{name}", name, spec)
    return findings


def profile_mcp_errors(profile_dir: Path) -> list[str]:
    """Parse every profile's MCP block and report malformed toml or literal secrets."""
    errors: list[str] = []
    for profile_path in sorted(profile_dir.rglob("*.md")):
        relative = profile_path.relative_to(ROOT) if profile_path.is_relative_to(ROOT) else profile_path
        try:
            profile = parse_profile_mcp(profile_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            errors.append(f"{relative}: {exc}")
            continue
        errors.extend(f"{relative}: {finding}" for finding in literal_secret_errors(profile))
    return errors


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

    # Vendored dependencies are not ours to fix: npm ships files carrying the
    # publisher's own home path. Scanning them would fail the portability check
    # on every `npm install`. Generated output (dist/) is still scanned.
    scan_skip_dirs = {".git", "node_modules"}
    for candidate in ROOT.rglob("*"):
        if not candidate.is_file() or scan_skip_dirs.intersection(candidate.parts):
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
        errors.extend(profile_mcp_errors(profile_dir))

    if errors:
        print("verification failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"verified {len(skill_dirs)} skills, manifests, and profiles; checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
