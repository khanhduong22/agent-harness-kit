#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage D's repair sentence for a hold that misses its text floor -- PROVEN, never advice.

The whole point of this module is the last line of `solved_fix()`: nothing is emitted as a
transform until `solve_camera.check()` has been run against it and returned PASS on BOTH
assertions. Three ways that matters, each of which shipped a wrong number before the proof
step existed:

  ROUNDING     `k_read` is reported to 4 decimals, and 24/18 = 1.33333... rounds DOWN to
               1.3333, which lands at 23.9994 frame px -- a fix that fails the gate it was
               solved from. k is therefore CEILED at 4 decimals, then proved.
  CENTRE       a hold may declare a `center` off its bbox centre. Framing at the minimum
               passing k around that centre can push the bbox out of frame, so the fix is
               re-checked; if it does not contain, the same k is re-framed on the BBOX
               centre and proved again before it is offered.
  HALF-UP      tx/ty use solve_camera's own `_round` (half-up), not Python's half-even
               `round()`, so the numbers match the ones the solver wrote into the goldens.

When no transform can be proved the fix states ARITHMETIC ESCAPES with numbers instead --
which side overflows by how much and the tx/ty interval that would contain, or the bbox and
fs_min an over-stuffed beat would need. camera-beat.md forbids the fourth option (zooming
out), so it is never offered.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from solve_camera import _round as round_half_up                     # noqa: E402
from solve_camera import check as solve_check                        # noqa: E402
from solve_camera import solve as solve_frame                        # noqa: E402


def ceil_k(p_min, fs_min):
    """The smallest 4-decimal k that still meets the floor. Ceil, never round: a k that is
    one ulp light reads as 23.9994 frame px against a floor of 24 and fails the paste-back."""
    if fs_min <= 0:
        return 0.0
    return math.ceil((p_min / fs_min) * 1e4) / 1e4


def transform_for(viewport, k, center):
    """(tx, ty) that puts `center` in the middle of the frame at scale k, half-up rounded."""
    return (round_half_up(viewport[0] / 2.0 - k * center[0], 0),
            round_half_up(viewport[1] / 2.0 - k * center[1], 0))


def tx_range(width, k, b0, size):
    """The closed interval of tx that keeps [b0, b0+size] inside the frame at scale k.
    Empty (lo > hi) when the box is simply wider than the frame at that k."""
    return -k * b0, width - k * (b0 + size)


def _proves(viewport, bbox, fs_min, k, tx, ty, gate):
    out = solve_check(viewport, bbox, fs_min, k, tx, ty, 0.0, gate=gate)
    return out if out["containment"] == "PASS" and out["text_floor"] != "FAIL" else None


def _overflow(margins):
    """The sides that do not contain, worst first, as `left 140.0` strings."""
    over = sorted(((side, -value) for side, value in margins.items() if value < -1e-6),
                  key=lambda pair: -pair[1])
    return ", ".join(f"{side} by {amount:g} world px" for side, amount in over)


def _escape_centre(hold_id, viewport, bbox, k, centre, proof, box):
    """No transform contains at the minimum passing k around this centre: say which side
    overflows by how much, and the tx/ty interval that WOULD contain at that same k."""
    bx, by, bw, bh = bbox
    tx_lo, tx_hi = tx_range(viewport[0], k, bx, bw)
    ty_lo, ty_hi = tx_range(viewport[1], k, by, bh)
    room = (f"tx in [{tx_lo:g}, {tx_hi:g}] and ty in [{ty_lo:g}, {ty_hi:g}]"
            if tx_lo <= tx_hi and ty_lo <= ty_hi else
            f"NO tx/ty contains it at k={k:g}: the bbox is {bw:g}x{bh:g} world px, which is "
            f"wider than the {viewport[0] / k:.1f}x{viewport[1] / k:.1f} frame that k gives")
    return (f"Hold {hold_id} needs k={k:g} to meet its text floor, but at that k "
            f"neither its declared centre {centre[0]:g},{centre[1]:g} nor the bbox centre "
            f"{bx + bw / 2:g},{by + bh / 2:g} keeps bbox {box} in frame -- it overflows "
            f"{_overflow(proof['margins'])}. Keep k={k:g} and set {room}, or shrink the "
            f"must-show bbox. Never zoom out (references/camera-beat.md).")


def _escape_stuffed(hold_id, need, bbox, fs_min, box):
    k_read, k_max = need["k_read"], need["k_max"]
    return (f"Shrink hold {hold_id}'s must-show bbox to at most "
            f"{need['viewport'][0] / k_read:.1f}x{need['viewport'][1] / k_read:.1f} world px "
            f"(it is {bbox[2]:g}x{bbox[3]:g}), or raise its smallest essential text to fs_min "
            f"{need['p_min'] / k_max:.2f} world px (it is {fs_min:g}) -- k_read {k_read:g} is "
            f"above k_max {k_max:g}, so no k frames this beat. Never zoom out "
            f"(references/camera-beat.md): restack, let the upstream node peek, or split "
            f"the beat.")


def solved_fix(hold_id, viewport, bbox, fs_min, gate, center):
    """([one fix sentence], binding constraint). A transform is emitted ONLY when
    solve_camera.check() passes it on containment AND the text floor."""
    bbox = [float(v) for v in bbox]
    viewport = [float(v) for v in viewport]
    need = solve_frame(viewport, bbox, fs_min, pad=0.0, gate=gate)
    box = ",".join(f"{v:g}" for v in bbox)
    if need["status"] == "empty-interval":
        return [_escape_stuffed(hold_id, need, bbox, fs_min, box)], need["binding"]

    k2 = ceil_k(need["p_min"], fs_min)
    bbox_centre = (bbox[0] + bbox[2] / 2.0, bbox[1] + bbox[3] / 2.0)
    for centre, why in ((tuple(center), ""), (bbox_centre, " recentred on the bbox centre "
                                              f"{bbox_centre[0]:g},{bbox_centre[1]:g}, which "
                                              "the declared centre could not contain")):
        tx2, ty2 = transform_for(viewport, k2, centre)
        proof = _proves(viewport, bbox, fs_min, k2, tx2, ty2, gate)
        if proof:
            extra = f"; also set center to [{centre[0]:g}, {centre[1]:g}]" if why else ""
            return [f"Set hold {hold_id} to k={k2:g} tx={tx2:g} ty={ty2:g} (re-solved from "
                    f"bbox {box} at fs_min {fs_min:g}{why}; re-checked: containment PASS, "
                    f"{proof['text_frame_px']:g} frame px against the {gate} floor "
                    f"{proof['p_min']:g}{extra})"], need["binding"]
    # Neither centre frames it: no honest transform exists, so state the arithmetic instead.
    tx2, ty2 = transform_for(viewport, k2, bbox_centre)
    failed = solve_check(viewport, bbox, fs_min, k2, tx2, ty2, 0.0, gate=gate)
    return [_escape_centre(hold_id, viewport, bbox, k2, tuple(center), failed, box)], \
        need["binding"]
