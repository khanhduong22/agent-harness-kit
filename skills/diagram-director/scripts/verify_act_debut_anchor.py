#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage B: the two identity defects that read a DECLARATION, not the DOM alone.

Both ride the `tier-identity` row (diagram-director/scripts/verify_tier_identity.py) and both compare a
manifest claim with what an act actually draws:

  acts/debut-accent-missing  an id in `delta.added` must wear the debut accent in the act
                             that added it -- "each act's NEW components take the accent on
                             entry" (references/camera-beat.md), made checkable.
  acts/anchor-not-shared     a hold's `anchor` must be drawn by BOTH acts its window sits
                             between: an anchor the incoming act does not draw is not a
                             fixed point, it is a cut.

Apart from the identity module so both files stay under the repo's 200-line rule. `_defect`
is imported inside each function: the two modules would otherwise import each other.
"""

DEBUT_CLASS = "node--new"      # the house idiom for "new in this act" (camera-beat.md)


def debut_defects(acts, manifest):
    """Every id an act DECLARED it added must wear the debut accent in that act."""
    from verify_tier_identity import _defect        # local: breaks the import cycle
    by_act, out = {e["act"]: e for e in acts}, []
    for entry in manifest.get("acts") or []:
        act = entry.get("act")
        nodes = (by_act.get(act) or {}).get("nodes") or {}
        for node_id in (entry.get("delta") or {}).get("added", []):
            node = nodes.get(node_id)
            if node and DEBUT_CLASS not in node["classes"]:
                out.append(_defect(
                    "acts/debut-accent-missing",
                    f"act {act}: {node_id} debuts without .{DEBUT_CLASS}",
                    {"act": act, "node": node_id},
                    {"id": node_id, "act": act, "classes": node["classes"],
                     "expected_class": DEBUT_CLASS},
                    f"Add the class {DEBUT_CLASS} to {node_id}'s group in act {act} -- each "
                    f"act's NEW components take the accent on entry (camera-beat.md)"))
    return out


def anchor_defects(acts, manifest):
    """An anchor hold's node must be in EVERY act its window touches -- the whole point."""
    from verify_tier_identity import _defect        # local: breaks the import cycle
    out, holds = [], manifest.get("holds") or []
    for hold in holds:
        anchor, window = hold.get("anchor"), hold.get("window") or []
        if not anchor or len(window) != 2:
            continue
        touched = [e for e in acts if e["window"] and
                   e["window"][0] <= window[1] and window[0] <= e["window"][1]]
        # An anchor hold that PRECEDES the crossfade sits inside ONE act -- which is the
        # shape a cut wants, because a hold whose midpoint lands in the overlap gets its
        # geometry measured and its contact sheet shot with two acts half-drawn over each
        # other. The other act it is about is then the next one.
        if len(touched) == 1:
            touched += [e for e in acts if e["act"] == touched[0]["act"] + 1]
        missing = [e["act"] for e in touched if anchor not in e["nodes"]]
        if len(touched) < 2 or missing:
            out.append(_defect(
                "acts/anchor-not-shared",
                f"hold {hold.get('id')}: anchor {anchor} is not in act(s) "
                f"{missing or '(the hold touches only one act)'}",
                {"hold": hold.get("id"), "node": anchor},
                {"anchor": anchor, "window": window,
                 "acts_touched": [e["act"] for e in touched], "missing_from": missing},
                f"Anchor hold {hold.get('id')} on a node both act(s) "
                f"{[e['act'] for e in touched]} draw, or move its window "
                f"{window} to sit across the crossfade it means to hold through"))
    return out
