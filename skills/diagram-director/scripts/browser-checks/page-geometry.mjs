// Screen-space geometry the render-side gates share, installed INTO the page.
//
// Every gate here measures the same two things -- "is this element actually painted right
// now" and "how far is this rect from that painted stroke" -- and every gate used to carry
// its own copy. The copies drifted: `verify-hold-geometry.mjs` learned `allowThin` for
// axis-aligned paths (a horizontal `<path>` has a zero-height client rect) months after
// `verify-text-containment.mjs` was written, and a check that never learned it silently
// skipped most of a cut's edges. This module is where that lesson is kept once.
//
// PAINTED, NOT GEOMETRIC. An edge is not its centreline: it is a band, centreline +- half
// the computed stroke width, and `verify-frame-edge-margin.mjs` was born from a cut that
// cleared a frame side by 0.8px on the centreline while its 11px halo was 8px over the
// edge. `paintedBand()` returns that band, honouring `vector-effect: non-scaling-stroke`
// as a constant SCREEN width, and refuses (null) a path with no stroke paint at all --
// an unpainted path occludes nothing and must not be reported as if it did.
//
// Install once per page, after `document.fonts.ready`:
//
//     import { installGeometry } from "./page-geometry.mjs";
//     await installGeometry(page);           // -> window.__ddGeom
function ddGeomFactory() {
  // `allowThin`: a perfectly horizontal or vertical <path> has a ZERO-height (or
  // zero-width) client rect, because getBoundingClientRect measures the geometry and not
  // the stroke. Requiring both dimensions silently skips every axis-aligned edge on the
  // page, which is most of them (found by verify-hold-geometry.mjs's own fixture).
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

  const inView = (r) =>
    r.right > 0 && r.left < innerWidth && r.bottom > 0 && r.top < innerHeight;

  /** A plain, structured-clonable copy of a DOMRect -- page callbacks return these. */
  const boxOf = (r) => ({ left: r.left, right: r.right, top: r.top, bottom: r.bottom });

  /** Penetration depth of two rects in px; 0 when they do not overlap at all. */
  const overlapPx = (a, b) => {
    const dx = Math.min(a.right, b.right) - Math.max(a.left, b.left);
    const dy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    return dx > 0 && dy > 0 ? Math.min(dx, dy) : 0;
  };

  const ptSegDist = (p, a, b) => {
    const dx = b.x - a.x, dy = b.y - a.y;
    const len2 = dx * dx + dy * dy;
    let t = len2 ? ((p.x - a.x) * dx + (p.y - a.y) * dy) / len2 : 0;
    t = Math.max(0, Math.min(1, t));
    return Math.hypot(p.x - (a.x + t * dx), p.y - (a.y + t * dy));
  };

  const side = (a, b, p) => (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x);

  const segsCross = (a, b, c, d) => {
    const d1 = side(a, b, c), d2 = side(a, b, d);
    const d3 = side(c, d, a), d4 = side(c, d, b);
    return ((d1 > 0) !== (d2 > 0)) && ((d3 > 0) !== (d4 > 0));
  };

  const segSegDist = (a, b, c, d) => segsCross(a, b, c, d) ? 0 : Math.min(
    ptSegDist(a, c, d), ptSegDist(b, c, d), ptSegDist(c, a, b), ptSegDist(d, a, b));

  const inRect = (p, r) =>
    p.x >= r.left && p.x <= r.right && p.y >= r.top && p.y <= r.bottom;

  /** Distance from segment a->b to rect r; 0 when the segment touches or enters it. */
  const segRectDist = (a, b, r) => {
    if (inRect(a, r) || inRect(b, r)) return 0;
    const c = [{ x: r.left, y: r.top }, { x: r.right, y: r.top },
               { x: r.right, y: r.bottom }, { x: r.left, y: r.bottom }];
    let best = Infinity;
    for (let i = 0; i < 4; i++) {
      best = Math.min(best, segSegDist(a, b, c[i], c[(i + 1) % 4]));
      if (best === 0) return 0;
    }
    return best;
  };

  /**
   * Distance from a sampled polyline to a rect, capped at `cap` (default 400px) so a
   * far-away edge costs one bbox comparison per sample instead of four segment solves.
   * The cap is a READOUT bound, never a verdict: any distance below it is exact.
   */
  const polyRectDist = (pts, r, cap) => {
    let best = cap === undefined ? 400 : cap;
    for (let i = 1; i < pts.length; i++) {
      const a = pts[i - 1], b = pts[i];
      if (Math.max(a.x, b.x) < r.left - best || Math.min(a.x, b.x) > r.right + best ||
          Math.max(a.y, b.y) < r.top - best || Math.min(a.y, b.y) > r.bottom + best) continue;
      best = Math.min(best, segRectDist(a, b, r));
      if (best === 0) return 0;
    }
    return best;
  };

  /**
   * `{halfPx, pts}` -- half the painted stroke width in SCREEN px, and the path sampled in
   * screen space. Handles polylines and curves with one instrument: the sampler follows
   * whatever the path does, and the spacing (~3 user units, 24..600 samples) is finer than
   * any tolerance these gates use. null when the path is unpainted or has no length.
   */
  const paintedBand = (path) => {
    const cs = getComputedStyle(path);
    if (!cs.stroke || cs.stroke === "none") return null;
    const ctm = path.getScreenCTM ? path.getScreenCTM() : null;
    if (!ctm) return null;
    let length = 0;
    try { length = path.getTotalLength(); } catch { return null; }
    if (!length) return null;
    const scale = (Math.hypot(ctm.a, ctm.b) + Math.hypot(ctm.c, ctm.d)) / 2;
    const width = parseFloat(cs.strokeWidth) || 0;
    // non-scaling-stroke is a constant SCREEN width -- multiplying it by the camera scale
    // would invent paint the page never draws.
    const nonScaling = (cs.vectorEffect || path.getAttribute("vector-effect")) === "non-scaling-stroke";
    const n = Math.max(24, Math.min(600, Math.ceil(length / 3)));
    const pts = [];
    for (let i = 0; i <= n; i++)
      pts.push(path.getPointAtLength((length * i) / n).matrixTransform(ctm));
    return { halfPx: (nonScaling ? width : width * scale) / 2, pts };
  };

  return { visible, inView, boxOf, overlapPx, segRectDist, polyRectDist, paintedBand };
}

export const GEOM_SOURCE = ddGeomFactory.toString();

/** Hang `__ddGeom` on the page's window. Call once, after `document.fonts.ready`. */
export async function installGeometry(page) {
  await page.evaluate((src) => {
    window.__ddGeom = new Function(`return (${src})`)()();
  }, GEOM_SOURCE);
}
