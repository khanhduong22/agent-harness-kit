#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage B: a rendered `+N / -N` act chip must print the sizes of its own act delta.

The chip is OPTIONAL. The sheet's `## Phase 2 -- ACT DELTA` row -- and the `acts[]` entry
emitted from it -- is the FACT; the pill on an act title card is one way of SHOWING that
fact, shipped opt-in as `templates/snippets/act-delta-chip.html` plus the `cb-delta-chip`
block in `templates/snippets/camera-beat.css`. The frozen goldens render none (user
decision, 2026-08-30), so this gate lives on its own row with three honest outcomes:

  N-A    no act renders a chip -- nothing was measured here, and a PASS would claim
         otherwise. An optional decoration nobody used is not a defect.
  PASS   at least one chip is rendered and every one of them equals its act's delta.
  FAIL   acts/delta-chip-mismatch -- a chip EXISTS whose `+N`/`-N` disagree with
         len(delta.added) / len(delta.removed). Scenery may be omitted; it may not lie.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import act_dom_scan as scan                                          # noqa: E402
from verify_act_delta import FEATURE, _delta_ids                     # noqa: E402
from verify_all_report import na                                     # noqa: E402
from verify_tier_identity import STAGE, _defect, registry, row       # noqa: E402


def check_chips(html, manifest):
    """The `delta-chip` row: N-A with no chip, FAIL only on a chip that contradicts."""
    viewbox = (manifest.get("target") or {}).get("viewbox") or [0, 0, 1920, 1080]
    declared = {e.get("act"): e for e in (manifest.get("acts") or [])}
    defects, rendered, bare = [], 0, 0
    for entry in registry(html, viewbox):
        spec = declared.get(entry["act"])
        if spec is None:                     # acts/delta-mismatch already owns that act
            continue
        chips = scan.read_chips(entry["body"])
        rendered += len(chips)
        bare += 0 if chips else 1
        added, removed, _changed = _delta_ids(spec)
        for chip in chips:
            # The removed slot PRINTS a minus, so it must equal -len(removed): a chip that
            # spells `+1` where the act retired one is not saying what the act did.
            if chip["added"] == len(added) and chip["removed"] == -len(removed):
                continue
            defects.append(_defect(
                "acts/delta-chip-mismatch",
                f"act {entry['act']}: chip reads {chip['raw']!r}, delta is "
                f"+{len(added)} -{len(removed)}",
                {"act": entry["act"]},
                {"act": entry["act"], "chip_added": chip["added"],
                 "chip_removed": chip["removed"], "delta_added": len(added),
                 "delta_removed": len(removed)},
                f"Set act {entry['act']}'s delta chip to +{len(added)} and -{len(removed)}, "
                f"the sizes of its own ACT DELTA row -- or delete the chip, which is "
                f"optional scenery"))
    if not rendered:
        return na(STAGE, "delta-chip",
                  f"no chip rendered in any of {bare} act(s) -- optional scenery; the "
                  f"sheet's ACT DELTA row is the fact a chip would restate")
    return row("delta-chip", defects,
               f"{rendered} rendered chip(s) print their own act's delta sizes"
               + (f"; {bare} act(s) render none (optional scenery)" if bare else ""))


def stage_results(html, manifest):
    """The `delta-chip` row, or N-A when `act-delta` is not declared at all."""
    if FEATURE not in set(manifest.get("features") or []):
        return [na(STAGE, "delta-chip", f"feature {FEATURE!r} not declared")]
    return [check_chips(html, manifest)]
