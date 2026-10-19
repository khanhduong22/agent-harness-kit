// A caption card's rect is BAKED from the caption text's measured bbox, which
// means it is a function of the typeface. Any fork that changes --font-label
// invalidates every box: neon-dark's mono caption ran ~13% wider than the
// Inter the boxes were baked against and spilled its first word onto the dark
// canvas, unreadable. Re-bake per fork; never hand-nudge.
//
//   node rebake-caption-boxes.mjs [--base <url>] <file.html> [...]   (writes in place)
//
// The file is measured through the SERVER, not from disk: file:// gives the
// page a different font/CDN reality than the one it ships into. --base is the
// http root the files are served from; `SERVE_BASE` in the environment sets the
// same thing, and :8931 is only the house convention -- it is a PORT NUMBER, not
// a promise, and on a machine where something else already holds it the default
// silently points at a stranger's server. Whichever port you actually served on,
// pass it: `--base http://localhost:<port>` or `export SERVE_BASE=...`.
import { readFileSync, writeFileSync } from "node:fs";
import { basename } from "node:path";
import puppeteer from "./resolve-puppeteer.mjs";

const argv = process.argv.slice(2);
let base = process.env.SERVE_BASE || "http://localhost:8931";
const files = [];
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === "--base") { base = argv[++i]; continue; }
  files.push(argv[i]);
}
if (!files.length) { console.error("usage: rebake-caption-boxes.mjs [--base <url>] <file.html> [...]"); process.exit(2); }
base = base.replace(/\/$/, "");

const PAD_X = 14, PAD_Y = 8;
const b = await puppeteer.launch({ headless: true });

let bad = 0;
for (const file of files) {
  const p = await b.newPage();
  const url = `${base}/${basename(file)}`;
  try {
    await p.goto(url, { waitUntil: "networkidle2" });
  } catch (err) {
    // This rewrites files in place off what it measures, so a wrong root is not
    // an inconvenience, it is a corrupted cut. Name the root and stop.
    console.error(`FAIL: cannot load ${url} -- ${err.message}`);
    console.error(`  the base is ${process.env.SERVE_BASE ? "SERVE_BASE" : "the :8931 default"}; `
                  + "serve the file's own directory and pass that root "
                  + "(--base http://localhost:<port>, or export SERVE_BASE)");
    await b.close();
    process.exit(2);
  }
  await p.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 600));
  const boxes = await p.evaluate(({ PAD_X, PAD_Y }) => {
    const out = {};
    for (const g of document.querySelectorAll(".beat-caption")) {
      const key = g.querySelector("rect").getAttribute("data-cap");
      const bb = g.querySelector("text").getBBox();
      out[key] = {
        x: +(bb.x - PAD_X).toFixed(1), y: +(bb.y - PAD_Y).toFixed(1),
        w: +(bb.width + 2 * PAD_X).toFixed(1), h: +(bb.height + 2 * PAD_Y).toFixed(1),
      };
    }
    return out;
  }, { PAD_X, PAD_Y });
  await p.close();

  let src = readFileSync(file, "utf8"), changed = 0;
  // The id is ANY [a-z0-9-] token, not `bN`: recap holds are r1..rN, act holds a1..aN,
  // and a pattern that only knew `b\d` re-baked 0 boxes and hard-failed on a cut whose
  // captions were named anything else. Whitespace is likewise tolerant (\s+ between
  // attributes, \s* before the self-close) so a re-indented or re-emitted file still
  // matches; rx/ry are captured verbatim and written back untouched.
  src = src.replace(
    /<rect\s+class="caption-box"\s+x="[-\d.]+"\s+y="[-\d.]+"\s+width="[\d.]+"\s+height="[\d.]+"((?:\s+(?:rx|ry)="[\d.]+")*)\s+data-cap="([a-z0-9-]+)"\s*\/>/g,
    (m, rxry, key) => {
      const bx = boxes[key];
      if (!bx) return m;
      changed++;
      return `<rect class="caption-box" x="${bx.x}" y="${bx.y}" width="${bx.w}" height="${bx.h}"${rxry} data-cap="${key}" />`;
    });
  writeFileSync(file, src);
  console.log(`${basename(file)}: re-baked ${changed} caption boxes`);
  // A rewriter that matches nothing while captions exist is a silent no-op --
  // same trap as a verifier passing on an empty element set. Hard-fail it.
  if (changed === 0 && Object.keys(boxes).length > 0) {
    console.error(`FAIL: ${Object.keys(boxes).length} caption(s) found in DOM but 0 rects matched the bake pattern -- check attribute order`);
    bad++;
  }
}
await b.close();
process.exit(bad ? 1 : 0);
