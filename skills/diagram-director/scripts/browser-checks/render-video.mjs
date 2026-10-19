// Deterministic video export for a finished cut: frame-step every animation via
// currentTime (no live capture, no dropped frames), encode with ffmpeg, then
// VERIFY the result by decoding a frame back out of the finished MP4.
//
// Harvested from the scratchpad script that rendered the first process golden
// (2026-08-27), with the two lessons of that day built in:
//   1. capture and encode are ONE command here -- the day they were separate,
//      a re-render shipped stale footage because only the capture ran;
//   2. the tool never reports success from its own logs -- it re-opens the MP4
//      it wrote and checks a decoded frame differs from black/empty.
//
// Usage:
//   node diagram-director/scripts/browser-checks/render-video.mjs <url-or-file> <out.mp4>
//        [--fps 30] [--master 38400] [--width 1920] [--height 1080]
//        [--manifest cut.manifest.json] [--start-ms N] [--end-ms N]
//        [--profile gpu-native-1] [--encoder libx264|videotoolbox] [--silent-audio]
//
// DELIVERY FLAGS (all opt-in; with none of them the command below is byte-for-byte
// the export it always was). `--profile gpu-native-1` launches with the launch_args
// of `episode-director/data/render-profiles/gpu-native-1.json` (ANGLE Metal), then
// measures GPU evidence over CDP BEFORE a single frame is captured and ABORTS with
// exit 1 if the active GL renderer is software or compositing/rasterization is not
// enabled -- that profile's rule is "missing evidence or fallback aborts the export",
// so a software fallback must never be photographed and called a GPU render. The
// measured evidence is printed and written next to the MP4 as `<out>.render.json`.
// The profile names the full Chrome for Testing build, so point
// PUPPETEER_EXECUTABLE_PATH at that binary rather than at chrome-headless-shell;
// a build mismatch is reported, not silently accepted. `--encoder videotoolbox`
// encodes with Apple's hardware H.264 at High/yuv420p and constant quality 80,
// the lowest rung measured to MATCH the libx264 -crf 18 default on flat vector art
// (render-video-options.mjs carries the measurement), keeping `libx264 -crf 18` the
// default -- videotoolbox buys wall-clock, not bytes: it writes roughly twice the
// file for the same picture. `--silent-audio` muxes a stereo 48 kHz silent AAC
// track over the COPIED video stream, because the skill's delivery rule wants an
// audio track present (some uploaders mishandle silent files); the post-verify then
// also asserts that the audio stream really is in the file it wrote. `--start-ms N`
// is the head half of the seam handling (HEAD-SEAM RULE below): the first captured
// instant, symmetric with --end-ms, defaulting to 0.
//
// LINEAR-ENDING RULE: a looping cut's final moments are the next lap's WIND-UP
// (state windows like [98.7%,100%] re-dim the stage so t=master == t=0 for the
// web loop seam). Correct on the web, wrong in a linear MP4 -- the video reads
// "about to replay" instead of "finished". So when --manifest is given, the
// render TRIMS at the earliest late-window start (any non-camera window that
// touches 100% and starts after 90%), ending on the last clean recap frame.
// --end-ms overrides manually. User-reported defect, 2026-08-27.
//
// HEAD-SEAM RULE: the same loop seam exists at the OTHER end, and the manifest does
// not describe it. A cut whose final act is lit at 0% -- `@keyframes act2 {0%{opacity:1}
// ...}` -- hands the stage over to act 1 across the first beat, so t=0 is the previous
// lap's LAST frame. Correct on the web, wrong in a linear MP4: the video opens on its
// own ending, then dissolves backwards into the opening. The trim rule above cannot
// see this, because the baked manifest records the late window (`[36.6, 100]`) but not
// the zero-length instant at 0%, so there is no 0%-and-100% PAIR to match on. Until
// the manifest records that window, the start is given EXPLICITLY: --start-ms is the
// first captured instant, the frame count and the verified duration are
// (end-ms - start-ms), and the default 0 leaves every existing export byte-identical.
// Measured on jev-decision-agent 2026-09-21: act 2 at full opacity at t=0, blank by
// 600ms, act 1 at full opacity at 1200ms -> --start-ms 1200.
// Requires ffmpeg on PATH. Exit codes: 0 ok, 1 render/encode/verify failure,
// 2 puppeteer unavailable (same contract as the other browser checks).
import puppeteer, { UNVERIFIED_BANNER } from "./resolve-puppeteer.mjs";
import {
  encodeArgs, frameSpan, parseRenderArgs, silentAudioArgs, windupEndMs,
} from "./render-video-options.mjs";
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtempSync, rmSync, statSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, isAbsolute, relative, resolve as resolvePath } from "node:path";
import { fileURLToPath } from "node:url";

if (!puppeteer) { console.error(UNVERIFIED_BANNER); process.exit(2); }

let opts;
try { opts = parseRenderArgs(process.argv.slice(2)); }
catch (err) { console.error(err.message); process.exit(1); }

const { target, outPath, fps: FPS, width: W, height: H, startMs: START, encoder, silentAudio } = opts;

// MASTER: an explicit --master wins; else the manifest's target.master_ms; else
// 38400. The day this order was wrong, a 48s cut shipped missing its last 9.6s
// because the tool's default silently beat the manifest.
const manifest = opts.manifestPath ? JSON.parse(readFileSync(opts.manifestPath, "utf8")) : null;
const MASTER = opts.masterFlag !== null ? opts.masterFlag : (manifest?.target?.master_ms ?? 38400);
let endMs = opts.endMsFlag !== null ? opts.endMsFlag : MASTER;
if (manifest && endMs === MASTER) {
  // WIND-UP, not content: a late window only counts when the SAME element also
  // has a window starting at 0% -- that pair is the loop seam re-arming the
  // opening state. A lone [95,100] window is the finale's own content (the
  // 5tier recap taught us: trimming it beheaded the last recap step).
  const trim = windupEndMs(manifest, MASTER);
  if (trim) {
    endMs = trim.endMs;
    console.log(`linear ending: trimming at ${endMs}ms (seam wind-up starts ${trim.startPct.toFixed(2)}%)`);
  } else {
    console.log(`linear ending: no seam wind-up in the manifest; ending at master ${endMs}ms`);
  }
}
let FRAMES;
try { FRAMES = frameSpan({ startMs: START, endMs, fps: FPS }); }
catch (err) { console.error(err.message); process.exit(1); }
const url = /^https?:|^file:/.test(target)
  ? target
  : "file://" + (isAbsolute(target) ? target : join(process.cwd(), target));

// The source the evidence file names: the local HTML behind the target. An http
// target is served from somewhere, so the manifest's own `target.file` (resolved
// next to the manifest) is the honest source; with neither, the field says why.
function sourceFile() {
  let path = null;
  if (/^file:/.test(target)) path = fileURLToPath(target);
  else if (!/^https?:/.test(target)) path = resolvePath(target);
  else if (opts.manifestPath && manifest?.target?.file) {
    path = resolvePath(dirname(opts.manifestPath), manifest.target.file);
  }
  if (!path) return { source_file: null, source_sha256: null, source_reason: "http target with no manifest target.file" };
  const rel = relative(process.cwd(), path);
  const named = rel.startsWith("..") ? path : rel;
  // A source that cannot be read is UNVERIFIED, not fatal: this runs AFTER a capture
  // and a verified encode, and throwing here threw away a whole good export's evidence
  // the day another generator rewrote the cut mid-run. The MP4 still stands; what the
  // evidence must not do is stay silent about a sha it never took.
  try {
    return { source_file: named,
      source_sha256: createHash("sha256").update(readFileSync(path)).digest("hex") };
  } catch (err) {
    return { source_file: named, source_sha256: null,
      source_reason: `UNVERIFIED -- source could not be read: ${err.message}` };
  }
}

// The profile's own launch args and the profile's own GPU predicate. Both are read
// from episode-director rather than re-derived here: `nativeGpuActive` is the
// sanctioned rule for "is this a native GPU or a software fallback", and a second
// copy of it would drift from the one the render profile's qualification clause
// points at. The import is dynamic and lives inside this branch, so the default
// export path loads nothing from episode-director at all; and it is honest about
// the coupling -- the profile JSON already lives there, so `--profile` could never
// have worked without that directory being present.
let profile = null, launchArgs = [], nativeGpuActive = null;
if (opts.profile) {
  const profileUrl = new URL(`../../../episode-director/data/render-profiles/${opts.profile}.json`, import.meta.url);
  profile = JSON.parse(readFileSync(profileUrl, "utf8"));
  const boundary = await import(new URL("../../../episode-director/scripts/browser-checks/secure-browser-boundary.mjs", import.meta.url));
  ({ nativeGpuActive } = await import(new URL("../../../episode-director/scripts/render-episode-v0.mjs", import.meta.url)));
  launchArgs = boundary.secureLaunchArgs(profile.launch_args);
}

async function measureGpu(browser) {
  const session = await browser.target().createCDPSession();
  try {
    const { gpu } = await session.send("SystemInfo.getInfo");
    return {
      native_active: nativeGpuActive(gpu),
      gl_renderer: gpu.auxAttributes?.glRenderer || null,
      gl_vendor: gpu.auxAttributes?.glVendor || null,
      feature_status: gpu.featureStatus,
    };
  } finally { await session.detach(); }
}

const frameDir = mkdtempSync(join(tmpdir(), "render-video-"));
const browser = await puppeteer.launch(
  profile ? { headless: "new", args: launchArgs } : { headless: "new" });
let gpu = null, browserBuild = null;
try {
  if (profile) {
    browserBuild = await browser.version();
    if (browserBuild !== profile.browser?.build) {
      console.error(`NOTE: host browser ${browserBuild} != profile ${profile.browser?.build}`);
    }
    try { gpu = await measureGpu(browser); }
    catch (err) { gpu = { native_active: false, error: String(err.message) }; }
    console.log(`gpu evidence: ${JSON.stringify(gpu)}`);
    if (!gpu.native_active) {
      await browser.close();
      rmSync(frameDir, { recursive: true, force: true });
      console.error(`ABORT -- profile ${profile.id} requires a native GPU; measured: ${JSON.stringify(gpu)}`);
      process.exit(1);
    }
  }

  const page = await browser.newPage();
  await page.setViewport({ width: W, height: H });
  await page.goto(url, { waitUntil: "networkidle2" });

  // pause everything once; warm-up seek to the deepest-zoom instant first so
  // fonts/layers are rasterized before frame 0 is captured
  const n = await page.evaluate((ms) => {
    const anims = document.getAnimations();
    for (const a of anims) { try { a.pause(); a.currentTime = ms; } catch {} }
    return anims.length;
  }, Math.round(MASTER / 2));
  await new Promise(r => setTimeout(r, 300));
  console.log(`paused ${n} animations; rendering ${FRAMES} frames @ ${FPS}fps (master ${MASTER}ms)`
    + (START ? ` from ${START}ms to ${endMs}ms -- head seam trimmed` : ""));

  const t0 = Date.now();
  for (let f = 0; f < FRAMES; f++) {
    const t = START + f * (1000 / FPS);
    await page.evaluate((ms) => {
      for (const a of document.getAnimations()) { try { a.currentTime = ms; } catch {} }
    }, t);
    await page.screenshot({ path: join(frameDir, `f${String(f).padStart(5, "0")}.png`), captureBeyondViewport: false });
    if (f % 100 === 0) console.log(`  frame ${f}/${FRAMES}  t=${t.toFixed(1)}ms  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  console.log(`captured ${FRAMES} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
} finally {
  await browser.close();
}

// encode -- part of the same command, never a separate step. With --silent-audio
// the encode still happens here; the mux that follows only COPIES this stream.
const fail = (msg) => { rmSync(frameDir, { recursive: true, force: true }); console.error(msg); process.exit(1); };
const mutePath = silentAudio ? outPath + ".mute.mp4" : outPath;
const enc = spawnSync("ffmpeg", encodeArgs(
  { encoder, fps: FPS, framePattern: join(frameDir, "f%05d.png"), outPath: mutePath }), { stdio: "inherit" });
if (enc.status !== 0) fail("ffmpeg encode FAILED");
if (silentAudio) {
  const mux = spawnSync("ffmpeg", silentAudioArgs({ videoPath: mutePath, outPath }), { stdio: "inherit" });
  rmSync(mutePath, { force: true });
  if (mux.status !== 0) fail("ffmpeg silent-audio mux FAILED");
}
rmSync(frameDir, { recursive: true, force: true });

// verify out of the finished file: duration + a mid-file frame that isn't blank
const probe = spawnSync("ffprobe", ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", outPath], { encoding: "utf8" });
const dur = parseFloat(probe.stdout);
const want = (endMs - START) / 1000;
const midPng = outPath + ".verify.png";
const ext = spawnSync("ffmpeg", ["-y", "-v", "error", "-ss", String(want / 2), "-i", outPath, "-frames:v", "1", midPng]);
const midOk = ext.status === 0 && statSync(midPng).size > 20000; // a real frame, not a black card
rmSync(midPng, { force: true });
// the flag promised a track; read it back out of the file rather than trust the mux
let audioOk = true;
if (silentAudio) {
  const ap = spawnSync("ffprobe", ["-v", "error", "-select_streams", "a", "-show_entries",
    "stream=codec_name", "-of", "csv=p=0", outPath], { encoding: "utf8" });
  audioOk = ap.status === 0 && ap.stdout.trim().length > 0;
}
if (Math.abs(dur - want) > 0.15 || !midOk || !audioOk) {
  console.error(`VERIFY FAILED -- duration ${dur}s (want ${want}s), mid-frame ok=${midOk}, audio ok=${audioOk}`);
  process.exit(1);
}
if (profile) {
  const evidence = {
    profile: profile.id, browser_build: browserBuild, gpu,
    fps: FPS, frames: FRAMES, master_ms: MASTER, start_ms: START, end_ms: endMs,
    encoder, silent_audio: silentAudio, ...sourceFile(),
  };
  writeFileSync(outPath + ".render.json", JSON.stringify(evidence, null, 2) + "\n");
  console.log(`render evidence -> ${outPath}.render.json`);
}
console.log(`ok -- ${outPath}: ${dur}s @ ${FPS}fps, ${FRAMES} frames, mid-frame decoded and non-blank`
  + (silentAudio ? ", audio stream present" : ""));
