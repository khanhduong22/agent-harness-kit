#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The per-format, per-gate text floor for camera holds.

Policy, not arithmetic -- which is why it lives apart from `solve_camera.py`: the solver
does the same division either way, and the only thing that changes between a phone-held
vertical cut and a desk-read landscape one is the NUMBER a frame px has to clear.

One absolute constant did not survive two frame formats. 28 frame px was calibrated on a
VERTICAL 1080-wide export (the flash-sale cut) held at arm's length. A landscape 1920-wide
frame is read further from the eye across a wider field, and both frozen goldens sit there;
holding them to 28 would fail user-approved work, so the landscape row is calibrated from
those two sources instead.

`supporting` is recorded for authors and is NOT machine-checked: a manifest declares one
`fs_min` per hold -- the smallest ESSENTIAL text in that frame -- so nothing in the manifest
distinguishes a sub-label from a node label. Supporting-text legibility is a contact-sheet
item (references/pre-delivery-checklist.md).

See references/camera-beat.md -> "Choosing k" and references/multi-pane.md -> territory beats.
"""

FORMAT_FLOORS = {"vertical": {"essential": 28.0, "supporting": 19.0},
                 "landscape": {"essential": 24.0, "supporting": 17.0}}

# Whether the floor is a HARD gate for a hold of this gate kind.
#   read      -- the beat exists to be read; the floor is the gate.
#   territory -- a pane/tier orientation beat. Legibility here is containment plus the pane
#                heading, judged on the contact sheet; a node-label floor would fail every
#                honest territory beat (a whole pane at k_read does not fit a frame).
#   overview  -- waived outright: "legibility is judged per territory, never on the overview".
GATE_FLOOR_APPLIES = {"read": True, "territory": False, "overview": False}


def frame_format(viewport):
    """`vertical` or `landscape` from the frame's own aspect -- square counts as landscape."""
    width, height = viewport
    return "vertical" if height > width else "landscape"


def floor_for(gate, viewport):
    """(p_min, applies, reason) for a hold's gate in a frame of this format."""
    gate = gate or "read"
    if gate not in GATE_FLOOR_APPLIES:
        raise ValueError(f"gate {gate!r} is not one of {sorted(GATE_FLOOR_APPLIES)}")
    fmt = frame_format(viewport)
    p_min = FORMAT_FLOORS[fmt]["essential"]
    if GATE_FLOOR_APPLIES[gate]:
        return p_min, True, f"{gate} gate, {fmt} frame -> essential floor {p_min:g} frame px"
    why = ("containment + pane heading only (orientation beat)" if gate == "territory"
           else "floor waived on the overview")
    return p_min, False, f"{gate} gate -> {why}"
