#!/usr/bin/env python3
"""Merge rendered rules or project profiles into managed blocks.

Also renders profile-declared MCP servers and tool allowlists into a target
harness's native, project-scoped configuration (``--mcp`` mode).
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import tomllib
from pathlib import Path

TOML_BLOCK_RE = re.compile(r"^```toml[ \t]*\n(.*?)^```", re.DOTALL | re.MULTILINE)

#: Targets whose native MCP config shape has been verified. Everything else is
#: reported as unsupported rather than guessed at.
MCP_SUPPORTED_TARGETS = ("claude",)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", type=Path, help="Core rules path")
    parser.add_argument("--adapter", type=Path, help="Adapter markdown path")
    parser.add_argument("--content", type=Path, help="Direct content markdown path")
    parser.add_argument("--sub-content", type=str, help="Comma-separated sub-content markdown paths")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--backup-dir", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--marker", default="agent-harness-kit", help="Block marker prefix")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--migrate-legacy",
        type=Path,
        action="append",
        default=[],
        help="Legacy CLAUDE.md to fold into --destination, back up, then remove (repeatable)",
    )
    parser.add_argument("--receipt-file", type=Path, help="Path to append action to receipt.json")
    parser.add_argument("--hooks", action="store_true", help="Merge the profile hook block instead of rules")
    parser.add_argument("--hooks-profile", type=Path, help="Path to the profile hooks.json (--hooks)")
    parser.add_argument("--hooks-dir", type=Path, help="Deployed hook scripts directory, substituted for {{HOOKS_DIR}} (--hooks)")
    parser.add_argument("--mcp", action="store_true", help="Render profile MCP config instead of rules")
    parser.add_argument("--profile", type=str, help="Comma-separated profile markdown paths (--mcp)")
    parser.add_argument("--project-path", type=Path, help="Project root receiving MCP config (--mcp)")
    parser.add_argument("--target", help="Harness target: claude|codex|gemini (--mcp)")
    parser.add_argument(
        "--install-mode",
        default="copy",
        choices=("copy", "symlink"),
        help="Installer mode; MCP config is always materialised as a real file",
    )
    return parser.parse_args()


def render_content(args: argparse.Namespace) -> str:
    if args.content:
        content = args.content.read_text(encoding="utf-8").strip()
        if args.sub_content:
            sub_paths = [Path(p.strip()) for p in args.sub_content.split(",") if p.strip()]
            for sub_path in sub_paths:
                if sub_path.is_file():
                    content += "\n\n---\n\n" + sub_path.read_text(encoding="utf-8").strip()
        return content

    if not args.core or not args.adapter:
        raise ValueError("Either --content or both --core and --adapter must be specified")

    core = args.core.read_text(encoding="utf-8").strip()
    adapter = args.adapter.read_text(encoding="utf-8")
    if adapter.count("{{CORE_RULES}}") != 1:
        raise ValueError(f"{args.adapter} must contain {{CORE_RULES}} exactly once")
    return adapter.replace("{{CORE_RULES}}", core).strip()


def merge(original: str, rendered: str, marker_prefix: str, replace: bool = False) -> str:
    start_marker = f"<!-- {marker_prefix}:start -->"
    end_marker = f"<!-- {marker_prefix}:end -->"
    managed = f"{start_marker}\n{rendered}\n{end_marker}"
    if replace:
        return managed + "\n"
    has_start = start_marker in original
    has_end = end_marker in original
    if has_start != has_end:
        raise ValueError(f"destination contains an incomplete {marker_prefix} block")
    if has_start:
        before, remainder = original.split(start_marker, 1)
        _, after = remainder.split(end_marker, 1)
        return f"{before.rstrip()}\n\n{managed}{after}".strip() + "\n"
    if not original.strip():
        return managed + "\n"
    return original.rstrip() + "\n\n" + managed + "\n"


def strip_marker_block(text: str, marker_prefix: str) -> str:
    """Remove every ``<!-- prefix:start -->`` .. ``<!-- prefix:end -->`` block.

    Raises ValueError on an incomplete block rather than guessing where it ends.
    """
    start_marker = f"<!-- {marker_prefix}:start -->"
    end_marker = f"<!-- {marker_prefix}:end -->"
    while start_marker in text or end_marker in text:
        before, sep, remainder = text.partition(start_marker)
        if not sep or end_marker not in remainder:
            raise ValueError(f"text contains an incomplete {marker_prefix} block")
        _, _, after = remainder.partition(end_marker)
        text = before + after
    return text


def _normalise(text: str) -> str:
    return " ".join(text.split())


def fold_legacy(agents_text: str, legacy_text: str, marker_prefix: str, source_name: str = "CLAUDE.md") -> str:
    """Return ``agents_text`` with the legacy file's operator text appended.

    Pure. The kit's own marker block in the legacy file is dropped (the kit
    regenerates it), the rest is split into blank-line separated paragraphs,
    and any paragraph whose whitespace-normalised text already occurs in
    ``agents_text`` is skipped. What remains goes under a
    ``## Migrated from <source_name>`` heading, outside the kit markers, so a
    later marker-scoped rewrite leaves it alone. Returns ``agents_text``
    unchanged when nothing is left, which is what makes the fold idempotent.
    """
    known = _normalise(agents_text)
    fresh: list[str] = []
    for paragraph in re.split(r"\n\s*\n", strip_marker_block(legacy_text, marker_prefix)):
        paragraph = paragraph.strip()
        normalised = _normalise(paragraph)
        if not normalised or normalised in known:
            continue
        fresh.append(paragraph)
        known += " " + normalised
    if not fresh:
        return agents_text
    section = f"## Migrated from {source_name}\n\n" + "\n\n".join(fresh) + "\n"
    if not agents_text.strip():
        return section
    return agents_text.rstrip() + "\n\n" + section


def collect_legacy(paths: list[Path], destination: Path) -> list[tuple[Path, str, str]]:
    """Return ``(path, name relative to destination's directory, text)`` for each usable file.

    A symlink is never migrated: it may point at the destination itself or at a
    shared file, and copying then deleting it would not preserve that link.
    """
    found: list[tuple[Path, str, str]] = []
    for path in (p.expanduser() for p in paths):
        if path.is_symlink():
            print(f"skipping symlink: {path}")
            continue
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"skipping legacy file that is not UTF-8: {path}")
            continue
        found.append((path, os.path.relpath(path, destination.parent), text))
    return found


def parse_profile_mcp(text: str) -> dict:
    """Parse the fenced ```toml block(s) of a profile into an MCP profile dict.

    Pure: takes profile markdown, returns ``{"mcp": {...}, "mcp_tools": [...]}``.
    A profile without a toml block yields empty sections.
    """
    servers: dict[str, dict] = {}
    tools: list[str] = []
    for block in TOML_BLOCK_RE.findall(text):
        try:
            data = tomllib.loads(block)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"malformed toml block: {exc}") from exc

        declared = data.get("mcp", {})
        if not isinstance(declared, dict):
            raise ValueError("[mcp] must be a table of server declarations")
        for name, spec in declared.items():
            if not isinstance(spec, dict):
                raise ValueError(f"[mcp.{name}] must be a table")
            if "mcp_tools" in spec:
                raise ValueError(
                    f"[mcp.{name}] contains mcp_tools; declare mcp_tools above the [mcp.*] tables "
                    "so toml parses it as a top-level key"
                )
            servers[name] = spec

        declared_tools = data.get("mcp_tools", [])
        if not isinstance(declared_tools, list) or not all(isinstance(t, str) for t in declared_tools):
            raise ValueError("mcp_tools must be a list of strings")
        tools.extend(declared_tools)

    return {"mcp": servers, "mcp_tools": tools}


def load_mcp_profile(paths: list[Path]) -> dict:
    """Read profile files and merge their MCP declarations into one profile."""
    profile: dict = {"mcp": {}, "mcp_tools": []}
    for path in paths:
        try:
            part = parse_profile_mcp(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise ValueError(f"{path}: {exc}") from exc
        profile["mcp"].update(part["mcp"])
        profile["mcp_tools"].extend(part["mcp_tools"])
    return profile


def render_mcp_config(profile: dict, target: str) -> dict:
    """Return the harness-native MCP mapping for one target.

    Pure: no filesystem access. Claude renders ``{"mcpServers": {...}}``, which
    the installer writes to ``<project>/.mcp.json``. Unverified targets return
    an explicit ``{"unsupported": <target>}`` marker instead of a guess.
    """
    if target not in MCP_SUPPORTED_TARGETS:
        return {"unsupported": target}
    servers = profile.get("mcp") or {}
    return {"mcpServers": {name: copy.deepcopy(servers[name]) for name in sorted(servers)}}


def render_tool_allowlist(profile: dict, target: str) -> list[str]:
    """Return permission entries, e.g. ``["mcp__postgres__query", ...]``.

    Pure: no filesystem access. Order is preserved and duplicates are dropped.
    """
    if target not in MCP_SUPPORTED_TARGETS:
        return []
    allowlist: list[str] = []
    for tool in profile.get("mcp_tools") or []:
        if tool not in allowlist:
            allowlist.append(tool)
    return allowlist


def unsupported_target(rendered: dict) -> str | None:
    """Return the target name when ``render_mcp_config`` refused to render."""
    return rendered.get("unsupported")


def merge_mcp_config(original: dict, rendered: dict) -> dict:
    """Merge rendered servers into an existing .mcp.json document."""
    merged = copy.deepcopy(original) if original else {}
    servers = merged.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError("existing mcpServers is not an object")
    servers.update(copy.deepcopy(rendered.get("mcpServers", {})))
    merged["mcpServers"] = servers
    return merged


def merge_tool_allowlist(settings: dict, entries: list[str]) -> dict:
    """Merge allowlist entries into permissions.allow without clobbering it."""
    merged = copy.deepcopy(settings) if settings else {}
    permissions = merged.get("permissions", {})
    if not isinstance(permissions, dict):
        raise ValueError("existing permissions is not an object")
    allow = permissions.get("allow", [])
    if not isinstance(allow, list):
        raise ValueError("existing permissions.allow is not an array")
    for entry in entries:
        if entry not in allow:
            allow.append(entry)
    permissions["allow"] = allow
    merged["permissions"] = permissions
    return merged


def append_receipt(receipt_file: Path | None, action: dict) -> None:
    if not receipt_file:
        return
    receipt_file = receipt_file.expanduser()
    receipt_file.parent.mkdir(parents=True, exist_ok=True)
    if receipt_file.is_file():
        data = json.loads(receipt_file.read_text(encoding="utf-8"))
    else:
        data = {"actions": []}
    data.setdefault("actions", []).append(action)
    receipt_file.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_json_document(destination: Path, updated: dict, kind: str, args: argparse.Namespace) -> int:
    """Write a merged JSON document, backing up and recording it for rollback."""
    existed = destination.is_file()
    original_text = destination.read_text(encoding="utf-8") if existed else ""
    updated_text = json.dumps(updated, indent=2) + "\n"

    if existed and json.loads(original_text or "{}") == updated:
        print(f"{kind} unchanged: {destination}")
        return 0

    if args.dry_run:
        print(f"would write {kind}: {destination}")
        return 0

    backup_path: Path | None = None
    if existed:
        backup_path = args.backup_dir.expanduser() / args.label / destination.name
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, backup_path)
        print(f"backed up {kind}: {destination} -> {backup_path}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(updated_text, encoding="utf-8")
    print(f"wrote {kind}: {destination}")

    append_receipt(
        args.receipt_file,
        {
            "type": "file",
            "destination": str(destination.resolve()),
            "existed": existed,
            "backup_path": str(backup_path.resolve()) if backup_path else None,
        },
    )
    return 0


def read_json_document(path: Path, kind: str) -> dict:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"existing {kind} is not valid JSON: {path} ({exc})") from exc


def run_mcp(args: argparse.Namespace) -> int:
    if not args.profile or not args.project_path or not args.target:
        raise ValueError("--mcp requires --profile, --project-path and --target")

    profile = load_mcp_profile([Path(p.strip()) for p in args.profile.split(",") if p.strip()])
    project = args.project_path.expanduser().resolve()

    rendered = render_mcp_config(profile, args.target)
    refused = unsupported_target(rendered)
    if refused:
        print(f"mcp unsupported target: {refused} (no config written; see Phase 3)")
        return 0

    servers = rendered["mcpServers"]
    allowlist = render_tool_allowlist(profile, args.target)
    if not servers and not allowlist:
        print(f"mcp: no servers or tools declared for {project}")
        return 0

    if args.install_mode == "symlink":
        print("mcp: rendered config is always a real file (--mode symlink does not apply)")

    if servers:
        mcp_path = project / ".mcp.json"
        merged = merge_mcp_config(read_json_document(mcp_path, "mcp config"), rendered)
        write_json_document(mcp_path, merged, "mcp config", args)

    if allowlist:
        settings_path = project / ".claude" / "settings.json"
        merged_settings = merge_tool_allowlist(
            read_json_document(settings_path, "permission config"), allowlist
        )
        write_json_document(settings_path, merged_settings, "permission config", args)

    return 0


def render_hooks(profile_path: Path, hooks_dir: Path) -> dict:
    """Load the profile hook block and point every command at the deployed scripts."""
    text = profile_path.expanduser().read_text(encoding="utf-8")
    text = text.replace("{{HOOKS_DIR}}", str(hooks_dir.expanduser().resolve()))
    document = json.loads(text)
    hooks = document.get("hooks")
    if not isinstance(hooks, dict):
        raise ValueError(f"{profile_path}: expected a top-level 'hooks' object")
    return hooks


def _entry_is_kit_owned(entry: dict, hooks_dir: Path, kit_basenames: set[str]) -> bool:
    """True when every command in this entry is one of the kit's own hook scripts.

    Kit entries carry no marker of their own — the schema has nowhere to put one
    — so ownership is inferred from the command. Two signals, either sufficient:
    the command resolves inside the *current* run's hooks_dir (the common
    case; `is_relative_to`, not a string prefix — a sibling like
    `hooks-legacy/foo.sh` starts with the string "hooks_dir" but is not inside
    it), or its basename matches one the kit currently ships (catches entries
    written under a *previous* AGENT_HARNESS_HOME — hooks_dir is derived from
    that value, so it changes if the operator's home does, and the
    is-relative-to check alone would then misclassify the old entries as the
    operator's own and let them accumulate as undead duplicates instead of
    being replaced).

    A false positive here (an operator's own script that happens to share a
    kit script's exact basename) is possible but narrow; the alternative —
    stale kit entries silently piling up forever — is the wider failure mode.
    """
    commands = [h.get("command", "") for h in entry.get("hooks", []) if isinstance(h, dict)]
    if not commands:
        return False
    owned = []
    for c in commands:
        try:
            in_current_dir = Path(c).resolve().is_relative_to(hooks_dir)
        except (OSError, ValueError):
            in_current_dir = False
        owned.append(in_current_dir or Path(c).name in kit_basenames)
    return all(owned)


def merge_hooks(settings: dict, rendered: dict, hooks_dir: Path) -> dict:
    """Merge kit hook entries into existing settings, preserving operator entries.

    Kit-owned entries are dropped and re-added rather than appended to, so a
    reinstall cannot duplicate them and a hook removed from the kit disappears
    on the next install.
    """
    merged = copy.deepcopy(settings) if settings else {}
    existing = merged.get("hooks", {})
    if not isinstance(existing, dict):
        raise ValueError("existing hooks is not an object")
    resolved_hooks_dir = hooks_dir.expanduser().resolve()
    kit_basenames = {
        Path(h.get("command", "")).name
        for entries in rendered.values()
        for e in entries
        for h in e.get("hooks", [])
        if isinstance(h, dict) and h.get("command")
    }

    for event, entries in rendered.items():
        current = existing.get(event, [])
        if not isinstance(current, list):
            raise ValueError(f"existing hooks.{event} is not an array")
        kept = [
            e for e in current
            if not (isinstance(e, dict) and _entry_is_kit_owned(e, resolved_hooks_dir, kit_basenames))
        ]
        existing[event] = kept + copy.deepcopy(entries)

    merged["hooks"] = existing
    return merged


def run_hooks(args: argparse.Namespace) -> int:
    if not args.hooks_profile or not args.hooks_dir or not args.destination:
        raise ValueError("--hooks requires --hooks-profile, --hooks-dir and --destination")
    destination = args.destination.expanduser()
    original = json.loads(destination.read_text(encoding="utf-8")) if destination.is_file() else {}
    rendered = render_hooks(args.hooks_profile, args.hooks_dir)
    updated = merge_hooks(original, rendered, args.hooks_dir)
    return write_json_document(destination, updated, "hook config", args)


def main() -> int:
    args = parse_args()
    if args.hooks:
        return run_hooks(args)
    if args.mcp:
        return run_mcp(args)
    if not args.destination:
        raise ValueError("--destination is required")
    destination = args.destination.expanduser()
    dest_existed = destination.exists()
    original = destination.read_text(encoding="utf-8") if dest_existed else ""
    rendered = render_content(args)
    updated = merge(original, rendered, marker_prefix=args.marker, replace=args.replace)

    migrating: list[tuple[Path, str, str]] = []
    for path, name, text in collect_legacy(args.migrate_legacy, destination):
        try:
            updated = fold_legacy(updated, text, args.marker, name)
        except ValueError as exc:
            print(f"leaving {path} in place: {exc}")
            continue
        migrating.append((path, name, text))

    rules_changed = updated != original
    if not rules_changed and not migrating:
        print(f"rules unchanged: {destination}")
        return 0

    if args.dry_run:
        if rules_changed:
            print(f"would update rules: {destination}")
        for path, _, _ in migrating:
            print(f"would migrate legacy rules: {path} -> {destination} (backed up, then removed)")
        return 0

    backup_path: Path | None = None
    if rules_changed and dest_existed:
        backup_path = args.backup_dir.expanduser() / args.label / destination.name
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, backup_path)
        print(f"backed up rules: {destination} -> {backup_path}")

    legacy_backups: list[Path] = []
    for path, name, _ in migrating:
        legacy_backup = args.backup_dir.expanduser() / args.label / "legacy" / name.replace(os.sep, "__")
        legacy_backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, legacy_backup)
        legacy_backups.append(legacy_backup)
        print(f"backed up legacy rules: {path} -> {legacy_backup}")

    if rules_changed:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(updated, encoding="utf-8")
        print(f"updated rules: {destination}")
        append_receipt(
            args.receipt_file,
            {
                "type": "rule",
                "destination": str(destination.resolve()),
                "existed": dest_existed,
                "backup_path": str(backup_path.resolve()) if backup_path else None,
            },
        )

    # Nothing is removed until the destination has been re-read and shown to
    # already contain everything the legacy files held: folding again must be a
    # no-op. Any failure above or here leaves every legacy file where it was.
    written = destination.read_text(encoding="utf-8")
    for path, name, text in migrating:
        if fold_legacy(written, text, args.marker, name) != written:
            raise RuntimeError(f"{destination} does not contain everything from {path}; leaving it in place")

    for (path, _, _), legacy_backup in zip(migrating, legacy_backups):
        resolved = str(path.resolve())
        path.unlink()
        print(f"migrated legacy rules: {path} -> {destination}")
        append_receipt(
            args.receipt_file,
            {
                "type": "file",
                "destination": resolved,
                "existed": True,
                "backup_path": str(legacy_backup.resolve()),
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
