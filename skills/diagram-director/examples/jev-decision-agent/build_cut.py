#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generator for jev-decision-agent-9x16: one coordinate table -> HTML + timeline TSV + manifest.

Two acts on one master timeline: ACT 1 is the same support-ticket agent built on a traditional
LLM only, ACT 2 swaps Jev in for the small decisions. Every string here is copied from
jev-decision-agent-9x16.sheet.md (the single source of truth). Geometry is derived from the node
table so edges and spotlight brackets cannot drift from the boxes they attach to.
Windows come from emit_timeline.py and camera poses from solve_camera.py -- nothing on the master
timeline is hand-computed.

Run from the repository root (then re-bake the caption boxes and run verify_all.py):
    python3 diagram-director/examples/jev-decision-agent/build_cut.py
"""
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "scripts"
NAME = "jev-decision-agent-9x16"

W, H = 1080, 1920
SAFE = (60, 150, 890, 1540)                    # x0, y0, x1, y1 -- worst case of Reels/Shorts/TikTok
SAFE_CX, SAFE_CY = (SAFE[0] + SAFE[2]) / 2, (SAFE[1] + SAFE[3]) / 2
BEAT_MS = 4800                                 # the house beat: one slot for b1..b13
# ---- the opening title slot `t0` (sheet DEVIATIONS -> "Opening title beat t0") -----------
# HALF a beat, and the deliverable is a video, so nothing is spent ramping in: at 0ms the
# blur, the wash and the title card are already fully on over act 1. The card holds for
# TITLE_HOLD_MS, then TITLE_OUT_MS sweeps it away while the blur and the wash clear.
TITLE_MS = 2400                                # the whole slot
TITLE_HOLD_MS = 2000                           # card + blur + wash fully on, 0 -> 2000ms
TITLE_OUT_MS = 400                             # card wipe-out, blur and wash clear
TITLE_FS = 66                                  # the DISPLAY line (line 2), frame px
TITLE_EYEBROW_FS = 46                          # line 1, the eyebrow: 0.70 of the display line
TITLE_LINE_EM = 1.4                            # baseline-to-baseline, in the DISPLAY line's em
TITLE_CY = 820                                 # the card's centre: the diagram's body
# The house re-bake pads a caption card 14x8 around its text -- sized for a ~15px narration
# line and far too tight at 66px ("sát mép quá", user review). The title card takes DISPLAY
# padding instead, applied by `--pad-title-card` AFTER the re-bake so it is measured, not
# estimated. Both sit above the review's floors (48 / 32).
TITLE_PAD_X, TITLE_PAD_Y = 56, 36
REBAKE_PAD_X, REBAKE_PAD_Y = 14, 8             # browser-checks/rebake-caption-boxes.mjs
# FROSTED GLASS, not a white-out (sheet DEVIATIONS). blur(60px) + wash .80 hid the diagram
# by WHITENING it, which reads as a pale veil; blur(90px) + wash .35 was worse -- on a canvas
# that is mostly paper, a radius that big averages the cast's pale fills away to nothing
# (measured: max chroma 12/255 across the frame, i.e. flat paper). The fix is the THIRD term:
# a big radius destroys the structure, saturate gives the colour back, the wash knocks the
# contrast down.
#
# It is a NATIVE SVG FILTER on a dedicated backdrop group, not a CSS `filter:` on the scene.
# WebKit does not apply CSS filter FUNCTIONS to elements inside an <svg> -- it honours them on
# HTML elements and on the root <svg> only -- so the CSS form rendered in Chrome (every gate,
# the contact sheet and the MP4 exporter) and was silently dropped in Safari, where the user
# reviews. `filter="url(#frost)"` is SVG 1.1 and renders in both.
FROST_STD = 130                                # feGaussianBlur; CSS blur(130px) == stdDev 130
FROST_SATURATE = 6                             # feColorMatrix type="saturate"
# userSpaceOnUse region, wide enough that 3*stdDev never reaches an edge inside the frame
FROST_REGION = (-400, -400, 1880, 2720)
FROST_ACT = 1                                  # the act the backdrop impersonates
WASH_OPACITY = "0.2"
LABEL_LEAD_MS = 100                            # edge labels come back with the sharp frame
# Every slot boundary of the cut is a multiple of this, so it -- not the 4800ms house beat --
# is the GRID the manifest declares and `keyframe-grid` measures hand-authored stops against.
GRID_MS = 2400
P_MIN = 28                                     # vertical essential-text floor, frame px
LABEL_FS = 16                                  # node label, world px: the other essential text
EDGE_FS = 13                                   # --fs-sub: edge labels, world px
TRUNK_HALF = 9                                 # veil window either side of a lit edge's centreline

# ---- layout grid ------------------------------------------------------------------------
NODE_W, NODE_H = 160, 72
AGENT_W = 190                                  # room for the bot face left of the label
SUP_W, SUP_H = 150, 64                         # supporting tier: one size step down
ROW_TOP, PITCH = 258, 153                      # 46px of air under the subtitle (was 18: too tight)
# The cast is centred on the FRAME (spine near x=540), not on the platform-safe band (centre 475):
# the right rail only covers the lower-right corner, and a column parked 65px left of centre reads
# as a mistake. Every node and label still ends at x <= 890; only the thin stale trunk touches it.
DX = 75
COL = {"L": 210 + DX, "M": 450 + DX, "R": 710 + DX}   # column centre x


def row(i):
    return ROW_TOP + (i - 1) * PITCH


def node(nid, comp, role, shape, col, r, label, sub, title, acts=(1, 2), sup=False, hero=False,
         w=None, dx=0):
    """`sub` and `title` may be {act: text} when the same component says something else per act.

    `dx` nudges ONE node off its column centre without moving the column: the triage LLM takes
    +15 so the `timeout` label has a gap wide enough to sit in without riding either neighbour's
    spotlight bracket. Every edge is computed from node geometry, so they follow it.
    """
    h = SUP_H if sup else NODE_H
    w = w or (SUP_W if sup else NODE_W)
    return dict(id=nid, comp=comp, role=role, shape=shape, x=COL[col] - w / 2 + dx,
                y=row(r) + (NODE_H - h) / 2, w=w, h=h, label=label, sub=sub, title=title,
                acts=acts, sup=sup, hero=hero)


NODES = [
    node("customer", "browser", "client", "device", "M", 1, "customer", "assume 50K/day",
         "customer — sends a ticket on any channel and receives the reply"),
    node("ticket-api", "api-gateway", "service", "hexagon", "M", 2, "ticket API", "all channels in",
         "ticket API — one ingress for tickets from every channel"),
    node("state-builder", "microservice", "service", "rounded", "M", 3, "state builder",
         "state + state_version",
         "state builder — code that merges the ticket with only the facts the questions need into "
         "one versioned state"),
    node("customer-db", "sql-database", "data", "cylinder", "L", 3, "customer db", "account facts",
         "customer db — account, plan and order facts", sup=True),
    node("llm-router", "text-llm", "service", "llm", "M", 4, "LLM router",
         "agent? → JSON",
         "LLM router — a text model asked which agent should take the ticket, answering token by "
         "token", acts=(1,), w=AGENT_W),
    node("jev-gateway", "decision-model", "service", "decider", "M", 4, "Jev gateway",
         "agent? urgent? complaint?",
         "Jev gateway — one request, three questions scored in parallel on the same state: which "
         "agent, how urgent, is it a complaint; a timeout falls back to the triage LLM",
         acts=(2,), hero=True, w=236),
    node("decision-registry", "config-server", "infra", "config", "L", 4, "registry",
         "agents + thresholds",
         "decision registry — versioned questions, the agent list (always with other) and "
         "thresholds per question and per question type", acts=(2,), sup=True),
    node("triage-llm", "text-llm", "service", "llm", "R", 4, "triage LLM",
         "unsure · other",
         "triage LLM — a reasoning model that places the tickets Jev is unsure about, the other "
         "option, and every ticket while Jev is unreachable", acts=(2,), dx=15),
    node("dispatcher", "agent-dispatcher", "service", "fanout", "M", 5, "dispatcher",
         {1: "rules on a label", 2: "prob. vs threshold"},
         {1: "dispatcher — code that hands the ticket to whichever agent the LLM named",
          2: "dispatcher — deterministic code that compares each probability with its threshold "
             "and assigns the ticket with a compare-and-set on state_version"}, w=AGENT_W),
    node("support-agent", "llm-agent", "service", "bot", "L", 6, "support agent", "how-to · account",
         "support agent — customer-care agent for how-to and account questions", w=AGENT_W),
    node("sales-agent", "llm-agent", "service", "bot", "M", 6, "sales agent", "advice · quotes",
         "sales agent — pre-sales advice and quotes", w=AGENT_W),
    node("complaint-agent", "llm-agent", "service", "bot", "R", 6, "complaint agent",
         "classify · resolve", "complaint agent — classifies and works complaints", w=AGENT_W),
    node("outcome-log", "event-stream", "async", "pipe", "M", 7, "outcome log",
         "prob. + outcome",
         "outcome log — every dispatch with its probability and what really happened: resolved, "
         "handed back, escalated", acts=(2,)),
    node("human-desk", "message-queue", "async", "pipe", "R", 7, "human desk",
         {1: "severe cases", 2: "severe · audit sample"},
         {1: "human desk — severe complaints wait for a person",
          2: "human desk — severe complaints and risky actions wait for a person, plus a random "
             "sample of confident dispatches so calibration also sees that band"}),
    node("calibration-monitor", "metrics-collector", "infra", "gauge", "M", 8, "calibration",
         "prob. vs outcome",
         "calibration monitor — compares predicted probability with outcomes per question",
         acts=(2,), sup=True),
]
N = {n["id"]: n for n in NODES}


def cx(i): return N[i]["x"] + N[i]["w"] / 2
def cy(i): return N[i]["y"] + N[i]["h"] / 2
def top(i): return N[i]["y"]
def bot(i): return N[i]["y"] + N[i]["h"]
def left(i): return N[i]["x"]
def right(i): return N[i]["x"] + N[i]["w"]


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def vline(a, z):
    return f"M {f(cx(a))} {f(bot(a))} V {f(top(z))}"


# The stale trunk runs at x=897, 7px right of the cut's own `x <= 890` convention: the
# triage LLM is nudged +15 off its column, so its spotlight bracket ends at x=892 and at
# 890 bracket and trunk touched at that node's two right corners. It is the one element
# allowed past 890 -- a 1.5px line, no label out there (sheet DEVIATIONS).
TRUNK_STALE_X, TRUNK_TUNE_X = 822 + DX, 95 + DX
BRANCH_Y = bot("dispatcher") + 36              # where the agent lanes fan out
MERGE_L_Y = cy("outcome-log") + 4
STALE_Y = cy("dispatcher") + 24
PRIMARY = "edge edge--primary anim-dash-flow"
NOLABEL = (None, 0, 0, "")


def lanes(act, names):
    """dispatcher -> the three agents; `names` = the three edge labels, left to right."""
    dx, by = cx("dispatcher"), bot("dispatcher")
    return [
        (f"e-to-support", (act,), "dispatcher", "support-agent",
         f"M {f(dx - 40)} {f(by)} V {f(BRANCH_Y)} H {f(cx('support-agent'))} "
         f"V {f(top('support-agent'))}", PRIMARY, "end",
         (names[0], (cx("support-agent") + dx - 40) / 2, BRANCH_Y - 8, "middle")),
        (f"e-to-sales", (act,), "dispatcher", "sales-agent", vline("dispatcher", "sales-agent"),
         "edge", "end", (names[1], dx + 9, BRANCH_Y + 22, "start")),
        (f"e-to-complaint", (act,), "dispatcher", "complaint-agent",
         f"M {f(dx + 40)} {f(by)} V {f(BRANCH_Y)} H {f(cx('complaint-agent'))} "
         f"V {f(top('complaint-agent'))}", "edge", "end",
         (names[2], cx("complaint-agent") - 60, BRANCH_Y - 8, "start")),
    ]


# (id, acts, from, to, d, css classes, markers, (label, x, y, anchor))
EDGES = [
    ("e-ticket", (1, 2), "customer", "ticket-api", vline("customer", "ticket-api"), PRIMARY, "both",
     ("ticket · reply", cx("customer") + 12, (bot("customer") + top("ticket-api")) / 2 + 5, "start")),
    ("e-api-state", (1, 2), "ticket-api", "state-builder", vline("ticket-api", "state-builder"),
     PRIMARY, "end", NOLABEL),
    ("e-facts", (1, 2), "customer-db", "state-builder",
     f"M {f(right('customer-db'))} {f(cy('customer-db'))} H {f(left('state-builder'))}", "edge", "end",
     ("facts", (right("customer-db") + left("state-builder")) / 2, cy("customer-db") - 8, "middle")),
    # ---- act 1: a text LLM names the agent ------------------------------------------------
    ("e-state-llm", (1,), "state-builder", "llm-router", vline("state-builder", "llm-router"),
     PRIMARY, "end", NOLABEL),
    ("e-llm-dispatch", (1,), "llm-router", "dispatcher", vline("llm-router", "dispatcher"), PRIMARY,
     "end", ("“sales”", cx("llm-router") - 12, (bot("llm-router") + top("dispatcher")) / 2 + 5,
             "end")),
    *lanes(1, ("“support”", "“sales”", "“complaint”")),
    # ---- act 2: Jev picks the agent, code dispatches on the probability ----------------------
    ("e-state-jev", (2,), "state-builder", "jev-gateway", vline("state-builder", "jev-gateway"),
     PRIMARY, "end", NOLABEL),
    ("e-questions", (2,), "decision-registry", "jev-gateway",
     f"M {f(right('decision-registry'))} {f(cy('decision-registry'))} H {f(left('jev-gateway'))}",
     "edge", "end", ("ask", (right("decision-registry") + left("jev-gateway")) / 2,
                     cy("decision-registry") - 8, "middle")),
    ("e-jev-dispatch", (2,), "jev-gateway", "dispatcher", vline("jev-gateway", "dispatcher"),
     PRIMARY, "end", NOLABEL),
    ("e-fallback", (2,), "jev-gateway", "triage-llm",
     f"M {f(right('jev-gateway'))} {f(cy('jev-gateway'))} H {f(left('triage-llm'))}",
     "edge edge--error", "end", ("timeout", (right("jev-gateway") + left("triage-llm")) / 2,
                                 cy("jev-gateway") - 8, "middle")),
    ("e-unsure", (2,), "dispatcher", "triage-llm",
     f"M {f(right('dispatcher'))} {f(cy('dispatcher') - 10)} H {f(cx('triage-llm'))} "
     f"V {f(bot('triage-llm'))}", "edge", "both",
     ("unsure ⇄ agent", (right("dispatcher") + cx("triage-llm")) / 2, cy("dispatcher") - 18,
      "middle")),
    ("e-thresholds", (2,), "decision-registry", "dispatcher",
     f"M {f(cx('decision-registry'))} {f(bot('decision-registry'))} V {f(cy('dispatcher'))} "
     f"H {f(left('dispatcher'))}", "edge", "end",
     ("thresholds", (cx("decision-registry") + left("dispatcher")) / 2, cy("dispatcher") - 8,
      "middle")),
    *lanes(2, ("confident", "confident", "complaint")),
    ("e-support-log", (2,), "support-agent", "outcome-log",
     f"M {f(cx('support-agent'))} {f(bot('support-agent'))} V {f(MERGE_L_Y)} "
     f"H {f(left('outcome-log'))}", "edge", "end", NOLABEL),
    ("e-sales-log", (2,), "sales-agent", "outcome-log", vline("sales-agent", "outcome-log"),
     PRIMARY, "end", ("resolved · handed back", cx("sales-agent") - 12,
                      (bot("sales-agent") + top("outcome-log")) / 2 + 5, "end")),
    ("e-verdict", (2,), "human-desk", "outcome-log",
     f"M {f(left('human-desk'))} {f(cy('human-desk'))} H {f(right('outcome-log'))}", "edge", "end",
     ("verdict", (left("human-desk") + right("outcome-log")) / 2, cy("human-desk") - 8, "middle")),
    ("e-bins", (2,), "outcome-log", "calibration-monitor",
     vline("outcome-log", "calibration-monitor"), "edge", "end",
     ("outcomes", cx("outcome-log") + 12, (bot("outcome-log") + top("calibration-monitor")) / 2 + 5,
      "start")),
    ("e-tune", (2,), "calibration-monitor", "decision-registry",
     f"M {f(left('calibration-monitor'))} {f(cy('calibration-monitor'))} H {TRUNK_TUNE_X} "
     f"V {f(cy('decision-registry'))} H {f(left('decision-registry'))}", "edge edge--async", "open",
     ("tune thresholds", TRUNK_TUNE_X - 8, row(6) + 60, "rot")),
    # ---- both acts ------------------------------------------------------------------------
    ("e-severe", (1, 2), "complaint-agent", "human-desk", vline("complaint-agent", "human-desk"),
     "edge", "end", ("severe", cx("complaint-agent") + 12,
                     (bot("complaint-agent") + top("human-desk")) / 2 + 5, "start")),
    ("e-stale", (1, 2), "dispatcher", "state-builder",
     f"M {f(right('dispatcher'))} {f(STALE_Y)} H {TRUNK_STALE_X} V {f(cy('state-builder'))} "
     f"H {f(right('state-builder'))}", "edge edge--error", "end",
     ("stale → rebuild", (right("dispatcher") + TRUNK_STALE_X) / 2 + 30, STALE_Y + 17, "middle")),
]
def gap_top(r):                                # top of the free band under row r
    return row(r) + NODE_H


# ---- staged state: is-overloaded on the LLM router (b4 only) -----------------------------
OVERLOAD_NODE = "llm-router"
CHIP_TEXT = "34 IN FLIGHT"                     # S18, via the sheet's CHROME STRINGS
CHIP_W, CHIP_H = 104, 18


def chip_box():
    """The chip's world bbox: top-LEFT of the LLM router, riding its left border.

    state-effects.css puts the pill at the node's top-RIGHT -- but its own collision rule
    says "put the chip on the border's free side", and here the spine
    (`state builder -> LLM router`) lands on the node's top CENTRE, so a right-half pill
    buries that arrowhead and a pill hanging off the right border pushes the shared
    b2-b4 bbox past the read floor. The left border is the free side and costs nothing:
    that shot's bbox is bound by the caption card, 150 world px further left.

    The pill is drawn in WORLD space, not inside the node group: a chip is the one node
    mark that deliberately hangs off the border, and `verify-text-containment.mjs` holds
    every `<text>` inside a `g.node` to that node's shape box with no chip exemption
    (measured: the in-node pill failed it by 83px). Its second sweep then forbids foreign
    text over a node shape, so the pill may overlap the border but its TEXT may not --
    which is what the 14px of pill padding on each side buys.
    """
    x1 = left(OVERLOAD_NODE) + 8               # 8px of the pill sits on the node
    y0 = top(OVERLOAD_NODE) + 4
    return (x1 - CHIP_W, y0, x1, y0 + CHIP_H)


def sbox(nid, b=None):
    """A subject's FULL visual bbox -- the node plus any state chip this beat lights on it.

    camera-beat.md -> Beat spotlight: "A subject's state chip is part of the subject: the
    overlay's box must enclose chip and node together." b2 and b3 stage nothing, so they
    keep the plain node box; only b4 grows.
    """
    l, r, t, bm = left(nid), right(nid), top(nid), bot(nid)
    if b and b.get("stage") == "overload" and nid == OVERLOAD_NODE:
        x0, y0, x1, y1 = chip_box()
        l, r, t, bm = min(l, x0), max(r, x1), min(t, y0), max(bm, y1)
    return l, r, t, bm


                # free column beside rows 3-5, inside the stale trunk

# One entry per slot; `ms` is the slot's own length (default BEAT_MS).
# `cont` = the camera holds the previous pose (no pull-back between).
BEATS = [
    # t0 -- the opening title. No act of its own: it reveals act 1 under a blur + paper wash
    # and hands the frame to b1 sharp. `title` switches the caption to the display card and
    # the camera hold to the card's own 2.0s.
    dict(id="t0", act=1, gate="overview", subjects=[], ms=TITLE_MS, title=True,
         lines=["Kiến trúc hệ thống AI Agents", "without Jev vs with Jev"]),
    dict(id="b1", act=1, gate="overview", subjects=[],
         lines=["Một ticket vào: giao cho agent nào?", "Chưa có Jev, câu này phải hỏi LLM."]),
    # b2..b4 are one shot and share ONE card slot, placed so the WIDEST of the three (b3, and
    # b4 ties it at 40 characters) ends left of the spine that carries this beat's own edge
    # (state builder -> LLM router, x=525). b4 stages `is-overloaded` on the router; its chip
    # rides the node's LEFT border, which costs this shot's bbox nothing (see chip_box).
    dict(id="b2", act=1, gate="read", subjects=["llm-router"], show=["state-builder", "llm-router"],
         card=(265, gap_top(3) + 7),
         lines=["Code chỉ cần một chữ sales,", "nhưng LLM vẫn phải sinh từng token."]),
    dict(id="b3", act=1, gate="read", subjects=["llm-router"], show=["state-builder", "llm-router"],
         card=(265, gap_top(3) + 7), cont=True,
         lines=["Agent chạy nhiều bước: những lần chờ nhỏ", "ở mỗi lựa chọn cứ thế cộng dồn."]),
    dict(id="b4", act=1, gate="read", subjects=["llm-router"], show=["state-builder", "llm-router"],
         card=(265, gap_top(3) + 7), cont=True, stage="overload",
         lines=["Giả sử 50K ticket mỗi ngày: giờ cao điểm",
                "LLM phải gánh khoảng 34 call cùng lúc."]),
    dict(id="b5", act=1, gate="read", subjects=["dispatcher"],
         show=["llm-router", "dispatcher", "sales-agent"], card=(618, gap_top(4) + 7),
         anchor="dispatcher",
         lines=["Chỉ có nhãn, xác suất thì không đáng tin.",
                "Giao nhầm agent, code cũng không biết."]),
    dict(id="b6", act=2, gate="overview", subjects=[],
         lines=["Thêm Jev: model chỉ chọn,", "không sinh text."]),
    # b7: the sheet's shortened caption (longest line 35 chars) is what buys this card a right
    # edge left of the spine -- at 39 it could not clear x=519 without dropping under the floor.
    dict(id="b7", act=2, gate="read", subjects=["jev-gateway", "decision-registry"],
         show=["state-builder", "jev-gateway", "decision-registry"], card=(290, gap_top(3) + 7),
         lines=["Một call, chấm 3 câu hỏi song song:", "khoảng 70–500 ms, có kèm xác suất."]),
    # b8: the lane between the tune-thresholds trunk (x=285) and the spine (x=525) is 240 wide and
    # the card is wider, so the card moves to the gap RIGHT of the spine above the dispatcher and
    # the support lane leaves the frame instead (sheet DEVIATIONS: must-show shrinks).
    dict(id="b8", act=2, gate="read", subjects=["dispatcher"],
         show=["dispatcher", "sales-agent"], card=(583, gap_top(4) + 6),
         lines=["Code so xác suất với threshold:", "đủ cao thì giao thẳng cho agent đó."]),
    # b9: the CAS beat. Must-show is the state builder, the dispatcher and the whole
    # `stale -> rebuild` trunk between them, so the bbox is pinned at 430 (dispatcher's own
    # left edge) and at the trunk's painted band on the right -- 469 world px, which meets the
    # read floor only at `air=0`. Both nodes are still fully in frame: the frame runs 60/k world
    # px left and 190/k right of the safe rect the bbox is fitted to. The card sits in the band
    # between rows 3 and 4, right of the spine and left of the trunk (b10 uses the same slot in
    # its own window).
    # `lit_edges`: the caption is about the TRUNK, not only where it lands, so the veil opens
    # along all three of its legs and over its label as well as over the subject. The spotlight
    # bracket stays on the state builder alone -- the path is lit, the subject is bracketed.
    dict(id="b9", act=2, gate="read", subjects=["state-builder"],
         show=["dispatcher", "state-builder"], card=(636, gap_top(3) + 18),
         air=0, extra=[TRUNK_STALE_X + 2], lit_edges=["e-stale"],
         lines=["Khách nhắn thêm lúc code đang quyết?", "State cũ thì dựng lại rồi mới giao."]),
    # b10's card was nudged +12 off the b9/b10 slot centre: at 612 its left edge sat ON the
    # `state builder -> Jev gateway` spine's painted band. Neither endpoint is a b10 subject, so
    # no subject-edge sweep saw it -- the all-edges sweep does. Free: the bbox is bound by the
    # triage LLM's bracket at 894, so k is unchanged.
    dict(id="b10", act=2, gate="read", subjects=["triage-llm"],
         show=["dispatcher", "triage-llm"], card=(624, gap_top(3) + 7),
         lines=["Lưng chừng, hoặc Jev không trả lời kịp", "thì để triage LLM chọn agent."]),
    # b11's card clears the `outcomes` edge label (it ends at x=597.7) on the right; b12's card
    # owns the other side of that same edge, so the label itself never moves. Three lines (the
    # sheet's own break): the two-line card ran past x=890.
    dict(id="b11", act=2, gate="read", subjects=["complaint-agent", "human-desk"],
         show=["complaint-agent", "human-desk"], card=(685, gap_top(7) + 24),
         lines=["Khiếu nại nặng, hoặc action", "rủi ro như refund thì luôn",
                "phải qua người duyệt."]),
    # b12: left of the spine (outcome log -> calibration, x=525) and centred in the free band
    # between the two subjects' spotlight brackets (outcome-log bottom +13.5 .. calibration top -13.5).
    dict(id="b12", act=2, gate="read", subjects=["outcome-log", "calibration-monitor"],
         show=["sales-agent", "outcome-log", "calibration-monitor"],
         card=(283, gap_top(7) + 16.2),
         lines=["Agent trả ticket về là một lần giao nhầm.", "Lấy log ra so, lệch thì siết threshold."]),
    # the closing overview holds 2x: one slot of caption, one of looking (split into two holds)
    dict(id="b13", act=2, gate="overview", subjects=[], ms=2 * BEAT_MS, split=BEAT_MS,
         lines=["Việc của agent thì để agent làm.", "Chọn agent là Jev, luật giao việc ở code."]),
]


def slot_ms(b):
    return b.get("ms", BEAT_MS)


def start_ms(i):
    """Absolute ms at which slot `i` opens. Slots are no longer uniform (t0 is half a beat),
    so every window in this file is computed from ms and handed to the emitter as ms."""
    return sum(slot_ms(x) for x in BEATS[:i])


MASTER_MS = sum(slot_ms(b) for b in BEATS)     # 69600 = 2400 + 12x4800 + 9600
                                               # = 120x580 = 1200x58 = 2400x29. NOT 4800xN.
MOVE = 600 / MASTER_MS * 100                   # one camera move, percent of master
ACT2_SLOT = next(i for i, b in enumerate(BEATS) if b["act"] == 2)
OVERVIEW_BAND_Y = 1408                         # top of the overview caption band
K_MAX = 2.2                                    # one zoom register across the cut
LINE_H = 1.25                                  # caption line height, em


def est_text_w(s, fs):
    return len(s) * fs * 0.49                  # Inter 600 estimate; the rect is re-baked anyway


def pct_of(ms):
    return ms / MASTER_MS * 100


def slot_start(i):
    return pct_of(start_ms(i))


def solve_beats():
    """k from the SAFE rect (platform UI covers the rest), pose from solve_camera.py."""
    for b in BEATS:
        if b["gate"] == "overview":
            b.update(k=1.0, fs=float(P_MIN), fs_min=13.0, card_xy=(SAFE_CX + DX - 24, OVERVIEW_BAND_Y),
                     bbox=[SAFE[0], SAFE[1], SAFE[2] - SAFE[0], SAFE[3] - SAFE[1]])
            if b.get("title"):                 # the display card, centred on the FRAME
                b.update(fs=float(TITLE_FS),
                         card_xy=(W / 2, TITLE_CY - (2 * TITLE_FS * LINE_H + 16) / 2))
            continue
        # every entry is already an OUTER bound: nodes and the card get 8 of air, a subject's
        # spotlight bracket (pad 12 + half its 3px stroke) and the named extras are taken as-is
        air, brk = b.get("air", 8), 14
        subs = [sbox(n, b) for n in b["subjects"]]
        xs0 = [left(n) - air for n in b["show"]] + [s[0] - brk for s in subs]
        xs1 = [right(n) + air for n in b["show"]] + [s[1] + brk for s in subs]
        ys0 = [top(n) - air for n in b["show"]] + [s[2] - brk for s in subs]
        ys1 = [bot(n) + air for n in b["show"]] + [s[3] + brk for s in subs]
        xs0 += [b["extra_left"]] if "extra_left" in b else []
        xs1 += b.get("extra", [])
        k = 1.9
        for _ in range(3):                     # the card's size depends on k, and k on the card
            fs = round(P_MIN / k + 0.05, 1)
            cw = max(est_text_w(s, fs) for s in b["lines"]) + 28
            ch = len(b["lines"]) * fs * LINE_H + 16
            ccx, cty = b["card"][0] + DX, b["card"][1]
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
    for i, b in enumerate(BEATS):              # beats of one continuous shot share ONE pose
        if b.get("cont"):
            first = BEATS[i - 1]
            k = min(first["k"], b["k"])
            x0 = min(first["bbox"][0], b["bbox"][0])
            y0 = min(first["bbox"][1], b["bbox"][1])
            x1 = max(first["bbox"][0] + first["bbox"][2], b["bbox"][0] + b["bbox"][2])
            y1 = max(first["bbox"][1] + first["bbox"][3], b["bbox"][1] + b["bbox"][3])
            for shot in (first, b):
                shot.update(k=k, bbox=[x0, y0, x1 - x0, y1 - y0], focus=first["focus"])
    for b in BEATS:
        if b["gate"] == "overview":
            continue
        if b["k"] * LABEL_FS < P_MIN:
            sys.exit(f"{b['id']}: k {b['k']} puts the {LABEL_FS}px labels under {P_MIN} frame px")
        b["fs"] = round(P_MIN / b["k"] + 0.05, 1)
        b["fs_min"] = min(b["fs"], float(LABEL_FS))

    holds = []
    for i, b in enumerate(BEATS):
        a_ms = start_ms(i)
        start, end = pct_of(a_ms), pct_of(a_ms + slot_ms(b))
        nxt_cont = i + 1 < len(BEATS) and BEATS[i + 1].get("cont")
        if b.get("title"):                     # the hold IS the card: midpoint = 1000ms
            windows = [(b["id"], 0.0, pct_of(TITLE_HOLD_MS))]
        elif b.get("split"):                   # one hold per beat: caption half, then look half
            cut = pct_of(a_ms + b["split"])
            windows = [(b["id"] + "a", start, cut), (b["id"] + "b", cut, 100.0)]
        elif b["gate"] == "overview":
            windows = [(b["id"], start, end)]
        else:
            windows = [(b["id"], start if b.get("cont") else start + MOVE,
                        end if nxt_cont else end - MOVE)]
        bx, by, bw, bh = b["bbox"]
        k = b["k"]
        if b["gate"] == "overview":
            centre = (W / 2, H / 2)
        else:
            # the world point that lands on the SAFE centre: the beat's focus, clamped so the
            # whole must-show bbox still fits the safe rect
            hw, hh = (SAFE[2] - SAFE[0]) / 2 / k, (SAFE[3] - SAFE[1]) / 2 / k
            # aim the focus at the FRAME centre; the clamp still keeps the bbox inside the safe rect
            want = b["focus"][0] - (W / 2 - SAFE_CX) / k
            sx = min(max(want, bx + bw - hw), bx + hw)
            sy = min(max(b["focus"][1], by + bh - hh), by + hh)
            centre = (sx + (W / 2 - SAFE_CX) / k + b.get("nudge", 0),
                      sy + (H / 2 - SAFE_CY) / k)
        for hid, a, z in windows:
            cmd = [sys.executable, str(SCRIPTS / "solve_camera.py"), "--viewport", f"{W}x{H}",
                   "--bbox", ",".join(f(v) for v in ((0, 0, W, H) if b["gate"] == "overview"
                                                     else b["bbox"])),
                   "--fs-min", str(b["fs_min"]), "--gate", b["gate"], "--k", str(k),
                   "--center", f"{centre[0]:.2f},{centre[1]:.2f}", "--id", hid,
                   "--window", f"{a:.4f},{z:.4f}", "--json"]
            if b["gate"] == "read":
                cmd += ["--fs-min-source",
                        f".cap-{b['id']} text" if b["fs_min"] < LABEL_FS else ".node__label"]
            out = json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
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
# glyph geometry from node-shapes-ml.html#shape-text-model-bubble (the `text-llm` row),
# shifted 4px up for this cut's 72-tall card: a chat bubble with lines of text and a typing
# cursor -- a model that WRITES, token by token. Named because b4's overload overlay re-draws
# the same glyph in the error role on top of its replica.
GLYPH_LLM = ('<g class="node__icon">'
             '<path class="node__detail glyph__line glyph__fill" d="M 17 18 H 43 a 7 7 0 0 1 7 7 V 41 '
             'a 7 7 0 0 1 -7 7 H 28 L 20 56 V 48 H 17 a 7 7 0 0 1 -7 -7 V 25 a 7 7 0 0 1 7 -7 Z" />'
             '<path class="node__detail glyph__line" d="M 17 27 H 43 M 17 34 H 43 M 17 41 H 28" />'
             '<rect x="31" y="37.5" width="4" height="7" rx="1" ry="1" /></g>')


def shape_svg(n):
    w, h, s = n["w"], n["h"], n["shape"]
    if s == "device":
        return (f'<rect class="node__shape" x="0" y="0" width="{w}" height="{h}" rx="8" ry="8" />'
                f'<path class="node__detail" d="M 0 18 H {w}" />'
                '<circle class="node__icon" cx="14" cy="9" r="3" />'
                '<circle class="node__icon" cx="26" cy="9" r="3" />'
                '<circle class="node__icon" cx="38" cy="9" r="3" />', 46, 62)
    if s == "hexagon":
        return (f'<polygon class="node__shape" points="20,0 {w-20},0 {w},{h/2:g} {w-20},{h} '
                f'20,{h} 0,{h/2:g}" />', 33, 51)
    if s == "rounded":
        return (f'<rect class="node__shape" x="0" y="0" width="{w}" height="{h}" rx="8" ry="8" />',
                33, 51)
    if s == "bot":
        # glyph geometry from node-shapes-ml.html#shape-agent-bot (the `llm-agent` row), shifted
        # 4px up for this cut's 72-tall card: the familiar bot face -- antenna, two eyes, ears --
        # left of the label, so three agents read as three of a kind and never as plain services
        face = ('<g class="node__icon">'
                '<path class="node__detail bot__line" d="M 30 24 V 17" />'
                '<circle cx="30" cy="14" r="3" />'
                '<rect class="node__detail bot__line bot__head" x="14" y="24" width="32" height="26" rx="8" ry="8" />'
                '<rect x="9" y="32" width="4" height="10" rx="2" ry="2" />'
                '<rect x="47" y="32" width="4" height="10" rx="2" ry="2" />'
                '<circle cx="24" cy="35" r="3" /><circle cx="36" cy="35" r="3" />'
                '<path class="node__detail bot__line" d="M 24 43 H 36" /></g>')
        return (f'<rect class="node__shape" x="0" y="0" width="{w}" height="{h}" rx="8" ry="8" />'
                + face, 33, 51)
    if s == "llm":
        return (f'<rect class="node__shape" x="0" y="0" width="{w}" height="{h}" rx="8" ry="8" />'
                + GLYPH_LLM, 33, 51)
    if s == "decider":
        # glyph geometry from node-shapes-ml.html#shape-decision-bars (the `decision-model` row),
        # shifted 4px up for this cut's 72-tall card: a probability per option with the pick ticked
        # -- a model that CHOOSES and says how sure it is, and writes nothing
        glyph = ('<g class="node__icon">'
                 '<rect class="glyph__bar" x="12" y="38" width="9" height="14" rx="2" ry="2" />'
                 '<rect class="glyph__bar glyph__bar--pick" x="25" y="24" width="9" height="28" rx="2" ry="2" />'
                 '<rect class="glyph__bar" x="38" y="43" width="9" height="9" rx="2" ry="2" />'
                 '<path class="node__detail glyph__line glyph__tick" d="M 24 15 l 4 4 l 8 -9" />'
                 '<path class="node__detail glyph__line" d="M 9 55 H 50" /></g>')
        return (f'<rect class="node__shape" x="0" y="0" width="{w}" height="{h}" rx="8" ry="8" />'
                + glyph, 33, 51)
    if s == "fanout":
        # glyph geometry from node-shapes-ml.html#shape-dispatch-fanout (the `agent-dispatcher`
        # row), shifted 4px up for this cut's 72-tall card: one stem fanning out to three
        # arrowheads -- in once, out to ONE of many, which is what the three lanes below do
        glyph = ('<g class="node__icon">'
                 '<circle cx="13" cy="36" r="3.5" />'
                 '<path class="node__detail glyph__line" d="M 16 36 H 26 '
                 'M 26 36 C 34 36 34 20 44 20 M 26 36 H 44 M 26 36 C 34 36 34 52 44 52" />'
                 '<path d="M 43 16 L 51 20 L 43 24 Z M 43 32 L 51 36 L 43 40 Z '
                 'M 43 48 L 51 52 L 43 56 Z" /></g>')
        return (f'<rect class="node__shape" x="0" y="0" width="{w}" height="{h}" rx="8" ry="8" />'
                + glyph, 33, 51)
    if s == "cylinder":
        a, r = 12, w / 2
        return (f'<path class="node__shape" d="M 0 {a} A {r:g} {a} 0 0 1 {w} {a} V {h-a} '
                f'A {r:g} {a} 0 0 1 0 {h-a} Z" />'
                f'<path class="node__detail" d="M 0 {a} A {r:g} {a} 0 0 0 {w} {a}" />', 39, 54)
    if s == "pipe":
        return (f'<rect class="node__shape" x="0" y="0" width="{w}" height="{h}" rx="6" ry="6" />'
                f'<g class="queue"><rect class="queue__track" x="12" y="{h-22}" width="{w-24}" '
                f'height="12" rx="4" ry="4" />'
                f'<rect class="queue__fill anim-queue-fill" x="12" y="{h-22}" width="{w-24}" '
                f'height="12" rx="4" ry="4" />'
                f'<path class="node__detail" d="M 46 {h-22} V {h-10} M 80 {h-22} V {h-10} '
                f'M 114 {h-22} V {h-10}" /></g>', 24, 41)
    if s == "gauge":
        # The dial sits 4px higher than the snippet's own y: at y=24 its ink bottom cleared
        # the ink TOP of `calibration` (baseline 40) by 2.8 screen px, under the
        # glyph-label-gap floor of 3. Raising it is free -- the arm still ends 6px inside
        # the card's top border and no other mark lives in that band.
        return (f'<rect class="node__shape" x="0" y="0" width="{w}" height="{h}" rx="8" ry="8" />'
                f'<g class="node__icon"><path class="node__detail" d="M {w-38} 20 A 14 14 0 0 1 '
                f'{w-10} 20" /><path class="node__detail" d="M {w-24} 20 L {w-15} 11" /></g>',
                40, 55)
    if s == "config":
        return (f'<rect class="node__shape" x="0" y="0" width="{w}" height="{h}" rx="4" ry="4" />'
                f'<rect class="node__detail node__detail--dashed" x="7" y="7" width="{w-14}" '
                f'height="{h-14}" rx="2" ry="2" />'
                f'<g class="node__icon"><path class="node__detail" d="M {w-38} 14 H {w-14} '
                f'M {w-38} 22 H {w-14}" /><circle cx="{w-31}" cy="14" r="2.4" />'
                f'<circle cx="{w-21}" cy="22" r="2.4" /></g>', 37, 51)
    raise ValueError(s)


GLYPH_LEFT = ("bot", "llm", "decider", "fanout")   # primary components: glyph left, text right


def per_act(value, act):
    return value[act] if isinstance(value, dict) else value


def overload_overlay(window):
    """states.csv#is-overloaded on the LLM router, EDUCATIONAL register.

    camera-beat.md -> "State intensity is a register property": the full form is a coloured
    replica of the node's own shape (state-effects.css#state-overlay-replica), shake-stress on
    the overlay group, the fill-level bar past its threshold, and the chip carrying the number
    on top of all of it. The base node is never mutated -- the group is a CHILD of the node
    group, sitting between `.node__body` and the node's own label/sub, so label and sub keep
    painting on top of it (camera-beat.md -> "Paint order is invisible to structural gates":
    a replica drawn after the node text erases the label during the beat that explains it).
    The glyph lives inside `.node__body` and would be covered, so it is re-drawn here in the
    error role's own tokens. Local coordinates: the node group is already translated.
    """
    n = N[OVERLOAD_NODE]
    w, h = n["w"], n["h"]
    bx, by, bw, bh = 18, 7, w - 30, 8          # fill-level bar, near the top of the shape
    return (
        f'          <g class="stage stage-overload is-overloaded past-threshold" '
        f'data-role="error" data-window="{window}">\n'
        f'            <g class="anim-shake-stress">\n'
        f'              <rect class="state-replica state-replica--error" x="0" y="0" '
        f'width="{w}" height="{h}" rx="8" ry="8" />\n'
        f'              {GLYPH_LLM}\n'
        f'              <rect class="state-fill-bar__track" x="{bx}" y="{by}" width="{bw}" '
        f'height="{bh}" rx="4" ry="4" />\n'
        f'              <rect class="state-fill-bar" x="{bx}" y="{by}" width="{f(bw * 0.88)}" '
        f'height="{bh}" rx="4" ry="4" />\n'
        f'              <path class="state-fill-bar__mark" d="M {f(bx + bw * 0.7)} {by - 3} '
        f'V {by + bh + 3}" />\n'
        f'            </g>\n'
        f'          </g>\n')


def overload_chip(window):
    """The chip half of the same staged state, in WORLD space (see chip_box).

    Same class, so it takes the same emitted `--win`, and the same annotation, so the
    window verifier sees one condition rendered by two elements.
    """
    x0, y0, x1, _y1 = chip_box()
    return (f'        <g class="stage stage-overload" data-role="error" '
            f'data-window="{window}">\n'
            f'          <g class="anim-shake-stress">\n'
            f'            <rect class="state-chip__box" x="{f(x0)}" y="{f(y0)}" '
            f'width="{CHIP_W}" height="{CHIP_H}" />\n'
            f'            <text class="state-chip__text" x="{f((x0 + x1) / 2)}" '
            f'y="{f(y0 + 13)}">{CHIP_TEXT}</text>\n'
            f'          </g>\n'
            f'        </g>')


def node_svg(n, act, stage_window=None):
    body, ly, sy = shape_svg(n)
    tx = (56 + n["w"] - 4) / 2 if n["shape"] in GLYPH_LEFT else n["w"] / 2
    cls = "node" + ("" if n["sup"] else " node--primary") + (" node--hero" if n["hero"] else "")
    stage = overload_overlay(stage_window) if stage_window and n["id"] == OVERLOAD_NODE else ""
    return (f'        <g class="{cls}" data-node-id="{n["id"]}" data-role="{n["role"]}" '
            f'transform="translate({f(n["x"])},{f(n["y"])})">\n'
            f'          <title>{per_act(n["title"], act)}</title>\n'
            f'          <g class="node__body">{body}</g>\n'
            f'{stage}'
            f'          <text class="node__label" x="{f(tx)}" y="{ly}">{n["label"]}</text>\n'
            f'          <text class="node__sub" x="{f(tx)}" y="{sy}">'
            f'{per_act(n["sub"], act)}</text>\n'
            f'        </g>')


def edge_svg(e, act, label_window=""):
    """`label_window` is the emitted `.edge__label` window: the labels are dark for the whole
    of t0, so the title card never covers one (the blur makes them unreadable regardless)."""
    eid, _acts, a, z, d, cls, mk, (label, lx, ly, anchor) = e
    marker = {"end": 'marker-end="url(#arrow)"',
              "both": 'marker-start="url(#arrow)" marker-end="url(#arrow)"',
              "open": 'marker-end="url(#arrow-open)"'}[mk]
    win = f' data-window="{label_window}"' if label_window else ""
    out = (f'        <g class="edge-group"><path class="{cls}" id="a{act}-{eid}" data-from="{a}" '
           f'data-to="{z}" d="{d}" {marker}><title>{a} to {z}</title></path>')
    if label and anchor == "rot":              # reads bottom-to-top, outside the trunk
        out += (f'<text class="edge__label" x="{f(lx)}" y="{f(ly)}"{win} '
                f'transform="rotate(-90 {f(lx)} {f(ly)})">{label}</text>')
    elif label:
        out += (f'<text class="edge__label" x="{f(lx)}" y="{f(ly)}"{win} '
                f'style="text-anchor:{anchor}">{label}</text>')
    return out + "</g>"


ACT_TITLE = {1: "act 1 · a text LLM picks the agent",
             2: "act 2 · Jev picks, the agents do the work"}
PARK = {1: "translate(0px,-2400px)", 2: "translate(0px,-4800px)"}


def frost_svg(window):
    """t0's backdrop: a STATIC impression of act 1, blurred once by a native SVG filter.

    Not the real scene. One filled shape per act-1 node at its real position and size in its
    role tokens, plus the act's edges as plain strokes, over an opaque paper ground that is
    LARGER than the filter region (so the region holds no edge of it and the blur stays flat
    inside the frame). Under stdDeviation 130 it is indistinguishable from the cut itself.

    Drawing an impression rather than filtering the scene buys three things: the filter is
    STATIC (only opacity and the park transform animate, so no filtered raster is ever
    re-rasterised under the moving camera), the ids are not duplicated, and the group is
    invisible to every gate that reads the graph -- no `class="node"`, no `class="edge"`,
    no `data-node-id`, no text, and `aria-hidden`.
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
    out.append("      </g>")
    return "\n".join(out)


def act_svg(act, window, stage_window="", label_window=""):
    edges = "\n".join(edge_svg(e, act, label_window) for e in EDGES if act in e[1])
    nodes = "\n".join(node_svg(n, act, stage_window if act == 1 else None)
                      for n in NODES if act in n["acts"])
    return (f'      <g class="act act-{act}" data-act="{act}" data-window="{window}">\n'
            f'        <g class="layer-heading" aria-hidden="true">\n'
            f'          <text class="subtitle" x="540" y="208">{ACT_TITLE[act]}</text>\n'
            f'{legend_svg() if act == 2 else ""}\n'
            f'        </g>\n{edges}\n{nodes}\n'
            f'{overload_chip(stage_window) if act == 1 else ""}\n      </g>')


def bracket(nid, b=None):
    pad, arm = 12, 22
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


def edge_rects(eid):
    """A lit edge's veil windows: a thin band along each leg, plus its label's box.

    Read off the edge's own path, so the windows follow the boxes the same way the edge
    does. At a corner the EARLIER leg's band runs TRUNK_HALF past the joint and the later
    one starts that much in, so the corner square is covered exactly once (see `disjoint`).
    Both free ends are butt-cut: the lower leg starts ON the dispatcher's right border and
    the upper one ends on the state builder's, so neither uncovers more of a card than the
    sliver where the edge physically meets it.
    """
    pts = edge_points(eid)
    out = []
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        back = TRUNK_HALF if i else 0.0                    # joint behind: start past its square
        fwd = TRUNK_HALF if i + 2 < len(pts) else 0.0      # joint ahead: cover its square
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
        w = est_text_w(label, EDGE_FS) + 28
        x0 = {"middle": lx - w / 2, "start": lx - 14, "end": lx - w + 14}[anchor]
        out.append((x0, ly - EDGE_FS - 4, x0 + w, ly + 5))
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
    """The same union, re-cut so no two rects overlap.

    The veil is ONE even-odd path: a patch inside two windows is inside three subpaths, so
    it flips back to WASHED. Tiling instead of overlapping is what stops a trunk corner, or
    the label box under the trunk, from painting a grey square over what it uncovers.
    """
    out = []
    for r in rects:
        parts = [r]
        for kept in out:
            parts = [p for q in parts for p in _minus(q, kept)]
        out += parts
    return out


def veil(b):
    """One even-odd path: the whole world minus a window over each subject (bracket-sized)
    and along each edge the beat LIGHTS.

    The subject window is the subject's FULL visual bbox, so b4's grows left to take in the
    overload chip -- node and chip are lit together, b2 and b3 keep the plain node window.
    `lit_edges` adds the beat's own path: b9's sentence is about the `stale -> rebuild`
    trunk, which under the 60% wash read as scenery while the words were about it.
    """
    pad = 12
    wins = [(l - pad, t - pad, r + pad, bm + pad)
            for l, r, t, bm in (sbox(s, b) for s in b["subjects"])]
    for eid in b.get("lit_edges", []):
        wins += edge_rects(eid)
    d = "M -1080 -1920 H 2160 V 3840 H -1080 Z"
    for x0, y0, x1, y1 in disjoint(wins):
        d += f" M {f(x0)} {f(y0)} V {f(y1)} H {f(x1)} V {f(y0)} Z"
    # the GROUP rides the beat's 0..1 spotlight window; the wash inside keeps its own strength
    return (f'      <g class="beat-veil focus-{b["id"]}"><path class="beat-veil__wash" '
            f'fill-rule="evenodd" d="{d}" /></g>')


# The title card's keywords, in the order they occur on their line. Everything between them
# stays paper: colour is EMPHASIS here, not meaning (sheet CHROME STRINGS).
TITLE_KEYWORDS = ("without Jev", "with Jev")


def title_line_fs(i):
    """Line 1 is the EYEBROW, line 2 the display line (user review, third pass)."""
    return TITLE_EYEBROW_FS if i == 0 else TITLE_FS


def title_spans(line, ccx, base_cls=""):
    """One text chunk per line, with the keywords split out into `.kw` tspans.

    Only the FIRST tspan of a line carries `x`, so the whole line is ONE text chunk and
    `text-anchor:middle` centres it as a unit -- a per-tspan `x` would anchor each fragment
    on its own and break the line apart. `base_cls` rides EVERY tspan of the line, because
    it carries the line's font-size: put it on the first one only and a keyword split would
    silently leave the rest of the line at the other size.
    """
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
        out.append(f"<tspan{attrs}{cls}>{text}</tspan>")
    return "".join(out)


def caption_svg(b):
    fs = b["fs"]
    ccx, cty = b["card_xy"]
    n = len(b["lines"])
    cw = max(est_text_w(s, fs) for s in b["lines"]) + 28
    ch = n * fs * LINE_H + 16
    base = cty + 8 + fs * 0.95
    if b.get("title"):
        # Two sizes on one card, so the estimate is per line; the rect is re-baked from the
        # measured text and then re-padded by `--pad-title-card` anyway. The BASELINE is what
        # matters here: it is placed so the measured text box centres on TITLE_CY.
        cw = max(est_text_w(s, title_line_fs(i)) for i, s in enumerate(b["lines"])) + 28
        asc1 = TITLE_EYEBROW_FS * 1.05         # line 1 carries stacked Vietnamese diacritics
        desc2 = TITLE_FS * 0.24
        gap = TITLE_LINE_EM * TITLE_FS
        ch = asc1 + gap + desc2 + 16
        base = TITLE_CY - (asc1 + gap + desc2) / 2 + asc1
        cty = base - asc1 - 8
        # The joiner carries the space that makes textContent the manifest's string (the two
        # lines joined by one space) at ZERO advance, so neither centred line is pushed off
        # x=540 by half a space -- visible at this size, invisible at a narration caption's.
        chunks = []
        for i, s in enumerate(b["lines"]):
            if i:
                chunks.append('<tspan class="cap-joiner"> </tspan>')
            chunk = title_spans(s, ccx, "eyebrow" if i == 0 else "")
            if i:                              # the line's own dy rides its first tspan; the
                                               # em resolves on THAT tspan's (display) size
                chunk = chunk.replace("<tspan", f'<tspan dy="{TITLE_LINE_EM}em"', 1)
            chunks.append(chunk)
        spans = "".join(chunks)
    else:
        spans = "".join(
            f'<tspan x="{f(ccx)}" dy="{0 if i == 0 else LINE_H}em">{s}'
            f'{" " if i < n - 1 else ""}</tspan>'
            for i, s in enumerate(b["lines"]))
    # The spacer widens the group's bbox to the LEFT of the painted card, so the emitter's
    # parked-left clip (a strip 1% wide at the bbox's left edge) holds no antialiased card edge.
    # The title card grows past its estimate in `--pad-title-card`, so its spacer clears the
    # DISPLAY padding too -- otherwise the strip would land inside the finished card.
    spacer_dx = cw / 2 + 40 + (TITLE_PAD_X if b.get("title") else 0)
    return (f'      <g class="beat-caption cap-{b["id"]}">\n'
            f'        <circle class="caption-spacer" cx="{f(ccx - spacer_dx)}" cy="{f(cty + 4)}" r="2" />\n'
            f'        <rect class="caption-box" x="{f(ccx - cw/2)}" y="{f(cty)}" width="{f(cw)}" '
            f'height="{f(ch)}" rx="8" ry="8" data-cap="{b["id"]}" />\n'
            f'        <text x="{f(ccx)}" y="{f(base)}" xml:space="preserve">{spans}</text>\n'
            f'      </g>')


def timeline_tsv():
    rows = ["element\tkind\tkeyframe\twindows\tlead\ttail\twipe\tpark\tseam\ttext\tsource"]
    s2 = start_ms(ACT2_SLOT)
    # Act 1 is lit from 0%: t0 opens ON it, under the blur. There is no hand-over and no loop
    # seam -- the web loop hard-cuts from the closing act-2 overview back to the title card,
    # a deliberate cut (user ruling 2026-09-21), so `.act-2` carries no `seam`.
    rows.append(f".act-1\tact\tact1\t0ms:{s2}ms\t600ms\t600ms\t\t{PARK[1]}\t\t"
                f"\tlayouts:layered-tb")
    rows.append(f".act-2\tact\tact2\t{s2 + 600}ms:100%\t600ms\t\t\t{PARK[2]}\t\t"
                f"\tlayouts:layered-tb")
    # t0's frosted backdrop. An `act` row because it needs exactly what an act needs: lit for
    # its window, then PARKED off-canvas so its filtered raster is never composited under the
    # moving camera. It carries no `data-act` and its class is not `act…`, so the act gates
    # (act_dom_scan.ACT_OPEN) never see it; `acts[]` is not declared, so a third `kind: act`
    # hold is only a park the emitter writes for free.
    rows.append(f".frost\tact\tfrost\t0ms:{TITLE_HOLD_MS}ms\t600ms\t{TITLE_OUT_MS}ms\t"
                f"\t{PARK[2]}\t\t\tmotion:camera-beat")
    # t0's paper wash, over the frost.
    rows.append(f".t0-wash\tstate\tt0-wash\t0ms:{TITLE_HOLD_MS}ms:0ms:{TITLE_OUT_MS}ms"
                f"\t\t\t\t\t\t\t")
    # Edge labels are OFF while the title card is up: under the blur they are unreadable
    # anyway, and a caption card may never cover a VISIBLE edge label (caption-occlusion).
    rows.append(f".edge__label\tstate\tt0-labels\t{TITLE_MS}ms:100%:{LABEL_LEAD_MS}ms"
                f"\t\t\t\t\t\t\t")
    for i, b in enumerate(BEATS):
        if b.get("stage"):
            s = start_ms(i)
            # the SAME window as the beat's spotlight: a red, shaking node that opened 600ms
            # before the wash read as a flash of alarm before the camera had committed
            rows.append(f".stage-{b['stage']}\tstate\tw-{b['stage']}"
                        f"\t{s + BEAT_MS // 4}ms:{s + 3 * BEAT_MS // 4}ms"
                        f"\t\t\t\t\t\t\tstates:is-overloaded")
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
            # the house window, slot-relative: .125 -> .75 (.25 for the act-2 opener). b1 has
            # no special case left -- t0 carries the opening, so b1 gets the normal 3.0s.
            head = BEAT_MS // 4 if i == ACT2_SLOT else BEAT_MS // 8
            start, end, tail, wipe = s + head, s + 3 * BEAT_MS // 4, 432, 408
        rows.append(f".cap-{b['id']}\tcaption\tcap-{b['id']}\t{start}ms:{end}ms\t600ms"
                    f"\t{tail}ms\t{wipe}ms\t\t\t{text}\tmotion:camera-beat")
    return "\n".join(rows) + "\n"


def pct(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") + "%"


def camera_keyframes():
    ease = "animation-timing-function:ease-in-out"
    stops = []                                 # (a, z, transform or None, comment)
    for i, b in enumerate(BEATS):
        start, end = slot_start(i), pct_of(start_ms(i) + slot_ms(b))
        nxt_cont = i + 1 < len(BEATS) and BEATS[i + 1].get("cont")
        if b["gate"] == "overview":
            stops.append((start, end, None, b["id"]))
        elif b.get("cont"):                    # extend the previous hold instead of re-entering
            a, _z, t, c = stops[-1]
            stops[-1] = (a, end if nxt_cont else end - MOVE, t, f"{c}+{b['id']}")
        else:
            k, tx, ty = b["pose"]
            stops.append((start + MOVE, end if nxt_cont else end - MOVE,
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
    # The heading is scenery: on for the three overview slots only. It is also the title, and
    # the title must never be on screen twice -- so it is OFF for the whole of t0 and comes
    # back with the sharp frame at the slot boundary, as the blur and the wash clear.
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
    # NOTHING animates `filter` any more: the frost is a STATIC `filter="url(#frost)"` on its
    # own backdrop group, and only that group's opacity and park transform move -- both
    # emitted. `beats` is the cut's one hand-authored master-length block again.
    return "\n".join(out)


LEGEND = [("client", "customer", 92), ("service", "code · agents", 242), ("data", "db", 424),
          ("async", "desk · log", 524), ("infra", "registry · monitor", 682)]


def legend_svg():
    """The legend is a claim about the FINAL act's cast, so its counts are computed from it."""
    final = max(a for n in NODES for a in n["acts"])
    counts = {}
    for n in NODES:
        if final in n["acts"]:
            counts[n["role"]] = counts.get(n["role"], 0) + 1
    out = ['          <g class="legend">']
    for role, members, x in LEGEND:
        out.append(f'          <rect x="{x}" y="1511" width="16" height="16" rx="4" '
                   f'fill="var(--role-{role})" stroke="var(--ink-{role})" stroke-width="1.8"/>')
        out.append(f'          <text data-legend-role="{role}" x="{x + 22}" y="1524">{role} '
                   f'×{counts[role]} <tspan class="k">{members}</tspan></text>')
    out.append("          </g>")
    return "\n".join(out)


DESC = (
    "A comparison in two acts of one ticket dispatcher: a ticket arrives and the system has to "
    "decide which agent takes it -- the support agent, the sales agent or the complaint agent. "
    "Act 1, without Jev: the ticket API receives tickets from every channel, the state builder "
    "merges the ticket with account facts from the customer db into one versioned state, and an "
    "LLM router is asked which agent should take it. The code needs one word such as sales, yet "
    "the LLM still generates it token by token; in an agent that runs many steps every small "
    "choice is another wait, and on an assumed 50K tickets a day the peak hour leaves the LLM "
    "router overloaded, carrying about 34 calls at once. "
    "The dispatcher gets only a label with no trustworthy probability, so a wrong hand-off goes "
    "unnoticed. Severe complaints go from the complaint agent to the human desk. Act 2, with Jev: "
    "the Jev gateway sends the state and three questions from the decision registry -- which "
    "agent, how urgent, is it a complaint -- in one call; they are scored in parallel in roughly "
    "70 to 500 ms and come back with probabilities. The dispatcher, deterministic code, compares "
    "each probability with its threshold and assigns a confident ticket straight to that agent "
    "with a compare-and-set on state_version; a stale state goes back to the state builder. An "
    "unsure ticket, the other option, or a Jev timeout goes to a triage LLM that picks the agent. "
    "Severe complaints and risky actions such as refunds always wait at the human desk, which also "
    "reviews a random sample of confident dispatches. Every dispatch lands in the outcome log with "
    "its probability and what really happened -- resolved, handed back, escalated -- and the "
    "calibration monitor compares the two and tunes the thresholds in the registry. Closing "
    "point: the agents do the work, Jev picks the agent, and the dispatch rules stay in code.")


NEG_STOP = re.compile(r"(?<=[{}])[^{}]*?-\d[\d.]*%[^{}]*\{[^{}]*\}")
ZERO_START_ACTS = 2                            # `.act-1` and `.frost` both open at 0%


def drop_park_before_zero(css):
    """Strip the act keyframes' pre-window park segment when the window starts at 0%.

    `timeline_css_idiom.act_windows` always writes `park -> unpark -> live`, with the park
    running to `start - lead`. Act 1's window now starts AT 0% (t0 opens on it), so those two
    stops resolve NEGATIVE -- `0%,-0.8721%` and `-0.8621%` -- which is not a keyframe selector
    and describes a moment before the loop that does not exist. There is nothing to park
    before 0%, so the segments are dropped whole; every remaining stop is the emitter's own.
    """
    out, removed = NEG_STOP.sub("", css), len(NEG_STOP.findall(css))
    if removed != 2 * ZERO_START_ACTS:         # two head stops per act row that opens at 0%
        sys.exit(f"drop_park_before_zero: expected {2 * ZERO_START_ACTS} negative-stop "
                 f"segments, found {removed}")
    return out


# The re-baked title-card rect, matched only while it has NOT been padded yet: the post-step
# appends `data-pad="title"` when it is done, which is both its idempotence guard and what
# keeps a later re-bake off this one card -- rebake-caption-boxes.mjs requires `data-cap` to
# be the rect's LAST attribute, so the padded rect stops matching its pattern and survives.
TITLE_RECT = re.compile(
    r'<rect class="caption-box" x="(?P<x>[-\d.]+)" y="(?P<y>[-\d.]+)" '
    r'width="(?P<w>[\d.]+)" height="(?P<h>[\d.]+)"(?P<rxry>(?: r[xy]="[\d.]+")*) '
    r'data-cap="t0" />')


def pad_title_card():
    """Give the title card DISPLAY padding, from the MEASURED text box. Run after the re-bake.

    `rebake-caption-boxes.mjs` writes every caption card as `text.getBBox()` inflated by its
    own 14x8 -- the right padding for a 15px narration line, far too little at 66px. This
    step undoes exactly that inflation to recover the measured text box, then re-inflates it
    by TITLE_PAD_X/Y. Nothing here is estimated: the only number that comes from this file is
    the padding, and the box it pads was measured in a browser.
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
    tw, th = w - 2 * REBAKE_PAD_X, h - 2 * REBAKE_PAD_Y
    nx, ny = tx - TITLE_PAD_X, ty - TITLE_PAD_Y
    nw, nh = tw + 2 * TITLE_PAD_X, th + 2 * TITLE_PAD_Y
    if nx < 80 or nx + nw > 1000:
        sys.exit(f"pad_title_card: the padded card runs {f(nx)}..{f(nx + nw)}, outside "
                 f"x 80..1000 -- drop TITLE_FS and rebuild")
    src = src[:m.start()] + (
        f'<rect class="caption-box" x="{f(nx)}" y="{f(ny)}" width="{f(nw)}" '
        f'height="{f(nh)}"{m.group("rxry")} data-cap="t0" data-pad="title" />') + src[m.end():]
    path.write_text(src, encoding="utf-8")
    print(f"cap-t0 text box (measured) {f(tw)}x{f(th)} at ({f(tx)},{f(ty)})")
    print(f"cap-t0 card {f(nw)}x{f(nh)} at ({f(nx)},{f(ny)}) -- x {f(nx)}..{f(nx + nw)}, "
          f"y {f(ny)}..{f(ny + nh)}; padding {TITLE_PAD_X}x{TITLE_PAD_Y} on the text box")


def build():
    holds = solve_beats()
    tsv = HERE / f"{NAME}.timeline.tsv"
    tsv.write_text(timeline_tsv(), encoding="utf-8")
    # --beat is the GRID, not the house beat: t0 is half a 4800ms beat, so 4800 no longer
    # divides the master and every slot boundary sits on 2400 instead.
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
    acts = "\n".join(act_svg(a, windows_of[f".act-{a}"], windows_of[".stage-overload"],
                             windows_of[".edge__label"]) for a in (1, 2))

    html = TEMPLATE.format(
        master=f"{MASTER_MS / 1000:g}s", camera=camera_keyframes(),
        timeline=drop_park_before_zero(css.stdout),
        cap_sizes=cap_sizes, desc=DESC, acts=acts, focus=focus, captions=captions, veils=veils,
        park1=PARK[1], park2=PARK[2], wash_window=windows_of[".t0-wash"], wash=WASH_OPACITY,
        eyebrow_fs=TITLE_EYEBROW_FS, frost=frost_svg(windows_of[".frost"]),
        frost_x=FROST_REGION[0], frost_y=FROST_REGION[1], frost_w=FROST_REGION[2],
        frost_h=FROST_REGION[3], frost_std=FROST_STD, frost_sat=FROST_SATURATE)
    (HERE / f"{NAME}.html").write_text(html, encoding="utf-8")

    manifest = {
        "manifest": 1,
        "target": {"file": f"{NAME}.html", "title": "AI agents: without Jev vs with Jev",
                   "type": "request-lifecycle", "layout": "layered-tb", "style": "flat-minimal",
                   "palette": "house", "register": "educational", "viewbox": [0, 0, W, H],
                   # beat_ms is the cut's GRID, the unit every slot boundary sits on. It was
                   # the 4800ms house beat while every slot was one; t0 is half a beat, so
                   # 4800 no longer divides the master and 2400 is what the boundaries land
                   # on. Every b-beat is still 4800ms = two grid units.
                   "master_ms": MASTER_MS, "beat_ms": GRID_MS},
        "features": ["beats", "acts", "staged-states", "state-chips", "spotlight", "captions",
                     "legend", "reduced-motion-mode", "node-identity"],
        "holds": holds + frag.get("holds", []),
        "captions": frag.get("captions", []),
        "glyphs": [],
        "sources": {
            "types": ["request-lifecycle"], "layouts": ["layered-tb"], "styles": ["flat-minimal"],
            "components": sorted({n["comp"] for n in NODES}),
            "states": ["is-overloaded"],
            "motion": ["dash-flow", "queue-fill", "camera-beat", "shake-stress"]},
    }
    (HERE / f"{NAME}.manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for b in BEATS:
        print(b["id"], "act", b["act"], b["gate"], "k", b["k"], "fs", b["fs"],
              "bbox", [round(v) for v in b["bbox"]])
    print("master", MASTER_MS, "ms")


TEMPLATE = """<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI agents: without Jev vs with Jev — 9:16</title>
<!-- GENERATED by build_cut.py from jev-decision-agent-9x16.sheet.md. Do not hand-edit:
     change the sheet, then the generator, then rebuild + re-bake + verify. -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap">
<style>
:root{{
  --bg:#f8fafc;--surface:#f8fafc;--grid:color-mix(in srgb, #475569 10%, transparent);
  --ink:#1e293b;--muted:#475569;--stroke:#475569;--stroke-w:1.5px;--radius:8px;
  --font-title:"Inter","Geist",ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --font-label:"Inter","Geist",ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --fs-label:16px;--fs-sub:13px;
  --role-client:#dbeafe;   --ink-client:#2563eb;   --accent-client:#3b82f6;   --on-client:#1e40af;
  --role-service:#ffedd5;  --ink-service:#ea580c;  --accent-service:#f97316;  --on-service:#9a3412;
  --role-data:#dcfce7;     --ink-data:#16a34a;     --accent-data:#22c55e;     --on-data:#166534;
  --role-async:#f3e8ff;    --ink-async:#9333ea;    --accent-async:#a855f7;    --on-async:#6b21a8;
  --role-external:#f3f4f6; --ink-external:#4b5563; --accent-external:#6b7280; --on-external:#1f2937;
  --role-error:#fee2e2;    --ink-error:#dc2626;    --accent-error:#ef4444;    --on-error:#991b1b;
  --role-infra:#f1f5f9;    --ink-infra:#475569;    --accent-infra:#14b8a6;    --on-infra:#1e293b;
  --dur-flow:1200ms;--dur-fill:2400ms;
  --dash:8;--dash-gap:6;--dash-cycle:56;--empty:22%;
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
/* not a node role: the staged is-overloaded overlay re-points the same four tokens so the
   replica, the re-drawn glyph, the bar and the chip all resolve through the ERROR family */
[data-role="error"]   {{--fill:var(--role-error);   --line:var(--ink-error);   --accent:var(--accent-error);   --on:var(--on-error)}}

.grid-bg{{fill:url(#grid-dots)}}
.node{{color:var(--line)}}
.node__body{{transform-box:fill-box;transform-origin:center}}
.node__shape{{fill:var(--fill);stroke:var(--line);stroke-width:var(--stroke-w);stroke-linejoin:round;stroke-linecap:round}}
.node__detail{{fill:none;stroke:var(--line);stroke-width:1;opacity:.65;stroke-linecap:round}}
.node__detail--dashed{{stroke-dasharray:5 4}}
.node__icon{{fill:var(--line);stroke:none;opacity:.9}}
.node__icon .node__detail{{opacity:.9}}
.node__label{{fill:var(--on);font-family:var(--font-label);font-size:var(--fs-label);font-weight:600;text-anchor:middle}}
.node__sub{{fill:var(--on);font-family:var(--font-label);font-size:var(--fs-sub);text-anchor:middle;opacity:.85;font-variant-ligatures:none}}
.glyph__line{{stroke-width:1.8;opacity:.95}}
.glyph__fill{{fill:var(--surface)}}
.glyph__bar{{fill:var(--line);opacity:.55}}
.glyph__bar--pick{{opacity:1}}
.node--hero .node__icon{{fill:var(--surface)}}
.node--hero .node__detail{{stroke:var(--surface)}}
.node--hero .glyph__bar{{fill:var(--surface)}}
.node--hero .glyph__bar--pick{{fill:var(--accent)}}
.node--hero .glyph__tick{{stroke:var(--accent);stroke-width:2.4}}
.bot__line{{stroke-width:1.8;opacity:.95}}
.bot__head{{fill:var(--surface)}}
.node--primary .node__shape{{stroke-width:calc(var(--stroke-w) * 1.4)}}
/* the delta of the comparison: inverted polarity (ink body, paper text) inside its role's accent
   outline -- the one attention lever that adds no hue to the palette */
.node--hero .node__shape{{fill:var(--ink);stroke:var(--accent);stroke-width:3.5px}}
.node--hero .node__label,.node--hero .node__sub{{fill:var(--surface)}}
.node--hero .node__sub{{opacity:.92}}
.queue__track{{fill:var(--on);opacity:.16;stroke:none}}
.queue__fill{{fill:var(--accent);stroke:none}}
.queue .node__detail{{stroke:var(--fill);opacity:.9}}

.edge{{fill:none;stroke:var(--stroke);stroke-width:var(--stroke-w);stroke-linecap:round;stroke-linejoin:round}}
.edge--primary{{stroke-width:calc(var(--stroke-w) * 1.35)}}
.edge--async{{stroke:var(--ink-async);stroke-dasharray:10 7}}
.edge--error{{stroke:var(--ink-error);stroke-dasharray:14 5 4 5}}
/* the window itself is emitted with the others; the labels are dark for the whole of t0 */
.edge__label{{fill:var(--muted);font-family:var(--font-label);font-size:var(--fs-sub);text-anchor:middle;font-variant-ligatures:none;
  animation-duration:var(--master);animation-timing-function:linear;animation-iteration-count:infinite}}
.marker{{fill:var(--stroke);stroke:none}}
.marker--open{{fill:none;stroke:var(--ink-async);stroke-width:1.6;stroke-linecap:round}}

.title{{font:600 34px var(--font-title);fill:var(--ink);text-anchor:middle;letter-spacing:-.01em}}
.subtitle{{font:400 19px var(--font-label);fill:var(--muted);text-anchor:middle}}
.legend text{{font:400 13px var(--font-label);fill:var(--ink)}}
.legend .k{{font-weight:600}}

/* ---- motion: templates/snippets/motion-blocks.css, durations snapped to master divisors */
.anim-dash-flow{{stroke-dasharray:var(--dash) var(--dash-gap);stroke-dashoffset:var(--dash-cycle);
  animation:dash-flow var(--dur-flow) linear infinite}}
@keyframes dash-flow{{to{{stroke-dashoffset:0}}}}
.anim-queue-fill{{clip-path:inset(0 100% 0 0);animation:queue-fill var(--dur-fill) ease-out infinite alternate}}
@keyframes queue-fill{{from{{clip-path:inset(0 100% 0 0)}}to{{clip-path:inset(0 var(--empty) 0 0)}}}}

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
/* ---- t0: the opening title card on a blurred, washed scene --------------------------- */
/* The keywords of the TITLE (never of a narration caption) take the service accent on the
   ink card: 5.8:1 against --ink, well past AA. Colour is emphasis here, not meaning. */
.cap-t0 .kw{{fill:var(--accent-service)}}
/* line 1 is the EYEBROW, line 2 the display line; the class rides every tspan of line 1 */
.cap-t0 .eyebrow{{font-size:{eyebrow_fs}px}}
/* carries the space that joins the two lines into the manifest's one string, at zero
   advance -- so neither centred line is pushed off x=540 by half a space */
.cap-t0 .cap-joiner{{font-size:0}}
/* The frosted backdrop. NO CSS `filter:` anywhere in this file -- WebKit drops those on
   elements inside an <svg>, so the blur existed in Chrome and not in Safari. It is a native
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
/* spotlight, second half: in a 9:16 frame six rows are on screen at once, so zoom alone does not
   single the subject out -- the rest of the world is washed toward the paper while it is lit */
.beat-veil__wash{{fill:var(--surface);stroke:none;opacity:.6}}
.beat-veil{{opacity:0;pointer-events:none;
  animation-duration:var(--master);animation-timing-function:linear;animation-iteration-count:infinite}}
/* ---- staged state: templates/snippets/state-effects.css (is-overloaded, educational) --- */
.stage{{opacity:0;animation-duration:var(--master);animation-timing-function:linear;
  animation-iteration-count:infinite}}
/* state-overlay-replica. Opaque, NOT the snippet's fill-opacity .6: this overlay re-draws the
   router's glyph in the error role on top of the replica, and at .6 the base orange glyph
   ghosted through and the 120ms shake pulled the two copies apart. The node's own label and
   sub still paint on top (#9a3412 on #fee2e2 = 5.9:1, AA). */
.state-replica{{stroke-width:calc(var(--stroke-w) + 0.8px)}}
.state-replica--error{{fill:var(--role-error);stroke:var(--ink-error)}}
.is-overloaded .state-fill-bar{{fill:var(--accent);opacity:.35}}
/* past threshold the bar switches to the error role (states.csv Color Guidance). The snippet
   names `--role-error`, which in this palette is the pale surface tint and would vanish on
   the replica, so the bar takes the same family's saturated member. */
.is-overloaded.past-threshold .state-fill-bar{{fill:var(--accent-error);opacity:1}}
.state-fill-bar__track{{fill:var(--on-error);opacity:.16}}
.state-fill-bar__mark{{fill:none;stroke:var(--on-error);stroke-width:2;opacity:.8}}
/* state-chip: pill + 11px caps; the NUMBER is the story, never a bare red glow */
.state-chip__box{{rx:9px;height:18px;fill:var(--role-error);stroke:var(--ink-error);stroke-width:1.5}}
.state-chip__text{{font-family:var(--font-label);font-size:11px;font-weight:600;
  letter-spacing:.04em;text-transform:uppercase;text-anchor:middle;
  font-variant-ligatures:none;fill:var(--on-error)}}
/* motion-recipes.md#shake-stress -- on the OVERLAY group only; 120ms divides the master 560x */
.anim-shake-stress{{animation:shake-stress 120ms linear infinite}}
@keyframes shake-stress{{
  0%,100%{{transform:translate(-1.5px,0)}}
  25%{{transform:translate(1.2px,-.6px)}}
  50%{{transform:translate(-1.1px,.6px)}}
  75%{{transform:translate(1.5px,0)}}
}}
.node__focus{{fill:none;stroke:var(--ink);stroke-width:3px;stroke-linecap:square;opacity:0;
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
  .node__focus,.beat-veil,.stage{{animation:none !important;opacity:0 !important}}
  .anim-shake-stress{{animation:none !important;transform:none !important}}
  .anim-dash-flow{{animation:none !important;stroke-dasharray:none !important;stroke-dashoffset:0 !important}}
  .edge--async{{stroke-dasharray:10 7 !important}}
  .edge--error{{stroke-dasharray:14 5 4 5 !important}}
  .anim-queue-fill{{animation:none !important;clip-path:inset(0 var(--empty) 0 0) !important}}
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
    <title id="dgm-title">AI agents: without Jev vs with Jev</title>
    <desc id="dgm-desc">{desc}</desc>
    <defs>
      <marker id="arrow" class="marker" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7"
              markerHeight="7" orient="auto-start-reverse" markerUnits="strokeWidth">
        <path d="M 0 0 L 10 5 L 0 10 z" />
      </marker>
      <marker id="arrow-open" class="marker marker--open" viewBox="0 0 10 10" refX="9" refY="5"
              markerWidth="8" markerHeight="8" orient="auto-start-reverse" markerUnits="strokeWidth">
        <path d="M 0 0 L 10 5 L 0 10" fill="none" />
      </marker>
      <pattern id="grid-dots" width="20" height="20" patternUnits="userSpaceOnUse">
        <circle cx="1" cy="1" r="1" fill="var(--grid)" />
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
          <text class="title" x="540" y="180">AI agents: without Jev vs with Jev</text>
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
    else:
        build()
