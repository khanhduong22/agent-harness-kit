#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Result record and stage table for diagram-director/scripts/verify_all.py.

Four statuses, and the distinction between the last two is the whole point of the
manifest (references/output-manifest.md):

  PASS        the check ran and the cut is clean
  FAIL        the check ran and found a violation -- including a DECLARED feature
              that renders empty, which is a lost layer, not an absence
  N-A         the manifest never declared this feature, so there is nothing to check
  UNVERIFIED  the check could not run (no puppeteer). NOT a pass; the delivery
              message must name it (diagram-director/scripts/browser-checks/README.md).
"""

from collections import namedtuple

PASS, FAIL, NA, UNVERIFIED = "PASS", "FAIL", "N-A", "UNVERIFIED"
_RANK = {PASS: 0, NA: 0, UNVERIFIED: 1, FAIL: 2}

# The last four fields are the MACHINE half (diagram-director/scripts/verify_all_json.py): a stable
# `code`, the `subject` the defect is about, measured `evidence`, and `fixes` that were
# proven by re-solving. They all default, so every existing construction site keeps
# working -- and `render()` reads the first four by name, so the human stage table cannot
# change shape when a check starts carrying evidence.
Result = namedtuple("Result", "stage name status reason code subject evidence fixes")
Result.__new__.__defaults__ = (None, None, None, ())


def ok(stage, name, reason="", **extra):
    return Result(stage, name, PASS, reason, **extra)


def bad(stage, name, reason, **extra):
    return Result(stage, name, FAIL, reason, **extra)


def na(stage, name, reason, **extra):
    return Result(stage, name, NA, reason, **extra)


def unverified(stage, name, reason, **extra):
    return Result(stage, name, UNVERIFIED, reason, **extra)


def worst(results):
    """FAIL beats UNVERIFIED beats PASS/N-A -- what the exit code is derived from."""
    status = PASS
    for res in results:
        if _RANK[res.status] > _RANK[status]:
            status = res.status
    return status


def render(results, title=""):
    """The stage table. One line per check: stage, name, status, one-line reason."""
    if not results:
        return "(no checks ran)"
    w_stage = max(len(r.stage) for r in results)
    w_name = max(len(r.name) for r in results)
    lines = []
    if title:
        lines += [title, "=" * len(title)]
    for res in results:
        reason = " ".join((res.reason or "").split())
        lines.append(f"{res.stage:<{w_stage}}  {res.name:<{w_name}}  "
                     f"{res.status:<10}  {reason}")
    counts = {}
    for res in results:
        counts[res.status] = counts.get(res.status, 0) + 1
    lines.append("")
    lines.append("  ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    return "\n".join(lines)
