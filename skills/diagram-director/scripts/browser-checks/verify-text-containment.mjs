// The CDN class of bug: node text crossing its own shape's border, at the
// text's OWN y-band (hexagons AND diamonds narrow towards top/bottom, at
// different rates -- the polygon's own vertex count decides which). Run after
// any font change -- mono runs ~20% wider than sans at equal size. Also sweeps
// text-over-foreign-node and floating edge endpoints.
//
// A label whose whole y-band is OUTSIDE the body (the diamond's sanctioned
// below-label) keeps the plain shape box as its budget and skips the narrowing
// only -- there is no body at that y to narrow. See the `outside` counter.
//
//   node verify-text-containment.mjs <url>              (serve over HTTP)
import puppeteer from "./resolve-puppeteer.mjs";

const url = process.argv[2];
if (!url) { console.error("usage: verify-text-containment.mjs <url>"); process.exit(2); }

const b = await puppeteer.launch({ headless: true });
const p = await b.newPage();
await p.goto(url, { waitUntil: "networkidle2" });
await p.evaluate(() => document.fonts.ready);
await new Promise(r => setTimeout(r, 600));
const { res: out, nodes, outside } = await p.evaluate(() => {
  const PAD = 6, res = [];
  let outside = 0;
  // A polygon's own vertices, in the shape's user space. `tagName === "polygon"`
  // says nothing about which polygon: a hexagon has SIX sides falling away at
  // 20/40, a decision diamond has FOUR falling away twice as fast. Counting them
  // is the structural test; assuming hexagon fails the shipped diamond snippet.
  const pointsOf = (sh) => {
    if (sh.tagName !== "polygon" || !sh.points) return null;
    const out = [];
    for (let i = 0; i < sh.points.numberOfItems; i++) {
      const pt = sh.points.getItem(i);
      out.push({ x: pt.x, y: pt.y });
    }
    return out;
  };
  for (const node of document.querySelectorAll("g.node")) {
    const shape = node.querySelector(".node__shape:not([style])") || node.querySelector(".node__shape");
    if (!shape) continue;
    const sb = shape.getBBox();
    const midX = sb.x + sb.width / 2, midY = sb.y + sb.height / 2, EPS = 0.5;
    const pts = pointsOf(shape);
    const isHex = pts && pts.length === 6;      // 20/40 slope on both sides
    // DIAMOND: four vertices on the nominal box's edge MIDPOINTS -- two on the
    // vertical midline, two on the horizontal one (node-shapes.html#shape-diamond
    // and node-shapes-actions.html#shape-decision-diamond are both exactly this).
    const isDiamond = pts && pts.length === 4 &&
      pts.filter(pt => Math.abs(pt.x - midX) < EPS).length === 2 &&
      pts.filter(pt => Math.abs(pt.y - midY) < EPS).length === 2;
    for (const t of node.querySelectorAll("text")) {
      if (t.closest(".face-detail")) continue;   // morph face measured at its own beat
      const tb = t.getBBox();
      // BELOW-LABEL (or above-label): a text whose whole y-band sits OUTSIDE the
      // body. The narrowing rule below must NOT apply to it -- there is no body at
      // that y to narrow. It is the sanctioned idiom for a decision diamond, whose
      // interior closes to nothing exactly where a label would go, so the shipped
      // snippet puts label/sub at y=98/114 under an 80-tall body; insetting by the
      // slope at dy=58 shrank the allowed band to 37.5..122.5 and failed the
      // snippet's own example by ~12px. What such a label still gets is the shape's
      // PLAIN bbox as its horizontal budget -- a label wider than the node it hangs
      // under is a real defect and stays caught -- plus every other sweep, none of
      // which is waived: its own node's art by verify-glyph-label-gap.mjs, a foreign
      // node by the OVER-FOREIGN-NODE sweep below, an edge running through it by
      // verify-hold-geometry.mjs sweep 2. Its VERTICAL containment is the one thing
      // nobody can assert, and that is exactly what hold-geometry exempts.
      const outsideBody = tb.y >= sb.y + sb.height || tb.y + tb.height <= sb.y;
      if (outsideBody) outside++;
      let x0 = sb.x + PAD, x1 = sb.x + sb.width - PAD;
      if (!outsideBody && (isHex || isDiamond)) {
        const dy = Math.max(Math.abs(tb.y - midY), Math.abs(tb.y + tb.height - midY));
        // the shape's OWN slope: half-width per half-height for the diamond,
        // the family's 20/40 chamfer for the hexagon.
        const slope = isDiamond ? (sb.width / sb.height) : (20 / 40);
        const inset = Math.min(dy * slope, sb.width / 2);
        x0 = sb.x + inset + PAD; x1 = sb.x + sb.width - inset - PAD;
      }
      const over = Math.max(x0 - tb.x, tb.x + tb.width - x1);
      if (over > 0) res.push({ label: t.textContent.trim().slice(0, 30),
        cls: t.getAttribute("class") || "", over: Math.round(over * 10) / 10 });
    }
  }
  // second sweep: any text overlapping a node shape it does not belong to.
  // SCREEN space via getBoundingClientRect -- getBBox() is local and ignores
  // ancestor transforms, so under translate()-positioned nodes it compares
  // unrelated coordinate systems (the classic getBBox trap; hit once here).
  for (const a of document.getAnimations()) { a.pause(); a.currentTime = 0; }
  // ascii-terminal draws its "shape" as box-drawing TEXT, so a node there has
  // no .node__shape at all -- skip those instead of crashing on a null.
  const shapes = [...document.querySelectorAll("g.node")].map(n => {
    const sh = n.querySelector(".node__shape:not([style])") || n.querySelector(".node__shape");
    if (!sh) return null;
    return { n, b: sh.getBoundingClientRect() };
  }).filter(Boolean);
  for (const t of document.querySelectorAll("text")) {
    if (t.closest(".face-detail") || t.closest(".beat-caption")) continue;  // captions: opacity 0 at t=0
    const tb = t.getBoundingClientRect(); if (!tb.width) continue;
    const own = t.closest("g.node");
    for (const { n, b } of shapes) {
      if (n === own) continue;
      const ox = Math.min(tb.right, b.right) - Math.max(tb.left, b.left);
      const oy = Math.min(tb.bottom, b.bottom) - Math.max(tb.top, b.top);
      if (ox > 1 && oy > 1)
        res.push({ label: t.textContent.trim().slice(0, 30), cls: "OVER-FOREIGN-NODE",
                   over: Math.round(Math.min(ox, oy)) });
    }
  }
  // third sweep: every edge endpoint must be rooted on a node. A path that
  // starts 20px past its node's corner renders as a floating dash head
  // (review-caught). Tolerance 12px covers arrowhead shortening.
  // A style whose nodes have no <shape> element at all (ascii-terminal draws
  // its frame as box-drawing TEXT) leaves nothing to anchor against: every
  // edge would report as floating. Fall back to the node GROUP's own box,
  // which is the same rectangle the frame characters are drawn on.
  const groups = [...document.querySelectorAll("g.node")];
  const nodeRects = shapes.length ? shapes.map(({ b }) => b) : groups.map(n => n.getBoundingClientRect());
  const near = (pt) => nodeRects.some(b =>
    pt.x >= b.left - 12 && pt.x <= b.right + 12 && pt.y >= b.top - 12 && pt.y <= b.bottom + 12);
  for (const path of document.querySelectorAll("path.edge")) {
    const L = path.getTotalLength(); if (!L) continue;
    const m = path.getScreenCTM();
    for (const [t, name] of [[0, "start"], [L, "end"]]) {
      const p0 = path.getPointAtLength(t).matrixTransform(m);
      if (!near(p0)) res.push({ label: (path.querySelector("title")?.textContent || "").trim().slice(0, 40),
                                cls: `EDGE-${name.toUpperCase()}-FLOATING`, over: 0 });
    }
  }
  return { res, nodes: groups.length, outside };
});
await b.close();
// House rule: a check that finds nothing FAILS. Zero nodes means a wrong url,
// a broken page, or selector drift -- never a clean diagram.
if (!nodes) { console.error("FAIL: zero g.node elements found -- wrong url, broken page, or selector drift"); process.exit(1); }
// Counted, never silent: a cut where this fires often is placing labels outside
// bodies as a habit, and that is a contact-sheet conversation.
const below = outside ? ` + ${outside} below/above-label(s) measured on the plain `
  + "shape box (no narrowing -- no body at that y)" : "";
console.log(out.length ? "OVERFLOWS:" : `all node text inside its shape (6px pad, ${nodes} nodes)${below}`);
out.forEach(v => console.log(`  "${v.label}" [${v.cls}] overflows by ${v.over}px`));
// ##DIAG: structured evidence for `verify_all.py --json` (README -> "The ##DIAG line").
// One line per violation, JSON on one line, no severity -- the runner owns policy. A
// floating endpoint and an overflowing text are different codes, so they are split here
// rather than left for a consumer to re-derive from the class string.
out.forEach(v => console.log("##DIAG " + JSON.stringify({
  code: v.cls.endsWith("-FLOATING") ? "edge/floating-endpoint" : "text/containment",
  subject: { element: v.cls, text: v.label },
  evidence: { kind: v.cls, over_px: v.over, pad_px: 6 } })));
process.exit(out.length ? 1 : 0);
