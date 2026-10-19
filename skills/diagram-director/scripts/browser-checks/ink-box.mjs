// The ONE ink measurement the render-side gates share.
//
// Pre-delivery item 12 -- "measure ink, not the font box". `getBBox()` and
// `getBoundingClientRect()` on an SVG `<text>` return the FACE's layout box: full ascent
// plus full descent vertically, advance width including side bearings horizontally. That
// box is larger than the pixels the glyphs actually put on screen, so a gate measuring it
// reports contacts a screenshot shows as clear gaps. `verify-glyph-label-gap.mjs` read
// `gap 0.9px` on a pair that is visibly clear at 4x for exactly this reason.
//
// `verify-hold-geometry.mjs` already did it honestly, with the measurement inlined in its
// own page callback. It lives here now so every gate that needs ink gets the SAME numbers
// instead of a second copy free to drift -- the failure mode `act_dom_scan.py`'s header
// names for the shape discriminator, one directory over.
//
// It runs IN THE PAGE. `installInk(page)` serialises the function below onto
// `window.__ddInkBox`; a page callback then calls `window.__ddInkBox(el, ctx)` with a 2D
// canvas context of its own. The result is in SCREEN px, so it composes with
// `getBoundingClientRect()` readings taken at the same instant.
//
// It returns **null**, never a guess, when the element cannot report a real baseline (not
// an SVG text, an empty string, no font size, no CTM). Every caller must then fall back to
// the client rect AND SAY SO, because a fallback that is silent is a font-box reading
// wearing an ink reading's name.

/**
 * Screen-space ink bounds of one text element. Runs in the page; no closures.
 *
 * Vertical: canvas `measureText().actualBoundingBoxAscent/Descent` at the text's own
 * computed font, anchored on the true baseline (`getStartPositionOfChar(0)` through
 * `getScreenCTM()`), scaled by the CTM's vertical scale at this instant.
 * Horizontal: the same measurement's `actualBoundingBoxLeft/Right`, anchored on the same
 * start position -- which already accounts for `text-anchor`, so an anchored run is
 * measured where it paints rather than where its box begins.
 */
function ddInkBox(el, ctx) {
  const cs = getComputedStyle(el);
  const size = parseFloat(cs.fontSize) || 0;
  if (!size) return null;
  const text = el.textContent;
  if (!text || !text.trim()) return null;
  ctx.font = `${cs.fontStyle} ${cs.fontWeight} ${size}px ${cs.fontFamily}`;
  const m = ctx.measureText(text);
  const ctm = el.getScreenCTM ? el.getScreenCTM() : null;
  if (!ctm) return null;
  const sx = Math.hypot(ctm.a, ctm.c);
  const sy = Math.hypot(ctm.b, ctm.d);
  let start;
  try { start = el.getStartPositionOfChar(0).matrixTransform(ctm); }
  catch { return null; }
  return {
    top: start.y - m.actualBoundingBoxAscent * sy,
    bottom: start.y + m.actualBoundingBoxDescent * sy,
    left: start.x - m.actualBoundingBoxLeft * sx,
    right: start.x + m.actualBoundingBoxRight * sx,
  };
}

export const INK_SOURCE = ddInkBox.toString();

/** Hang `__ddInkBox` on the page's window. Call once, after `document.fonts.ready`. */
export async function installInk(page) {
  await page.evaluate((src) => {
    window.__ddInkBox = new Function(`return (${src})`)();
  }, INK_SOURCE);
}
