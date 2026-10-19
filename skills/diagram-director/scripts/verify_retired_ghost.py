#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage B: an act that RETIRES a component owes it one visible farewell.

`references/camera-beat.md`: a retired component gets one outline ghost in the act that
drops it, and never appears again. The requirement is DERIVED from the DOM -- see
check_ghosts -- so it cannot be deleted, only met or failed.

  acts/retired-ghost-missing  a retired id with no `.is-ghost` group in that act; a ghost
                              whose shapes carry a fill; or a cut whose stylesheet has no
                              rule scoping `.is-ghost` with `fill:none`, which paints every
                              ghost in the file solid at once.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import act_dom_scan as scan                                          # noqa: E402
from verify_act_delta import FEATURE                                 # noqa: E402
from verify_all_report import na                                     # noqa: E402
from verify_tier_identity import STAGE, _defect, registry, row       # noqa: E402


def check_ghosts(html, manifest):
    """The `retired-ghost` row: every id an act RETIRED gets one outline farewell there.

    DERIVED, never volunteered. The required set for act N is `ids(act N-1) - ids(act N)`
    read off the DOM -- the same subtraction `acts/delta-mismatch` holds the manifest to --
    so deleting the sheet's `ghost-of` column together with the ghost group does not remove
    the requirement, it fails the row. `ghostOf` in the manifest is documentation ON TOP: an
    id declared there must also be drawn, and extra ghosts are free.

    A ghost must also BE an outline, which is two facts: no inline fill on its shapes, and a
    stylesheet rule scoping `.is-ghost` with `fill:none`. Deleting that one rule repaints
    every ghost solid while each group still reads innocently, so the rule is checked too.
    """
    box = (manifest.get("target") or {}).get("viewbox") or [0, 0, 1920, 1080]
    documented = {e.get("act"): list(e.get("ghostOf") or [])
                  for e in (manifest.get("acts") or [])}
    outline_rule = scan.ghost_outline_rule(html)
    defects, total, drawn_ghosts, previous = [], 0, 0, set()
    for entry in registry(html, box):
        act, ids = entry["act"], set(entry["nodes"])
        required = sorted((previous - ids) | set(documented.get(act) or []))
        previous = ids
        ghosts = {g["ghost_of"]: g for g in scan.read_ghosts(entry["body"])}
        drawn_ghosts += len(ghosts)
        for node_id in required:
            total += 1
            ghost = ghosts.get(node_id)
            if ghost is None:
                defects.append(_defect(
                    "acts/retired-ghost-missing",
                    f"act {act}: no .is-ghost group for {node_id}, which act {act} retired",
                    {"act": act, "node": node_id},
                    {"act": act, "id": node_id, "retired_in_act": act,
                     "derived_from": "ids(act N-1) - ids(act N)",
                     "ghosts_found": sorted(ghosts)},
                    f'Draw <g class="node-ghost is-ghost" data-ghost-of="{node_id}"> in act '
                    f"{act} with fill:none -- an act that drops a component owes it one "
                    f"visible farewell; retired once, visibly, then never again"))
            elif ghost["filled"] or not ghost["shapes"]:
                defects.append(_defect(
                    "acts/retired-ghost-missing",
                    f"act {act}: the {node_id} ghost has {ghost['filled']} filled shape(s)",
                    {"act": act, "node": node_id},
                    {"act": act, "id": node_id, "shapes": ghost["shapes"],
                     "filled": ghost["filled"]},
                    f"Set fill:none on the {node_id} ghost's {ghost['shapes']} shape(s) in "
                    f"act {act} -- a filled ghost reads as a component still running"))
    if (total or drawn_ghosts) and outline_rule is None:
        defects.append(_defect(
            "acts/retired-ghost-missing",
            f"{drawn_ghosts} ghost group(s) are drawn and no stylesheet rule scopes "
            f".is-ghost with fill:none, so every one of them paints solid",
            {"feature": FEATURE},
            {"ghosts_drawn": drawn_ghosts, "ghosts_required": total,
             "missing_rule": ".is-ghost .node__shape { fill: none }",
             "searched": "the cut's <style> block(s)"},
            "Restore the `.is-ghost … { fill: none }` rule in the cut's <style> "
            "(templates/snippets/camera-beat.css -> cb-ghost-retired) -- deleting the rule "
            "that makes a ghost an outline turns every farewell back into a live component"))
    return row("retired-ghost", defects,
               f"{total} retired id(s) drawn outline-only, {drawn_ghosts} ghost group(s) "
               f"in the cut" if total or drawn_ghosts
               else "no act retires an id and none declares a ghostOf -- nothing to bury")


def stage_results(html, manifest):
    """The `retired-ghost` row, or N-A when the cut never declared `act-delta`."""
    if FEATURE not in set(manifest.get("features") or []):
        return [na(STAGE, "retired-ghost", f"feature {FEATURE!r} not declared")]
    return [check_ghosts(html, manifest)]
