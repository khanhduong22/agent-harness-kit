#!/usr/bin/env python3
"""Controller-owned file snapshots for bounded agent effects."""

import hashlib
import json
import os
from pathlib import Path


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def snapshot(root, excluded=()):
    """Return a deterministic path/type/hash snapshot without following symlinks."""
    root = Path(root).resolve()
    excluded = {Path(item).as_posix().rstrip("/") for item in excluded}
    rows = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        relbase = Path(base).relative_to(root)
        dirs[:] = sorted(d for d in dirs if (relbase / d).as_posix() not in excluded
                          and d not in {".git", "__pycache__"})
        for name in list(dirs):
            path, rel = Path(base) / name, (relbase / name).as_posix()
            if path.is_symlink():
                rows[rel] = {"type": "symlink", "target": os.readlink(path)}
                dirs.remove(name)
        for name in sorted(files):
            path, rel = Path(base) / name, (relbase / name).as_posix()
            if rel in excluded:
                continue
            if path.is_symlink():
                rows[rel] = {"type": "symlink", "target": os.readlink(path)}
            elif path.is_file():
                rows[rel] = {"type": "file", "sha256": _sha(path)}
    return rows


def digest(rows):
    """Return the SHA-256 of one canonical snapshot."""
    raw = json.dumps(rows, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()


def changed(before, after):
    """Return every path whose object type, target, or bytes changed."""
    return sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))


def verify_effects(before, after, allowed, forbidden=()):
    """Return violations when changes escape allowed roots or touch forbidden paths."""
    allowed = tuple(Path(p).as_posix().rstrip("/") for p in allowed)
    forbidden = tuple(Path(p).as_posix().rstrip("/") for p in forbidden)
    violations = []
    for path in changed(before, after):
        if after.get(path, {}).get("type") == "symlink":
            violations.append(f"symlink-effect:{path}")
        elif any(path == item or path.startswith(item + "/") or item.startswith(path + "/")
               for item in forbidden):
            violations.append(f"forbidden:{path}")
        elif not any(path == item or path.startswith(item + "/") for item in allowed):
            violations.append(f"outside-writes:{path}")
    return sorted(violations)


def effect_digest(before, after):
    """Return a controller-derived digest binding both snapshots and their changed paths."""
    payload = {"before": digest(before), "after": digest(after), "changed": changed(before, after)}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()
