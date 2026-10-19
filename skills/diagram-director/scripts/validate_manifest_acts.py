#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`acts[]` and the two act-gate hold fields, validated for SHAPE (references/output-manifest.md).

Apart from diagram-director/scripts/validate_manifest.py so that file stays under the repo's 200-line rule,
and because this is one coherent contract: the act delta a cut declares, the `anchor` a
camera hold is held on, and the `lens` a spotlight beat announces.

Shape only. Whether the declared delta is TRUE is diagram-director/scripts/verify_act_delta.py's job -- that
needs the cut, and nothing in this file ever opens one.
"""

import re

CHANGE_KINDS = {"topology", "semantic", "scope", "moved"}
KEBAB = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def validate_acts(data, kinds, say):
    """`acts[]`, plus the two hold fields the act gates read (`anchor`, `lens`).

    `say` is the caller's one-line error sink, so every message reads exactly like the rest
    of the manifest report.
    """
    for i, hold in enumerate(data.get("holds") or []):
        anchor = hold.get("anchor")
        if anchor is not None and not (isinstance(anchor, str) and KEBAB.match(anchor)):
            say(f"holds[{i}].anchor {anchor!r} must be a kebab-case data-node-id")
        lens = hold.get("lens")
        if lens is None:
            continue
        if hold.get("kind") != "spotlight" or not (isinstance(lens, list) and len(lens) == 2):
            say(f"holds[{i}].lens {lens!r} must be two roles on a spotlight hold")

    acts = data.get("acts")
    if acts is None:
        return
    if not isinstance(acts, list):
        return say("`acts` must be a list of {act, window, delta} entries")
    act_holds = kinds.get("act", [])
    previous = 0
    for i, entry in enumerate(acts):
        number = entry.get("act")
        if not isinstance(number, int) or number <= previous:
            say(f"acts[{i}].act {number!r} must be an int, unique and ascending")
        else:
            previous = number
        window = entry.get("window")
        if not (isinstance(window, list) and len(window) == 2
                and all(isinstance(v, (int, float)) for v in window)):
            say(f"acts[{i}].window {window!r} must be [a, b] in master percent")
        elif len(act_holds) == len(acts):
            # The act's own hold is where the window came from; a second spelling of it
            # here is a place for the two to drift, so they are compared.
            first = (act_holds[i].get("windows") or [[None, None]])[0]
            if [float(v) for v in window] != [float(v) for v in first]:
                say(f"acts[{i}].window {window} is not act hold "
                    f"{act_holds[i].get('element')!r}'s first window {first}")
        delta = entry.get("delta")
        if not isinstance(delta, dict) or set(delta) != {"added", "removed", "changed"}:
            say(f"acts[{i}].delta must carry exactly added, removed and changed")
            continue
        ids = set()
        for key in ("added", "removed"):
            for node_id in delta.get(key) or []:
                ids.add(node_id)
                if not (isinstance(node_id, str) and KEBAB.match(node_id)):
                    say(f"acts[{i}].delta.{key}: {node_id!r} is not a kebab-case node id")
        for change in delta.get("changed") or []:
            ids.add((change or {}).get("id"))
            if not isinstance(change, dict) or change.get("what") not in CHANGE_KINDS:
                say(f"acts[{i}].delta.changed: {change!r} needs id + what "
                    f"{sorted(CHANGE_KINDS)}")
        for key in entry.get("captionAliases") or {}:
            if key not in ids:
                say(f"acts[{i}].captionAliases: {key!r} is not one of this act's delta ids")
        # Shape only, and OPTIONAL: which ids owe a farewell is derived from the DOM by
        # diagram-director/scripts/verify_retired_ghost.py (`ids(act N-1) - ids(act N)`). An id listed here
        # is an EXTRA ghost the cut promises to draw -- it can add to that set, never shrink it.
        for node_id in entry.get("ghostOf") or []:
            if not (isinstance(node_id, str) and KEBAB.match(node_id)):
                say(f"acts[{i}].ghostOf: {node_id!r} is not a kebab-case node id")
