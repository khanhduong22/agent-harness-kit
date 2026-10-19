#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Static connector check for generated diagrams: every edge's head and tail
must be rooted on a node, ON THE SIDE THAT FACES THE EDGE.

Two defect classes, both review-caught before the check covered them:

  FLOATING    a path whose first point sits 20px past its node's corner
              renders as a dash head connected to nothing.
  WRONG-SIDE  a path whose endpoint IS on the node boundary but on a side
              the edge had to wrap around to reach -- the enqueue run in
              `examples/progressive-500k-5tier.html` arrived from the right
              and landed mid-way across the queue's TOP border. Anchoring
              alone cannot see this: the endpoint is legitimately on the box.

Runs on the raw HTML with no browser -- usable in any environment the skill
runs in.

What is checked, per `<path class="edge ...">`:
  - ANCHORING. START (tail) and END (head) of the path's `d` must each lie
    within `--tol` px (default 12, covering arrowhead shortening) of some
    node shape's bounding box.
  - NEAREST SIDE. The endpoint must sit on the side of that box whose
    OUTWARD NORMAL faces where the edge actually goes -- its next vertex
    (the far endpoint on a two-point path). Formally: with `n` the unit
    outward normal of the side the endpoint sits on and `r` the departure
    vertex, `n · (r - p) > -tol`. That dot product is the signed distance
    from `r` to the plane of that side, so the rule reads "the edge's next
    vertex must be outside the side it attaches to, give or take `tol`".
    Within `tol` px of a corner BOTH adjacent sides count, which is what
    lets a diagonal edge land on a corner honestly.
    Calibration: under this rule every endpoint in all three SVG-mode goldens
    and all three acceptance diagrams scores >= 0, so the `tol` slack is
    pure headroom, not a threshold fitted around an existing violation.
    (The departure vertex, not the far endpoint, is what makes that true:
    an elbowed mesh edge in `compare-chat-pubsub.html` leaves the bottom of
    ws-1 and turns; measured against its FAR endpoint it would score -2.)

Node boxes come from each `<g class="node ...">`'s real `.node__shape`
(rect / polygon / circle / path), mapped through EVERY `<g transform>` between
the node group and the shape -- `translate()` and `scale()`, composed in
document order. The `scale()` leg is not optional: `templates/snippets/
node-shapes.html` makes a `<g transform="scale(k)">` wrapper around the
`.node__body` THE sanctioned way to resize a node (hub at 1.25, receded tiers
at 0.85), so a parser that reads only the group translate measures those nodes
at their unscaled size and reports correct endpoints as floating. Path shapes
(cylinders, clouds) get an extra pad because their arcs bulge past their
command endpoints; this is an anchoring check, not exact geometry.

Two node-shaped things that are NOT `.node__shape` also anchor an endpoint,
because the diagram idioms they belong to genuinely terminate edges on them:

  LIFELINE     a swimlane `<path class="lane-line">`. In sequence/swimlane
               semantics the actor box sits in the lane-label column and its
               dashed lifeline carries the lane across the canvas; messages
               land on the LIFELINE, which is part of the participant, exactly
               as in UML. See `lane_lines()` for the structural tie that keeps
               this from being a blanket exemption.
  CLUSTER      a `<rect class="group__box">` boundary. A labelled cluster is a
               real target -- `examples/03` routes the cluster's active-zone
               connector onto the AZ boundary, because the zone IS the
               boundary (the standby zone, which groups nothing, is a node and
               is anchored as one). Only the boundary LINE anchors, never the
               interior: see `on_group_border()`.

Usage: python3 diagram-director/scripts/verify_edge_anchors.py file.html [more.html] [--tol 12]
Exit 0 when every endpoint anchors on a facing side; 1 otherwise, listing
each defect.
"""

import argparse
import re
import sys

NUM = r"-?\d+(?:\.\d+)?"
PATH_SHAPE_PAD = 22  # arc bulge allowance for path-drawn shapes (cylinder ry)


def _floats(text):
    return [float(v) for v in re.findall(NUM, text)]


def _compose(state, tag):
    """Fold a tag's `transform="..."` into (tx, ty, sx, sy), in written order.

    Only translate/scale: rotate/skew/matrix are refused up front by
    UNSUPPORTED, so anything reaching here is axis-aligned and a box stays a
    box. `world = t + s * local`, so a nested transform scales by the scale
    already accumulated above it.
    """
    tx, ty, sx, sy = state
    m = re.search(r'transform="([^"]*)"', tag)
    if not m:
        return state
    for fn, args in re.findall(r'(translate|scale)\(([^)]*)\)', m.group(1)):
        v = _floats(args)
        if not v:
            continue
        if fn == "translate":
            tx += sx * v[0]
            ty += sy * (v[1] if len(v) > 1 else 0.0)
        else:
            sx *= v[0]
            sy *= v[1] if len(v) > 1 else v[0]
    return (tx, ty, sx, sy)


def _ctm_at(body, base, pos):
    """The composed transform in force at offset `pos` inside a node group.

    Replays the `<g>` opens and `</g>` closes that precede `pos` as a stack, so
    a shape wrapped in `<g class="node__body"><g transform="scale(1.25)">`
    inherits both. Without this replay the sanctioned scale wrapper is invisible
    and the node measures at its unscaled size.
    """
    stack = [base]
    for m in re.finditer(r'<(/?)g\b[^>]*?(/?)>', body):
        if m.start() >= pos:
            break
        closing, self_closing = m.group(1), m.group(2)
        if closing:
            if len(stack) > 1:
                stack.pop()
        elif not self_closing:
            stack.append(_compose(stack[-1], m.group(0)))
    return stack[-1]


NODE_SHAPE = re.compile(r'<(rect|polygon|circle|path)\s[^>]*>')


def node_shapes(body):
    """Every `.node__shape` element inside a node group's body, in painter's order."""
    return [m for m in NODE_SHAPE.finditer(body) if "node__shape" in m.group(0)]


def pick_node_shape(shapes):
    """WHICH SHAPE IS THE NODE -- keyed on STRUCTURE, not on markup spelling.

    A node group may stack several `.node__shape` elements: replica-count ghosts,
    offset by -14/-7px, then the real body. Two structural facts pick the body, in
    order:
      1. an explicit ghost class (`node__ghost--1/2`) marks a replica, so drop those
         -- examples/progressive-500k-5tier.html;
      2. whatever is left is in PAINTER'S ORDER, and the body is the one drawn on
         top, i.e. the LAST -- examples/progressive-500k-ccu.html and
         compare-chat-pubsub.html, whose ghosts carry no class at all and are always
         emitted before the body.
    The previous heuristic keyed on the literal substring `opacity` inside an inline
    `style=`; moving ghost opacity into a CSS class (which the veteran-recede ladder
    needs) silently re-pointed the checker at the ghost's offset box and five correct
    endpoints reported FLOATING.

    It lives as a function because a SECOND reader needs the same answer:
    diagram-director/scripts/verify_tier_identity.py builds a node's shape signature from it, and a
    duplicated discriminator is exactly what caused those five false floaters.
    """
    if not shapes:
        return None
    real = [m for m in shapes if "ghost" not in m.group(0)]
    return (real or shapes)[-1]


def shape_signature(shape):
    """`tag|class-token class-token` for the shape a node is drawn with.

    The IDENTITY discriminator: two acts drawing the same id must draw it with the
    same tag and the same shape classes. Class tokens are sorted so DOM order cannot
    make one node look like two.
    """
    if shape is None:
        return ""
    match = re.search(r'class="([^"]*)"', shape.group(0))
    tokens = sorted((match.group(1) if match else "").split())
    return f"{shape.group(1)}|{' '.join(tokens)}"


def node_boxes(html):
    """(x0, y0, x1, y1) per node group, world coordinates."""
    boxes = []
    # Two-step on purpose. A single regex with a lazy prefix and an OPTIONAL
    # transform group silently matches the group as empty (the lazy quantifier
    # never expands once the rest of the pattern succeeds), so every node came
    # back at translate(0,0) and every endpoint "floated". Match the open tag,
    # then read the transform out of the matched tag text.
    opens = list(re.finditer(r'<g class="node[ "][^>]*>', html))
    for i, gm in enumerate(opens):
        tag = gm.group(0)
        base = _compose((0.0, 0.0, 1.0, 1.0), tag)
        end = opens[i + 1].start() if i + 1 < len(opens) else len(html)
        body = html[gm.end():end]
        shapes = node_shapes(body)
        shape = pick_node_shape(shapes)
        if shape is None:
            continue
        tag, attrs = shape.group(1), shape.group(0)

        def attr(name, default=0.0):
            m = re.search(name + r'="(' + NUM + r')"', attrs)
            return float(m.group(1)) if m else default

        if tag == "rect":
            x, y = attr("x"), attr("y")
            box = (x, y, x + attr("width"), y + attr("height"))
        elif tag == "circle":
            cx, cy, r = attr("cx"), attr("cy"), attr("r")
            box = (cx - r, cy - r, cx + r, cy + r)
        elif tag == "polygon":
            pts = _floats(re.search(r'points="([^"]*)"', attrs).group(1))
            xs, ys = pts[0::2], pts[1::2]
            box = (min(xs), min(ys), max(xs), max(ys))
        else:  # path shape: hull of the points the commands actually visit.
            # Never hull over raw floats -- an arc's rx/ry/flags interleave
            # with coordinates and mis-pair everything (a cylinder came back
            # 250px tall the wrong way before this used the command walker).
            pts = _walk(re.search(r'd="([^"]*)"', attrs).group(1)) or []
            if not pts:
                continue
            xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
            box = (min(xs) - PATH_SHAPE_PAD, min(ys) - PATH_SHAPE_PAD,
                   max(xs) + PATH_SHAPE_PAD, max(ys) + PATH_SHAPE_PAD)
        tx, ty, sx, sy = _ctm_at(body, base, shape.start())
        wx = sorted((box[0] * sx + tx, box[2] * sx + tx))
        wy = sorted((box[1] * sy + ty, box[3] * sy + ty))
        boxes.append((wx[0], wy[0], wx[1], wy[1]))
    return boxes


def _walk(d):
    """Every on-path anchor point an absolute M/L/H/V/A/Z path visits."""
    tokens = re.findall(r"([MLHVAZmlhvaz])|(" + NUM + r")", d)
    x = y = None
    visited = []
    cmd = None
    nums = []
    def flush():
        nonlocal x, y, nums
        if cmd in ("M", "L"):
            for i in range(0, len(nums) - 1, 2):
                x, y = nums[i], nums[i + 1]
                visited.append((x, y))
        elif cmd == "H":
            for v in nums:
                x = v; visited.append((x, y))
        elif cmd == "V":
            for v in nums:
                y = v; visited.append((x, y))
        elif cmd == "A" and len(nums) >= 7:
            x, y = nums[-2], nums[-1]
            visited.append((x, y))
        nums.clear()
    for letter, number in tokens:
        if letter:
            flush()
            if letter in "mlhva":
                return None  # relative commands unsupported
            cmd = letter.upper()
        else:
            nums.append(float(number))
    flush()
    return visited


SIDES = (("left", -1.0, 0.0), ("right", 1.0, 0.0),
         ("top", 0.0, -1.0), ("bottom", 0.0, 1.0))


def facing_side(pt, ref, box, tol):
    """(ok, side, depth) for an endpoint `pt` on `box` departing towards `ref`.

    The side the endpoint sits on is the nearest one; anything within `tol` of
    that distance counts too, so a corner landing is judged on BOTH its sides.
    `depth` is the best signed distance from `ref` to those sides' planes --
    positive means the edge leaves outward, negative means it had to wrap.
    """
    x0, y0, x1, y1 = box
    dist = {"left": abs(pt[0] - x0), "right": abs(pt[0] - x1),
            "top": abs(pt[1] - y0), "bottom": abs(pt[1] - y1)}
    near = min(dist.values())
    best, best_side = None, None
    for name, nx, ny in SIDES:
        if dist[name] > near + tol:
            continue
        depth = nx * (ref[0] - pt[0]) + ny * (ref[1] - pt[1])
        if best is None or depth > best:
            best, best_side = depth, name
    return best > -tol, best_side, best


def _extends_from(lb, box):
    """True when bbox `lb` lies inside `box`'s span on one axis and begins at or
    beyond `box`'s edge on the other -- i.e. it runs OUT of the node.

    The `PATH_SHAPE_PAD` slack on the outward axis is the same over-approximation
    the pad itself is: a path-drawn node's box is deliberately inflated by that
    much for arc bulge, so example 01's Postgres cylinder reaches 2px past the
    lane-label column and would otherwise be judged to OVERLAP the very lifeline
    it owns. The slack is bounded by an existing constant, not fitted to the
    2px it happens to cover here.
    """
    x0, y0, x1, y1 = box
    p = PATH_SHAPE_PAD
    return ((y0 <= lb[1] and lb[3] <= y1 and (lb[2] < x0 + p or lb[0] > x1 - p)) or
            (x0 <= lb[0] and lb[2] <= x1 and (lb[3] < y0 + p or lb[1] > y1 - p)))


def lane_lines(html, boxes):
    """Swimlane lifelines that are structurally a node's extension.

    `<path class="lane-line">` is the per-lane dashed baseline a swimlane
    diagram draws from the lane-label column across the canvas; the actor's box
    sits in that column, centred on the line, and every message arrow lands on
    the LINE, not on the box. That is the idiom, not a shortcut: eight hops all
    leaving one 160x80 box would not be a sequence diagram.

    The tie that stops this from being a blanket exemption: a lane line anchors
    only if some node's span CONTAINS it on its degenerate axis (it runs through
    that actor's vertical centre) while staying clear of that node on the other
    (it extends away from the box). A dashed rule drawn in open canvas, or one
    slid off its actor's lane, matches no node and anchors nothing -- the
    endpoints on it go straight back to FLOATING.
    """
    lines = []
    for m in re.finditer(r'<path class="lane-line[ "][^>]*\sd="([^"]+)"', html):
        pts = _walk(m.group(1))
        if not pts or len(pts) < 2:
            continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        lb = (min(xs), min(ys), max(xs), max(ys))
        if any(_extends_from(lb, b) for b in boxes):
            lines.append(pts)
    return lines


def _seg_dist(p, a, b):
    """Distance from point `p` to segment `a`-`b`."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    span = dx * dx + dy * dy
    t = 0.0 if span == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / span))
    return ((p[0] - a[0] - t * dx) ** 2 + (p[1] - a[1] - t * dy) ** 2) ** 0.5


def on_lane_line(pt, ref, lines, tol):
    """Endpoint sits on a lifeline AND the edge actually leaves it.

    The second half is the lifeline's answer to the nearest-side rule: a line
    has no sides to wrap around, but an edge drawn ALONG the lifeline touches it
    everywhere and attaches nowhere, so the departure vertex must be off it.
    Sitting past the lifeline's END fails too -- `_seg_dist` is measured to the
    SEGMENT, not to its infinite line.
    """
    for pts in lines:
        for a, b in zip(pts, pts[1:]):
            if _seg_dist(pt, a, b) <= tol and _seg_dist(ref, a, b) > tol:
                return True
    return False


def group_boxes(html):
    """(x0, y0, x1, y1) per `.group__box` cluster boundary, world coordinates."""
    boxes = []
    opens = list(re.finditer(r'<g class="group[ "][^>]*>', html))
    for i, gm in enumerate(opens):
        base = _compose((0.0, 0.0, 1.0, 1.0), gm.group(0))
        end = opens[i + 1].start() if i + 1 < len(opens) else len(html)
        body = html[gm.end():end]
        for rm in re.finditer(r'<rect\s[^>]*>', body):
            if "group__box" not in rm.group(0):
                continue
            attrs = rm.group(0)

            def attr(name):
                m = re.search(name + r'="(' + NUM + r')"', attrs)
                return float(m.group(1)) if m else 0.0

            tx, ty, sx, sy = _ctm_at(body, base, rm.start())
            x, y = attr("x"), attr("y")
            wx = sorted((x * sx + tx, (x + attr("width")) * sx + tx))
            wy = sorted((y * sy + ty, (y + attr("height")) * sy + ty))
            boxes.append((wx[0], wy[0], wx[1], wy[1]))
    return boxes


def on_group_border(pt, ref, gboxes, tol):
    """Endpoint terminates ON a labelled cluster boundary, facing outward.

    A cluster that holds contents is drawn as a boundary rather than a node, and
    an edge addressed to the cluster has nothing else to land on -- in
    `examples/03` the active AZ is a boundary (it groups three autoscaling
    groups) while the standby AZ, grouping nothing, is a plain node.

    Only the boundary LINE anchors. Cluster boxes are hundreds of px across, so
    reusing the node rule's "inside the padded box" test would let an endpoint
    dropped anywhere in the cluster's empty middle count as attached; requiring
    the endpoint within `tol` of a side keeps a floater a floater. The facing
    rule then applies unchanged.
    """
    for box in gboxes:
        x0, y0, x1, y1 = box
        if not (x0 - tol <= pt[0] <= x1 + tol and y0 - tol <= pt[1] <= y1 + tol):
            continue
        if min(abs(pt[0] - x0), abs(pt[0] - x1),
               abs(pt[1] - y0), abs(pt[1] - y1)) > tol:
            continue
        if facing_side(pt, ref, box, tol)[0]:
            return True
    return False


UNSUPPORTED = (
    # nested/warped coordinate systems this static parser cannot follow;
    # for these styles rely on the browser-side sweep in the delivery checks
    (r'transform="[^"]*(?:rotate|matrix|skew)', "rotated/skewed node transforms"),
    (r'<g class="panel" transform=', "panel-wrapped nodes (comic-storytelling)"),
    (r'<g class="iso', "isometric projection groups"),
)


def check_file(path, tol):
    html = open(path, encoding="utf-8").read()
    for pattern, why in UNSUPPORTED:
        if re.search(pattern, html):
            print(f"SKIP {path}: {why} -- outside this checker's flat-translate scope")
            return []
    boxes = node_boxes(html)
    if not boxes:
        # Two real cases, and neither is a pass: ascii-terminal renders its nodes in a
        # <pre>, and an HTML-MODE cut (the `process` genre) draws div stations under a
        # geometry-only SVG overlay, so there is no `.node__shape` to face. The latter
        # is checked instead by diagram-director/scripts/browser-checks/verify-html-edge-anchors.mjs,
        # which verify_all.py dispatches to on `manifest.genre` -- run that, not this.
        print(f"SKIP {path}: no .node__shape geometry -- ascii-terminal renders in a "
              f"<pre>, and an HTML-mode cut is checked by verify-html-edge-anchors.mjs")
        return []
    lanes = lane_lines(html, boxes)
    gboxes = group_boxes(html)
    problems = []
    # \s before d= is load-bearing: without it the regex latches onto the
    # d=" inside marker-end="url(...)" and reads the marker URL as the path.
    for m in re.finditer(r'<path class="edge[ "][^>]*\sd="([^"]+)"[^>]*>'
                         r'(?:<title>([^<]*)</title>)?', html):
        d, title = m.group(1), (m.group(2) or d_short(m.group(1))).strip()
        pts = _walk(d)
        if not pts or len(pts) < 2:
            problems.append(f'FLOATING {path}: cannot parse edge d="{d[:40]}..." '
                            f"(relative commands?)")
            continue
        # The DEPARTURE vertex, not the far endpoint: an elbowed edge's first
        # segment is what decides which side it should have attached to.
        for pt, ref, which in ((pts[0], pts[1], "tail (start)"),
                               (pts[-1], pts[-2], "head (end)")):
            anchors = [b for b in boxes
                       if b[0] - tol <= pt[0] <= b[2] + tol and b[1] - tol <= pt[1] <= b[3] + tol]
            if not anchors:
                # Node shapes first, then the two other things an edge may
                # legitimately terminate on. Only reached when NO node box
                # claims the endpoint, so a wrong-side landing on a node can
                # never be laundered into a lifeline or boundary pass.
                if on_lane_line(pt, ref, lanes, tol):
                    continue
                if on_group_border(pt, ref, gboxes, tol):
                    continue
                problems.append(f"FLOATING {path}: {which} floats at ({pt[0]:.0f},{pt[1]:.0f}) "
                                f"-- \"{title[:60]}\"")
                continue
            verdicts = [facing_side(pt, ref, b, tol) for b in anchors]
            if any(v[0] for v in verdicts):
                continue
            _ok, side, depth = max(verdicts, key=lambda v: v[2])
            problems.append(f"WRONG-SIDE {path}: {which} sits on the {side} border at "
                            f"({pt[0]:.0f},{pt[1]:.0f}) but the edge leaves towards "
                            f"({ref[0]:.0f},{ref[1]:.0f}), {-depth:.0f}px behind that side "
                            f"-- \"{title[:60]}\"")
    return problems


def d_short(d):
    return d[:32]


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Check that every edge head/tail anchors on the facing side of a node")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--tol", type=float, default=12.0,
                    help="max px an endpoint may sit off a node box (arrowhead gap); "
                         "also the corner tolerance and the wrap slack of the side rule")
    args = ap.parse_args(argv)
    all_problems = []
    for f in args.files:
        all_problems += check_file(f, args.tol)
    for p in all_problems:
        print(p)
    if all_problems:
        print(f"\n{len(all_problems)} anchoring defect(s).")
        return 1
    print(f"OK -- every edge endpoint anchors on the facing side of a node "
          f"({len(args.files)} file(s), tol {args.tol}px).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
