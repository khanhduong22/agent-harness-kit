#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage B: the role lens, and the legend as a claim the DOM has to pay.

A role-lens beat answers ONE question -- how do these two roles talk? It declares
`lens: [roleA, roleB]` on its spotlight hold, and three things follow mechanically:

  lens/edge-set-mismatch  the animated (dash-flow) edges in that act must be EXACTLY the
                          edges whose endpoints span the two roles. A lens that animates a
                          third role is teaching a different lesson than the one it
                          announced; a lens that animates fewer is announcing a lesson it
                          does not show.
  lens/node-not-idled     every node outside the two roles carries `.is-idle` in that act.
  lens/edge-unattributed  every `path.edge` in a lens act declares BOTH endpoints. The
                          cross-role set is computed FROM `data-from`/`data-to`, so an edge
                          that declares neither is invisible to the comparison: stripping
                          the attributes shrinks the cross-role set until it equals the
                          animated one and the gate goes green on a cut nobody fixed. An
                          undeclared endpoint is the defect, and it is reported INSTEAD of
                          the set comparison -- a graph the file does not declare cannot be
                          compared with anything.
  manifest/feature-empty  `role-lens` is declared and no lens hold carries a window, so
                          nothing was compared -- the house rule: a check that finds
                          nothing FAILS.

The edge set is read from `data-from`/`data-to`, which is why this gate is stdlib: the cut
declares its own graph, so the check never needs a browser to know which edge joins which
roles.

The legend half of this family -- `legend-fact`, the entries and their counts -- lives in
diagram-director/scripts/verify_legend_fact.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import act_dom_scan as scan                                          # noqa: E402
from verify_all_report import na                                     # noqa: E402
from verify_tier_identity import STAGE, _defect, registry, row       # noqa: E402

FEATURE = "role-lens"
IDLE_CLASS = "is-idle"


def lens_holds(manifest):
    return [h for h in (manifest.get("holds") or [])
            if h.get("kind") == "spotlight" and h.get("lens")]


def _act_for(acts, window):
    """The act whose own window contains this lens window -- a lens lives inside one act."""
    for entry in acts:
        span = entry["window"] or []
        if len(span) == 2 and span[0] - 1e-6 <= window[0] and window[1] <= span[1] + 1e-6:
            return entry
    return None


def _is_animated(edge):
    return any("dash-flow" in token for token in edge["classes"])


def check_lens(html, manifest):
    """The `role-lens` row: the animated set IS the cross-role set, and nothing else moves."""
    viewbox = (manifest.get("target") or {}).get("viewbox") or [0, 0, 1920, 1080]
    acts = registry(html, viewbox)
    defects, checked = [], 0
    holds = lens_holds(manifest)
    for hold in holds:
        roles = set(hold.get("lens") or [])
        if not (hold.get("windows") or []):
            defects.append(_defect(
                "manifest/feature-empty",
                f"lens hold {hold.get('element')!r} declares lens {sorted(roles)} and no "
                f"window, so this gate compared nothing",
                {"feature": FEATURE, "hold": hold.get("element")},
                {"feature": FEATURE, "element": hold.get("element"),
                 "lens": sorted(roles), "windows": hold.get("windows")},
                f"Give the lens hold {hold.get('element')!r} the window(s) it plays in, or "
                f"drop `lens` from it and `role-lens` from `features` -- a lens beat with "
                f"no window is a declared feature with no evidence"))
            continue
        for window in hold.get("windows") or []:
            entry = _act_for(acts, window)
            if entry is None:
                defects.append(_defect(
                    "lens/edge-set-mismatch",
                    f"lens {hold.get('element')}: window {window} is inside no act",
                    {"hold": hold.get("element")},
                    {"element": hold.get("element"), "window": window,
                     "act_windows": [e["window"] for e in acts]},
                    f"Move the lens window {window} inside one act's own window -- a lens "
                    f"that spans a crossfade is asking about two different systems"))
                continue
            checked += 1
            defects += _lens_defects(hold, roles, window, entry)
    if not checked and not defects:
        defects.append(_defect(
            "manifest/feature-empty",
            f"feature {FEATURE!r} is declared and no lens window was checked",
            {"feature": FEATURE},
            {"feature": FEATURE, "lens_holds": len(holds), "windows_checked": 0},
            f"Declare a spotlight hold with `lens: [roleA, roleB]` and at least one window, "
            f"or remove {FEATURE!r} from `features` -- a check that finds nothing FAILS"))
    return row("role-lens", defects,
               f"{checked} lens window(s): the dash-flow edges are exactly the cross-role "
               f"edges, and every out-of-lens node is idled")


def _lens_defects(hold, roles, window, entry):
    role_of = {node_id: node["role"] for node_id, node in entry["nodes"].items()}
    edges = list(scan.read_edges(entry["body"]))
    out, cross, animated = [], set(), set()
    bare = [i for i, edge in enumerate(edges) if not (edge["from"] and edge["to"])]
    if bare:
        out.append(_defect(
            "lens/edge-unattributed",
            f"act {entry['act']}: {len(bare)} edge(s) declare no data-from/data-to, so the "
            f"cross-role set for lens {sorted(roles)} cannot be computed",
            {"act": entry["act"], "hold": hold.get("element")},
            {"act": entry["act"], "lens": sorted(roles), "edges": len(edges),
             "unattributed_indexes": bare,
             "unattributed": [{"index": i, "from": edges[i]["from"],
                               "to": edges[i]["to"], "classes": edges[i]["classes"]}
                              for i in bare]},
            f"Give every path.edge in act {entry['act']} both data-from and data-to -- the "
            f"lens compares the animated edges with the edges that JOIN {sorted(roles)}, "
            f"and an edge that names no endpoint silently leaves that comparison"))
        return out + _idle_defects(hold, roles, entry)
    for i, edge in enumerate(edges):
        key = f"{edge['from']}->{edge['to']}#{i}"
        if {role_of.get(edge["from"]), role_of.get(edge["to"])} == roles and len(roles) == 2:
            cross.add(key)
        if _is_animated(edge):
            animated.add(key)
    if cross != animated:
        out.append(_defect(
            "lens/edge-set-mismatch",
            f"act {entry['act']} lens {sorted(roles)}: {len(animated)} animated edge(s), "
            f"{len(cross)} cross-role edge(s)",
            {"act": entry["act"], "hold": hold.get("element")},
            {"act": entry["act"], "lens": sorted(roles), "window": window,
             "animated_only": sorted(animated - cross),
             "cross_role_only": sorted(cross - animated)},
            f"In act {entry['act']}, run dash-flow on exactly the {len(cross)} edge(s) that "
            f"join {sorted(roles)}: add it to {sorted(cross - animated)} and remove it from "
            f"{sorted(animated - cross)}"))
    return out + _idle_defects(hold, roles, entry)


def _idle_defects(hold, roles, entry):
    """Everything outside the two roles the lens announced must recede."""
    out = []
    stray = sorted(node_id for node_id, node in entry["nodes"].items()
                   if node["role"] not in roles and IDLE_CLASS not in node["classes"])
    if stray:
        out.append(_defect(
            "lens/node-not-idled",
            f"act {entry['act']} lens {sorted(roles)}: {len(stray)} node(s) outside the "
            f"lens are not idled ({stray[0]})",
            {"act": entry["act"], "hold": hold.get("element")},
            {"act": entry["act"], "lens": sorted(roles), "not_idled": stray},
            f"Add .{IDLE_CLASS} to {stray} in act {entry['act']} -- everything outside the "
            f"two roles the lens announced must recede"))
    return out


def stage_results(html, manifest):
    """The `role-lens` row, or N-A when the cut never declared the feature."""
    if FEATURE not in set(manifest.get("features") or []):
        return [na(STAGE, "role-lens", f"feature {FEATURE!r} not declared")]
    return [check_lens(html, manifest)]
