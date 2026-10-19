// Geometry AT THE DECLARED HOLDS -- the two failures every existing sweep misses
// because every existing sweep measures t=0 at k=1, and a beats cut is never seen
// at t=0 at k=1.
//
// SWEEP 1 -- ink-vertical containment.
//   Pre-delivery item 12: getBBox()/getBoundingClientRect() on SVG <text> return the
//   FACE's layout box (full ascent + descent), not the pixels the glyphs put on screen,
//   so a tall-ascent face reports overflows a screenshot shows as clear gaps. The honest
//   measurement -- canvas ink bounds anchored on the real baseline -- now lives in
//   ink-box.mjs, shared with the glyph-gap and caption-occlusion gates so the three
//   cannot drift; this sweep asserts the INK sits inside its node shape's box.
//   Horizontal containment stays verify-text-containment.mjs's job
//   (advance width is what should govern x, and it already measures the y-band).
//
// SWEEP 2 -- straight-segment edge vs node / foreign text.
//   Checklist item 7: "no edge passes through an unrelated node, and no edge passes
//   through any text". Two kinds of path are measured, and between them they cover
//   every edge that is made of straight lines:
//     - a POLYLINE (`d` is only M/L/H/V/Z -- the orthogonal handoff run `M..L..L..L`
//       that carries most of a process cut) is DECOMPOSED at its own vertices and
//       every segment is swept. Sampling the whole path against its chord classified
//       these as curves and skipped them: an L-shaped run deviates from its chord by
//       half its own bend. A process cut arrived with 10 of 12 edges unmeasured while
//       the N/A line implied only curves were skipped -- an honest instrument may not
//       report a coverage number it does not have.
//     - anything else is compared to its own chord over 20 samples, so a bezier that
//       happens to be flat is treated as the segment it visibly is.
//   REAL CURVES ARE SKIPPED -- deliberately, and the skip is printed. A curve's
//   clearance is a judgement about the route it takes around things, and the honest
//   instrument for that is the contact sheet (diagram-director/scripts/browser-checks/contact-sheet.mjs),
//   not a bounding box.
//
//   "Connected" (the nodes an edge is allowed to touch) stays a property of the WHOLE
//   path's two endpoints, not of each segment -- otherwise an orthogonal run would
//   excuse itself from every node it happens to bend near.
//
// Both sweeps run once per declared camera hold, at that hold's seeked time and pinned
// transform (see hold-frames.mjs for exactly what "at that hold" reproduces), and only
// over elements that are actually VISIBLE at that instant -- an act parked off-canvas or
// a state overlay outside its window is not on screen and is not measured.
//
//   node verify-hold-geometry.mjs <url> [--manifest <path>] [--ink-tol N] [--edge-tol N]
import puppeteer from "./resolve-puppeteer.mjs";
import { readManifest, cameraHolds, masterMs, holdMidpointMs, freezeAt, pinCamera, parseArgs }
  from "./hold-frames.mjs";
import { installInk } from "./ink-box.mjs";

const USAGE = "usage: verify-hold-geometry.mjs <url> [--manifest <path>] [--ink-tol N] [--edge-tol N]";
const { url, manifest: manifestPath, extra } = parseArgs(process.argv.slice(2), USAGE);
const INK_TOL = Number(extra["ink-tol"] ?? 2);     // screen px of slack on the ink box
const EDGE_TOL = Number(extra["edge-tol"] ?? 2);   // screen px an edge may clip a box by

const manifest = readManifest(manifestPath);
const holds = cameraHolds(manifest);
const master = masterMs(manifest);
if (!holds.length) {
  console.error(`FAIL: ${manifestPath} declares no camera holds -- nothing to evaluate at`);
  process.exit(1);
}

const browser = await puppeteer.launch({ headless: true });
const page = await browser.newPage();
const vb = (manifest.target || {}).viewbox || [0, 0, 1920, 1080];
await page.setViewport({ width: Math.round(vb[2]), height: Math.round(vb[3]) });
await page.goto(url, { waitUntil: "networkidle2" });
await page.evaluate(() => document.fonts.ready);
await new Promise(r => setTimeout(r, 500));
await installInk(page);

const violations = [];
let measuredTexts = 0, measuredEdges = 0, skippedCurves = 0, exemptLabels = 0;

for (const hold of holds) {
  const t = holdMidpointMs(hold, master);
  await freezeAt(page, t);
  const before = await pinCamera(page, hold);
  const out = await page.evaluate(({ INK_TOL, EDGE_TOL }) => {
    const res = [];
    let texts = 0, edges = 0, curves = 0, belowLabels = 0;

    // `allowThin`: a perfectly horizontal or vertical <path> has a ZERO-height (or
    // zero-width) client rect -- getBoundingClientRect measures the geometry, not the
    // stroke -- so requiring both dimensions silently skipped every axis-aligned edge
    // on the page, which is most of them. Found by a fixture whose only edge was
    // horizontal and reported "0 straight edges" while visibly crossing a node.
    const visible = (el, allowThin) => {
      const r = el.getBoundingClientRect();
      if (allowThin ? (!r.width && !r.height) : (!r.width || !r.height)) return false;
      for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
        const cs = getComputedStyle(n);
        if (cs.display === "none" || cs.visibility === "hidden") return false;
        if (Number(cs.opacity) < 0.5) return false;
      }
      return true;
    };
    const inView = (r) => r.right > 0 && r.left < innerWidth && r.bottom > 0 && r.top < innerHeight;

    // ---- sweep 1: ink-vertical containment --------------------------------
    // A text's containing box is NOT always the node shape. A state chip is drawn
    // on its own pill (`.state-chip-box`) that deliberately hangs off the node's
    // edge -- measuring it against the node shape would fail two frozen goldens for
    // rendering their state idiom correctly. So the box is chosen mechanically:
    // the SMALLEST drawn box anywhere inside the node group that horizontally spans
    // the text and vertically overlaps it. For a node label that is the node shape;
    // for a chip it is the chip's pill. Nothing is special-cased by class name.
    const BOXES = "rect, polygon, ellipse, circle, path.node__shape";
    const boxFor = (el, node, tb) => {
      let best = null, bestArea = Infinity;
      for (const s of node.querySelectorAll(BOXES)) {
        if (!visible(s)) continue;
        const r = s.getBoundingClientRect();
        if (!r.width || !r.height) continue;
        if (r.left > tb.left + 2 || r.right < tb.right - 2) continue;      // must span it
        if (r.bottom <= tb.top || r.top >= tb.bottom) continue;            // must overlap it
        const area = r.width * r.height;
        if (area < bestArea) { best = r; bestArea = area; }
      }
      return best;
    };
    const ctx = document.createElement("canvas").getContext("2d");
    for (const node of document.querySelectorAll("g.node")) {
      const shape = node.querySelector(".node__shape:not([style])") || node.querySelector(".node__shape");
      if (!shape || !visible(shape)) continue;
      if (!inView(shape.getBoundingClientRect())) continue;
      for (const el of node.querySelectorAll("text")) {
        if (el.closest(".face-detail")) continue;      // morph face has its own beat
        if (!el.textContent.trim() || !visible(el)) continue;
        const tb = el.getBoundingClientRect();
        if (!inView(tb)) continue;
        let sb = boxFor(el, node, tb);
        if (!sb) {
          const body = shape.getBoundingClientRect();
          // BELOW-LABEL: no drawn box in this node overlaps the text's y-band at all,
          // and the text sits clear of the body above or below it. That is the
          // decision diamond's sanctioned idiom -- its interior narrows to nothing
          // where a label would go, so node-shapes-actions.html#shape-decision-diamond
          // puts label/sub at y=98/114 under an 80-tall body. Asserting "ink inside the
          // body" on it is asserting something the shape was never asked to do; the
          // collisions it CAN have are measured by sweep 2 below (an edge running
          // through it), verify-text-containment.mjs's foreign-node sweep, and
          // verify-glyph-label-gap.mjs (its own node's art). Counted, never silent.
          if (tb.top >= body.bottom || tb.bottom <= body.top) { belowLabels++; continue; }
          sb = body;
        }
        // Ink, not the font box (item 12). The measurement used to be written out here;
        // it now lives in ink-box.mjs so the glyph-gap and caption-occlusion gates read
        // the SAME numbers instead of a second copy free to drift. Vertical bounds only:
        // advance width is what should govern x, and verify-text-containment.mjs already
        // measures the y-band. A text with no anchorable baseline is not counted.
        const ink = window.__ddInkBox(el, ctx);
        if (!ink) continue;
        texts++;
        const over = Math.max(sb.top - ink.top, ink.bottom - sb.bottom);
        if (over > INK_TOL)
          res.push({ kind: "INK-VERTICAL", label: el.textContent.trim().slice(0, 30),
                     over: Math.round(over * 10) / 10 });
      }
    }

    // ---- sweep 2: straight-segment edge vs node / foreign text -------------
    const nodeBoxes = [];
    for (const n of document.querySelectorAll("g.node")) {
      const sh = n.querySelector(".node__shape:not([style])") || n.querySelector(".node__shape");
      if (!sh || !visible(sh)) continue;
      nodeBoxes.push({ el: n, r: sh.getBoundingClientRect(),
                       name: (n.querySelector(".node__label")?.textContent || "?").trim().slice(0, 20) });
    }
    const textBoxes = [];
    for (const el of document.querySelectorAll("text")) {
      if (!el.textContent.trim() || !visible(el)) continue;
      if (el.closest(".beat-caption")) continue;       // caption cards ride above the scene
      // A packet's cargo glyph rides ALONG its edge -- that is the packet-travel recipe,
      // not a collision. Excluding `.packet` is the house rule, found by the progressive
      // golden whose binary-stream packet carries a "101" chip down its own path.
      if (el.closest(".packet")) continue;
      textBoxes.push({ el, r: el.getBoundingClientRect(),
                       owner: el.closest("g.node"), name: el.textContent.trim().slice(0, 24) });
    }
    // Liang-Barsky: does segment p0->p1 cross the rectangle (shrunk by tol)?
    const crosses = (p0, p1, r, tol) => {
      const x0 = r.left + tol, x1 = r.right - tol, y0 = r.top + tol, y1 = r.bottom - tol;
      if (x1 <= x0 || y1 <= y0) return false;
      let t0 = 0, t1 = 1;
      const dx = p1.x - p0.x, dy = p1.y - p0.y;
      for (const [p, q] of [[-dx, p0.x - x0], [dx, x1 - p0.x], [-dy, p0.y - y0], [dy, y1 - p0.y]]) {
        if (p === 0) { if (q < 0) return false; continue; }
        const rr = q / p;
        if (p < 0) { if (rr > t1) return false; if (rr > t0) t0 = rr; }
        else { if (rr < t0) return false; if (rr < t1) t1 = rr; }
      }
      return t1 > t0;
    };

    // Vertices of a path built only from moves and lines, in the path's USER space.
    // Returns null the moment a curve command appears -- those go to the sampler.
    // Written out rather than sampled because the whole point is the BEND: an
    // orthogonal run's vertices are where it turns, and getPointAtLength cannot
    // tell you where a turn is without you already knowing.
    const polylineVertices = (d) => {
      if (!d || /[csqta]/i.test(d)) return null;
      const verts = [];
      let x = 0, y = 0, sx = 0, sy = 0, started = false;
      const re = /([MmLlHhVvZz])([^MmLlHhVvZz]*)/g;
      let m;
      while ((m = re.exec(d))) {
        const cmd = m[1];
        const rel = cmd === cmd.toLowerCase();
        const nums = (m[2].match(/-?\d*\.?\d+(?:[eE][-+]?\d+)?/g) || []).map(Number);
        if (cmd === "M" || cmd === "m") {
          for (let i = 0; i + 1 < nums.length; i += 2) {
            if (rel && started) { x += nums[i]; y += nums[i + 1]; }
            else { x = nums[i]; y = nums[i + 1]; }
            if (i === 0 && verts.length) return null;   // a second subpath: not our shape
            if (i === 0) { sx = x; sy = y; started = true; }
            verts.push({ x, y });                       // pairs after the first are lineto
          }
        } else if (cmd === "L" || cmd === "l") {
          for (let i = 0; i + 1 < nums.length; i += 2) {
            if (rel) { x += nums[i]; y += nums[i + 1]; } else { x = nums[i]; y = nums[i + 1]; }
            verts.push({ x, y });
          }
        } else if (cmd === "H" || cmd === "h") {
          for (const n of nums) { x = rel ? x + n : n; verts.push({ x, y }); }
        } else if (cmd === "V" || cmd === "v") {
          for (const n of nums) { y = rel ? y + n : n; verts.push({ x, y }); }
        } else {                                        // Z / z
          x = sx; y = sy; verts.push({ x, y });
        }
      }
      return verts.length >= 2 ? verts : null;
    };

    for (const path of document.querySelectorAll("path.edge")) {
      if (!visible(path, true)) continue;
      const L = path.getTotalLength();
      if (!L) continue;
      const ctm = path.getScreenCTM();
      if (!ctm) continue;
      const at = (u) => path.getPointAtLength(u).matrixTransform(ctm);
      const p0 = at(0), p1 = at(L);
      // The segments this path contributes to the sweep, in SCREEN space.
      let segments = null;
      const verts = polylineVertices(path.getAttribute("d"));
      if (verts) {
        const svg = path.ownerSVGElement;
        const toScreen = (v) => {
          const pt = svg.createSVGPoint(); pt.x = v.x; pt.y = v.y;
          return pt.matrixTransform(ctm);
        };
        const screen = verts.map(toScreen);
        segments = [];
        for (let i = 1; i < screen.length; i++) {
          const a = screen[i - 1], b2 = screen[i];
          if (Math.hypot(b2.x - a.x, b2.y - a.y) < 1) continue;   // degenerate
          segments.push([a, b2]);
        }
        if (!segments.length) continue;
      } else {
        const chord = Math.hypot(p1.x - p0.x, p1.y - p0.y);
        // straightness, MEASURED: max deviation from the chord over 20 samples
        let dev = 0;
        for (let i = 1; i < 20; i++) {
          const p = at((L * i) / 20);
          const num = Math.abs((p1.y - p0.y) * p.x - (p1.x - p0.x) * p.y + p1.x * p0.y - p1.y * p0.x);
          dev = Math.max(dev, chord ? num / chord : 0);
        }
        if (dev > 1.5) { curves++; continue; }          // a real curve -> contact sheet
        segments = [[p0, p1]];
      }
      const near = (pt, r) => pt.x >= r.left - 12 && pt.x <= r.right + 12 &&
                              pt.y >= r.top - 12 && pt.y <= r.bottom + 12;
      // connectedness belongs to the EDGE, not to a segment of it
      const connected = nodeBoxes.filter(b => near(p0, b.r) || near(p1, b.r));
      const mid = at(L / 2);
      const title = (path.querySelector("title")?.textContent || path.getAttribute("class") || "edge")
        .trim().slice(0, 34);
      // one report per (edge, victim): a run that clips the same node on two of its
      // segments is one defect, and printing it twice reads as two.
      const seen = new Set();
      const note = (kind, label) => {
        const key = `${kind}|${label}`;
        if (seen.has(key)) return;
        seen.add(key);
        res.push({ kind, label, over: 0 });
      };
      for (const [a, b2] of segments) {
        if (!inView({ left: Math.min(a.x, b2.x), right: Math.max(a.x, b2.x),
                      top: Math.min(a.y, b2.y), bottom: Math.max(a.y, b2.y) })) continue;
        edges++;
        for (const b of nodeBoxes) {
          if (connected.includes(b)) continue;
          if (crosses(a, b2, b.r, EDGE_TOL)) note("EDGE-THROUGH-NODE", `${title} -> ${b.name}`);
        }
        for (const tbox of textBoxes) {
          // a label inside a node the edge connects to is already excluded with that node;
          // an edge's OWN label is the text nearest its midpoint and is excluded below
          if (tbox.owner && connected.some(bb => bb.el === tbox.owner)) continue;
          const ownLabel = tbox.r.left - 24 <= mid.x && mid.x <= tbox.r.right + 24 &&
                           tbox.r.top - 24 <= mid.y && mid.y <= tbox.r.bottom + 24 && !tbox.owner;
          if (ownLabel) continue;
          if (crosses(a, b2, tbox.r, EDGE_TOL)) note("EDGE-THROUGH-TEXT", `${title} -> "${tbox.name}"`);
        }
      }
    }
    return { res, texts, edges, curves, belowLabels };
  }, { INK_TOL, EDGE_TOL });

  measuredTexts += out.texts; measuredEdges += out.edges; skippedCurves += out.curves;
  exemptLabels += out.belowLabels;
  const id = hold.id || "(unnamed)";
  for (const v of out.res) {
    violations.push(`${id}: [${v.kind}] ${v.label}${v.over ? ` by ${v.over}px` : ""}`);
    // ##DIAG: one JSON object per line, structured evidence for `verify_all.py --json`
    // (README -> "The ##DIAG line"). The runner strips these before it builds the prose
    // tail and it owns severity, so nothing here declares one. Only INK-VERTICAL is
    // emitted: the two edge-crossing classes have no code in the registry yet and stay
    // in the row's prose reason rather than being mislabelled.
    if (v.kind === "INK-VERTICAL")
      console.log("##DIAG " + JSON.stringify({ code: "text/ink-vertical",
        subject: { hold: id, text: v.label },
        evidence: { kind: v.kind, over_px: v.over ?? null, tol_px: INK_TOL } }));
  }
  // `before` is the transform the beats keyframes had at this instant, printed so a
  // drift between manifest and CSS is visible rather than silently overwritten.
  console.log(`  hold ${id.padEnd(10)} t=${Math.round(t)}ms  k=${hold.k}  ` +
              `ink-texts ${String(out.texts).padStart(3)}  straight-segs ${String(out.edges).padStart(3)}` +
              `  curves-skipped ${out.curves}  below-labels ${out.belowLabels}` +
              `  was ${String(before).replace(/\s+/g, "")}`);
}
await browser.close();

// House rule: a check that finds nothing FAILS.
if (!measuredTexts && !measuredEdges) {
  console.error("FAIL: measured zero texts and zero edges at every hold -- wrong url, "
                + "broken page, or selector drift");
  process.exit(1);
}
console.log(`N/A: ${skippedCurves} curved edge instance(s) skipped -- curves are reviewed on the `
            + "contact sheet, not by bounding box. Polylines are NOT in this number: they are "
            + "decomposed at their vertices and every segment is swept.");
if (exemptLabels)
  console.log(`N/A: ${exemptLabels} below/above-label instance(s) exempt from ink-vertical `
              + "containment (no body at that y -- the decision diamond's sanctioned idiom); "
              + "their collisions are covered by sweep 2 and the containment/glyph-gap checks");
if (violations.length) {
  console.log("HOLD-GEOMETRY VIOLATIONS:");
  violations.forEach(v => console.log(`  ${v}`));
  process.exit(1);
}
console.log(`all clear across ${holds.length} hold(s): ${measuredTexts} ink boxes inside their `
            + `node (tol ${INK_TOL}px), ${measuredEdges} straight segment(s) crossing nothing (tol ${EDGE_TOL}px)`);
process.exit(0);
