// THE CONTACT SHEET -- one image showing the cut at every hold it declares.
//
// It is not a check and it never exits 1 on the diagram's account. It exists because
// three of the delivery gates cannot be measured and must be LOOKED AT:
//   curves        -- the route a curved edge takes around what it passes; the geometry
//                    sweep skips curves on purpose (verify-hold-geometry.mjs)
//   style fidelity-- whether the presentation is the style's idiom or a re-derivation
//                    from memory (pre-delivery-checklist item 16, user-caught in one glance)
//   semantic truth-- whether each label is a true claim about the system (item 11)
// A green verify-all with no one having looked at the sheet is an unreviewed cut.
//
// HOW THE FRAMES ARE MADE: every animation is paused and seeked to the hold's window
// midpoint, then the hold's transform is pinned on `.camera` -- see hold-frames.mjs for
// the honest limits of that reproduction. This is a real seek of the master timeline,
// NOT an animation-delay rewrite.
//
// COMPOSITE: `sharp` is resolved the same portable way puppeteer is -- PUPPETEER_RESOLVE_DIR
// first, then a plain import -- and is OPTIONAL. Without it the frames are still written
// as individual PNGs next to an index.html that lays them out, and the script SAYS so.
//
//   node contact-sheet.mjs <url> [--manifest <path>] [--out <dir>] [--cols N] [--tile PX]
import { createRequire } from "node:module";
import { mkdirSync, writeFileSync } from "node:fs";
import { basename, join } from "node:path";
import puppeteer from "./resolve-puppeteer.mjs";
import { readManifest, cameraHolds, masterMs, holdMidpointMs, freezeAt, pinCamera, parseArgs }
  from "./hold-frames.mjs";

const USAGE = "usage: contact-sheet.mjs <url> [--manifest <path>] [--out <dir>] [--cols N] [--tile PX]";
const { url, manifest: manifestPath, out, extra } = parseArgs(process.argv.slice(2), USAGE);
const OUT_DIR = out || ".";
const TILE_W = Number(extra.tile ?? 640);

async function resolveSharp() {
  const dir = process.env.PUPPETEER_RESOLVE_DIR;
  if (dir) { try { return createRequire(dir)("sharp"); } catch { /* fall through */ } }
  try { return (await import("sharp")).default; } catch { return null; }
}

const manifest = readManifest(manifestPath);
const holds = cameraHolds(manifest);
if (!holds.length) {
  console.error(`FAIL: ${manifestPath} declares no camera holds -- nothing to sheet`);
  process.exit(1);
}
const vb = (manifest.target || {}).viewbox || [0, 0, 1920, 1080];
const [vw, vh] = [Math.round(vb[2]), Math.round(vb[3])];
const master = masterMs(manifest);
const stem = basename(manifestPath).replace(/\.manifest\.json$/i, "");
mkdirSync(OUT_DIR, { recursive: true });

const browser = await puppeteer.launch({ headless: true });
const page = await browser.newPage();
await page.setViewport({ width: vw, height: vh });
await page.goto(url, { waitUntil: "networkidle2" });
await page.evaluate(() => document.fonts.ready);
await new Promise(r => setTimeout(r, 600));

// WHICH HOLDS GET A FRAME. Camera holds always. ACT holds too, once per window --
// and that is not padding: a camera hold that spans several acts has a window
// midpoint that can land squarely on an act CROSSFADE, and the frame then shows two
// acts ghosted through each other. Observed on the progressive golden, whose `a3` and
// `a4-recap` camera windows both straddle an act seam. Acts are the only kind that own
// the whole canvas in turn, so they are the only ones that need their own sample;
// state, spotlight and traffic overlays ride inside a camera hold and are visible in
// its frame already. `--holds camera` restricts to the camera set.
const actHolds = String(extra.holds || "") === "camera" ? []
  : (manifest.holds || []).filter(h => h.kind === "act");
const shots = holds.map(h => ({ hold: h, window: h.window, pin: true, kind: "camera" }));
for (const h of actHolds)
  for (const [i, w] of (h.windows || []).entries())
    shots.push({ hold: h, window: w, pin: false, kind: "act",
                 id: `${(h.element || "act").replace(/^\./, "")}${i ? `-r${i}` : ""}` });

const frames = [];
for (const shot of shots) {
  const t = holdMidpointMs({ window: shot.window }, master);
  await freezeAt(page, t);
  // An act frame is NOT pinned: the beats animation is the authority on where the
  // camera is at that instant, and that is what the reviewer needs to judge.
  if (shot.pin) await pinCamera(page, shot.hold);
  else await page.evaluate(() => document.querySelector(".camera")?.style.removeProperty("transform"));
  const id = shot.id || shot.hold.id || `hold-${frames.length + 1}`;
  const file = join(OUT_DIR, `${stem}--${id}.png`);
  await page.screenshot({ path: file });
  const [a, b] = shot.window || [0, 100];
  const tail = shot.pin ? `k=${shot.hold.k}  gate:${shot.hold.gate || "read"}` : "act (camera as animated)";
  frames.push({ id, file, label: `${id}  ${a}-${b}%  t=${Math.round(t)}ms  ${tail}` });
  console.log(`  frame ${id.padEnd(12)} ${file}`);
}
await browser.close();

const cols = Number(extra.cols ?? Math.min(3, frames.length));
const rows = Math.ceil(frames.length / cols);
const tileH = Math.round((TILE_W * vh) / vw);
const BAND = 26;
const sharp = await resolveSharp();

if (!sharp) {
  const html = `<title>${stem} contact sheet</title>
<style>body{background:#111;color:#eee;font:14px system-ui;margin:24px}
figure{display:inline-block;margin:0 12px 18px 0;width:${TILE_W}px}
img{width:100%;border:1px solid #444}figcaption{padding:4px 0;font:12px ui-monospace,monospace}</style>
<h1>${stem} — ${frames.length} holds</h1>
<p>sharp not resolvable, so these are individual frames, not one composited image.</p>
${frames.map(f => `<figure><img src="${basename(f.file)}"><figcaption>${f.label}</figcaption></figure>`).join("\n")}`;
  const index = join(OUT_DIR, `${stem}--contact-sheet.html`);
  writeFileSync(index, html, "utf8");
  console.log(`\nFALLBACK: sharp is not resolvable, so no single composited image was made.`);
  console.log(`  ${frames.length} PNG(s) + ${index} -- open the index over HTTP and review it.`);
  process.exit(0);
}

const W = cols * TILE_W, H = rows * (tileH + BAND);
const esc = (s) => s.replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
const composite = [];
for (const [i, f] of frames.entries()) {
  const left = (i % cols) * TILE_W, top = Math.floor(i / cols) * (tileH + BAND);
  composite.push({ input: await sharp(f.file).resize(TILE_W, tileH, { fit: "fill" }).toBuffer(),
                   left, top });
  const band = `<svg width="${TILE_W}" height="${BAND}" xmlns="http://www.w3.org/2000/svg">
    <rect width="100%" height="100%" fill="#15181d"/>
    <text x="8" y="18" font-family="monospace" font-size="13" fill="#d7dce3">${esc(f.label)}</text></svg>`;
  composite.push({ input: Buffer.from(band), left, top: top + tileH });
}
const sheet = join(OUT_DIR, `${stem}--contact-sheet.png`);
await sharp({ create: { width: W, height: H, channels: 4,
                        background: { r: 8, g: 10, b: 13, alpha: 1 } } })
  .composite(composite).png().toFile(sheet);
console.log(`\ncontact sheet: ${sheet}  (${cols}x${rows} grid, ${frames.length} holds, ${W}x${H})`);
console.log("MANDATORY VISUAL REVIEW -- open it and check curves, style fidelity, semantic truth "
            + "(pre-delivery-checklist items 11, 16, and the curve N/A in verify-hold-geometry).");
process.exit(0);
