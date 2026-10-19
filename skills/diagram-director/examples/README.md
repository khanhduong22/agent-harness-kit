# Examples

This directory holds two kinds of file, and they are governed differently.

**A. The FROZEN golden educational cuts (`compare-chat-pubsub.html`, `progressive-500k-ccu.html`,
`progressive-500k-5tier.html`, `vibe-code-voi-ai.html`).** These are the **style/idiom authority** —
the published quality bar for the educational/beats register. Checklist item 16 (style fidelity)
diffs a new cut's presentation layer against these files and against
`templates/snippets/camera-beat.css` (which is distilled from the first two, block by cited block).
Before this set shipped, that bar lived only in a session scratchpad, so no fresh agent — Claude or
otherwise — could reach it from the repo alone.

**They are per-GENRE authorities, and the split is not decorative.** The first three are
`system-design` cuts (`references/genres/system-design.md`): SVG-native, boxes that are deployed
software. `vibe-code-voi-ai.html` is the `process` genre's first golden
(`references/genres/process.md`): HTML stations under a geometry-only SVG overlay, boxes that are
documents, screens and decisions. What crosses the line between them is the ENGINE idiom — camera,
caption card, spotlight brackets, staged windows, the negative-delay rule, reduced motion. What does
NOT cross is how the cast is drawn. Diff a new cut against the golden of ITS OWN genre.

- **Frozen.** They are never regenerated as a side effect of any build, tuning pass or restyle.
  Regeneration is an explicit decision, taken on the record, and it invalidates the checksums below
  (which must then be re-recorded in the same change).
- **Checksummed** (`shasum -a 256`), so drift is detectable rather than arguable:

  | File | SHA-256 |
  |---|---|
  | `compare-chat-pubsub.html` | `eb98930114d2f0569905fbd44207b9233186c0915b10a799a98dec34946c4351` |
  | `progressive-500k-ccu.html` | `12c873b0649cf72d759f3005ecd92384488b1050ff305026e4c0dc53c0321493` |
  | `progressive-500k-5tier.html` | `474b622cd96278614e0fade42afc05f5682040226385a9bcf32e3d579c862498` |
  | `vibe-code-voi-ai.html` | `651495a7dc158f32c86b2661a55cfb0603efda194cdccf1bb6a26a1b40701d44` |

  `compare-chat-pubsub.html` was **re-solved on 2026-08-27** (REVISION 2, user-approved, off the
  queued visual review in `plans/reports/gates-260827-1408-three-gate-debts.md` → Unresolved 1).
  **CAMERA ONLY** — no cast, no edge, no string, no window, no `k`, no caption. Two holds moved:
  `b3-b5` `ty` −703 → **−714** and `b6` `tx` −1063 → **−783**. Both had been passing the new
  `frame-edge-margin` gate on the CLIPPED-ANCHOR waiver, i.e. on a crop the gate is right to
  forgive and a reviewer had never looked at. At `b6` the frame's left edge landed on world
  x 759.3 — pane A's ws-3 and User B sliced down the middle and *their* 204-frame-px delivery
  line painted 0.4px over the boundary for its whole run. At `b3-b5` the frame's top edge landed
  on world y 319.5 — User A's bottom border, so the incoming `1 msg` edge ended 1px INSIDE the
  frame instead of arriving from outside it. `b6`'s must-show bbox now names the pane-A pair the
  frame would otherwise halve (plus `cap-b6`'s card): `1080,240,730,540` → `680,240,1130,598.4`,
  centre 1445 → 1245. `k` stays **1.4 on both pane beats** — the constant `multi-pane.md` cites
  this cut for — so b2 and b6 still show their panes at the same scale, and the neighbour in
  shot is orientation (multi-pane.md) rather than a sliced cast. `b3-b5` keeps its bbox: User A
  cannot join it at k 2.2 (240→740.4 is 500.4 world px against a 490.9px frame) and dropping k
  to fit would pull half of pane B into the pane-A mesh beat, so the frame drops 5 world px
  instead and the edge genuinely CROSSES the top side. Result: the gate passes this cut with
  **0 waivers** (was 2), 42 measured edge instances over 5 holds. Previous SHA-256:
  `c0263f75e24e6a1e4719bf7497320bbc775bbd81e8a01e39ce8a190c05fff9f2`.

  `vibe-code-voi-ai.html` was **re-baked on 2026-08-27** (REVISION 6, user-reported: *"chỗ camera
  follow đường loop về đang nhanh quá, cần chờ lại một chút"*). PACING ONLY — no cast, no edge, no
  string, no transform, no `k/tx/ty` changed; the master stays 38400ms and `b4` still opens at
  39.0625%. b3's own envelope was re-split from **hold 2100 / travel 900 / settle 600 / overview
  breather 600** to **hold 1500 / travel 1200 / settle 1500 / straight to b4 600**, every stop still
  on the cut's 300ms grid: `b3` 26.5625→**30.4688%**, `b3b` **33.5938→37.5%**. The settle at the
  follow's destination was the real defect — six tenths of a second, shorter than the caption's own
  wipe, so the viewer followed the packet home and the camera left before the packet arrived. It is
  now 1500ms, and the tracked packet's whole final descent into `AI · builds the UI` (measured off
  the finished MP4: y 80 at 13.667s → the arrowhead at 14.37s) happens with the camera dead still.
  The 600ms that paid for it is the **return-to-overview breather at 37.5%**, deleted for this one
  beat: `b3b` pans straight to `b4`. That is a recorded deviation from `camera-beat.md`'s "every
  working beat ends by throwing the viewer back to the whole picture" — taken because b3b and b4
  share scale (k 1.6), ty family and subject, so a 680px lateral pan re-establishes nothing that
  left, and is gentler than any of the five breathers the cut keeps (each zooms 1.6–2×) in the same
  600ms. Knock-ons re-derived, not assumed: `traffic-b3` + `arc-halo` windows to 37.5%, `focus-b3b`
  12900→14400ms, `recede-b3`/`br-back` held to 37.5%, and `lod-app`'s two close-tier windows MERGED
  (10200→18600ms) because there is no longer an overview instant between b3 and b4 to be far at.
  Reduced-motion still byte-identical; loop seam byte-identical. Full arithmetic: *Revision 6* in
  `vibe-code-voi-ai.sheet.md`. Previous SHA-256:
  `18bda6762b3e1bdbd93d6b1847985763a76a2a6a912a2bce4fe8346682e47a2e`.

  `vibe-code-voi-ai.html` was **re-baked on 2026-08-27** (REVISION 5, user-reported: *"biên quá sát
  nên đường nét dẫn về dễ bị che và không thấy rõ"*). At the loop-highlight beat the orange return
  arc — the beat's SUBJECT, wearing an 11px halo — ran **2.4 frame px** from the frame's top edge at
  `b3` and 16.0 at `b3b`, once the halo is counted as paint. The cause was a must-show bbox that named
  the arc in its comment and stopped 26 world px above it, and that left `cap-b3`'s card out too:
  every camera gate measures the bbox a hold DECLARES, so nothing failed. Both holds were re-solved
  from a bbox that carries the arc's painted band AND the caption card — `b3` k 1.68 → **1.6**, tx
  −1276 → **−1143**, ty −237 → **−192**; `b3b` ty −212 → **−192** — which puts the arc 36 frame px
  clear of the top and the card 36.8 clear of the bottom at both holds, and turns the mid-beat follow
  into a pure horizontal pan (same k, same ty). `cap-b3` went 15.5px → 16px to stay on the ~26
  frame px target at the new k. **No window, no keyframe stop, no `data-window` and no on-screen
  string changed.** The rule is now doctrine (`references/camera-beat.md` → *Keep the teaching line
  off the frame edge*, M = 24 frame px on the painted band) and mechanical
  (`diagram-director/scripts/browser-checks/verify-frame-edge-margin.mjs`, in `verify_all.py` stage E for `process`
  cuts; mutation-tested — it fails the pre-fix golden on exactly these two holds and passes after).
  `verify_all` is now **20 PASS / 4 N-A** (the extra PASS is the new gate); the three system-design
  goldens are untouched. Full arithmetic: REVISION 5 in `vibe-code-voi-ai.sheet.md`. Previous SHA-256:
  `29e610695a0327324271fe47345e93c93461b6b69cf6a8509bbfd73d8ffb4d05`.

  `vibe-code-voi-ai.html` was **re-baked on 2026-08-27** (REVISION 4, user-directed: *"V2 ổn. Em làm
  lại cái html để apply"*). A re-bake of a frozen golden is an explicit decision taken on the record,
  and this is that record. b5's snap block was three flush rectangles plus two rotated teal seam keys
  — sampler-v2 vocabulary authored before the product-first pivot, which had come to read as an
  unrendered placeholder beside a real BRD document and a real browser window. It is now the
  **cartridge module** block approved on
  `plans/reports/designer-260827-1230-snap-block-enrichment-board.md`: three pieces carrying the
  products they actually are (the same dashboard from b3/b4, an API card, the same `items` table from
  b4), a jigsaw knob wearing the LEFT piece's role colour already seated in the next piece's socket,
  and a full-bleed port band the record runs through — with the knob dead-centre on the band, so the
  joint and the packet's throat are one object. The idiom was entered in
  `references/genres/process.md` → *Vocabulary — mộng / ổ / port band* BEFORE it was used, which is
  what legalises it; a one-off shell metaphor is banned by that same section.
  The block grew 810×130 → **810×282**, which moved everything under it: the b5 spotlight bracket, the
  b5 packet path (`M 90 825 H 840` → `M 90 1019 H 840`, derived as block-bottom − 23 = the port band's
  centre), b6's edge (`M 870 825 H 1000` → `M 870 1019 H 1000`), the "snap three pieces" edge's drop
  (x 470 → 780, to keep the whole run clear of the caption card), b5's camera hold
  (`ty −1350` → `−1502`, `k` still 2, bbox height 130 → 282), b5's caption (which moved ABOVE the
  block — `camera-beat.md` permits the gap above or below when a fixed slot will not fit), the verdict
  banner and both overview captions. **No window, no keyframe stop, no `data-window`, and no
  on-screen string changed** — golden regression re-derives at 0.0000 pp and `verify_all` re-ran at
  **19 PASS / 4 N-A**, unchanged. Full arithmetic and every knock-on: REVISION 4 in
  `vibe-code-voi-ai.sheet.md`. Previous SHA-256:
  `4667e194db070e1f8908880c6a151728879406320c2da648dcc61874d1b219fb`.

  `vibe-code-voi-ai.html` was **frozen 2026-08-27** — the process genre's first golden, promoted
  after four user review rounds (`plans/260826-1800-workflow-explainer-and-stacked-compare/phase-05-process-vignette-pivot-status.md`
  is the full record). It entered the directory from `tests/process-full-build-handoff/` with
  COMMENT edits and nothing else: the two header comments that named its event table now point at
  `tests/fixtures/vibe-code-voi-ai.timeline.tsv`, where the table actually lives, and the file
  header says it is a frozen golden. Its manifest is byte-identical to the handoff copy; its sheet
  changed only the same two path references. No pixel, window, keyframe or on-screen string changed
  in the move — `verify_all` re-ran on the promoted file at **19 PASS / 4 N-A**, unchanged.

  `progressive-500k-5tier.html` was **re-frozen again on 2026-08-30** (AMENDMENT #6, code review of
  phase 03, REQUEST_CHANGES item 2): the retirement ghost stopped being VOLUNTEERED. `ghostOf` was
  the only thing that asked for one, so deleting the sheet cell and the ghost group together left a
  green table over a cut that buried nobody. `diagram-director/scripts/verify_retired_ghost.py` now DERIVES the
  requirement — the ids an act drops (`ids(act N−1) − ids(act N)`, off the DOM) each owe one outline
  farewell in that act — and this cut owed three it had never drawn: **`alb` and `app` at T4,
  `postgres` at T5**. All three are now drawn, in the T2 ghost's own idiom (160×80, `fill:none`,
  dashed, opacity .38, `aria-hidden`, no `data-node-id`), in the band `y 375–455, x 350–750` that is
  empty in both acts — no node, edge, window, keyframe, caption, hold or camera value moved to make
  room. The manifest gains `ghostOf` on acts 4 and 5 and the sheet's ACT DELTA row the matching
  cells (documentation now, not the requirement); `emit_act_delta.py` still round-trips `acts[]`
  byte for byte. Four more deletion holes closed in the same pass: a `.is-ghost … { fill:none }`
  rule is now required in the cut's `<style>`, a declared `moved` waives only an ADJACENT 4×3 cell,
  every `path.edge` in a lens act must declare `data-from`/`data-to` (`lens/edge-unattributed`), a
  lens hold with no window FAILS on both sides instead of passing zero comparisons, and the shrink
  tripwire tracks `holds[].anchor` and the `acts[]` numbers too. One more stale claim went with
  them: the legend's member prose still named `alb` and `postgres`, both retired before the
  final act, so a reader took the cast list for the last frame and got two components that are
  no longer there. `service ×6 alb · gateway · services · workers · router` →
  `service ×6 gateway · services · workers · router`, and `data ×6 postgres · shards ·
  replicas · redis` → `data ×6 auth-db · shards · replicas · redis`; `verify_legend_fact.py`
  now fails `legend/member-retired` for any member token that is the id or rendered label of a
  component the final act does not draw (collective prose like `services` or `shards` matches
  no id and is left alone). Gate table: **37 PASS / 3 N-A**, exit 0, unchanged. Contact sheet re-shot (25 frames) and read: the ghosts sit alone in the empty
  band, nothing overlaps — but the file CHANGED after the sign-off above, so that sign-off does not
  carry over: **visual re-review needed**, reviewed-by: pending (user). Previous SHA-256:
  `e37289801047eb0344ad433bbba0c026dd11c99d23eb06fa1b8b8237a59516bb`; the manifest went
  `b95d986143b2e8b4a713c2363ff3f621a403764fbb8249249f45525ca62dd8b4` →
  `97fbf5e4aeaa0bd03101d0cf46f441688cfd2a1b205868b6d6ffa41ae544728b`.

  `progressive-500k-5tier.html` was **re-frozen again on 2026-08-30** (AMENDMENT #5, user decision taken
  after reviewing the contact sheet): the five `+N −N` delta chips AMENDMENT #4
  had put in the act title band were **removed** — the five `g.act-chip` groups and the CSS rules
  that styled them, and nothing else. No node, edge, window, keyframe, caption, hold or camera value
  moved; the manifest is byte-identical
  (`b95d986143b2e8b4a713c2363ff3f621a403764fbb8249249f45525ca62dd8b4`) and the ACT DELTA row it
  emits is unchanged. The chip remains shipped as OPT-IN scenery
  (`templates/snippets/act-delta-chip.html` + the `cb-delta-chip` block in
  `templates/snippets/camera-beat.css`): the sheet's ACT DELTA row is the FACT, the chip is one
  optional rendering of it, absent by default. The gate followed the decision instead of the file —
  `delta-chip` is now a row of its own and reports **N-A** (*"no chip rendered — optional scenery"*)
  when no act draws one, failing only when a chip EXISTS whose numbers disagree with
  `len(delta.added)` / `len(delta.removed)`; the opt-in path stays proven on
  `tests/fixtures/tier-identity/` (chip-bearing positive + the `delta-chip-mismatch` negative) and
  the chipless path on `variant-no-chip.html`. Gate table: **37 PASS / 3 N-A**, exit 0 — the third
  N-A is `delta-chip` itself, which is the point. Contact sheet re-shot (25 frames): no chip in any
  act frame. reviewed-by: viettranx (user) · 2026-08-30 · verdict: accept · contact sheet after
  chip removal, 25 frames. Previous SHA-256:
  `d961a14434cb36661fbc5540c8fd657b7592afa70de5202dc88091e3f64b3a86`.

  `progressive-500k-5tier.html` was **re-frozen on 2026-08-30** (AMENDMENT #4, plan
  `260830-1325-archify-lessons-gates-tier-identity-floor` phase 03): this cut is the exemplar for
  the act rules, so it is where the act rules stopped being prose. Every one of the 46 node groups
  gains a stable `data-node-id`; all 48 edges gain `data-from`/`data-to`; the sheet gains the
  machine twin of TIER BOUNDARIES (`## Phase 2 — ACT DELTA`) and the manifest gains the `acts[]`
  it emits, plus the features `node-identity` and `act-delta`. On screen: five static `+N −N` delta
  chips in the title band (x 585, one fixed column, right of the widest verdict pill), ONE retired
  ghost (`app-monolith`, outline-only, act 2, one row below its old C3/R1 slot because `alb` stands
  there now), and the legend's five role entries now carry the final act's real counts
  (`client ×1 · service ×6 · data ×6 · async ×2 · infra ×1`) with the swatches re-spaced to
  150/300/700/1090/1320 to fit them. One hold ADDED — `a3-anchor`, a `read`-gate anchor beat on
  `postgres`, the node acts 3 and 4 both draw — carved out of `a3b`'s tail, which shortens `a3b`'s
  window 40.4167 → 39.1667; no keyframe, no transform and no on-screen instant changed, because the
  camera already sits at one continuous `25%,55.4167%` pose across a3a/a3b/a4a/a4b. NO hold id was
  removed or renamed. `role-lens` was evaluated and NOT taken into this golden (it does not fit the
  48s master without moving an existing window) — it ships proven on the fixtures instead, recorded
  in the sheet. Gate table: **37 PASS / 2 N-A**, with `tier-identity`, `act-delta`, `retired-ghost`
  and `legend-fact` all PASS. Contact sheet re-shot (25 frames). reviewed-by: viettranx (user) ·
  2026-08-30 · verdict: accept · contact sheet after chip removal, 25 frames. Previous SHA-256:
  `eb2b276da53f86a8f2824daf10e814d3f44f5e3ed70ea61647561ca8d00e511d`; its manifest went
  `dd1ee0153ff99934475ed32a27faec569d8b9d5ec08485a3a0985407faa8f9eb` →
  `b95d986143b2e8b4a713c2363ff3f621a403764fbb8249249f45525ca62dd8b4`.
  `progressive-500k-ccu.html` is the regression anchor and its SHA-256 is unchanged by this work.

  `progressive-500k-5tier.html` was re-checksummed on **2026-08-26** (AMENDMENT #3, user-directed):
  the shard routing key goes universal — `user_id` named a specific column in a cut subtitled THE
  BASIC PATTERNS, so the four strings that carried it (router sub, `cap-a5a`, the router `<title>`,
  the `<desc>`) now teach the mechanism instead (`by hash(key)` / `hash(shard key)`); one caption
  BOX width re-baked, no window, no keyframe, no geometry (golden regression re-derives at
  0.0000 pp) — see AMENDMENT #3 in `progressive-500k-5tier.sheet.md`. Previous SHA-256:
  `ebaed96b20b5526e5b61d11096610b46eb9fbfef92993eecb0088402de9f9151`.

  Before that it was re-checksummed the same day (AMENDMENT #2, user-directed):
  the three T4/T5 domain services gain the replica-stack ghosts and the `xN` sub they had been
  missing since v3 — six nodes in acts 4 and 5, no caption, no window, no keyframe, no transform
  (golden regression re-derives at 0.0000 pp) — see AMENDMENT #2 in
  `progressive-500k-5tier.sheet.md` for the arithmetic behind every count. Previous SHA-256:
  `12b496e431015bee4cc0a428d5cbc309fcdd6d0603307ac688696c06ff6f4dc9`.

  And before that, the same day again, for a user-directed title clarification (title band
  now reads `0 → 500K CCU · THE BASIC PATTERNS`, `<desc>` gains one caveat sentence — AMENDMENT #1);
  the SHA-256 that amendment replaced was
  `5dc140470bd04238f9d46e15706d1a907a1edd0ab73a5a7762deda4bdadfc67a`.

- **Solution sheets included** (`compare-chat-pubsub.sheet.md`, `progressive-500k-ccu.sheet.md`,
  `progressive-500k-5tier.sheet.md`, `vibe-code-voi-ai.sheet.md` — the last one on the PROCESS sheet
  schema in `references/genres/process.md`, which adds AUDIENCE / CORE WORKFLOW / persona audit).
  Not documentation-for-its-own-sake: every string on screen — each caption claim, each chip
  number, each act title and load band — traces to its sheet's event table, and the sheet is the
  single source the windows and the keyframes were both derived from. A golden without its sheet
  would be a look with no provenance.
- **Output manifests included** (`compare-chat-pubsub.manifest.json`,
  `progressive-500k-ccu.manifest.json`, `progressive-500k-5tier.manifest.json`,
  `vibe-code-voi-ai.manifest.json` — the only one that declares `"genre": "process"`, which is what
  `diagram-director/scripts/verify_all.py` dispatches on), governed exactly
  like the sheets: they declare what each
  cut contains — features, every hold and window, every caption string, every dataset row id — so a
  verifier can tell a missing layer from a layer this cut never had. Spec:
  `references/output-manifest.md`. They are derived from the sheets, not from the HTML, and
  `tests/run_golden_regression.py` re-derives their windows and transforms from
  `tests/fixtures/*.timeline.tsv` + `golden-camera-holds.tsv` and diffs them against the frozen
  files on every smoke run — so a manifest that drifts from its golden fails the build.
- **All four render standalone in a browser**, no server and no build step, like every other file
  here.
- **Inline comments inside the goldens are historical, not normative.** Frozen byte-for-byte means
  a few pre-decision words survive in their comments (e.g. "typewriter" where the shipped spec is
  the continuous wipe). The spec is `templates/snippets/camera-beat.css` + `references/camera-beat.md`;
  where a golden's comment disagrees with those, the comment loses. The goldens' *rendered behavior*
  agrees with the spec — only the prose in comments predates it.
- **Their gates are replayed from the repo**, at these paths, not from wherever they were authored:
  `diagram-director/scripts/browser-checks/verify-staged-windows.mjs` (plain, `--acts`, `--reduced-motion`),
  `verify-caption-boxes.mjs`, `verify-text-containment.mjs`, `verify-glyph-label-gap.mjs`, and
  `python3 diagram-director/scripts/verify_edge_anchors.py` (anchoring AND the nearest-side rule). The whole set is
  what `python3 diagram-director/scripts/verify_all.py <cut>.html --serve` runs in one command. The process golden
  swaps two of those for its construction mode, and `verify_all.py` makes the swap itself off
  `manifest.genre`: the static `verify_edge_anchors.py` finds no `.node__shape` in an HTML-mode cut
  and SKIPS it, so `diagram-director/scripts/browser-checks/verify-html-edge-anchors.mjs` does that job instead
  (FLOATING / WRONG-SIDE / DEAD-GEOMETRY, plus the webapp contract and the LOD-leak sweep) against
  live `getBoundingClientRect` boxes. Stage E gains one genre-scoped check on the same path,
  `verify-frame-edge-margin.mjs` (no edge hugs a frame side it does not cross, 24 frame px on the
  painted band — REVISION 5). Its number, as of AMENDMENT #6 (2026-08-30), is **23 PASS /
  10 N-A** — the stage table has grown six act-family rows since REVISION 5 and every one of
  them prints N-A on this cut, which declares none of their features. The other three, same
  run: `progressive-500k-5tier.html` **37 PASS / 3 N-A**, `progressive-500k-ccu.html` **23
  PASS / 7 N-A**, `compare-chat-pubsub.html` **21 PASS / 9 N-A**. All four exit 0.

| Cut | Genre | Register / type | Master | Structure |
|---|---|---|---|---|
| `compare-chat-pubsub.html` | `system-design` | educational / `comparison` | 33.6s (7 × 4800ms) | 2 panes, 7 beats, staged overload → down → domino |
| `progressive-500k-ccu.html` | `system-design` | educational / `scaling-story` | 38.4s (8 × 4800ms) | 4 acts (T1–T4) + recap pass, staged state per act |
| `progressive-500k-5tier.html` | `system-design` | educational / `scaling-story` | 48s (10 × 4800ms) | 5 acts (T1–T5), 8 content beats + `r1..r5` recap holds + an `intro` park hold, staged state per act |
| `vibe-code-voi-ai.html` | `process` | educational / `process-loop` | 38.4s (6 × 4800ms + a 9600ms closing overview) | 7 beats on one 2160×1440 canvas, 8 camera holds (b3 + a mid-beat follow to `b3b`), two-tier LOD, happy path with one return loop |

**`progressive-500k-5tier.html` is the exemplar for the storyboard rules, and the primary
progressive/scaling-story copy source** (SKILL.md → Output Rules points there). It is where the
four attention rules in `references/multi-pane.md` — foreground budget ≤ ~5 nodes **per beat**,
veterans receding down the style's OWN stroke ladder, solved lessons compressing to the supporting
box, and fixed canvas zoning across every act — were trialled, and where each of them cost
something real: T4 needs six new components in one act (pub/sub must land with decomposition), so
the budget is honoured 5+1 across two beats; the recede ladder is `flat-minimal`'s own ×1.4 step
inverted, riding `.node__body` only so labels keep full ink; zoning lost once to a label length and
is documented in the sheet rather than absorbed. It is also the cut that produced the **one camera
hold per BEAT** rule (`references/camera-beat.md`, `references/output-manifest.md`): a single `a4`
hold spanning two beats put its midpoint in no beat's land and dropped the act's payoff from the
contact sheet. `progressive-500k-ccu.html` remains frozen as the **4-tier reference and regression
anchor** — it is not superseded, it is the older, smaller answer, and it is what proves the emitter
and solver have not drifted.

**`vibe-code-voi-ai.html` is the `process` genre's idiom authority**, and the only golden built in
the HTML-first construction mode. What it demonstrates, and what a new process cut should be diffed
against block by block:

- **HTML stations + a thin SVG overlay for connectors only.** Stations are divs (wrapped Vietnamese
  text, grids, mono texture — all painful-to-impossible in SVG); the overlay is geometry only,
  never a `<text>`, sitting under the stations at `1 SVG unit == 1 CSS px`. The full contract, with
  the traps that produced each clause, is `templates/snippets/process-stage-and-edges.css` and
  `references/genres/process.md`.
- **Product-first stations, not boxes-with-labels.** The brief is a one-page document
  (`station-brd-doc`); the app is a browser window running a real dashboard (`station-webapp` +
  `webapp-skin--dashboard`); the deploy beat is a responsive browser + phone pair. The first
  acceptance cut drew this cast as labelled boxes and the user rejected it outright — that
  rejection is why the genre exists as its own pack.
- **The cartridge idiom (REV 4).** When several pieces of one product are built separately and then
  have to fit together, the joint and the flow are ONE object: a jigsaw knob in the left piece's role
  colour, seated in the next piece's socket, sitting dead-centre on the full-bleed port band the
  record runs through. Shell shapes that carry meaning must be named in
  `references/genres/process.md` before a cut uses one — that section, not this cut, is the authority.
- **Two-tier LOD choreographed to the beats.** Far at the overviews, close at b2 (the brief) and
  b3/b4 (the app), switched by an animated `@property --lodc` on the station wrapper — a
  single-canvas beats cut has no per-beat wrapper to flip and no JS. Nothing inside an LOD subtree
  may set its own `opacity` (cascade collision); dim with `color-mix` instead.
- **A mid-beat camera FOLLOW.** b3 declares two holds — `b3` and `b3b` — so the camera moves inside
  one beat and arrives on a subject its bracket has already named. One hold per BEAT is still the
  rule; a follow declares each end of the move.
- **A 2× closing recap.** Beats 1–6 run one beat each; beat 7, the closing overview, holds 9600ms.
  The OPENING overview stays 1× because it is a teaser. That is an ENGINE rule now
  (`references/camera-beat.md` → per-beat shape) and it is NOT retroactive to the three
  system-design goldens, which predate it.
- **English on the elements, Vietnamese in the explanation.** Every string on a station is English;
  the seven captions, the narration and the page heading are Vietnamese. `references/genres/process.md`
  → *Language* has the two-register table and the mono-quote escape hatch.

**One accepted cosmetic limitation, on the record.** Under memory pressure a caption can blink for a
single frame on loop 2+ (never on pass 1). Diagnosed as a stale compositor tile: the caption sat
invisible ~30s at `opacity:0` with its `clip-path` parked open, and a tile rasterized while the clip
was open could be served for one frame when opacity left 0. The structural fix shipped — the caption
is now **100% clip-driven**, `opacity` is a constant 1 and never appears in a keyframe, so no
compositor-side visibility gate exists to serve a stale tile (its exit became a same-direction
wipe-out; sheet deviation 24). The blink could not be reproduced across five live-playback
configurations here. **The user accepted the residue as cosmetic** — it is invisible in a rendered
video, which is what this cut is for — so it is recorded, not chased further. **The engine pass
shipped on 2026-08-27**: `diagram-director/scripts/timeline_css_idiom.py::caption_window` now emits exactly this
clip-only block, so this cut's `cap-b*` keyframes are no longer an exemption —
`tests/run_golden_regression.py` diffs all seven of them stop-for-stop and `PROCESS_OWN_IDIOM` is
down to `lod-`. The debt moved to the other three goldens, which still ship the legacy opacity+clip
caption; they are exempted by name as `SD_LEGACY_CAPTION` with the user's deferral recorded, and
that exemption fails the moment it stops matching anything.

**B. The three acceptance-test diagrams** (`01-`, `02-`, `03-`), described below. These are
scenario records, not the idiom authority.

---

Three acceptance-test diagrams produced by following `SKILL.md` literally, end to end, from a
single user prompt each — no hand-patching of the output HTML to hide a routing/dataset/template
gap. Every source-level fix these scenarios exposed was made in `SKILL.md`, `references/*.md`,
`templates/base/*.html`, `templates/snippets/*.html`, `data/layouts.csv`, or
`data/diagram-types.csv` (never in the example file itself); see each file's header comment for the
specific note, and the acceptance report for the full list. Each diagram below was verified from a
rendered screenshot in both colour schemes, not from its markup — two of the defects recorded here
were invisible in the source and obvious on screen.

All three pass every item in `references/pre-delivery-checklist.md`: reduced-motion end state,
AA-contrast colors (every color used traces back to an unmodified `data/color-semantics.csv` row —
verified by grep-diffing hex codes against the dataset, zero custom colors introduced), `role="img"`
+ `<title>` + `<desc>` on the SVG root with a `<title>` accessible name per node group, no color-only
or motion-only encoding, runtime matching the declared `--target`, node counts within each layout's
sweet spot with zero overlapping nodes/edges, motion restricted to `transform`/`opacity`/`clip-path`/
`stroke-dashoffset` (no `width`/`height`/`top`/`left` animation), real `<text>` labels throughout, and
well-formed standalone HTML (verified with Python's `html.parser`, balanced tags, zero unexpected
external hosts other than the ones named below).

All six SVG-mode examples also pass the nearest-side edge-anchor gate
(`diagram-director/scripts/verify_edge_anchors.py`), which smoke now runs over the whole directory — though the gate
postdates these three, and the 20 endpoints it first flagged here turned out to be blind spots in
the checker rather than defects in the diagrams, so they pass on their original geometry. The
seventh file, `vibe-code-voi-ai.html`, has no `.node__shape` to face (its stations are divs), so
that gate SKIPS it by design and says so; its equivalent is the browser check named above.

| # | Prompt | Target | Style | Diagram type / layout | File |
|---|---|---|---|---|---|
| 1 | `vẽ request lifecycle của hệ thống ecommerce, style sketch` | local | `hand-drawn-sketch` | request-lifecycle / swimlane | `01-ecommerce-request-lifecycle-sketch.html` |
| 2 | `event-driven order pipeline with queue and workers` | artifact | `flat-minimal` | event-driven-pubsub / hub-spoke | `02-event-driven-order-pipeline-flat.html` |
| 3 | `kubernetes deployment topology for a 3-service app` | local | `blueprint` | deployment-topology / clustered-domains | `03-k8s-deployment-topology-blueprint.html` |

## 1 — ecommerce request lifecycle (sketch, local)

Bilingual prompt (Vietnamese with English technical nouns) on purpose, to exercise the router on the
real usage pattern. As run literally, `--blueprint` initially fell back with "no diagram-type matched
the scenario" — the tokenizer's coverage-abstain gate (`min_coverage 0.34` in `core.search`) rejected
the match because 5 of 9 query tokens were plain Vietnamese words absent from `diagram-types.csv`'s
vocabulary, even though the two English tokens that DID match ("request", "lifecycle") scored far
above the floor on their own. Fixed at the source in `data/diagram-types.csv`: added a few
Vietnamese keyword phrases specific to this type ("vẽ luồng yêu cầu", "sơ đồ hệ thống yêu cầu") to
`request-lifecycle`'s `Keywords` cell, which raises coverage to 0.56 without touching `scripts/**`
(out of this pass's ownership). One correction pass; re-ran clean afterward, 8 lanes (browser → cdn →
waf → load-balancer → api-gateway → orders-service → cache → sql-database, then one response arrow
returning to browser), one primary hop (api-gateway → orders-service) drawn thicker, `dash-flow` only
per the blueprint's motion assignment.

**Fixed at the source since (was the "one node size" caveat):** this file originally hand-recomputed
every shape's internal coordinates to hit swimlane's then-stated `node 150x60`, a cost that recurred
for every layout whose node size differed from `node-shapes.html`'s 160×80. Resolved in the dataset
instead of per diagram: node size is not what distinguishes these layouts — arrangement and gaps are
— so `data/layouts.csv` now specifies **every** layout against the shipped 160×80 box and carries the
character of each layout in its gaps, radius and grouping. One deliberate size difference survives,
hub-spoke's larger hub, because there size *means* something, and it is produced by the single
documented mechanism in `node-shapes.html`'s header (uniform `scale(k)` on the node body with
`vector-effect="non-scaling-stroke"`, labels outside the wrapper) rather than by new per-shape
variants. Every node in this file is now a verbatim snippet copy; only `translate()` differs.

**Also fixed here (invisible in the markup, obvious on screen):** `.lane-line` was styled with
`stroke:var(--line)`, but `--line` is only defined on `[data-role]` elements and a lane line has no
role — the stroke resolved to `unset` → inherit → the SVG default of `none`, so all eight lifelines
rendered *invisibly* and the diagram read as scattered arrows in a mostly-empty field. Now
`stroke:var(--stroke)` (the global token `.edge` already uses). With the lifelines visible and the
step columns pulled in to swimlane's `step column gap 130px`, the staircase reads as one continuous
trace: each hop drops 140px and steps 130px right, so consecutive hops nearly touch.

## 2 — event-driven order pipeline (flat-minimal, **artifact**)

Router picked `event-driven-pubsub` + `hub-spoke` correctly on the first pass (the query's own node
kinds — pubsub-topic, event-bus, microservice, worker, dead-letter-queue — cover both the
"event-driven" and "queue and workers" halves of the prompt in one type, so no `queue-worker` vs.
`event-driven-pubsub` ambiguity in practice). `--target artifact` correctly dropped
`fanout-broadcast` from the type's `packet-travel|dash-flow`-style Recommended Motion (it's `needs-js`,
barred for artifacts) and left only `pulse-glow`, applied to the event-bus hub and the worker pool.

**Artifact safety, stated correctly:** `--target artifact` means zero external `<script>` tags and
zero CDN assets — but **not** zero `<link>` tags. Google Fonts is the one external host the Claude
Artifact sandbox permits: `fonts.googleapis.com` stylesheets plus the `fonts.gstatic.com` font files
they pull. Every other external host is blocked there. So this diagram ships an **active** Inter
`<link>` (matching `templates/base/flat-minimal.html`, which also ships it active), with the system
font stack behind it in `--font-title`/`--font-label` in case the request is blocked anyway. What it
ships zero of is external scripts and CDN assets — verified with
`grep -E '<script[^>]+src=|<link[^>]+href="https?://(?!fonts\.(googleapis|gstatic)\.com)'`
(no matches). An earlier revision of this file, and of the ADAPT notes in three base templates,
claimed the opposite ("the Google Fonts `<link>` is commented out on purpose"); that claim was wrong
and has been corrected in `SKILL.md`, `references/pre-delivery-checklist.md`, all four base
templates, and here.

**Resolved (was the 4-spoke caveat):** hub-spoke's `Node Count Sweet Spot` is "5-15 spokes", and
`event-driven-pubsub` used to list exactly 5 `Node Kinds` — one of which becomes the hub, leaving 4
spokes, permanently under the floor. Resolved by widening the *type*, not by lowering the layout's
floor, because the deficiency was real on its own terms: a fan-out with a single consumer is not a
fan-out, which is precisely the anti-pattern that row already warns about. `Node Kinds` now also
carries `webhook-dispatcher` (push delivery to partner APIs) and `metrics-collector` (telemetry
subscriber) — both long-standing rows in `components.csv`, both ordinary members of a real pub/sub
topology. That is 7 kinds → 1 hub + 6 spokes, inside the sweet spot, and this diagram was redrawn to
match: spokes at `360/6 = 60°` apart, consumers on the right arc, publisher/DLQ/observability on the
left arc. The rewrite also fixed a genuine collision the 4-spoke version had — its east and west edge
labels overprinted the hub, because at the old `spoke radius 260px` a horizontal spoke leaves only
~100px between hub edge and spoke edge for a ~150px label. `layouts.csv` now derives the radius
(`max(360px, 100px / sin(180°/N))`) so both label room and inter-spoke clearance hold at any N.

**Also fixed here (a CSS-cascade trap worth knowing):** edge labels that need a non-default alignment
were written as the SVG presentation attribute `text-anchor="end"`. Presentation attributes lose to
*any* stylesheet rule, and `.edge__label` sets `text-anchor` — so those labels silently rendered
centred and overprinted their own connector. All four base templates had the same line. Fixed by
moving the override to an inline `style="text-anchor:end"`, which does win the cascade.

## 3 — Kubernetes deployment topology (blueprint, local)

Run without `--style`, the auto-picker chose `isometric-2.5d` over `blueprint` for
`deployment-topology` even though both are equally listed in the type's `Best Styles` and the target
is `local` (no artifact-safety filtering in play) — `isometric-2.5d` has `Template Status=planned`, so
the very next resolution step had to substitute the `blueprint` template anyway and emit a warning.
Avoidable churn in `blueprint_composer.py`'s style auto-selection (ranks by raw BM25 score only, no
preference for a shipped template when an equally-endorsed alternative exists) — that file is
`scripts/**`, out of this pass's edit scope, so the diagram was produced the same way `SKILL.md`'s own
Example Workflow handles scenario 1: pin `--style blueprint` explicitly. One correction pass (adding
the flag); documented in the file's header rather than silently avoided.

Deployment-topology's `Node Kinds` (kubernetes-cluster, availability-zone, region, load-balancer,
autoscaling-group) don't distinguish "rendered as a node shape" from "rendered as the layout's
required cluster-boundary box" — `region` and the active `availability-zone` are rendered as the
labeled `clustered-domains` boundary they need to be anyway (drawing a second, separate node on top
would just duplicate the same label); the standby zone, with no children to group, is rendered as a
literal node. All 5 Node Kinds appear at least once. `replication-sync` (the only motion in the
type/style intersection, `needs-js`, fine for `--target local`) is applied to the three
`autoscaling-group` nodes — checkout, orders, catalog, matching the prompt's "3-service app" — fading
in in deployment order to represent the cluster bringing each service's replicas into sync; per
`motion-recipes.md` this is a one-shot boot animation (`forwards`, not `infinite`) that holds its end
state rather than looping.

**Fixed here (dead space):** both boundary boxes used to run far past their contents — the
`AZ (us-east-1a)` box ended 110px below its last node and the region box 150px below that, so a third
of the canvas was an empty band. Both now hug their contents at exactly the clustered-domains
`cluster padding 32px` on all four sides (`Region` = 40,138 → 1268,524 around contents 72..1236 ×
170..492; `AZ` = 72,348 → 816,492 around contents 104..784 × 380..460), with the label 16px above the
border per the same rule, and the viewBox trimmed to a uniform 20px margin around the region box.
Node geometry also went back to the verbatim 160×80 snippets after `clustered-domains` was
standardised on that box, and the standby-failover connector now lands on the standby zone's left
edge instead of part-way across its top edge.

**Also fixed at the source:** while confirming this scenario's `--target local` CDN reference against
`references/style-guides.md`'s exact-version citation rule (`pre-delivery-checklist.md` item 5), found
the doc's rough.js example pinned `roughjs@4.6.6/bundled/rough.min.js` while the actually-shipped
`templates/base/hand-drawn-sketch.html` loads `roughjs@4/bundled/rough.js` — doc and template
disagreed. Updated the doc snippet to match the shipped template (the file that actually executes is
the source of truth), so scenario 1's citation is now checklist-item-5-compliant by exact match.

**Also found, not fixed (would need a product decision, not a copyedit):**
`SKILL.md`'s Output Rules said "Non-interactive: looping motion only," which contradicts
`connection-draw-in` and `replication-sync` — both already shipped, both explicitly one-shot
(`forwards`, no `infinite`) per `motion-recipes.md`. Reworded the rule to name the one-shot
boot-sequence exception instead of silently ignoring the contradiction while building this file.
