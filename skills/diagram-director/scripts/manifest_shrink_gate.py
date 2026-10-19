#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage A tripwire: a manifest may not shrink its way out of a failing gate.

The manifest is SELF-DECLARATION, and every render-side gate is keyed off it: a declared
feature that renders empty is a hard FAIL, an undeclared one prints N-A. So the cheapest
way to turn a red runner green is to delete the declaration -- drop `captions` from
`features`, or drop the hold whose text floor fails -- and the cut still has the defect
with a clean stage table over it. Deleting a declaration is not a repair.

This compares the manifest on disk with the one committed at HEAD and refuses a SHRINKING
set of DECLARATIONS -- `features`, `holds[].id`, the node each anchor hold is held on
(`holds[].anchor`) and the act numbers in `acts[]` -- unless the cut's sheet carries a dated
`AMENDMENT` heading whose section NAMES every removed item on a line that says it went
(`removed`, `dropped`, `retired`, `no longer`). Naming it anywhere in the section is not
enough: these sheets already carry amendments about other things, and a word like
`captions` or a hold id turns up in that prose, so a bare substring test would wave
through the exact deletion this gate exists to catch. Growth is free; renaming is a removal
plus an addition, so it needs the amendment too, which is the point -- an id is what the
gates and the contact sheet address a hold by.

Absence of history is not a skipped check. An untracked manifest (a scratch copy, a fresh
cut, a worktree with no git) has nothing to compare against, so stage A prints `N-A` with
that reason: never a pass by accident, and never UNVERIFIED -- UNVERIFIED means a check
that COULD have run did not, and this one ran and found no predecessor.
"""

import datetime
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import manifest_predecessor                                          # noqa: E402
from verify_all_report import bad, na, ok                            # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
STAGE, LABEL = "A manifest", "shrink"
# `## AMENDMENT 2026-08-30 -- ...`: a heading, the word, and an ISO date on the same line.
AMENDMENT_HEADING = re.compile(r"^\s{0,3}#{1,6}\s*AMENDMENT\b[^\n]*?(\d{4}-\d{2}-\d{2})",
                               re.MULTILINE)
# The removed item must be named on a line that SAYS it was removed. Naming it anywhere
# inside an amendment section is not enough: every sheet here already carries amendments
# about other things, and words like `captions` or a hold id appear in them as ordinary
# prose -- so a bare substring test passes the exact deletion it exists to catch.
REMOVAL_WORDS = ("remov", "delet", "drop", "retir", "no longer", "withdraw")


def previous(path):
    """The manifest as committed at HEAD, or None when there is no history for it.

    The lookup follows renames (see `manifest_predecessor`): a golden that MOVED still has
    a predecessor, and reporting none for it would hand back the fix-by-deletion hole.
    Untracked, no git, or detached with no HEAD all stay "no predecessor".
    """
    blob = manifest_predecessor.blob_at_head(path, REPO_ROOT)
    if blob is None:
        return None
    try:
        return json.loads(blob)
    except ValueError:
        return None


def declared(manifest):
    """Every declaration a cut cannot quietly shrink, as one set of nameable items.

    Features and hold ids were the original two. Anchors and act numbers joined them
    because both are gate KEYS: `acts/anchor-not-shared` only ever runs on a hold that
    carries `anchor`, and every act gate iterates `acts[]` -- so deleting the field is the
    same fix-by-deletion the features list was closed against. The anchor is tracked by the
    NODE it names, which is how an amendment would write it ("the postgres anchor was
    dropped"), and an act by its number.
    """
    holds = manifest.get("holds") or []
    return (set(manifest.get("features") or [])
            | {h["id"] for h in holds if h.get("id")}
            | {str(h["anchor"]) for h in holds if h.get("anchor")}
            | {f"act {e['act']}" for e in (manifest.get("acts") or [])
               if e.get("act") is not None})


def sheet_for(manifest_path):
    """`<cut>.sheet.md` beside the manifest -- the house convention (examples/)."""
    path = Path(manifest_path)
    return path.with_name(path.name.replace(".manifest.json", ".sheet.md"))


def amendments(sheet_path):
    """[(iso date, section text), ...] for every dated AMENDMENT heading in the sheet.

    The date must PARSE: `## AMENDMENT 9999-99-99` looks dated to a regex and is not a
    date, and an amendment nobody can place in time cannot be audited later."""
    try:
        text = Path(sheet_path).read_text(encoding="utf-8")
    except OSError:
        return []
    found = []
    matches = list(AMENDMENT_HEADING.finditer(text))
    for i, match in enumerate(matches):
        try:
            datetime.date.fromisoformat(match.group(1))
        except ValueError:
            continue
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        found.append((match.group(1), text[match.start():end]))
    return found


def _names_removal(section, item):
    """Does this amendment section say, on one line, that `item` went?

    WHOLE WORD, always: a substring test lets an amendment about hold `a10` excuse the
    deletion of `a1`, which is the neighbouring-id version of the very exploit this gate
    exists to close."""
    word = re.compile(rf"\b{re.escape(item.lower())}\b")
    for line in section.splitlines():
        low = line.lower()
        if word.search(low) and any(token in low for token in REMOVAL_WORDS):
            return True
    return False


def unreadable(manifest_path):
    """The reason this manifest cannot be parsed, or None. An unreadable manifest is stage
    A `validate`'s failure to report -- calling it a shrink would name the wrong defect."""
    try:
        json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return str(exc)
    return None


def check(manifest_path, sheet_path=None):
    """[] when the manifest did not shrink, [(code, evidence)] when it shrank unamended, or
    None when there is nothing to compare (no committed predecessor, or an unreadable file
    -- both mean "this gate has no verdict", never "it passed")."""
    if unreadable(manifest_path):
        return None
    prev = previous(manifest_path)
    if prev is None:
        return None
    try:
        now = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None
    removed = sorted(declared(prev) - declared(now))
    if not removed:
        return []
    sheet = Path(sheet_path or sheet_for(manifest_path))
    found = amendments(sheet)
    unnamed = [item for item in removed
               if not any(_names_removal(section, item) for _date, section in found)]
    if found and not unnamed:
        return []
    return [("manifest/shrink-unamended",
             {"removed": removed, "unnamed": unnamed,
              "sheet": sheet.name,
              "amendments_found": [date for date, _section in found]})]


def stage_result(manifest_path, sheet_path=None):
    """The stage-A row. One list so `stage_a()` can concatenate it in one expression."""
    sheet = Path(sheet_path or sheet_for(manifest_path))
    where = f"sheet {sheet.name}" if sheet.exists() else "no sheet beside the manifest"
    problem = unreadable(manifest_path)
    if problem:
        return [na(STAGE, LABEL, f"manifest is unreadable ({problem}) -- stage A `validate` "
                                 f"owns that failure; there is nothing to compare")]
    verdict = check(manifest_path, sheet_path)
    if verdict is None:
        return [na(STAGE, LABEL, "no committed predecessor at HEAD -- nothing to compare "
                                 "(untracked manifest, fresh cut, or no git history)")]
    if not verdict:
        return [ok(STAGE, LABEL, f"features, hold ids, anchors and act numbers did not "
                             f"shrink vs HEAD ({where})")]
    code, evidence = verdict[0]
    return [bad(STAGE, LABEL,
                f"{len(evidence.get('removed', []))} declaration(s) removed vs HEAD "
                f"{evidence.get('removed')} with no dated AMENDMENT in {sheet.name} naming "
                f"{evidence.get('unnamed') or 'them'} -- deleting a declaration is not a repair",
                code=code, evidence=evidence,
                fixes=[f"Restore {evidence.get('removed')} in {Path(manifest_path).name}, or "
                       f"add a dated `## AMENDMENT <YYYY-MM-DD>` section to {sheet.name} that "
                       f"names {evidence.get('unnamed') or evidence.get('removed')} verbatim "
                       f"and says why the cut no longer claims it"])]
