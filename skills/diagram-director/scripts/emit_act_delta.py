#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sheet -> `acts[]` EMITTER: the ACT DELTA table becomes the manifest's act deltas.

The five-tier sheet already carries `## Phase 1 -- TIER BOUNDARIES`, and that table stays
exactly as it is: it is an ARGUMENT ("what broke", "what T(n+1) added") and no parser can
check an argument. Beside it the sheet carries the MACHINE TWIN, `## Phase 2 -- ACT DELTA`,
which says the same story in ids:

    ## Phase 2 -- ACT DELTA

    | act | window | added | removed | changed | ghost-of | caption-alias |
    (`ghost-of` is DOCUMENTATION: the farewell an act owes is derived from `removed`
     by diagram-director/scripts/verify_retired_ghost.py, so an empty cell waives nothing)
    |---|---|---|---|---|---|---|
    | 1 | 5,15 | users . app-monolith | -- | -- | -- | app-monolith=One box |
    | 4 | 41.6667,56.6667 | api-gateway | alb . app | redis:moved | -- | -- |

Separator between values is the middle dot the repo's prose tables already use; an em dash
means EMPTY. `changed` cells are `id:what`, `what` from archify's taxonomy narrowed to what
a gate can check: `topology` | `semantic` | `scope` | `moved`. `caption-alias` cells are
`id=surface form` -- the escape hatch for a caption that names a component in prose ("One
box", "gateway") rather than by its kebab-case id.

WHY AN EMITTER AND NOT A HAND-WRITTEN BLOCK. `acts[].delta` is checked against the id sets
the DOM really draws (diagram-director/scripts/verify_act_delta.py), so it is not decoration -- and the
round-trip `emit_timeline.py --acts-table <sheet> --format json` is what stops the manifest
drifting from the sheet that authorised it. The sheet is the source; this is the only path
from it to the manifest.

  python3 diagram-director/scripts/emit_act_delta.py diagram-director/examples/progressive-500k-5tier.sheet.md"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from emit_timeline import Refuse, parse_table                        # noqa: E402

COLUMNS = ("act", "window", "added", "removed", "changed", "ghost-of", "caption-alias")
REQUIRED = COLUMNS[:4]
# archify's change taxonomy, narrowed to the four a gate in this repo can check.
CHANGE_KINDS = ("topology", "semantic", "scope", "moved")
SEPARATOR = "·"                 # the sheet's own multi-value idiom
EMPTY = {"", "-", "—", "–", "--"}
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HEADING = re.compile(r"^\s{0,3}#{1,6}\s.*\bACT DELTA\b", re.IGNORECASE)


def table_lines(text, where):
    """The markdown table under the `ACT DELTA` heading, and nothing else.

    Stops at the next heading, so a sheet may carry prose after the table without the
    splitter trying to read it as a row. A heading that MENTIONS the table without carrying
    one -- an AMENDMENT block saying what it changed -- is passed over rather than treated
    as the table's start, so amendment prose can name the table it amends.
    """
    lines, taking, out = text.splitlines(), False, []
    for line in lines:
        if HEADING.match(line):
            taking, out = True, []
            continue
        if not taking:
            continue
        if line.lstrip().startswith("#"):
            if out:
                break
            taking = False          # that heading talked ABOUT the table; keep looking
            continue
        if line.strip().startswith("|"):
            out.append(line.rstrip())
        elif out:
            break                       # blank line or prose AFTER the table ends it
    if not out:
        raise Refuse(f"{where}: no `## ... ACT DELTA` table -- the emitter reads the "
                     f"sheet, it does not invent a delta")
    return out


def _values(cell, where, column):
    """A `·`-separated cell as a list; an em dash is empty, never the string '—'."""
    cell, out = (cell or "").strip(), []
    if cell in EMPTY:
        return out
    for part in cell.split(SEPARATOR):
        part = part.strip()
        if not part:
            raise Refuse(f"{where}: {column} has an empty value between separators")
        out.append(part)
    return out


def _ids(cell, where, column):
    ids = _values(cell, where, column)       # kebab-case is the id contract, not a style
    for node_id in ids:
        if not KEBAB.match(node_id):
            raise Refuse(f"{where}: {column} id {node_id!r} is not kebab-case -- a "
                         f"`data-node-id` is [a-z0-9] words joined by single hyphens")
    return ids


def _changed(cell, where):
    """`id:what` pairs. `what` is author-declared and only its VOCABULARY is checked."""
    out = []
    for token in _values(cell, where, "changed"):
        if ":" not in token:
            raise Refuse(f"{where}: changed entry {token!r} must be `id:what` with what "
                         f"one of {list(CHANGE_KINDS)}")
        node_id, _, what = token.partition(":")
        node_id, what = node_id.strip(), what.strip()
        if not KEBAB.match(node_id):
            raise Refuse(f"{where}: changed id {node_id!r} is not kebab-case")
        if what not in CHANGE_KINDS:
            raise Refuse(f"{where}: changed {node_id!r} declares what={what!r}, not one "
                         f"of {list(CHANGE_KINDS)}")
        out.append({"id": node_id, "what": what})
    return out


def _aliases(cell, where, delta_ids):
    """`id=surface form` pairs. A key that is not a delta id is a typo, not an alias."""
    out = {}
    for token in _values(cell, where, "caption-alias"):
        if "=" not in token:
            raise Refuse(f"{where}: caption-alias entry {token!r} must be `id=surface form`")
        node_id, _, surface = token.partition("=")
        node_id, surface = node_id.strip(), surface.strip()
        if not surface:
            raise Refuse(f"{where}: caption-alias {node_id!r} has no surface form")
        if node_id not in delta_ids:
            raise Refuse(f"{where}: caption-alias {node_id!r} is not one of this act's "
                         f"delta ids {sorted(delta_ids)}")
        out[node_id] = surface
    return out


def _window(cell, where):
    parts = [p.strip() for p in (cell or "").split(",")]   # master percent, as the sheet
    if len(parts) != 2:
        raise Refuse(f"{where}: window {cell!r} must be `START,END` in master percent")
    try:
        span = [float(parts[0]), float(parts[1])]
    except ValueError:
        raise Refuse(f"{where}: window {cell!r} is not two numbers") from None
    if not 0 <= span[0] < span[1] <= 100:
        raise Refuse(f"{where}: window {span} must be 0 <= start < end <= 100")
    return span


def parse(text, where="<sheet>"):
    """The `acts[]` fragment for one sheet. Refuses every gap; defaults nothing."""
    rows = parse_table(table_lines(text, where), where, COLUMNS, REQUIRED)
    acts, seen = [], []
    for row in rows:
        raw_act = (row.get("act") or "").strip()
        if not raw_act.isdigit():
            raise Refuse(f"{where}: act {raw_act!r} is not an integer")
        act = int(raw_act)
        at = f"{where}: act {act}"
        if seen and act <= seen[-1]:
            raise Refuse(f"{at}: acts must be unique and ascending (after {seen[-1]})")
        seen.append(act)
        added = _ids(row.get("added"), at, "added")
        removed = _ids(row.get("removed"), at, "removed")
        changed = _changed(row.get("changed"), at)
        entry = {"act": act, "window": _window(row.get("window"), at),
                 "delta": {"added": added, "removed": removed, "changed": changed}}
        ghosts = _ids(row.get("ghost-of"), at, "ghost-of")
        if ghosts:
            entry["ghostOf"] = ghosts
        aliases = _aliases(row.get("caption-alias"), at,
                           set(added) | set(removed) | {c["id"] for c in changed})
        if aliases:
            entry["captionAliases"] = aliases
        acts.append(entry)
    return {"acts": acts}


def fragment(path):
    """`{"acts": [...]}` read from a sheet file. What `emit_timeline --acts-table` merges."""
    sheet = Path(path)
    return parse(sheet.read_text(encoding="utf-8"), sheet.name)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("sheet", help="the cut's solution sheet")
    args = ap.parse_args(argv)
    try:
        frag = fragment(args.sheet)
    except (OSError, Refuse) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(frag, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
