#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The stdlib DOM reader the act-identity gates share: acts, nodes, edges, ghosts, legend.

Two gate modules ask the same questions of a cut -- which ids does act N draw, what role
and shape does each carry, which edges join them -- so the READING lives here once and the
JUDGING lives in diagram-director/scripts/verify_tier_identity.py and diagram-director/scripts/verify_role_lens.py. A second
reader is how the shape discriminator drifted once already (see `pick_node_shape`).

Instruments: `re` plus a brace-free `<g>`/`</g>` depth walk. No browser, no parser tree --
same instruments stage B already uses, so these gates never report UNVERIFIED. A truncated
act group yields a SHORT body rather than an exception: the gates then report a missing id
or a mismatched delta, which is a diagnostic, not a traceback.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_edge_anchors import node_shapes, pick_node_shape, shape_signature  # noqa: E402

ACT_OPEN = re.compile(r'<g class="act[^"]*"[^>]*data-act="(\d+)"[^>]*data-window="([^"]*)"[^>]*>')
NODE_OPEN = re.compile(r'<g class="node[ "][^>]*>')
GHOST_OPEN = re.compile(r'<g class="[^"]*\bis-ghost\b[^"]*"[^>]*>')
CHIP_OPEN = re.compile(r'<g class="[^"]*\bact-chip\b[^"]*"[^>]*>')
# `.is-ghost … { … fill:none … }`: `[^{}]*` cannot cross a brace, so the `fill:none`
# matched here always belongs to a block whose selector names `.is-ghost`.
GHOST_OUTLINE_RULE = re.compile(r"\.is-ghost[^{}]*\{[^{}]*fill\s*:\s*none", re.S)
EDGE_TAG = re.compile(r'<path class="edge[^"]*"[^>]*>')
G_TAG = re.compile(r"<(/?)g\b[^>]*?(/?)>")
# A tag inside an HTML COMMENT is not drawn, so it is not read (base templates carry examples).
COMMENT = re.compile(r"<!--.*?-->", re.S)
ATTR = r'{}="([^"]*)"'
TRANSLATE = re.compile(r"translate\(\s*(-?[\d.]+)\s*[, ]\s*(-?[\d.]+)")
# `client ×3` / `data x4` -- the count a legend entry claims for the role it labels.
COUNT = re.compile(r"[×x]\s*(\d+)")


def _attr(tag, name, default=""):
    match = re.search(ATTR.format(name), tag)
    return match.group(1) if match else default


def group_body(text, open_match):
    """The inner text of the `<g>` that `open_match` opened, by `<g>`/`</g>` depth.

    Returns everything up to the matching close, or to end-of-text when the group never
    closes -- a malformed cut is stage B's `well-formed` row's business, not a crash here.
    """
    depth, pos = 1, open_match.end()
    for tag in G_TAG.finditer(text, open_match.end()):
        if tag.group(2):                       # <g ... /> -- self-closing, no depth change
            continue
        depth += -1 if tag.group(1) else 1
        if depth == 0:
            return text[open_match.end():tag.start()]
        pos = tag.end()
    return text[open_match.end():max(pos, open_match.end())]


def zone(x, y, viewbox, cols=4, rows=3):
    """The 4x3 viewbox grid cell a point lands in -- the continuity rule's tolerance.

    `references/multi-pane.md` allows a surviving component to anchor NEAR its previous
    position, so identity is compared on CELLS, never on coordinates: a quarter of the
    frame wide and a third of it tall, which frees a nudge and refuses a relocation.
    """
    vx, vy, vw, vh = [float(v) for v in viewbox]
    col = min(cols - 1, max(0, int((float(x) - vx) / vw * cols))) if vw else 0
    row = min(rows - 1, max(0, int((float(y) - vy) / vh * rows))) if vh else 0
    return [col, row]


def _text_of(body, pattern):
    match = re.search(pattern, body, re.S)
    return re.sub(r"<[^>]*>", "", match.group(1)).strip() if match else ""


def read_nodes(body):
    """Every `g.node` in one act body: id, role, classes, origin, shape signature, label."""
    out, body = [], COMMENT.sub("", body)
    for open_match in NODE_OPEN.finditer(body):
        tag = open_match.group(0)
        inner = group_body(body, open_match)
        translate = TRANSLATE.search(_attr(tag, "transform"))
        shape = pick_node_shape(node_shapes(inner))
        # The RENDERED label first: a caption echoes what is drawn on the box, never the
        # `<title>` sentence. `<title>` is the fallback for a node drawn without a label.
        label = _text_of(inner, r'<text class="node__label[^"]*"[^>]*>(.*?)</text>') \
            or _text_of(inner, r"<title>(.*?)</title>")
        out.append({"id": _attr(tag, "data-node-id"), "role": _attr(tag, "data-role"),
                    "classes": _attr(tag, "class").split(),
                    "x": float(translate.group(1)) if translate else 0.0,
                    "y": float(translate.group(2)) if translate else 0.0,
                    "shape": shape_signature(shape), "label": label})
    return out


def read_edges(body):
    """Every `path.edge` in one act body, with the node ids it declares it joins."""
    return [{"from": _attr(tag.group(0), "data-from"),
             "to": _attr(tag.group(0), "data-to"),
             "classes": _attr(tag.group(0), "class").split()}
            for tag in EDGE_TAG.finditer(COMMENT.sub("", body))]


def read_ghosts(body):
    """Retired-component ghosts: `<g class="node-ghost is-ghost" data-ghost-of="id">`.

    A ghost deliberately does NOT carry `data-node-id`: it is the memory of a component,
    not the component. Giving it the id would make the retired node present again and turn
    the act's own delta into a lie -- the exact thing `acts/retired-id-returns` exists for.
    """
    out = []
    for open_match in GHOST_OPEN.finditer(body):
        inner = group_body(body, open_match)
        painted = [m.group(0) for m in node_shapes(inner)
                   if re.search(r'fill\s*[:=]\s*["\']?(?!none)[^;"\'\s]', m.group(0))]
        out.append({"ghost_of": _attr(open_match.group(0), "data-ghost-of"),
                    "shapes": len(node_shapes(inner)), "filled": len(painted)})
    return out


def signed(text):
    """The number a chip slot prints, WITH its sign: `+3` -> 3, `-0` -> 0, `-3` -> -3.

    U+2212 counts as a minus. Reading the magnitude only would let the ADDED slot print
    `-3` and still equal an act that added three -- the sign is half of the claim."""
    flat = text.replace("\u2212", "-").strip()
    magnitude = int(re.sub(r"\D", "", flat) or 0)
    return -magnitude if flat.startswith("-") else magnitude


def read_chips(body):
    """Static delta chips: the `+N` / `-N` a title card prints for its act.

    `added` and `removed` are the SIGNED numbers as printed, so the removed slot is
    expected to be negative -- the judge compares it with `-len(delta.removed)`.
    """
    out = []
    for open_match in CHIP_OPEN.finditer(body):
        inner = group_body(body, open_match)
        add = _text_of(inner, r'<text class="act-chip__add"[^>]*>(.*?)</text>')
        rm = _text_of(inner, r'<text class="act-chip__rm"[^>]*>(.*?)</text>')
        out.append({"added": signed(add), "removed": signed(rm), "raw": f"{add} {rm}"})
    return out


def ghost_outline_rule(html):
    """The stylesheet rule that paints EVERY `.is-ghost` shape as an outline, or None.

    A ghost is judged outline-only from two places, because either one alone is a hole:
    an inline `fill` on the shape (read by `read_ghosts`) and this rule. Deleting the rule
    from the cut's `<style>` repaints every ghost solid while each ghost group still looks
    innocent -- fix-by-deletion, and the gate has to see it.
    """
    for style in re.finditer(r"<style[^>]*>(.*?)</style>", html, re.S):
        match = GHOST_OUTLINE_RULE.search(style.group(1))
        if match:
            return match.group(0)
    return None


def read_acts(html):
    """[{act, window, body}] in document order, one per `<g class="act…" data-act="N">`."""
    acts, html = [], COMMENT.sub("", html)
    for open_match in ACT_OPEN.finditer(html):
        first = (open_match.group(2).split() or [""])[0]
        try:
            window = [float(v) for v in first.split(",")]
        except ValueError:
            window = []
        acts.append({"act": int(open_match.group(1)), "window": window,
                     "body": group_body(html, open_match)})
    return acts


def read_legend(html):
    """[{role, count, text}] for every ROLE entry inside `g.legend`.

    A role entry DECLARES itself: `<text data-legend-role="data">data ×6 …</text>`. The
    attribute is the contract, not the prose, for two reasons. A legend also carries state
    swatches (`--role-warn`, `--role-degrade`) and a weight ladder, which are not roles and
    must not be read as claims about the cast; and an entry that says which role it stands
    for cannot dodge the gate by rewording its own label.
    """
    open_match = re.search(r'<g class="[^"]*\blegend\b[^"]*"[^>]*>', html)
    if not open_match:
        return []
    body = group_body(html, open_match)
    out = []
    for entry in re.finditer(r'<text[^>]*data-legend-role="([a-z-]+)"[^>]*>(.*?)</text>',
                             body, re.S):
        flat = " ".join(re.sub(r"<[^>]*>", " ", entry.group(2)).split())
        match = COUNT.search(flat)
        out.append({"role": entry.group(1),
                    "count": int(match.group(1)) if match else None, "text": flat})
    return out
