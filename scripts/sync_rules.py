#!/usr/bin/env python3
"""Merge rendered rules or project profiles into managed blocks."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", type=Path, help="Core rules path")
    parser.add_argument("--adapter", type=Path, help="Adapter markdown path")
    parser.add_argument("--content", type=Path, help="Direct content markdown path")
    parser.add_argument("--sub-content", type=str, help="Comma-separated sub-content markdown paths")
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--backup-dir", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--marker", default="agent-harness-kit", help="Block marker prefix")
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--receipt-file", type=Path, help="Path to append action to receipt.json")
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
    destination = args.destination.expanduser()
    dest_existed = destination.exists()
    original = destination.read_text(encoding="utf-8") if dest_existed else ""
    rendered = render_content(args)
    updated = merge(original, rendered, marker_prefix=args.marker, replace=args.replace)

    if updated == original:
        print(f"rules unchanged: {destination}")
        return 0

    if args.dry_run:
        print(f"would update rules: {destination}")
        return 0

    backup_path: Path | None = None
    if dest_existed:
        backup_path = args.backup_dir.expanduser() / args.label / destination.name
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, backup_path)
        print(f"backed up rules: {destination} -> {backup_path}")

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
