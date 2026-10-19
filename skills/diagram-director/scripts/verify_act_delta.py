#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage B: the act delta a cut DECLARES is the delta its DOM actually draws.

`acts[].delta` would be decoration if nothing compared it with the file. These checks
are what make it evidence:

  acts/delta-mismatch       `added` must equal ids(act N) - ids(act N-1), `removed` must
                            equal ids(act N-1) - ids(act N). Both are DERIVED, so a manifest
                            can only be right about them. `changed` is author-declared and
                            checked for ID EXISTENCE only -- no gate infers semantics.
  acts/delta-caption-empty  a caption inside act N's window must NAME something act N
                            changed -- by id, by the node's rendered label, or by a
                            `captionAliases` surface form. The mechanical form of "a tier
                            caption that only restates the CCU number has said nothing"
                            (references/multi-pane.md). Three-way, because ids are
                            kebab-case and captions are prose (in one golden, Vietnamese):
                            anything stricter fails correct cuts, anything looser stops
                            being a check.
  (two more rows ride the same feature and live beside this one: the retired-component
   farewell in diagram-director/scripts/verify_retired_ghost.py, and the optional `+N / -N` title-card chip
   -- one RENDERING of a delta, never the delta -- in diagram-director/scripts/verify_act_delta_chip.py)
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import act_dom_scan as scan                                          # noqa: E402
from verify_all_report import na                                     # noqa: E402
from verify_tier_identity import STAGE, _defect, registry, row       # noqa: E402

FEATURE = "act-delta"


def _names(caption, needles):
    """The needles this caption really contains, matched on token boundaries, case-blind.
    Boundaries matter: a bare `app` would otherwise match "happens" and certify a caption
    that names nothing. Hyphens count as word characters, so `app` does not match
    `app-monolith` either -- naming the successor is not naming what it replaced."""
    text = caption.lower()
    found = []
    for needle in needles:
        token = needle.strip().lower()
        if token and re.search(rf"(?<![a-z0-9-]){re.escape(token)}(?![a-z0-9-])", text):
            found.append(needle)
    return found


def _delta_ids(entry):
    delta = entry.get("delta") or {}
    return (list(delta.get("added") or []), list(delta.get("removed") or []),
            [c.get("id") for c in (delta.get("changed") or [])])   # ids only: no semantics


def check_delta(html, manifest):
    """The `act-delta` row: delta truth and caption truth. Chips ride their own row."""
    viewbox = (manifest.get("target") or {}).get("viewbox") or [0, 0, 1920, 1080]
    acts = registry(html, viewbox)
    declared = {e.get("act"): e for e in (manifest.get("acts") or [])}
    captions = manifest.get("captions") or []
    defects, previous = [], set()

    for entry in acts:
        act, drawn = entry["act"], set(entry["nodes"])
        spec = declared.get(act)
        if spec is None:
            defects.append(_defect(
                "acts/delta-mismatch", f"act {act} has no acts[] entry",
                {"act": act}, {"act": act, "ids_drawn": sorted(drawn)},
                f"Add an ACT DELTA row for act {act} to the sheet and re-emit acts[] with "
                f"`emit_timeline.py --acts-table` -- {len(drawn)} node(s) are drawn there"))
            previous = drawn
            continue
        added, removed, changed = _delta_ids(spec)
        for field, got, want in (("added", set(added), drawn - previous),
                                 ("removed", set(removed), previous - drawn)):
            if got != want:
                defects.append(_defect(
                    "acts/delta-mismatch",
                    f"act {act}: delta.{field} declares {sorted(got)}, the DOM says "
                    f"{sorted(want)}",
                    {"act": act},
                    {"act": act, "field": field, "declared": sorted(got),
                     "derived": sorted(want), "only_declared": sorted(got - want),
                     "only_drawn": sorted(want - got)},
                    f"Set act {act}'s `{field}` to {sorted(want)} in the sheet's ACT DELTA "
                    f"row -- {field} is derived, not chosen (a rename is a removal plus an "
                    f"addition)"))
        for node_id in changed:
            if node_id not in drawn:
                defects.append(_defect(
                    "acts/delta-mismatch",
                    f"act {act}: delta.changed names {node_id}, which it does not draw",
                    {"act": act, "node": node_id},
                    {"act": act, "field": "changed", "id": node_id,
                     "ids_drawn": sorted(drawn)},
                    f"Remove {node_id} from act {act}'s `changed` cell, or draw it in act "
                    f"{act} -- a changed component is one that is still there"))
        defects += _caption_defects(act, entry, spec, added + removed + changed, captions)
        previous = drawn

    return row("act-delta", defects,
               f"{len(declared)} declared act delta(s) equal the id sets the DOM draws; "
               f"every act's caption names something that act changed")


def _caption_defects(act, entry, spec, delta_ids, captions):
    """Act N's captions must name at least one of the ids act N changed."""
    if not delta_ids:
        return []
    window = entry["window"] or [0, 100]
    aliases = spec.get("captionAliases") or {}
    needles = set(delta_ids)
    for node_id in delta_ids:
        node = entry["nodes"].get(node_id)
        if node and node["label"]:
            needles.add(node["label"])
        if node_id in aliases:
            needles.add(aliases[node_id])
    # OVERLAP, not containment: a caption that starts inside act N and runs a beat past its
    # crossfade is still act N's caption, and containment quietly dropped it from the check.
    inside = [c for c in captions
              if (c.get("window") or [0, 0])[0] < window[1] - 1e-6
              and window[0] < (c.get("window") or [0, 100])[1] - 1e-6]
    hits = {c.get("element"): _names(c.get("text") or "", needles) for c in inside}
    if any(hits.values()):
        return []
    return [_defect(
        "acts/delta-caption-empty",
        f"act {act}: none of its {len(inside)} caption(s) name any of {sorted(delta_ids)}",
        {"act": act},
        {"act": act, "window": window, "delta_ids": sorted(delta_ids),
         "captions": dict(hits), "needles_tried": sorted(needles)},
        f"Rewrite one caption inside {window} to name one of {sorted(delta_ids)} (or its "
        f"rendered label), or declare the surface form it already uses as a caption-alias "
        f"in act {act}'s ACT DELTA row -- a tier caption that only restates the load number "
        f"has said nothing")]


def stage_results(html, manifest):
    """The `act-delta` row, or N-A when the cut never declared `act-delta`."""
    if FEATURE not in set(manifest.get("features") or []):
        return [na(STAGE, "act-delta", f"feature {FEATURE!r} not declared")]
    return [check_delta(html, manifest)]
