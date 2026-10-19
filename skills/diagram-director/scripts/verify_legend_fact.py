#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage B: the legend is a CLAIM about the cast, and the DOM has to pay it.

  legend/entry-unbacked   a legend entry names a role no act draws
  legend/count-wrong      an entry's `×N` is not that role's node count in the FINAL act
  legend/member-retired   an entry's MEMBER PROSE (`service ×6 alb · gateway · …`) names a
                          component the final act no longer draws. The count can be right
                          while the names beside it are a year out of date, and a reader
                          takes the names for the cast -- so a member token that is the id
                          or rendered label of a RETIRED component fails. Collective prose
                          (`services`, `shards`) matches no id and is left alone: this
                          catches the retired name, not the abbreviation.
  manifest/feature-empty  `legend` is declared and NO entry says which role it stands for --
                          the house rule, a check that finds nothing FAILS

Legend counting rides the EXISTING `legend` feature and only runs when `node-identity` is
declared too: without ids there is no reliable per-act cast to count.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import act_dom_scan as scan                                          # noqa: E402
from verify_all_report import na                                     # noqa: E402
from verify_tier_identity import STAGE, _defect, registry, row       # noqa: E402

LEGEND_FEATURES = ("legend", "node-identity")


def _members(text):
    """The member tokens after `xN`: `service x6 gateway · services` -> [gateway, services]."""
    tail = re.split(r"[×x]\s*\d+", text, maxsplit=1)
    return [token.strip() for token in (tail[1] if len(tail) > 1 else "").split("·")
            if token.strip()]


def _retired_names(acts):
    """{lowercase name: (id, last act that drew it)} for every id the FINAL act does not.

    Both the id and the node's rendered label count as names, because a legend writes
    whichever reads better. Anything the final act still draws is never in here.
    """
    final = acts[-1]["nodes"] if acts else {}
    live = {key.lower() for key in final}
    live |= {node["label"].lower() for node in final.values() if node["label"]}
    gone = {}
    for entry in acts[:-1]:
        for node_id, node in entry["nodes"].items():
            for name in (node_id, node["label"]):
                if name and name.lower() not in live:
                    gone[name.lower()] = (node_id, entry["act"])
    return gone


def _member_defects(entries, acts):
    """A legend that still names a component the cut retired is a stale cast list."""
    gone, out = _retired_names(acts), []
    final_act = acts[-1]["act"] if acts else None
    for item in entries:
        for token in _members(item["text"]):
            hit = gone.get(token.lower())
            if hit is None:
                continue
            node_id, last_act = hit
            out.append(_defect(
                "legend/member-retired",
                f"legend entry {item['text']!r} names {token!r}, retired after act "
                f"{last_act} and not drawn in act {final_act}",
                {"role": item["role"], "node": node_id},
                {"role": item["role"], "member": token, "id": node_id,
                 "last_drawn_in_act": last_act, "final_act": final_act,
                 "entry": item["text"]},
                f"Drop {token!r} from the {item['role']!r} legend entry, or name a component "
                f"act {final_act} still draws -- the legend is read as the cast of the last "
                f"frame, and a retired name there un-retires it"))
    return out


def check_legend(html, manifest):
    """The `legend-fact` row: every entry names a role the DOM has, with its real count."""
    viewbox = (manifest.get("target") or {}).get("viewbox") or [0, 0, 1920, 1080]
    acts = registry(html, viewbox)
    entries = scan.read_legend(html)
    drawn = {node["role"] for entry in acts for node in entry["nodes"].values()}
    final = acts[-1] if acts else {"act": None, "nodes": {}}
    counts = {}
    for node in final["nodes"].values():
        counts[node["role"]] = counts.get(node["role"], 0) + 1
    defects = []
    if not entries and drawn:
        # The house rule (diagram-director/scripts/browser-checks/README.md): a check that finds nothing
        # FAILS. A cut that declares `legend` and carries no entry saying which role it
        # stands for has a legend this gate cannot read, which is not the same as a legend
        # that is right -- and reading it is the whole claim `legend` makes.
        defects.append(_defect(
            "manifest/feature-empty",
            f"feature 'legend' is declared but no legend entry carries data-legend-role, "
            f"so none of the {len(drawn)} drawn role(s) is claimed by one",
            {"feature": "legend"},
            {"feature": "legend", "entries": 0, "roles_drawn": sorted(drawn)},
            f'Add data-legend-role="<role>" to each role entry in the legend (one of '
            f"{sorted(drawn)}) so the entry says which role it stands for"))
    defects += _member_defects(entries, acts)
    for item in entries:
        role, claimed = item["role"], item["count"]
        if role not in drawn:
            defects.append(_defect(
                "legend/entry-unbacked",
                f"legend entry {item['text']!r} names role {role!r}, which no act draws",
                {"role": role}, {"role": role, "roles_drawn": sorted(drawn)},
                f"Delete the {role!r} legend entry or draw a node with "
                f'data-role="{role}" -- a legend is a claim about the cast, not a wish'))
            continue
        real = counts.get(role, 0)
        if claimed != real:
            members = sorted(node_id for node_id, node in final["nodes"].items()
                             if node["role"] == role)
            defects.append(_defect(
                "legend/count-wrong",
                f"legend entry {item['text']!r} -- the final act draws {real} "
                f'data-role="{role}" node(s)',
                {"role": role},
                {"role": role, "claimed": claimed, "final_act": final["act"],
                 "actual": real, "members": members},
                f"legend entry {item['text']!r} -- the final act draws {real} "
                f'`data-role="{role}"` nodes ({", ".join(members)}); set it to '
                f"'{role} ×{real}'."))
    return row("legend-fact", defects,
               f"{len(entries)} legend role entry(s) match the final act's cast "
               f"{sorted(counts.items())}")


def stage_results(html, manifest):
    """The `legend-fact` row, or N-A when `legend`/`node-identity` are not both declared."""
    missing = sorted(set(LEGEND_FEATURES) - set(manifest.get("features") or []))
    if missing:
        return [na(STAGE, "legend-fact", f"feature(s) {missing} not declared")]
    return [check_legend(html, manifest)]
