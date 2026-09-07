#!/usr/bin/env python3
"""Merge one rendered rule adapter into a managed block."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

START = "<!-- agent-harness-kit:start -->"
END = "<!-- agent-harness-kit:end -->"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--backup-dir", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def render(core_path: Path, adapter_path: Path) -> str:
    core = core_path.read_text(encoding="utf-8").strip()
    adapter = adapter_path.read_text(encoding="utf-8")
    if adapter.count("{{CORE_RULES}}") != 1:
        raise ValueError(f"{adapter_path} must contain {{CORE_RULES}} exactly once")
    return adapter.replace("{{CORE_RULES}}", core).strip()


def merge(original: str, rendered: str, replace: bool = False) -> str:
    managed = f"{START}\n{rendered}\n{END}"
    if replace:
        return managed + "\n"
    has_start = START in original
    has_end = END in original
    if has_start != has_end:
        raise ValueError("destination contains an incomplete agent-harness-kit block")
    if has_start:
        before, remainder = original.split(START, 1)
        _, after = remainder.split(END, 1)
        return f"{before.rstrip()}\n\n{managed}{after}".strip() + "\n"
    if not original.strip():
        return managed + "\n"
    return original.rstrip() + "\n\n" + managed + "\n"


def main() -> int:
    args = parse_args()
    destination = args.destination.expanduser()
    original = destination.read_text(encoding="utf-8") if destination.exists() else ""
    updated = merge(original, render(args.core, args.adapter), replace=args.replace)
    if updated == original:
        print(f"rules unchanged: {destination}")
        return 0
    if args.dry_run:
        print(f"would update rules: {destination}")
        return 0
    if destination.exists():
        backup = args.backup_dir.expanduser() / args.label / destination.name
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(destination, backup)
        print(f"backed up rules: {destination} -> {backup}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(updated, encoding="utf-8")
    print(f"updated rules: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
