// THE FRAME-MARGIN GATE: no teaching line may hug the edge of the frame it is
// being taught in.
//
// WHY IT HAS TO EXIST. Every other camera gate measures the MUST-SHOW BBOX a
// hold DECLARES (solve_camera --check, verify_all stage D). An edge is not in
// that bbox unless the author put it there, so a connector can run a couple of
// pixels inside the frame -- or half under it -- while every declared number
// passes. Reported on the process golden's loop beat: the orange return arc had
// been rerouted OVER the top of the stage, its horizontal run landed 11.6 frame
// px from the frame's top edge at b3 (2.4 px once its 11px halo is counted), and
// the user could not see the line that the beat exists to explain. Nothing
// failed. That is the hole this closes.
//
// THE RULE (references/camera-beat.md -> "Keep the teaching line off the frame
// edge"; references/genres/process.md -> Build traps).
//
//   At a beat's hold, an edge may come within M frame px of a frame side ONLY
//   where the beat is genuinely heading off-frame on that side -- which is true
//   in exactly two measurable ways: the path CROSSES that side, or that side
//   CUTS one of the edge's own anchor stations. Every other side must stay at
//   least M px clear of every PAINTED point of the path. Default M = 24 frame
//   px, the same landscape legibility unit the text floor uses.
//
//   Where both of an edge's stations are FULLY in frame neither exemption can
//   fire, so the rule reduces to the lead's statement of it: the entire path
//   stays M px inside the frame.
//
// THE CLIPPED-ANCHOR EXEMPTION (lead ruling, 2026-08-27):
//
//     một cạnh đã cắt chính station của edge thì không nợ edge đó khoảng thở
//
// The framing has itself told the viewer "this continues off-frame", so an edge
// hugging that side is a consequence of a sanctioned crop, not a hidden teaching
// line. It is the CROSSING exemption's sibling -- both say "this is where the
// beat leaves the frame", one read off the path, one off the thing the path is
// attached to. Computed per (edge, side, hold) from the station's measured bbox
// against that frame side, never a named allowlist. Every waiver is PRINTED with
// the clearance it waived; a silent exemption is how a gate rots. This clause is
// shared with the SVG-mode twin (verify-svg-frame-edge-margin.mjs) because it is
// part of the RULE, not of either instrument -- it fires on no process hold in
// the frozen golden, and it would NOT have waived that golden's b3 defect: the
// return arc's stations are cut by the LEFT, and the side it hugged was the TOP.
//
// SCOPE, and why it is drawn here. An edge BOTH of whose stations are off-frame
// is scenery in that beat, not a teaching line, and is not measured. An edge
// with at least one visible station at each end IS measured -- including one
// whose far station is only half in frame, because that is exactly the case the
// defect lived in (at b3 the AI station is clipped by the left edge, the arc
// legitimately runs off to it, and the LEFT side is therefore exempt while the
// TOP -- which the arc never crosses -- is not).
//
// PAINTED, not geometric. The distance measured is to the path's painted band:
// the sample point pushed out by half the stroke width. A path's halo -- a
// second, wider path drawn with an IDENTICAL `d`, the house idiom for making an
// edge the subject of a beat (`.arc-halo`) -- is part of that edge's paint, so
// the widest visible stroke among same-`d` paths is what sets the half-width.
// Measuring the centreline alone passed the golden's b3b hold by 0.8px while the
// halo was 8px over the frame edge.
//
// CROSSING is read off the CENTRELINE, never the painted band -- otherwise a
// fat stroke could bribe its way to an exemption by spilling over a side it
// never actually goes through.
//
// House rule (diagram-director/scripts/browser-checks/README.md): a check that finds nothing
// FAILS. Zero measured edges across every hold is a wrong url, a broken page or
// selector drift, never a clean cut.
//
//   node verify-frame-edge-margin.mjs <url> [--manifest <path>] [--margin 24]
//        [--tol 12] [--samples 240] [--frame .frame] [--station "[data-station]"]
import puppeteer from "./resolve-puppeteer.mjs";
import { readManifest, cameraHolds, masterMs, holdMidpointMs, freezeAt, pinCamera, parseArgs }
  from "./hold-frames.mjs";

const USAGE = "usage: verify-frame-edge-margin.mjs <url> [--manifest <path>] [--margin N] "
  + "[--tol N] [--samples N] [--frame <sel>] [--station <sel>]";
const { url, manifest: manifestPath, extra } = parseArgs(process.argv.slice(2), USAGE);
const MARGIN = Number(extra.margin ?? 24);        // frame px a non-crossed side owes
const TOL = Number(extra.tol ?? 12);              // stage px, endpoint -> station (as the
                                                  // anchor checker uses; scaled by k here)
const SAMPLES = Number(extra.samples ?? 240);
const FRAME_SEL = typeof extra.frame === "string" ? extra.frame : ".frame";
const STATION_SEL = typeof extra.station === "string" ? extra.station : "[data-station]";

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
let measured = 0, scenery = 0, unanchored = 0;

for (const hold of holds) {
  await freezeAt(page, holdMidpointMs(hold, master));
  await pinCamera(page, hold);
  const out = await page.evaluate(({ MARGIN, TOL, SAMPLES, FRAME_SEL, STATION_SEL, k }) => {
    const res = [], waived = [];
    let edges = 0, offstage = 0, floating = 0;

    const frame = document.querySelector(FRAME_SEL);
    if (!frame) return { res: [{ kind: "CONTRACT", label: FRAME_SEL,
      detail: "no frame element -- there is no frame to measure a margin against" }],
      waived, edges, offstage, floating };
    const fr = frame.getBoundingClientRect();
    // The frame keeps its AUTHORED layout box and is scaled to the viewport by the
    // fit layer, so dividing the rect by that ratio puts every reading back in the
    // frame px the manifest, the text floor and this margin are all written in.
    const W = frame.offsetWidth, H = frame.offsetHeight;
    const fit = W ? fr.width / W : 1;
    const toFrame = (x, y) => ({ x: (x - fr.left) / fit, y: (y - fr.top) / fit });
    const boxOf = (el) => {
      const r = el.getBoundingClientRect();
      const a = toFrame(r.left, r.top), b = toFrame(r.right, r.bottom);
      return { x0: a.x, y0: a.y, x1: b.x, y1: b.y };
    };
    const rendered = (el) => {
      for (let n = el; n && n.nodeType === 1; n = n.parentElement) {
        const cs = getComputedStyle(n);
        if (cs.display === "none" || cs.visibility === "hidden") return false;
        if (Number(cs.opacity) < 0.5) return false;
      }
      return true;
    };

    // ---- stations, and which of them this frame actually shows -------------
    const stations = [];
    for (const el of document.querySelectorAll(STATION_SEL)) {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height || !rendered(el)) continue;
      const box = boxOf(el);
      stations.push({ box, name: (el.getAttribute("data-station") || "?").slice(0, 24),
                      visible: box.x1 > 0 && box.x0 < W && box.y1 > 0 && box.y0 < H });
    }

    // ---- the paths, and each one's painted half-width ----------------------
    const EDGE_RE = /(^|\s)edge($|\s|-)/;
    const svgs = [...document.querySelectorAll("svg.edges, svg.edges-top")];
    const paint = new Map();      // `d` -> widest VISIBLE half-stroke in frame px
    const all = [];
    for (const svg of svgs) {
      for (const p of svg.querySelectorAll("path")) {
        if (p.closest("defs") || p.closest("marker")) continue;
        if (!rendered(p)) continue;
        const ctm = p.getScreenCTM();
        if (!ctm) continue;
        const scale = Math.hypot(ctm.a, ctm.b) / fit;         // user units -> frame px
        const sw = (parseFloat(getComputedStyle(p).strokeWidth) || 0) * scale;
        const d = p.getAttribute("d") || "";
        paint.set(d, Math.max(paint.get(d) || 0, sw / 2));
        all.push({ p, ctm, d });
      }
    }

    for (const { p, ctm, d } of all) {
      if (!EDGE_RE.test((p.getAttribute("class") || "").trim())) continue;   // halos ride along
      const L = p.getTotalLength();
      if (!L) continue;
      const label = (p.getAttribute("data-edge") || p.getAttribute("class") || "edge").slice(0, 40);
      const half = paint.get(d) || 0;
      const at = (u) => {
        const q = p.getPointAtLength(u).matrixTransform(ctm);
        return toFrame(q.x, q.y);
      };
      // SCOPE. An edge is a teaching line in this beat only if the frame shows
      // something at BOTH of its ends. `tol` is the anchor checker's stage-px
      // tolerance carried into frame px by this hold's own scale.
      const t = TOL * k;
      const stationsAt = (pt) => stations.filter(s =>
        pt.x >= s.box.x0 - t && pt.x <= s.box.x1 + t &&
        pt.y >= s.box.y0 - t && pt.y <= s.box.y1 + t);
      const ends = [stationsAt(at(0)), stationsAt(at(L))];
      if (ends.some(list => !list.length)) { floating++; continue; }   // anchoring is another gate's job
      if (!ends.every(list => list.some(s => s.visible))) { offstage++; continue; }

      // ---- CLIPPED-ANCHOR exemption: see the header. Measured per (edge, side,
      // hold) from the station's own bbox against the frame side, never a name.
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
  }, { MARGIN, TOL, SAMPLES, FRAME_SEL, STATION_SEL, k: Number(hold.k) });

  measured += out.edges; scenery += out.offstage; unanchored += out.floating;
  const id = hold.id || "(unnamed)";
  for (const v of out.res) violations.push(`${id}: [${v.kind}] ${v.label}: ${v.detail}`);
  for (const w of out.waived || []) waivers.push(`${id}: ${w}`);
  console.log(`  hold ${id.padEnd(10)} k=${hold.k}  edges-measured ${String(out.edges).padStart(3)}`
    + `  off-stage ${String(out.offstage).padStart(3)}  unanchored ${out.floating}`
    + `  clipped-anchor waivers ${(out.waived || []).length}`);
}
await browser.close();

if (!measured) {
  console.error("FAIL: zero edges measured at every hold -- wrong url, broken page, or "
    + `selector drift ("${FRAME_SEL}" / "${STATION_SEL}" / svg.edges)`);
  process.exit(1);
}
console.log(`N/A: ${scenery} edge instance(s) not measured -- a station off-frame at one end `
  + "or nothing of the run on screen: scenery in that beat, not a teaching line"
  + (unanchored ? `; ${unanchored} unanchored endpoint edge(s) left to verify-html-edge-anchors` : ""));
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
