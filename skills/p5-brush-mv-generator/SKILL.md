---
name: p5-brush-mv-generator
description: End-to-end workflow for creating hand-painted watercolor & ink Music Videos (MV) using p5.js, p5.brush, Puppeteer headless Chrome, and FFmpeg from an audio file and character reference images.
---

# p5.brush Watercolor Music Video Generator

## 1. Audio & Vocal Onset Alignment (`src/lyrics.js`)
1. **Measure Exact Duration & BPM**:
   - Inspect duration with `ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 assets/song.mp3`.
   - Extract 0.1s RMS energy envelope using `ffmpeg -i assets/song.mp3 -ac 1 -ar 1000 -f s16le - | python3 ...` to locate exact vocal onsets and breath pauses.
2. **Vocal-Only Karaoke Invariant**:
   - **NEVER** add placeholder/descriptive lines into `LY` (`src/lyrics.js`) during instrumental Intros, Interludes, vocalizing ("Ah-ah-ah") Bridges, or Outros.
   - `LY` entries `[start, end, mainLyric, subLyric]` must strictly match timestamps where lyrics are sung.
   - Any title card during the Intro/Outro must be drawn in world space via `letter()` inside the chapter file, not via the bottom karaoke bar.

## 2. Character Rig Architecture (`src/cast.js` & `src/clawd.js`)
1. **Protagonist (`heroine(x, y, s, o)`)**:
   - Model hairstyle, outfit, accessories (e.g., shoulder tote bag), and signature pose (`o.pose === 'photo'`) from the user's reference photo.
2. **Companion Rig (`clawd(x, y, u, o)`)**:
   - Default to an expressive **Watercolor Chibi Cat** (or user-requested mascot) while preserving the standard local coordinate contract:
     - Ground point `(x, y)`, scale unit `u`, head centered at `(0, -5.6u)`, arms pivoting at `(±4.4u, -4.4u)` with `armL(u, sw)` and `armR(u, sw)` hooks at arm tips (`2.2u` outward).
     - Preserving these hooks guarantees held props (violin, flute, lantern, paintbrush) and hats (`fedora`, `crown`, `party`, `bowtie`, `halo`) align automatically across all chapters.

## 3. High-Speed GPU Rendering & Sample-Accurate Audio (`render.mjs`)
1. **Platform GPU Backend**:
   - Use `--use-angle=metal` on macOS (`process.platform === 'darwin'`) and `--use-angle=d3d11` on Windows.
2. **Multi-Browser Workers & Page Recycling**:
   - Launch an independent `puppeteer.launch()` instance per worker in `--frames` mode and recycle the page every 50 frames (`pageFrames % 50 === 0`) to prevent `p5.brush` WebGL framebuffer accumulation.
3. **Sample-Accurate Audio Slicing (`--clip`)**:
   - Always use `-filter_complex "[1:a]atrim=start=${a}:end=${b},asetpts=PTS-STARTPTS[aout]"` instead of input `-ss` before `-i song.mp3` to prevent VBR MP3 seek drift.
