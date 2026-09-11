#!/usr/bin/env python3
"""Sync project-scoped MCP configurations across Claude Code and Antigravity."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync project-scoped MCP configs.")
    parser.add_argument("--source", type=Path, required=True, help="Base MCP json profile")
    parser.add_argument(
        "--target-format",
        required=True,
        choices=["claude", "antigravity", "gemini"],
        help="Target platform format",
    )
    parser.add_argument("--destination", type=Path, required=True, help="Destination json file")
    parser.add_argument("--backup-dir", type=Path, required=True, help="Backup directory")
    parser.add_argument("--label", required=True, help="Backup label")
    parser.add_argument("--receipt-file", type=Path, help="Receipt JSON file to append action")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying")
    return parser.parse_args()


def convert_server(cfg: dict, target_format: str) -> dict:
    server = dict(cfg)
    is_http = (
        server.get("type") == "http"
        or "serverUrl" in server
        or "url" in server
    )
    if is_http:
        url = server.get("url") or server.get("serverUrl")
        if target_format == "claude":
            out = {"type": "http", "url": url}
            for k, v in server.items():
                if k not in ("type", "url", "serverUrl"):
                    out[k] = v
            return out
        else:  # antigravity / gemini
            out = {"serverUrl": url}
            for k, v in server.items():
                if k not in ("type", "url", "serverUrl"):
                    out[k] = v
            return out
    else:  # stdio
        out = {}
        if "command" in server:
            out["command"] = server["command"]
        if "args" in server:
            out["args"] = server["args"]
        for k, v in server.items():
            if k not in ("command", "args"):
                out[k] = v
        return out


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


def main() -> int:
    args = parse_args()
    source_path = args.source.expanduser()
    if not source_path.is_file():
        print(f"Error: source profile not found: {source_path}", file=sys.stderr)
        return 1

    source_data = json.loads(source_path.read_text(encoding="utf-8"))
    source_servers = source_data.get("mcpServers", source_data)

    target_fmt = "antigravity" if args.target_format in ("antigravity", "gemini") else "claude"

    converted_servers = {}
    for name, cfg in source_servers.items():
        converted_servers[name] = convert_server(cfg, target_fmt)

    destination = args.destination.expanduser()
    dest_existed = destination.is_file()

    if dest_existed:
        try:
            dest_data = json.loads(destination.read_text(encoding="utf-8"))
            if not isinstance(dest_data, dict):
                dest_data = {}
        except Exception:
            dest_data = {}
    else:
        dest_data = {}

    if "mcpServers" not in dest_data or not isinstance(dest_data["mcpServers"], dict):
        dest_data["mcpServers"] = {}
    dest_data["mcpServers"].update(converted_servers)

    rendered = json.dumps(dest_data, indent=2) + "\n"

    if dest_existed:
        original = destination.read_text(encoding="utf-8")
        try:
            orig_json = json.loads(original)
            if orig_json == dest_data:
                print(f"mcp unchanged: {destination}")
                return 0
        except Exception:
            if original == rendered:
                print(f"mcp unchanged: {destination}")
                return 0

    if args.dry_run:
        action_str = "update" if dest_existed else "install"
        print(f"would {action_str} mcp: {destination}")
        return 0

    backup_path = None
    if dest_existed:
        backup_path = args.backup_dir.expanduser() / args.label / destination.name
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, backup_path)
        print(f"backed up mcp: {destination} -> {backup_path}")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf-8")
    action_str = "updated" if dest_existed else "installed"
    print(f"{action_str} mcp: {destination}")

    append_receipt(
        args.receipt_file,
        {
            "type": "mcp",
            "destination": str(destination.resolve()),
            "existed": dest_existed,
            "backup_path": str(backup_path.resolve()) if backup_path else None,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
