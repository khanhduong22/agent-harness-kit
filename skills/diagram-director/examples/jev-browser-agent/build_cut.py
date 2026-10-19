#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generator for jev-browser-agent-9x16: one coordinate table -> HTML + timeline TSV + manifest.

Two acts on one master timeline: ACT 1 is a browser agent whose next action is WRITTEN by a text
LLM, ACT 2 is the same task with Jev CHOOSING the action from the page's own indexed controls.
Every string here is copied from jev-browser-agent-9x16.sheet.md (the single source of truth).
Geometry is derived from the node table so edges and spotlight brackets cannot drift from the
boxes they attach to. Windows come from emit_timeline.py and camera poses from solve_camera.py --
nothing on the master timeline is hand-computed.

Adapted from ../jev-decision-agent/build_cut.py (the same-day cut this one inherits its idiom
from: title beat `t0` on a native SVG frosted pane, frame-centred cast, spotlight brackets over a
paper veil with a bracket-sized window, clamped focus, glyph-left ML rows, hero treatment, act
crossfade + recap, legend drawn with the final act).

TWO THINGS THIS CUT DOES DIFFERENTLY, both forced and both measured (see the sheet's Build facts):

1. NO STRING WIDTH IS ESTIMATED. The morning cut approximated Inter with `len(s) * fs * 0.49`.
   This cut's cast carries long literal strings (an element table, a JSON object, an operation
   list) where a 5% error is a text overflow, so every string's advance was measured once in the
   browser at fs=100 (advance is linear in size) and lives in MEASURED below. `tw()` refuses a
   string that was never measured, so a new string cannot be sized by guesswork.

2. THE SPINE IS OFF-CENTRE (x=590 against a cast centred on x=525). A caption card at the vertical
   read floor is ~75% of the safe width, so in a single-column cut a card in the gap ALWAYS covers
   the vertical edge running through that gap -- and for every beat here that edge is anchored on
   the beat's own subject, which `verify-caption-occlusion` fails outright. Solved by moving the
   flow to the cards' right shoulder: every read card's right edge is CARD_R, 8 world px left of
   the spine's painted band, and the cast stays centred on the frame.

Run from the repository root:
    python3 diagram-director/examples/jev-browser-agent/build_cut.py
    # then serve this folder, re-bake the caption boxes, pad the title card, make the play copy:
    #   node .../rebake-caption-boxes.mjs --base http://localhost:<port> <cut>.html
    #   python3 .../build_cut.py --pad-title-card
    #   python3 .../build_cut.py --make-play
    # then: python3 diagram-director/scripts/verify_all.py <cut>.html --serve --target local --json
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "scripts"
NAME = "jev-browser-agent-9x16"

W, H = 1080, 1920
SAFE = (60, 150, 890, 1540)                    # x0, y0, x1, y1 -- worst case of Reels/Shorts/TikTok
SAFE_CX, SAFE_CY = (SAFE[0] + SAFE[2]) / 2, (SAFE[1] + SAFE[3]) / 2
BEAT_MS = 4800                                 # the house beat: one slot for b1..b12
GRID_MS = 2400                                 # t0 is HALF a beat, so 2400 -- not 4800 -- is the
                                               # grid every slot boundary of this cut sits on
# ---- the opening title slot `t0` (camera-beat.md -> Opening title beat) -------------------
TITLE_MS = 2400
TITLE_HOLD_MS = 2000
TITLE_OUT_MS = 400
TITLE_FS = 52                                  # the DISPLAY line (line 2), frame px
TITLE_EYEBROW_FS = 44                          # line 1, the eyebrow -- the 9:16 floor exactly
TITLE_LINE_EM = 1.4                            # baseline-to-baseline, in the DISPLAY line's em
TITLE_CY = 900                                 # the card's centre: the diagram's body
TITLE_PAD_X, TITLE_PAD_Y = 48, 34              # display padding, the packet's floors are 48 / 32
REBAKE_PAD_X, REBAKE_PAD_Y = 14, 8             # browser-checks/rebake-caption-boxes.mjs
TITLE_X_BOUND = (80, 1000)                     # the padded card must stay inside this
# FROSTED GLASS, as a NATIVE SVG filter on a dedicated backdrop group -- never a CSS `filter:`
# on the scene. WebKit does not apply CSS filter functions to elements inside an <svg>, so the
# CSS form renders in Chrome (every gate, the contact sheet, the exporter) and silently does
# nothing in Safari, where the user reviews. Values carried over from the morning cut's review.
FROST_STD = 130
FROST_SATURATE = 6
FROST_REGION = (-400, -400, 1880, 2720)
FROST_ACT = 1
WASH_OPACITY = "0.2"
LABEL_LEAD_MS = 100                            # edge labels come back with the sharp frame

P_MIN = 28                                     # vertical essential-text floor, frame px

# ---- SCALE: the cast is drawn at 1.32x so `transform: none` already fills the frame -------
# Controller review of the first contact sheet: at every `overview` hold the cast column spanned
# ~300 world px of a 1080 frame -- 28 % -- with the rest paper, the same class the user flagged
# on the morning cut. Of the two legal fixes, this is the one that leaves the TITLE BEAT
# UNTOUCHED: giving the overview holds a computed `k_fit` would scale the title card with the
# camera (it lives inside `.camera`), so its 52 px display line, its measured display padding
# and its x 80…1000 bound would all have to be re-derived through k, and the frosted backdrop
# would composite under a moving camera at the very dissolve it exists to avoid. Scaling the
# WORLD instead keeps every overview hold at k=1, so t0 is bit-for-bit the beat that was
# reviewed.
#
# S is the largest scale that still fits three things at once: the cast's 595-unit horizontal
# span inside the 830 px safe band, its 844-unit vertical span between the subtitle and the
# overview caption band, and that caption card itself (fs is pinned to 28 frame px at k=1, so
# it is 86 world px tall and does NOT shrink with the cast).
S = 1.30


def sc(v):
    return v * S


# Sizes INSIDE a node group stay in local units: every node is emitted as
# `translate(x,y) scale(S)`, so its own drawing code, its glyph geometry and its font sizes are
# unchanged from the reviewed build and scale together for free.
LABEL_FS = 16                                  # node label (local): the essential text
SUB_FS = 13                                    # node sub (local)
SUP_LABEL_FS, SUP_SUB_FS = 14, 11              # supporting tier: one size step down
ROW_FS = 11                                    # page / page-state interior rows (texture class)
BADGE_FS = 11
JSON_FS = 11                                   # the LLM's detail face (mono)
BARS_FS, BARS_LBL_FS = 10.5, 10                # Jev's detail face
TAG_FS = 9                                     # the `example values` tag, muted, on the heading row
# TWO lines per control, as rounds 1-3 drew them: `[n] role` over its value. The round-4 WIP had
# folded them onto one line to buy column height for a b5/b11 that bracketed `page` AND
# `actions` together; the controller's ruling makes the page a PEEK there, which gives the
# height back, so the rows stay legible (measured below). Pitch 28 / box 26 is the round-3
# 34 / 30 compressed by the one step the five-row column can afford: at 11px the second line's
# ink reaches 25.4 of the 26-tall field and the first line's starts at 3.1.
CTL_PITCH, CTL_BOX_H = 28, 26                  # one control per 28, its field 26 tall
STATE_PITCH = 26
# Sizes in WORLD space scale explicitly, so they render at the same frame px they did before.
EDGE_FS = sc(13)
TRUNK_HALF = sc(9)                             # veil window either side of a lit edge's centreline
FOCUS_PAD, FOCUS_ARM, FOCUS_SW = sc(12), sc(22), sc(3)   # camera-beat.md's 12 / 22 / 3, scaled
AIR, BRK = sc(8), sc(14)                       # solver margins: plain node, bracketed subject

# ---- layout grid (every offset is a local unit through `sc`) ------------------------------
# The whole cast is centred on the SAFE BAND (x 475), not on the frame: its branches are
# asymmetric -- the text helper and the stale loop both hang left of the column while only the
# return trunk goes right -- so centring the column itself would push the stale trunk off the
# canvas. The heading and the legend stay centred on the FRAME at x=540.
# 200, not 202: at 202 the act-1 return trunk sat 20 frame px off b3's RIGHT frame edge
# against camera-beat.md's 24 (measured). Each unit taken off CAST_R also moves CX right by
# half a unit, so the trunk's own clearance to `state + questions` falls 1 unit per unit --
# 200 leaves the trunk 19.9 world px clear of that label and 25 frame px inside b3's frame.
# CAST_R is pinned from BOTH sides. Above it, b2/b7 have the narrowest bbox of any read hold
# (the page and the page state are the slimmest spine nodes), so their frame reaches only
# `bbox_right + 166/k` and the return trunk must stay inside it: CAST_R <= 188.5. Below it,
# the trunk owes `state + questions` 14 local of clearance. At 200 the trunk sat 11.2 frame px
# inside b8's frame and at 192 it sat 16.4 inside b2's, both against a required 24; 186 clears
# b2/b7 by 5.9 frame px over that, and the label still fits because it takes two lines now.
# Round 4 keeps 186: the `actions` strip is 260 local wide (130 either side of CX), so it still
# leaves the return trunk 72.8 world px of lane, and CAST_R is the one number b2/b7's frame
# margin is measured against.
CAST_L, CAST_R = 415, 186                      # local span of the cast, left and right of CX
CX = round(475 + sc((CAST_L - CAST_R) / 2))    # 624: the column's centre
# SPINE_X is pinned between two measured walls. Pushing it LEFT narrows every read card (the
# card ends 8 units short of it) until b5's shot -- the only one that must also hold the return
# trunk -- drops under the read floor. Pushing it RIGHT walks the spine's own edge labels into
# that trunk: `state + questions` is 105.9 local units at 13 and starts 8 right of the spine.
SPINE_X = CX + sc(71)                          # the vertical flow, on the cards' right shoulder
CARD_R = SPINE_X - sc(8)                       # every read caption card ends here
RETURN_X = CX + sc(CAST_R)                     # the loop's return trunk, right
# The stale trunk sits 3 local INSIDE the cast's left extreme. Measured: at CAST_L exactly it
# ran 23.4 frame px off b9's LEFT frame edge against camera-beat.md's 24, and b9 cannot buy
# the room by widening its bbox (it is the tightest read hold in the cut). CAST_L keeps its
# value so the centring is unchanged; the cost is that the cast sits 1.5 local left of the
# safe band's true centre.
STALE_INSET = 3
STALE_X = CX - sc(CAST_L - STALE_INSET)        # act 2's `stale -> re-observe` trunk, left
# The gap between Jev and the text helper is 96 local, not the 40 floor. It carries two things
# that both need clear air: `text?` rides that edge, and the latency chip hangs off Jev's left
# border into the same lane. 96 is the largest value b10's read floor allows (its span is
# `375 + gap` local against a 472.7 ceiling once the text helper is a peek bound), and it
# leaves the chip's own spotlight bracket 6.6 world px clear of the text helper.
GAP_TEXT_HELPER = 96
ROW_TOP = 240
# FIVE rows: page / page state / LLM-Jev / executor-validator / actions. Two things pay for the
# new row without anything going under a floor.
#
#   1. The two morphs are now IN-NODE detail faces -- camera-beat.md's canonical morph ("both
#      faces live in the node group"), and what CHROME STRINGS always called them ("interior of
#      the LLM", "interior of Jev"). Rounds 1-3 drew them as world-space panels in the gap under
#      the node, which cost that gap 138 local; the gap is now a caption gap like any other.
#      The `example values` tag also moved onto the `operation` heading row, saving a text line.
#      Measured alternative, rejected: `"action": [{"input": {"index": 2, ...}}]` on ONE line is
#      240.8 local at 11px mono against a 218 inner width, so it keeps its two-line wrap.
#   2. b5/b11 bracket `actions` ALONE and hold `page` as a PEEK at 80 % (controller ruling in
#      the sheet's DEVIATIONS), so the column's read-gate budget is
#      `0.8*PAGE_H + everything below it`, not the whole column -- and the control rows keep
#      their two lines.
#
# Each of the three lower gaps carries a caption card, so each is sized
# `card offset + tallest card at that gap's k + the bracket pad of the subject under it`.
# Gap 1 carries no card (b2/b7's card hangs BELOW its subject, in gap 2) and only has to seat
# the `read` / `snapshot` label.
PAGE_H, STATE_H, DECIDE_H, ROW_H, ACT_H = 142, 124, 84, 78, 88
LOCAL_BANDS = [(PAGE_H, 40), (STATE_H, 82), (DECIDE_H, 82), (ROW_H, 85), (ACT_H, 0)]
BANDS = []
_y = ROW_TOP
for _h, _g in LOCAL_BANDS:
    BANDS.append((_y, sc(_h)))
    _y += sc(_h) + sc(_g)
# Every read card's top, measured into its own gap. Gap 3 takes a smaller offset because
# nothing is bracketed above it and b10's card is the tallest in the cut; gap 4 keeps the
# full 16 because the stale return's run crosses that gap 15.6 world px down and the card
# may not cover it.
CARD_OFF = {1: sc(16), 2: sc(16), 3: sc(10), 4: sc(16)}
# The return trunk now leaves the ACTIONS strip (sheet: "the return trunk leaves from the
# actions strip"), so its foot is 36 local under row 5 rather than 64 under row 4 -- the
# bottom band below it is unchanged from round 3 and still holds card, legend and footer.
RETURN_Y = BANDS[4][0] + BANDS[4][1] + sc(36)  # the return edge's foot
# The stale return leaves the validator's foot into gap 4, ABOVE the b5/b11 caption card that
# shares the gap (the card's top is CARD_OFF = 16 local down, the run sits at 12) and its label
# rides ABOVE the run and LEFT-anchored on the trunk, where the card's left edge (which starts
# at x~310 at b11's zoom) can never reach it.
STALE_Y = BANDS[3][0] + BANDS[3][1] + sc(12)
# ---- latency chips: one pill on the deciding node of each act, always on with that act ----
# Local units like a node, but drawn in WORLD space as a sibling of the node groups: a chip is
# the one node mark that deliberately hangs off the border, and `verify-text-containment`
# sweep 1 holds every <text> inside a `g.node` to that node's shape box with no chip exemption
# (the morning cut measured an in-node pill failing it by 83 px). Sweep 2 then forbids foreign
# text OVER a node shape, so the pill may overlap the border but its text may not -- which is
# what CHIP_PAD_R buys: the text ends 6 local units clear of the node's left edge.
#
# Two lines, because one will not fit. The lane between the text helper and Jev is 96 local
# and the pill's own bracket has to stay out of the text helper; that caps the pill at 82
# local, and `~70-500 ms / step` is 8.99 local units of advance per px of size -- a single
# line would need a 6 px face. Split, the widest line is 6.00/px, so 10 px fits with room.
# The join rides a trailing space on line 1, so `textContent` is the sheet's string exactly.
CHIP_FS = 10                                   # local
CHIP_PAD_L, CHIP_PAD_R, CHIP_PAD_Y = 10, 12, 3
# 4, measured: at 6 the pill's right edge came within 4.0 world px of the glyph's ink. At 4 it
# keeps 6.6, still reads as seated on the border, and the text clears the node's shape by 10.5.
CHIP_OVERLAP = 4                               # how far the pill sits ON the node's left border
CHIP_TOP_OFF = 2                               # below the node's own top edge
CHIPS = {"llm": ["est. ~2\u20135 s", "/ step"], "jev": ["~70\u2013500 ms", "/ step"]}


def chip_local_size(nid):
    w = max(tw(t, CHIP_FS, 600) for t in CHIPS[nid]) + CHIP_PAD_L + CHIP_PAD_R
    return w, len(CHIPS[nid]) * CHIP_FS * LINE_H + 2 * CHIP_PAD_Y


def chip_box(nid):
    """The chip's WORLD box: hung off the node's LEFT border, inside its own vertical span."""
    lw, lh = chip_local_size(nid)
    x1 = left(nid) + sc(CHIP_OVERLAP)
    y0 = top(nid) + sc(CHIP_TOP_OFF)
    return (x1 - sc(lw), y0, sc(lw), sc(lh))


def chip_svg(nid, act):
    lw, lh = chip_local_size(nid)
    x, y, _w, _h = chip_box(nid)
    n = N[nid]
    cls = "chip" + (" chip--hero" if n["hero"] else "")
    out = [f'        <g class="{cls}" data-role="{n["role"]}" aria-hidden="true" '
           f'transform="translate({f(x)},{f(y)}) scale({S:g})">',
           f'          <rect class="chip__box" x="0" y="0" width="{f(lw)}" height="{f(lh)}" '
           f'rx="{f(lh / 2)}" ry="{f(lh / 2)}" />']
    spans = "".join(
        f'<tspan x="{CHIP_PAD_L}" dy="{0 if i == 0 else LINE_H}em">{esc(t)}'
        f'{" " if i < len(CHIPS[nid]) - 1 else ""}</tspan>'
        for i, t in enumerate(CHIPS[nid]))
    out.append(f'          <text class="chip__text" x="{CHIP_PAD_L}" '
               f'y="{f(CHIP_PAD_Y + CHIP_FS * 0.98)}" xml:space="preserve">{spans}</text>')
    out.append("        </g>")
    return "\n".join(out)


# ---- chrome, in frame units (it is read at k=1 and never scales with the cast) ------------
TITLE_Y, TITLE_CHROME_FS = 184, 40
SUBTITLE_Y, SUBTITLE_FS = 218, 22
# The bottom band now stacks four things between the return edge's foot label (ink ends 1358.2)
# and the safe bottom at 1540, all measured on the baked boxes: the overview caption card
# 1370..1454.8, the legend's ink 1467..1486, the footer's ink 1495..1512. Gaps 11.8 / 12.2 /
# 9 / 28. The legend had to move up 44 px from where round 2 left it to make the room.
LEGEND_Y, LEGEND_FS, LEGEND_SWATCH = 1478, 15, 16
FOOTER_Y, FOOTER_FS = 1506, 14
FOOTER = "Diagram m\u00f4 ph\u1ecfng theo repo GitHub github.com/browser-use/jev-ultrafast"
# 1370: the baked overview card runs from here for 84.8 px, so it clears the return edge's
# foot label above it by 11.8 and the legend's ink below it by 12.2.
OVERVIEW_BAND_Y = 1370                         # the overview caption band, under the cast


def band(r):
    return BANDS[r - 1]


def gap_top(r):                                # top of the free band under row r
    y, h = band(r)
    return y + h


# ---- measured string advances (width per 1px of font-size) --------------------------------
# Measured once in the browser at font-size 100 with the cut's own font stack
# (Inter 400/500/600 from Google Fonts, and the system mono stack for the JSON card), then
# divided by 100. Advance is linear in size -- checked by measuring the same run at 12, 13 and
# 14 px and getting an identical ratio. `s`/`m` = sans/mono, then the weight.
MEASURED = {
    "s400|Zurich → London · one-way": 13.0494,
    "s400|DOM tree · indexed · screenshot": 15.2116,
    "s400|element table · atomic snapshot": 15.0358,
    "s400|thinking ·": 4.3159,
    "s400|next_goal · action": 8.2695,
    "s400|parse JSON → check → run": 13.0436,
    "s400|operation? target? ·": 9.1427,
    "s400|one round trip": 6.6578,
    "s400|fresh? visible? not occluded?": 13.7222,
    "s400|only for TYPE_TEXT": 9.3966,
    "s400|read": 2.1266,
    "s400|prompt": 3.3873,
    "s400|JSON": 2.7305,
    "s400|click · input": 5.3902,
    "s400|× N steps": 4.5459,
    "s400|snapshot": 4.3384,
    "s400|state + questions": 8.1480,
    "s400|state +": 3.2647,
    "s400|questions": 4.6022,
    "s400|text?": 2.2819,
    's400|{"text": "Zurich"}': 8.0670,
    "s400|TYPE_TEXT [2]": 7.1383,
    "s400|type · wait ≤ 200 ms": 9.6275,
    "s400|next step": 4.3658,
    "s400|stale → re-observe": 8.9581,
    "s400|button": 3.0386,
    "s400|combobox": 4.9942,
    "s400|Change ticket type · Round trip": 14.6367,
    "s400|Where from? · San Francisco": 13.6284,
    "s400|Where to? · empty": 8.6427,
    "s400|CLICK · TYPE_TEXT ✓ ·": 11.0519,
    "s400|SELECT · SCROLL": 8.5469,
    "s400|[1] · [2] ✓ · [3]": 6.6714,
    "s400|act 1 · a text LLM writes the next action": 18.3653,
    "s400|act 2 · Jev picks it from the page's own controls": 22.6475,
    "s400|client ×1 ": 4.1875,
    "s400|data ×1 ": 3.6983,
    "s400|service ×3 ": 5.3033,
    "s400|page": 2.3800,
    "s400|page state": 4.9830,
    "s400|Jev · text helper · validator": 12.5078,
    "s500|operation": 4.5573,
    "s500|target": 2.8273,
    "s500|[1]": 1.1588,
    "s500|[2]": 1.3542,
    "s500|[3]": 1.3647,
    "s600|Google Flights": 6.9403,
    "s600|page state": 5.0936,
    "s600|LLM": 2.0533,
    "s600|executor": 4.2541,
    "s600|Jev": 1.7400,
    "s600|validator": 4.2239,
    "s600|text helper": 5.1816,
    "s600|Browser agent: LLM vs Jev": 13.0170,
    "s600|actions": 3.5417,
    "s400|runs the named tool": 9.4141,
    "s400|runs the picked operation": 12.0719,
    "s400|run": 1.5586,
    "s400|click": 2.1758,
    "s400|input": 2.3639,
    "s400|scroll": 2.5430,
    "s400|CLICK": 2.9669,
    "s400|TYPE_TEXT": 5.5177,
    "s400|SCROLL": 3.9113,
    "s400|Zurich": 3.0113,
    "s400|Zurich|": 3.3438,
    "s400|example values": 7.3258,
    "s400|button Change ticket type \u00b7 Round trip": 17.9566,
    "s400|Where from? \u00b7 ": 6.9513,
    "s400|San Francisco": 6.6773,
    "s400|service \u00d74 ": 5.3316,
    "s400|Jev \u00b7 text helper \u00b7 validator \u00b7 actions": 16.7789,
    "s400|CLICK 9% \u00b7 TYPE_TEXT 84% \u2713 \u00b7 ": 15.7442,
    "s400|SELECT 4% \u00b7 SCROLL 3%": 12.3370,
    "s400|[1] 5% \u00b7 [2] 91% \u2713 \u00b7 [3] 4%": 12.7272,
    "s600|est. ~2\u20135 s": 5.2283,
    "s600|~70\u2013500 ms": 6.0002,
    "s600|/ step": 2.7394,
    "s400|Diagram m\u00f4 ph\u1ecfng theo repo GitHub github.com/browser-use/jev-ultrafast": 35.3288,
    "s600|Agent điều khiển browser": 12.3564,
    "s600|LLM viết action · Jev chọn action": 15.8155,
    "s600|Mục tiêu: tìm chuyến bay Zürich → London.": 20.9155,
    "s600|Agent phải tự bấm trên trang, từng bước một.": 21.7389,
    "s600|Mỗi bước, code đọc cây DOM thành danh sách": 22.4459,
    "s600|element có đánh số, kèm screenshot khi cần.": 21.7291,
    "s600|LLM nhận cả trang làm prompt, rồi sinh": 18.7577,
    "s600|JSON từng token: thinking, next_goal, action.": 21.7609,
    "s600|Action chỉ là text JSON: code phải parse,": 19.6573,
    "s600|rồi tự kiểm tra xem element còn trên trang.": 20.4656,
    "s600|Bấm xong lại đọc trang, lặp N bước —": 17.9847,
    "s600|bước nào cũng phải chờ LLM sinh chữ.": 18.5714,
    "s600|Với Jev: cùng trang, cùng mục tiêu,": 17.1131,
    "s600|nhưng model chỉ chọn, không sinh text.": 19.0084,
    "s600|Một lần gọi browser đọc hết control đang hiện:": 22.4183,
    "s600|tên, giá trị, text — không cần screenshot.": 19.7716,
    "s600|Jev trả lời hai câu hỏi trong một round trip:": 20.3989,
    "s600|làm gì, với element nào — kèm xác suất.": 19.2575,
    "s600|Chỉ với TYPE_TEXT, một LLM nhỏ mới viết": 20.0580,
    "s600|chữ cần gõ — và phải ra đúng JSON.": 17.5959,
    "s600|Trước khi gõ, code kiểm tra: trang còn mới,": 20.6334,
    "s600|element còn hiện, không bị che.": 15.3575,
    "s600|Gõ Zurich, đợi gợi ý tối đa 200 ms,": 16.5022,
    "s600|rồi đọc trang tiếp — cả task 7,1 giây.": 17.1038,
    "s600|LLM thì viết câu trả lời, code phải parse.": 19.1645,
    "s600|Jev chỉ chọn trong menu trang, kèm xác suất.": 21.9380,
    'm400|"thinking": "…"': 9.0308,
    'm400|"next_goal": "…"': 9.6328,
    'm400|"action": [{"input": ': 12.6431,
    'm400|{"index": 2, …}}]': 10.2350,
}


def tw(text, fs, weight=400, mono=False):
    """Measured advance of `text` at `fs`. A string nobody measured is a build failure --
    this cut sizes cards and panels off these numbers, so an estimate would be a silent
    overflow rather than a visible one."""
    key = f"{'m' if mono else 's'}{weight}|{text}"
    if key not in MEASURED:
        sys.exit(f"tw: {key!r} was never measured -- re-run the measurement probe and add it")
    return MEASURED[key] * fs


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


# ---- the cast --------------------------------------------------------------------------
# `sub` may be {act: text} when the same component says something else per act, and a LIST when
# the sheet's one string is set on two lines (the rendered textContent is the sheet's string,
# joined by a single space -- the same idiom the caption cards use for their own line breaks).
def node(nid, comp, role, shape, r, w, h, label, sub, title, acts=(1, 2), dx=0,
         sup=False, hero=False, tight_sub=False):
    """`w`/`h` are LOCAL units -- the node group is emitted at `scale(S)`, so its own drawing
    code never sees the cast's scale. `w`/`h` on the returned dict are WORLD, because every
    edge, bracket and camera bbox in this file is computed in world space."""
    y, bh = band(r)
    return dict(id=nid, comp=comp, role=role, shape=shape, x=CX - sc(w) / 2 + sc(dx),
                y=y + (bh - sc(h)) / 2, w=sc(w), h=sc(h), lw=w, lh=h,
                label=label, sub=sub, title=title,
                acts=acts, sup=sup, hero=hero, tight_sub=tight_sub, row=r)


# J3's element table, verbatim (sheet CHROME STRINGS). Drawn as the page's three controls with
# index badges, and as the page state's three table rows -- one string set, two presentations.
CONTROLS = [("[1]", "button", "Change ticket type · Round trip"),
            ("[2]", "combobox", "Where from? · San Francisco"),
            ("[3]", "combobox", "Where to? · empty")]

# The text helper's return drops from its own foot, 30 local in from its left edge, which is
# what keeps it left of b10's caption card. The stale return leaves the validator's foot 55
# local left of the column centre, so it does not share the left vertex with that return.
TEXT_ASK_Y = 0.0                               # set once the node table exists
TEXT_BACK_X = CX - sc(115 + GAP_TEXT_HELPER + 170 - 30)
STALE_FOOT_X = CX - sc(55)

NODES = [
    node("page", "browser", "client", "device", 1, 210, PAGE_H, "Google Flights",
         "Zurich → London · one-way",
         "Google Flights — the page the agent works on: the goal is one-way Zurich to London, "
         "and its three controls carry the indices [1], [2] and [3]"),
    node("page-state", None, "data", "state-card", 2, 210, STATE_H, "page state",
         {1: "DOM tree · indexed · screenshot", 2: "element table · atomic snapshot"},
         {1: "page state — the DOM tree serialised as indexed text for the prompt, plus a "
             "screenshot when vision is on",
          2: "page state — one atomic snapshot: an indexed table of the visible controls with "
             "their names, values and text, read in one browser call, no screenshot"},
         tight_sub=True),
    node("llm", "text-llm", "service", "llm", 3, 230, DECIDE_H, "LLM",
         ["thinking ·", "next_goal · action"],
         "LLM — a text model that receives the whole page state as its prompt and generates, "
         "token by token, a JSON with thinking, next_goal and an action list", acts=(1,)),
    node("executor", "microservice", "service", "rounded", 4, 200, 72, "executor",
         "parse JSON → check → run",
         "executor — plain code: parses the JSON, checks the named index against the live page, "
         "runs the action, then re-observes", acts=(1,)),
    node("jev", "decision-model", "service", "decider", 3, 230, DECIDE_H, "Jev",
         ["operation? target? ·", "one round trip"],
         "Jev — one request per step: the state plus two questions, which operation and which "
         "target, answered together with a probability per option; every option it can pick was "
         "observed on the page", acts=(2,), hero=True),
    node("text-helper", "text-llm", "service", "llm", 3, 170, 66, "text helper",
         "only for TYPE_TEXT",
         "text helper — a small LLM that writes the text to type, only when the operation is "
         "TYPE_TEXT; its output must parse as a small JSON object before it is typed",
         acts=(2,), sup=True, dx=-(230 / 2 + GAP_TEXT_HELPER + 170 / 2)),
    node("validator", "guardrail-filter", "service", "hexagon", 4, 220, ROW_H, "validator",
         "fresh? visible? not occluded?",
         "validator — before acting: the page is still fresh, the target still visible and not "
         "occluded; then it runs the action with a bounded wait and re-observes. A stale page "
         "re-observes instead of acting, and a retry never double-clicks", acts=(2,)),
    # The action itself, one node holding three cells (sheet DEVIATIONS: three boxes would draw
    # a flowchart of verbs). Same slot in both acts, `changed:semantic` -- only the vocabulary
    # differs (B4), which is why the cells are per-act.
    node("actions", None, "service", "strip", 5, 260, ACT_H, "actions",
         {1: "runs the named tool", 2: "runs the picked operation"},
         {1: "actions — the browser action the executor runs on the page: click, input or "
             "scroll, with the one this step uses lit",
          2: "actions — the browser action the validator runs on the page: CLICK, TYPE_TEXT or "
             "SCROLL, with the one Jev picked lit"}),
]

# The action strip, per act (B4 / J2). `lit` is the index of the cell this step uses:
# act 1 lights `input`, act 2 lights `TYPE_TEXT` -- the same slot, each system's own word.
STRIP = {1: (["click", "input", "scroll"], 1), 2: (["CLICK", "TYPE_TEXT", "SCROLL"], 1)}
STRIP_CELL_FS = 11                             # local; 19.4 frame px at b5/b11's k
# The lit cell wears `is-selected` (states.csv): role-accent stroke one step heavier than
# the cell's CURRENT stroke. Its Motion Ref is `pulse-glow`, whose recipe is a drop-shadow
# filter -- banned under a moving camera -- so camera-beat.md's documented substitute
# applies: a static ring on the subject whose OPACITY alone breathes, on the row's own
# rhythm and easing. 1600ms does not divide the master (40.5x); 1800 does, exactly 36x.
PULSE_MS = 1800
STRIP_TYPED = "Zurich"                         # shown inside the type-text cell's glyph (J5)
PAGE_REACT_ROW = 1                             # row `[2] combobox`, zero-based
PAGE_REACT_VALUE = "Zurich|"                   # the caret is part of the sheet string
N = {n["id"]: n for n in NODES}
TEXT_ASK_Y = N["jev"]["y"] + N["jev"]["h"] / 2 + sc(20)


def cx(i): return N[i]["x"] + N[i]["w"] / 2
def cy(i): return N[i]["y"] + N[i]["h"] / 2
def top(i): return N[i]["y"]
def bot(i): return N[i]["y"] + N[i]["h"]
def left(i): return N[i]["x"]
def right(i): return N[i]["x"] + N[i]["w"]


PRIMARY = "edge edge--primary anim-dash-flow"
NOLABEL = (None, 0, 0, "")


def spine(a, z):
    """The forward flow: down the cast's right shoulder at SPINE_X, so the gap left of it is a
    clear lane for the caption card (see the module docstring)."""
    return f"M {f(SPINE_X)} {f(bot(a))} V {f(top(z))}"


def loop_back(a):
    """The return edge: out of the bottom at SPINE_X, along the foot, up the return trunk and
    back into the page's right side. Leaving at SPINE_X keeps it on the same line the forward
    flow uses; the foot runs BELOW the last row so the two trunk labels have somewhere to sit."""
    return (f"M {f(SPINE_X)} {f(bot(a))} V {f(RETURN_Y)} H {f(RETURN_X)} "
            f"V {f(cy('page'))} H {f(right('page'))}")


# (id, acts, from, to, d, css classes, markers, (label, x, y, anchor))
EDGES = [
    # ---- act 1: the LLM writes the action -------------------------------------------------
    ("e-read", (1,), "page", "page-state", spine("page", "page-state"), PRIMARY, "end",
     ("read", SPINE_X + 8, (bot("page") + top("page-state")) / 2 + sc(5), "start")),
    ("e-prompt", (1,), "page-state", "llm", spine("page-state", "llm"), PRIMARY, "end",
     ("prompt", SPINE_X + 8, (bot("page-state") + top("llm")) / 2 + sc(5), "start")),
    ("e-json", (1,), "llm", "executor", spine("llm", "executor"), PRIMARY, "end",
     ("JSON", SPINE_X + 8, (bot("llm") + top("executor")) / 2 + sc(5), "start")),
    # The action itself is a node now, so the step ends on it and the loop returns FROM it
    # (sheet FLOWS: `executor -> run -> actions -> click · input -> page`). `run` renders once
    # per act, from that act's executing step.
    ("e-run-1", (1,), "executor", "actions", spine("executor", "actions"), PRIMARY, "end",
     ("run", SPINE_X + 8, (bot("executor") + top("actions")) / 2 + sc(5), "start")),
    ("e-return-1", (1,), "actions", "page", loop_back("actions"), PRIMARY, "end",
     ("click · input", (SPINE_X + RETURN_X) / 2, RETURN_Y + sc(18), "middle")),
    # ---- act 2: Jev picks it, the validator acts ------------------------------------------
    ("e-snapshot", (2,), "page", "page-state", spine("page", "page-state"), PRIMARY, "end",
     ("snapshot", SPINE_X + 8, (bot("page") + top("page-state")) / 2 + sc(5), "start")),
    ("e-state-q", (2,), "page-state", "jev", spine("page-state", "jev"), PRIMARY, "end",
     # TWO LINES: at one, this label reaches 139.8 world px past the spine and pushes the
     # return trunk out past what b2/b7's frame can hold. Split, its widest line is 79.0 and
     # `textContent` is still the sheet's one string.
     (["state +", "questions"], SPINE_X + 8,
      (bot("page-state") + top("jev")) / 2 - sc(4), "start")),
    # 20 local below the node's centre: the latency chip owns the top of this lane, and the
    # label needs 10 world px under the pill
    ("e-text-ask", (2,), "jev", "text-helper",
     f"M {f(left('jev'))} {f(TEXT_ASK_Y)} H {f(right('text-helper'))}", "edge", "end",
     # centred in the widened lane: ~10.8 world px to each spotlight bracket (controller
     # review of b8 -- at the old 40-unit gap it sat inside Jev's bracket box)
     ("text?", (left("jev") + right("text-helper")) / 2, TEXT_ASK_Y - sc(8), "middle")),
    ("e-text-back", (2,), "text-helper", "validator",
     f"M {f(TEXT_BACK_X)} {f(bot('text-helper'))} V {f(cy('validator'))} "
     f"H {f(left('validator'))}",
     "edge", "end", ('{"text": "Zurich"}', (TEXT_BACK_X + left("validator")) / 2,
                     cy("validator") - sc(8), "middle")),
    ("e-jev-val", (2,), "jev", "validator", spine("jev", "validator"), PRIMARY, "end",
     ("TYPE_TEXT [2]", SPINE_X + 8, (bot("jev") + top("validator")) / 2 + sc(5), "start")),
    # UNDER the foot, not above it: `type · wait ≤ 200 ms` is 125.2 world px and the foot is
    # 124 wide between its two verticals, so a label on the line crosses its own trunk at both
    # ends. Below the foot nothing else is drawn, and both acts keep the same slot.
    ("e-run-2", (2,), "validator", "actions", spine("validator", "actions"), PRIMARY, "end",
     ("run", SPINE_X + 8, (bot("validator") + top("actions")) / 2 + sc(5), "start")),
    ("e-return-2", (2,), "actions", "page", loop_back("actions"), PRIMARY, "end",
     ("type · wait ≤ 200 ms", (SPINE_X + RETURN_X) / 2, RETURN_Y + sc(18), "middle")),
    # out of the validator's FOOT, not its left vertex -- the text helper's return already
    # lands there, and two arrows on one point read as one edge. The label is LEFT-anchored on
    # the trunk rather than centred on the run: gap 4 also carries b11's caption card, whose
    # left edge would cover a centred label.
    ("e-stale", (2,), "validator", "page-state",
     f"M {f(STALE_FOOT_X)} {f(bot('validator'))} V {f(STALE_Y)} H {f(STALE_X)} "
     f"V {f(cy('page-state'))} H {f(left('page-state'))}", "edge edge--error", "end",
     ("stale → re-observe", STALE_X + sc(10), STALE_Y - sc(8), "start")),
]
# The loop count and the loop's continuation ride the return TRUNK, rotated, one per act --
# the foot carries the action label and there is no room for a second horizontal string there.
TRUNK_LABEL = {1: "× N steps", 2: "next step"}
# 14 px left of the trunk, not 8: rotated, a 13 px label's ink reaches 2.9 px PAST its baseline
# on the descender side, so an 8 px offset left only 4.4 px of clear paper. y=1000 keeps its
# 60 px run clear of `state + questions` above it and `TYPE_TEXT [2]` below.
TRUNK_LABEL_XY = (RETURN_X - sc(14), BANDS[2][0] + BANDS[2][1] / 2)


def vbox(nid):
    """A node's FULL visual bbox -- its shape plus any latency chip hung off it.

    camera-beat.md -> Beat spotlight: "A subject's state chip is part of the subject: the
    overlay's box must enclose chip and node together." The same holds for the must-show sets,
    so `show` nodes read this too, not just subjects.
    """
    l, r, t, bm = left(nid), right(nid), top(nid), bot(nid)
    if nid in CHIPS:
        cx0, cy0, cw, ch = chip_box(nid)
        l, r = min(l, cx0), max(r, cx0 + cw)
        t, bm = min(t, cy0), max(bm, cy0 + ch)
    return l, r, t, bm


def sbox(nid, b=None):
    """A subject's full visual bbox."""
    return vbox(nid)



# ---- the storyboard (sheet Phase 2) -------------------------------------------------------
# `card` = (right edge, top) -- every read card's right edge is CARD_R, which is what keeps it
# off the spine its own subject hangs on, and every card's top is CARD_OFF into the gap it
# sits in. b2/b7's card hangs BELOW its subject (gap 2) rather than above it: with five rows
# the column cannot afford four card-sized gaps, and the adjacency rule reads the same either
# way -- the card is in the gap touching its own subject.
BEATS = [
    dict(id="t0", act=1, gate="overview", subjects=[], ms=TITLE_MS, title=True,
         lines=["Agent điều khiển browser", "LLM viết action · Jev chọn action"]),
    dict(id="b1", act=1, gate="overview", subjects=[],
         lines=["Mục tiêu: tìm chuyến bay Zürich → London.",
                "Agent phải tự bấm trên trang, từng bước một."]),
    dict(id="b2", act=1, gate="read", subjects=["page-state"], show=["page", "page-state"],
         card=(CARD_R, gap_top(2) + CARD_OFF[2]),
         lines=["Mỗi bước, code đọc cây DOM thành danh sách",
                "element có đánh số, kèm screenshot khi cần."]),
    dict(id="b3", act=1, gate="read", subjects=["llm"], show=["page-state", "llm"],
         card=(CARD_R, gap_top(2) + CARD_OFF[2]),
         lines=["LLM nhận cả trang làm prompt, rồi sinh",
                "JSON từng token: thinking, next_goal, action."]),
    dict(id="b4", act=1, gate="read", subjects=["executor"], show=["llm", "executor"],
         card=(CARD_R, gap_top(3) + CARD_OFF[3]),
         lines=["Action chỉ là text JSON: code phải parse,",
                "rồi tự kiểm tra xem element còn trên trang."]),
    # b5 is the anchor hold: `page` is alive in both acts, so the crossfade changes the system
    # around a fixed point. Its window ends before act 2 un-parks (the hold stops one camera
    # move short of the slot boundary, and act 2's window opens 600ms after it).
    #
    # SUBJECT = `actions` + the lit return edge; the page is CONTEXT, held as a PEEK bound at
    # 80 % of its height from the bottom (controller ruling in the sheet's DEVIATIONS:
    # bracketing page AND actions together spans the whole column at a read gate and forces the
    # element-table rows onto one line). The reaction on row `[2]` is in frame either way.
    dict(id="b5", act=1, gate="read", subjects=["actions"], show=["executor"],
         card=(CARD_R, gap_top(4) + CARD_OFF[4]), extra=[RETURN_X + sc(2)],
         extra_top=bot("page") - 0.8 * N["page"]["h"], lit_edges=["e-return-1"],
         anchor="page",
         lines=["Bấm xong lại đọc trang, lặp N bước —",
                "bước nào cũng phải chờ LLM sinh chữ."]),
    dict(id="b6", act=2, gate="overview", subjects=[],
         lines=["Với Jev: cùng trang, cùng mục tiêu,",
                "nhưng model chỉ chọn, không sinh text."]),
    dict(id="b7", act=2, gate="read", subjects=["page-state"], show=["page", "page-state"],
         card=(CARD_R, gap_top(2) + CARD_OFF[2]),
         lines=["Một lần gọi browser đọc hết control đang hiện:",
                "tên, giá trị, text — không cần screenshot."]),
    dict(id="b8", act=2, gate="read", subjects=["jev"], show=["page-state", "jev"],
         card=(CARD_R, gap_top(2) + CARD_OFF[2]),
         lines=["Jev trả lời hai câu hỏi trong một round trip:",
                "làm gì, với element nào — kèm xác suất."]),
    # b9/b10: the `text?` lane had to grow to 74 local so its label clears both spotlight
    # brackets (controller review). That pushes the Jev/text-helper pair past what the read
    # floor can frame, so camera-beat.md's own remedy applies -- the UPSTREAM peeks instead of
    # being framed. b9 drops Jev from the must-show (measured: it still renders fully inside
    # the frame, 752.8 against a frame that reaches 815.9); b10 keeps the text helper as a
    # peek bound at 80 % of its width (measured: 99.2 % of it is actually in frame).
    dict(id="b9", act=2, gate="read", subjects=["text-helper"], show=["text-helper"],
         card=(CARD_R, gap_top(2) + CARD_OFF[2]),
         lines=["Chỉ với TYPE_TEXT, một LLM nhỏ mới viết",
                "chữ cần gõ — và phải ra đúng JSON."]),
    # b10's card shares the gap-3 slot. Both of the validator's inputs are routed around it:
    # the spine lands 8px right of the card's edge, and the text helper's return drops at
    # x=230, 16px left of it.
    dict(id="b10", act=2, gate="read", subjects=["validator"],
         show=["jev", "validator"], card=(CARD_R, gap_top(3) + CARD_OFF[3]),
         extra_left=right("text-helper") - 0.8 * N["text-helper"]["w"],
         lines=["Trước khi gõ, code kiểm tra: trang còn mới,",
                "element còn hiện, không bị che."]),
    dict(id="b11", act=2, gate="read", subjects=["actions"], show=["validator"],
         card=(CARD_R, gap_top(4) + CARD_OFF[4]), extra=[RETURN_X + sc(2)],
         extra_top=bot("page") - 0.8 * N["page"]["h"], lit_edges=["e-return-2"],
         lines=["Gõ Zurich, đợi gợi ý tối đa 200 ms,",
                "rồi đọc trang tiếp — cả task 7,1 giây."]),
    dict(id="b12", act=2, gate="overview", subjects=[], ms=2 * BEAT_MS, split=BEAT_MS,
         lines=["LLM thì viết câu trả lời, code phải parse.",
                "Jev chỉ chọn trong menu trang, kèm xác suất."]),
]


def slot_ms(b):
    return b.get("ms", BEAT_MS)


def start_ms(i):
    return sum(slot_ms(x) for x in BEATS[:i])


MASTER_MS = sum(slot_ms(b) for b in BEATS)     # 64800 = 2400 + 11x4800 + 9600
                                               # = 1200x54 = 2400x27. NOT 4800xN.
MOVE = 600 / MASTER_MS * 100
ACT2_SLOT = next(i for i, b in enumerate(BEATS) if b["act"] == 2)
K_MAX = 2.2
LINE_H = 1.25


def cap_w(lines, fs):
    return max(tw(s, fs, 600) for s in lines) + 28


def cap_h(lines, fs):
    return len(lines) * fs * LINE_H + 16


def pct_of(ms):
    return ms / MASTER_MS * 100


def slot_start(i):
    return pct_of(start_ms(i))


def solve_beats():
    """k from the SAFE rect (platform UI covers the rest), pose from solve_camera.py."""
    for b in BEATS:
        if b["gate"] == "overview":
            b.update(k=1.0, fs=float(P_MIN), fs_min=sc(LABEL_FS),
                     card_xy=(W / 2, OVERVIEW_BAND_Y),
                     bbox=[SAFE[0], SAFE[1], SAFE[2] - SAFE[0], SAFE[3] - SAFE[1]])
            if b.get("title"):                 # the display card, centred on the FRAME
                b.update(fs=float(TITLE_FS),
                         card_xy=(W / 2, TITLE_CY - (2 * TITLE_FS * LINE_H + 16) / 2))
            continue
        air, brk = b.get("air", AIR), BRK      # brk = bracket pad + half its focus stroke
        subs = [sbox(n, b) for n in b["subjects"]]
        shows = [vbox(n) for n in b["show"]]
        xs0 = [v[0] - air for v in shows] + [s[0] - brk for s in subs]
        xs1 = [v[1] + air for v in shows] + [s[1] + brk for s in subs]
        ys0 = [v[2] - air for v in shows] + [s[2] - brk for s in subs]
        ys1 = [v[3] + air for v in shows] + [s[3] + brk for s in subs]
        # A PEEK bound is one coordinate, not a box: camera-beat.md's "let the upstream node
        # peek at >=80% visible instead of fully framed". `extra_left` bounds a node that hangs
        # off the frame's left, `extra_top` one above it.
        xs0 += [b["extra_left"]] if "extra_left" in b else []
        ys0 += [b["extra_top"]] if "extra_top" in b else []
        xs1 += b.get("extra", [])
        k = 1.9
        for _ in range(6):                     # the card's size depends on k, and k on the card
            fs = round(P_MIN / k + 0.05, 1)
            cw, ch = cap_w(b["lines"], fs), cap_h(b["lines"], fs)
            cr, cty = b["card"]
            ccx = cr - cw / 2
            x0, x1 = min(xs0 + [ccx - cw / 2 - air]), max(xs1 + [ccx + cw / 2 + air])
            y0, y1 = min(ys0 + [cty - air]), max(ys1 + [cty + ch + air])
            k = min((SAFE[2] - SAFE[0]) / (x1 - x0), (SAFE[3] - SAFE[1]) / (y1 - y0), K_MAX)
            k = int(k * 100) / 100
        fx0 = min([s[0] for s in subs] + [ccx - cw / 2])
        fx1 = max([s[1] for s in subs] + [ccx + cw / 2])
        fy0 = min([s[2] for s in subs] + [cty])
        fy1 = max([s[3] for s in subs] + [cty + ch])
        b.update(k=k, bbox=[x0, y0, x1 - x0, y1 - y0], card_xy=(ccx, cty),
                 focus=((fx0 + fx1) / 2, (fy0 + fy1) / 2))
    for b in BEATS:
        if b["gate"] == "overview":
            continue
        if b["k"] * sc(LABEL_FS) < P_MIN:
            sys.exit(f"{b['id']}: k {b['k']} puts the {f(sc(LABEL_FS))}px labels under "
                     f"{P_MIN} frame px")
        b["fs"] = round(P_MIN / b["k"] + 0.05, 1)
        b["fs_min"] = min(b["fs"], sc(LABEL_FS))

    holds = []
    for i, b in enumerate(BEATS):
        a_ms = start_ms(i)
        start, end = pct_of(a_ms), pct_of(a_ms + slot_ms(b))
        if b.get("title"):                     # the hold IS the card: midpoint = 1000ms
            windows = [(b["id"], 0.0, pct_of(TITLE_HOLD_MS))]
        elif b.get("split"):                   # one hold per beat: caption half, then look half
            cut = pct_of(a_ms + b["split"])
            windows = [(b["id"] + "a", start, cut), (b["id"] + "b", cut, 100.0)]
        elif b["gate"] == "overview":
            windows = [(b["id"], start, end)]
        else:
            windows = [(b["id"], start + MOVE, end - MOVE)]
        bx, by, bw, bh = b["bbox"]
        k = b["k"]
        if b["gate"] == "overview":
            centre = (W / 2, H / 2)
        else:
            # the world point that lands on the SAFE centre: the beat's focus, aimed at the
            # FRAME centre and clamped so the whole must-show bbox stays in the safe rect
            hw, hh = (SAFE[2] - SAFE[0]) / 2 / k, (SAFE[3] - SAFE[1]) / 2 / k
            want = b["focus"][0] - (W / 2 - SAFE_CX) / k
            sx = min(max(want, bx + bw - hw), bx + hw)
            sy = min(max(b["focus"][1], by + bh - hh), by + hh)
            centre = (sx + (W / 2 - SAFE_CX) / k, sy + (H / 2 - SAFE_CY) / k)
        for hid, a, z in windows:
            cmd = [sys.executable, str(SCRIPTS / "solve_camera.py"), "--viewport", f"{W}x{H}",
                   "--bbox", ",".join(f(v) for v in ((0, 0, W, H) if b["gate"] == "overview"
                                                     else b["bbox"])),
                   "--fs-min", str(b["fs_min"]), "--gate", b["gate"], "--k", str(k),
                   "--center", f"{centre[0]:.2f},{centre[1]:.2f}", "--id", hid,
                   "--window", f"{a:.4f},{z:.4f}", "--json"]
            if b["gate"] == "read":
                cmd += ["--fs-min-source",
                        f".cap-{b['id']} text" if b["fs_min"] < sc(LABEL_FS)
                        else ".node__label"]
            out = json.loads(subprocess.run(cmd, capture_output=True, text=True,
                                            check=True).stdout)
            if out.get("status") != "ok":
                sys.exit(f"solve_camera refused {hid}: {out}")
            frag = out["manifest"]
            frag["window"] = [round(a, 4), round(z, 4)]
            if b.get("anchor"):
                frag["anchor"] = b["anchor"]
            holds.append(frag)
            b.setdefault("pose", (frag["k"], frag["tx"], frag["ty"]))
    return holds


# ---- shapes (geometry from templates/snippets/node-shapes*.html, scaled to w x h) --------
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def keep(text):
    """`xml:space="preserve"` for a fragment whose trailing space is the join to the next one.
    Without it the parser collapses that space away and the pair concatenates one space short of
    the sheet's string -- which is what the verifier found on the JSON card and on Jev's option
    line (D1, round 5)."""
    return ' xml:space="preserve"' if text != text.rstrip() else ""


# node-shapes-ml.html#shape-text-model-bubble (the `text-llm` row): a chat bubble with lines of
# text and a typing cursor -- a model that WRITES, token by token. Authored for the snippet's
# 80-tall row; `dy` re-seats it on this cut's cards.
GLYPH_LLM_BODY = ('<path class="node__detail glyph__line glyph__fill" d="M 17 18 H 43 a 7 7 0 0 1 '
                  '7 7 V 41 a 7 7 0 0 1 -7 7 H 28 L 20 56 V 48 H 17 a 7 7 0 0 1 -7 -7 V 25 '
                  'a 7 7 0 0 1 7 -7 Z" />'
                  '<path class="node__detail glyph__line" d="M 17 27 H 43 M 17 34 H 43 '
                  'M 17 41 H 28" />'
                  '<rect x="31" y="37.5" width="4" height="7" rx="1" ry="1" />')
# node-shapes-ml.html#shape-decision-bars (the `decision-model` row): a probability per option
# with the pick ticked -- a model that CHOOSES and says how sure it is, and writes nothing.
GLYPH_DECIDER_BODY = ('<rect class="glyph__bar" x="12" y="38" width="9" height="14" rx="2" ry="2" />'
                      '<rect class="glyph__bar glyph__bar--pick" x="25" y="24" width="9" '
                      'height="28" rx="2" ry="2" />'
                      '<rect class="glyph__bar" x="38" y="43" width="9" height="9" rx="2" ry="2" />'
                      '<path class="node__detail glyph__line glyph__tick" d="M 24 15 l 4 4 l 8 -9" />'
                      '<path class="node__detail glyph__line" d="M 9 55 H 50" />')
GLYPH_SEAT = 56


def glyph(body, h, scale=1.0):
    """The snippet's own geometry, re-seated: shifted so it centres on a card of height `h`,
    and scaled once for the supporting tier (one glyph, one KIND, two sizes)."""
    dy = (h - 72) / 2 - 4 * scale
    return (f'<g class="node__icon" transform="translate(0,{f(dy)}) scale({scale:g})">'
            f'{body}</g>')


def shape_svg(n):
    """(shape, glyph, label_y, sub_y) in LOCAL units. The glyph comes back SEPARATELY because on
    a morph node it belongs to the summary face and has to crossfade with the label and the sub
    (controller ruling: the viewer sees `LLM` / `Jev` before the panel takes the card)."""
    w, h, s = n["lw"], n["lh"], n["shape"]
    box = f'<rect class="node__shape" x="0" y="0" width="{w}" height="{h}" rx="8" ry="8" />'
    if s == "device":
        return (box + f'<path class="node__detail" d="M 0 14 H {w}" />'
                '<circle class="node__icon" cx="13" cy="7" r="2.6" />'
                '<circle class="node__icon" cx="23" cy="7" r="2.6" />'
                '<circle class="node__icon" cx="33" cy="7" r="2.6" />', "", 30, 44)
    if s == "strip":
        return box, "", 20, 34
    if s == "state-card":
        return box, "", 20, 34
    if s == "hexagon":
        return (f'<polygon class="node__shape" points="20,0 {w-20},0 {w},{h/2:g} {w-20},{h} '
                f'20,{h} 0,{h/2:g}" />', "", 34, 54)
    if s == "rounded":
        return box, "", 33, 51
    if s == "llm":
        scale = 0.85 if n["sup"] else 1.0
        ly, sy = (28, 45) if n["sup"] else (32, 52)
        return box, glyph(GLYPH_LLM_BODY, h, scale), ly, sy
    if s == "decider":
        return box, glyph(GLYPH_DECIDER_BODY, h), 32, 52
    raise ValueError(s)


GLYPH_LEFT = ("llm", "decider")                # primary components: glyph left, text right


def per_act(value, act):
    return value[act] if isinstance(value, dict) else value


def value_parts(i):
    """Line 2 of a control row -- its VALUE, as the sheet writes it. Row `[2]` is split at its
    value so the b5/b11 page reaction can replace ONLY `San Francisco` with `Zurich|`; every
    rendered string stays a sheet string, and the join rides a trailing space."""
    _badge, _role, value = CONTROLS[i]
    if i == PAGE_REACT_ROW:
        head, tail = value.split(" · ")
        return [f"{head} · ", tail]
    return [value]


def row_lines_svg(i, ytop, bx, vx):
    """One control, on TWO lines: `[n] role` over its value (J3, the form rounds 1-3 drew)."""
    badge, role, _value = CONTROLS[i]
    bw = tw(badge, BADGE_FS, 500) + 12
    out = [f'<rect class="ctl__badge" x="{f(bx)}" y="{ytop + 1}" width="{f(bw)}" '
           f'height="14" rx="4" ry="4" />',
           f'<text class="ctl__badgetext" x="{f(bx + bw / 2)}" y="{ytop + 11}">{badge}</text>',
           f'<text class="ctl__role" x="{f(bx + bw + 8)}" y="{ytop + 11}">{role}</text>']
    x = vx
    for part in value_parts(i):
        out.append(f'<text class="ctl__value" x="{f(x)}" y="{ytop + 23}" '
                   f'xml:space="preserve">{esc(part)}</text>')
        x += tw(part, ROW_FS)
    return "".join(out)


CTL_TOP, STATE_TOP = 52, 42                    # the first control row, in each card's own space


def page_interior(n):
    """The page's own three controls, each on two lines in its own field (J3).

    The FIELD holds BOTH of the control's lines. `verify-hold-geometry` sweep 1 hands each text
    the smallest drawn box inside its node group that spans it horizontally and overlaps its
    FONT box, then asserts the text's INK is inside that box -- so a field drawn around the
    value line alone reaches up into the NEXT control's role line and claims it (measured on
    the first build: `combobox` came out 10.1 px below a box that was never its own).
    """
    w = n["lw"]
    out = []
    for i in range(len(CONTROLS)):
        ytop = CTL_TOP + i * CTL_PITCH
        out.append(f'<rect class="ctl__box" x="14" y="{ytop}" width="{w - 28}" '
                   f'height="{CTL_BOX_H}" rx="5" ry="5" />')
        out.append(row_lines_svg(i, ytop, 20, 22))
    return "".join(out)


def page_react_svg(act, window):
    """b5 / b11: the page REACTS -- row `[2]`'s value becomes `Zurich|` (sheet FLOWS and CHROME
    STRINGS). A staged overlay on the page's interior with its own `data-window`, never a
    mutation of the row: the patch is drawn in the field's own fill over `San Francisco`, with
    the new value in its place, and it fades on the hold's own window.

    The patch is a `<path>`, not a `<rect>`, deliberately: sweep 1 reads
    `rect, polygon, ellipse, circle, path.node__shape` as candidate containers, so a patch rect
    would become the typed value's container and hold its ink to a 13-unit band instead of to
    the control's own field.
    """
    i = PAGE_REACT_ROW
    ytop = CTL_TOP + i * CTL_PITCH
    head, tail = value_parts(i)
    x = 22 + tw(head, ROW_FS)
    x1 = x + tw(tail, ROW_FS) + 2
    y0, y1 = ytop + 12, ytop + CTL_BOX_H - 1
    return (f'\n          <g class="page-react page-react-a{act}" data-window="{window}">'
            f'<path class="ctl__patch" d="M {f(x - 2)} {y0} H {f(x1)} V {y1} '
            f'H {f(x - 2)} Z" />'
            f'<text class="ctl__value ctl__value--typed" x="{f(x)}" '
            f'y="{ytop + 23}">{esc(PAGE_REACT_VALUE)}</text></g>')


def state_interior(n):
    """The same three rows as a table (sheet CHROME STRINGS / J3). No field boxes here -- the
    table's rules are `<path>`s, which sweep 1 does not read as a container, so every row's
    text is held to the card itself."""
    out = []
    for i in range(len(CONTROLS)):
        ytop = STATE_TOP + i * STATE_PITCH
        out.append(row_lines_svg(i, ytop, 14, 24))
        if i < len(CONTROLS) - 1:              # a rule BETWEEN rows, never a second border
            out.append(f'<path class="ctl__rule" d="M 14 {ytop + 25} H {n["lw"] - 14}" />')
    return "".join(out)


# ---- the `actions` strip: three cells, this step's own one lit ---------------------------
# ONE node holding three cells, not three nodes (sheet DEVIATIONS: three boxes would draw a
# flowchart of verbs). Each cell is a custom figurative glyph over its texture-class name --
# the mapping table records `actions` as NO ROW, which is the only licence for a hand-made
# shape. Geometry, local: cell 70 x 42 on a pitch of 78, art in y 2..22, the name's baseline at
# 37, so the art clears its own name by 7.1 local (6.8 screen px against
# verify-glyph-label-gap's floor of 3) and the name's ink sits 2.6 inside the cell.
CELL_W, CELL_GAP, CELL_TOP, CELL_H = 70, 8, 41, 42


def cell_glyphs(i, ox, oy):
    """The three action glyphs, drawn in the role's own stroke/fill tokens so the veil and
    every skin re-colour them for free. `node__icon` rides the group so that
    verify-glyph-label-gap MEASURES this art against the node's text rather than ignoring it.

    ABSOLUTE coordinates, not a per-cell `transform`: `verify-text-containment` sweep 1 compares
    a text's `getBBox()` with the node SHAPE's, and getBBox is local to the element's own user
    space -- a translate between them silently compares two coordinate systems (measured: the
    `TYPE_TEXT` cell name reported a 1.3px overflow of a node it sits 100px inside).
    """
    def px(pairs):
        return " ".join(f"{ox + x:g} {oy + y:g}" for x, y in pairs)
    if i == 0:                                 # a pointer with its press ring
        pts = [(30, 3), (30, 20), (34, 16), (37, 22), (40, 20.5), (37.2, 15), (42, 14)]
        return ('<g class="node__icon cell__art">'
                f'<circle class="cell__ring" cx="{ox + 35:g}" cy="{oy + 12:g}" r="9" />'
                f'<path class="cell__ink" d="M {px(pts[:1])} L {px(pts[1:])} Z" />'
                '</g>')
    if i == 1:                                 # an input field with the typed value + a caret
        return ('<g class="node__icon cell__art">'
                f'<rect class="cell__field" x="{ox + 11:g}" y="{oy + 4:g}" width="48" '
                f'height="17" rx="3" ry="3" />'
                f'<text class="cell__typed" x="{ox + 15:g}" y="{oy + 17:g}">{STRIP_TYPED}</text>'
                f'<path class="cell__caret" d="M {ox + 51:g} {oy + 7:g} V {oy + 18:g}" />'
                '</g>')
    # A scrollbar: a tall narrow TRACK with its thumb, and the two arrows beside it. Drawn
    # narrow on purpose -- at 16x20 with the arrows inside, the first pass read as a mouse.
    return ('<g class="node__icon cell__art">'
            f'<rect class="cell__field" x="{ox + 33:g}" y="{oy + 1:g}" width="10" height="22" '
            'rx="4" ry="4" />'
            f'<rect class="cell__ink" x="{ox + 34.5:g}" y="{oy + 9:g}" width="7" height="8" '
            'rx="2" ry="2" />'
            f'<path class="cell__arrow" d="M {ox + 24:g} {oy + 8:g} L {ox + 27.5:g} {oy + 4:g} '
            f'L {ox + 31:g} {oy + 8:g} M {ox + 24:g} {oy + 16:g} L {ox + 27.5:g} {oy + 20:g} '
            f'L {ox + 31:g} {oy + 16:g}" />'
            '</g>')


def actions_interior(n, act=1):
    names, lit = STRIP[act]
    x0 = (n["lw"] - (3 * CELL_W + 2 * CELL_GAP)) / 2
    y = CELL_TOP
    out = []
    for i, name in enumerate(names):
        x = x0 + i * (CELL_W + CELL_GAP)
        on = i == lit
        out.append(f'<g class="cell{" is-selected" if on else " is-dim"}">'
                   f'<rect class="cell__box" x="{x:g}" y="{y:g}" width="{CELL_W}" '
                   f'height="{CELL_H}" rx="5" ry="5" />'
                   + (f'<rect class="cell__pulse" x="{x - 3:g}" y="{y - 3:g}" '
                      f'width="{CELL_W + 6}" height="{CELL_H + 6}" rx="8" ry="8" />'
                      if on else "")
                   + cell_glyphs(i, x, y)
                   + f'<text class="cell__name" x="{x + CELL_W / 2:g}" y="{y + 37:g}">'
                   f'{name}</text>'
                   f'</g>')
    return "".join(out)


INTERIOR = {"page": page_interior, "page-state": state_interior,
            "actions": lambda n, act=1: actions_interior(n, act)}


# ---- the two interior morphs: a DETAIL FACE inside the node ------------------------------
# camera-beat.md -> Interior morph: "The focused component crossfades from its summary face to
# a detail face ... Both faces live in the node group; opacity swaps on the master timeline
# during that beat." Rounds 1-3 drew these as world-space panels in the gap under the node;
# the controller's round-4 ruling puts them back inside it, which is also what CHROME STRINGS
# always said -- "interior of the LLM at its beat", "interior of Jev".
MORPH = {"llm": "json", "jev": "bars"}
MORPH_BEAT = {"json": "b3", "bars": "b8"}
# The third sheet line is set on TWO lines and the join rides a TRAILING SPACE on the first of
# them, the idiom every other split string in this cut uses (the two-line subs, `state +
# questions`, the caption cards, row `[2]`'s value): the two fragments concatenate to the sheet's
# string byte for byte. The fragment that carries the space is emitted `xml:space="preserve"`,
# or the parser collapses it away and the pair is one space short (verifier D1, round 5).
JSON_LINES = ['"thinking": "…"', '"next_goal": "…"',
              '"action": [{"input": ', '{"index": 2, …}}]']
JSON_INDENT = (0, 0, 0, 14)                    # the wrapped 4th line reads as one object
# operation / target, each with its option line(s) and one bar per option (J2, J3, L2). The
# percentages are illustrative and live ONLY inside this panel, which carries the tag.
BARS_GROUPS = [("operation", [9, 84, 4, 3], 1,
                # broken at a ` · ` boundary, the space that joins the two fragments
                # riding the first one (see JSON_LINES above)
                ["CLICK 9% · TYPE_TEXT 84% ✓ · ", "SELECT 4% · SCROLL 3%"]),
               ("target", [5, 91, 4], 1, ["[1] 5% · [2] 91% ✓ · [3] 4%"])]
BARS_TAG = "example values"
BAR_W, BAR_GAP, BAR_MAX, BAR_MIN = 7, 2, 12, 2
# Both detail faces start RIGHT of the glyph seat and end 6 local inside the card. The glyph
# belongs to the SUMMARY face and is dark while the detail face is up, but verify-glyph-label-gap
# measures every `.node__icon` against every text in its node at t=0 regardless of opacity -- and
# the honest reading of that is that the two faces must not occupy the same band anyway.
# FACE_L is the glyph seat exactly: the glyph's own ink ends at 50, so 56 keeps it 6 local
# (5.8 screen px, against verify-glyph-label-gap's floor of 3) clear of the panel, and the
# two units that buys are what the joining space costs Jev's longest option line -- it
# ends at 221.3 against the 224 the containment sweep allows.
FACE_L, FACE_R = GLYPH_SEAT, 6


def json_face(n):
    """The LLM's detail face: the JSON object it generates, B2's field names only. The fourth
    line is the third one's continuation -- `"action": [{"input": {"index": 2, …}}]` is 240.8
    local at 11px mono against a 218 inner width -- indented by an `x` offset, never by spaces,
    so `textContent` stays the sheet's string joined by one space."""
    w = n["lw"]
    wide = max(tw(s, JSON_FS, mono=True) + JSON_INDENT[i] for i, s in enumerate(JSON_LINES))
    x0 = round(FACE_L + (w - FACE_R - FACE_L - wide) / 2, 1)
    return "".join(
        f'<text class="morph__code" x="{f(x0 + JSON_INDENT[i])}" '
        f'y="{20 + i * 15}"{keep(line)}>{esc(line)}</text>'
        for i, line in enumerate(JSON_LINES))


def bars_face(n):
    """Jev's detail face: a probability per option with the pick ticked, tagged `example
    values` on the `operation` heading row (L2). Hero polarity rides the NODE, so this panel
    inverts with it for free -- ink body, paper text, accent on the picked bar."""
    w, right = n["lw"], n["lw"] - FACE_R
    out, y = [], 18
    for group, pcts, pick, lines in BARS_GROUPS:
        out.append(f'<text class="morph__grouplabel" x="{FACE_L}" y="{y}">{group}</text>')
        # The bars ride their group's HEADING row: the option lines are the widest strings in
        # the card and a bar column beside them would collide (measured, 3.5 local).
        span = len(pcts) * BAR_W + (len(pcts) - 1) * BAR_GAP
        bx = right - span
        if group == "operation":               # the tag sits on the SAME row, right-aligned
            out.append(f'<text class="morph__tag" x="{right}" y="{y}" '
                       f'style="text-anchor:end">{BARS_TAG}</text>')
            bx = right - tw(BARS_TAG, TAG_FS) - 8 - span
        for m, p in enumerate(pcts):
            h = max(BAR_MIN, round(BAR_MAX * p / 100, 1))
            cls = "morph__bar morph__bar--pick" if m == pick else "morph__bar"
            out.append(f'<rect class="{cls}" x="{f(bx + m * (BAR_W + BAR_GAP))}" '
                       f'y="{f(y + 2 - h)}" width="{BAR_W}" height="{f(h)}" '
                       f'rx="1.5" ry="1.5" />')
        for line in lines:
            y += 14
            out.append(f'<text class="morph__opt" x="{FACE_L}" y="{y}"{keep(line)}>'
                       f'{esc(line)}</text>')
        y += 16
    return "".join(out)


MORPH_FACE = {"json": json_face, "bars": bars_face}


def sub_svg(n, act, tx, sy):
    """One <text>, one or two lines. When the sheet's string is set on two lines the join rides
    a trailing space on line 1, so textContent is the sheet's string exactly."""
    value = per_act(n["sub"], act)
    cls = "node__sub" + (" node__sub--tight" if n.get("tight_sub") else "")
    if isinstance(value, str):
        return f'<text class="{cls}" x="{f(tx)}" y="{sy}">{esc(value)}</text>'
    spans = "".join(
        f'<tspan x="{f(tx)}" dy="{0 if i == 0 else LINE_H}em">{esc(s)}'
        f'{" " if i < len(value) - 1 else ""}</tspan>' for i, s in enumerate(value))
    return (f'<text class="{cls}" x="{f(tx)}" y="{sy}" '
            f'xml:space="preserve">{spans}</text>')


def node_svg(n, act, wins):
    """One node group. `wins` maps an emitted selector to its `data-window` value, so the two
    windowed things that live INSIDE a node -- the morph's detail face and the page's reaction
    -- take the emitter's percentages like every other staged element."""
    shape, gl, ly, sy = shape_svg(n)
    tx = (GLYPH_SEAT + n["lw"] - 4) / 2 if n["shape"] in GLYPH_LEFT else n["lw"] / 2
    cls = "node" + ("" if n["sup"] else " node--primary") + (" node--hero" if n["hero"] else "") \
        + (" node--sup" if n["sup"] else "")
    inner = (INTERIOR[n["id"]](n, act) if n["id"] == "actions"
             else INTERIOR[n["id"]](n) if n["id"] in INTERIOR else "")
    summary = (
        gl
        + fade_wrap(f'lf-{n["id"]}-label',
                    f'<text class="node__label" x="{f(tx)}" y="{ly}">{n["label"]}</text>', wins)
        + fade_wrap(f'lf-{n["id"]}-sub', sub_svg(n, act, tx, sy), wins))
    if n["id"] in MORPH:
        # The canonical camera-beat morph: both faces live in the node group and swap opacity on
        # the master timeline. The summary face takes the INVERSE of the detail face's emitted
        # window -- emitted from the same table, so `keyframe-grid` sees declared instants only
        # -- and the two cross-dissolve over the spotlight's own 0.6 s ramp rather than cut.
        kind = MORPH[n["id"]]
        body = (f'          <g class="node__body">{shape}</g>\n'
                f'          <g class="face-summary sum-{kind}" '
                f'data-window="{wins[f".sum-{kind}"]}">{summary}</g>\n'
                f'          <g class="face-detail morph-{kind}" '
                f'data-window="{wins[f".morph-{kind}"]}">{MORPH_FACE[kind](n)}</g>\n')
    else:
        body = (f'          <g class="node__body">{shape}</g>\n'
                f'          {summary}\n')
    react = (page_react_svg(act, wins[f".page-react-a{act}"]) if n["id"] == "page" else "")
    return (f'        <g class="{cls}" data-node-id="{n["id"]}" data-role="{n["role"]}" '
            f'transform="translate({f(n["x"])},{f(n["y"])}) scale({S:g})">\n'
            f'          <title>{esc(per_act(n["title"], act))}</title>\n'
            f'{body}'
            f'          <g class="node__interior">{inner}</g>{react}\n'
            f'        </g>')


# ---- scenery-clip windows -----------------------------------------------------------------
# A read hold frames its own subject; a string belonging to somewhere else can end up straddling
# the frame's edge and sit there, cut mid-word, for the whole hold. camera-beat.md's remedy for
# the heading is the one applied here per string: fade it out for exactly the holds that would
# cut it, on the same window machinery `t0` already uses for every edge label. The wrapper group
# multiplies with the label's own t0 window, so neither has to know about the other.
#
# Keys are slugs; the value is the list of beat ids whose hold cuts that string. MEASURED on the
# built page (see the sheet's round-4 build facts) -- never guessed, and re-measured whenever the
# geometry moves.
LABEL_FADE = {
    # MEASURED at every read hold's own pose (the probe walks every visible <text> and reports
    # the ones the frame cuts LEFT or RIGHT; a top/bottom slice of a peeking node's interior is
    # a peek, not a cut word, and is left alone).
    "lf-e-text-back": ["b7", "b8"],          # `{"text": "Zurich"}`  79% / 51% of it in frame
    "lf-text-helper-label": ["b7"],          # `text helper`         38%
    "lf-text-helper-sub": ["b7", "b8", "b11"],   # `only for TYPE_TEXT`  41% / 13% / 94%
    "lf-e-return-2": ["b9"],                 # `type · wait ≤ 200 ms` 89%
    "lf-e-stale": ["b10", "b11"],            # `stale → re-observe`   84% / 25%
}


def fade_wrap(slug, body, wins):
    if slug not in LABEL_FADE:
        return body
    return f'<g class="labelfade {slug}" data-window="{wins["." + slug]}">{body}</g>'


def edge_svg(e, act, wins, label_window=""):
    """`label_window` is the emitted `.edge__label` window: the labels are dark for the whole
    of t0, so the title card never covers one (the blur makes them unreadable regardless)."""
    eid, _acts, a, z, d, cls, mk, (label, lx, ly, anchor) = e
    marker = {"end": 'marker-end="url(#arrow)"',
              "both": 'marker-start="url(#arrow)" marker-end="url(#arrow)"'}[mk]
    win = f' data-window="{label_window}"' if label_window else ""
    out = (f'        <g class="edge-group"><path class="{cls}" id="a{act}-{eid}" data-from="{a}" '
           f'data-to="{z}" d="{d}" {marker}><title>{a} to {z}</title></path>')
    if label:
        lines = label if isinstance(label, list) else [label]
        body = "".join(
            f'<tspan x="{f(lx)}" dy="{0 if i == 0 else LINE_H}em">{esc(t)}'
            f'{" " if i < len(lines) - 1 else ""}</tspan>' for i, t in enumerate(lines))
        out += fade_wrap(f"lf-{eid}",
                         f'<text class="edge__label" x="{f(lx)}" y="{f(ly)}"{win} '
                         f'style="text-anchor:{anchor}" xml:space="preserve">{body}</text>',
                         wins)
    return out + "</g>"


def trunk_label_svg(act, wins, label_window=""):
    lx, ly = TRUNK_LABEL_XY
    win = f' data-window="{label_window}"' if label_window else ""
    return "        " + fade_wrap(
        f"lf-trunk-{act}",
        f'<text class="edge__label" x="{f(lx)}" y="{f(ly)}"{win} '
        f'style="text-anchor:middle" transform="rotate(-90 {f(lx)} {f(ly)})">'
        f'{esc(TRUNK_LABEL[act])}</text>', wins)


ACT_TITLE = {1: "act 1 · a text LLM writes the next action",
             2: "act 2 · Jev picks it from the page's own controls"}
PARK = {1: "translate(0px,-2400px)", 2: "translate(0px,-4800px)"}


def frost_svg(window):
    """t0's backdrop: a STATIC impression of act 1, blurred once by a native SVG filter.

    Not the real scene. One filled shape per act-1 node at its real position and size in its
    role tokens, plus the act's edges as plain strokes, over an opaque paper ground LARGER than
    the filter region (so the region holds no edge of it and the blur stays flat inside the
    frame). Under stdDeviation 130 it is indistinguishable from the cut itself, and it carries
    no text, no `data-node-id`, no `node`/`edge` class and `aria-hidden`, so no identity,
    containment or legend gate ever sees it.
    """
    out = [f'      <g class="frost" filter="url(#frost)" aria-hidden="true" '
           f'data-window="{window}">',
           '        <rect class="frost__ground" x="-800" y="-800" width="2680" '
           'height="3520" />']
    for e in EDGES:
        if FROST_ACT in e[1]:
            cls = "frost__line" + (" frost__line--error" if "edge--error" in e[5] else "")
            out.append(f'        <path class="{cls}" d="{e[4]}" />')
    for n in NODES:
        if FROST_ACT in n["acts"]:
            out.append(f'        <rect class="frost__box" data-role="{n["role"]}" '
                       f'x="{f(n["x"])}" y="{f(n["y"])}" width="{f(n["w"])}" '
                       f'height="{f(n["h"])}" rx="8" ry="8" />')
            if n["id"] in CHIPS:               # the latency pill is part of the act's silhouette
                cx0, cy0, cw, ch = chip_box(n["id"])
                out.append(f'        <rect class="frost__box" data-role="{n["role"]}" '
                           f'x="{f(cx0)}" y="{f(cy0)}" width="{f(cw)}" height="{f(ch)}" '
                           f'rx="{f(ch / 2)}" ry="{f(ch / 2)}" />')
    out.append("      </g>")
    return "\n".join(out)


def footer_svg():
    """The repo credit (sheet CHROME STRINGS -> Footer). Scenery on the HEADING layer, so it is
    on for every overview hold and fades with the heading while the camera is away -- it is
    never in a read hold's must-show set, and a read hold never has to frame it."""
    return f'          <text class="footer" x="540" y="{FOOTER_Y}">{esc(FOOTER)}</text>'


def act_svg(act, wins, label_window=""):
    window = wins[f".act-{act}"]
    edges = "\n".join(edge_svg(e, act, wins, label_window) for e in EDGES if act in e[1])
    nodes = "\n".join(node_svg(n, act, wins) for n in NODES if act in n["acts"])
    chips = "\n".join(chip_svg(nid, act) for nid in CHIPS if act in N[nid]["acts"])
    return (f'      <g class="act act-{act}" data-act="{act}" data-window="{window}">\n'
            f'        <g class="layer-heading" aria-hidden="true">\n'
            f'          <text class="subtitle" x="540" y="{SUBTITLE_Y}">'
            f'{esc(ACT_TITLE[act])}</text>\n'
            f'{legend_svg() if act == 2 else ""}\n'
            f'{footer_svg()}\n'
            f'        </g>\n{edges}\n{trunk_label_svg(act, wins, label_window)}\n{nodes}\n'
            f'{chips}\n      </g>')


def bracket(nid, b=None):
    pad, arm = FOCUS_PAD, FOCUS_ARM
    l, r, t, bm = sbox(nid, b)
    L, R, T, B = l - pad, r + pad, t - pad, bm + pad
    return (f"M {f(L+arm)} {f(T)} H {f(L)} V {f(T+arm)} M {f(R-arm)} {f(T)} H {f(R)} V {f(T+arm)} "
            f"M {f(R)} {f(B-arm)} V {f(B)} H {f(R-arm)} M {f(L+arm)} {f(B)} H {f(L)} V {f(B-arm)}")


def edge_points(eid):
    """The polyline an edge's own `d` draws. M/H/V only -- every trunk in this cut is orthogonal."""
    toks = next(e for e in EDGES if e[0] == eid)[4].split()
    pts, x, y, i = [], 0.0, 0.0, 0
    while i < len(toks):
        c = toks[i]
        if c == "M":
            x, y, i = float(toks[i + 1]), float(toks[i + 2]), i + 3
        elif c == "H":
            x, i = float(toks[i + 1]), i + 2
        elif c == "V":
            y, i = float(toks[i + 1]), i + 2
        else:
            raise ValueError(f"{eid}: a lit edge is read as M/H/V, not {c!r}")
        pts.append((x, y))
    return pts


def edge_rects(eid, act):
    """A lit edge's veil windows: a thin band along each leg, plus its labels' boxes.

    Read off the edge's own `d`, so the windows follow the boxes the same way the edge does. At
    a corner the earlier leg runs TRUNK_HALF past the joint and the later one starts that much
    in, so the corner square is covered exactly once (see `disjoint`).
    """
    pts = edge_points(eid)
    out = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        back = TRUNK_HALF if i else 0.0
        fwd = TRUNK_HALF if i + 2 < len(pts) else 0.0
        if y0 == y1:
            s = 1 if x1 > x0 else -1
            a, z = x0 + s * back, x1 + s * fwd
            out.append((min(a, z), y0 - TRUNK_HALF, max(a, z), y0 + TRUNK_HALF))
        elif x0 == x1:
            s = 1 if y1 > y0 else -1
            a, z = y0 + s * back, y1 + s * fwd
            out.append((x0 - TRUNK_HALF, min(a, z), x0 + TRUNK_HALF, max(a, z)))
        else:
            raise ValueError(f"{eid}: leg {i} is diagonal; the band is orthogonal")
    label, lx, ly, anchor = next(e for e in EDGES if e[0] == eid)[7]
    if label:
        lines = label if isinstance(label, list) else [label]
        w = max(tw(t, EDGE_FS) for t in lines) + sc(20)
        x0 = {"middle": lx - w / 2, "start": lx - sc(10), "end": lx - w + sc(10)}[anchor]
        out.append((x0, ly - EDGE_FS - sc(4),
                    x0 + w, ly + sc(5) + (len(lines) - 1) * EDGE_FS * LINE_H))
    tl, (tlx, tly) = TRUNK_LABEL[act], TRUNK_LABEL_XY
    th = tw(tl, EDGE_FS) + sc(20)              # rotated: the advance runs down the y axis
    out.append((tlx - EDGE_FS - sc(4), tly - th / 2, tlx + sc(5), tly + th / 2))
    return out


def _minus(r, o):
    """`r` with the part `o` covers cut out, as up to four rects (everything axis-aligned)."""
    x0, y0, x1, y1 = r
    ox0, oy0, ox1, oy1 = o
    if ox1 <= x0 or ox0 >= x1 or oy1 <= y0 or oy0 >= y1:
        return [r]
    ix0, ix1 = max(x0, ox0), min(x1, ox1)
    iy0, iy1 = max(y0, oy0), min(y1, oy1)
    parts = []
    if y0 < iy0:
        parts.append((x0, y0, x1, iy0))
    if iy1 < y1:
        parts.append((x0, iy1, x1, y1))
    if x0 < ix0:
        parts.append((x0, iy0, ix0, iy1))
    if ix1 < x1:
        parts.append((ix1, iy0, x1, iy1))
    return parts


def disjoint(rects):
    """The same union, re-cut so no two rects overlap. The veil is ONE even-odd path, so a patch
    inside two windows is inside three subpaths and flips back to WASHED -- a grey square on a
    corner. Tiling instead of overlapping is what stops that."""
    out = []
    for r in rects:
        parts = [r]
        for kept in out:
            parts = [p for q in parts for p in _minus(q, kept)]
        out += parts
    return out


def veil(b):
    """One even-odd path: the whole world minus a bracket-sized window over each subject and a
    band along each edge the beat LIGHTS. A 9:16 frame at k~2 shows several rows at once, so
    zoom alone does not single the subject out (morning-cut review); the wash does."""
    pad = FOCUS_PAD
    wins = [(l - pad, t - pad, r + pad, bm + pad)
            for l, r, t, bm in (sbox(s, b) for s in b["subjects"])]
    for eid in b.get("lit_edges", []):
        wins += edge_rects(eid, b["act"])
    # No panel window any more: the morph is a DETAIL FACE inside its node, so the subject's own
    # bracket window already holds it.
    d = "M -1080 -1920 H 2160 V 3840 H -1080 Z"
    for x0, y0, x1, y1 in disjoint(wins):
        d += f" M {f(x0)} {f(y0)} V {f(y1)} H {f(x1)} V {f(y0)} Z"
    return (f'      <g class="beat-veil focus-{b["id"]}"><path class="beat-veil__wash" '
            f'fill-rule="evenodd" d="{d}" /></g>')


# The title card's keywords, in the order they occur on their line. Everything between them
# stays paper: colour is EMPHASIS here, not meaning (sheet CHROME STRINGS).
TITLE_KEYWORDS = ("LLM", "Jev")


def title_line_fs(i):
    return TITLE_EYEBROW_FS if i == 0 else TITLE_FS


def title_spans(line, ccx, base_cls=""):
    """One text chunk per line, with the keywords split out into `.kw` tspans. Only the FIRST
    tspan of a line carries `x`, so the whole line is ONE chunk and `text-anchor:middle` centres
    it as a unit. `base_cls` rides EVERY tspan of the line, because it carries the line's
    font-size: on the first one only, a keyword split would leave the rest at the other size."""
    parts, rest = [], line
    while rest:
        hit = min((rest.index(k), k) for k in TITLE_KEYWORDS if k in rest) \
            if any(k in rest for k in TITLE_KEYWORDS) else None
        if not hit:
            parts.append((rest, False))
            break
        at, kw = hit
        if at:
            parts.append((rest[:at], False))
        parts.append((kw, True))
        rest = rest[at + len(kw):]
    out = []
    for i, (text, is_kw) in enumerate(parts):
        attrs = f' x="{f(ccx)}"' if i == 0 else ""
        names = ([base_cls] if base_cls else []) + (["kw"] if is_kw else [])
        cls = f' class="{" ".join(names)}"' if names else ""
        out.append(f"<tspan{attrs}{cls}>{esc(text)}</tspan>")
    return "".join(out)


def caption_svg(b):
    fs = b["fs"]
    ccx, cty = b["card_xy"]
    n = len(b["lines"])
    cw, ch = cap_w(b["lines"], fs), cap_h(b["lines"], fs)
    base = cty + 8 + fs * 0.95
    if b.get("title"):
        # Two sizes on one card, so the estimate is per line; the rect is re-baked from the
        # measured text and then re-padded by `--pad-title-card`. The BASELINE is what matters:
        # it is placed so the measured text box centres on TITLE_CY.
        cw = max(tw(s, title_line_fs(i), 600) for i, s in enumerate(b["lines"])) + 28
        asc1 = TITLE_EYEBROW_FS * 1.05         # line 1 carries stacked Vietnamese diacritics
        desc2 = TITLE_FS * 0.24
        gap = TITLE_LINE_EM * TITLE_FS
        ch = asc1 + gap + desc2 + 16
        base = TITLE_CY - (asc1 + gap + desc2) / 2 + asc1
        cty = base - asc1 - 8
        chunks = []
        for i, s in enumerate(b["lines"]):
            if i:
                # the joiner carries the space that makes textContent the manifest's string, at
                # ZERO advance, so neither centred line is pushed off x=540 by half a space
                chunks.append('<tspan class="cap-joiner"> </tspan>')
            chunk = title_spans(s, ccx, "eyebrow" if i == 0 else "")
            if i:                              # the line's own dy rides its first tspan; the
                chunk = chunk.replace("<tspan", f'<tspan dy="{TITLE_LINE_EM}em"', 1)
            chunks.append(chunk)
        spans = "".join(chunks)
    else:
        spans = "".join(
            f'<tspan x="{f(ccx)}" dy="{0 if i == 0 else LINE_H}em">{esc(s)}'
            f'{" " if i < n - 1 else ""}</tspan>'
            for i, s in enumerate(b["lines"]))
    # The spacer widens the group's bbox to the LEFT of the painted card, so the emitter's
    # parked-left clip (a strip 1% wide at the bbox's left edge) holds no antialiased card edge.
    spacer_dx = cw / 2 + 40 + (TITLE_PAD_X if b.get("title") else 0)
    return (f'      <g class="beat-caption cap-{b["id"]}">\n'
            f'        <circle class="caption-spacer" cx="{f(ccx - spacer_dx)}" '
            f'cy="{f(cty + 4)}" r="2" />\n'
            f'        <rect class="caption-box" x="{f(ccx - cw/2)}" y="{f(cty)}" '
            f'width="{f(cw)}" height="{f(ch)}" rx="8" ry="8" data-cap="{b["id"]}" />\n'
            f'        <text x="{f(ccx)}" y="{f(base)}" xml:space="preserve">{spans}</text>\n'
            f'      </g>')


REACT_BEAT = {1: "b5", 2: "b11"}               # the page reacts at act 1's b5 and act 2's b11
FADE_MS = 600                                  # the crossfade / clip-fade ramp, one camera move


def beat_index(bid):
    return next(i for i, b in enumerate(BEATS) if b["id"] == bid)


def beat_window_ms(bid):
    """A beat's SPOTLIGHT window in ms -- the quarter-to-three-quarters hold every overlay in
    this cut rides, so a morph and its spotlight breathe together."""
    s = start_ms(beat_index(bid))
    return s + BEAT_MS // 4, s + 3 * BEAT_MS // 4


def hold_window_ms(bid):
    """A beat's CAMERA hold in ms: the slot minus one camera move at each end."""
    i = beat_index(bid)
    s = start_ms(i)
    return s + 600, s + slot_ms(BEATS[i]) - 600


def complement(blocks):
    """The master timeline minus `blocks`, each end pulled in by one fade so the emitter's own
    600 ms lead/tail lands exactly on the block's edges."""
    out, at = [], 0
    for a, z in sorted(blocks):
        out.append((at, a - FADE_MS))
        at = z + FADE_MS
    out.append((at, MASTER_MS))
    return [(a, z) for a, z in out if z > a]


def fmt_windows(wins):
    return " ".join(f"{a}ms:{'100%' if z >= MASTER_MS else str(z) + 'ms'}" for a, z in wins)


def timeline_tsv():
    rows = ["element\tkind\tkeyframe\twindows\tlead\ttail\twipe\tpark\tseam\ttext\tsource"]
    s2 = start_ms(ACT2_SLOT)
    # Act 1 is lit from 0%: t0 opens ON it, under the frost. There is no hand-over and no loop
    # seam -- the web loop hard-cuts from the closing act-2 overview back to the title card, a
    # deliberate cut (camera-beat.md -> Opening title beat), so `.act-2` carries no `seam`.
    rows.append(f".act-1\tact\tact1\t0ms:{s2}ms\t600ms\t600ms\t\t{PARK[1]}\t\t\tlayouts:layered-tb")
    rows.append(f".act-2\tact\tact2\t{s2 + 600}ms:100%\t600ms\t\t\t{PARK[2]}\t\t"
                f"\tlayouts:layered-tb")
    # t0's frosted backdrop. An `act` row because it needs exactly what an act needs: lit for
    # its window, then PARKED off-canvas so its filtered raster is never composited under the
    # moving camera. It carries no `data-act` and its class is not `act…`, so the act gates
    # never see it, and `acts[]` is not declared.
    rows.append(f".frost\tact\tfrost\t0ms:{TITLE_HOLD_MS}ms\t600ms\t{TITLE_OUT_MS}ms\t"
                f"\t{PARK[2]}\t\t\tmotion:camera-beat")
    rows.append(f".t0-wash\tstate\tt0-wash\t0ms:{TITLE_HOLD_MS}ms:0ms:{TITLE_OUT_MS}ms"
                f"\t\t\t\t\t\t\t")
    # Edge labels are OFF while the title card is up: under the frost they are unreadable
    # anyway, and a caption card may never cover a VISIBLE edge label (caption-occlusion).
    rows.append(f".edge__label\tstate\tt0-labels\t{TITLE_MS}ms:100%:{LABEL_LEAD_MS}ms"
                f"\t\t\t\t\t\t\t")
    # The two interior morphs, and the SUMMARY face each one replaces. The summary's windows are
    # the exact complement of the detail's, emitted from this same table, so the pair
    # cross-dissolves over the spotlight's own 600 ms ramp and `keyframe-grid` sees nothing but
    # instants the manifest declares.
    for kind, bid in MORPH_BEAT.items():
        a, z = beat_window_ms(bid)
        rows.append(f".morph-{kind}\tstate\tw-{kind}\t{a}ms:{z}ms"
                    f"\t\t\t\t\t\t\tmotion:camera-beat")
        rows.append(f".sum-{kind}\tstate\tw-sum-{kind}"
                    f"\t{fmt_windows(complement([(a, z)]))}"
                    f"\t\t\t\t\t\t\tmotion:camera-beat")
    # The page's reaction at b5 / b11 -- one window per act, so a parked act never carries the
    # other act's beat.
    for act, bid in REACT_BEAT.items():
        a, z = beat_window_ms(bid)
        rows.append(f".page-react-a{act}\tstate\tw-react-a{act}\t{a}ms:{z}ms"
                    f"\t\t\t\t\t\t\tmotion:camera-beat")
    # Scenery-clip windows: a string a read hold would cut mid-word at the frame edge is dark
    # for exactly that hold (camera-beat.md's heading rule, applied per string).
    for slug, bids in LABEL_FADE.items():
        rows.append(f".{slug}\tstate\tw-{slug}"
                    f"\t{fmt_windows(complement([hold_window_ms(b) for b in bids]))}"
                    f"\t\t\t\t\t\t\tmotion:camera-beat")
    for i, b in enumerate(BEATS):
        s = start_ms(i)
        if b["subjects"]:
            rows.append(f".focus-{b['id']}\tspotlight\tfocus-{b['id']}"
                        f"\t{s + BEAT_MS // 4}ms:{s + 3 * BEAT_MS // 4}ms"
                        f"\t\t\t\t\t\t\tmotion:camera-beat")
    for i, b in enumerate(BEATS):
        s = start_ms(i)
        text = " ".join(b["lines"])
        if b.get("title"):
            # Already fully revealed at 0ms (`wipe` 0): the deliverable is a video, and its
            # first frame is the title itself, not a card sliding in.
            start, end, tail, wipe = 0, TITLE_HOLD_MS, TITLE_OUT_MS, 0
        else:
            head = BEAT_MS // 4 if i == ACT2_SLOT else BEAT_MS // 8
            start, end, tail, wipe = s + head, s + 3 * BEAT_MS // 4, 432, 408
        rows.append(f".cap-{b['id']}\tcaption\tcap-{b['id']}\t{start}ms:{end}ms\t600ms"
                    f"\t{tail}ms\t{wipe}ms\t\t\t{text}\tmotion:camera-beat")
    return "\n".join(rows) + "\n"


def pct(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") + "%"


def camera_keyframes():
    ease = "animation-timing-function:ease-in-out"
    stops = []
    for i, b in enumerate(BEATS):
        start, end = slot_start(i), pct_of(start_ms(i) + slot_ms(b))
        if b["gate"] == "overview":
            stops.append((start, end, None, b["id"]))
        else:
            k, tx, ty = b["pose"]
            stops.append((start + MOVE, end - MOVE,
                          f"translate({tx}px,{ty}px) scale({k})", b["id"]))
    out = ["@keyframes beats{"]
    for j, (a, z, t, c) in enumerate(stops):
        if t is None:
            out.append(f"  {pct(a)},{pct(z)}{{transform:none;{ease}}} /* {c} */")
            continue
        out.append(f"  {pct(a)},{pct(z)}{{transform:{t};{ease}}} /* {c} */")
        nxt = stops[j + 1] if j + 1 < len(stops) else None
        if nxt and nxt[2] is not None:         # pull back to the overview between two zoomed beats
            out.append(f"  {pct(z + MOVE)}{{transform:none;{ease}}}")
    out.append("}")
    # The heading is scenery: on for the overview slots only. It is also the title, and the
    # title must never be on screen twice -- so it is OFF for the whole of t0 and comes back
    # with the sharp frame at the slot boundary, as the frost and the wash clear.
    a2 = slot_start(ACT2_SLOT)
    b1_end = pct_of(start_ms(1) + BEAT_MS)
    a2_end = pct_of(start_ms(ACT2_SLOT) + BEAT_MS)
    last = slot_start(len(BEATS) - 1)
    out.append("@keyframes heading-fade{")
    out.append(f"  0%,{pct(pct_of(TITLE_HOLD_MS))}{{opacity:0}}")
    out.append(f"  {pct(pct_of(TITLE_MS))},{pct(b1_end)}{{opacity:1}}")
    out.append(f"  {pct(b1_end + MOVE)},{pct(a2 - MOVE)}{{opacity:0}}")
    out.append(f"  {pct(a2)},{pct(a2_end)}{{opacity:1}}")
    out.append(f"  {pct(a2_end + MOVE)},{pct(last - MOVE)}{{opacity:0}}")
    out.append(f"  {pct(last)},100%{{opacity:1}}")
    out.append("}")
    return "\n".join(out)


# The legend is "computed from its cast" (sheet CHROME STRINGS). Revision 2 put a
# fourth SERVICE node on the canvas, so act 2's service count is 4 and `actions` joins
# the member list -- the `x3` the sheet prints is that line evaluated before the
# revision, and `legend-fact` holds the count to the DOM. Flagged in the build facts.
LEGEND = [("client", "page"), ("data", "page state"),
          ("service", "Jev \u00b7 text helper \u00b7 validator \u00b7 actions")]
LEGEND_GAP = 30                                # between entries, frame px


def legend_svg():
    """The legend is a claim about the FINAL act's cast, so its counts are computed from it.
    Its entries are laid out from their MEASURED widths and the row is centred on the frame."""
    final = max(a for n in NODES for a in n["acts"])
    counts = {}
    for n in NODES:
        if final in n["acts"]:
            counts[n["role"]] = counts.get(n["role"], 0) + 1
    entries = [(role, members, f"{role} \u00d7{counts[role]} ")
               for role, members in LEGEND]
    widths = [LEGEND_SWATCH + 6 + tw(head, LEGEND_FS) + tw(members, LEGEND_FS)
              for _role, members, head in entries]
    x = 540 - (sum(widths) + LEGEND_GAP * (len(entries) - 1)) / 2
    out = ['          <g class="legend">']
    for (role, members, head), w in zip(entries, widths):
        out.append(f'          <rect x="{f(x)}" y="{LEGEND_Y - LEGEND_SWATCH + 3}" '
                   f'width="{LEGEND_SWATCH}" height="{LEGEND_SWATCH}" rx="4" '
                   f'fill="var(--role-{role})" stroke="var(--ink-{role})" stroke-width="1.8"/>')
        out.append(f'          <text data-legend-role="{role}" '
                   f'x="{f(x + LEGEND_SWATCH + 6)}" y="{LEGEND_Y}">{head}'
                   f'<tspan class="k">{esc(members)}</tspan></text>')
        x += w + LEGEND_GAP
    out.append("          </g>")
    return "\n".join(out)


DESC = (
    "A browser agent doing one task, in two acts: find one-way flights from Zurich to London on "
    "a Google Flights page whose three controls are indexed [1] button Change ticket type, "
    "[2] combobox Where from?, and [3] combobox Where to?. "
    "Act 1, the action is WRITTEN by a text LLM: every step, code reads the page's DOM tree into "
    "an indexed list of elements, with a screenshot when vision is on; the whole page state "
    "becomes the model's prompt and it generates, token by token, one JSON object with thinking, "
    "next_goal and an action list -- an estimated two to five seconds per step. The executor "
    "parses that JSON, checks the index it names "
    "against the live page, runs the click or the input, and the loop repeats for N steps -- "
    "every step waiting for a model to write text, and every action arriving as text that code "
    "has to parse and re-check, because nothing structural stops the model naming an element the "
    "page does not offer. "
    "Act 2, the action is CHOSEN by Jev: one browser call reads every visible control atomically "
    "with its name, value and text, and no screenshot. Jev answers two questions in one round "
    "trip of roughly 70 to 500 milliseconds -- which operation, and which target -- over the "
    "operations and elements the page "
    "itself offered, with a probability per option and no free text. Only when the operation is "
    "TYPE_TEXT does a small LLM write the text to type, and its output must parse as a small "
    "JSON object first. Before acting, the validator rechecks that the page is still fresh, that "
    "the target is still visible and not occluded; a stale page re-observes instead of acting, "
    "and a retry never double-clicks. Then it types Zurich into the Where from? combobox, waits "
    "at most 200 ms for the suggestions, and reads the page again -- 7.1 seconds for the whole "
    "task. Closing point: an LLM writes an answer that code must parse; Jev only picks from the "
    "menu the page itself put up, with a probability attached.")


NEG_STOP = re.compile(r"(?<=[{}])[^{}]*?-\d[\d.]*%[^{}]*\{[^{}]*\}")
ZERO_START_ACTS = 2                            # `.act-1` and `.frost` both open at 0%


def drop_park_before_zero(css):
    """Strip the act keyframes' pre-window park segment when the window starts at 0%.

    `timeline_css_idiom.act_windows` always writes `park -> unpark -> live`, with the park
    running to `start - lead`. Act 1's window starts AT 0% (t0 opens on it), so those two stops
    resolve NEGATIVE, which is not a keyframe selector and describes a moment before the loop
    that does not exist. There is nothing to park before 0%, so the segments are dropped whole.
    """
    out, removed = NEG_STOP.sub("", css), len(NEG_STOP.findall(css))
    if removed != 2 * ZERO_START_ACTS:
        sys.exit(f"drop_park_before_zero: expected {2 * ZERO_START_ACTS} negative-stop "
                 f"segments, found {removed}")
    return out


TITLE_RECT = re.compile(
    r'<rect class="caption-box" x="(?P<x>[-\d.]+)" y="(?P<y>[-\d.]+)" '
    r'width="(?P<w>[\d.]+)" height="(?P<h>[\d.]+)"(?P<rxry>(?: r[xy]="[\d.]+")*) '
    r'data-cap="t0" />')


def pad_title_card():
    """Give the title card DISPLAY padding, from the MEASURED text box. Run after the re-bake.

    `rebake-caption-boxes.mjs` writes every caption card as `text.getBBox()` inflated by its own
    14x8 -- the right padding for a 15px narration line, far too little at display size. This
    step undoes exactly that inflation to recover the measured text box, then re-inflates it by
    TITLE_PAD_X/Y. The only number this file contributes is the padding; the box it pads was
    measured in a browser. `data-pad="title"` is both the idempotence guard and what keeps a
    later re-bake off this one card (rebake-caption-boxes.mjs matches only a rect whose
    `data-cap` is the LAST attribute).
    """
    path = HERE / f"{NAME}.html"
    src = path.read_text(encoding="utf-8")
    if 'data-cap="t0" data-pad="title"' in src:
        sys.exit("pad_title_card: the title card is already padded -- re-run build_cut.py "
                 "and the re-bake first (this step is not idempotent by design)")
    m = TITLE_RECT.search(src)
    if not m:
        sys.exit("pad_title_card: no un-padded cap-t0 caption box found -- did the re-bake run?")
    x, y, w, h = (float(m.group(k)) for k in ("x", "y", "w", "h"))
    tx, ty = x + REBAKE_PAD_X, y + REBAKE_PAD_Y          # the measured text box
    twid, th = w - 2 * REBAKE_PAD_X, h - 2 * REBAKE_PAD_Y
    nx, ny = tx - TITLE_PAD_X, ty - TITLE_PAD_Y
    nw, nh = twid + 2 * TITLE_PAD_X, th + 2 * TITLE_PAD_Y
    if nx < TITLE_X_BOUND[0] or nx + nw > TITLE_X_BOUND[1]:
        sys.exit(f"pad_title_card: the padded card runs {f(nx)}..{f(nx + nw)}, outside "
                 f"x {TITLE_X_BOUND[0]}..{TITLE_X_BOUND[1]} -- drop TITLE_FS and rebuild")
    src = src[:m.start()] + (
        f'<rect class="caption-box" x="{f(nx)}" y="{f(ny)}" width="{f(nw)}" '
        f'height="{f(nh)}"{m.group("rxry")} data-cap="t0" data-pad="title" />') + src[m.end():]
    path.write_text(src, encoding="utf-8")
    print(f"cap-t0 text box (measured) {f(twid)}x{f(th)} at ({f(tx)},{f(ty)})")
    print(f"cap-t0 card {f(nw)}x{f(nh)} at ({f(nx)},{f(ny)}) -- x {f(nx)}..{f(nx + nw)}, "
          f"y {f(ny)}..{f(ny + nh)}; padding {TITLE_PAD_X}x{TITLE_PAD_Y} on the text box")


REDUCED = re.compile(r"@media \(prefers-reduced-motion:reduce\)\{.*?\n\}\n", re.S)


def make_play():
    """The viewing copy. The user's machine has Reduce Motion ON, so the shipped file opens on
    its static end state there -- which is correct, and useless for reviewing the motion. The
    play copy is the SAME file with the reduced-motion block removed and nothing else touched,
    exactly as the morning cut's `.play.html` was made. It is a viewing copy, never a gated
    deliverable."""
    src = (HERE / f"{NAME}.html").read_text(encoding="utf-8")
    out, n = REDUCED.subn("/* viewing copy: reduced-motion block removed */\n", src)
    if n != 1:
        sys.exit(f"make_play: expected exactly one reduced-motion block, found {n}")
    (HERE / f"{NAME}.play.html").write_text(out, encoding="utf-8")
    print(f"{NAME}.play.html written ({len(out)} bytes; reduced-motion block removed)")


def build():
    holds = solve_beats()
    tsv = HERE / f"{NAME}.timeline.tsv"
    tsv.write_text(timeline_tsv(), encoding="utf-8")
    emit = [sys.executable, str(SCRIPTS / "emit_timeline.py"), str(tsv), "--master",
            f"{MASTER_MS}ms", "--beat", f"{GRID_MS}ms"]
    css = subprocess.run(emit + ["--format", "css"], capture_output=True, text=True)
    if css.returncode:
        sys.exit(css.stderr)
    frag = json.loads(subprocess.run(emit + ["--format", "json"], capture_output=True, text=True,
                                     check=True).stdout)
    windows_of = {h["element"]: " ".join(f"{a:g},{z:g}" for a, z in h["windows"])
                  for h in frag["holds"] if h.get("element")}

    cap_sizes = "\n".join(f".cap-{b['id']} text{{font-size:{b['fs']}px}}" for b in BEATS)
    focus = "\n".join(
        f'      <path class="node__focus focus-{b["id"]}" d="{bracket(s, b)}" />'
        for b in BEATS for s in b["subjects"])
    captions = "\n".join(caption_svg(b) for b in BEATS)
    veils = "\n".join(veil(b) for b in BEATS if b["subjects"])
    acts = "\n".join(act_svg(a, windows_of, windows_of[".edge__label"]) for a in (1, 2))

    html = TEMPLATE.format(
        master=f"{MASTER_MS / 1000:g}s", camera=camera_keyframes(),
        timeline=drop_park_before_zero(css.stdout),
        cap_sizes=cap_sizes, desc=esc(DESC), acts=acts, focus=focus, captions=captions,
        veils=veils,
        park1=PARK[1], park2=PARK[2], wash_window=windows_of[".t0-wash"], wash=WASH_OPACITY,
        eyebrow_fs=TITLE_EYEBROW_FS, frost=frost_svg(windows_of[".frost"]),
        frost_x=FROST_REGION[0], frost_y=FROST_REGION[1], frost_w=FROST_REGION[2],
        frost_h=FROST_REGION[3], frost_std=FROST_STD, frost_sat=FROST_SATURATE,
        sub_fs=SUB_FS, sup_label_fs=SUP_LABEL_FS, sup_sub_fs=SUP_SUB_FS,
        row_fs=ROW_FS, badge_fs=BADGE_FS, json_fs=JSON_FS, bars_fs=BARS_FS,
        bars_lbl_fs=BARS_LBL_FS, tag_fs=TAG_FS, strip_fs=STRIP_CELL_FS,
        pulse_ms=PULSE_MS, scale=f"{S:g}", edge_fs=f(EDGE_FS),
        edge_sw=f(sc(1.5)), focus_sw=f(FOCUS_SW), grid=f(sc(20)),
        title_fs=TITLE_CHROME_FS, subtitle_fs=SUBTITLE_FS, legend_fs=LEGEND_FS,
        title_y=TITLE_Y, chip_fs=CHIP_FS, footer_fs=FOOTER_FS)
    (HERE / f"{NAME}.html").write_text(html, encoding="utf-8")

    manifest = {
        "manifest": 1,
        "target": {"file": f"{NAME}.html", "title": "Browser agent: LLM vs Jev",
                   "type": "request-lifecycle", "layout": "layered-tb", "style": "flat-minimal",
                   "palette": "house", "register": "educational", "viewbox": [0, 0, W, H],
                   # beat_ms is the cut's GRID, the unit every slot boundary sits on. t0 is half
                   # the 4800ms house beat, so 4800 no longer divides the master and 2400 is what
                   # the boundaries land on. Every b-beat is still 4800ms = two grid units.
                   "master_ms": MASTER_MS, "beat_ms": GRID_MS},
        "features": ["beats", "acts", "staged-states", "spotlight", "captions",
                     "legend", "reduced-motion-mode", "node-identity"],
        "holds": holds + frag.get("holds", []),
        "captions": frag.get("captions", []),
        "glyphs": [],
        "sources": {
            "types": ["request-lifecycle"], "layouts": ["layered-tb"], "styles": ["flat-minimal"],
            "components": sorted({n["comp"] for n in NODES if n["comp"]}),
            # `is-selected` is the lit action cell (sheet Phase 3 mapping table). Its Motion Ref
            # is `pulse-glow`, whose recipe is a drop-shadow filter -- banned under a moving
            # camera (camera-beat.md), so the row's SEMANTIC is kept and the filter replaced by
            # the documented opacity-only ring-pulse on a static ring, retuned 1600 -> 1800ms so
            # it divides the 64800ms master 36 times.
            "states": ["is-selected"],
            "motion": ["dash-flow", "pulse-glow", "camera-beat"]},
    }
    (HERE / f"{NAME}.manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for b in BEATS:
        print(b["id"], "act", b["act"], b["gate"], "k", b["k"], "fs", b["fs"],
              "card_x", f(b["card_xy"][0]), "bbox", [round(v) for v in b["bbox"]])
    print("master", MASTER_MS, "ms")


TEMPLATE = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Browser agent: LLM vs Jev — 9:16</title>
<!-- GENERATED by build_cut.py from jev-browser-agent-9x16.sheet.md. Do not hand-edit:
     change the sheet, then the generator, then rebuild + re-bake + verify. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap">
<style>
:root{{
  --bg:#f8fafc;--surface:#f8fafc;--grid:color-mix(in srgb, #475569 10%, transparent);
  --ink:#1e293b;--muted:#475569;--stroke:#475569;--radius:8px;
  --font-title:"Inter","Geist",ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --font-label:"Inter","Geist",ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --font-mono:ui-monospace,SFMono-Regular,Menlo,"Roboto Mono",monospace;
  --fs-label:16px;--fs-sub:{sub_fs}px;          /* LOCAL: inside a scaled node group */
  --stroke-w:1.5px;--stroke-w-world:{edge_sw}px; /* the cast is drawn at scale({scale}) */
  --role-client:#dbeafe;   --ink-client:#2563eb;   --accent-client:#3b82f6;   --on-client:#1e40af;
  --role-service:#ffedd5;  --ink-service:#ea580c;  --accent-service:#f97316;  --on-service:#9a3412;
  --role-data:#dcfce7;     --ink-data:#16a34a;     --accent-data:#22c55e;     --on-data:#166534;
  --role-async:#f3e8ff;    --ink-async:#9333ea;    --accent-async:#a855f7;    --on-async:#6b21a8;
  --role-external:#f3f4f6; --ink-external:#4b5563; --accent-external:#6b7280; --on-external:#1f2937;
  --role-error:#fee2e2;    --ink-error:#dc2626;    --accent-error:#ef4444;    --on-error:#991b1b;
  --role-infra:#f1f5f9;    --ink-infra:#475569;    --accent-infra:#14b8a6;    --on-infra:#1e293b;
  --dur-flow:1200ms;
  --dash:8;--dash-gap:6;--dash-cycle:56;
  --master:{master};
}}
*,*::before,*::after{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font-label)}}
.diagram{{margin:0 auto;width:min(100vw,1080px)}}
.diagram__canvas{{display:block;width:min(100vw,1080px);height:auto;background-color:var(--surface)}}

[data-role]{{--fill:var(--role-external);--line:var(--ink-external);--accent:var(--accent-external);--on:var(--on-external)}}
[data-role="client"]  {{--fill:var(--role-client);  --line:var(--ink-client);  --accent:var(--accent-client);  --on:var(--on-client)}}
[data-role="service"] {{--fill:var(--role-service); --line:var(--ink-service); --accent:var(--accent-service); --on:var(--on-service)}}
[data-role="data"]    {{--fill:var(--role-data);    --line:var(--ink-data);    --accent:var(--accent-data);    --on:var(--on-data)}}
[data-role="async"]   {{--fill:var(--role-async);   --line:var(--ink-async);   --accent:var(--accent-async);   --on:var(--on-async)}}
[data-role="infra"]   {{--fill:var(--role-infra);   --line:var(--ink-infra);   --accent:var(--accent-infra);   --on:var(--on-infra)}}

.grid-bg{{fill:url(#grid-dots)}}
.node{{color:var(--line)}}
.node__body{{transform-box:fill-box;transform-origin:center}}
.node__shape{{fill:var(--fill);stroke:var(--line);stroke-width:var(--stroke-w);stroke-linejoin:round;stroke-linecap:round}}
.node__detail{{fill:none;stroke:var(--line);stroke-width:1;opacity:.65;stroke-linecap:round}}
.node__icon{{fill:var(--line);stroke:none;opacity:.9}}
.node__icon .node__detail{{opacity:.9}}
.node__label{{fill:var(--on);font-family:var(--font-label);font-size:var(--fs-label);font-weight:600;text-anchor:middle}}
.node__sub{{fill:var(--on);font-family:var(--font-label);font-size:var(--fs-sub);text-anchor:middle;opacity:.85;font-variant-ligatures:none}}
/* one step down for the sub that would otherwise fill its card to the border: page state's
   act-1 sub measures 197.8 world px at 13px inside a 210px card (SKILL.md: text stays >=6px
   off the border at its own y-band) */
.node__sub--tight{{font-size:12px}}
/* supporting tier: one size step down, box and display label together (SKILL.md Output Rules) */
.node--sup .node__label{{font-size:{sup_label_fs}px}}
.node--sup .node__sub{{font-size:{sup_sub_fs}px}}
.glyph__line{{stroke-width:1.8;opacity:.95}}
.glyph__fill{{fill:var(--surface)}}
.glyph__bar{{fill:var(--line);opacity:.55}}
.glyph__bar--pick{{opacity:1}}
.node--hero .node__icon{{fill:var(--surface)}}
.node--hero .node__detail{{stroke:var(--surface)}}
.node--hero .glyph__bar{{fill:var(--surface)}}
.node--hero .glyph__bar--pick{{fill:var(--accent)}}
.node--hero .glyph__tick{{stroke:var(--accent);stroke-width:2.4}}
.node--primary .node__shape{{stroke-width:calc(var(--stroke-w) * 1.4)}}
/* the delta of the comparison: inverted polarity (ink body, paper text) inside its role's accent
   outline -- the one attention lever that adds no hue to the palette */
.node--hero .node__shape{{fill:var(--ink);stroke:var(--accent);stroke-width:3.5px}}
.node--hero .node__label,.node--hero .node__sub{{fill:var(--surface)}}
.node--hero .node__sub{{opacity:.92}}

/* ---- the page's controls / the page state's table rows: J3, texture class -------------- */
.ctl__badge{{fill:var(--on);opacity:.14;stroke:none}}
.ctl__badgetext{{fill:var(--on);font-family:var(--font-label);font-size:{badge_fs}px;font-weight:500;
  text-anchor:middle;font-variant-ligatures:none}}
.ctl__role{{fill:var(--on);font-family:var(--font-label);font-size:{row_fs}px;opacity:.72;
  font-variant-ligatures:none}}
.ctl__value{{fill:var(--on);font-family:var(--font-label);font-size:{row_fs}px;opacity:.92;
  font-variant-ligatures:none}}
.ctl__box{{fill:var(--surface);stroke:var(--line);stroke-width:1;opacity:.8}}
.ctl__rule{{fill:none;stroke:var(--line);stroke-width:1;opacity:.28}}
/* the page's reaction at b5 / b11: a staged overlay, never a mutation of the row */
.page-react{{opacity:0;animation-duration:var(--master);animation-timing-function:linear;
  animation-iteration-count:infinite}}
.ctl__patch{{fill:var(--surface);stroke:none}}
.ctl__value--typed{{fill:var(--on);opacity:1;font-weight:500}}

/* ---- the `actions` strip: three cells, the step's own one lit ------------------------- */
.cell__box{{fill:var(--surface);stroke:var(--line);stroke-width:1.5}}
.cell__name{{fill:var(--on);font-family:var(--font-label);font-size:{strip_fs}px;
  text-anchor:middle;font-variant-ligatures:none}}
.cell__art{{fill:none}}
.cell__ink{{fill:var(--line);stroke:none;opacity:.9}}
.cell__ring{{fill:none;stroke:var(--line);stroke-width:1.6;opacity:.55}}
.cell__field{{fill:var(--surface);stroke:var(--line);stroke-width:1.2;opacity:.85}}
.cell__caret{{fill:none;stroke:var(--line);stroke-width:1.6;stroke-linecap:round}}
.cell__arrow{{fill:none;stroke:var(--line);stroke-width:1.5;stroke-linecap:round;
  stroke-linejoin:round;opacity:.8}}
.cell__typed{{fill:var(--on);font-family:var(--font-label);font-size:{strip_fs}px;
  font-variant-ligatures:none}}
/* states.csv -> is-selected: the role accent, one step heavier than the cell's CURRENT stroke */
.cell.is-selected .cell__box{{stroke:var(--accent);stroke-width:2.5}}
.cell.is-selected .cell__ink,.cell.is-selected .cell__caret{{stroke:var(--accent)}}
.cell.is-selected .cell__caret{{stroke:var(--accent)}}
/* the two dimmed cells take the muted stroke (sheet CHROME STRINGS) */
.cell.is-dim .cell__box{{stroke:var(--muted);opacity:.7}}
.cell.is-dim .cell__name{{opacity:.6}}
.cell.is-dim .cell__art{{opacity:.55}}
/* pulse-glow's opacity-only substitute: a static ring whose OPACITY alone breathes, on the
   row's own rhythm; 1800ms divides the 64800ms master exactly 36 times */
.cell__pulse{{fill:none;stroke:var(--accent);stroke-width:2;
  animation:cell-ring-pulse {pulse_ms}ms ease-in-out infinite}}
@keyframes cell-ring-pulse{{0%,100%{{opacity:.55}}50%{{opacity:.08}}}}

/* ---- the interior morphs: a DETAIL FACE inside the node, crossfading with the summary -- */
.face-summary{{opacity:1;animation-duration:var(--master);animation-timing-function:linear;
  animation-iteration-count:infinite}}
.face-detail{{opacity:0;animation-duration:var(--master);animation-timing-function:linear;
  animation-iteration-count:infinite}}
.morph__code{{fill:var(--on);font-family:var(--font-mono);font-size:{json_fs}px;
  font-variant-ligatures:none}}
.morph__grouplabel{{fill:var(--on);font-family:var(--font-label);font-size:{bars_lbl_fs}px;
  font-weight:500;opacity:.7;font-variant-ligatures:none}}
.morph__tag{{fill:var(--on);font-family:var(--font-label);font-size:{tag_fs}px;opacity:.6;
  font-variant-ligatures:none}}
.morph__opt{{fill:var(--on);font-family:var(--font-label);font-size:{bars_fs}px;
  font-variant-ligatures:none}}
.morph__bar{{fill:var(--line);opacity:.4}}
.morph__bar--pick{{fill:var(--accent);opacity:1}}
/* the hero keeps its inverted polarity on the detail face too (controller ruling) */
.node--hero .morph__code,.node--hero .morph__opt,
.node--hero .morph__grouplabel,.node--hero .morph__tag{{fill:var(--surface)}}
.node--hero .morph__bar{{fill:var(--surface);opacity:.45}}
.node--hero .morph__bar--pick{{fill:var(--accent);opacity:1}}
/* a string a read hold would cut mid-word is dark for exactly that hold */
.labelfade{{opacity:1;animation-duration:var(--master);animation-timing-function:linear;
  animation-iteration-count:infinite}}

.edge{{fill:none;stroke:var(--stroke);stroke-width:var(--stroke-w-world);stroke-linecap:round;stroke-linejoin:round}}
.edge--primary{{stroke-width:calc(var(--stroke-w-world) * 1.35)}}
.edge--error{{stroke:var(--ink-error);stroke-dasharray:14 5 4 5}}
/* the window itself is emitted with the others; the labels are dark for the whole of t0 */
.edge__label{{fill:var(--muted);font-family:var(--font-label);font-size:{edge_fs}px;text-anchor:middle;font-variant-ligatures:none;
  animation-duration:var(--master);animation-timing-function:linear;animation-iteration-count:infinite}}
.marker{{fill:var(--stroke);stroke:none}}

/* ---- latency chip: a pill on the deciding node, in that node's own role tokens -------- */
.chip__box{{fill:var(--role-service);stroke:var(--ink-service);stroke-width:1.5}}
.chip__text{{fill:var(--on-service);font-family:var(--font-label);font-size:{chip_fs}px;
  font-weight:600;font-variant-ligatures:none}}
/* Jev keeps its inverted polarity, so its pill inverts with it: ink body, paper text inside
   the service accent */
.chip--hero .chip__box{{fill:var(--ink);stroke:var(--accent-service);stroke-width:2}}
.chip--hero .chip__text{{fill:var(--surface)}}
/* the repo credit: scenery, muted, on the heading layer */
.footer{{font:400 {footer_fs}px var(--font-label);fill:var(--muted);text-anchor:middle;
  font-variant-ligatures:none;opacity:.85}}
.title{{font:600 {title_fs}px var(--font-title);fill:var(--ink);text-anchor:middle;letter-spacing:-.01em}}
.subtitle{{font:400 {subtitle_fs}px var(--font-label);fill:var(--muted);text-anchor:middle}}
.legend text{{font:400 {legend_fs}px var(--font-label);fill:var(--ink)}}
.legend .k{{font-weight:600}}

/* ---- motion: templates/snippets/motion-blocks.css, durations snapped to master divisors */
.anim-dash-flow{{stroke-dasharray:var(--dash) var(--dash-gap);stroke-dashoffset:var(--dash-cycle);
  animation:dash-flow var(--dur-flow) linear infinite}}
@keyframes dash-flow{{to{{stroke-dashoffset:0}}}}

/* ---- beats + acts: templates/snippets/camera-beat.css --------------------------------- */
.camera{{transform-origin:0 0;animation:beats var(--master) linear infinite}}
{camera}
.layer-heading{{animation:heading-fade var(--master) linear infinite}}
.act{{opacity:0;animation-duration:var(--master);animation-timing-function:linear;
  animation-iteration-count:infinite}}
.act-1{{transform:{park1}}}
.act-2{{transform:{park2}}}
.beat-caption{{opacity:1;clip-path:inset(-6% 100% -6% -1%);animation-duration:var(--master);
  animation-timing-function:linear;animation-iteration-count:infinite}}
.caption-box{{fill:var(--ink);stroke:none;opacity:.97}}
.caption-spacer{{fill:none;stroke:none}}
.beat-caption text{{fill:var(--surface);font-family:var(--font-label);font-weight:600;
  text-anchor:middle;font-variant-ligatures:none}}
{cap_sizes}
/* ---- t0: the opening title card on a frosted, washed scene --------------------------- */
/* The keywords of the TITLE (never of a narration caption) take the service accent on the
   ink card. Colour is emphasis here, not meaning. */
.cap-t0 .kw{{fill:var(--accent-service)}}
/* line 1 is the EYEBROW, line 2 the display line; the class rides every tspan of line 1 */
.cap-t0 .eyebrow{{font-size:{eyebrow_fs}px}}
/* carries the space that joins the two lines into the manifest's one string, at zero advance */
.cap-t0 .cap-joiner{{font-size:0}}
/* The frosted backdrop. NO CSS `filter:` anywhere in this file -- WebKit drops those on
   elements inside an <svg>, so the blur would exist in Chrome and not in Safari. It is a native
   `filter="url(#frost)"` attribute on this group, applied ONCE and never animated; the group
   itself only fades and then parks off-canvas, exactly like an act. */
.frost{{opacity:0;transform:{park2};
  animation-duration:var(--master);animation-timing-function:linear;animation-iteration-count:infinite}}
.frost__ground{{fill:var(--surface)}}
.frost__box{{fill:var(--fill);stroke:var(--line);stroke-width:2}}
.frost__line{{fill:none;stroke:var(--stroke);stroke-width:2}}
.frost__line--error{{stroke:var(--ink-error)}}
.t0-wash{{fill:var(--surface);fill-opacity:{wash};opacity:0;
  animation-duration:var(--master);animation-timing-function:linear;animation-iteration-count:infinite}}
/* spotlight, second half: in a 9:16 frame several rows are on screen at once, so zoom alone does
   not single the subject out -- the rest of the world is washed toward the paper while it is lit */
.beat-veil__wash{{fill:var(--surface);stroke:none;opacity:.6}}
.beat-veil{{opacity:0;pointer-events:none;
  animation-duration:var(--master);animation-timing-function:linear;animation-iteration-count:infinite}}
.node__focus{{fill:none;stroke:var(--ink);stroke-width:{focus_sw}px;stroke-linecap:square;opacity:0;
  animation-duration:var(--master);animation-timing-function:linear;animation-iteration-count:infinite}}
{timeline}
@media (prefers-reduced-motion:reduce){{
  .camera{{animation:none !important;transform:none !important}}
  .layer-heading{{animation:none !important;opacity:1 !important}}
  .beat-caption{{animation:none !important;opacity:0 !important}}
  /* no title beat at rest: no frost, no wash, no card -- the block already parks act 2 */
  .frost{{animation:none !important;opacity:0 !important;transform:{park2} !important}}
  .t0-wash{{animation:none !important;opacity:0 !important}}
  .edge__label{{animation:none !important;opacity:1 !important}}
  .node__focus,.beat-veil{{animation:none !important;opacity:0 !important}}
  /* the resting visual is the SUMMARY face and an unreacted page; `is-selected` keeps its
     accent stroke and the ring stops breathing, which is the state row's own fallback */
  .face-detail,.page-react{{animation:none !important;opacity:0 !important}}
  .face-summary,.labelfade{{animation:none !important;opacity:1 !important}}
  .cell__pulse{{animation:none !important;opacity:.55 !important}}
  .anim-dash-flow{{animation:none !important;stroke-dasharray:none !important;stroke-dashoffset:0 !important}}
  .edge--error{{stroke-dasharray:14 5 4 5 !important}}
  /* the informative end state is the FINISHED design: act 2 alone */
  .act{{animation:none !important;opacity:0 !important}}
  .act-1{{transform:{park1} !important}}
  .act-2{{opacity:1 !important;transform:none !important}}
}}
</style>
</head>
<body>
<main class="diagram">
  <svg class="diagram__canvas" viewBox="0 0 1080 1920" role="img" aria-labelledby="dgm-title dgm-desc">
    <title id="dgm-title">Browser agent: LLM vs Jev — 9:16</title>
    <desc id="dgm-desc">{desc}</desc>
    <defs>
      <marker id="arrow" class="marker" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7"
              markerHeight="7" orient="auto-start-reverse" markerUnits="strokeWidth">
        <path d="M 0 0 L 10 5 L 0 10 z" />
      </marker>
      <pattern id="grid-dots" width="{grid}" height="{grid}" patternUnits="userSpaceOnUse">
        <circle cx="1.3" cy="1.3" r="1.3" fill="var(--grid)" />
      </pattern>
      <!-- t0's frosted glass. SVG 1.1, so Safari renders it exactly as Chrome does;
           `color-interpolation-filters="sRGB"` makes the two stages match the CSS
           `blur() saturate()` this replaces. The region is user-space and wide enough that
           3*stdDeviation never reaches one of its edges inside the 1080x1920 frame. -->
      <filter id="frost" filterUnits="userSpaceOnUse" x="{frost_x}" y="{frost_y}"
              width="{frost_w}" height="{frost_h}" color-interpolation-filters="sRGB">
        <feGaussianBlur stdDeviation="{frost_std}" />
        <feColorMatrix type="saturate" values="{frost_sat}" />
      </filter>
    </defs>
    <g class="camera">
      <rect class="grid-bg" x="-1080" y="-1920" width="3240" height="5760" />
      <g class="layer-heading">
        <g aria-hidden="true">
          <text class="title" x="540" y="{title_y}">Browser agent: LLM vs Jev</text>
        </g>
      </g>
{acts}
{frost}
      <rect class="t0-wash" x="-1080" y="-1920" width="3240" height="5760"
            data-window="{wash_window}" aria-hidden="true" />
      <g class="layer-veil">
{veils}
      </g>
      <g class="layer-focus">
{focus}
      </g>
      <g class="layer-captions">
{captions}
      </g>
    </g>
  </svg>
</main>
</body>
</html>
"""

if __name__ == "__main__":
    if "--pad-title-card" in sys.argv[1:]:
        pad_title_card()
    elif "--make-play" in sys.argv[1:]:
        make_play()
    else:
        build()
