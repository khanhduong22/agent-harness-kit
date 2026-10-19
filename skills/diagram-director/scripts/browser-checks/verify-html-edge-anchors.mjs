// The HTML-MODE edge check: `diagram-director/scripts/verify_edge_anchors.py` for a cut whose
// stations are DIVs.
//
// WHY IT HAS TO EXIST. The static checker finds node boxes only from SVG
// `<g class="node">`/`.node__shape`. A `--genre process` cut is built HTML-first
// (references/genres/process.md -> "Construction mode"): every station is a div,
// and only the CONNECTORS live in a thin `<svg class="edges">` overlay. Run the
// static checker on one and it finds ZERO boxes, so every overlay `<path
// class="edge">` reports FLOATING -- a gate that fails 100% of correct files is
// not a gate. This script asks the same two questions of the same two defect
// classes, but measures the station boxes in a browser, where an HTML box is the
// only place its geometry exists.
//
// WHY THE PX PARITY IS EXACT, not approximate. Clause 2 of the stage/overlay
// contract (templates/snippets/process-stage-and-edges.css) pins
// `viewBox="0 0 <stage w> <stage h>"` on a `.stage` that carries the SAME
// explicit px width and height, so 1 SVG user unit == 1 CSS px forever. A path's
// `d` is therefore already in stage-local px, and a station's
// getBoundingClientRect only has to be moved into the same origin (and divided
// by whatever scale the camera happens to be at) to be compared with it. No
// projection, no tolerance for a mapping error.
//
// THE THREE DEFECT CLASSES
//   FLOATING       an endpoint that is not within `--tol` px of any station box.
//                  Same rule and same default tol (12, arrowhead shortening) as
//                  verify_edge_anchors.py.
//   WRONG-SIDE     an endpoint that IS on a station box but on the side the edge
//                  had to wrap around to reach. Ported from
//                  verify_edge_anchors.py -> facing_side(): with `n` the unit
//                  outward normal of the side the endpoint sits on and `r` the
//                  reference point the edge runs towards, the rule is
//                  `n . (r - p) > -tol`. Within `tol` of a corner BOTH adjacent
//                  sides count, which is what lets a diagonal edge land on a
//                  corner honestly.
//
//                  WHAT `r` IS, and why it is NOT the control point. On a
//                  STRAIGHT segment `r` is the adjacent vertex -- unchanged, and
//                  the same rule the static checker applies. On a BEZIER it is
//                  the curve's own on-path point a quarter of the terminal
//                  segment away (t=0.25 from a tail, t=0.75 to a head), NOT the
//                  adjacent control point.
//                  A CONTROL POINT CAN BRIBE THE TANGENT RULE: it is authored,
//                  it need not lie on the curve, and bending it sideways makes
//                  the local tangent claim an approach the curve never makes --
//                  so a path that truly arrives from below can be made to read
//                  as arriving from the left and pass the left-side test. The
//                  static SVG checker never met this (it skips golden curves by
//                  design and its straight segments use real vertices); the HTML
//                  mode is where curves are load-bearing, so the sample has to
//                  come off the curve. Mutation-proved: a `C` whose last control
//                  is dragged left of a left-edge landing while the curve itself
//                  comes back from inside the box passes the old rule and fails
//                  this one.
//   DEAD-GEOMETRY  the HTML mode's own defect, and the price of contract clause
//                  4: `.edges` sits UNDER the stations, so a path may legally run
//                  behind one -- but a path whose ENTIRE run is behind opaque
//                  station boxes has not been drawn at all. It is in the markup,
//                  it passes anchoring, and it is invisible. process.md lists it
//                  as a build trap; this is the instrument for it.
//
// THE WEBAPP TEMPLATE CONTRACT (v2), same script, because it is the same claim
// measured one layer in: a green pull-line is only honest if the thing it leaves
// from is a real, visible, measured anchor. Scoped to WEBAPP stations only -- a
// `[data-station]` that carries `.win` or holds a `[data-anchor]` -- so a cut
// with no webapp station (every cut built before this station existed) is
// untouched and this whole block is vacuous.
//   WEBAPP-CONTRACT  a webapp station that does not carry EXACTLY THREE
//                    `[data-anchor]` elements (invariant #2), or that has no
//                    `.win__url` in its chrome (invariant #1) -- and, for a
//                    `.win--deploy` station, one that carries ANY anchor: the
//                    deploy beat claims "it is live at an address", not "this is
//                    where the data lives".
//   ANCHOR-GATED     an anchor that IS, or sits inside, a `[data-lod="close"]`
//                    element. Such an element is opacity:0 at the far tier, so
//                    its pull-line would leave from a box the viewer cannot see
//                    at overview and the three-anchor claim would be a zoom-only
//                    truth. The `.lod` crossfade is the fix: its box is never
//                    gated.
//   LOD-LEAK         an element inside the LOD system that sets its OWN
//                    `opacity`. `[data-lod="close"]` and a station rule have
//                    IDENTICAL specificity and the station sheet loads later, so
//                    the bare declaration silently wins and the element never
//                    hides (cost a rebuild: `.kpi__d{opacity:.72}`). Measured by
//                    forcing every `data-lod-tier` host to "far" with transitions
//                    disabled and reading back the computed opacity, so the
//                    verdict does not depend on which tier the page happens to
//                    be parked at.
//
// House rule (diagram-director/scripts/browser-checks/README.md): a check that finds nothing
// FAILS. Zero stages, zero stations or zero edges is a wrong url, a broken page
// or selector drift -- never a clean cut. Zero WEBAPP stations is not one of
// those: the station is optional vocabulary, not part of the stage contract.
//
//   node verify-html-edge-anchors.mjs <url> [--tol 12] [--stage <sel>]
//        [--station <sel>] [--samples 64]
import puppeteer from "./resolve-puppeteer.mjs";

const USAGE = "usage: verify-html-edge-anchors.mjs <url> [--tol N] [--stage <sel>] "
  + "[--station <sel>] [--samples N]";
const argv = process.argv.slice(2);
let url = null;
const flags = {};
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a.startsWith("--")) flags[a.slice(2)] = argv[++i];
  else if (!url) url = a;
}
if (!url) { console.error(USAGE); process.exit(2); }
const TOL = Number(flags.tol ?? 12);
const STAGE_SEL = flags.stage || ".stage";
const STATION_SEL = flags.station || "[data-station]";
const SAMPLES = Number(flags.samples ?? 64);

const browser = await puppeteer.launch({ headless: true });
const page = await browser.newPage();
await page.goto(url, { waitUntil: "networkidle2" });
await page.evaluate(() => document.fonts.ready);
await new Promise(r => setTimeout(r, 500));

const out = await page.evaluate(({ TOL, STAGE_SEL, STATION_SEL, SAMPLES }) => {
  // The camera may be mid-move at t=0, so freeze the page first: every box read
  // below must belong to ONE instant, and the scale divided out must be the
  // scale that was in force when the rect was measured.
  for (const a of document.getAnimations()) {
    try { a.pause(); a.currentTime = 0; } catch { /* finished/idle */ }
  }
  document.documentElement.getBoundingClientRect();

  const SIDES = [["left", -1, 0], ["right", 1, 0], ["top", 0, -1], ["bottom", 0, 1]];

  // Ported from verify_edge_anchors.py -> facing_side(). Returns the BEST signed
  // distance from `ref` to the plane of the side(s) the endpoint sits on.
  const facingSide = (pt, ref, box, tol) => {
    const dist = { left: Math.abs(pt.x - box.x0), right: Math.abs(pt.x - box.x1),
                   top: Math.abs(pt.y - box.y0), bottom: Math.abs(pt.y - box.y1) };
    const near = Math.min(dist.left, dist.right, dist.top, dist.bottom);
    let best = null, bestSide = null;
    for (const [name, nx, ny] of SIDES) {
      if (dist[name] > near + tol) continue;               // corner: both sides count
      const depth = nx * (ref.x - pt.x) + ny * (ref.y - pt.y);
      if (best === null || depth > best) { best = depth; bestSide = name; }
    }
    return { ok: best > -tol, side: bestSide, depth: best };
  };

  // ---- path `d` -> segments, in the path's own (== stage px) coordinates -----
  // Absolute commands only, exactly like the static checker: a `process` cut's
  // overlay is emitted, and an emitter that writes relative commands has a bug
  // the checker should surface rather than paper over.
  const NUM = /-?\d*\.?\d+(?:[eE][-+]?\d+)?/g;
  const parse = (d) => {
    if (!d) return null;
    if (/[mlhvcsqtaz]/.test(d.replace(/[MLHVCSQTAZ]/g, ""))) return null;  // relative
    const segs = [];
    let x = 0, y = 0, sx = 0, sy = 0, started = false;
    const re = /([MLHVCSQTAZ])([^MLHVCSQTAZ]*)/g;
    let m;
    while ((m = re.exec(d))) {
      const cmd = m[1];
      const n = (m[2].match(NUM) || []).map(Number);
      const push = (nx, ny, c1, c2) => {
        segs.push({ a: { x, y }, b: { x: nx, y: ny }, c1: c1 || null, c2: c2 || null });
        x = nx; y = ny;
      };
      if (cmd === "M") {
        for (let i = 0; i + 1 < n.length; i += 2) {
          if (i === 0) {
            if (started) return null;                       // second subpath: not our shape
            x = n[0]; y = n[1]; sx = x; sy = y; started = true;
          } else push(n[i], n[i + 1]);
        }
      } else if (cmd === "L") {
        for (let i = 0; i + 1 < n.length; i += 2) push(n[i], n[i + 1]);
      } else if (cmd === "H") { for (const v of n) push(v, y); }
      else if (cmd === "V") { for (const v of n) push(x, v); }
      else if (cmd === "C") {
        for (let i = 0; i + 5 < n.length; i += 6)
          push(n[i + 4], n[i + 5], { x: n[i], y: n[i + 1] }, { x: n[i + 2], y: n[i + 3] });
      } else if (cmd === "Q") {
        // BOTH controls are set to the single quadratic control: the departure
        // DIRECTION is identical either way, and `quad` tells the sampler below
        // to evaluate the quadratic, so the point it returns is on the real curve.
        for (let i = 0; i + 3 < n.length; i += 4) {
          push(n[i + 2], n[i + 3], { x: n[i], y: n[i + 1] }, { x: n[i], y: n[i + 1] });
          segs[segs.length - 1].quad = true;
        }
      } else if (cmd === "S" || cmd === "T" || cmd === "A") {
        return null;                                        // not emitted by this genre
      } else if (cmd === "Z") { push(sx, sy); }
    }
    return segs.length ? segs : null;
  };

  // A point ON the segment at parameter t. This is what closes the control-point
  // loophole: a control point is authored and need not touch the curve, so the
  // facing rule asks the curve itself where it came from.
  const pointAt = (s, t) => {
    const u = 1 - t;
    if (!s.c1) return { x: s.a.x + (s.b.x - s.a.x) * t, y: s.a.y + (s.b.y - s.a.y) * t };
    if (s.quad)
      return { x: u * u * s.a.x + 2 * u * t * s.c1.x + t * t * s.b.x,
               y: u * u * s.a.y + 2 * u * t * s.c1.y + t * t * s.b.y };
    return { x: u*u*u * s.a.x + 3*u*u*t * s.c1.x + 3*u*t*t * s.c2.x + t*t*t * s.b.x,
             y: u*u*u * s.a.y + 3*u*u*t * s.c1.y + 3*u*t*t * s.c2.y + t*t*t * s.b.y };
  };
  // A quarter of the terminal segment: far enough that a bent control point
  // cannot dominate the direction, near enough that it is still the approach and
  // not the far end of the curve.
  const APPROACH_T = 0.25;

  const res = [];
  let stages = 0, stationCount = 0, edgeCount = 0, webappCount = 0, lodChecked = 0;

  for (const stage of document.querySelectorAll(STAGE_SEL)) {
    const svg = stage.querySelector("svg.edges") || stage.querySelector("svg");
    if (!svg) continue;
    const vb = (svg.getAttribute("viewBox") || "").trim().split(/[\s,]+/).map(Number);
    if (vb.length !== 4 || !vb[2] || !vb[3]) {
      res.push({ kind: "CONTRACT", label: "stage svg", detail:
        `<svg class="edges"> has no usable viewBox ("${svg.getAttribute("viewBox")}") -- `
        + "contract clause 2 (1 svg unit == 1 css px) cannot hold" });
      continue;
    }
    const sr = stage.getBoundingClientRect();
    // The stage's own px size is the viewBox by contract; the rect is that size
    // times whatever the camera scale is. Dividing by the ratio puts every
    // measured box back into the units the path `d` is written in.
    const scale = sr.width / vb[2];
    const sy2 = sr.height / vb[3];
    if (!(scale > 0) || Math.abs(scale - sy2) > 0.01) {
      res.push({ kind: "CONTRACT", label: "stage box", detail:
        `stage rect ${sr.width.toFixed(1)}x${sr.height.toFixed(1)} is not a uniform scale of `
        + `viewBox ${vb[2]}x${vb[3]} (x ${scale.toFixed(4)} vs y ${sy2.toFixed(4)}) -- `
        + "clause 1/2: the stage px size and the viewBox must agree" });
      continue;
    }
    stages++;
    const local = (r) => ({ x0: (r.left - sr.left) / scale, y0: (r.top - sr.top) / scale,
                            x1: (r.right - sr.left) / scale, y1: (r.bottom - sr.top) / scale });
    const boxes = [];
    for (const el of stage.querySelectorAll(STATION_SEL)) {
      const r = el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      boxes.push({ box: local(r),
                   name: (el.getAttribute("data-station") || el.className || "?")
                     .toString().trim().slice(0, 28) });
    }
    stationCount += boxes.length;
    if (!boxes.length) continue;

    for (const path of svg.querySelectorAll('path[class*="edge"]')) {
      const cls = (path.getAttribute("class") || "").trim();
      if (!/(^|\s)edge($|\s|-)/.test(cls)) continue;
      edgeCount++;
      const label = (path.getAttribute("data-edge") || cls).slice(0, 40);
      const segs = parse(path.getAttribute("d"));
      if (!segs) {
        res.push({ kind: "UNPARSED", label, detail:
          `d="${(path.getAttribute("d") || "").slice(0, 46)}..." -- absolute M/L/H/V/C/Q/Z only` });
        continue;
      }
      const first = segs[0], last = segs[segs.length - 1];
      // STRAIGHT: the adjacent vertex, exactly as verify_edge_anchors.py does.
      // CURVED: a point sampled off the curve itself -- see the header note on
      // the control-point loophole.
      const ends = [
        { pt: first.a, ref: first.c1 ? pointAt(first, APPROACH_T) : first.b,
          curved: !!first.c1, which: "tail (start)" },
        { pt: last.b, ref: last.c1 ? pointAt(last, 1 - APPROACH_T) : last.a,
          curved: !!last.c1, which: "head (end)" },
      ];
      for (const { pt, ref, curved, which } of ends) {
        const anchors = boxes.filter(({ box }) =>
          pt.x >= box.x0 - TOL && pt.x <= box.x1 + TOL &&
          pt.y >= box.y0 - TOL && pt.y <= box.y1 + TOL);
        if (!anchors.length) {
          res.push({ kind: "FLOATING", label, detail:
            `${which} floats at (${pt.x.toFixed(0)},${pt.y.toFixed(0)}) -- no station within ${TOL}px` });
          continue;
        }
        const verdicts = anchors.map(a => ({ a, v: facingSide(pt, ref, a.box, TOL) }));
        if (verdicts.some(v => v.v.ok)) continue;
        const worst = verdicts.reduce((m, v) => (v.v.depth > m.v.depth ? v : m));
        res.push({ kind: "WRONG-SIDE", label, detail:
          `${which} sits on the ${worst.v.side} border of ${worst.a.name} at `
          + `(${pt.x.toFixed(0)},${pt.y.toFixed(0)}) but the ${curved ? "curve runs" : "edge leaves"}`
          + ` towards (${ref.x.toFixed(0)},${ref.y.toFixed(0)})`
          + `${curved ? " -- sampled ON the curve a quarter of the terminal segment away, "
                        + "not at the control point" : ""}`
          + `, ${(-worst.v.depth).toFixed(0)}px behind that side` });
      }

      // ---- DEAD GEOMETRY ---------------------------------------------------
      // Contract clause 4 lets an edge run behind a station rather than be
      // clipped by hand. The cost is a path that is entirely behind opaque
      // blocks and therefore never drawn. Sample the run and require at least
      // one sample in the open.
      const L = path.getTotalLength();
      if (L > 1) {
        let open = 0, total = 0;
        for (let i = 0; i <= SAMPLES; i++) {
          const p = path.getPointAtLength((L * i) / SAMPLES);
          total++;
          const covered = boxes.some(({ box }) =>
            p.x >= box.x0 && p.x <= box.x1 && p.y >= box.y0 && p.y <= box.y1);
          if (!covered) open++;
        }
        if (!open)
          res.push({ kind: "DEAD-GEOMETRY", label, detail:
            `all ${total} samples of this path lie under opaque station boxes -- `
            + "the connector exists only in the markup (process.md build trap)" });
      }
    }
  }

  // ===== WEBAPP TEMPLATE CONTRACT v2 =====================================
  // Runs AFTER every box above has been measured: it mutates `data-lod-tier`
  // and kills transitions, and neither may be in force while geometry is read.
  const killer = document.createElement("style");
  // A transition would make the tier flip below report the value the page was
  // ALREADY at (the transition has not advanced yet), which is a false LOD-LEAK
  // on a correct page. Kill them for the duration of the sweep only.
  killer.textContent = "*,*::before,*::after{transition:none !important}";
  document.head.appendChild(killer);

  for (const stage of document.querySelectorAll(STAGE_SEL)) {
    for (const el of stage.querySelectorAll(STATION_SEL)) {
      // A WEBAPP station is one that carries the shell class or holds an
      // anchor. Anything else on the rail -- a brief, a jar, a diamond -- is
      // out of scope, which is what keeps this block vacuous on older cuts.
      const isWebapp = el.classList.contains("win") || !!el.querySelector("[data-anchor]");
      if (!isWebapp) continue;
      webappCount++;
      const name = (el.getAttribute("data-station") || el.className || "?").toString().slice(0, 28);
      const anchors = [...el.querySelectorAll("[data-anchor]")];

      if (el.classList.contains("win--deploy")) {
        if (anchors.length)
          res.push({ kind: "WEBAPP-CONTRACT", label: name, detail:
            `.win--deploy carries ${anchors.length} [data-anchor] -- at the deploy beat the claim `
            + 'is "it is live at an address", not "this is where the data lives"; anchors belong '
            + "to the derivation beat only" });
      } else if (anchors.length !== 3) {
        res.push({ kind: "WEBAPP-CONTRACT", label: name, detail:
          `${anchors.length} [data-anchor] element(s) -- template contract v2 invariant #2 is `
          + "EXACTLY THREE semantic anchors (a form is one possible source, never the required one)" });
      }
      if (el.classList.contains("win") && !el.querySelector(".win__url"))
        res.push({ kind: "WEBAPP-CONTRACT", label: name, detail:
          "no .win__url inside the browser chrome -- invariant #1 is chrome AND the address, "
          + "which is what says the artifact runs on the web before the deploy beat says it" });

      for (const a of anchors) {
        if (a.closest('[data-lod="close"]'))
          res.push({ kind: "ANCHOR-GATED", label: name, detail:
            `anchor "${a.dataset.anchor}" is (or sits inside) a [data-lod="close"] element -- `
            + "opacity:0 at the far tier, so the three-anchor claim would be true only at zoom; "
            + "wrap it in the .lod crossfade instead, whose box is never gated" });
      }
    }

  }

  // ---- LOD CASCADE LEAK ---------------------------------------------------
  // Swept over the WHOLE DOCUMENT, not per stage: the tier host is wherever the
  // author put it -- the stage, the beat wrapper, or the .frame above both --
  // and a per-stage query silently finds none of the last two.
  const hosts = [...document.querySelectorAll("[data-lod-tier]")];
  if (hosts.length) {
    const prev = hosts.map(h => h.getAttribute("data-lod-tier"));
    hosts.forEach(h => h.setAttribute("data-lod-tier", "far"));
    for (const el of document.querySelectorAll('[data-lod="close"], .lod__near')) {
      if (!el.closest("[data-lod-tier]")) continue;
      // an element driven by keyframes is parked at t=0 by the freeze above, so
      // its opacity is an animation frame, not a cascade verdict.
      if (getComputedStyle(el).animationName !== "none") continue;
      lodChecked++;
      const op = Number(getComputedStyle(el).opacity);
      if (op > 0.01)
        res.push({ kind: "LOD-LEAK", label: (el.className || el.tagName).toString().slice(0, 28),
          detail: `opacity ${op} at the FAR tier ("${el.textContent.trim().slice(0, 20)}") -- `
            + "something inside the LOD subtree sets its own opacity and wins the cascade at equal "
            + "specificity. Dim with color-mix; leave opacity to the tier switch" });
    }
    hosts.forEach((h, i) => (prev[i] === null ? h.removeAttribute("data-lod-tier")
                                              : h.setAttribute("data-lod-tier", prev[i])));
  }
  killer.remove();

  return { res, stages, stationCount, edgeCount, webappCount, lodChecked };
}, { TOL, STAGE_SEL, STATION_SEL, SAMPLES });

await browser.close();

const { res, stages, stationCount, edgeCount, webappCount, lodChecked } = out;
// House rule: a check that finds nothing FAILS. `webappCount` is deliberately
// NOT in this test -- the webapp station is optional vocabulary, so zero of them
// is a normal cut, not selector drift.
if (!stages || !stationCount || !edgeCount) {
  console.error(`FAIL: ${stages} stage(s) matching "${STAGE_SEL}", ${stationCount} station(s) `
    + `matching "${STATION_SEL}", ${edgeCount} path.edge -- wrong url, broken page, or selector drift`);
  process.exit(1);
}
if (res.length) {
  console.log("HTML-EDGE-ANCHOR / WEBAPP-CONTRACT DEFECTS:");
  for (const v of res) console.log(`  [${v.kind}] ${v.label}: ${v.detail}`);
  console.log(`\n${res.length} defect(s) across ${edgeCount} edge(s) / ${webappCount} webapp station(s).`);
  process.exit(1);
}
console.log(`all clear -- ${edgeCount} edge endpoint pair(s) anchored on a facing station side `
  + `and none dead, across ${stages} stage(s) / ${stationCount} station(s) (tol ${TOL}px); `
  + `webapp contract v2 ok on ${webappCount} station(s), ${lodChecked} LOD element(s) swept`);
process.exit(0);
