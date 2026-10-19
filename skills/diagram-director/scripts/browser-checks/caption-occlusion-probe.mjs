// The PAGE half of verify-caption-occlusion.mjs. Both functions below are serialised into
// the browser by `page.evaluate`, so they close over nothing and take every input as an
// argument. They live apart from the driver because the driver's job -- seek, pin, decide,
// print, exit -- is a different responsibility from measuring one instant.
//
// Requires `window.__ddGeom` (page-geometry.mjs) and `window.__ddInkBox` (ink-box.mjs).

/**
 * Is this caption's card fully revealed at the instant the page is currently seeked to?
 *
 * The house caption is hidden by GEOMETRY, not opacity: a `clip-path` inset parked 101%
 * past the card's right edge wipes in and out (references/camera-beat.md -> "The caption
 * animates ONE property, and it is clip-path"). The three system-design goldens still ship
 * the older opacity+clip block, so BOTH are read: revealed means the card is opaque AND
 * every inset side sits at or outside the card body. Measuring a half-wiped card would
 * report an occlusion the viewer never sees, and missing one would hide a real defect --
 * so the driver walks a small ladder of instants and asks this at each.
 */
export function readCaptionState(sel) {
  const el = document.querySelector(sel);
  if (!el) return { found: false };
  const cs = getComputedStyle(el);
  const opacity = Number(cs.opacity);
  const clip = cs.clipPath || "none";
  let open = true;
  const inset = clip.match(/inset\(([^)]*)\)/);
  if (inset) {
    // Parked poses are far outside the body (100%/101%, or the same in px); an open pose
    // is at or just past the edge (-1%). A 2-unit threshold separates them in either unit.
    const values = inset[1].trim().split(/[\s/]+/).map(parseFloat).filter(v => !Number.isNaN(v));
    open = values.every(v => v <= 2);
  }
  return { found: true, revealed: opacity >= 0.9 && open, opacity, clip };
}

/**
 * One caption, one instant. Returns everything measured; the driver owns the verdict.
 *
 * `bbox` is the hold's must-show box in WORLD units (`holds[].bbox`), or null. It is used
 * for one thing only: proving a proposed dx keeps the card inside the frame the hold was
 * solved for. Without it no fix is proposed -- an unproven fix is advice, and this gate
 * does not give advice.
 */
export function measureCaption({ sel, tol, subjectPad, bbox }) {
  const G = window.__ddGeom;
  const card = document.querySelector(sel);
  if (!card) return { found: false };
  const boxEl = card.querySelector("rect.caption-box, rect") || card;
  const rect = G.boxOf(boxEl.getBoundingClientRect());
  const ctx = document.createElement("canvas").getContext("2d");

  // ---- edge labels: a rendered string the card would destroy ------------------------
  // `.edge__label--mono` is a BEM modifier shipped WITHOUT its base class in two goldens,
  // so a `.edge__label` selector would miss it. Matching the token catches both, and an
  // edge label is an edge label whichever spelling the file uses.
  const labels = [];
  for (const el of document.querySelectorAll('[class*="edge__label"]')) {
    if (!el.textContent.trim() || !G.visible(el)) continue;
    const client = el.getBoundingClientRect();
    if (!G.inView(client)) continue;
    const ink = window.__ddInkBox(el, ctx);
    labels.push({ text: el.textContent.trim().slice(0, 30),
                  box: ink ? { left: ink.left, right: ink.right, top: ink.top, bottom: ink.bottom }
                           : G.boxOf(client),
                  measuredOn: ink ? "ink" : "box" });
  }

  // ---- subjects: the nodes this beat's lit spotlight encloses ------------------------
  // No new manifest field: the beat already says who it is about, on screen, by lighting
  // brackets around them. A bracket's four L-shaped subpaths share one bbox, and
  // camera-beat.md lets a merged bracket enclose the caption card too -- harmless here,
  // because only `g.node` shapes are read out of it.
  const brackets = [];
  for (const focus of document.querySelectorAll(".node__focus")) {
    if (!G.visible(focus, true)) continue;
    const r = focus.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    brackets.push(G.boxOf(r));
  }
  // Both construction modes, because the RULE is engine-general and only the instrument is
  // per-genre (the same split verify-frame-edge-margin.mjs and its SVG twin make): an
  // SVG-mode cut's subjects are `g.node > .node__shape`, an HTML-mode `process` cut's are
  // `[data-station]` divs.
  const candidates = [];
  for (const node of document.querySelectorAll("g.node")) {
    const shape = node.querySelector(".node__shape:not([style])") || node.querySelector(".node__shape");
    if (!shape || !G.visible(shape)) continue;
    candidates.push({ id: node.getAttribute("data-node-id"),
                      name: node.getAttribute("data-node-id")
                        || ((node.querySelector(".node__label") || {}).textContent || "?").trim().slice(0, 20),
                      box: G.boxOf(shape.getBoundingClientRect()) });
  }
  for (const station of document.querySelectorAll("[data-station]")) {
    if (!G.visible(station)) continue;
    candidates.push({ id: station.getAttribute("data-station"),
                      name: station.getAttribute("data-station"),
                      box: G.boxOf(station.getBoundingClientRect()) });
  }
  const subjectNodes = candidates.filter(c =>
    brackets.some(b => c.box.left >= b.left - subjectPad && c.box.right <= b.right + subjectPad &&
                       c.box.top >= b.top - subjectPad && c.box.bottom <= b.bottom + subjectPad));
  const subjects = new Set(subjectNodes.map(c => c.name));
  const subjectIds = new Set(subjectNodes.map(c => c.id).filter(Boolean));

  // ---- edges: painted band, split into this beat's subjects and everything else ------
  // "Touches a subject" is read TWO ways, and either is enough. The declared way is
  // `data-from`/`data-to` naming a subject's `data-node-id`. The measured way is an
  // ENDPOINT landing on a subject's box (12px, the same slack verify-hold-geometry.mjs
  // uses for "connected") -- without it the rule would be N-A on every cut written before
  // `node-identity` existed, which is three of the four frozen goldens, and an
  // identity-less cut is exactly the kind that ships this defect.
  const NEAR = 12;
  const touches = (pt) => subjectNodes.some(c =>
    pt.x >= c.box.left - NEAR && pt.x <= c.box.right + NEAR &&
    pt.y >= c.box.top - NEAR && pt.y <= c.box.bottom + NEAR);
  const edges = [];
  for (const path of document.querySelectorAll("path.edge")) {
    if (!G.visible(path, true)) continue;
    const band = G.paintedBand(path);
    if (!band) continue;
    const from = path.getAttribute("data-from"), to = path.getAttribute("data-to");
    const name = from || to ? `${from || "?"} -> ${to || "?"}`
      : (path.getAttribute("data-edge")
         || (path.querySelector("title") || {}).textContent
         || path.getAttribute("class") || "edge").trim().slice(0, 40);
    const declared = Boolean((from && subjectIds.has(from)) || (to && subjectIds.has(to)));
    const anchored = touches(band.pts[0]) || touches(band.pts[band.pts.length - 1]);
    const distance = G.polyRectDist(band.pts, rect);
    edges.push({ name, isSubject: declared || anchored, band,
                 clearance: distance - band.halfPx,
                 overlap: Math.max(0, band.halfPx - distance) });
  }

  // ---- a fix only if it is PROVEN ---------------------------------------------------
  // Walk dx outwards 1px at a time and re-measure. The first offset at which the shifted
  // card clears every label and every subject edge by >= 1px AND still lies inside the
  // hold's must-show box is a fact about this page, not a suggestion. If none exists
  // within 240px, no fix is reported.
  const violatingLabels = labels.filter(l => G.overlapPx(rect, l.box) > tol);
  const violatingEdges = edges.filter(e => e.isSubject && e.overlap > tol);
  let fix = null;
  if (violatingLabels.length || violatingEdges.length) {
    const camera = document.querySelector(".camera");
    const ctm = camera && camera.getScreenCTM ? camera.getScreenCTM() : null;
    let frame = null, scale = 1;
    if (bbox && ctm) {
      const svg = camera.ownerSVGElement || camera;
      const toScreen = (x, y) => {
        const pt = svg.createSVGPoint(); pt.x = x; pt.y = y;
        return pt.matrixTransform(ctm);
      };
      const a = toScreen(bbox[0], bbox[1]), b = toScreen(bbox[0] + bbox[2], bbox[1] + bbox[3]);
      frame = { left: Math.min(a.x, b.x), right: Math.max(a.x, b.x),
                top: Math.min(a.y, b.y), bottom: Math.max(a.y, b.y) };
      scale = Math.hypot(ctm.a, ctm.b) || 1;
    }
    const clearsAt = (dx) => {
      const moved = { left: rect.left + dx, right: rect.right + dx, top: rect.top, bottom: rect.bottom };
      if (frame && (moved.left < frame.left || moved.right > frame.right)) return false;
      for (const l of labels) if (G.overlapPx(moved, l.box) > 0) return false;
      for (const e of edges)
        if (e.isSubject && G.polyRectDist(e.band.pts, moved) < e.band.halfPx + 1) return false;
      return true;
    };
    if (frame) {
      for (let step = 1; step <= 240 && !fix; step++)
        for (const dx of [-step, step])
          if (clearsAt(dx)) { fix = { dxPx: dx, dxWorld: Math.round((dx / scale) * 10) / 10 }; break; }
    }
  }

  return {
    found: true, card: rect,
    subjects: [...subjects].sort(), brackets: brackets.length,
    labelsSeen: labels.length,
    labelHits: violatingLabels.map(l => ({ text: l.text, measuredOn: l.measuredOn,
                                           overlap: Math.round(G.overlapPx(rect, l.box) * 10) / 10 })),
    edgesSeen: edges.length,
    subjectEdgesSeen: edges.filter(e => e.isSubject).length,
    subjectHits: violatingEdges.map(e => ({ name: e.name, overlap: Math.round(e.overlap * 10) / 10 })),
    otherHits: edges.filter(e => !e.isSubject && e.overlap > tol)
      .map(e => ({ name: e.name, overlap: Math.round(e.overlap * 10) / 10 })),
    tightestSubject: edges.filter(e => e.isSubject).reduce(
      (best, e) => (best === null || e.clearance < best ? e.clearance : best), null),
    fix,
  };
}
