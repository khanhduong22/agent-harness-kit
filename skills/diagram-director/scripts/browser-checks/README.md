# Browser-side checks

The render-side gates. Everything in `scripts/*.py` reasons about the FILE; everything here
reasons about the rendered page — measured boxes, seeked timelines, emulated media features.
That is the whole reason the directory exists: a diagram can be structurally perfect and
visually broken, and every failure listed below shipped green through the static checks first.

All of them are **optional** — the skill has no npm dependency and never will (see puppeteer
resolution below) — but a cut that ships without them ships unverified.

## The checks

| Script | What it catches (and the failure it was born from) |
|---|---|
| `verify-caption-boxes.mjs` | Caption text spilling its own card. Neither the node-containment sweep (text vs node shapes) nor the safe-area sweep (text vs frame) compares those two boxes, so a restyled fork whose label font changed spilled a word onto raw canvas at card-text polarity — dark on dark, unreadable, every other gate green. |
| `verify-text-containment.mjs` | Three sweeps: node text crossing its own shape's border **at the text's own y-band** (a polygon narrows toward top/bottom at a rate its own VERTEX COUNT decides — a 6-point hexagon at 20/40, a 4-point decision diamond twice as fast; treating every polygon as a hexagon failed the shipped diamond snippet's own coordinates. A text whose y-band is entirely OUTSIDE the body is a below-label — the diamond's sanctioned idiom — and skips the NARROWING only: there is no body at that y to narrow, so it is measured against the plain shape box instead, which still catches a label wider than the node it hangs under. It is counted on the pass line, never silent. Its vertical containment is the one thing nobody can assert, and that is what hold-geometry's `[INK-VERTICAL]` exempts. Mono runs ~20% wider than sans after a font swap); text overlapping a node it does not belong to (measured in SCREEN space — `getBBox()` is local and ignores ancestor transforms, the classic trap, hit once here); and edge endpoints not rooted on any node (review-caught: a path starting 20px past its node's corner renders as a floating dash head). |
| `verify-glyph-label-gap.mjs` | A badge glyph touching its OWN node's label. The containment sweeps check text-vs-shape and text-vs-foreign-node, so this passes everything — user-caught with a payment card touching "stripe" and a person touching "auth0"; the numeric sweep then found four hexagon badges within 0–2px that the eye had missed. **Measured on INK since 2026-09-21** (item 12): the glyph's client rect is what it paints, but a text's is the FACE's layout box, and a label with no capitals or ascenders carries empty rows of it above the first pixel — which is how this check reported `gap 0.9px` on a pair that is visibly clear at 4x. The text's bounds now come from the shared `ink-box.mjs`; a text with no anchorable baseline falls back to the client rect and the run PRINTS how many pairs were read that way. The change can only widen a gap, so nothing that passed can start failing. **Gating is DOM evidence, not only a feature**: `verify_all.py` runs it whenever the file draws a `.node__icon` inside a `g.node`, the way `node-identity` reads the DOM — a cut with seven node glyphs and no packets correctly declares no `payload-glyphs`, and used to skip the only check of that class. Declaring `payload-glyphs` still makes it mandatory on its own, so declared-but-empty is still a hard fail. |
| `verify-caption-occlusion.mjs` | **A caption card painted over the very edge its caption explains.** `verify-caption-boxes.mjs` measures a caption against its own card; `verify-hold-geometry.mjs` skips `.beat-caption` by design ("caption cards ride above the scene"), so nothing measured a card against the scene UNDER it — and a delivered cut reached review with four beats whose card sat on the edge the sentence named (the worst hid both inputs it listed) and one that covered an edge label until `outcomes` read as `outc…`, with every gate green. The rule (`references/camera-beat.md` → Captions): a card never covers an edge LABEL (`caption/occludes-edge-label`) and never covers the painted band of an edge touching its own beat's SUBJECTS (`caption/occludes-subject-edge`); crossing OTHER scenery is a printed WARNING (`caption/occludes-edge`) and never fails, because a lower-third over plain background is the house idiom. Measured at an instant inside the caption's OWN window where the card is fully revealed — after the wipe-in, before the wipe-out, read off the computed `clip-path` inset and opacity so both the current clip-only block and the goldens' legacy opacity block are handled — at the pose of the hold that instant falls in, over only the elements visible THERE. **Subjects are derived, not declared**: the lit `.node__focus` brackets already say who the beat is about, so the subject set is the `g.node`/`[data-station]` boxes a lit bracket encloses, and a subject edge is one whose `data-from`/`data-to` names one of them OR whose endpoint lands on one (12px, the same slack hold-geometry uses for "connected" — without it the rule would be N-A on the three goldens written before `node-identity` existed). A caption with no lit bracket has NO subject set: the label rule still applies, the subject-edge rule is N-A **for that caption and says so**. The tightest subject clearance is printed per caption even when it passes, so a 0.6px near-miss is in the log rather than a surprise next time. `supportedFixes` carries a dx only when the shifted card was RE-MEASURED clear of everything and still inside the hold's must-show bbox; otherwise none, because advice is not evidence. Needs the manifest (`--manifest`); genre-neutral, stage E. |
| `verify-staged-windows.mjs` | Staged states and acts that do not render when the storyboard says they do: a stage that never appears, an act bleeding through its successor, a recap replaying out of order, a loop parking on a fade instead of the finished design, or a reduced-motion render showing a montage of every act. Every other check measures ONE instant; this one seeks the master timeline. Contract: `references/camera-beat.md` → "Scenario timeline — staged states and acts". |
| `verify-console-clean.mjs` | Pre-delivery item 17, mechanised: console errors, uncaught exceptions and failed subresources. A broken CDN script, a malformed `offset-path` or a missing `<defs>` reference all fail SILENTLY in the DOM — the page renders without the thing the reference pointed at, and every geometry sweep stays green because the element it would have measured is simply not there. `/favicon.ico` is the browser's own request, not the page's, and is excluded. |
| `verify-hold-geometry.mjs` | The two failures every other sweep misses because every other sweep measures t=0 at k=1, and a beats cut is never seen at t=0 at k=1. (a) **ink-vertical containment** — item 12's rule applied for real: vertical bounds from canvas `measureText().actualBoundingBoxAscent/Descent` anchored on the true baseline, against the smallest drawn box in the node that spans the text (a `.state-chip` is measured against its own pill, not the node it hangs off). (b) **straight-segment edge vs node/foreign text** — a POLYLINE (`d` is only M/L/H/V/Z: the orthogonal handoff run `M..L..L..L`) is decomposed at its own vertices and every segment is swept; anything else has its straightness MEASURED against its own chord. Sampling alone classified L-shaped runs as curves and skipped them — a process cut arrived with 10 of 12 edges unmeasured under an `N/A` line that said only curves were skipped. Real curves are still skipped with an explicit `N/A`, because a curve's clearance is a routing judgement the contact sheet makes. The ink sweep reports below-label exemptions on its own `N/A` line. Needs the cut's manifest: `--manifest <cut>.manifest.json`. |
| `verify-html-edge-anchors.mjs` | The `--genre process` twin of `diagram-director/scripts/verify_edge_anchors.py`. That checker finds node boxes only from SVG `<g class="node">`/`.node__shape`, and a process cut is built HTML-first — stations are divs, only the connectors live in an `<svg class="edges">` overlay — so it finds ZERO boxes and reports every correct edge as FLOATING. This one measures the station boxes in the browser, divides out the camera scale, and compares them with the path `d` in the same units (contract clause 2 pins 1 svg unit == 1 css px, so the parity is exact, not approximate). Same two defect classes and the same `--tol 12`: FLOATING, and WRONG-SIDE ported verbatim from `facing_side()` (outward normal vs the DEPARTURE vertex — the next on-path point, or the first bezier control point). Plus one HTML-mode-only class, **DEAD-GEOMETRY**: contract clause 4 lets an edge run BEHIND a station rather than be clipped by hand, and the price is a path whose whole run is behind opaque blocks — in the markup, anchored, and never drawn. `verify_all.py` runs this INSTEAD of `verify-text-containment.mjs` when the manifest declares `"genre": "process"`. Selectors are overridable: `--stage`, `--station` (default `[data-station]`). It also carries the **webapp template contract v2**, scoped to webapp stations only (a `[data-station]` carrying `.win` or holding a `[data-anchor]`), so a cut without one is untouched: `WEBAPP-CONTRACT` (exactly three `[data-anchor]`; a `.win__url` in the chrome; zero anchors on a `.win--deploy` station), `ANCHOR-GATED` (an anchor inside a `[data-lod="close"]` subtree is invisible at the far tier, so its pull-line would be a zoom-only truth) and `LOD-LEAK` (an element inside the LOD system setting its own `opacity` wins the cascade at equal specificity and never hides — measured by forcing every `data-lod-tier` host to `far` with transitions disabled). |
| `verify-frame-edge-margin.mjs` | **A teaching line that hugs the edge of the frame it is being taught in.** Every other camera gate measures the must-show BBOX a hold DECLARES, and an edge is only in that bbox if the author put it there — so a connector can sit 2px inside the frame while `solve_camera --check`, stage D and the anchor sweep all stay green. Born from the process golden's loop beat: the orange return arc, rerouted over the top of the stage, ran 11.6 frame px from the frame's top edge at `b3` (2.4 once its 11px halo is counted) and the user could not see the one line the beat exists to explain. The rule (`references/camera-beat.md` → "Keep the teaching line off the frame edge"): at a hold, an edge may come within **M frame px (default 24)** of a frame side ONLY where it actually CROSSES that side; every side it does not cross owes M px of clearance to the path's **painted** band. Where both stations are fully in frame the path crosses nothing, so the whole path must stay M px inside. Scoped to edges the frame shows something at BOTH ends of — an edge running off to a station that is not in this frame at all is scenery in that beat. **Painted, not geometric**: a halo (a wider path with an IDENTICAL `d`, the house idiom for making an edge a beat's subject) is part of that edge's paint, and measuring the centreline alone passed `b3b` by 0.8px while the halo was 8px over the edge. **Crossing is read off the centreline**, so a fat stroke cannot bribe its way to an exemption. **The clipped-anchor exemption** (lead ruling 2026-08-27, shared by both readers because it is part of the RULE): a side that already CUTS one of the edge's own anchor stations owes that edge nothing — *một cạnh đã cắt chính station của edge thì không nợ edge đó khoảng thở* — because the crop has itself announced the continuation. Measured per (edge, side, hold) from the station's bbox against that frame side, never a named allowlist, and every waiver is PRINTED with the clearance it waived. It fires on **no** hold of the process golden, and it would not have waived that golden's b3 defect (stations cut by the LEFT, hug on the TOP). Needs the manifest (`--manifest`); HTML-mode station selector (`.frame` + `[data-station]` divs), so `verify_all.py` runs it on `"genre": "process"` cuts. Its SVG-mode twin is the next row. |
| `verify-svg-frame-edge-margin.mjs` | **The SVG-mode twin of the row above — same rule, same M = 24 frame px, different instrument.** A `system-design` cut IS an SVG document: its frame is the root `<svg>`'s viewBox (every reading divided by the rendered/viewBox fit ratio, so distances stay in the units the manifest and the text floor are written in) and its stations are `g.node > .node__shape` — the shape, not the group, so a label or badge cannot inflate the box an endpoint is judged against — plus the two other things an edge may honestly terminate on, `.lane-line` lifelines and `.group__box` cluster boundaries, exactly as `diagram-director/scripts/verify_edge_anchors.py` enumerates them. Scope, painted-band measurement, centreline-only crossing and the clipped-anchor exemption are identical to the HTML twin — on the goldens the clause fires exactly twice, both on `compare-chat-pubsub` (b3-b5 *User A* cut by the TOP, b6 *ws-3* cut by the LEFT) and zero times on the other three cuts; `vector-effect:non-scaling-stroke` is read as a constant SCREEN width so a future cut that adopts it on an edge is not mis-sized. Needs the manifest (`--manifest`); `verify_all.py` runs it on `system-design` cuts (the default genre) in the same stage-E slot. |
| `verify-camera-live.mjs` | **The camera the manifest describes vs the camera the page RUNS.** Every other camera gate looks somewhere else: stage D re-solves the holds without opening a browser, stage E PINS the hold's transform onto `.camera` before it measures, and `run_golden_regression.py` reads the HTML with a regex — so a cut whose `@keyframes beats` had been killed by a comment that closed `*/` one paragraph early printed **20 PASS with no camera motion at all**; the only signal was `pinCamera`'s `was none` readout, a printed word rather than a gate. This is that word turned into a gate: at every declared hold it seeks the page to the window midpoint and reads the COMPUTED transform of `.camera` **before anything is pinned**, then checks it against that hold's `k/tx/ty`. `transform:none` is read as the identity (three of the four goldens write their overview holds that way, as `beat_transforms()` does) — which is harmless because the check refuses to run on a cut with fewer than **two distinct declared poses**, so a dead camera always reads `none` at a hold whose pose is not the identity. Tolerance 1e-4 on k and 0.05px on tx/ty: the hold window is a plateau, so the midpoint reading is exact bar float noise. Needs the manifest (`--manifest`); genre-neutral, stage E. |
| `contact-sheet.mjs` | Not a check — the artifact the reviewer eyeballs, and generating it is MANDATORY (checklist item 18). Renders the cut at every declared hold and composites one image — camera holds at their pinned transform, plus one frame per ACT window, because a camera hold that spans several acts has a midpoint that can land on an act crossfade and show two acts ghosted together (observed on the progressive golden's `a3` and `a4-recap`). Curves, style fidelity and semantic truth are reviewed here and nowhere else. `sharp` is optional and resolved the same portable way puppeteer is; without it you get individual PNGs plus an HTML index, and the script says so. |
| `hold-frames.mjs` | Not a check — the shared "reproduce a declared hold" module the two above use. It PAUSES every animation and seeks `currentTime` to the hold's window midpoint (a genuine master-timeline seek, not an `animation-delay` rewrite), then pins the hold's `k/tx/ty` on `.camera` with an `!important` inline transform, which outranks the keyframes in the cascade. It reports the computed transform it replaced, so a drift between the manifest and the CSS shows up instead of being silently overwritten. |
| `ink-box.mjs` | Not a check — the ONE ink measurement, installed into the page as `window.__ddInkBox`. Item 12 ("measure ink, not the font box") in one place: canvas `measureText().actualBoundingBox*` at the text's own computed font, anchored on the real baseline and start position through `getScreenCTM()`. It was inlined in `verify-hold-geometry.mjs`; it was extracted rather than copied when the glyph-gap and caption-occlusion gates needed it, because two copies of a measurement is how the shape discriminator drifted once already (`scripts/act_dom_scan.py` header). Returns **null**, never a guess, when there is no anchorable baseline — every caller then falls back to the client rect and says it did. |
| `page-geometry.mjs` | Not a check — the shared screen-space geometry, installed as `window.__ddGeom`: visibility (including `allowThin`, the axis-aligned-path lesson that took months to reach every copy), rect overlap, segment-to-rect distance, and `paintedBand()` — an edge sampled in screen space with half its computed stroke width, honouring `vector-effect: non-scaling-stroke` as a constant SCREEN width and refusing an unpainted path. PAINTED, not geometric: a centreline cleared a frame side by 0.8px once while the halo was 8px over it. |
| `rebake-caption-boxes.mjs` | Not a check — the rewriter that makes `verify-caption-boxes` pass honestly. A caption card's rect is baked from the text's measured bbox, so it is a function of the typeface: neon-dark's mono caption ran ~13% wider than the Inter the boxes were baked against. Re-bake per fork; never hand-nudge. |

## House rule: a check that finds nothing FAILS

Zero captions, zero nodes, zero glyph/text pairs, zero `[data-window]` elements, zero rects
matched by the rewriter — every one of those is a wrong URL, a broken page or selector drift,
and every one of them used to report a cheerful green. They are hard failures now. Exit codes:
`0` pass, `1` violation (or empty element set), `2` bad usage.

## The `##DIAG` line — structured evidence for `verify_all.py --json`

A check may print, on stdout, one JSON object per line behind a `##DIAG ` prefix:

```
##DIAG {"code":"edge/frame-margin","subject":{"element":"path.edge-enqueue","hold":"a4b"},"evidence":{"side":"top","clearance_px":11.6,"required_px":24}}
```

Contract, both directions:

- **`code`** is the only required key, and it must be one the registry
  (`diagram-director/scripts/diagnostic_codes.py`) already knows. A code it does not know, an unparseable line, or
  a line over 8 KB is folded into `runner/check-missing` with the raw text as evidence — never a
  crash, never silence. Codes are `<namespace>/<slug>`; new namespaces are allowed, new codes are
  registered in that file rather than invented at the print site.
- **`subject`** says WHAT the defect is about (`hold`, `element`, `text`), **`evidence`** carries
  the NUMBERS the check already measured. Both are free-form objects and both are optional.
- **`supportedFixes`** is optional and rides through to the envelope's `supportedFixes`. It is an
  imperative sentence WITH NUMBERS that the check PROVED — `verify-caption-occlusion.mjs` walks the
  card outwards a pixel at a time and re-measures before it offers a dx, and stays silent when no
  offset clears everything inside the hold's bbox. Never "consider", never "try": a fix nobody
  measured is advice, and this envelope does not carry advice.
- **A `.mjs` never declares severity.** It reports what it measured; the runner owns policy
  (`error` / `warning` / `unverified`), so the same finding can be fatal in one stage and
  advisory in another without touching this file. `caption/occludes-edge` is the registry's one
  `warning` today: a card over plain scenery is measured, printed and shipped.
- `run_node()` in `diagram-director/scripts/verify_all_browser.py` strips these lines from BOTH streams before it
  builds the one-line prose tail, so the human stage table reads exactly as it did before a check
  learned to emit them. They are ADDITIVE in the envelope: the stage row is still one diagnostic,
  and each `##DIAG` line is one more beside it — a check that codes only some of its violation
  classes does not drop the rest out of the envelope.
- Emitting them is optional. `verify-hold-geometry.mjs` (ink-vertical), `verify-text-containment.mjs`
  (overflow + floating endpoint), `verify-svg-frame-edge-margin.mjs` (frame margin),
  `verify-glyph-label-gap.mjs` (badge gap) and `verify-caption-occlusion.mjs` (all three caption
  classes) do today.

## Serve over HTTP, never `file://`

Fonts, CDN scripts and media features all behave differently under `file://`, and the numbers
these checks produce are only meaningful against the reality the page ships into. Serve the
directory and point the checks at `http://localhost:<port>/…`:

```bash
python3 -m http.server 8931 --directory .   # then, in another shell:
node diagram-director/scripts/browser-checks/verify-caption-boxes.mjs   http://localhost:8931/my-cut.html
node diagram-director/scripts/browser-checks/verify-text-containment.mjs http://localhost:8931/my-cut.html
node diagram-director/scripts/browser-checks/verify-glyph-label-gap.mjs  http://localhost:8931/my-cut.html
node diagram-director/scripts/browser-checks/verify-staged-windows.mjs   http://localhost:8931/my-cut.html
node diagram-director/scripts/browser-checks/verify-staged-windows.mjs   http://localhost:8931/my-cut.html --acts
node diagram-director/scripts/browser-checks/verify-staged-windows.mjs   http://localhost:8931/my-cut.html --reduced-motion
node diagram-director/scripts/browser-checks/verify-console-clean.mjs   http://localhost:8931/my-cut.html
node diagram-director/scripts/browser-checks/verify-html-edge-anchors.mjs http://localhost:8931/my-cut.html   # --genre process cuts
node diagram-director/scripts/browser-checks/verify-hold-geometry.mjs   http://localhost:8931/my-cut.html --manifest my-cut.manifest.json
node diagram-director/scripts/browser-checks/verify-frame-edge-margin.mjs http://localhost:8931/my-cut.html --manifest my-cut.manifest.json
node diagram-director/scripts/browser-checks/verify-svg-frame-edge-margin.mjs http://localhost:8931/my-cut.html --manifest my-cut.manifest.json
node diagram-director/scripts/browser-checks/verify-camera-live.mjs         http://localhost:8931/my-cut.html --manifest my-cut.manifest.json
node diagram-director/scripts/browser-checks/verify-caption-occlusion.mjs http://localhost:8931/my-cut.html --manifest my-cut.manifest.json
node diagram-director/scripts/browser-checks/contact-sheet.mjs          http://localhost:8931/my-cut.html --manifest my-cut.manifest.json --out sheets/
node diagram-director/scripts/browser-checks/rebake-caption-boxes.mjs    my-cut.html          # --base http://localhost:8931
```

**Do not run these one at a time in delivery.** `python3 diagram-director/scripts/verify_all.py <cut>.html --serve`
runs the whole set, decides which of them are MANDATORY for this cut from its manifest's declared
feature list (declared-but-empty is a hard fail, undeclared prints `N-A`), serves the file itself
on a free port, and adds the stdlib structural checks and the per-hold camera math. Reach for the
individual scripts when you are iterating on one failure.

`rebake-caption-boxes.mjs` takes local file paths (it rewrites them in place) but measures them
through the server: pass `--base <url>`, or export `SERVE_BASE=http://localhost:<port>` — the two
set the same thing and `--base` wins.

**8931 is a convention, not a promise.** Every command above hard-codes it because a README needs
*some* number, and the whole set (`verify_all.py --serve` included) works on any port. On a machine
where something already holds 8931 the default points at a stranger's server, and `rebake` in
particular rewrites your file off whatever it finds there — so it now refuses with the root it
tried instead of failing obscurely. Pick a free port, serve **the cut's own directory**, and pass
that root everywhere:

```bash
PORT=8945; python3 -m http.server $PORT --directory "$(dirname my-cut.html)" &
export SERVE_BASE="http://localhost:$PORT"
node diagram-director/scripts/browser-checks/rebake-caption-boxes.mjs my-cut.html    # uses SERVE_BASE
node diagram-director/scripts/browser-checks/verify-caption-boxes.mjs "$SERVE_BASE/my-cut.html"
```

## Puppeteer resolution

Puppeteer is **not** a dependency of this skill, and `resolve-puppeteer.mjs` carries **no
machine-local default** — it used to hardcode one contributor's home directory, which made these
gates work on exactly one laptop and fail everywhere else with a stranger's path in the error.
Resolution order:

1. **`PUPPETEER_RESOLVE_DIR`** — any directory from which `require("puppeteer")` resolves (the
   `chrome-devtools` skill's `scripts/` directory is the usual one, but any node project that
   installed puppeteer works). **The trailing slash matters**: `createRequire` treats a bare path
   as a *file* and resolves relative to its parent.
2. **a plain `import("puppeteer")`** — a local `node_modules`, an `npm link`, or a global install
   exposed through `NODE_PATH`.

```bash
PUPPETEER_RESOLVE_DIR=/path/to/node-project/ node diagram-director/scripts/browser-checks/verify-staged-windows.mjs <url>
```

### The UNVERIFIED skip path

If neither resolves, the script prints the `UNVERIFIED` banner and exits `2`. It never silently
skips, and **exit 2 is not a pass** — it means the render-side gates did not run at all:

```
UNVERIFIED -- puppeteer not available; render-side checks did not run.
```

A cut delivered after a code-2 skip is an **unverified cut, and the delivery message must say so**
— name which checks did not run and why. Reporting "checks passed", or saying nothing, turns a
skipped gate into a claimed one, which is the exact failure the house rule above ("a check that
finds nothing FAILS") exists to prevent. Same wording is required by
`references/pre-delivery-checklist.md` item 15.

## render-video.mjs
Deterministic video export for a finished cut: frame-steps every animation via
`currentTime`, encodes with ffmpeg IN THE SAME COMMAND, then verifies duration
and a decoded mid-frame out of the finished MP4. Never report a video delivered
from capture logs alone — this tool exists because that once shipped stale
footage. `node diagram-director/scripts/browser-checks/render-video.mjs <cut.html> <out.mp4>
[--fps 30] [--master 38400]`.
