# Pre-Delivery Checklist

Run every one of these checks before handing a generated diagram to the user. This is a gate,
not a suggestion.

## Run the runner first

```bash
python3 diagram-director/scripts/verify_all.py <cut>.html --serve            # --target local for a CDN cut
node diagram-director/scripts/browser-checks/contact-sheet.mjs http://127.0.0.1:<port>/<cut>.html \
     --manifest <cut>.manifest.json --out <dir>             # then LOOK at the sheet
```

`verify_all.py` runs the mechanical half of this list in one pass and prints a stage table
(exit `0` all green, `1` a failure, `3` the render-side stages could not run — an UNVERIFIED
cut, which the delivery message must say). It reads the cut's `<cut>.manifest.json`
(`references/output-manifest.md`) to decide which checks are mandatory: a feature the manifest
DECLARES that renders empty is a hard fail; one it never declared prints `N-A`.

| Item | Mechanised by |
|---|---|
| 3 ARIA & semantic structure | stage B `aria` (presence); the accessible NAMES stay an eye check |
| 5 runtime matches target | stage B `external-hosts` |
| 7 edge anchors | `diagram-director/scripts/verify_edge_anchors.py`, stage C `text-containment` |
| 7 text inside its component | stage C `text-containment`, stage E `hold-geometry` |
| 7 nothing crosses anything | stage E `hold-geometry` — **straight segments only; curves are item 18** |
| 9 60fps discipline | stage B `animation-props` |
| 7 the caption card vs the scene under it | stage E `caption-occlusion` — a card never covers an edge LABEL or an edge of its own beat's subjects (mandatory when the manifest declares `captions` AND `beats`); a card over other scenery is a printed WARNING, never a failure |
| 12 measure ink, not the font box | stage E `hold-geometry` (ink-vertical, at every declared hold); stage C `glyph-label-gap` (the badge-vs-label gap, on ink since 2026-09-21); both read the one measurement in `browser-checks/ink-box.mjs` |
| 13 restyled fork re-passes | stage C `caption-boxes`, `glyph-label-gap`, `text-containment` |
| — a node that draws a badge owes its label clearance | stage C `glyph-label-gap`, mandatory when the FILE draws a `.node__icon` inside a `g.node` — DOM evidence, like `node-identity`, not only the `payload-glyphs` feature |
| 14 multi-pane territory frames | stage D `camera` (containment + the per-gate text floor) |
| 15 staged-window checks | stage C `staged-windows` in all three modes |
| 15 the camera the page runs | stage E `camera-live` — the live computed `.camera` transform at each hold, read BEFORE stage E pins it |
| 17 no console errors | stage C `console-clean` |
| — camera-beat divisor rule | stage B `master-divisors` (every animation-duration divides the master) + `keyframe-grid` (the STOPS inside those durations: every hand-authored master-length stop is an instant the manifest names) |
| — manifest shape and source ids | stage A `validate` |
| — the cut declares its own graph | stage B `tier-identity` — every `g.node` carries `data-node-id`, every `path.edge` carries `data-from`/`data-to` resolving to ids in the file |
| — fix-by-deletion | stage A `shrink` — `features`/`holds[].id` may not shrink vs the committed manifest without a dated AMENDMENT in the sheet naming each removed item |

**Repair is bounded.** Count objective errors (`python3 diagram-director/scripts/verify_all.py <cut>.html --serve
--json` → `diagnostics` with `"severity": "error"`). Continue only while that count reaches a NEW
MINIMUM. Two consecutive rounds without a new minimum → stop and report truthfully what still
fails. A verify that passes FREEZES the cut: no further edits without re-running the whole runner.
The rule is a monotone-improvement condition, not a round budget — three rounds that each remove a
defect are fine; two that do not are the signal that the approach, not the edit, is wrong.

**The cut declares its own graph.** Every `g.node` carries a kebab-case `data-node-id`, unique and
stable inside the file, and every `path.edge` carries `data-from`/`data-to` naming ids that exist in
it: no `g.node` without one and no `path.edge` missing an endpoint. Without them a gate can measure
shapes and text but never the GRAPH, so nothing can compare what the cut draws with what its
manifest claims — and a cut with acts builds its whole delta on top of these ids
(`references/output-manifest.md` → Node identity and the act delta).

**Deleting a declaration is not a repair.** Dropping a `features` entry or a hold turns a FAIL into
an `N-A` while the cut keeps the defect, so stage A refuses a manifest that shrank against HEAD
without a dated `## AMENDMENT` in the sheet naming what went (`references/output-manifest.md` →
Governance). Same for a `supportedFixes` line the runner solved for you: paste the numbers, re-run,
and let the gate say so — a fix is proven by re-running, never by reasoning about it.

**Items 1, 2, 4, 6, 8, 10, 11, 16 and 18 are NOT mechanised and never will be.** Nothing measures
whether a label is TRUE, whether the presentation is the style's idiom or a re-derivation from
memory, or whether a persona's naive question has an answer on screen. A green runner is the
floor, not the delivery.

1. **Reduced-motion renders the informative end state.** A `@media (prefers-reduced-motion: reduce)`
   block exists and neutralizes *every* `animation`/`transition` declared elsewhere in the file. The
   result is the diagram's resting, meaningful state (solid strokes, packets parked at destination,
   queues shown at their current fill level) — never a mid-animation freeze frame.

2. **Contrast is AA (≥4.5:1) for all text and for stroke-vs-background.** `data/color-semantics.csv`
   rows are pre-verified by `validate_csv.py`, so using an unmodified palette row is safe. If you
   introduced any custom color (a one-off accent, a gradient stop, a glow tint), check it yourself —
   it did not go through the validator.

3. **ARIA and semantic structure are present.** Every `<svg>` root has `role="img"` plus a `<title>`
   and `<desc>` describing what the diagram shows. Every node group carries an accessible name — a
   `<title>` as its first child (the convention every shipped base template uses) or an `aria-label`
   attribute, not both on the same element. A visible legend maps colors/shapes to their meaning —
   except in a deliberately monochrome style (`hud-monochrome`), where colour encodes no role and a
   colour legend would explain nothing; there the labels and status chips must carry role instead.

4. **No color-only or motion-only encoding.** Every piece of meaning carried by color (role, status,
   severity) is also carried by a label, icon, or line style. Every piece of meaning carried by motion
   (active vs. idle, hit vs. miss) has a static equivalent visible when reduced-motion is active.

5. **Runtime matches the declared target.**
   - `--target artifact`: zero external `<script>` tags and no CDN assets. Zero `needs-js` motion
     techniques. Zero styles whose `Runtime` column is `needs-js` (e.g. no `hand-drawn-sketch` via
     rough.js — use its css-only `feTurbulence`/`feDisplacementMap` fallback instead). A Google Fonts
     `<link>` **is** allowed and expected: `fonts.googleapis.com` / `fonts.gstatic.com` are the sole
     hosts the Artifact sandbox permits. Every font still needs a real fallback stack behind it.
   - `--target local`: CDN `<script>` tags are allowed but must match the exact package/version named
     in `references/style-guides.md` (e.g. `roughjs@4`) — don't substitute an unverified CDN URL.

6. **No `planned`-style template cited.** If `styles.csv → Template Status` for the chosen style is
   `planned`, the delivered diagram was composed from `templates/snippets/` + the style's token/
   rendering rules in `style-guides.md`, and the response does not claim a base template file exists
   for that style.

7. **Layout geometry: node count, clearance, and collisions.** There is no auto-layout solver, so
   every coordinate is a decision you have to check.
   - **Count.** Actual node count is inside the chosen `layouts.csv → Node Count Sweet Spot`, and ≤20
     total regardless of the layout's stated ceiling. The sweet spot is **advisory** — guidance for
     the default case, not a gate. A tier or pane that passes the hard gates (containment at its
     hold, the per-gate text floor, clearance) may exceed it when the storyboard demands; the
     solution sheet must then say why. The ≤20 total and the clearance floor below are NOT advisory.
   - **Clearance — too close is a defect even when nothing overlaps.** Use the chosen layout's
     `Spacing Rules` as the target; they are quoted at a nominal 160×80 node and leave ~60px clear
     between node edges (`layered-lr` column gap 220 = 160 node + 60 clear; `swimlane` says so
     outright; `tree-hierarchy` sibling gap 60). If you resize nodes, scale the gap: the hard floor is
     **half the node's shorter side, and never below 40px**. Below that, adjacent nodes read as one
     block and edge labels have nowhere to sit.
   - **Text stays inside its component.** Every label, sub-label and count inside a node keeps
     ≥6px clearance to the shape's border, measured at the text's OWN y-band — hexagons, cylinders
     and clouds narrow away from their midline, so the widest point proves nothing. Re-measure after
     ANY font change: switching a sub-label to mono widens it ~20% and pushed one straight through a
     hexagon's slanted side (observed). Measure with `getBBox()` per text vs its shape; do not
     eyeball it.
   - **Every gap earns its label.** A label placed in a gap must fit inside it without touching either
     node. If it does not fit, shorten it, or move it outside the node band — do not let it ride on
     top of a node.
   - **Every edge head and tail anchors on a node — run the checker, don't eyeball.**
     `python3 diagram-director/scripts/verify_edge_anchors.py <file.html>` walks every `path.edge` and fails if
     either endpoint sits more than 12px off every node box (observed failure: an async edge whose
     first point floated 20px past its node's corner). Flat translate() diagrams only — rotated,
     panel-wrapped and `<pre>`-rendered styles are skipped with a note; check those in the browser.
   - **An edge attaches to the node side that FACES its far endpoint — never wrapping round to an
     adjacent side, and never landing a hair off a corner.** The same checker enforces it (a
     landing exactly ON a corner is legal, which is what a true diagonal needs). Anchoring alone
     cannot see this class: the endpoint is genuinely on the node box, so it passes every geometry
     sweep and still reads as a connector that missed its target (user-caught in the five-tier
     golden: the `enqueue` run arrived from the RIGHT and landed mid-way across the queue's TOP
     border).
   - **Nothing crosses anything.** No edge passes through an unrelated node, and no edge passes
     through *any* text. Two edges heading the same way are nested, not crossed. Verify the return/
     response paths especially: they are the ones that get routed back across the whole diagram.
   - **No edge hugs the FRAME edge at a hold — 24 frame px, measured on the painted band.** Clearance
     to other nodes is only half of it: a beats cut crops the world per beat, and an edge can be
     legally routed, correctly anchored, inside every declared bbox, and still run two pixels inside
     the crop. An edge may approach a frame side only where the beat genuinely leaves the frame
     there — the path CROSSES that side, or that side CUTS one of the edge's own anchor stations
     (*một cạnh đã cắt chính station của edge thì không nợ edge đó khoảng thở*). Every other side
     owes it 24 px, and a halo counts as part of the edge's paint. Each clipped-anchor waiver is
     printed by the gate: read them, they are queued visual review, not a verdict. Rule:
     `references/camera-beat.md` → "Keep the teaching line off the frame edge".
     Gate: stage E `frame-edge-margin`, one reader per construction mode and the same rule in both —
     `verify-frame-edge-margin.mjs` on `process` cuts, `verify-svg-frame-edge-margin.mjs` on
     `system-design` cuts; `verify_all.py` picks by `manifest.genre`. Observed: a return arc at 2.4 px
     from the frame top, reported by the user, green on every other gate.
   - **Confirm by rendering, not by arithmetic.** Coordinate math and bounding-box checks both pass on
     layouts that are visibly broken — a line running straight through a label is legal geometry.
     Screenshot the result and look at it.

8. **Motion budget respected.** The primary flow path is animated; secondary/incidental edges are
   static. Animated edge count does not exceed 12 (`MAX_ANIMATED_EDGES`). That ceiling is about
   readability, not frame rate — measurement found 120 animated edges still running at a locked
   60fps, so trim competing motion because it distracts, not because it is slow.

9. **60fps discipline.** Every animated property is one of `transform`, `opacity`, `clip-path`,
   `stroke-dashoffset`, `offset-distance` (or `filter`/`backdrop-filter` used sparingly per
   `style-guides.md`). No animation targets `width`, `height`, `top`, or `left` — those trigger
   layout/paint on every frame instead of running on the compositor.

10. **Labels are real text.** No text is baked into a raster image, a rough.js-drawn path, or a canvas
    element. All node labels, edge labels, and legend entries are selectable `<text>` or HTML text
    nodes, so they remain screen-reader accessible and are indexed if the file is ever searched.

11. **Component text says what that component actually does.** Item 10 checks that a label *is* text;
    this checks that the text is *true*. Read every node label, sub-label and edge label as a claim
    about the system, and verify each one against that component's real responsibility.
    - **A guarantee written on the wrong component is a design error, not a typo.** It tells the
      reader a property is enforced at a point where it is not. Observed failure: an API gateway
      labelled `1 per user` in a flash-sale diagram, when the one-purchase-per-user check is only
      safe *inside* the store's own atomic script — the label announced that a race was closed at a
      place where it was still wide open.
    - **No fact has two owners.** If a responsibility appears on a node, it must not also be claimed
      by a different node or by an edge label pointing elsewhere.
    - **A node's sub-label and its adjoining edge label must not restate each other** — that spends
      two slots on one fact and hides a second one you could have shown.
    - **Diff the labels whenever you fork a diagram.** Re-cutting a diagram into another layout,
      aspect ratio, or language silently revives label text that was already corrected in the
      original. Compare the new cut's labels against the source before delivering both.
    - **Diff the RENDERED strings, not just the source.** A grep of the markup cannot see a font
      ligature: JetBrains Mono turns `>=` into `≥`, and any style that sets `letter-spacing` turns
      that back off, so two forks of one authored string ship different characters (observed).
      `font-variant-ligatures:none` on the mono/code classes settles it in every fork at once.

12. **Measure ink, not the font box.** `getBBox()` and `getBoundingClientRect()` on SVG `<text>`
    return the FACE's layout box — full ascent plus descent — not the pixels the glyphs put on
    screen. A serif or rounded face with a tall ascent then reports overflows and overlaps that a
    screenshot shows as clear gaps (observed: Jost and Source Serif both failed a safe-area lip and
    a label/sub "overlap" that did not exist). Take vertical bounds from canvas
    `measureText().actualBoundingBoxAscent/Descent`; horizontal may stay the advance width, which is
    what should govern x-containment anyway.

13. **A restyled fork re-passes every geometry check.** Skinning a finished cut into another style
    changes the typeface, and the layout was measured against the old one. Re-run label-in-shape and
    safe-area containment, and **re-bake every baked rect** (caption cards are baked from their
    text's bbox). Assert separately that each caption sits inside its own card: the node-containment
    and safe-area sweeps both pass while a caption spills onto raw canvas, since neither compares
    those two boxes. See SKILL.md → Restyling a Finished Cut.

14. **Multi-pane deliverables pass the territory checks.** For a comparison or progressive-tiers
    cut (`references/multi-pane.md`): (a) components appearing in more than one pane render
    IDENTICALLY — diff the rendered panes, not your intent; only the delta takes the accent;
    (b) every pane/tier fits its own beat frame at k_read (frame math AND screenshot — overview
    legibility is not a gate, per-territory legibility is); (c) every tier-transition caption
    names what broke and what was added; (d) no edge crosses a gutter; (e) the shared legend
    covers every role and state used in any territory.

15. **Scenario/educational cuts pass the staged-window checks.** For any cut that stages states or
    clears the canvas per act (`references/camera-beat.md` → Scenario timeline): every staged state
    is an OVERLAY carrying a `data-window="A,B"` annotation — never a mutation of the base node's
    paint properties. Run `diagram-director/scripts/browser-checks/verify-staged-windows.mjs` in all three modes
    (plain, `--acts`, `--reduced-motion`): per-window visibility, per-act isolation, recap order,
    the final act's parking window running to 100%, and reduced-motion showing the final act alone.
    Every event — each transition, each caption claim — traces to the sheet's event table
    (`time% | subject | transition | caption claim`), which is also what the build generated the
    windows from. Staged replicas paint UNDER the node's own text (DOM order: replica group before
    the label) — no gate measures paint order, and a replica painted over its label erases the node
    name exactly during the held beat; the hold-frame inspection (item 18) is the check that
    catches it.

    **The viewer persona audit is part of this gate.** An educational cut is delivered to a declared
    audience, so walk that audience through the finished render — beat by beat, act by act — asking
    their naive question at every mechanism on screen and naming the element or caption that answers
    it (`references/workflow-phases.md` → Phase 2). Record the walkthrough in the sheet's audit
    table. A mechanism with no on-screen answer ships as decoration: observed, a queue labelled
    `async work` with no consumer and no named work, green on every geometry gate in this list,
    because none of them can ask what a component is FOR. States must also read at the register the
    cut is in — an educational cut whose overload is a chip and a hairline is under-told
    (`camera-beat.md` → State intensity).

    **If the render-side checks could not run, the cut ships labelled UNVERIFIED.** Puppeteer is not
    a dependency of this skill, so `diagram-director/scripts/browser-checks/*.mjs` resolves it from
    `PUPPETEER_RESOLVE_DIR` or a plain `import("puppeteer")` and, finding neither, prints
    `UNVERIFIED -- puppeteer not available; render-side checks did not run.` and exits `2`. Exit `2`
    is **not** a pass: it means the gate never measured anything. The delivery message must then name
    which checks did not run and why, in the same breath as the deliverable — an unverified cut that
    says nothing reads as a verified one, and the whole point of these gates is that a diagram can be
    structurally perfect and visually broken. Details: `diagram-director/scripts/browser-checks/README.md` → The
    UNVERIFIED skip path.

    **Delta and legend truth (act cuts only).** A cut that declares `node-identity` also declares,
    per act, what it added and what it retired — and `diagram-director/scripts/verify_tier_identity.py` re-derives
    both from the id sets the DOM draws, so a delta the author wished for fails
    `acts/delta-mismatch`. Three things ride with it and are worth reading before the run rather
    than after: each act's caption must NAME something that act changed (`acts/delta-caption-empty`
    — an id, its rendered label, or a declared caption alias); a retired component may appear once
    more, as an outline-only `.is-ghost`, and never again; and the legend is a claim about the cast,
    so every entry must name a role the DOM has and carry the count that role really has in the
    final act (`legend/entry-unbacked`, `legend/count-wrong`).

16. **Style fidelity: the presentation layer is copied, not re-derived.** Every geometry check in
    this list passes on a cut whose LOOK has drifted off its style — none of them measure idiom.
    Observed: a comparison cut re-wrote its stylesheet from memory around the right tokens and
    shipped harsh full-opacity edges, solid accent paths where the house draws async as dashed
    with open markers, captions that faded instead of wiping, and no heading fade — every
    sweep green, user review caught it in one glance. Before shipping, diff the cut's presentation
    against the sources it must come from: `templates/base/<style>.html` (edge weights/opacities,
    marker defs incl. `markerUnits`, node stroke tiers) and, for any beats/educational cut,
    `templates/snippets/camera-beat.css` (the copy-source block per idiom: `cb-caption-card`,
    `cb-heading-fade`, `cb-spotlight-bracket`, `cb-stage-window`, `cb-act-recap`,
    `cb-negative-delay`, `cb-reduced-motion`).
    Check specifically: caption **wipe reveal** (continuous `clip-path` inset, never stepped, and
    **clip-ONLY** — `opacity` is a constant 1, never keyframed, and the exit is a same-direction
    wipe-out; diff a caption against the emitter,
    `diagram-director/scripts/timeline_css_idiom.py`, never against a pre-2026-08-27 cut) with the
    card in **inverted polarity** (`fill: var(--ink)` box, `var(--surface)` text), heading
    fade, packet treatment, and spotlight idiom — the house draws **corner brackets** (pad 12,
    arm 22, `stroke-linecap: square`), not a closed ring — plus the full reduced-motion block. The
    same diff covers CONTENT: every node's shape must come from its component's `Snippet Ref`
    (observed in the same cut: browsers drawn as plain rounded-rects instead of `shape-device`,
    an event-bus as a hand-invented drum instead of `shape-pipe`). If a line of your stylesheet
    or a shape in your markup has no counterpart in those sources, justify it or delete it.
    *Golden regression is a MACHINE check and is not a step in this list:
    `tests/run_golden_regression.py` (run by `tests/run_smoke.py`) re-derives every window,
    transform and keyframe stop of the frozen cuts and fails on any drift.*

17. **File opens standalone with no console errors.** Open the finished HTML directly in a browser
    (for `local` target) or preview it as a Claude Artifact (for `artifact` target) and confirm there
    are zero console errors — a broken CDN script, a malformed `offset-path`, or a missing `<defs>`
    reference all fail silently in the DOM otherwise.
    *Mechanised: `verify_all.py` stage C `console-clean` (console errors, uncaught exceptions and
    failed subresources; `/favicon.ico` is the browser's own request and is excluded).*

18. **The contact sheet is generated AND looked at. This is mandatory, not optional.**

    ```bash
    node diagram-director/scripts/browser-checks/contact-sheet.mjs <url> --manifest <cut>.manifest.json --out <dir>
    ```

    It seeks the master timeline to each declared hold's window midpoint, pins that hold's camera
    transform, and composites every frame into ONE image (individual PNGs plus an HTML index if
    `sharp` is not resolvable — it says which it did). Act holds get their own frame per window on
    top of the camera holds: a camera hold spanning several acts has a midpoint that can land on an
    act crossfade, and that frame then shows two acts ghosted through each other. Three delivery
    gates in this list cannot be measured and are reviewed on that image and nowhere else:

    - **Curves.** `verify-hold-geometry.mjs` checks straight segments and prints an explicit `N/A`
      for every curve it skipped. A curve's clearance is a judgement about the route it takes
      around what it passes; a bounding box cannot make it. Look at each curve on the sheet.
    - **Style fidelity** (item 16). Every geometry sweep passes on a cut whose LOOK has drifted off
      its style. Diff the sheet against `templates/base/<style>.html` and the copy-source
      snippets (`templates/snippets/camera-beat.css` for a beats cut).
    - **Semantic truth** (item 11) and the persona audit (item 15). Read the labels and captions as
      they appear at each hold, in the frame the viewer actually gets them in.

    A green `verify_all.py` with no one having opened the contact sheet is an unreviewed cut, and
    the two failures that reached users last (harsh full-opacity edges; a queue with no consumer)
    were both green on every mechanical gate and obvious in one glance at a frame.
