#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage B: a component keeps ONE identity across acts, or the cut is not one system.

`references/multi-pane.md`'s continuity rule -- "a component alive across tiers keeps its
shape, role colour and relative position ... Retired components never reappear" -- was prose
only: nothing said the `postgres` drum in act 4 was the drum act 1 introduced, so the rule
could break by honest mistake with every gate green. `data-node-id` makes it checkable, and
this module is the ways that sentence can be broken:

  acts/node-id-missing        a `g.node` in an act with no id, or two nodes sharing one
  acts/identity-role-drift    one id, two `data-role`s across acts
  acts/identity-shape-drift   one id, two shape signatures (tag + `.node__shape` class set,
                              via verify_edge_anchors' discriminator -- never re-derived)
  acts/identity-zone-drift    one id, two 4x3 grid cells. A declared `moved` rebases the
                              baseline only for an ADJACENT cell (|dcol|+|drow| <= 1):
                              a blanket `id:moved` must not switch the rule off, and a
                              component that crosses the frame is a removal plus an addition
  acts/retired-id-returns     an id absent in act N and drawn again in act N+k
  acts/debut-accent-missing   an id in `delta.added` whose group lacks the debut accent
  acts/anchor-not-shared      an anchor hold names an id one of its acts does not draw
                              (both live in diagram-director/scripts/verify_act_debut_anchor.py: they read
                              the MANIFEST's declarations, not the DOM alone)

Read from the FILE with `re` (diagram-director/scripts/act_dom_scan.py), so the row is never UNVERIFIED.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import act_dom_scan as scan                                          # noqa: E402
from verify_act_debut_anchor import anchor_defects, debut_defects    # noqa: E402
from verify_all_report import bad, na, ok                            # noqa: E402

STAGE, FEATURE = "B structural", "node-identity"


def registry(html, viewbox):
    """[{act, window, nodes: {id: info}, flaws}] -- the id registry, per act. `flaws` are
    the two ways an act can fail to HAVE one: a node with no id, two claiming one."""
    out = []
    for entry in scan.read_acts(html):
        nodes, flaws = {}, []      # flaw = a node the registry cannot key on
        for i, node in enumerate(scan.read_nodes(entry["body"])):
            node_id = node["id"]
            if not node_id:
                flaws.append({"act": entry["act"], "index": i, "label": node["label"],
                              "why": "no data-node-id"})
                continue
            if node_id in nodes:
                flaws.append({"act": entry["act"], "id": node_id,
                              "why": "two nodes in this act carry the id"})
                continue
            node["zone"] = scan.zone(node["x"], node["y"], viewbox)
            nodes[node_id] = node
        out.append({"act": entry["act"], "window": entry["window"], "body": entry["body"],
                    "nodes": nodes, "flaws": flaws})
    return out


def _defect(code, reason, subject, evidence, fix):
    return dict(code=code, reason=reason, subject=subject, evidence=evidence, fix=fix)


def row(label, defects, ok_reason):
    """One stage-table row per gate FAMILY; each measured defect rides as a payload. The
    row carries the FIRST defect's code, exactly as a browser sweep does --
    verify_all_json.py expands `evidence['diagnostics']` into one diagnostic each, so the
    second and third findings of one sweep are not lost behind the first."""
    if not defects:
        return ok(STAGE, label, ok_reason)
    head, rest = defects[0], defects[1:]
    evidence = dict(head["evidence"])
    if rest:
        evidence["diagnostics"] = [{"code": d["code"], "subject": d["subject"],
                                    "evidence": d["evidence"]} for d in rest]
    return bad(STAGE, label, f"{len(defects)} defect(s); first: {head['reason']}",
               code=head["code"], subject=head["subject"], evidence=evidence,
               fixes=[d["fix"] for d in defects])


def _declared_moves(acts_declared):
    """{act: {id, ...}} -- the ids an act DECLARED it moved, which waives the zone check."""
    return {e.get("act"): {c.get("id") for c in (e.get("delta") or {}).get("changed", [])
                           if c.get("what") == "moved"} for e in acts_declared or []}


def _steps(cell_a, cell_b):
    """Manhattan distance between two 4x3 cells -- 1 is next door, 2 is across the frame."""
    return sum(abs(int(a) - int(b)) for a, b in zip(cell_a, cell_b))


def _far_move(node_id, seen, node, act):
    """A DECLARED move that is not a move: `moved` waives the neighbour, never the frame."""
    return _defect(
        "acts/identity-zone-drift",
        f"{node_id}: declared moved, but zone {seen['zone']} in act {seen['act']} -> "
        f"{node['zone']} in act {act} is {_steps(seen['zone'], node['zone'])} cells apart",
        {"node": node_id},
        {"id": node_id, "act_a": seen["act"], "act_b": act, "zone_a": seen["zone"],
         "zone_b": node["zone"], "cells_apart": _steps(seen["zone"], node["zone"]),
         "declared": "moved", "adjacent_max": 1},
        f"Draw {node_id} in act {act} within one 4x3 cell of {seen['zone']}, or stop "
        f"calling it the same component: a relocation across the frame is removed + added, "
        f"not a move -- `moved` waives the neighbouring cell, never the whole frame")


def check_identity(html, manifest):
    """The `tier-identity` row: ids exist, and each means one thing in every act."""
    acts = registry(html, (manifest.get("target") or {}).get("viewbox") or [0, 0, 1920, 1080])
    moved = _declared_moves(manifest.get("acts"))
    defects, first, present = [], {}, {}

    for entry in acts:
        act = entry["act"]
        for flaw in entry["flaws"]:
            name = flaw.get("id") or f"node #{flaw['index']} ({flaw.get('label') or '?'})"
            defects.append(_defect(
                "acts/node-id-missing", f"act {act}: {name} -- {flaw['why']}",
                {"act": act, "node": name}, flaw,
                f"Give act {act}'s {name} a unique kebab-case data-node-id -- a node with "
                f"no id cannot be tracked, which is what makes the delta checkable"))
        for node_id, node in entry["nodes"].items():
            present.setdefault(node_id, []).append(act)
            # Compared against the id's FIRST appearance, so a drift is one defect and not
            # one per later act. A DECLARED move rebases the zone; nothing else does.
            seen = first.setdefault(node_id, dict(node, act=act))
            for field, code in (("role", "acts/identity-role-drift"),
                                ("shape", "acts/identity-shape-drift"),
                                ("zone", "acts/identity-zone-drift")):    # one pass each
                if node[field] == seen[field]:
                    continue
                if field == "zone" and node_id in moved.get(act, set()):
                    if _steps(seen["zone"], node["zone"]) <= 1:
                        seen["zone"], seen["act"] = node["zone"], act   # declared: rebase
                        continue
                    defects.append(_far_move(node_id, seen, node, act))
                    continue
                defects.append(_defect(
                    code, f"{node_id}: {field} {seen[field]} in act {seen['act']}, "
                          f"{node[field]} in act {act}",
                    {"node": node_id},
                    {"id": node_id, "act_a": seen["act"], "act_b": act,
                     f"{field}_a": seen[field], f"{field}_b": node[field]},
                    (f"Draw {node_id} in act {act} in zone {seen[field]}, where act "
                     f"{seen['act']} draws it -- or, if the move is deliberate, declare it "
                     f"in the sheet's ACT DELTA row as {node_id}:moved")
                    if field == "zone" else
                    (f"Set {node_id}'s {field} in act {act} to {seen[field]!r}, the value it "
                     f"carries in act {seen['act']} -- a rename is a removal plus an "
                     f"addition, never a quiet edit")))

    for node_id, seen_in in present.items():
        gaps = [e["act"] for e in acts
                if seen_in[0] <= e["act"] <= seen_in[-1] and e["act"] not in seen_in]
        if gaps:
            defects.append(_defect(
                "acts/retired-id-returns",
                f"{node_id} is absent in act(s) {gaps} and drawn again in act {seen_in[-1]}",
                {"node": node_id},
                {"id": node_id, "present_in": seen_in, "absent_in": gaps},
                f"Either keep {node_id} in act(s) {gaps} or give the returning component a "
                f"NEW id -- a retired component that reappears makes every act delta a lie"))

    defects += debut_defects(acts, manifest) + anchor_defects(acts, manifest)
    return row("tier-identity", defects,
               f"{len(present)} id(s) across {len(acts)} act(s) keep one role, one shape "
               f"signature, one 4x3 zone; no retired id returns")


def stage_results(html, manifest):
    """The `tier-identity` row, or N-A when the cut never declared `node-identity`.

    Two shapes of cut, one row. With act groups the registry above compares an id across
    acts; with none there is nothing to compare ACROSS, but the contract still holds inside
    the file -- ids present and unique, edge endpoints resolving -- and a green row over an
    empty act list would be the silent pass this suite exists to refuse."""
    if FEATURE not in set(manifest.get("features") or []):
        return [na(STAGE, "tier-identity", f"feature {FEATURE!r} not declared")]
    if not scan.read_acts(html):
        from verify_plain_identity import check_plain   # local: breaks the import cycle
        return [check_plain(html)]
    return [check_identity(html, manifest)]
