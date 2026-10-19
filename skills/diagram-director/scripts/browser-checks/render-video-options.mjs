// Pure decisions for render-video.mjs: what the flags mean, where the linear cut
// ends, and the exact ffmpeg argument list each encoder gets. No fs, no process,
// no browser -- so a unit test can assert the produced argv without a machine that
// has Chrome, and so the DEFAULT argument list can be pinned by a test and never
// drift (the goldens' documented export path is the libx264 one below).
export const ENCODERS = ["libx264", "videotoolbox"];
export const PROFILES = ["gpu-native-1"];

// h264_videotoolbox constant-quality, not bitrate: flat vector art alternates huge
// flat fields with hard 1px edges, so a fixed bitrate either starves the edges or
// wastes megabits on the flats. 80 is the lowest 5-step rung that MATCHES the
// libx264 -crf 18 default rather than merely looking fine -- measured 2026-09-21 on
// 60 real 1080x1920 frames of the jev-decision-agent cut (beat b4: red router card,
// chip text, hairlines), PSNR against the yuv420p source: crf 18 = 53.4 dB avg /
// 51.3 min; q:v 80 = 54.6 / 53.4; q:v 70 = 50.7 / 49.7; q:v 65 = 48.1 / 47.1.
export const VIDEOTOOLBOX_QUALITY = 80;

export const USAGE = [
  "usage: render-video.mjs <url-or-file> <out.mp4> [--fps N] [--master MS]",
  "       [--width N] [--height N] [--manifest cut.manifest.json]",
  "       [--start-ms N] [--end-ms N]",
  `       [--profile ${PROFILES.join("|")}] [--encoder ${ENCODERS.join("|")}] [--silent-audio]`,
].join("\n");

// Flags are read positionally-first (target, out) then by name, exactly as the
// original tool did; unknown flags stay ignored so an old invocation cannot start
// failing. What IS refused: an unknown profile or encoder, and a named flag with
// no value -- both would otherwise fall through to a silent default.
export function parseRenderArgs(argv) {
  const [target, outPath] = argv;
  if (!target || !outPath) throw new Error(USAGE);

  const num = (name, dflt) => {
    const i = argv.indexOf(`--${name}`);
    return i < 0 ? dflt : Number(argv[i + 1]);
  };
  const str = (name) => {
    const i = argv.indexOf(`--${name}`);
    if (i < 0) return null;
    const value = argv[i + 1];
    if (value === undefined || value.startsWith("--")) throw new Error(`--${name} needs a value`);
    return value;
  };

  const profile = str("profile");
  if (profile !== null && !PROFILES.includes(profile)) {
    throw new Error(`unknown --profile ${profile}; known: ${PROFILES.join(", ")}`);
  }
  const encoder = str("encoder") ?? "libx264";
  if (!ENCODERS.includes(encoder)) {
    throw new Error(`unknown --encoder ${encoder}; known: ${ENCODERS.join(", ")}`);
  }

  return {
    target, outPath,
    fps: num("fps", 30),
    width: num("width", 1920),
    height: num("height", 1080),
    manifestPath: str("manifest"),
    masterFlag: argv.includes("--master") ? num("master", 38400) : null,
    startMs: num("start-ms", 0),
    endMsFlag: argv.includes("--end-ms") ? num("end-ms", NaN) : null,
    profile, encoder,
    silentAudio: argv.includes("--silent-audio"),
  };
}

// LINEAR-ENDING RULE, the manifest half (the script header carries the why).
// Returns null when the cut has no loop-seam wind-up -- then the linear MP4 runs
// the whole master and the closing hold keeps every frame it was given.
export function windupEndMs(manifest, master) {
  const starts = (manifest?.holds || [])
    .filter((h) => h.kind !== "camera")
    .filter((h) => (h.windows || []).some(([a]) => a <= 0.001))
    .flatMap((h) => h.windows || [])
    .filter(([a, b]) => b >= 99.999 && a > 90)
    .map(([a]) => a);
  if (!starts.length) return null;
  const startPct = Math.min(...starts);
  return { endMs: Math.floor((startPct / 100) * master) - 1, startPct };
}

// The captured span, validated. `start-ms` defaults to 0, and at 0 this is exactly
// the frame count the tool always computed -- the head trim cannot move the default
// export by a single frame. Frame f is captured at startMs + f * (1000 / fps).
export function frameSpan({ startMs, endMs, fps }) {
  if (!Number.isFinite(startMs) || startMs < 0) {
    throw new Error(`--start-ms must be a number >= 0 (got ${startMs})`);
  }
  if (!Number.isFinite(endMs) || endMs <= startMs) {
    throw new Error(`--end-ms (${endMs}) must be greater than --start-ms (${startMs})`);
  }
  if (!Number.isFinite(fps) || fps <= 0) throw new Error(`--fps must be > 0 (got ${fps})`);
  return Math.round(((endMs - startMs) / 1000) * fps);
}

export function encodeArgs({ encoder, fps, framePattern, outPath }) {
  const head = ["-y", "-v", "error", "-framerate", String(fps), "-i", framePattern];
  if (encoder === "libx264") {
    return [...head, "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", outPath];
  }
  if (encoder === "videotoolbox") {
    return [...head, "-c:v", "h264_videotoolbox", "-profile:v", "high",
      "-q:v", String(VIDEOTOOLBOX_QUALITY), "-pix_fmt", "yuv420p", outPath];
  }
  throw new Error(`unknown encoder ${encoder}`);
}

// The delivery rule wants an audio track present, not an audio track invented: the
// video stream is COPIED, so muxing cannot re-encode the picture that was already
// verified, and -shortest keeps the silence from outliving the last frame.
export function silentAudioArgs({ videoPath, outPath }) {
  return ["-y", "-v", "error", "-i", videoPath,
    "-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-shortest", outPath];
}
