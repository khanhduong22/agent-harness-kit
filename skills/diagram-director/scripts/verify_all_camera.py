#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage D of diagram-director/scripts/verify_all.py: every declared camera hold, re-checked.

Reuses `solve_camera.check()` -- the same arithmetic that produced the holds -- with
the per-format/per-gate floor policy from `camera_text_floors.py` switched on. Two
assertions per hold:

  containment   the hold's must-show bbox is inside the frame the transform gives.
                pad 0 DELIBERATELY: --pad shapes the SOLVE, not the check, so an author
                who pulled the camera back on purpose still passes and the per-side
                margins say how much slack is left. (Lead decision, phase 06.)
  text floor    k * fs_min against the floor for this hold's gate in this frame format.
                `territory` and `overview` report N-A with the reason -- they were never
                held to a node-label floor. A manifest that DECLARES a `p_min` below the
                policy floor for a gate the floor applies to is itself a defect and fails
                here: the manifest cannot license a laxer floor than the policy.

Nothing here opens a browser. The rendered half -- that the text at that hold really is
that size on screen -- is stage E and the contact sheet.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from camera_solved_fix import solved_fix                              # noqa: E402
from camera_text_floors import floor_for                              # noqa: E402
from solve_camera import check as solve_check                         # noqa: E402
from verify_all_report import bad, na, ok                             # noqa: E402

STAGE = "D camera"


def hold_center(hold):
    """The hold's declared centre, falling back to its bbox centre (solve_camera's rule)."""
    center = hold.get("center")
    if center and len(center) == 2:
        return float(center[0]), float(center[1])
    bx, by, bw, bh = [float(v) for v in hold["bbox"]]
    return bx + bw / 2.0, by + bh / 2.0


def camera_holds(manifest):
    return [h for h in (manifest.get("holds") or []) if h.get("kind") == "camera"]


def viewport_of(manifest):
    """The frame in px. viewbox is [x, y, w, h]; the format is decided by w vs h."""
    box = (manifest.get("target") or {}).get("viewbox") or [0, 0, 0, 0]
    return [float(box[2]), float(box[3])]


def check_holds(manifest):
    """One Result per declared camera hold, plus one N-A line if there are none."""
    holds = camera_holds(manifest)
    features = set(manifest.get("features") or [])
    if not holds:
        if "beats" in features:
            return [bad(STAGE, "holds", "feature 'beats' declared but no camera hold "
                                        "in the manifest -- declared-but-empty",
                        code="manifest/feature-empty",
                        evidence={"feature": "beats", "camera_holds": 0})]
        return [na(STAGE, "holds", "no camera holds declared (feature 'beats' absent)")]
    viewport = viewport_of(manifest)
    if viewport[0] <= 0 or viewport[1] <= 0:
        return [bad(STAGE, "holds", f"target.viewbox gives a {viewport} frame",
                    code="manifest/hold-missing-field", evidence={"viewport": viewport})]

    results = []
    for hold in holds:
        hold_id = hold.get("id") or "(unnamed)"
        gate = hold.get("gate", "read")
        missing = [k for k in ("k", "tx", "ty", "bbox", "fs_min") if k not in hold]
        if missing:
            results.append(bad(STAGE, hold_id, f"hold is missing {missing}",
                               code="manifest/hold-missing-field",
                               subject={"hold": hold_id},
                               evidence={"missing": missing},
                               fixes=[f"Add {missing} to hold {hold_id} in the manifest, "
                                      f"solved by diagram-director/scripts/solve_camera.py"]))
            continue
        try:
            out = solve_check(viewport, [float(v) for v in hold["bbox"]],
                              float(hold["fs_min"]), float(hold["k"]),
                              float(hold["tx"]), float(hold["ty"]), 0.0, gate=gate)
            policy_floor, applies, reason = floor_for(gate, viewport)
        except ValueError as exc:
            results.append(bad(STAGE, hold_id, str(exc), code="camera/hold-containment",
                               subject={"hold": hold_id}, evidence={"error": str(exc)}))
            continue
        declared = float(hold.get("p_min") or 0)
        note = (f"k {out['k']:g} -> {out['text_frame_px']:g} frame px; {reason}; "
                f"margins {out['margins']}")
        subject = {"hold": hold_id}
        base = {"k": out["k"], "fs_min": float(hold["fs_min"]),
                "text_frame_px": out["text_frame_px"], "floor": out["p_min"], "gate": gate}
        if hold.get("fs_min_source"):
            base["fs_min_source"] = hold["fs_min_source"]
        if out["containment"] == "FAIL":
            results.append(bad(STAGE, hold_id, f"bbox is not inside the frame -- {note}",
                               code="camera/hold-containment", subject=subject,
                               evidence={**base, "margins": out["margins"],
                                         "frame_world": out["frame_world"]}))
        elif out["text_floor"] == "FAIL":
            # The fix is SOLVED here, not advised (diagram-director/scripts/camera_solved_fix.py):
            # solve_camera re-derives the smallest k that passes this gate's floor and
            # RE-CHECKS the transform it built, so a transform is printed only after it
            # has passed the same two assertions this row just failed.
            fixes, binding = solved_fix(hold_id, viewport, hold["bbox"],
                                        float(hold["fs_min"]), gate, hold_center(hold))
            results.append(bad(STAGE, hold_id, f"text floor -- {note}",
                               code="camera/hold-text-floor", subject=subject,
                               evidence={**base, "binding": binding}, fixes=fixes))
        elif applies and declared and declared < policy_floor - 1e-9:
            results.append(bad(STAGE, hold_id,
                               f"manifest declares p_min {declared:g} below the policy "
                               f"floor {policy_floor:g} for a {gate} gate -- {note}",
                               code="camera/pmin-below-policy", subject=subject,
                               evidence={**base, "declared_p_min": declared,
                                         "policy_floor": policy_floor},
                               fixes=[f"Set hold {hold_id}'s p_min to {policy_floor:g} "
                                      f"(the {gate}-gate floor for this frame format) or "
                                      f"remove the field and let the policy speak"]))
        else:
            results.append(ok(STAGE, hold_id, note))
    return results
