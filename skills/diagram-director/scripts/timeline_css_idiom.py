#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The CSS shape of a camera-beat window, one function per window kind.

Split out of emit_timeline.py on a real boundary: that module answers "what may
the sheet's event table say", this one answers "what does a window of this kind
look like as `@keyframes`". These four functions ARE the idiom -- the same blocks
`templates/snippets/camera-beat.css` distils from the two frozen goldens
(cb-stage-window, cb-act-recap, cb-caption-card) -- so changing a fade shape here
changes it in exactly one place, and tests/run_golden_regression.py catches it.

Every input is already a percent of the master. No parsing, no defaults, no I/O.
"""

EPS_GUARD = 0.01        # act park/unpark guard stop; keeps the parked pose off the fade
# The caption wipe's three poses. Both parked poses are ZERO-AREA and sit OUTSIDE
# the card body (100% past its left edge, 101% past its right), so a parked clip
# can never leave an antialiased sliver on the card's own border.
PARKED_LEFT = "inset(-6% 100% -6% -1%)"     # before: clipped away to the LEFT
OPEN = "inset(-6% -1% -6% -1%)"             # during: fully revealed
PARKED_RIGHT = "inset(-6% -1% -6% 101%)"    # after: swept off to the RIGHT
EASE = "animation-timing-function:ease-in-out"


def pct(value):
    """One rounding, at the end: 4dp, trailing zeros dropped (house format)."""
    text = f"{round(value, 4):.4f}".rstrip("0").rstrip(".")
    return text if text else "0"


def seg(start, end, decl):
    """One keyframe segment; a zero-length span collapses to a single stop."""
    stops = pct(start) + "%" if abs(end - start) < 1e-9 else f"{pct(start)}%,{pct(end)}%"
    return stops + "{" + decl + "}"


def opacity_windows(wins):
    """state / spotlight / traffic: hidden outside its windows, fading at the edges.

    wins is [(start, end, lead, tail), ...], sorted and non-overlapping. A window
    starting at 0 needs no fade-in, and a fade-out past 100 clamps to a bare 100%
    stop -- which is how a window that runs to the loop seam closes the seam.
    """
    out = []
    if wins[0][0] > 0:
        out.append(seg(0.0, max(wins[0][0] - wins[0][2], 0.0), "opacity:0"))
    for i, (start, end, _lead, tail) in enumerate(wins):
        out.append(seg(start, end, "opacity:1"))
        if end >= 100:
            break
        fade_out = end + tail
        if fade_out >= 100:
            out.append(seg(100.0, 100.0, "opacity:0"))
            break
        nxt = 100.0 if i + 1 == len(wins) else max(wins[i + 1][0] - wins[i + 1][2], fade_out)
        out.append(seg(fade_out, nxt, "opacity:0"))
    return "".join(out)


def act_windows(wins, park, seam=None):
    """act: the same windows, plus the off-canvas park pose between them.

    An act that is merely transparent still occupies the canvas, so between its
    windows it is TRANSLATED away and only un-parked EPS_GUARD before its fade-in.
    `seam` (a fade-out duration) applies when the act's last window runs to 100%:
    it is the act the loop parks on, so it is still lit at 0%.
    """
    out, park_decl = [], f"opacity:0;transform:{park}"
    live, dark = "opacity:1;transform:none", "opacity:0;transform:none"
    park_from = 0.0
    if seam is not None and wins[-1][1] >= 100 and wins[0][0] > 0:
        out.append(seg(0.0, 0.0, live))
        out.append(seg(seam, seam, dark))
        park_from = seam + EPS_GUARD
    for i, (start, end, lead, tail) in enumerate(wins):
        unpark = start - lead
        out.append(seg(park_from, unpark - EPS_GUARD, park_decl))
        out.append(seg(unpark, unpark, dark))
        out.append(seg(start, end, live))
        if end >= 100:
            break
        fade_out = end + tail
        out.append(seg(fade_out, fade_out, dark))
        park_from = fade_out + EPS_GUARD
        if i + 1 == len(wins):
            out.append(seg(park_from, 100.0, park_decl))
    return "".join(out)


def caption_window(start, end, tail, wipe):
    """caption: one property, three stops -- a clip-only wipe IN, hold, wipe OUT.

    `opacity` is NOT here, and that is the whole point. It used to be: the legacy
    block snapped opacity 0 -> 1 an epsilon before the wipe and faded it back at the
    end, so the card was hidden by TRANSPARENCY between beats while its clip sat
    parked OPEN. opacity is a COMPOSITOR property and clip-path is a PAINT one, so
    on the frame opacity left 0 a compositor that had evicted the long-invisible
    layer's tiles could present the stale OPEN raster -- the whole card, for one
    frame -- before the fresh clipped raster committed. Pass 1 was always clean
    (no stale tile had ever existed); every pass after it could blink. Diagnosed
    and fixed on the process golden, 2026-08-27 (its sheet, deviation 24;
    plans/reports/builder-260826-2330-process-full-build.md revisions 3.2/3.2a).

    So: `opacity` is a constant 1 on the base rule and never appears in a keyframe,
    and the card is hidden by GEOMETRY at all times. There is no "becomes visible
    again" event left for a compositor to serve a stale tile into. Both parked poses
    are zero-area and outside the card body, and the base `clip-path` is the closed
    one, so a cut whose keyframes never apply hides every caption rather than
    showing them all.

    Consequences worth stating, because they are visible: the EXIT is now a
    same-direction wipe-out (the sentence is swept away the way it arrived) instead
    of a fade, and the two spans carry `ease-in-out` so the wipe accelerates and
    settles instead of running at one linear rate.
    """
    return "".join([
        seg(0.0, start, f"clip-path:{PARKED_LEFT};{EASE}"),
        seg(start + wipe, end, f"clip-path:{OPEN};{EASE}"),
        seg(end + tail, 100.0, f"clip-path:{PARKED_RIGHT}")])
