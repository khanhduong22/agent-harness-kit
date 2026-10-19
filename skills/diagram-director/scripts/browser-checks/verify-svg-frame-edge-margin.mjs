// THE FRAME-MARGIN GATE, SVG-MODE TWIN. Same rule as
// verify-frame-edge-margin.mjs, different instrument: no teaching line may hug
// the edge of the frame it is being taught in.
//
// WHY A SECOND FILE AND NOT A FLAG. The rule is engine-general
// (references/camera-beat.md -> "Keep the teaching line off the frame edge");
// what differs is where a cut hides its frame and its stations. A `process` cut
// is built HTML-first -- a `.frame` div holding `[data-station]` divs under an
// `svg.edges` overlay. A `system-design` cut IS an SVG document: the root
// `<svg>` is the frame, and its stations are `g.node > .node__shape` inside a
// `<g class="camera">` that carries the zoom. One reader each, one rule.
//
// THE RULE, restated so this file stands on its own:
//
//   At a beat's hold, an edge may come within M frame px of a frame side ONLY
//   where the beat is genuinely heading off-frame on that side -- which is true
//   in exactly two measurable ways: the path CROSSES that side, or that side
//   CUTS one of the edge's own anchor stations. Every other side must stay at
//   least M px clear of every PAINTED point of the path. Default M = 24 frame
//   px, the same landscape legibility unit the text floor uses.
//
// FRAME PX. The frame is the root `<svg>`'s viewBox, so every reading is divided
// by the fit ratio (rendered width / viewBox width). That puts distances in the
// same units the manifest, solve_camera and the text floor are written in --
// user units at k=1 -- no matter what size the page is rendered at.
//
// SCOPE. Identical to the HTML twin. An edge BOTH of whose stations are
// off-frame is scenery in that beat, not a teaching line, and is not measured.
// An edge with a visible station at each end IS measured, including one whose
// far station is only half in frame.
//
// THE CLIPPED-ANCHOR EXEMPTION (lead ruling, 2026-08-27). A side that already
// CUTS one of the edge's own anchor stations owes that edge nothing:
//
//     một cạnh đã cắt chính station của edge thì không nợ edge đó khoảng thở
//
// The framing has itself told the viewer "this continues off-frame", so an edge
// hugging that side is a consequence of a sanctioned crop, not a hidden teaching
// line -- the reader's eye is already off the page there. It is the CROSSING
// exemption's sibling: both say "this is where the beat leaves the frame", one
// read off the path, one off the thing the path is attached to. Computed per
// (edge, side, hold) from the station's measured bbox against that frame side,
// never a named allowlist, so it keeps working -- and keeps refusing -- on cuts
// that do not exist yet. Every waiver it grants is PRINTED with the clearance it
// waived and the station that bought it; a silent exemption is how a gate rots.
// Found on `compare-chat-pubsub` b3-b5 (User A cut by the TOP, 99% above frame)
// and b6 (ws-3 and User B both cut by the LEFT).
//
// WHAT COUNTS AS A STATION. The three things an edge may honestly terminate on,
// the same three diagram-director/scripts/verify_edge_anchors.py enumerates and for the same
// reasons: a node's `.node__shape`; a swimlane `.lane-line` lifeline (messages
// land on the lifeline, which is part of the participant); and a `.group__box`
// cluster boundary (a labelled cluster that holds contents is a real target).
// Getting this list wrong does not weaken the rule -- an unrecognised endpoint
// makes the edge UNANCHORED, which this check skips and
// verify_edge_anchors.py / verify-html-edge-anchors.mjs fails on instead.
//
// PAINTED, not geometric; CROSSING off the CENTRELINE. Both exactly as the HTML
// twin documents: the distance is measured to the path's painted band (the
// widest visible stroke among same-`d` paths, so a `.arc-halo`-style halo is
// counted), while the crossing test uses the centreline alone so a fat stroke
// cannot bribe its way to an exemption.
//
// House rule (diagram-director/scripts/browser-checks/README.md): a check that finds nothing
// FAILS. Zero measured edges across every hold is a wrong url, a broken page or
// selector drift, never a clean cut.
//
//   node verify-svg-frame-edge-margin.mjs <url> [--manifest <path>] [--margin 24]
//        [--tol 12] [--samples 240] [--frame "svg"] [--node "g.node"]
import puppeteer from "./resolve-puppeteer.mjs";
import { readManifest, cameraHolds, masterMs, holdMidpointMs, freezeAt, pinCamera, parseArgs }
  from "./hold-frames.mjs";

const USAGE = "usage: verify-svg-frame-edge-margin.mjs <url> [--manifest <path>] "
  + "[--margin N] [--tol N] [--samples N] [--frame <sel>] [--node <sel>]";
const { url, manifest: manifestPath, extra } = parseArgs(process.argv.slice(2), USAGE);
const MARGIN = Number(extra.margin ?? 24);        // frame px a non-crossed side owes
const TOL = Number(extra.tol ?? 12);              // stage px, endpoint -> station
const SAMPLES = Number(extra.samples ?? 240);
const FRAME_SEL = typeof extra.frame === "string" ? extra.frame : "svg";
const NODE_SEL = typeof extra.node === "string" ? extra.node : "g.node";

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

const violations = [], waivers = [];

// The measured clearance out of a violation's own detail line, or null when absent.
// Written as a function so 0.0 survives: it is a violation's most severe value.
const clearance = detail => {
  const n = Number((detail.match(/runs ([\d.]+) frame px/) || [])[1]);
  return Number.isNaN(n) ? null : n;
};
let measured = 0, scenery = 0, unanchored = 0;

for (const hold of holds) {
  await freezeAt(page, holdMidpointMs(hold, master));
  await pinCamera(page, hold);
  const out = await page.evaluate(({ MARGIN, TOL, SAMPLES, FRAME_SEL, NODE_SEL, k }) => {
    const res = [], waived = [];
    let edges = 0, offstage = 0, floating = 0;

    // ---- the frame: the root <svg>, read in viewBox units ------------------
    const svg = document.querySelector(FRAME_SEL);
    if (!svg) return { res: [{ kind: "CONTRACT", label: FRAME_SEL,
      detail: "no root <svg> -- there is no frame to measure a margin against" }],
      waived, edges, offstage, floating };
    const fr = svg.getBoundingClientRect();
    const box = svg.viewBox && svg.viewBox.baseVal;
    const W = box && box.width ? box.width : fr.width;
    const H = box && box.height ? box.height : fr.height;
    const fit = W ? fr.width / W : 1;
    const toFrame = (x, y) => ({ x: (x - fr.left) / fit, y: (y - fr.top) / fit });
    const rectOf = (el) => {
      const r = el.getBoundingClientRect();
      const a = toFrame(r.left, r.top), b = toFrame(r.right, r.bottom);
      return { x0: a.x, y0: a.y, x1: b.x, y1: b.y, w: r.width, h: r.height };
    };
    const rendered = (el) => {
      for (let n = el; n && n.nodeType === 1 && n !== document.documentElement;
           n = n.parentElement) {
        const cs = getComputedStyle(n);
        if (cs.display === "none" || cs.visibility === "hidden") return false;
        if (Number(cs.opacity) < 0.5) return false;
      }
      return true;
    };

    // ---- stations: node shapes, cluster boundaries, lifelines --------------
    // The same three anchors diagram-director/scripts/verify_edge_anchors.py recognises. A
    // `.node__shape` is measured on the SHAPE, not on the group, so a node's
    // label or badge cannot inflate the box an endpoint is judged against.
    const stations = [];
    const push = (el, name) => {
      const r = el.getBoundingClientRect();
      if (!r.width && !r.height) return;
      if (!rendered(el)) return;
      const b = rectOf(el);
      stations.push({ box: b, name: String(name || "?").slice(0, 24),
                      visible: b.x1 > 0 && b.x0 < W && b.y1 > 0 && b.y0 < H });
    };
    for (const g of document.querySelectorAll(NODE_SEL)) {
      const shapes = [...g.querySelectorAll(".node__shape")]
        .filter(s => !/ghost/.test(s.getAttribute("class") || ""));
      const shape = shapes[shapes.length - 1];   // painter's order: the body is on top
      const title = g.querySelector("title, text");
      if (shape) push(shape, (title && title.textContent) || g.getAttribute("class"));
    }
    for (const r of document.querySelectorAll("rect.group__box")) push(r, "cluster");
    for (const l of document.querySelectorAll("path.lane-line")) push(l, "lifeline");

    // ---- the paths, and each one's painted half-width ----------------------
    const EDGE_RE = /(^|\s)edge($|\s|-)/;
    const paint = new Map();      // `d` -> widest VISIBLE half-stroke in frame px
    const all = [];
    for (const p of document.querySelectorAll("path")) {
      if (p.closest("defs") || p.closest("marker") || p.closest("clipPath")) continue;
      if (!rendered(p)) continue;
      const ctm = p.getScreenCTM();
      if (!ctm) continue;
      const cs = getComputedStyle(p);
      // `vector-effect:non-scaling-stroke` paints a constant SCREEN width, so it
      // does NOT ride the camera's k; anything else is in user units and does.
      // The goldens use it on node shapes rather than on edges, but reading it
      // wrong would silently mis-size the painted band of any cut that adopts it.
      const scale = (p.getAttribute("vector-effect") === "non-scaling-stroke"
        || cs.vectorEffect === "non-scaling-stroke")
        ? 1 / fit
        : Math.hypot(ctm.a, ctm.b) / fit;                     // user units -> frame px
      const sw = (parseFloat(cs.strokeWidth) || 0) * scale;
      const d = p.getAttribute("d") || "";
      paint.set(d, Math.max(paint.get(d) || 0, sw / 2));
      all.push({ p, ctm, d });
    }

    for (const { p, ctm, d } of all) {
      if (!EDGE_RE.test((p.getAttribute("class") || "").trim())) continue;   // halos ride along
      const L = p.getTotalLength();
      if (!L) continue;
      const title = p.querySelector("title");
      const label = ((title && title.textContent)
        || p.getAttribute("class") || "edge").slice(0, 40);
      const half = paint.get(d) || 0;
      const at = (u) => {
        const q = p.getPointAtLength(u).matrixTransform(ctm);
        return toFrame(q.x, q.y);
      };
      // SCOPE. An edge is a teaching line in this beat only if the frame shows
      // something at BOTH of its ends. `tol` is verify_edge_anchors.py's stage-px
      // tolerance carried into frame px by this hold's own scale.
      const t = TOL * k;
      const stationsAt = (pt) => stations.filter(s =>
        pt.x >= s.box.x0 - t && pt.x <= s.box.x1 + t &&
        pt.y >= s.box.y0 - t && pt.y <= s.box.y1 + t);
      const ends = [stationsAt(at(0)), stationsAt(at(L))];
      if (ends.some(list => !list.length)) { floating++; continue; }   // anchoring is another gate's job
      if (!ends.every(list => list.some(s => s.visible))) { offstage++; continue; }

      // ---- CLIPPED-ANCHOR exemption (lead ruling, 2026-08-27) ---------------
      // A side that already CUTS one of this edge's own anchor stations owes
      // that edge nothing. The crop itself has told the viewer "this continues
      // off-frame", so the edge starting on the sliver of a half-shown station
      // is a consequence of a sanctioned framing, not a hidden teaching line.
      // Measured per (edge, side, hold) from the station's own bbox against the
      // frame side -- never a named allowlist, so it stays honest on cuts that
      // do not exist yet. It is the same shape as the CROSSING exemption: both
      // say "this side is where the beat goes off-frame", one read off the
      // path, one off the thing the path is attached to.
      const clipped = { left: false, right: false, top: false, bottom: false };
      for (const s of [...ends[0], ...ends[1]]) {
        if (s.box.x0 < 0) clipped.left = true;
        if (s.box.x1 > W) clipped.right = true;
        if (s.box.y0 < 0) clipped.top = true;
        if (s.box.y1 > H) clipped.bottom = true;
      }

      // ---- the sweep --------------------------------------------------------
      const crossed = { left: false, right: false, top: false, bottom: false };
      const clear = { left: Infinity, right: Infinity, top: Infinity, bottom: Infinity };
      const worst = {};
      let inside = 0;
      for (let i = 0; i <= SAMPLES; i++) {
        const q = at((L * i) / SAMPLES);
        // CROSSING off the centreline only -- a fat stroke may not buy an exemption.
        if (q.x < 0) crossed.left = true;
        if (q.x > W) crossed.right = true;
        if (q.y < 0) crossed.top = true;
        if (q.y > H) crossed.bottom = true;
        if (q.x < 0 || q.x > W || q.y < 0 || q.y > H) continue;   // the run that is off-frame
        inside++;
        const dist = { left: q.x - half, right: W - q.x - half,
                       top: q.y - half, bottom: H - q.y - half };
        for (const side of Object.keys(dist))
          if (dist[side] < clear[side]) { clear[side] = dist[side]; worst[side] = q; }
      }
      if (!inside) { offstage++; continue; }       // nothing of it is on screen at this hold
      edges++;
      for (const side of ["left", "right", "top", "bottom"]) {
        if (crossed[side] || clear[side] >= MARGIN) continue;
        const q = worst[side];
        if (clipped[side]) {
          // Waived, and SAID so. An exemption that fires silently is how a gate
          // rots into a rubber stamp -- every waiver is printed with the number
          // it waived, so a reviewer can still take it to the contact sheet.
          const cut = [...ends[0], ...ends[1]].find(s =>
            (side === "left" && s.box.x0 < 0) || (side === "right" && s.box.x1 > W) ||
            (side === "top" && s.box.y0 < 0) || (side === "bottom" && s.box.y1 > H));
          waived.push(`${label}: ${clear[side].toFixed(1)} px from the ${side.toUpperCase()} `
            + `edge, waived -- its own station "${cut ? cut.name : "?"}" is cut by that side`);
          continue;
        }
        res.push({ kind: "FRAME-MARGIN", label, detail:
          `runs ${clear[side].toFixed(1)} frame px from the ${side.toUpperCase()} edge at `
          + `(${q.x.toFixed(0)},${q.y.toFixed(0)}) -- ${MARGIN} required, the path never crosses `
          + `that side and no station of its own is cut by it, so it is not on its way off-frame`
          + (half > 0.6 ? ` (painted band: centreline +/- ${half.toFixed(1)}px)` : "") });
      }
    }
    return { res, edges, offstage, floating, waived };
  }, { MARGIN, TOL, SAMPLES, FRAME_SEL, NODE_SEL, k: Number(hold.k) });

  measured += out.edges; scenery += out.offstage; unanchored += out.floating;
  const id = hold.id || "(unnamed)";
  for (const v of out.res) {
    violations.push(`${id}: [${v.kind}] ${v.label}: ${v.detail}`);
    // ##DIAG: structured evidence for `verify_all.py --json` (README -> "The ##DIAG
    // line"). Severity is the runner's, never this script's; the side and the two
    // numbers are what a repair needs, and they are already measured above.
    if (v.kind === "FRAME-MARGIN")
      console.log("##DIAG " + JSON.stringify({ code: "edge/frame-margin",
        subject: { hold: id, element: v.label },
        evidence: { side: (v.detail.match(/from the ([A-Z]+) edge/) || [])[1] || null,
                    // isNaN, never `|| null`: an edge sitting exactly ON the frame side
                    // measures 0.0, and `0 || null` would erase the worst reading there is.
                    clearance_px: clearance(v.detail),
                    required_px: MARGIN } }));
  }
  for (const w of out.waived || []) waivers.push(`${id}: ${w}`);
  console.log(`  hold ${id.padEnd(10)} k=${hold.k}  edges-measured ${String(out.edges).padStart(3)}`
    + `  off-stage ${String(out.offstage).padStart(3)}  unanchored ${out.floating}`
    + `  clipped-anchor waivers ${(out.waived || []).length}`);
}
await browser.close();

if (!measured) {
  console.error("FAIL: zero edges measured at every hold -- wrong url, broken page, or "
    + `selector drift ("${FRAME_SEL}" / "${NODE_SEL}" / path.edge*)`);
  process.exit(1);
}
console.log(`N/A: ${scenery} edge instance(s) not measured -- a station off-frame at one end `
  + "or nothing of the run on screen: scenery in that beat, not a teaching line"
  + (unanchored ? `; ${unanchored} unanchored endpoint edge(s) left to verify_edge_anchors.py` : ""));
if (waivers.length) {
  console.log(`N/A: ${waivers.length} (edge, side) pair(s) waived by the CLIPPED-ANCHOR clause `
    + "-- the side already cuts the edge's own station, so the crop has announced the "
    + "continuation and the edge owes it nothing:");
  waivers.forEach(w => console.log(`  ${w}`));
}
if (violations.length) {
  console.log("FRAME-MARGIN VIOLATIONS:");
  violations.forEach(v => console.log(`  ${v}`));
  console.log(`\n${violations.length} violation(s). A teaching line that hugs or exits the frame `
    + "edge is invisible exactly when it matters -- re-solve the hold or reroute the edge.");
  process.exit(1);
}
console.log(`all clear across ${holds.length} hold(s): ${measured} edge instance(s) stay `
  + `${MARGIN}+ frame px clear of every frame side they neither cross nor have a station cut by `
  + `(painted band, halos counted; ${waivers.length} clipped-anchor waiver(s))`);
process.exit(0);
