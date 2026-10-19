// Glyph art vs its OWN node's text: the containment sweeps check text-vs-shape
// and text-vs-foreign-node, so a badge glyph overlapping its own label passes
// every gate (user-caught: payment card touching "stripe", person touching
// "auth0"). Measures each node__icon group / small node__detail element
// against each text in the same node; flags intersections and gaps < MIN_GAP.
//
// MEASURED ON INK, not the font box (pre-delivery item 12). The glyph is geometry -- its
// client rect IS what it paints -- but a text's client rect is the FACE's layout box, full
// ascent over full descent, and a label set in a tall-ascent face carries empty rows of it
// above the capitals. Measuring that box against a badge reported `gap 0.9px` on a pair a
// reviewer can see is clear at 4x. The vertical bounds now come from canvas
// `measureText().actualBoundingBoxAscent/Descent` anchored on the real baseline, and the
// horizontal from the same measurement's side bearings -- the shared helper in
// `ink-box.mjs`, extracted from `verify-hold-geometry.mjs` so the two cannot drift apart.
// A text the helper cannot anchor (not an SVG text, no CTM) falls back to the client rect
// and the run SAYS how many pairs were read that way; a silent fallback is a font-box
// reading wearing an ink reading's name.
//
// The change can only widen a measured gap, never narrow one, so nothing that passes on
// the font box can start failing on ink -- which is why this is the same script rather
// than a second one: two instruments disagreeing about the same pair is how a gate rots.
//
//   node verify-glyph-label-gap.mjs <url> [--min-gap N]      (serve over HTTP)
import puppeteer from "./resolve-puppeteer.mjs";
import { installInk } from "./ink-box.mjs";

const argv = process.argv.slice(2);
const url = argv.find(a => !a.startsWith("--"));
if (!url) { console.error("usage: verify-glyph-label-gap.mjs <url> [--min-gap N]"); process.exit(2); }
const flag = argv.indexOf("--min-gap");
const MIN_GAP = flag >= 0 ? Number(argv[flag + 1]) : 3;

const b = await puppeteer.launch({ headless: true });
const p = await b.newPage();
await p.goto(url, { waitUntil: "networkidle2" });
await p.evaluate(() => document.fonts.ready);
await new Promise(r => setTimeout(r, 500));
await installInk(p);
const out = await p.evaluate((MIN_GAP) => {
  const res = []; let checked = 0, fellBack = 0, nodesWithGlyphs = 0;
  const ctx = document.createElement("canvas").getContext("2d");
  for (const node of document.querySelectorAll("g.node")) {
    const glyphs = [];
    for (const g of node.querySelectorAll(".node__icon")) glyphs.push(g);
    for (const d of node.querySelectorAll(":scope > .node__body > .node__detail")) {
      // standalone details: skip full-size frames (dashed boundary, monolith wall)
      const bb = d.getBBox();
      if (bb.width < 60 && bb.height < 60) glyphs.push(d);
    }
    if (glyphs.length) nodesWithGlyphs++;
    const label = node.querySelector(".node__label")?.textContent.trim() ?? "?";
    for (const gl of glyphs) {
      const gb = gl.getBoundingClientRect();
      for (const t of node.querySelectorAll("text")) {
        // Text the glyph itself renders (the packet-bits "101" chip) is part of
        // the art, not a label it can collide with. Added 2026-08-26.
        if (gl.contains(t)) continue;
        if (!t.textContent.trim()) continue;
        const ink = window.__ddInkBox(t, ctx);
        if (!ink) fellBack++;
        const tb = ink || t.getBoundingClientRect();
        checked++;
        const gapX = Math.max(tb.left - gb.right, gb.left - tb.right);
        const gapY = Math.max(tb.top - gb.bottom, gb.top - tb.bottom);
        const gap = Math.max(gapX, gapY);   // separated if EITHER axis has a gap
        if (gap < MIN_GAP)
          res.push({ node: label, text: t.textContent.trim().slice(0, 24),
                     gap: Math.round(gap * 10) / 10, on: ink ? "ink" : "box" });
      }
    }
  }
  return { res, checked, fellBack, nodesWithGlyphs };
}, MIN_GAP);
await b.close();
if (!out.checked) { console.error("FAIL: zero glyph/text pairs found -- selector drift"); process.exit(1); }
console.log(out.res.length
  ? "GLYPH-TEXT VIOLATIONS:"
  : `all glyphs keep >=${MIN_GAP}px of INK from their node's text (${out.checked} pairs `
    + `across ${out.nodesWithGlyphs} glyph-bearing node(s))`);
out.res.forEach(v => console.log(`  [${v.node}] glyph vs "${v.text}": gap ${v.gap}px (on ${v.on})`));
// ##DIAG: one measured defect per line; the runner owns severity (README -> "The ##DIAG line").
out.res.forEach(v => console.log("##DIAG " + JSON.stringify({
  code: "glyph/label-gap", subject: { node: v.node, text: v.text },
  evidence: { gap_px: v.gap, min_gap_px: MIN_GAP, measured_on: v.on } })));
if (out.fellBack)
  console.log(`N/A: ${out.fellBack} pair(s) measured on the client rect, not ink -- the `
              + "text reports no anchorable baseline (not an SVG text, or no CTM)");
process.exit(out.res.length ? 1 : 0);
