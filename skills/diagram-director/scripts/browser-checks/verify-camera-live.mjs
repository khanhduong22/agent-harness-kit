// THE DEAD-CAMERA GATE: the camera the manifest describes must be the camera
// the page actually runs.
//
// WHY IT HAS TO EXIST. Reported on the process golden during the REV 6 pacing
// re-bake: a comment closed `*/` one paragraph early, the orphaned prose landed
// in the stylesheet and killed the `@keyframes beats` block, the page had NO
// CAMERA MOTION AT ALL -- and `verify_all.py` printed 20 PASS. Every gate looked
// somewhere else:
//
//   stage D  re-solves the holds FROM THE MANIFEST -- it never opens the page;
//   stage E  PINS the hold's transform onto `.camera` as an !important inline
//            style before it measures, so it measures the pose it just wrote;
//   regression  parses the HTML with a regex, and the dead block was still in
//            the file, just no longer parsed as CSS by the browser.
//
// The only signal was `pinCamera`'s `was` field printing `was none` instead of
// `was matrix(...)`, exactly as hold-frames.mjs documents -- a printed word, not
// a gate. This is that word turned into a gate.
//
// THE RULE (references/camera-beat.md -> "The manifest describes the camera the
// page runs"). At each declared camera hold, seek the page to that hold's window
// midpoint and read the COMPUTED transform of `.camera` BEFORE anything is
// pinned. It must be a real matrix -- not `none` -- and it must be the k/tx/ty
// the manifest declares for that hold, within tolerance.
//
// TWO DISTINCT INSTANTS, minimum. One reading cannot tell a live animation from
// a static inline transform that happens to match: the process golden's own
// reduced-motion rule parks `.camera` at b1's pose with `!important`. So the
// check requires the cut to declare at least two holds with DIFFERENT poses and
// verifies BOTH -- a camera stuck at one pose then fails at every other hold.
//
// `none` IS THE IDENTITY, not an error, and reading it any other way would fail
// three of the four frozen goldens: their overview and recap holds are written
// `transform:none` inside `beats`, exactly as tests/run_golden_regression.py's
// `beat_transforms()` reads them. This costs nothing, because the two-distinct-
// pose requirement guarantees at least one hold whose declared pose is NOT the
// identity -- and a dead camera reads `none` THERE too, which is the failure.
//
// TOLERANCE. The hold window is a plateau in `beats` (both of its stops carry
// the same transform), so the midpoint reading is exact bar float noise: 1e-4
// on k and 0.05 px on tx/ty, measured across all four frozen goldens. This is a
// rounding allowance, not slack -- a stale or missing camera is off by whole
// pixels and whole tenths of k.
//
// House rule (diagram-director/scripts/browser-checks/README.md): a check that finds nothing
// FAILS. No `.camera`, no holds, or a single declared pose is not a clean cut.
//
//   node verify-camera-live.mjs <url> [--manifest <path>] [--camera .camera]
//        [--tol-k 0.0001] [--tol-px 0.05]
import puppeteer from "./resolve-puppeteer.mjs";
import { readManifest, cameraHolds, masterMs, holdMidpointMs, parseArgs }
  from "./hold-frames.mjs";

const USAGE = "usage: verify-camera-live.mjs <url> [--manifest <path>] [--camera <sel>] "
  + "[--tol-k N] [--tol-px N]";
const { url, manifest: manifestPath, extra } = parseArgs(process.argv.slice(2), USAGE);
const CAM_SEL = typeof extra.camera === "string" ? extra.camera : ".camera";
const TOL_K = Number(extra["tol-k"] ?? 1e-4);
const TOL_PX = Number(extra["tol-px"] ?? 0.05);

const manifest = readManifest(manifestPath);
const holds = cameraHolds(manifest);
const master = masterMs(manifest);
if (!holds.length) {
  console.error(`FAIL: ${manifestPath} declares no camera holds -- nothing to evaluate at`);
  process.exit(1);
}
const poses = new Set(holds.map(h => `${h.k}|${h.tx}|${h.ty}`));
if (poses.size < 2) {
  console.error(`FAIL: ${manifestPath} declares ${holds.length} camera hold(s) but only `
    + `${poses.size} distinct pose -- one pose cannot tell a live camera from a parked one`);
  process.exit(1);
}

const browser = await puppeteer.launch({ headless: true });
const page = await browser.newPage();
const vb = (manifest.target || {}).viewbox || [0, 0, 1920, 1080];
await page.setViewport({ width: Math.round(vb[2]), height: Math.round(vb[3]) });
await page.goto(url, { waitUntil: "networkidle2" });
await page.evaluate(() => document.fonts.ready);
await new Promise(r => setTimeout(r, 300));

const violations = [];
let read = 0;

for (const hold of holds) {
  const id = hold.id || "(unnamed)";
  const at = holdMidpointMs(hold, master);
  // Deliberately NOT hold-frames' pinCamera: this must see the page's own camera,
  // so it seeks time and reads, and writes nothing.
  const got = await page.evaluate((t, sel) => {
    for (const a of document.getAnimations()) {
      try { a.pause(); a.currentTime = t; } catch { /* finished/idle */ }
    }
    const cam = document.querySelector(sel);
    if (!cam) return { missing: true };
    void cam.getBoundingClientRect();
    return { transform: getComputedStyle(cam).transform,
             animations: cam.getAnimations().map(a => a.animationName
               || (a.effect && a.effect.target && "css") || "?") };
  }, at, CAM_SEL);

  if (got.missing) {
    console.error(`FAIL: no element matches "${CAM_SEL}" -- there is no camera to read`);
    await browser.close();
    process.exit(1);
  }
  const want = { k: Number(hold.k), tx: Number(hold.tx), ty: Number(hold.ty) };
  const raw = (got.transform || "").trim();
  const m = /^matrix\(([^)]*)\)$/.exec(raw);
  if (!m && raw !== "none") {
    violations.push(`${id}: computed transform is "${raw}" at ${at.toFixed(0)}ms -- not a `
      + `2D matrix this check can read; manifest says `
      + `translate(${want.tx}px,${want.ty}px) scale(${want.k})`);
    continue;
  }
  const [a, b, c, d, e, f] = m ? m[1].split(",").map(Number) : [1, 0, 0, 1, 0, 0];
  read++;
  const off = [];
  if (Math.abs(a - want.k) > TOL_K || Math.abs(d - want.k) > TOL_K)
    off.push(`k ${a}/${d} != ${want.k}`);
  if (Math.abs(b) > TOL_K || Math.abs(c) > TOL_K)
    off.push(`camera is skewed/rotated (b=${b}, c=${c})`);
  if (Math.abs(e - want.tx) > TOL_PX) off.push(`tx ${e} != ${want.tx}`);
  if (Math.abs(f - want.ty) > TOL_PX) off.push(`ty ${f} != ${want.ty}`);
  if (off.length)
    violations.push(`${id}: the LIVE camera at ${at.toFixed(0)}ms is "${raw}" -- `
      + off.join("; ")
      + (raw === "none"
        ? " -- `none` is the identity, i.e. the camera animation is missing or inert "
          + "(a CSS syntax error anywhere before @keyframes beats kills the whole block)"
        : " (manifest and keyframes disagree: one of them was retimed and the other "
          + "was not)"));
  else
    console.log(`  hold ${id.padEnd(10)} ${at.toFixed(0).padStart(6)}ms  live `
      + `k ${a} tx ${e} ty ${f}  == manifest`);
}
await browser.close();

if (!read && !violations.length) {
  console.error("FAIL: zero camera readings taken -- wrong url or broken page");
  process.exit(1);
}
if (violations.length) {
  console.log("DEAD/DRIFTED CAMERA:");
  violations.forEach(v => console.log(`  ${v}`));
  console.log(`\n${violations.length} violation(s) over ${holds.length} hold(s). Stage D and `
    + "stage E both trust the manifest; this is the only gate that asks the PAGE.");
  process.exit(1);
}
console.log(`live camera matches the manifest at all ${holds.length} hold(s), `
  + `${poses.size} distinct poses (read before pinning, tol k ${TOL_K} / ${TOL_PX}px)`);
process.exit(0);
