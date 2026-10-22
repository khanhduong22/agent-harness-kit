#!/usr/bin/env python3
"""Validate skill structure and cross-machine portability."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_rules import parse_profile_mcp  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ABSOLUTE_USER_RE = re.compile(r"(?<![a-zA-Z0-9_.-])/(?:Users|home)/[^/\s]+/")
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
            raw_val = match.group(2)
            if (
                raw_val
                and not (
                    (raw_val.startswith('"') and raw_val.endswith('"'))
                    or (raw_val.startswith("'") and raw_val.endswith("'"))
                )
                and ": " in raw_val
            ):
                raise ValueError(
                    f"unquoted YAML value for '{match.group(1)}' contains ': ' which breaks YAML parsers; wrap in quotes"
                )
            values[match.group(1)] = raw_val.strip("'\"")
    return values


def skill_roots() -> list[Path]:
    roots = [SKILLS]
    overlay_root = ROOT / "overlays"
    if overlay_root.is_dir():
        roots.extend(sorted(overlay_root.glob("*/skills")))
    return roots


def _is_pointer_stub(path: Path) -> bool:
    """Return True if path is a pointer-only stub or thin adapter rather than a full ruleset."""
    if not path.is_file():
        return False
    try:
        content = path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return False

    if "# Workspace Rules — Pointer Only" in content:
        return True

    if content.startswith("@") and "# Agent Adapter" in content:
        return True

    if content.startswith("@"):
        remaining_lines = [
            line.strip()
            for line in content.splitlines()
            if line.strip()
            and not line.strip().startswith("@")
            and not line.strip().startswith("#")
            and not (line.strip().startswith("<!--") and line.strip().endswith("-->"))
        ]
        remaining_text = " ".join(remaining_lines)
        if len(remaining_text) < 50:
            return True

    return False


def check_duplicate_rules(workspaces: list[Path]) -> list[str]:
    """Report error if both AGENTS.md and .agents/AGENTS.md exist in a workspace or subproject."""
    errors: list[str] = []
    checked: set[Path] = set()

    for ws in workspaces:
        try:
            ws_resolved = ws.expanduser().resolve()
        except (OSError, RuntimeError):
            continue
        if ws_resolved in checked or not ws_resolved.is_dir():
            continue
        checked.add(ws_resolved)

        # 1. Check workspace root
        root_agents = ws_resolved / "AGENTS.md"
        dot_agents = ws_resolved / ".agents" / "AGENTS.md"
        if root_agents.is_file() and dot_agents.is_file():
            if not (_is_pointer_stub(root_agents) or _is_pointer_stub(dot_agents)):
                errors.append(
                    f"{ws_resolved}: duplicate rule files detected ({root_agents.name} and .agents/{dot_agents.name}); "
                    "choose exactly one rule file to prevent conflicting rules and context duplication"
                )

        # 2. Check immediate subdirectories (e.g. monorepo services / packages)
        try:
            children = sorted(ws_resolved.iterdir())
        except (OSError, PermissionError):
            continue

        for child in children:
            if (
                child.is_dir()
                and not child.name.startswith(".")
                and child.name not in {"node_modules", "dist", "build", "coverage", "vendor", "scratch", ".git"}
            ):
                child_root = child / "AGENTS.md"
                child_dot = child / ".agents" / "AGENTS.md"
                if child_root.is_file() and child_dot.is_file():
                    if not (_is_pointer_stub(child_root) or _is_pointer_stub(child_dot)):
                        errors.append(
                            f"{child}: duplicate rule files detected ({child_root.name} and .agents/{child_dot.name}); "
                            "choose exactly one rule file to prevent conflicting rules and context duplication"
                        )
    return errors


def check_agy_rule_frontmatter(workspaces: list[Path]) -> list[str]:
    """Validate that .agents/rules/*.md frontmatter has globs as a string, not a YAML sequence."""
    errors: list[str] = []
    checked_rules: set[Path] = set()

    for ws in workspaces:
        try:
            ws_resolved = ws.expanduser().resolve()
        except (OSError, RuntimeError):
            continue
        if not ws_resolved.is_dir():
            continue

        rule_dirs: list[Path] = [ws_resolved / ".agents" / "rules"]
        try:
            for child in ws_resolved.iterdir():
                if (
                    child.is_dir()
                    and not child.name.startswith(".")
                    and child.name not in {"node_modules", "dist", "build", "coverage", "vendor", "scratch", ".git"}
                ):
                    rule_dirs.append(child / ".agents" / "rules")
        except (OSError, PermissionError):
            pass

        for r_dir in rule_dirs:
            if not r_dir.is_dir():
                continue
            for rule_file in sorted(r_dir.glob("*.md")):
                rule_resolved = rule_file.resolve()
                if rule_resolved in checked_rules:
                    continue
                checked_rules.add(rule_resolved)

                try:
                    lines = rule_resolved.read_text(encoding="utf-8").splitlines()
                except (OSError, UnicodeDecodeError):
                    continue

                if not lines or lines[0].strip() != "---":
                    continue
                try:
                    end = lines.index("---", 1)
                except ValueError:
                    continue

                for i in range(1, end):
                    line = lines[i].strip()
                    m = re.match(r"^globs:\s*(.*)$", line)
                    if m:
                        val = m.group(1).strip()
                        is_seq = False
                        if val.startswith("[") or val.startswith("-"):
                            is_seq = True
                        elif not val or val.startswith("#"):
                            for j in range(i + 1, end):
                                next_line = lines[j].strip()
                                if not next_line or next_line.startswith("#"):
                                    continue
                                if next_line.startswith("-") or next_line.startswith("["):
                                    is_seq = True
                                break
                        if is_seq:
                            errors.append(
                                f"{rule_file}: 'globs' in .agents/rules frontmatter must be a string (e.g. globs: \"path/**\"), not a YAML sequence"
                            )
                        break
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate skill structure and cross-machine portability.")
    parser.add_argument("workspaces", nargs="*", type=Path, help="Optional workspace directories to check")
    parser.add_argument("--workspace", dest="extra_workspaces", action="append", type=Path, default=[], help="Workspace directory to check")
    args = parser.parse_args(argv)

    workspaces: list[Path] = [ROOT]
    if args.workspaces:
        workspaces.extend(args.workspaces)
    if args.extra_workspaces:
        workspaces.extend(args.extra_workspaces)
    env_ws = os.environ.get("AGENT_HARNESS_WORKSPACE")
    if env_ws:
        workspaces.append(Path(env_ws))

    errors: list[str] = []
    errors.extend(check_duplicate_rules(workspaces))
    errors.extend(check_agy_rule_frontmatter(workspaces))

    names: dict[str, Path] = {}
    skill_dirs = sorted(
        path
        for skill_root in skill_roots()
        for path in skill_root.iterdir()
        if path.is_dir() and path.name != "drafts" and not path.name.startswith(".")
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

    # Optional manifests
    optional_manifests = [
        ROOT / ".claude-plugin" / "hooks.json",
    ]
    for om in optional_manifests:
        if om.is_file():
            try:
                json.loads(om.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                errors.append(f"{om.relative_to(ROOT)}: invalid JSON ({exc})")

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
