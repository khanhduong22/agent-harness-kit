#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage B: the identity contract for a cut with NO act groups.

`node-identity` used to mean "every ACT node carries a `data-node-id`", so a cut without acts
could declare the feature and be measured against nothing: `registry()` finds no act group,
iterates an empty list and reports a green row. That is the same silent-pass shape the house
rule refuses everywhere else, and it made the feature undeclarable in practice for the single
-act cuts most sessions produce.

SKILL.md -> Output Rules now states the contract for EVERY cut, so this module holds an
act-less one to it, reading the file with the same stdlib scanner the act gates use:

  acts/node-id-missing    a `g.node` with no `data-node-id`, or two nodes sharing one
  edge/endpoint-unknown   a `path.edge` that declares no `data-from`/`data-to`, or names an
                          id no node in the file carries -- an edge whose endpoints cannot be
                          resolved is a line, not a claim about the graph
  manifest/feature-empty  `node-identity` declared and the file draws no `g.node` at all
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import act_dom_scan as scan                                          # noqa: E402
from verify_tier_identity import FEATURE, STAGE, _defect, row        # noqa: E402


def _node_defects(nodes):
    """Ids exist and are unique -- the two ways a file can fail to HAVE a registry."""
    out, seen = [], set()
    for index, node in enumerate(nodes):
        node_id, name = node["id"], node["label"] or "?"
        if not node_id:
            why, subject = "carries no data-node-id", f"node #{index} ({name})"
        elif node_id in seen:
            why, subject = "is the id of an earlier node in this file", node_id
        else:
            seen.add(node_id)
            continue
        out.append(_defect(
            "acts/node-id-missing", f"{subject} {why}",
            {"node": subject},
            {"index": index, "id": node_id, "label": name, "why": why,
             "ids_so_far": sorted(seen)},
            f"Give {subject} a unique kebab-case data-node-id -- a node the file cannot name "
            f"is a node no gate can compare with anything"))
    return out, seen


def _edge_defects(edges, ids):
    """Both endpoints declared, and both resolving to a node this file actually draws."""
    out = []
    for index, edge in enumerate(edges):
        unknown = [value for value in (edge["from"], edge["to"]) if not value or value not in ids]
        if not unknown:
            continue
        out.append(_defect(
            "edge/endpoint-unknown",
            f"edge #{index} declares from={edge['from']!r} to={edge['to']!r}; "
            f"{[u or '(missing)' for u in unknown]} is not a node id in this file",
            {"edge": f"{edge['from'] or '?'}->{edge['to'] or '?'}#{index}"},
            {"index": index, "from": edge["from"], "to": edge["to"],
             "unresolved": [u or None for u in unknown], "node_ids": sorted(ids)},
            f"Set edge #{index}'s data-from/data-to to ids this file draws ({sorted(ids)}) -- "
            f"an edge that names no endpoint is a line, not a claim about the graph"))
    return out


def check_plain(html):
    """The `tier-identity` row for a cut that has no act groups to walk."""
    nodes, edges = scan.read_nodes(html), scan.read_edges(html)
    if not nodes:
        return row("tier-identity", [_defect(
            "manifest/feature-empty",
            f"feature {FEATURE!r} is declared and the file draws no g.node at all",
            {"feature": FEATURE}, {"feature": FEATURE, "nodes": 0, "edges": len(edges)},
            f"Draw the cast as `<g class=\"node …\" data-node-id=…>` groups, or remove "
            f"{FEATURE!r} from `features` -- a check that finds nothing FAILS")], "")
    defects, ids = _node_defects(nodes)
    defects += _edge_defects(edges, ids)
    return row("tier-identity", defects,
               f"{len(nodes)} node(s) carry a unique data-node-id and {len(edges)} edge(s) "
               f"name endpoints this file draws (no act groups: the cross-act checks are "
               f"about acts, and this cut has none)")
