#!/usr/bin/env python3
"""Execute rollback of an agent-harness-kit installation using receipt.json."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rollback agent-harness-kit installation.")
    parser.add_argument(
        "--backup-root",
        type=Path,
        required=True,
        help="Root directory of backups (e.g., ~/.agent-harness-backups)",
    )
    parser.add_argument(
        "--target",
        default="latest",
        help="Backup timestamp to roll back, or 'latest'",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview rollback actions without applying changes",
    )
    return parser.parse_args()


def resolve_receipt(backup_root: Path, target: str) -> tuple[Path, dict]:
    backup_root = backup_root.expanduser()
    if not backup_root.is_dir():
        raise FileNotFoundError(f"Backup root directory does not exist: {backup_root}")

    target_dir: Path
    if target == "latest":
        # Check if 'latest' symlink exists
        latest_link = backup_root / "latest"
        if latest_link.is_symlink() or latest_link.is_dir():
            target_dir = latest_link.resolve()
        else:
            # Pick highest timestamp dir
            subdirs = sorted(
                [p for p in backup_root.iterdir() if p.is_dir() and p.name != "latest"],
                key=lambda p: p.name,
            )
            if not subdirs:
                raise FileNotFoundError(f"No backup runs found in {backup_root}")
            target_dir = subdirs[-1]
    else:
        target_dir = backup_root / target
        if not target_dir.is_dir():
            raise FileNotFoundError(f"Backup directory not found: {target_dir}")

    receipt_path = target_dir / "receipt.json"
    if not receipt_path.is_file():
        raise FileNotFoundError(f"receipt.json not found in {target_dir}")

    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    return receipt_path, data


def rollback_action(action: dict, dry_run: bool) -> str:
    action_type = action.get("type")
    dest_path = Path(action["destination"]).expanduser()
    backup_path = Path(action["backup_path"]).expanduser() if action.get("backup_path") else None
    existed = action.get("existed", False)

    if action_type == "symlink":
        if not dest_path.is_symlink() and not dest_path.exists():
            return f"skipped (not present): {dest_path}"
        if backup_path and backup_path.exists():
            if dry_run:
                return f"would restore backup to symlink location: {backup_path} -> {dest_path}"
            dest_path.unlink()
            if backup_path.is_dir():
                shutil.copytree(backup_path, dest_path)
            else:
                shutil.copy2(backup_path, dest_path)
            return f"restored backup: {dest_path}"
        else:
            if dry_run:
                return f"would remove created symlink: {dest_path}"
            dest_path.unlink()
            return f"removed symlink: {dest_path}"

    elif action_type in ("rule", "file"):
        if backup_path and backup_path.exists():
            if dry_run:
                return f"would restore file from backup: {backup_path} -> {dest_path}"
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, dest_path)
            return f"restored file: {dest_path}"
        elif not existed:
            if not dest_path.exists():
                return f"skipped (not present): {dest_path}"
            if dry_run:
                return f"would remove created file: {dest_path}"
            dest_path.unlink()
            return f"removed created file: {dest_path}"
        else:
            return f"skipped: no backup to restore for {dest_path}"

    return f"unknown action type: {action_type}"


def main() -> int:
    args = parse_args()
    try:
        receipt_path, receipt = resolve_receipt(args.backup_root, args.target)
    except FileNotFoundError as err:
        print(f"Rollback error: {err}", file=sys.stderr)
        return 1

    actions = receipt.get("actions", [])
    if not actions:
        print(f"No actions found in receipt: {receipt_path}")
        return 0

    print(f"Rolling back run from: {receipt.get('timestamp', 'unknown')} ({receipt_path.parent.name})")
    # Rollback in reverse order
    for action in reversed(actions):
        msg = rollback_action(action, args.dry_run)
        print(f"  {msg}")

    if not args.dry_run:
        # Mark receipt as rolled back
        receipt["rolled_back"] = True
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print("Rollback completed successfully.")
    else:
        print("Dry run completed. No files modified.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
