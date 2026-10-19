# Camera-Beat — the beats-mode guide

The full contract for narrated-camera diagrams: one master timeline, computed zoom, captions,
spotlight, morphs, language, reduced-motion, video export and sound. The catalog entry lives in
`data/motion.csv` (row `camera-beat`) and the library stub at `motion-recipes.md#camera-beat`;
everything below is the build-time detail. Workflow context (solution sheet → storyboard → build)
is `references/workflow-phases.md`; delivery gates are `references/pre-delivery-checklist.md`.

**The snippet is law.** This file is the prose contract; the implementation it describes is
`templates/snippets/camera-beat.css`, distilled block by cited block from the two frozen cuts the
user approved. Copy from the snippet. Where prose and snippet ever disagree, the snippet wins — it
is what shipped and what review accepted.

**Semantic.** The diagram narrates itself in timed acts ("beats"). Each beat zooms the camera to one
or a few components in story order, explains them with a world-space caption and/or an interior
detail view, then returns to the full overview. The final beat is always the overview with every
ambient motion running. Beats auto-play on an infinite loop; there is **no** scroll, click, or hover
control (locked product decision).

**Technique.** One `transform` animation on a single wrapper group. Never animate `viewBox` — that
needs JS and re-layouts every frame; `transform` on a `<g>` runs on the compositor.

**Structure.** Wrap the entire drawing (edges, nodes, packets) in one group:

```html
<svg viewBox="0 0 1800 800">
  <g class="camera">  <!-- everything zooms together -->
    ... layers ...
    <text class="beat-caption cap-b2" x="..." y="...">admits 2K/s -- the crowd waits here</text>
  </g>
</svg>
```

**The master timeline.** All beat animations (camera, captions, morphs) share ONE duration and key
off percentages of it, so they can never drift apart. Pick the master so every ambient loop divides
it: with the house ambient beat of 4800ms (dash 1200 x4, pulse 1600 x3, fill 2400 x2), any multiple
of 4800ms closes seamlessly. Example: 5 beats x 4800ms = master 24s. This holds through every
restyle: a skin that retunes a rhythm must land on a divisor (observed: two skins at 1400ms and
2000ms against a 43.2s master failed the video export's frame-0-vs-frame-end hash while every
divisor-true fork passed — SKILL.md → Restyling). The `Duration` cells in motion.csv are
STANDALONE defaults — in a free-looping diagram any duration closes on itself, so 1400ms is
legal there; under a master timeline, snap each recipe's duration to the nearest divisor before
use (1400→1200 or 1440; 2000→1920 or 2400). The export's loop-closure hash IS the check; run it
before publishing any looping video.

**Every mechanism drawn gets a beat.** If a component matters enough to draw, it matters enough to
explain; a node no beat ever visits is a node the viewer must decode alone. Budget beats from the
component count (roughly one per two components, plus overview bookends) before writing any CSS.

**Every beat contains the upstream node it receives from.** Never open a beat on a component
without its source: a beat framing only "waiting room + gateway" leaves the viewer asking what the
room is queueing *for*. Pair each component with where its traffic comes from (browsers + waiting
room; gateway + service), and let the next hop peek in at the frame's edge as a continuity cue.
The story order is the request's own path. Zoom per beat is computed, not guessed:
`k_read = P_min/fs_min` up to `k_fit` from the must-show bbox — see "Choosing k" below.

**Per-beat shape** (share of one beat): zoom-in ~12.5% (600ms), hold ~69% (3300ms), zoom-out ~12.5%
(600ms), overview breather ~6% (300ms). The hold must be long enough to read the caption.

| beat | length | why |
|---|---|---|
| opening overview | **1×** the standard beat | it is a teaser — the viewer has not been told anything yet, so there is nothing to take in |
| every working beat | **1×** | the shape above |
| **closing overview / recap** | **2×** | this is the one beat whose job is to be LOOKED AT rather than read |

**The closing overview holds twice as long as a working beat** (user decision, 2026-08-27). Every
working beat ends by throwing the viewer back to the whole picture for a breather, but the FINAL
return is not a breather — it is the beat where the parts they have just been walked through are
supposed to snap together as one diagram, and a 4.8s pass is not enough time to do that before the
loop restarts. Double it. Practically: `master = (n-1) × beat + 2 × beat` for n beats, the recap's
own caption keeps its normal pace and window (do NOT stretch the caption to fill the longer hold —
leave the tail caption-free so the viewer reads the DIAGRAM), and the extra length must not break
the divisor rule, so re-check every ambient duration against the new master and snap the ones that
no longer divide it. This applies to every genre, including a progressive tier story's final tier.
The three SYSTEM-DESIGN goldens predate the rule and are NOT to be re-cut for it; it bites from the
next cut or regeneration. First cut built to it, and now the process genre's frozen cut
(6 × 4800ms + 9600ms = 38400ms; its sticky pulse had to move 2800 → 2560ms to keep dividing).

**Caption pace: the goldens are normative — ~5 words/second.** This file used to say ~3 wps, which
no shipped cut obeys. Measured from the two user-approved goldens' own manifests (caption window ×
master duration, each manifest's `captions[].window`):

| cut | densest caption | pace |
|---|---|---|
| compare-chat-pubsub | `cap-b2`, 15 words in a 3.00s window | **5.0 wps** |
| progressive-500k-ccu | `cap-b2`, 15 words in a 2.61s window | 5.7 wps |
| progressive-500k-ccu | `cap-b5`, 19 words in a 2.73s window | 7.0 wps (outlier) |
| progressive-500k-5tier | densest caption 4.69 wps, mean 4.28 | corroborates the ceiling |

Every other golden caption sits between 2.4 and 4.0 wps. **~5 wps is the calibrated ceiling**: a
3.0s window carries about 15 words, a 3.3s hold about 16. The compare cut holds that line across
its whole run, so it is a pace real review has approved, not a target. Past it the caption is
skimmed rather than read — `cap-b5` is the one hold in either golden that pushes there, and it is
the exception that names the edge, not the budget to plan against. The rule the number serves is
unchanged and is the one to reason from: **a caption may not say more than its hold can carry.**
If it does, cut the caption — never stretch the hold, which desynchronises every downstream window.

**The world moves as one.** Everything that belongs to the scene zooms with it — including the
background grid. Draw the grid as a `<pattern>`-filled rect that is the `.camera` group's first
child, not as a CSS background on the `<svg>` element; a grid that stays fixed while nodes fly by
reads as a broken window, not a camera.

**Choosing k — compute it, do not feel it.** Two constraints bound every beat's zoom:

```
k_fit  = min( (W - 2m) / bbox_w , (H - 2m) / bbox_h )     m ~ 40 world px
k_read = P_min / fs_min
```

`bbox` is the beat's must-show set: target components + the upstream node + the caption. `fs_min`
is the smallest text this beat exists to show (a morph's code lines, the target's sub-label) in
world px, and `P_min` is the minimum legible size in FRAME px. Pick `k_read ≤ k ≤ min(k_fit, 3)`.

**`P_min` is per-format AND per-gate — it is not one constant.** 28 was calibrated on a VERTICAL
1080-wide export held at arm's length; a landscape 1920-wide frame is read further away across a
wider field, and every frozen golden lives there, so holding them to 28 would fail user-approved
work. Every hold therefore declares a `gate` in its manifest entry and the floor follows from that
gate plus the frame's format (`diagram-director/scripts/camera_text_floors.py` is the machine copy; the numbers are
the same ones):

| frame format | essential text | supporting subs | who enforces |
|---|---|---|---|
| vertical (1080-wide) | **28** frame px | 19 | `read` gate only |
| landscape (1920-wide) | **24** frame px | 17 | `read` gate only |

| hold `gate` | what is gated |
|---|---|
| `read` | the floor above is a HARD gate — the beat exists to be read |
| `territory` | containment + the pane heading only; a whole pane never fits at `k_read`, and its legibility is judged on the contact sheet, not by a node-label floor |
| `overview` | floor waived outright — "legibility is judged per territory, never on the overview" |

Only the ESSENTIAL row is machine-checked: a manifest declares one `fs_min` per hold (the smallest
essential text in that frame), so nothing in it separates a sub-label from a node label. The
supporting column is the author's target, verified by eye on the contact sheet.
`diagram-director/scripts/solve_camera.py --gate <gate>` applies this in **both** modes — `--check` against a built
cut, and plain solve when you are choosing `k` — and `diagram-director/scripts/verify_all.py` runs the check over
every declared hold. Solve mode without `--gate` knows only the flat `--pmin`, so it reports every
honest territory hold as an over-stuffed beat; under `territory`/`overview` the interval is simply
`0 ≤ k ≤ min(k_fit, 3)` and `k_read` is printed as `NOT binding`.

**If the interval is empty at a `read` gate, the beat is over-stuffed — never resolve it by zooming
out.** (At `territory` or `overview` there is no lower bound to be empty against; a whole pane that
does not fit at `k_read` is the normal case those gates exist for, not a defect.) A beat
whose text cannot be read is a beat that does not explain. Fix the geometry instead: stack the
component pair along the frame's long axis (portrait wants vertical adjacency; side-by-side pairs
bind `k_fit` to the narrow axis and strand you at k≈1.3–1.5, which review rejected as too shallow),
let the upstream node peek at ≥80% visible instead of fully framed, or split the beat. Measured on
the portrait cut: refitting per-beat bboxes plus a peeking upstream moved k from 1.3–1.5 up to
1.4–2.6 with every caption still safe.

**Camera math.** To center target `(cx, cy)` at scale `k` in a `W x H` viewBox:

```
tx = W/2 - k*cx        ty = H/2 - k*cy
transform: translate(tx px, ty px) scale(k)
```

`transform-origin: 0 0` on `.camera` is mandatory or the math is wrong. Keep `k <= 3`; past that,
strokes get thick and off-screen context loses meaning. Zoom itself is the focus device — content
outside the crop is maximally "dimmed" — so no veil/dimming layer is needed.

```css
.camera { transform-origin: 0 0; animation: beats var(--master, 24s) linear infinite; }
@keyframes beats {              /* 5 beats x 20% each; moves are 2.5% = 600ms of a 24s master */
  0%, 20%        { transform: none; animation-timing-function: ease-in-out; }
  22.5%, 36.25%  { transform: translate(-343px, -370px)  scale(2.2); animation-timing-function: ease-in-out; } /* beat 2 */
  38.75%, 40%    { transform: none; animation-timing-function: ease-in-out; }
  42.5%, 56.25%  { transform: translate(-2454px, -510px) scale(2.6); animation-timing-function: ease-in-out; } /* beat 3 */
  58.75%, 60%    { transform: none; animation-timing-function: ease-in-out; }
  62.5%, 76.25%  { transform: translate(-1000px, -797px) scale(1.9); animation-timing-function: ease-in-out; } /* beat 4 */
  78.75%, 100%   { transform: none; }   /* beat 5: finale overview, ambient runs */
}
```

**Captions.** World-space `<text>` INSIDE `.camera`, placed next to the focused component. They zoom
with the camera, which is the point: unreadable clutter at overview scale becomes readable exactly
when their beat arrives. Author them at `font-size: 24/k` user units so they render ~24px on screen
at that beat's zoom. Fade each on/off inside its own beat window on the same master duration:

Reveal each caption with a left-to-right wipe -- it pulls the eye far harder than a plain fade.
The wipe is a `clip-path` inset shrinking continuously over ~700ms (the queue-fill mechanism,
applied to text). Wrap each caption in a rounded card: a `<g class="beat-caption">` holding a
`rect` (`rx="8"`) plus the `<text>`, with the animation on the `<g>` so the wipe clips card and text
together. Size the rect from the text's **measured** `getBBox()` plus ~14x8 padding and bake the
numbers into the file -- guessed widths either clip descenders or leave lopsided margins. Colour the card by **inverting polarity**: fill `var(--ink)`, text `var(--surface)` — the caption
is the narrator's voice, not part of the scene, and the flipped card is unmissable without adding a
hue (in a monochrome style a new colour is forbidden; polarity is the legal attention lever). A
same-polarity panel (`color-mix(ink 9%, surface)`) was tried first and reviewed as too easy to miss. **Set the caption in a text face even when the style's label font is a display face.** The card
carries the longest line in the piece, at the smallest size, on screen for a few seconds — a script
or pixel face costs real legibility exactly where the viewer cannot re-read (observed: a hand-drawn
fork narrated in Caveat, reviewed as hard to read; the same line in Inter was fine). The display
face still owns the scenery labels — that is what carries the style. Widen the wipe's clip vertically (`inset(-6% ...)`) or it shaves the
card's top and bottom edges:

**The caption animates ONE property, and it is `clip-path`.** `opacity` is a constant 1 on the base
rule and never appears in a keyframe; the card is hidden by GEOMETRY at all times, at both ends of
its life, and the exit is a same-direction wipe-OUT rather than a fade. This is not a style choice —
it is the fix for a real defect. `opacity` is a **compositor** property, `clip-path` a **paint** one.
A card that spends ~30s of every loop at `opacity: 0` with its clip parked open has its raster tiles
evicted under memory pressure, and on the frame opacity leaves 0 the compositor can present the
**stale, fully-revealed tile** for one frame before the fresh clipped raster commits. Pass 1 is
always clean (no stale tile has ever existed); every pass after it can blink — which is exactly what
was reported on the process golden and diagnosed on 2026-08-27. Removing the opacity animation
removes the "becomes visible again" event the race needs. Both parked poses are **zero-area and
outside the card body** (100% past its left edge, 101% past its right), so a parked clip can never
leave an antialiased sliver, and the base `clip-path` is the closed one, so a cut whose keyframes
never apply hides every caption instead of showing them all.

```css
.beat-caption { opacity: 1; clip-path: inset(-6% 100% -6% -1%);
                animation: var(--cap) var(--master, 24s) linear infinite; }
.cap-b2 { --cap: cap-b2; }
@keyframes cap-b2 {                  /* wipe in, hold, wipe out -- clip only */
  0%, 25%      { clip-path: inset(-6% 100% -6%  -1%); animation-timing-function: ease-in-out }
  27.5%, 35%   { clip-path: inset(-6%  -1% -6%  -1%); animation-timing-function: ease-in-out }
  37%, 100%    { clip-path: inset(-6%  -1% -6% 101%) }
}
```

Three segments, six stops, emitted by `diagram-director/scripts/timeline_css_idiom.py::caption_window` from
`start / end / tail / wipe` alone. The `eps` column of the event table is a **legacy no-op**: it was
the opacity-snap epsilon of the old four-segment block and there is no opacity stop left for it to
sit before.

Copy-source with both goldens' measured numbers: `templates/snippets/camera-beat.css` →
`cb-caption-card`.

**The three SYSTEM-DESIGN goldens still ship the OLD four-segment block** (opacity 0 → snap to 1 →
hold → fade, both parked poses at the open clip). Their re-bake is a decision deferred by the user,
so `tests/run_golden_regression.py` carries a named `SD_LEGACY_CAPTION` exemption for them — which
still fails the moment it stops matching anything. Do not copy their caption keyframes into a new
cut; copy the block above. The process golden is the one that ships the current form.

**The heading is scenery — fade it out while the camera is away.** A title/subtitle line is wide;
once the camera zooms, some hold will drag it half-across the frame edge and park it there, cut
mid-word for the whole hold (observed: a subtitle sat clipped at the frame's right edge for a full
7.6s beat). Animate the heading layer's opacity on the master timeline: visible through the opening
overview, out with the first zoom-in, back with the finale return; reduced-motion keeps it visible.
Check every OTHER wide scenery line the same way at each hold — transient clipping during camera
moves is fine, a clipped hold is a defect.

**Keep the teaching line off the frame edge — M = 24 frame px.** At a beat's hold, an edge may come
within M of a frame side ONLY where the beat is genuinely heading off-frame on that side — which is
true in exactly two measurable ways: **the path CROSSES that side**, or **that side CUTS one of the
edge's own anchor stations** (*một cạnh đã cắt chính station của edge thì không nợ edge đó khoảng
thở* — the crop has already told the viewer this continues off-frame, so the hug is a consequence of
a sanctioned framing, not a hidden line; lead ruling 2026-08-27). **Every other side owes the edge
M px of clearance, measured to the path's PAINTED band, not its centreline.** Where both of an
edge's stations are fully in frame neither exemption can fire, so the whole path stays M px inside —
that is the rule's plain form. *A teaching line that hugs or exits the frame edge is invisible
exactly when it matters.* Three things make this its own rule rather than a note under the bbox:

- **No existing gate sees it.** Every camera check measures the must-show bbox a hold DECLARES, and
  an edge is in that bbox only if the author put it there. Observed on the process golden: b3's bbox
  named the return arc in its comment and stopped 26 world px above it, so the arc — the beat's
  SUBJECT, wearing its halo — ran 11.6 frame px from the frame's top (2.4 with the halo counted) with
  stage D, the solver and the anchor sweep all green, and the user reported the line as hidden.
- **The measure is PAINTED.** A halo (a second, wider path with an identical `d` — the house idiom
  for making an edge a beat's subject) is part of that edge's paint. The same golden's b3b hold
  cleared the top by 24.8 px on the centreline and by 16.0 px on the halo.
- **Crossing is read off the CENTRELINE**, never the painted band, or a fat stroke buys its own
  exemption by spilling over a side it never goes through. The clipped-anchor exemption is measured
  the same way — per (edge, side, hold), from the station's own bbox against that frame side, never
  a named allowlist — and every waiver it grants is PRINTED with the clearance it waived, because an
  exemption that fires silently is how a gate rots into a rubber stamp. A waiver is a **queued visual
  review**, not a verdict: it says the crop sanctioned the hug, not that the hug reads well.

The fix is the bbox, not the line: put the edge's painted band (and the caption card, if it was left
out too) into the hold's must-show set and re-solve. Rerouting the edge is the fallback, and only
where a corridor exists that crosses nothing. Gate: one reader per construction mode, same rule and
same M — `diagram-director/scripts/browser-checks/verify-frame-edge-margin.mjs` for HTML-mode (`process`) cuts, whose
stations are `[data-station]` divs inside a `.frame`, and
`diagram-director/scripts/browser-checks/verify-svg-frame-edge-margin.mjs` for SVG-mode (`system-design`) cuts, whose
frame is the root `<svg>` viewBox and whose stations are `g.node > .node__shape` plus the two other
things an edge may honestly terminate on, `.lane-line` lifelines and `.group__box` cluster
boundaries. `verify_all.py` picks the reader off `manifest.genre` in one stage-E slot.

**Place the card in a fixed slot inside the hold's frame — that is the house pattern.** Both
user-approved goldens do this, and they are normative: `progressive-500k-ccu` parks every caption
in one bottom band (`y=767.6` for `cap-b2..b5`), and `compare-chat-pubsub` centres each card on its
own frame's horizontal centre at the frame's lower edge. In both, the card is part of the hold's
must-show bbox (`tests/fixtures/golden-camera-holds.tsv`), so the solver frames it as content
rather than hoping it lands somewhere legal. A fixed slot is what makes captions read as one
narrator's voice instead of a label that jumps around the canvas per beat.

**The adjacency rule is the fallback, not the default.** Use it only when a fixed slot would put
the card outside its hold's frame — a tall or off-centre must-show set, a pane at the canvas edge.
Then place the card in the gap directly above or below the subject (or beside it), never a band
away: the caption and the highlight have to read as one gesture, and a card parked next to a
DIFFERENT component narrates that component instead (observed: a final beat's caption left sitting
near the store node from an earlier layout while the camera framed the reaper — the viewer pairs
the words with the wrong box). Either way, after the camera mapping the card must land inside the
platform safe rect during its own beat; if centring it would push it out, clamp it toward the safe
side and keep it touching the subject's gap.

**A caption card never covers an edge LABEL, and never covers an edge of its own beat's
SUBJECTS. It may cross other scenery.** The card is the narrator's voice laid over the picture,
so the one thing it may not do is erase the picture it is narrating. Two failures are the same
failure: a card parked on the connector the sentence names (observed on a delivered cut at four
beats, the worst of them hiding both inputs the sentence listed), and a card parked on a rendered
string until `outcomes` reads as `outc…`. Neither is a routing problem — the card is placed last,
so it is the card that moves. A lower-third over plain background is the house idiom and stays
legal: an edge the beat is not about is scenery, and crossing it is REPORTED with its measured
overlap rather than refused. Gate: `diagram-director/scripts/browser-checks/verify-caption-occlusion.mjs`, stage E,
mandatory when the manifest declares `captions` and `beats`. It measures at an instant inside the
caption's own window where the card is fully revealed, at the pose of the hold that instant falls
in, over the elements visible THERE — and it derives the beat's subjects from the beat itself: the
`g.node`/`[data-station]` boxes a lit spotlight bracket encloses, then the edges those boxes anchor.
A beat with no lit bracket (an overview) has no subject set, and the check says so per caption
instead of counting it as a pass. Fix by moving the card inside its slot, or by putting the edge's
painted band into the hold's must-show bbox and re-solving; the gate prints a dx only when it
re-measured one that clears everything and still lands inside that bbox.

**Keep the wipe continuous -- do not chop it into typewriter chunks.** Both discrete approaches
were tried and measured. `animation-timing-function: steps(n)` declared on a fractional keyframe is
silently ignored (computed `clip-path` interpolated linearly straight through it). Hand-built
staircase keyframes DO step, but coarse chunks (~80ms holds) read as stutter at 60Hz, not as typing
-- reviewed on screen and rejected. A smooth linear wipe is jank-proof at any refresh rate. The
`-1%` margins keep the first and last glyph's antialiasing clear of the clip edge.

**Interior morph (optional per beat).** The focused component crossfades from its summary face to a
detail face — e.g. a database node opening into the guard script it runs. Both faces live in the
node group; opacity swaps on the master timeline during that beat. Keep the detail face legible at
that beat's `k` (text at `17/k` user units or larger). The morph must be information, not decoration:
show the mechanism (a script, a queue's slots, a lock), never a bigger copy of the same label.

**Beat spotlight (required).** While the camera holds on a beat, the components that beat is ABOUT
light up; when the camera leaves, the light goes out. Without it, every node in the zoomed frame has
equal weight and the viewer re-derives the subject from the caption alone.

- **Subjects = the caption's subjects**, exactly. The upstream context node is in frame by rule but
  is never highlighted — the spotlight is what separates subject from scenery. A permanently-glowing
  hero node (glow budget) still gets the spotlight in its own beat; the two layers stack.
- **Overlay, not restyle.** Add a dedicated element per subject (last child of the node group so it
  inherits the translate) and animate ONLY its `opacity`; any glow lives in a static `filter` on the
  overlay's class. Never animate the node's own stroke/fill — paint properties come off the
  compositor.
- **The overlay is four corner brackets.** That is the house default in every style, not a HUD/FUI
  special case — both goldens are `flat-minimal` and both draw brackets. `stroke-linecap: square`,
  pad **12** around the subject's full visual bbox, arm **22**, four L-shaped subpaths (TL, TR, BR,
  BL). The exact `d` formula and a worked example are in `templates/snippets/camera-beat.css` →
  `cb-spotlight-bracket`; copy it rather than re-deriving it. A style whose language genuinely
  cannot carry brackets may substitute an **offset outline ring** — the only permitted alternative.
  A closed ring drawn on the node itself was reviewed and rejected.
- **Windows mirror the caption windows** on the same master duration — on as the camera arrives
  (~1.4% of master ≈ 0.6s fade), hold, off with the caption. One `@keyframes focus-bN` per beat; a
  node highlighted in several beats needs merged keyframes.
- **Merge adjacent subjects.** When two subjects sit closer than the bracket pad + arm, per-node
  brackets interlock in the gap (observed: two nodes 4px apart produced nested corner marks). Draw
  ONE overlay around the pair's union bbox — in world coordinates at the layer root, since it spans
  groups — and it may legally enclose the beat's caption card too.
- **The overlay is geometry: collision-check it.** Bracket arms are new strokes near node corners —
  re-run the edge/label clearance pass after adding them, and confirm each overlay sits fully inside
  its beat's frame. A subject's state chip is part of the subject: the overlay's box must enclose
  chip and node together (observed: a ring sized to the node alone sliced through the overload
  chip's first glyph) (`(x0..x1) = (0 - tx)/k .. (W - tx)/k`; observed: a bracket arm 5px outside the
  computed window rendered as a clipped corner).
- **Reduced-motion: overlays hidden** (`animation: none; opacity: 0`) — no camera, no lock-on.

## Scenario timeline — staged states and acts

Comparison and progressive cuts are *educational*: a beat must DEMONSTRATE the weakness — load
rises, a node saturates, it dies, the failure dominoes — not tour the layout (user direction,
2026-08-26). That demonstration is a second layer on the same master timeline. Catalog row:
`data/motion.csv → state-timeline`.

**Staged states are overlays, never mutations.** The base node stays untouched. The state's static
encoding — dashed ring, chip, fill-bar, from `data/states.csv` + `templates/snippets/state-effects.css`
— is drawn once into an overlay group whose `opacity` is keyed to a window of the master. Identical
machinery to captions and spotlights: one `@keyframes` per window, `animation-duration: var(--master)`,
`linear`, `infinite`. Animating the node's own `stroke-dasharray`/`stroke`/`fill` to "become
overloaded" takes the whole node off the compositor and re-rasters it every frame.

**The window annotation contract (single source for the verifier).** Every staged element carries
`data-window="A,B"` — A and B are percent of the master where the element is visible. An element
that returns later carries several windows, space-separated: `data-window="10,20 85,88"`. The build
generates BOTH the keyframes and the `data-window` attributes from the same storyboard table, so
they cannot drift; hand-writing either half re-opens exactly the drift the annotation exists to close.

```html
<g class="stage stage-overload" data-window="42,58">…dashed ring + chip…</g>
```
```css
.stage { opacity: 0; animation: var(--win) var(--master, 24s) linear infinite; }
.stage-overload { --win: w-overload; }
@keyframes w-overload {              /* 1.4% ≈ 0.6s crossfade at each edge */
  0%, 40.6% { opacity: 0 } 42%, 58% { opacity: 1 } 59.4%, 100% { opacity: 0 }
}
```

**State intensity is a register property.** The same `data-window` machinery renders at two
volumes, and the register picks which. In the *reference* register a state is stated quietly: chip +
dash/ring + fill bar, the poster-able form. In the *educational* register it is the full form — a
**colored replica overlay** (`templates/snippets/state-effects.css` → `state-overlay-replica`: a
copy of the node's shape filled and stroked in the state's own role tokens, living inside the state
group so the window's opacity recolors the node without ever mutating base paint), plus
`shake-stress` on overload windows, `collapse-death` played once into a down window, and the chip on
top of all of it. Nothing else changes: same windows, same annotations, same verifier. User review
(2026-08-26) rejected the quiet form in an educational cut as "too gentle" — if the cut exists to
show a thing breaking, the break has to be visible from across the room.

**Act title cards.** Each act opens with a display-size title card — the act's title plus its
load-band sub, both strings from the sheet — staged on the act's own window and positioned in the
layout's title band. It is scenery, so the style's display treatment is allowed here even where
captions are forbidden it (a caption is the narrator's voice at the smallest size on screen; a title
is a chapter heading). Small per-act corner labels were tried first and reviewed as too weak to
mark a scene change.

**Domino.** Ordered `is-down` onsets plus `error-propagation` / `flow-broken` on the causal edges
*between* them; each onset is its own window, opening after its upstream one by that edge's
propagation time. The sheet's event table — `time% | subject | transition | caption claim` — is the
single source for every window, every state and every caption in the cut.

**Acts (temporal tiers).** An act is a scene group `<g class="act" data-act="N" data-window="A,B">`
that owns the WHOLE canvas. The canvas "clears" between acts by window handoff (≈0.6s crossfade),
not by moving anything. Layout is free per act — an act is a fresh drawing of the system at that
stage of the story. Continuity: a component alive across acts keeps its identity (shape, role
colour, label) and anchors NEAR its previous position, so the eye reads growth rather than meeting
strangers; each act's NEW components take the accent on entry.

**Node identity across acts.** Every node group inside an act carries `data-node-id` — kebab-case,
unique in its act, identical in every act the component survives. It is what makes the continuity
sentence above checkable rather than merely true: see `references/output-manifest.md` → *Node
identity and the act delta*, where the delta each act declares (`added`/`removed`/`changed`) is
cross-checked against the id sets the DOM actually draws.

**The anchor hold.** Before an act crossfade, hold on a node that exists in BOTH acts — a `read`-gate
hold on the shared anchor, preferring the last active beat's subject. The crossfade then changes the
system around a fixed point instead of replacing the frame. The manifest carries `anchor:
"<node-id>"` on that hold and `acts/anchor-not-shared` fails when the id is missing from either act.
Carve the window out of the OUTGOING beat's tail rather than adding time to the master — an anchor
hold that lengthens the film to add a comma has re-cut it.

**And end the anchor hold before the incoming act un-parks.** This is the recap-hold rule again, and
it bit on the five-tier re-freeze: the hold was first written across the crossfade itself
(40.4167–41.6667%), where act 3 is still at full opacity and act 4 has already snapped back on
canvas. Its midpoint therefore had 45 ink texts and 23 segments in frame instead of 19 and 9, and
`verify-hold-geometry.mjs` reported act 3's write edge passing through act 4's `catalog-svc` — a
defect that is not on screen at any instant a viewer sees. The window was re-cut to
39.1667–40.4067%, the last instant act 4 is still parked off-canvas, and the reading was clean.
A hold's midpoint is a place two checks and one contact-sheet frame stand: it has to be an instant
with one act in it.

**The role-lens beat.** A role-lens beat answers one question — how do these two roles talk? Declare
`lens: [roleA, roleB]` on the spotlight hold. Every node outside those roles goes `.is-idle`;
dash-flow runs only on edges whose endpoints span the two roles. Nothing else moves; a lens that
animates a third role is teaching a different lesson than the one it announced. Edge contract: in a
`role-lens` cut, every `path.edge` carries `data-from`/`data-to` node ids, so the gate reads the
graph out of the file with no browser.

**Recap.** Each act group gets one extra short window (~3s) near the end, in act order, with the
camera holding the overview — the story replayed as a contact sheet. The FINAL act's last window
runs to 100%, so the loop parks on the finished design rather than on a fade.

**ONE CAMERA HOLD PER BEAT — never one hold per act.** A beat is a caption plus the spotlight set
it names; an act may contain several. Even when the camera does not move between them, declare one
hold per beat, each ending where the next begins. The reason is mechanical, not aesthetic: a hold
spanning two beats puts its own MIDPOINT between them, and the midpoint is exactly what the two
render-side checks read — `verify-hold-geometry.mjs` measures the frame there, and the contact sheet
shoots its frame there. A spanning hold therefore reports and photographs an instant no beat owns.
Observed in the five-tier golden's build: with a single `a4` hold, its midpoint (48.5%) fell 1.9%
before the T4 end-of-act seed's window, so the `HOT ROW` + `2K WPS` payoff never appeared on the
contact sheet at all — the reviewer was shown a frame in which the act's own argument had not
happened yet. Splitting `a4` into `a4a`/`a4b` at the same transform fixed it and changed nothing on
screen. The recap's `r1..rN` rule (`references/output-manifest.md`) is this same rule applied to
the replay windows, not a separate one. Several holds may declare the SAME `k/tx/ty`; that is
normal and is what a static camera across an act looks like in the manifest.

**Motion under a moving camera: a `filter` in a state row's Motion Ref must be substituted.** The
camera animates `scale()`, so a filtered raster can never be reused between frames (SKILL.md →
Output Rules). Several `data/motion.csv` rows are `Technique: opacity-filter` and put a
`drop-shadow` in their snippet — `pulse-glow` and `leader-election-pulse` are the ones state rows
reach for. When such a row is the Motion Ref of a state that plays under a moving camera, keep the
row's SEMANTIC (rhythm, duration, easing, reduced-motion cell) and drop the filter: animate opacity
only. `motion.csv` ships no opacity-only pulse row today, so the documented substitute is the
inline **ring-pulse** pattern the five-tier golden uses — a static ring/overlay element on the
subject whose `opacity` alone breathes on the row's own duration, the same overlay discipline the
spotlight bullets above already require. **The solution sheet records the substitution** (which row,
which filter, what replaced it, and that the row's reduced-motion cell is still satisfied) — it is a
deviation from a dataset cell, and every deviation is stated.

**Springs.** `templates/snippets/motion-blocks.css` → snippet `spring-easing-tokens` ships three
generated `linear()` timing functions — `--ease-spring-soft` (ζ=1.0, no overshoot),
`--ease-spring-snappy` (ζ=0.6, one ~9.5% overshoot), `--ease-spring-bouncy` (ζ=0.35, +31% then
−9.5% then +3%). They are **vocabulary, not a default**: `motion.csv` names one only on
`scale-out-spawn`, and the `camera-beat` row still reads *ease-in-out on the move segments, linear
master*.

ALLOWED — one-shot settles that ARRIVE somewhere and stop: a spawn, a node promote, a chip landing,
a state-overlay entrance, and **a camera move that pushes IN to a hold**. Tested on the five-tier
golden (`scratchpad/spring-easing/`, 2026-08-26): `spring-snappy` on the two push-in segments
(intro→a1 and a4→a5) swings the frame ~9.5% of the move's own delta past the mark — at a5 that is
scale 1.8083 → 1.8525 and ~53px of translate — and recovers inside the same 600ms segment. It reads
as a camera that *lands* rather than glides to a halt.

BANNED, no exceptions:
- **Looping ambients.** dash-flow, pulse-glow, queue-fill, heartbeat, shake-stress — an overshoot
  that repeats every cycle is not physics, it is a wobble, and the eye starts tracking the wobble
  instead of the flow.
- **The master timeline.** `.camera{animation:beats var(--master) linear infinite}` stays `linear`.
  The whole contract is that a beat percentage IS a time; a spring on the master breaks that and
  every caption, morph and window silently desynchronises.
- **Reduced motion.** Springs are removed there, like all motion. The reduced block already kills
  every class a spring may legally sit on; the `.ease-spring-*` rules add a belt-and-braces
  `animation-timing-function: linear !important`.
- **Camera moves that pull BACK.** Overshooting a zoom-out means momentarily showing *wider than
  the overview* — the frame appears to recoil. Keep `ease-in-out` on every return-to-overview
  segment. The golden's A/B left all three pull-backs untouched for exactly this reason.

Register: reference cuts use **soft or snappy only** — soft is the safe default for a camera
arrival (critically damped, zero frame swing, still a better arrival than `ease-in-out`), snappy is
the deliberate punch, at most one hero beat per cut. **`bouncy` is educational register only** —
state-overlay entrances in a teaching cut, where the point is that a thing *arrived and it matters*.
Never bouncy on the camera: at +31% of a zoom delta the frame visibly bounces.

**Two mechanical facts before you paste one in.** (1) `var()` is NOT substituted for
`animation-timing-function` inside `@keyframes` — measured on Chrome 148, it silently falls back to
the animation's own easing. Per-segment camera easing lives inside `@keyframes beats`, so a spring
there must be the **literal `linear(...)` string**, pasted from
`python3 diagram-director/scripts/generate_spring_easing.py --presets`. In a normal rule (including the `animation`
shorthand) `var(--ease-spring-snappy, ease-out)` resolves fine. (2) The seam and the gates are
untouched by a spring: easing changes only the interior of a segment, never a keyframe's value, so
`t=0` and `t=MASTER` stay byte-identical (verified) and every hold transform the camera gate reads
is unchanged. Transient tightening during the overshoot is a *move*, not a hold — the containment
floors are measured at holds and stay valid.

**Reduced-motion.** ONLY the final act is visible, its components at their resting states. The
informative end state is the finished architecture — never a frozen montage of every act at once,
and never a mid-cascade freeze.

**Register note.** The *reference* register is spatial: all tiers or panes visible at once,
poster-able (`references/multi-pane.md`). The *educational* register is this scenario machinery.
`comparison` and `scaling-story` default to educational when the user asks to explain, teach, or
show what breaks; pick spatial when the artefact must be readable as a still.

**All animation-delays in a looping cut are NEGATIVE.** A positive `animation-delay` leaves its
element un-animated at t=0 — parked at the keyframes' offset-0 pose — while at t=100% the same
element is mid-flight, so the loop seam is not byte-identical and the frame-0-vs-frame-end hash
fails. The negative equivalent (`-600ms` for `600ms`) produces the identical steady state with the
seam closed. Caught independently on both educational builds (2026-08-26) — the progressive cut and
the comparison cut — which is why it is a rule and not a note.

**Hard gates.** Per-window visibility, per-act isolation, recap order and the reduced-motion
final-act rule are all checked by `diagram-director/scripts/browser-checks/verify-staged-windows.mjs` (plain,
`--acts`, `--reduced-motion`). It fails on zero annotated elements — an un-annotated staged cut is
an unverified one.

**Do not hand-compute the percents on this page.** Two stdlib emitters do the arithmetic, and the
sheet stays the source of truth for every row they read:

- `diagram-director/scripts/emit_timeline.py` turns the event table into `@keyframes` + `animation-name` +
  `data-window` values (state / spotlight / traffic windows, act windows with their park pose and
  loop seam, caption wipes) and the manifest's `holds`/`captions` fragment. It is an emitter, not a
  compiler: a missing element, caption or window is a refusal, never a default.
- `diagram-director/scripts/solve_camera.py` turns a beat's must-show bbox into `k`, `tx`, `ty` by the formulas
  above, and its `--check` mode says whether an existing transform still frames its bbox and meets
  the text floor.

Both are regression-locked against the four frozen goldens by `tests/run_golden_regression.py`,
which re-derives every window and transform they ship and fails on any drift. Two named
exemptions cover the SHAPE half of that diff and nothing else — `PROCESS_OWN_IDIOM` (`lod-`, the
process golden's custom-property LOD ramp, still owed an engine pass) and `SD_LEGACY_CAPTION`
(`cap-`, the three system-design goldens' pre-2026-08-27 caption block, re-bake deferred by the
user). Both are spelt out in that file with their reason and date, both fail if they stop matching
anything, and every other row — including all seven of the process golden's captions, which the
emitter now reproduces stop-for-stop — is guarded unexempted.
A rounded percent fed back into another sum is exactly how window drift starts, and a measured
~5% miss on `k`/`tx` is why the second script exists.

**Every stop is an instant the manifest names.** A duration that divides the master says nothing
about where the stops INSIDE it land, and a HAND-AUTHORED block — one no event-table row re-derives —
keeps its literal percentages through a retiming. Observed: the process golden's 33.6s→38.4s re-bake
left `br-back`, `br-ok` and `pull-park` on the old scale; every duration still divided the master and
only a pixel diff caught it. So every stop of a hand-authored master-length `@keyframes` must land
on an instant the manifest already declares — a beat boundary (`target.beat_ms`) or a window edge of
some hold or caption — within 0.01 pp, which is the emitter's own 4dp rounding and nothing more.
Gate: `verify_all.py` stage B `keyframe-grid`, implemented in `diagram-director/scripts/verify_keyframe_grid.py`,
whose named exemptions (`OFF_GRID_EXEMPT`) carry their reason the way `run_golden_regression.py`'s do.

**The manifest describes the camera the page RUNS.** Stage D re-solves the holds without opening a
browser, stage E pins the hold's transform before it measures, and the regression reads the HTML
with a regex — so a cut whose `@keyframes beats` had been killed by a stray comment once printed a
full green board with no camera motion at all. At each hold the LIVE computed transform of `.camera`
is read BEFORE anything is pinned and must be that hold's own `k/tx/ty`; `transform:none` is the
identity, which is why the rule needs two holds with different poses to mean anything. Gate:
`diagram-director/scripts/browser-checks/verify-camera-live.mjs`, genre-neutral, stage E.

**Territory beats (multi-pane).** In a comparison or progressive-tiers cut
(`references/multi-pane.md`), beat targets may be whole territories — a pane or a load tier —
instead of component sets. The frame math is unchanged: per-territory fit uses the same
k_read/k_fit computation against the territory's bounding box. What such a beat is gated on is
`gate: territory` (see "P_min is per-format AND per-gate" above): the territory must be CONTAINED
in its frame and its pane heading must read — the node-label floor does not apply, because a whole
pane at `k_read` does not fit a frame, and the frozen goldens frame their panes at a constant k
below it. The overview beat's zoom may sit far outside previous norms (five stacked tiers zoom out
a long way) — that is accepted; legibility is judged per territory, never on the overview. Spotlight and caption rules apply within each territory exactly as they do in a
single-scene cut.

**Opening title beat (`t0`) — the scene behind frosted glass.** When a cut is headed for video and
needs a title, the title is its own beat at the very start, not a line squeezed above the diagram:
the whole scene sits behind a frosted pane, the title stands in one card at the centre of the
frame, and after ~2 s the pane clears onto the first overview. The rules, each learned on a
reviewed cut:

- **It is there at t=0.** Blur, wash and the fully revealed card are already on in frame 0 — no
  ramp-up. A ramp exists only to keep a WEB loop seamless (the last act must hand over to the first
  under the pane), and it spends the first second of a video on nothing. A cut with a title beat
  therefore leaves its **loop seam deliberately open**: frame 0 ≠ frame end, the loop hard-cuts
  back to the title, which is a legitimate cut. Record that in the sheet's DEVIATIONS, light the
  FIRST act from 0% (no `seam` on the last act), and export without any head trim.
- **Slot = half a beat (2400 ms on the 4800 ms house beat):** 0–2000 ms the card holds, 2000–2400 ms
  the card wipes out while blur and wash clear together, then the first overview beat starts sharp.
  The master stops being a multiple of the beat, so `target.beat_ms` becomes the half beat
  (`validate_manifest` wants `beat_ms | master_ms`); every ambient duration must still divide the
  new master, and event-table endpoints are written in ms once two slot lengths share a table.
- **Frosted glass, not a white-out — blur for SHAPE, saturate for COLOUR, a light wash for
  contrast.** The viewer must not be able to tell what is behind the pane: no box, row, lane or
  line may be recognisable (the test: if the cards of a row can be counted or the spine can be
  traced, it fails). But the pane must still read as GLASS: colour survives as soft, shapeless
  clouds. It takes THREE terms, because on a mostly-paper canvas the pale role fills average away
  to nothing under a big radius — measured on a reviewed cut, `blur(90px)` + wash .35 left a max
  chroma of 12/255: a flat white sheet, the very thing the blur was meant to avoid. So: a large
  radius destroys the structure, `saturate()` gives the colour back, and the wash only has to take
  the contrast down. Reviewed and rejected on the way: `blur(14px)` + wash .45 (a readable
  diagram), `blur(60px)` + wash .80 (hidden, but by whitening — reads as a pale sheet),
  `blur(70px) saturate(4.5)` + wash .22 (richest colour, but the spine could be traced). Accepted:
  **`filter: blur(130px) saturate(6)` with a `var(--surface)` wash at `fill-opacity: .20`** (max
  chroma ~53/255). Tune on the frame and MEASURE chroma rather than eyeballing white. Check the
  four frame edges at 0 ms for the filter region's rectangular cut-off (Chrome's CSS filter extends
  the region with the radius; an SVG `<filter>` region would not). Both terms interpolate to
  `none` through their identities, so the dissolve stays a smooth reveal.
- **Where the blur lives — and it must survive WebKit.** Safari does NOT apply CSS `filter:`
  functions (`blur()`, `saturate()`) to elements INSIDE an `<svg>`; it honours them on HTML elements
  and on the root `<svg>` only. Chrome renders them, and every gate, the contact sheet and the MP4
  exporter run Chrome — so a CSS-filter pane passes every check and shows NOTHING to a reviewer on
  Safari (observed: three review rounds asking for "more blur" on a pane whose blur had never
  rendered for the viewer). So the pane is built from a NATIVE SVG filter and no animated filter:
  a `<filter>` in `<defs>` (`feGaussianBlur` + `feColorMatrix type="saturate"`,
  `filterUnits="userSpaceOnUse"` with a region larger than the frame so no rectangular cut-off
  shows) applied by ATTRIBUTE to a dedicated static backdrop group that holds a text-free
  impression of the first act (one shape per node in its role tokens, the main lines) — no
  `data-node-id`, no `node`/`edge` classes, `aria-hidden`, so identity, containment and legend
  gates never see it. Only OPACITY is animated: backdrop + wash at 1 through the hold, then a
  cross-dissolve with the real scene; outside the slot the backdrop is PARKED off-canvas like a
  hidden act, so a filtered raster is never composited under the moving camera. The real scene
  carries no filter at any time. Grep the built file: no CSS `filter:` with `blur(`/`saturate(`
  and no `backdrop-filter`. **Review a cut in the browser its reviewer uses** before calling a
  visual effect done.
- **The title card** is a `.beat-caption` like any other (so the caption gates cover it and its
  string is in `captions[]`), set at display size in the text face: a smaller EYEBROW line over the
  display line (~0.65–0.7 of it, never under 44 frame px in 9:16), centred on the FRAME, keywords
  in the role accent and the rest in paper — emphasis, not meaning, and the accent must clear 4.5:1
  on the card as actually rendered (`.caption-box` is `opacity:.97`). **Padding is display padding:**
  ≥ 48 frame px left/right and ≥ 32 top/bottom measured on the text's INK (stacked Vietnamese
  diacritics raise the ink top). `rebake-caption-boxes.mjs` pads 14x8, which is right for a 15px
  caption and leaves a display line touching the card's edge — so the generator re-pads THIS card
  from the measured text box in a post-step after the re-bake, and marks the rect so a later
  re-bake leaves it alone. The join between the two lines rides a zero-size tspan so `textContent`
  is the manifest string while neither centred line is pushed off centre.
- **Nothing readable under the pane, and the title only once.** The heading layer is hidden while
  the card is up (the title must not be on screen twice), and edge labels take a window that opens
  when the slot ends — under the blur they are unreadable anyway, and it is the honest way to keep
  `caption-occlusion` green (never exempt the gate). Crossing blurred edges is scenery: warnings.
- **Reduced motion:** no blur, no wash, no card — the informative end state is unchanged.
- One `overview` camera hold over the card's 0–2000 ms, so the contact-sheet midpoint shows pane
  and card together. Frames to look at before delivery: 0, 1000, ~2200 (mid-dissolve: it must read
  as a reveal, not a pop) and the slot's end (sharp, heading on, labels back).

**Language.** Captions default to English. When the user asks for Vietnamese, keep `Inter` (its
Google Fonts build covers Vietnamese diacritics) or switch the caption face to `"Be Vietnam Pro"`
(`family=Be+Vietnam+Pro:wght@400;500;600`), and re-check caption widths — Vietnamese runs ~15-20%
longer than English for the same content.

**Reduced-motion fallback.** Camera parked at the overview (`transform: none`), captions hidden,
every ambient motion at its own end state. The narration must not be motion-only: the `<desc>`
carries the full beat-by-beat story for assistive tech, and each beat's key fact should also exist
statically (a node sub-label, an edge label) somewhere in the diagram.

**Video export.** Beats map 1:1 to video chapters. The deterministic frame exporter seeks the
master timeline like any other animation, with ONE addition: seek once through the deepest zoom and
back **before capturing frame 0**. Chrome's raster scale for a composited layer is history-dependent
-- a pristine layer and one that has been through a zoom re-raster differently at scale 1 (measured:
~1200px of sub-pixel drift between the two regimes; two post-zoom captures of the same instant were
identical). Without the warm-up, the loop point carries a one-frame shimmer. For shorts, budget beats to the
platform window: 4-6 beats x 4.8s lands in the 19-29s sweet spot.

**Sound (video export only).** The page itself stays silent — autoplay policies demand a user
gesture and the product is non-interactive, so audio belongs to the exported video. Because the
timeline is deterministic, cues are placed by arithmetic: a quiet tonal sweep at each camera move
(rising 180→320Hz on zoom-in at ~-28 dBFS, descending on zoom-out at ~-30 dBFS) and a short
woodblock-style tick (~1320Hz, dead in ~35ms, ~-30 dBFS) each time the packet lands on its
component, once per ambient cycle. Noise-based whooshes were tried and rejected as harsh — tonal
sweeps sit under content, noise fights it. Keep every generator at a true ±1 amplitude so the dB
gains mean what they say; normalize to a -6 dBFS ceiling (never boost) and mux with `-c:v copy` so
the video is not re-encoded. Texture, never foreground: if the sound is noticeable on first watch,
it is too loud — the reviewed mix peaks at -28 dBFS.

**Don't.** No playback controls of any kind. No beat that zooms past `k = 3`. No caption longer
than its hold can carry. No master duration that is not a multiple of every ambient loop in the file
— the loop will visibly jump.

## Portrait (9:16) derived cuts — verticalizing a landscape cut

A portrait cut is a **geometry + camera re-solve, not a re-authoring**:
the percent grid (windows, act/stage/focus/caption keyframe stops), every string, the staged-state
markup and the palette carry over verbatim, and the cut's sheet names the landscape sheet as the
string/timing authority and logs deltas only. Apply these measured rules:

- **Re-stack, don't crop.** A landscape flow spans ~1150 world px; fitting that into a 1080-wide
  frame lands k≈0.87 and essential text ~11 frame px — nothing survives the vertical `read` floor
  (28). Stack the flow top→bottom (users → edge/LB → services → data; async branches sideways),
  re-path every edge/packet/bracket, then solve every hold at `--viewport 1080x1920` — the floors
  switch by the frame's own aspect. Measured: every pose came out width-bound, k 1.4085–2.0833 vs
  the landscape's 1.3431–1.8083, inside the 1.4–2.6 the portrait note above predicts.
- **Chips leave the entry side.** In portrait a store is entered from directly above, so a
  landscape chip above the store may occupy the edge landing zone. Move the chip below the
  cylinder or to another side with explicit connector clearance.
- **Chrome: compact legend, highlighted load numbers.** A landscape legend rarely fits unchanged
  in a 1080-wide frame. Reflow or compress it while preserving every role/flow distinction required
  by the legend gate. Load-number accents must come from the current palette and independently clear
  4.5:1 against the selected canvas; never copy a measured color from another style.
- **Page sizing is `svg{width:min(100vw,1080px)}`, not an aspect-fit vh rule.**
  `verify-glyph-label-gap.mjs` measures SCREEN px without setting a viewport; an aspect-fit
  9:16 page renders ~337px wide in its 800×600 browser and honest art fails at 2.5px gaps.
- **Retime = a master change, never a grid change.** Pacing feedback ("beats too short") is
  answered by scaling the master on the untouched percent grid. The new master must remain a
  common multiple of every fixed ambient duration — packets keep their own tempo; only holds,
  pans and caption wipes lengthen.
- **Paint order is invisible to structural gates.** A stress replica painted AFTER the node text can
  erase the label exactly during the beat the camera holds on. The replica sits UNDER the node's
  own text (DOM: replica group before the label). Inspect every hold in the mandatory browser
  contact sheet; inspect the finished MP4 additionally when a video export is delivered.
