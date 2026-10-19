#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Camera-frame solver for beat holds (references/camera-beat.md -> "Choosing k").

Framing arithmetic only. It decides nothing about which components a beat shows,
what its caption says or how long it holds -- the sheet owns all of that. It takes
a must-show bbox and returns the transform that frames it:

    k_fit  = min( (W - 2m) / bbox_w , (H - 2m) / bbox_h )      m = --pad, default 40
    k_read = P_min / fs_min                                    P_min = --pmin, default 28
    k_read <= k <= min(k_fit, --kcap)          lower bound only where the floor is
                                               HARD; territory/overview start at 0
    tx = W/2 - k*cx        ty = H/2 - k*cy     (transform-origin: 0 0 is mandatory)

Why it exists: hand-computed holds drifted ~5% on k and tx across a reviewed cut.
The solver removes the arithmetic error; the composition judgement stays with the
author, who may pull k back anywhere down to k_read -- `--check` accepts that.

USAGE
  solve                                 # emit a hold's transform + manifest fragment
    solve_camera.py --viewport 1920x1080 --bbox 88,422,804,318.4 --fs-min 13
                    [--k 2.2] [--center 470,565] [--pad 40] [--pmin 28] [--kcap 3]
                    [--gate read|territory|overview]
                    [--id b3] [--window 30.3571,69.6429] [--fs-min-source ".cap-b3 text"]
                    [--json]
  check                                 # what verify-all runs against a built cut
    solve_camera.py --check --viewport 1920x1080 --bbox 88,422,804,318.4
                    --fs-min 13 --transform 2.2,-74,-703 [--gate read] [--json]

  --gate opts into the per-format/per-gate floor policy (diagram-director/scripts/camera_text_floors.py)
  instead of a flat --pmin: landscape essential 24, vertical essential 28, hard only at
  `read`. Valid in BOTH modes -- solve mode without it knows one flat P_min and so calls
  every honest territory hold over-stuffed, including the ones both goldens ship.
  Without --gate nothing changes in either mode.

  PAD RELIEF (`--gate overview` + explicit --k only). k=1 over the whole canvas is the
  commonest overview there is, and --pad 40 puts k_fit just under 1, so solve mode used
  to refuse a hold `--check` passes. Where the bbox is inside the frame at pad 0 -- the
  rule --check already uses -- solve mode accepts it and prints a `pad relief` line
  saying how much of the requested pad actually survived. A read beat that overflows
  its pad is still a defect; a territory beat still owes its pane heading room.

EXIT  0 ok · 2 bad input · 3 the frame does not hold (empty k interval, bbox out
      of frame, or the text floor is not met)
"""

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from camera_text_floors import GATE_FLOOR_APPLIES, floor_for   # noqa: E402

P_MIN_DEFAULT = 28.0    # legible frame px for a beat's essential text
PAD_DEFAULT = 40.0      # world-px margin inside the frame
K_CAP_DEFAULT = 3.0     # past this, strokes thicken and off-screen context dies


def _nums(text, count, name):
    parts = [p for p in text.replace("x", ",").split(",") if p.strip()]
    if len(parts) != count:
        raise ValueError(f"--{name} needs {count} numbers, got {text!r}")
    return [float(p) for p in parts]


def _round(value, precision):
    """Half-up, so 67.5 -> 68 like the goldens (Python's round() is half-even)."""
    if precision:
        return round(value, precision)
    return int(math.floor(value + 0.5)) if value >= 0 else -int(math.floor(-value + 0.5))


def frame(viewport, k, tx, ty):
    """The frame's rectangle in WORLD coordinates: (x0, y0, x1, y1)."""
    width, height = viewport
    return (-tx / k, -ty / k, (width - tx) / k, (height - ty) / k)


def solve(viewport, bbox, fs_min, pad=PAD_DEFAULT, p_min=P_MIN_DEFAULT,
          k_cap=K_CAP_DEFAULT, k=None, center=None, precision=0, gate=None,
          fs_min_source=None):
    """Framing for one hold. Returns a dict; 'status' is 'ok' or names the failure.

    `gate` routes the floor through camera_text_floors, exactly as --check does.
    Without it solve mode knows one flat P_min, so a TERRITORY hold -- a whole pane,
    judged on containment plus its heading -- comes back as an over-stuffed beat and
    exits 3; both goldens' own territory holds failed here while passing --check,
    so the solver could not express a hold the shipped work already contains. Where
    the gate waives the floor, k is solved from k_fit alone.
    """
    width, height = viewport
    bx, by, bw, bh = bbox
    if bw <= 0 or bh <= 0:
        raise ValueError("--bbox width and height must be positive")
    applies, reason = True, "hard floor"
    if gate is not None:
        p_min, applies, reason = floor_for(gate, viewport)
    k_fit = min((width - 2 * pad) / bw, (height - 2 * pad) / bh)
    k_read = p_min / fs_min if fs_min > 0 else 0.0
    # k_read is always REPORTED; it only CONSTRAINS where the floor is a hard gate.
    k_floor = k_read if applies else 0.0
    k_max = min(k_fit, k_cap)
    chosen = k_max if k is None else k
    cx, cy = center if center else (bx + bw / 2.0, by + bh / 2.0)
    tx = width / 2.0 - chosen * cx
    ty = height / 2.0 - chosen * cy
    status = "ok"
    if k_floor > k_max + 1e-9:
        status = "empty-interval"      # camera-beat.md: the beat is over-stuffed
    elif k is not None and not (k_floor - 1e-9 <= k <= k_max + 1e-9):
        status = "k-outside-interval"
    # PAD RELIEF, overview only. The commonest overview there is -- k=1 over the whole
    # canvas -- has k_fit just under 1 (the 40px pad eats ~3% of a 1920 frame), so solve
    # mode refused a hold that --check passes: --check measures containment at pad 0
    # because "the pad shapes a fresh framing, it is not a property of a transform
    # already chosen". Both frozen goldens hold exactly this shape. So when an overview
    # hold's own k puts the whole bbox inside the frame, solve mode agrees with --check
    # and says so, reporting how much of the requested pad actually survived. Scoped to
    # `overview` on purpose: a read beat that overflows its pad is a real defect, and a
    # territory beat still owes its pane heading room.
    pad_relief = None
    if status == "k-outside-interval" and gate == "overview" and k is not None and k > k_max:
        x0, y0, x1, y1 = frame(viewport, chosen, tx, ty)
        margins = {"left": bx - x0, "right": x1 - (bx + bw),
                   "top": by - y0, "bottom": y1 - (by + bh)}
        if all(value >= -1e-6 for value in margins.values()):
            status = "ok"
            pad_relief = {"pad_requested": pad,
                          "margins": {key: round(value, 3) for key, value in margins.items()},
                          "margin_min": round(min(margins.values()), 3)}
    # WHICH constraint decides the interval, so a caller repairing a hold knows what to
    # move. Reported, never enforced: it is a reading of the same three numbers below.
    if not applies:
        binding = "none"
    elif k_floor >= k_max - 1e-9:
        binding = "k_read"          # the floor itself is the ceiling: an over-stuffed beat
    else:
        binding = "kcap" if k_cap < k_fit else "k_fit"
    return {"status": status, "viewport": [width, height], "bbox": list(bbox),
            "pad_relief": pad_relief, "binding": binding, "fs_min_source": fs_min_source,
            "center": [round(cx, 4), round(cy, 4)], "pad": pad, "p_min": p_min,
            "fs_min": fs_min, "k_cap": k_cap,
            "gate": gate, "floor_applies": applies, "floor_reason": reason,
            "k_fit": round(k_fit, 4), "k_read": round(k_read, 4),
            "k_floor": round(k_floor, 4),
            "k_max": round(k_max, 4), "k": round(chosen, 4),
            "tx": _round(tx, precision), "ty": _round(ty, precision),
            "text_frame_px": round(chosen * fs_min, 2),
            "bound": "width" if (width - 2 * pad) / bw <= (height - 2 * pad) / bh else "height"}


def check(viewport, bbox, fs_min, k, tx, ty, pad=0.0, p_min=P_MIN_DEFAULT, gate=None):
    """Does an EXISTING transform hold? Containment and the text floor, reported apart.

    `gate` opts into the per-format/per-gate floor policy above: the floor VALUE comes
    from the frame's format and whether it is a hard gate comes from the hold's gate, so
    a territory or overview hold reports `N-A` instead of a floor it was never held to.
    Leaving `gate` None keeps the caller's own `p_min` and the original hard-floor
    behaviour -- no existing invocation changes meaning.
    """
    x0, y0, x1, y1 = frame(viewport, k, tx, ty)
    bx, by, bw, bh = bbox
    margins = {"left": bx - (x0 + pad), "right": (x1 - pad) - (bx + bw),
               "top": by - (y0 + pad), "bottom": (y1 - pad) - (by + bh)}
    contained = all(value >= -1e-6 for value in margins.values())
    applies, reason = True, "hard floor"
    if gate is not None:
        p_min, applies, reason = floor_for(gate, viewport)
    text_px = k * fs_min
    floor_ok = text_px >= p_min - 1e-9
    return {"containment": "PASS" if contained else "FAIL",
            "text_floor": "PASS" if floor_ok else "FAIL" if applies else "N-A",
            # In CHECK mode k is given, so the floor is the only constraint left to bind.
            "binding": "k_read" if applies else "none",
            "gate": gate, "floor_applies": applies, "floor_reason": reason,
            "frame_world": [round(v, 3) for v in (x0, y0, x1, y1)],
            "margins": {key: round(value, 3) for key, value in margins.items()},
            "text_frame_px": round(text_px, 2), "p_min": p_min,
            "k": k, "tx": tx, "ty": ty,
            "status": "ok" if contained and (floor_ok or not applies) else "fail"}


def fragment(result, hold_id, window):
    """The hold's entry for the output manifest (references/output-manifest.md)."""
    entry = {"id": hold_id or "hold", "kind": "camera",
             "k": result["k"], "tx": result["tx"], "ty": result["ty"],
             "center": result["center"], "bbox": result["bbox"],
             "fs_min": result["fs_min"], "p_min": result["p_min"]}
    if window:
        entry["window"] = window
    # Carry the gate through: verify-all reads exactly this key back.
    if result.get("gate"):
        entry["gate"] = result["gate"]
    # OPTIONAL (references/output-manifest.md): the text element that SET fs_min. Without
    # it a failing floor says "the smallest essential text is too small" and leaves the
    # author hunting for which text that is.
    if result.get("fs_min_source"):
        entry["fs_min_source"] = result["fs_min_source"]
    return entry


def _report(result, hold_id):
    width, height = result["viewport"]
    bx, by, bw, bh = result["bbox"]
    return "\n".join([
        f"hold        {hold_id or '(unnamed)'}",
        f"viewport    {width:g}x{height:g}   pad {result['pad']:g}   k cap {result['k_cap']:g}",
        f"bbox        {bx:g},{by:g}  {bw:g}x{bh:g}   center {result['center'][0]:g},{result['center'][1]:g}",
        f"k_read      {result['k_read']:g}   (P_min {result['p_min']:g} / fs_min {result['fs_min']:g})"
        + ("" if result["floor_applies"] else "   NOT binding"),
        f"gate        {result['gate'] or '(none, flat --pmin)'}   {result['floor_reason']}",
        f"k_fit       {result['k_fit']:g}   ({result['bound']}-bound)",
        f"binding     {result['binding']}"
        + (f"   fs_min from {result['fs_min_source']}" if result.get("fs_min_source") else ""),
        f"k           {result['k']:g}   -> essential text lands at {result['text_frame_px']:g} frame px",
        f"transform   translate({result['tx']}px,{result['ty']}px) scale({result['k']:g})",
        f"status      {result['status']}"]
        + ([f"pad relief  overview hold: k is above k_fit at pad {result['pad_relief']['pad_requested']:g}, "
            f"but the bbox is inside the frame at pad 0 -- tightest margin "
            f"{result['pad_relief']['margin_min']:g}px  {result['pad_relief']['margins']}"]
           if result.get("pad_relief") else []))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--viewport", required=True, help="W,H or WxH of the SVG viewBox")
    ap.add_argument("--bbox", required=True, help="must-show box: X,Y,W,H in world units")
    ap.add_argument("--fs-min", type=float, required=True,
                    help="smallest ESSENTIAL text in the frame, world px")
    ap.add_argument("--pad", type=float, default=PAD_DEFAULT)
    ap.add_argument("--pmin", type=float, default=P_MIN_DEFAULT)
    ap.add_argument("--kcap", type=float, default=K_CAP_DEFAULT)
    ap.add_argument("--k", type=float, help="pin k instead of solving for it")
    ap.add_argument("--center", help="CX,CY override; default is the bbox centre")
    ap.add_argument("--precision", type=int, default=0, help="decimals on tx/ty (default 0)")
    ap.add_argument("--fs-min-source", help="LABEL of the text element that set --fs-min; "
                                            "copied into the manifest fragment (optional)")
    ap.add_argument("--id", dest="hold_id", help="hold id for the manifest fragment")
    ap.add_argument("--window", help="A,B percent window, copied into the fragment")
    ap.add_argument("--check", dest="do_check", action="store_true")
    ap.add_argument("--gate", choices=sorted(GATE_FLOOR_APPLIES),
                    help="apply the per-format/per-gate floor policy instead of --pmin "
                         "(read|territory|overview, from the manifest hold). Valid in BOTH "
                         "modes: in solve mode a territory/overview hold is framed from k_fit "
                         "alone, which is the only way to express a hold both goldens contain")
    ap.add_argument("--transform", help="--check only: K,TX,TY of the built cut")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    try:
        viewport = _nums(args.viewport, 2, "viewport")
        bbox = _nums(args.bbox, 4, "bbox")
        window = _nums(args.window, 2, "window") if args.window else None
        if args.do_check:
            if not args.transform:
                raise ValueError("--check needs --transform K,TX,TY")
            k, tx, ty = _nums(args.transform, 3, "transform")
            # containment is "inside the frame at all"; --pad shapes the SOLVE, not
            # the check -- an author who pulled the camera back on purpose still passes,
            # and the reported margins say how much slack is left on each side.
            out = check(viewport, bbox, args.fs_min, k, tx, ty, 0.0, args.pmin, args.gate)
            print(json.dumps(out, indent=2) if args.json else
                  f"containment {out['containment']}   margins {out['margins']}\n"
                  f"text-floor  {out['text_floor']}   {out['text_frame_px']:g} frame px "
                  f"vs P_min {out['p_min']:g}   ({out['floor_reason']})\n"
                  f"status      {out['status']}")
            return 0 if out["status"] == "ok" else 3
        result = solve(viewport, bbox, args.fs_min, args.pad, args.pmin, args.kcap,
                       args.k, _nums(args.center, 2, "center") if args.center else None,
                       args.precision, args.gate, args.fs_min_source)
    except ValueError as exc:
        print(f"BAD INPUT: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({**result, "manifest": fragment(result, args.hold_id, window)}, indent=2))
    else:
        print(_report(result, args.hold_id))
        print("manifest    " + json.dumps(fragment(result, args.hold_id, window)))
    if result["status"] == "empty-interval":
        print("The beat is over-stuffed: k_read > min(k_fit, cap). camera-beat.md is explicit "
              "-- fix the geometry (restack, let the upstream node peek, or split the beat). "
              "Never resolve it by zooming out.", file=sys.stderr)
        if args.gate is None:
            print("If this is an orientation beat over a whole pane/tier it is a TERRITORY "
                  "hold, not an over-stuffed read beat -- re-run with `--gate territory` "
                  "(or `--gate overview`).", file=sys.stderr)
    return 0 if result["status"] == "ok" else 3


if __name__ == "__main__":
    sys.exit(main())
