# Output Rules, Format Contracts, Style Forks & Beats Mode

Companion reference for `diagram-director/SKILL.md`. Contains the Query Contract details, complete output rules, landscape vs vertical (1080×1920) frame contracts, style/node-rendering fork rules, and Beats Mode narrated camera specification.

---

## 0. Detailed Query Contract (`--blueprint` & `--domain`)

1. **New diagram → `--blueprint` first, always**, with `--genre` from STEP 0 and `--target` from STEP 1 (`python3 diagram-director/scripts/search.py "<scenario>" --blueprint --target artifact`).
   - Authoritative: diagram **type**, **layout**, **style** (absent explicit user override, in which case re-run `--blueprint --style <x>` and record in `DEVIATIONS`), **palette** tokens, edge semantics, motion set, anti-patterns.
   - Illustrative only (never a paste list): the **component catalog** (section 2). Component shapes must always come from per-component `--domain components` queries recorded in the Phase 3 mapping table (`references/workflow-phases.md` → Phase 3).
2. **If `--blueprint` ABSTAINS**, re-run with `--type <type-id>` or rephrase the scenario.
3. **Targeted follow-up concern → one `--domain` search**, carrying `--genre` on `types` and `components`. Cross-genre pointers (`id_lookup.py`) fire only on exact Component/row ID or `Aliases` matches.
4. Use 2–5 meaningful terms, one dominant intent, and always pass `--domain` explicitly.
5. `-n` defaults to `-n 1`; retry once with `-n 5` in exploration mode on an empty/off-topic result.
6. Record every `0`-result (`NO ROW — custom shape` / `NO ROW — cadence on edge`) and every rejected false friend in the solution sheet.
7. `--domain colors` with a Style ID returns all 7 role rows of that style's `Default Palette`. Never mix roles from two palettes into one diagram.

---

## 1. Output Rules

- Self-contained single HTML file by default. Split `styles.css` + `diagram.js` only past ~800 lines.
- Copy `templates/base/<style>.html` + the needed `templates/snippets/` rather than writing SVG from scratch. Check `styles.csv → Template Status` before naming a path, and **never cite a template path for a style marked `planned`**; compose that one from snippets and say so.
- **The copy-sources, by layer** — motion: `templates/snippets/motion-blocks.css`; states: `templates/snippets/state-effects.css`; shapes: `templates/snippets/node-shapes*.html` + `packet-glyphs.html`; **beats / educational cuts: `templates/snippets/camera-beat.css`** (caption card + wipe, heading fade, corner-bracket spotlight, staged-state windows, acts + recap, the negative-delay rule, reduced-motion). **For a `process` cut the genre's own snippets come first** (`templates/snippets/process-stations.html` + `.css`: HTML stations + SVG-overlay connectors, the two-tier LOD).
- **A progressive / scaling story COPIES its presentation layer, never re-derives it**: five acts, 48s master, and the worked implementation of the foreground-budget / veterans-recede / solved-compress / fixed-zoning rules (`references/multi-pane.md`) plus the one-hold-per-BEAT rule (`references/camera-beat.md`, `references/output-manifest.md`).
- Inline `<svg>` only, never `<img src="*.svg">`.
- `@media (prefers-reduced-motion: reduce)` is mandatory and must render the informative **end state** (solid strokes, packets parked, queues at rest) — not a frozen mid-animation frame.
- SVG root carries `role="img"` + `<title>` + `<desc>`; every node group carries an accessible name via a `<title>` child; a visible legend is present (except monochrome `hud-monochrome`).
- **Every node group carries `data-node-id`, every edge carries `data-from`/`data-to`** — kebab-case, unique and stable inside the file.
- Never encode meaning in color alone — pair with a label, icon, or line style.
- **Polling is a CADENCE ON AN EDGE, never a node.** Put the interval in the edge label (`GET /price · every 1s`), give the edge payload `request` and motion `round-trip` or staggered `packet-travel`. Never invent a poll-client node or substitute `cron-job`.
- **A component's condition comes from `data/states.csv`, in all three layers**: static encoding + chip (always visible), motion composed from `Motion Ref`, and reduced-motion resting visual. Rows with blank `Motion Ref` (`is-idle`, `is-down`, `flow-attention`) are static by design.
- **Stack/replica ghosts are outline-only** — a stroke silhouette (`fill:none`) offset behind the node, opacity stepping down.
- **Multi-pane diagrams (comparison panes, progressive load tiers)** follow `references/multi-pane.md`. Identical components render identically across panes (only the delta takes the accent), and every pane/tier fits one camera frame at `k_read`.
- **Staged states and acts are overlays on the master timeline**, carrying `data-window="A,B"` annotations verified by `diagram-director/scripts/browser-checks/verify-staged-windows.mjs`.
- **Every delivered diagram ships `<diagram>.manifest.json` beside its HTML**, validated by `diagram-director/scripts/validate_manifest.py`. Use `diagram-director/scripts/emit_timeline.py` and `diagram-director/scripts/solve_camera.py`.
- Non-interactive: looping motion by default (`dash-flow`, `pulse-glow`, `queue-fill`, `heartbeat`), except one-shot boot-sequence motions (`connection-draw-in`, `node-boot-sequence`, `replication-sync`). No hover/click/playback controls.
- Hand-place coordinates using the chosen layout's `Spacing Rules` (≤20 nodes, ≥40px or half shorter side between neighbours, text ≥6px off node border at its y-band).
- **The camera's world moves as one**: background grids live inside `.camera` as `<pattern>`-filled SVG rects.
- **Primary components outrank supporting ones by ~15% in size** and **wear a figurative glyph of what they ARE** seated left of the label on a widened card (~+30px, e.g. 190×80 in `templates/snippets/node-shapes-ml.html`).
- **Clusters and replicas are drawn as a stack** (`shape-replica-stack`) with explicit count in the sub-label; singletons (leader, single-threaded counter) are never stacked.
- **Turn ligatures off wherever literal text lives** (`font-variant-ligatures:none` on mono/code classes).
- **Render and look at the result before delivering.**

---

## 2. Output Format — Landscape or Vertical

| Format | When | Frame contract |
|---|---|---|
| **Landscape** (default) | Desktop pages, docs, YouTube, slides | Wide viewBox (~2:1–2.25:1); full component cast; fits one desktop viewport without scrolling |
| **Vertical / short** | TikTok, Reels, Shorts, phone-first teaching | 1080×1920. **Same solution, same component count, same beats and captions — only the layout system and camera targets change.** |

Vertical hard rules:
- **Safe area**: keep every readable element inside `x 60–890`, `y 150–1540` (top 150, bottom 380, right 190, left 60).
- **Centre headings on the FRAME (`x 540`), never on the safe band's centre (`x 475`)**, then verify the widest line ends inside the safe box.
- **Distribute the column across the whole safe band**: `gap = (safe_h − Σ row_heights) / n_gaps`, never below 40px (shrink row heights if needed, never the gap).
- **Fork discipline**: diff every label against the landscape source on creation AND on every later edit.
- Delivery: H.264 High, yuv420p, 30fps, audio track present, 15–60s window for shorts.

---

## 3. Restyling a Finished Cut (Style Forks & Node-Rendering Forks)

A delivered diagram can be re-skinned into any other style without touching a single coordinate by patching the font `<link>`, the `:root` token block, and a short skin override. Verification rules for forks:
- **Geometry is a function of the typeface — re-run every containment check** (mono runs ~15–20% wider than Inter; Caveat has tall ascenders).
- **Re-bake every baked rect** (caption cards depend on measured text bbox) and assert each caption sits inside its card.
- **Skin the elements, not the ground** (glass requires 10–20% translucent panes over a dark low-saturation ground with blooms, bright rim, and 1px specular top edge — never `backdrop-filter` on SVG).
- **Every looping duration must divide the master timeline (`master % duration == 0`)**.
- **A display face skins the scenery, never the narration** (beat captions always keep a readable text face).
- **Never put an SVG `filter:url()` on an element that can have zero area** (straight horizontal/vertical lines have 0 height/width bbox and become invisible) or on animated elements inside a moving `.camera`.
- **Changing `stroke-width` silently resizes arrowheads** (`markerUnits="strokeWidth"`): patch `markerWidth` in defs to keep `markerWidth × stroke-width` constant.
- **Ship the fork through one build command: generate → re-bake → verify**, and assert a non-zero element count in every check.

### Node-Rendering Forks (`<g class="node__body">`)
- `ascii-terminal`: box-drawing text pinned with `textLength` + `lengthAdjust="spacingAndGlyphs"`; labels stay in separate `<text>` elements.
- `isometric-2.5d`: add top and right faces on a 30° axis behind the front face; offset a copy of the shape itself for hexagons/cylinders.
- `comic-storytelling`: inked panel frame + halftone overlay, **no speech-bubble tails**; heavy text face with ink outline for headlines.
- `claymorphism`: half-perimeter inner rims (light arc top-left, dark arc bottom-right) + fat radius + wide cast shadow.

---

## 4. Beats Mode (Narrated Camera)

When asked to *walk through*, *explain step by step*, or *narrate* a system (or target a short video), the camera (`transform` on `.camera`, never `viewBox`) zooms to each component in story order:
- Auto-plays on an infinite loop with no interactive controls.
- **Every mechanism drawn gets a beat**, and **every beat contains the upstream node it receives from**.
- Captions sit in a baked rounded card (`rect` + `rx`) in a fixed slot inside the hold's frame (`≤ ~5 words/second`).
- **Final beat is always the full overview** (`@media (prefers-reduced-motion: reduce)` renders that state with captions hidden and narration in `<desc>`).
- **Zoom is computed via `diagram-director/scripts/solve_camera.py --gate`**: `k_read = P_min / fs_min` (24px landscape, 28px vertical) up to `k_fit`, capped at 3.
- **Subject spotlight**: four corner brackets (`cb-spotlight-bracket` in `templates/snippets/camera-beat.css`, pad 12, arm 22) around the subject's full visual bbox during the caption's timing window.
- Optional **opening title beat (`t0`)** behind frosted glass for ~2s (`references/camera-beat.md`).
