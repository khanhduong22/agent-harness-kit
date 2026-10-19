// Shared machinery for the checks that measure a cut AT ITS DECLARED HOLDS
// (verify-hold-geometry.mjs, contact-sheet.mjs). Same lib pattern as
// resolve-puppeteer.mjs: a plain .mjs module, no package, no dependency.
//
// HOW A HOLD IS REPRODUCED -- stated plainly, because a screenshot that lies about
// which instant it shows is worse than no screenshot:
//
// 1. TIME. Every animation on the page is `pause()`d and its `currentTime` set to the
//    hold's window MIDPOINT in ms (`(a+b)/2 % of master`). The master and the short
//    ambient loops all take the same absolute time: an infinite-iteration animation
//    computes its own iteration from `currentTime`, so a 2400ms dash loop seeked to
//    18000ms lands in the phase it would really be in at 18s. Negative `animation-delay`
//    is part of the effect timing, so it is honoured too. This is a genuine seek, NOT
//    the animation-delay trick -- nothing is re-declared and no keyframe is re-authored.
// 2. CAMERA. The hold's `k/tx/ty` are then written onto the `.camera` group as an
//    `!important` inline transform. Important declarations outrank animations in the
//    cascade, so this wins over the `beats` keyframes. It is belt-and-braces: at the
//    window midpoint the beats animation is ALREADY at this transform, and `pinCamera`
//    returns the computed transform it replaced so a drift between the manifest and the
//    keyframes is visible rather than silently overwritten.
//
// What this does NOT reproduce: anything driven by JS rAF (the skill ships css-only
// cuts) and any `steps()`/discrete timing whose sub-frame position differs between a
// seek and real playback.
import { readFileSync } from "node:fs";

export function readManifest(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

export function cameraHolds(manifest) {
  return (manifest.holds || []).filter(h => h.kind === "camera");
}

export function masterMs(manifest) {
  return Number((manifest.target || {}).master_ms) || 0;
}

export function holdMidpointMs(hold, master) {
  const [a, b] = hold.window || [0, 100];
  return ((Number(a) + Number(b)) / 2 / 100) * master;
}

/** Pause every animation and seek the whole page to `timeMs` of the master. */
export async function freezeAt(page, timeMs) {
  return page.evaluate((t) => {
    let n = 0;
    for (const a of document.getAnimations()) {
      try { a.pause(); a.currentTime = t; n++; } catch { /* finished/idle */ }
    }
    return n;
  }, timeMs);
}

/** Write the hold's transform onto `.camera`; returns the computed one it replaced. */
export async function pinCamera(page, hold) {
  const before = await page.evaluate(({ k, tx, ty }) => {
    const cam = document.querySelector(".camera");
    if (!cam) return null;
    // Clear a PREVIOUS pin first, or `was` reports the last hold's transform instead
    // of the keyframes' own -- which made the drift readout silently one hold behind.
    cam.style.removeProperty("transform");
    void cam.getBoundingClientRect();
    const was = getComputedStyle(cam).transform;
    cam.style.setProperty("transform", `translate(${tx}px, ${ty}px) scale(${k})`, "important");
    cam.style.setProperty("transform-origin", "0 0", "important");
    return was;
  }, { k: Number(hold.k), tx: Number(hold.tx), ty: Number(hold.ty) });
  await new Promise(r => setTimeout(r, 60));
  return before;
}

/** Parse `<url> [--manifest p]` the same way in every hold-aware check. */
export function parseArgs(argv, usage) {
  let url = null, manifest = null, out = null, extra = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--manifest") manifest = argv[++i];
    else if (a === "--out") out = argv[++i];
    else if (a.startsWith("--")) extra[a.replace(/^--/, "")] = argv[i + 1]?.startsWith("--") === false ? argv[++i] : true;
    else if (!url) url = a;
  }
  if (!url) { console.error(usage); process.exit(2); }
  if (!manifest) {
    // Default: <stem>.manifest.json in the CWD. The url's path is server-relative and
    // says nothing about where the file lives, so this is a convenience for running
    // from the diagram's own directory -- verify_all.py always passes --manifest.
    const stem = decodeURIComponent(new URL(url).pathname).split("/").pop()
      .replace(/\.html?$/i, "");
    manifest = `${stem}.manifest.json`;
  }
  return { url, manifest, out, extra };
}
