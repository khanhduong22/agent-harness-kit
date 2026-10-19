Skill 200Lab «Diagram director: vẽ sơ đồ system design có chuyển động thành một file HTML/SVG tự chứa, kèm kit miễn phí của 200Lab» v1 · phần lean-build «Lean build: one self-contained HTML/SVG file, layout, motion recipes and budget, beats, styles (own)» — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài.

# Lean build: one self-contained HTML file, hand-written

Phases 3-4 without the kit (`own`: the diagram-director engine's output rules, condensed). The
file must render in a chat app's artifact sandbox and open offline, so motion is CSS only and
nothing loads from the network.

## File contract

- One `.html`; inline `<svg>` (never `<img src="….svg">`); one `<style>`; no script unless a
  beats caption width must be measured once at load. No external host: system font stacks
  (`Inter, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`; mono
  `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`).
- Colours only as tokens on `:root` (`--surface --ink --muted --stroke --accent --role-client
  --role-service --role-data --role-async --ok --warn --crit`), with a dark set under
  `prefers-color-scheme: dark`. No literal colour elsewhere, so a restyle swaps one block.
- Ids come from the sheet; each edge is `<path class="edge" data-from="api" data-to="orders-db">`.
  By genre:
  - `system-design`: the SVG root has `role="img"`, a `<title>` and a `<desc>` (in beats mode,
    the full narration); each node is `<g class="node" data-node-id="orders-db">` with a `<title>`
    first child.
  - `process`: a `<figure aria-label="what the frame shows">` holding HTML stations
    `<div class="station" data-node-id="review">` with a visible title; connectors in one
    `<svg class="edges" aria-hidden="true">` under the stations; the narration in `<figcaption>`.
- A visible legend: role colours, solid line = synchronous call, dashed = asynchronous, the packet
  glyphs used.
- `font-variant-ligatures: none` on mono text, so `>=` renders as typed.

## Layout: hand-placed, no solver

- At most 20 nodes. Landscape viewBox about 2:1 (`0 0 1600 760`); nominal node 160×80.
- Flow direction by type: request lifecycle and pipelines left to right; tiers top to bottom;
  pub/sub a hub with subscribers fanned out; a sequence as lanes with shared time columns; a
  state machine as states and labelled transitions.
- Clearance: at least half a node's shorter side between neighbours, never below 40 px (60 is the
  nominal gap). Text sits at least 6 px inside its shape at the text's own height (hexagons and
  cylinders narrow away from the middle). An edge label fits its gap without touching a node.
- No edge crosses a node or any text; two edges going the same way are nested, not crossed;
  return paths are the usual offenders. An edge leaves and enters the side facing its far end.
- Shapes by kind: database a cylinder; cache a rounded rectangle with a badge; queue or stream a
  pipe with slots; gateway or load balancer a hexagon; client a device frame; a third party a
  dashed outline; N instances a stack (two offset outline-only ghosts behind the card, `×N` in the
  sub-label). Keep the scene grid inside the camera group in beats mode.

## Motion that shows behaviour

Animate only `transform`, `opacity`, `clip-path`, `stroke-dashoffset` and `offset-distance`.

| Behaviour | Recipe | Reduced-motion end state |
|---|---|---|
| continuous flow on an edge | dash-flow | solid stroke, no dashes |
| one request or message moving | packet-travel | packet parked at the destination |
| request out, response back | round-trip | both packets parked, latency in the label |
| work piling up in a buffer | queue-fill | bar at its current fill level |
| a node working | pulse-glow | full opacity, fixed glow |
| one event to every subscriber | fanout-broadcast (packets on each edge, same delay) | packets parked at each subscriber |
| retry after a failure, a breaker opening | retry-loop, circuit-breaker-flicker | final state with its chip |
| overload: requests dropped or held | load-shedding, throttle-gate | rejected packets parked at the gate, a `503` or rate chip |
| a failure spreading | error-propagation | failed nodes in their down state with chips |

```css
.edge--flow { stroke-dasharray: 8 6; animation: dash 1.2s linear infinite; }
@keyframes dash { from { stroke-dashoffset: 56; } to { stroke-dashoffset: 0; } }
.packet { offset-path: path("M 260 120 L 480 120"); animation: travel 2.4s ease-in-out infinite; }
@keyframes travel { from { offset-distance: 0%; } to { offset-distance: 100%; } }
.queue__bar { animation: fill 4.8s ease-out infinite; }
@keyframes fill { from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 var(--empty, 30%) 0 0); } }
.node--busy { animation: pulse 1.6s ease-in-out infinite; }
@keyframes pulse { 50% { opacity: .6; } }
```

- The packet's `offset-path` repeats its edge's `d`; concurrent packets are staggered 150-300 ms.
- Budget: at most 12 animated edges; animate the primary path, keep the rest solid and static.
- Every infinite duration divides the master loop (house beat 4.8 s; 1.2, 1.6, 2.4 and 4.8 s all
  divide 9.6 s), or the loop visibly jumps.
- Loops run forever with no hover, click or play control. A one-shot motion (a connection drawn
  in, nodes booting, replication catching up) plays once and holds its end state.
- A condition (overloaded, degraded, down) is shown three ways: a static encoding plus a chip
  with a word or number, a motion, and the reduced-motion resting look. Down and idle are static
  by design; stillness is their meaning.

## Reduced motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
  .edge--flow { stroke-dasharray: none; }
  .packet { offset-distance: 100%; }
  .queue__bar { clip-path: inset(0 var(--empty, 30%) 0 0); }
  .camera { transform: none; }  .caption { display: none; }
}
```

The result is the informative end state: the final overview, packets at their destinations,
queues at their level, chips visible, captions hidden (the narration lives in `<desc>`).

## Beats mode (a narrated camera)

- One `<g class="camera">` wraps the whole scene; one `@keyframes` on its `transform` moves it from
  hold to hold. Never animate the `viewBox`.
- Zoom per hold: the smallest essential text times the zoom reaches 24 px on screen in landscape
  (28 px vertical), with the zoom at most 3. A hold that cannot reach it is over-stuffed: split
  the beat.
- Captions: a rounded card and its text in one group, in a fixed slot of the hold's frame, ink card
  with surface-coloured text, revealed and hidden by a `clip-path` wipe while `opacity` stays 1.
  The card's width comes from the text's measured box, never a guess; re-measure after a font or
  language change (Vietnamese runs 15-20% longer).
- Spotlight: four corner brackets (12 px out from the subject, 22 px arms, square caps) shown on
  the caption's window only.
- Place every beat on one master timeline with negative `animation-delay`, from the storyboard's
  percentages; the loop ends on the full overview.

## Styles

- `flat-minimal` (default): light surface, 1.5 px strokes, soft role tints; docs and teaching.
- `blueprint`: navy ground, grid, mono labels; technical documents.
- `hand-drawn-sketch`: a `feTurbulence` displacement filter on closed shapes only. A filter on a
  straight line has a zero-area box and erases the line; never filter an animated element.
- `neon-dark`: dark ground, glowing strokes; talks and dark slides.
- One palette per diagram; all text and strokes at AA contrast (4.5:1) on their background.

## Vertical 9:16

1080×1920. Readable content stays inside x 60-890, y 150-1540 (platform buttons cover the rest);
headings centre on x 540, the frame's centre. Same cast, beats and captions as landscape. Spread
rows evenly: gap = (1390 − sum of row heights) / number of gaps, at least 40 px; shrink rows, never
the gap.

## Text language

Component names and technical labels stay in English by default (they are the system's names);
captions and the explanation follow the learner's request.
