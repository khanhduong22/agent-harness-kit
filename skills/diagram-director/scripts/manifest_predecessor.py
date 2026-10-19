#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The committed predecessor of one working-tree file, following renames.

Split out of `manifest_shrink_gate.py` so the gate stays under the module budget, and
because the lookup is the part with the subtle failure mode: `git show HEAD:<path>` names
the path as it is TODAY, so the moment a tracked file is moved -- the 2026-09-03 repo
restructure moved every golden under `diagram-director/` -- HEAD stops having that path and
every comparison silently degrades to "no predecessor". A gate that reports N-A because it
was looking in the wrong place is the fix-by-deletion hole it exists to close, reopened.

So when the current path is absent from HEAD we ask git, not ourselves, where the file used
to live: rename detection over the INDEX (`git diff --cached -M HEAD`) sees a move that has
been staged but not yet committed, which is exactly the window a restructure opens. A file
git reports no rename for really has no predecessor, and the caller still prints N-A.

argv is a LIST and every path is repo-relative: no user string reaches a shell.
"""

import subprocess
from pathlib import Path

GIT_TIMEOUT = 10


def _git(repo_root, *args):
    """The completed process, or None when git is absent, slow, or this is no repository."""
    try:
        return subprocess.run(("git", *args), cwd=str(repo_root), capture_output=True,
                              text=True, timeout=GIT_TIMEOUT)
    except (OSError, subprocess.SubprocessError):
        return None


def repo_relative(path, repo_root):
    """The path as git names it, or None when it lies outside the repository."""
    try:
        return Path(path).resolve().relative_to(Path(repo_root).resolve()).as_posix()
    except ValueError:
        return None


def staged_rename_source(rel, repo_root):
    """Where `rel` lived at HEAD when its move is staged but not yet committed, else None."""
    proc = _git(repo_root, "diff", "--cached", "--name-status", "-M", "HEAD")
    if proc is None or proc.returncode:
        return None
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[0].startswith("R") and parts[2] == rel:
            return parts[1]
    return None


def blob_at_head(path, repo_root):
    """The bytes this file had at HEAD (following a staged rename), or None if it had none."""
    rel = repo_relative(path, repo_root)
    if rel is None:
        return None
    for candidate in (rel, staged_rename_source(rel, repo_root)):
        if candidate is None:
            continue
        proc = _git(repo_root, "show", f"HEAD:{candidate}")
        if proc is not None and not proc.returncode:
            return proc.stdout
    return None
