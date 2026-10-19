# Solution sheet — 0 → 500K CCU, educational storyboard (v3)

Single source of truth for every string in `examples/progressive-500k-5tier.html`. Nothing renders that is not
traceable to a line here. Format: `references/workflow-phases.md` → Phase 1/2/3.

- **Target**: `artifact` (css-only, zero external `<script>`; Google Fonts `<link>` only).
- **Format**: landscape 1920×1080.
- **Type / layout / style / palette**: `scaling-story` / `progressive-tiers` / `flat-minimal` /
  `house` — carried from v2, all four AUTHORITATIVE from `search.py --blueprint`.
- **Register**: educational (acts + staged states + recap).
- **Audience declared**: junior dev who builds basic web apps, has never scaled one.
- **What changed from v2**: 4 tiers → 5 (microservices and sharding are now separate acts);
  pub/sub introduced at T4 as the *consequence* of decomposition; fixed canvas zoning; a three-step
  act-weight ladder; T5 compression of the solved lesson; a numerically consistent tier ladder.

---

## AMENDMENT — 2026-08-26 (title band + `<desc>` caveat)

**On the record: user-directed.** The user asked, explicitly, that the cut name these five
architectures as the BASIC patterns, and that the narration add the caveat that the ladder is not
the answer to every problem. The frozen-golden policy allows exactly this — an explicit decision,
taken on the record, with the checksums re-recorded in the same change (`examples/README.md`).

Two strings changed, nothing else. No caption, no window, no keyframe, no geometry, no chip;
`tests/run_golden_regression.py` re-derives this cut's 11 windows / 28 keyframes / 234 stops at
max deviation **0.0000 pp** after the amendment, which is the proof that timing and camera are
untouched.

| slot | before | after |
|---|---|---|
| title band, `text.title` (`x=960 y=54`) | `0 → 500K CCU` | `0 → 500K CCU · THE BASIC PATTERNS` |
| `<desc id="d">`, final sentence | *(ended: "…the loop parks on act 5.")* | + `These five are the BASIC patterns — the standard baseline of scaling, taught here in their simplest form; real systems diverge, and this ladder is not the answer to every problem.` |

The subtitle (`monolith · scale-out · read/write split · microservices · 3 shards`) is unchanged;
the `·` separator in the new title is its idiom, carried up one line. Measured at 1920×1080 at
every hold where the chrome layer is visible (`intro`, `r1`–`r5`, all k=1): the title renders
**641.0px wide, x 639.5..1280.5**, i.e. 639.5px clear on each side inside the band, 8px above the
subtitle as before, overlapping nothing. `verify_all` stage C `text-containment` (which sweeps
every `<text>`) stays green.

The document `<title>`/`<desc>` *heading* strings and `manifest.target.title`
(`0 to 500K CCU — five architectures, five break points`) were deliberately NOT touched: the
manifest mirrors the document `<title>` element, not the on-canvas title band, so no manifest
field mirrors a changed string.

---

## AMENDMENT #2 — 2026-08-26 (replica stacks on the three domain services)

**On the record: user-directed.** The user caught that the three domain services in acts 4 and 5
(`auth-svc`, `catalog-svc`, `order-svc`) were drawn as SINGLE boxes with no replica-stack
indication, while T2 and T3 had spent two acts teaching scale-out with ghost stacks and `xN` subs.
Read as a sequence, that says decomposition REPLACED replication — the exact wrong model for the
declared audience. This sheet's own Phase 1 line said it too: "Singularity by design (never
stacked): … each domain service". That line was the defect; it is corrected below.

The general rule this exposed is now encoded in `references/multi-pane.md` → *Attention budget*
("a lesson once taught persists in compressed form") and in `references/workflow-phases.md`'s
persona-audit question list.

### The arithmetic (nothing here is invented — every input is already in Phase 1 — NUMBERS)

**Per-replica capacity, anchored on T3.** T3 ran **12 app replicas at 100K CCU**. 100K/15 =
**6.7K ops/s**, so one replica of this cut's box class absorbs **6.7K / 12 ≈ 556 ops/s**. That
constant is held across T4 and T5: the sheet has no per-service capacity figure, and inventing one
per domain would be inventing a number. Two consequences, stated rather than hidden: it ignores
whatever the CDN absorbs upstream (`static · API`, no hit rate in the sheet), and it charges a
specialised service the same cost per op as a monolith replica doing everything. Both make these
counts an **upper bound** — the honest direction to be wrong in on a teaching diagram.

**The request partition.** The gateway routes each request by path prefix to exactly one service —
that is literally what the three `/auth` `/catalog` `/orders` edges draw — so the tier's ops/s
PARTITIONS across the three services, never duplicates:

- `/orders` = the write path = `ops/s ÷ 11` (the 10:1 mix, Phase 1 — NUMBERS).
- `/auth` = the session check. It is the cache-friendliest key in the cut, so it is served at the
  same **90% hit** rate the sheet already fixes for the read path: only **10% of ops** reach
  `auth-svc` itself.
- `/catalog` = the remainder — browse reads, the read-heavy domain.

| tier | ops/s | `/catalog` | `/orders` | `/auth` |
|---|---|---|---|---|
| **T4 · 300K** | 20K | 20K − 1.8K − 2.0K = **16.2K/s** | 20K/11 = **1.8K/s** | 10% × 20K = **2.0K/s** |
| **T5 · 500K** | 33.3K | 33.3K − 3.0K − 3.3K = **27.0K/s** | 33.3K/11 = **3.0K/s** | 10% × 33.3K = **3.3K/s** |

**Replica counts** = `ceil(load ÷ 556)`, then up to the next EVEN number — a stateless pool that
cannot be halved cannot survive losing half of itself, and both stateless pools already in the cut
are even (`app` ×6/×12, `workers` ×4). The ×3 read replicas are not a counter-example: a stateful
follower set is sized by lag and read fan-out, not by halving. Only `catalog-svc` at T5 is moved by
this step at all (48.5 → 49 → 50); no other rounding is applied.

| service | T4 raw | **T4 count** | T5 raw | **T5 count** |
|---|---|---|---|---|
| `catalog-svc` | 16.2K/556 = 29.1 | **×30** | 27.0K/556 = 48.5 | **×50** |
| `order-svc` | 1.8K/556 = 3.3 | **×4** | 3.0K/556 = 5.5 | **×6** |
| `auth-svc` | 2.0K/556 = 3.6 | **×4** | 3.3K/556 = 6.0 | **×6** |
| *fleet total* | | **38** | | **62** |
| *same load on ONE pool* | 20K/556 = 36.0 | 36 | 33.3K/556 = 60.0 | 60 |

Three things the reader gets for free from those numbers, none of which needed a new caption:

1. **Decomposition did not shrink the fleet** (38 ≈ 36, 62 ≈ 60). It split one knob into three.
2. **The knobs are 7.5× apart** (×30 vs ×4). The sheet's own T3→T4 boundary argues exactly this —
   "one scaling knob for three workloads whose read:write ratios differ 10×" — and the ×N subs are
   the first place in the cut where that claim is *visible* rather than asserted.
3. **`auth-svc` and `order-svc` land on the same count** (2.0K/s vs 1.8K/s). Recorded because it is
   what the arithmetic says, not smoothed into a prettier 8/4/2 ladder.

### What changed on the canvas (acts 4 and 5 only)

| node | act | before | after |
|---|---|---|---|
| `auth-svc` | 4 | plain box, sub `sessions · tokens` | + 2 ghosts, sub `x4 · sessions` |
| `catalog-svc` | 4 | plain box, sub `read-heavy` | + 2 ghosts, sub `x30 · read-heavy` |
| `order-svc` | 4 | plain box, sub `order writes` | + 2 ghosts, sub `x4 · order writes` |
| `auth-svc` | 5 | compressed box, sub `sessions · tokens` | + 2 ghosts **inside a `scale(0.85)` wrapper**, sub `x6 · sessions` |
| `catalog-svc` | 5 | compressed box, sub `read-heavy` | + 2 ghosts at 0.85, sub `x50 · read-heavy` |
| `order-svc` | 5 | plain box (BASE weight), sub `order writes` | + 2 ghosts at full scale, sub `x6 · order writes` |

Each node's `<title>` gains one count clause ("— four replicas;"), so the tooltip/a11y channel does
not contradict the picture the way it would if only the drawing were fixed. Nothing else moved: no
caption, no window, no keyframe, no transform, no chip, no other node, no manifest field.
`tests/run_golden_regression.py` re-derives 11 windows / 28 keyframes / 234 stops at max deviation
**0.0000 pp** after the amendment — the proof that the timeline is untouched.

**Ghost geometry is copied, not re-invented**: the same `-14/+14` and `-7/+7` offsets, the same
`.node__shape .node__ghost--1/2` classes with `style="fill:none;opacity:var(--ghost)"`, that the
T2/T3 `app` and `workers` nodes already use — so `verify_edge_anchors.py`'s structural
discriminator (drop `ghost`, keep the last `.node__shape`) keeps working unchanged, and the veteran
ladder's `--ghost:.2/.33` applies to the T5 pair automatically. The offset was NOT retuned: no
camera hold's must-show bbox moved (they are declared rectangles, and every ghost lies inside its
hold's bbox — worst case the T5 `a5a` frame, whose bbox starts at x=660 against a leftmost ghost
edge at x=1056). The T4 `a4a` spotlight bracket is out-poked by 2px at the order-svc ghost's
bottom-left corner, which is *identical* to what the frozen `workers` node already does under the
`a3b` bracket — precedent kept, not a new artefact.

**Sub format.** The count leads, because all four pre-existing replica subs in this cut lead with
it (`x6 replicas`, `x12 · one deploy`, `x3 · catalog reads`, `x4 consumers`) — a lesson persists in
the FORM it was taught in. Measured at 1920×1080 against the containment gate's own budget
(160 − 2×6 = **148** world px at full size; 136 − 2×6 = **124** px inside the compressed 0.85 box):

| sub | width | budget | verdict |
|---|---|---|---|
| `x4 · sessions` / `x6 · sessions` | 92.6 / 79.8 | 148 / 124 | fits |
| `x30 · read-heavy` / `x50 · read-heavy` | 121.3 / 104.7 | 148 / 124 | fits |
| `x4 · order writes` / `x6 · order writes` | 116.0 / 115.6 | 148 / 148 | fits |
| ~~`sessions · tokens · x4`~~ | **152.5** | 148 | **overflows — rejected** |
| ~~`sessions · tokens x4`~~ (compressed) | **124.6** | 124 | **overflows — rejected** |

So `auth-svc`'s sub trades the word "tokens" for the count: no format that keeps both fits either
box, the count is the lesson being repaired, and "tokens" survives in the node's `<title>`, in the
Phase 1 — COMPONENTS row, and in `auth-db`'s ownership claim.

### `shard-router` (and `api-gateway`, `alb`, `cdn`): checked, deliberately LEFT singular

A router tier is replicated in reality, so the question is real. It is not drawn stacked here, for
a reason this file already commits to: **the replica-stack idiom in this cut is attached to the
`shape-rounded-rect` deployable and the `shape-cylinder` follower-set, never to the edge/routing
tier.** `alb` (T2, T3), `cdn` (T3–T5) and `api-gateway` (T4, T5) are all drawn as ONE symbol of a
managed tier — a fork or a hexagon — and none of them was amended. Stacking `shard-router` alone
would contradict the three routing nodes standing beside it; stacking all four is a different,
larger idiom decision about what a hexagon means, touching 8 node instances across 4 acts, and it
is not what the user asked for. Two smaller reasons, recorded: the router occupies the single
primary's exact former slot, which is the act's "this became that" argument, and three outlines
behind a router that fans out to exactly three shards invites the wrong reading (routers ≠ shards).
`workers` and `read replicas` already carry their stacks; `queue` and `pub/sub stream` are async
plumbing, not compute, and are correctly unstacked; the three `pg-shard`s are disjoint key ranges
and must never be stacked (already stated in Phase 1).

---

## AMENDMENT #6 — 2026-08-30 (three derived retirement ghosts; the gate stopped taking the cut's word for it)

Code review of phase 03 (REQUEST_CHANGES, item 2): `ghostOf` was VOLUNTEERED, so deleting the
sheet's `ghost-of` cell together with the ghost group left every gate green over a cut that buried
nobody — fix by deletion. The requirement is now DERIVED in `scripts/verify_retired_ghost.py`: the
act that drops an id (`ids(act N−1) − ids(act N)`, the same subtraction `acts/delta-mismatch`
already holds the manifest to) owes it one outline farewell there, and `ghostOf` becomes
documentation that can only ADD to that set.

That is a claim this cut did not pay. It retired **`alb` and `app` at T4** and **`postgres` at T5**
and drew no farewell for any of them — one ghost (`app-monolith`, T2) for four retirements. Three
ghost groups are therefore ADDED to the file, in the same idiom as the T2 one (160×80, `fill:none`,
dashed, opacity .38, `aria-hidden`, no `data-node-id`):

| act | ghost | at | why there |
|---|---|---|---|
| 4 | `alb` | `translate(350,375)` | its old C2/R1 slot is `api-gateway`'s now |
| 4 | `app` | `translate(590,375)` | its old C3/R1 slot is `auth-svc`'s now |
| 5 | `postgres` | `translate(350,375)` | its old C3/R2 slot is `shard-router`'s now |

The band `y 375–455, x 350–750` is empty in BOTH acts — no node box, no edge segment, no label
(the nearest is `/orders` at x 945) — so nothing moved to make room: **no node, edge, window,
keyframe, caption, hold or camera value changed**, and the three boxes paint under the cast in the
one strip the layout never used. `acts[]` gains `ghostOf` for acts 4 and 5 and the ACT DELTA row
gains the matching `ghost-of` cells; `emit_act_delta.py` still reproduces `acts[]` byte for byte.

**The legend was naming two components that had left.** `service ×6 alb · gateway · services ·
workers · router` and `data ×6 postgres · shards · replicas · redis` — but `alb` retired at T4 and
`postgres` at T5, and this legend is read as the cast of the FINAL act (its `×N` counts are already
checked against act 5). The prose now reads `service ×6 gateway · services · workers · router` and
`data ×6 auth-db · shards · replicas · redis`: same counts, every name a node act 5 draws. Closed at
the gate too — `verify_legend_fact.py` fails `legend/member-retired` when a member token is the id
or rendered label of a component the final act does not draw. Collective prose (`services`,
`shards`, `replicas`) matches no id and is deliberately left alone: the check catches the retired
NAME, not the abbreviation.

Also in this pass, and visible nowhere: `.is-ghost … { fill:none }` is now required in the cut's
`<style>` (deleting that one rule repainted every ghost solid with the gate still green), a declared
`moved` waives only an ADJACENT 4×3 cell (`redis` C5/R1→C5/R2 still passes; a jump across the frame
is a removal plus an addition), every `path.edge` in a lens act must declare both endpoints, a lens
hold with no window FAILS instead of passing zero comparisons, and the shrink tripwire now tracks
`holds[].anchor` and the `acts[]` numbers as well as features and hold ids.

**Verification.** `verify_all.py … --serve` → **37 PASS / 3 N-A**, exit 0, unchanged from
AMENDMENT #5; golden regression re-derives at 0.0000 pp; `progressive-500k-ccu.html`,
`compare-chat-pubsub.html` and `vibe-code-voi-ai.html` are byte-untouched. SHA-256
`e37289801047eb0344ad433bbba0c026dd11c99d23eb06fa1b8b8237a59516bb` →
`474b622cd96278614e0fade42afc05f5682040226385a9bcf32e3d579c862498`.

**Contact sheet.** Re-shot, 25 frames, and read frame by frame: the three ghosts sit alone in the
empty band, dashed and faded, nothing overlaps. But the cut CHANGED after the 2026-08-30 sign-off,
so that sign-off does not carry: **visual re-review needed**. reviewed-by: pending (user).

---

## AMENDMENT #4 — 2026-08-30 (identity, act delta, one retired ghost, an anchor beat)

Plan `260830-1325-archify-lessons-gates-tier-identity-floor`, phase 03. This cut is the exemplar for
the act rules (`references/multi-pane.md` → continuity, retirement, transition captions), so it is
where those rules stop being prose a reviewer has to hold in their head.

**Added to the file.**
- `data-node-id` on all **46** node groups, ids taken from the Phase 3 component mapping table
  (`pub/sub stream` → `pubsub-stream`, `read replicas` → `read-replicas`,
  `pg-shard 1/3 · 2/3 · 3/3` → `pg-shard-1 · pg-shard-2 · pg-shard-3`; every other id is its label).
- `data-from`/`data-to` on all **48** `path.edge` elements, derived from which node box each
  endpoint actually anchors on. Nothing on screen changed; this is the graph the cut always drew,
  written down. Phase 04's semantic edge checks read it.
- Five delta chips, one per act title card, at a FIXED `translate(585,180)` — **REMOVED the same
  day by user decision; see the follow-up at the end of this amendment** — 16px right of the
  widest verdict pill (act 3's 211px), so the chip holds one column in every act exactly as every
  other slot in this cut does. `+3 −0 · +3 −1 · +4 −0 · +6 −2 · +4 −1`. Static scenery, no JS; the
  numbers are gated against the ACT DELTA row by `acts/delta-chip-mismatch`.
- ONE retired-component ghost: `app-monolith` in act 2, outline-only (`fill:none`, dashed,
  opacity .38), at `translate(830,375)` — one row BELOW its old C3/R1 slot, because `alb` stands in
  that slot now. It carries `data-ghost-of`, deliberately NOT `data-node-id`: a ghost is the memory
  of a component, not the component, and giving it the id would put `app-monolith` back into act 2's
  id set and make that act's own delta a lie.
- The legend's five role entries carry the FINAL act's real counts —
  `client ×1 · service ×6 · data ×6 · async ×2 · infra ×1` — and each declares the role it stands
  for (`data-legend-role`), so `legend/entry-unbacked` and `legend/count-wrong` can hold it to them.
  Swatch x positions re-spaced 150/290/640/990/1200 → **150/300/700/1090/1320** to make room; the
  member lists and the state/weight rows below are unchanged. Measured in the browser: the widest
  entry (`service`) ends at x 653 against the next swatch at 700.

**Added to the sheet.** `## Phase 2 — ACT DELTA`, the machine twin of `## Phase 1 — TIER
BOUNDARIES`. The prose table is untouched — it is the argument, and no parser can check an
argument. The twin says the same story in ids and is the ONLY path from this sheet to the
manifest's `acts[]` (`emit_timeline.py --acts-table`).

**Added to the manifest.** `features` gains `node-identity` and `act-delta`; `acts[]` carries the
five deltas; one hold is ADDED.

**The one hold change.** `a3-anchor` — a `read`-gate anchor beat on `postgres`, the node act 3 and
act 4 both draw — window `39.1667,40.4067`, carved out of `a3b`'s tail, which shortens `a3b` from
`35,40.4167` to `35,39.1667`. **No hold id was removed or renamed, and no window moved to make room:
the master, every keyframe, every transform and every on-screen instant are unchanged**, because
the camera already sits at one continuous `25%,55.4167%` pose across a3a/a3b/a3-anchor/a4a/a4b.
The anchor ends at 40.4067% — the last instant act 4 is still parked off-canvas. Written across the
crossfade first (40.4167–41.6667), its midpoint had 45 ink texts and 23 segments in frame instead
of 19 and 9, and hold-geometry reported act 3's write edge crossing act 4's `catalog-svc`: a defect
no viewer ever sees. The rule that came out of it is now in `references/camera-beat.md`.
`fs_min` is **18** here, not the 15 every other hold declares: an anchor hold exists to keep one
component's NAME readable across the crossfade, so its essential text is the `.node__label`, and
`fs_min_source` says so. 18 × 1.3431 = 24.18 frame px against the landscape read floor of 24.

**`role-lens` was evaluated and NOT taken into this golden.** A lens beat needs its own window, and
this cut's 48s master is fully spoken for: acts 1–5 tile 5%→75% with no gap, and every beat inside
them owns a caption and a spotlight set. Adding one would have moved an existing window, which is
the one thing the anchor beat was designed to avoid. It ships PROVEN on
`tests/fixtures/tier-identity/` instead (positive + two negatives), and the gate prints `N-A` here
because the feature is not declared — an honest absence, not a skipped check. Revisit it only with a
master re-cut on the record.

**`redis:moved` is the one declared move.** The zone rule compares 4×3 viewbox grid cells, so every
nudge inside a cell is free. `redis` is the only component that changes ROW: C5/R1 in T2–T3
(y=250) → C5/R2 from T4 (y=375), because `auth-db` takes R1 when the services get their own stores.
Declared as `redis:moved` in act 4's ACT DELTA row; an undeclared one fails
`acts/identity-zone-drift`.

**`app`/`alb` → the three services is a REMOVAL plus an ADDITION, not a rename.** Archify's rule,
adopted verbatim and recorded here because it is the T4 boundary's whole lesson: claiming the same
component survived would teach that microservices are a bigger `app`.

**One latent drift the round-trip exposed and this amendment repairs.**
`tests/fixtures/progressive-500k-5tier.timeline.tsv` still carried `cap-a5a`'s pre-AMENDMENT #3
string (`hash(user_id) picks the owner…`). AMENDMENT #3 changed that caption in the cut and the
manifest but not in the event-table fixture, and nothing caught it: the golden regression diffs
`data-window` attributes and `@keyframes` stops, never caption TEXT. The `--acts-table` round-trip
diffs the whole emitted fragment, so it surfaced immediately. The fixture now reads
`hash(shard key) …`, and `emit_timeline.py --acts-table` reproduces this manifest's `acts[]`,
`captions[]` and every windowed hold byte for byte. No cut byte changed.

**Verification.** `python3 scripts/verify_all.py examples/progressive-500k-5tier.html --serve` →
**37 PASS / 2 N-A**, exit 0, with `tier-identity`, `act-delta`, `retired-ghost` and `legend-fact`
all PASS and `role-lens` N-A. Golden regression re-derives at 0.0000 pp; the camera-hold fixture
gains the `a3-anchor` row and `a3b`'s shortened window. `progressive-500k-ccu.html`'s SHA-256 is
unchanged. SHA-256 rows updated in `examples/README.md` § A.

**Contact sheet.** Re-shot, 25 frames (`contact-sheet.mjs --manifest`), and looked at frame by
frame. reviewed-by: viettranx (user) · 2026-08-30 · verdict: accept · contact sheet after chip removal, 25 frames.

**AMENDMENT #5 — follow-up, 2026-08-30: the five delta chips were REMOVED (user decision,
after the contact sheet).** Looking at the frames, the user ruled the `+N −N` pill out of the golden: all five
`g.act-chip` groups and the CSS rules that styled them were **removed** from the cut, and nothing
else — no node, edge, window, keyframe, caption, hold or camera value moved, and the manifest is
byte-identical, ACT DELTA row included. The chip stays shipped as OPT-IN scenery
(`templates/snippets/act-delta-chip.html` + `cb-delta-chip` in `templates/snippets/camera-beat.css`):
this sheet's `## Phase 2 — ACT DELTA` row is the FACT, the chip is one optional rendering of it,
absent by default. `acts/delta-chip-mismatch` moved to a row of its own, `delta-chip`, which reports
**N-A** (*"no chip rendered — optional scenery"*) when no act draws one and fails only when a chip
EXISTS whose numbers disagree with its delta — never a quiet PASS on nothing. Re-verified:
**37 PASS / 3 N-A**, exit 0 (the added N-A is `delta-chip`). Contact sheet re-shot, 25 frames, no
chip in any act frame. SHA-256
`d961a14434cb36661fbc5540c8fd657b7592afa70de5202dc88091e3f64b3a86` →
`e37289801047eb0344ad433bbba0c026dd11c99d23eb06fa1b8b8237a59516bb`, recorded in
`examples/README.md` § A. reviewed-by: viettranx (user) · 2026-08-30 · verdict: accept · contact sheet after chip removal, 25 frames.

---

## AMENDMENT #3 — 2026-08-26 (the shard routing key goes universal)

**On the record: user-directed.** The user ruled that `hash(user_id)` is a *specific* choice
standing in a cut whose whole subtitle is THE BASIC PATTERNS, and that a viewer can read the
specific choice as part of the pattern. The lesson this act teaches is **"the shard key's hash
picks exactly one owner"** — not *which column* is the key. `user_id`, `order_id`, `tenant_id` are
all valid instantiations of the same mechanism, and choosing between them is a per-system decision
that depends on the access pattern, not on the ladder. A basic-patterns cut teaches the mechanism;
the key column is where a real system's judgement starts, and naming one on screen quietly ends
that judgement before it begins. So every user_id-specific string becomes the universal form.

Four strings changed, in the four channels that carried the key. No caption WINDOW, no keyframe, no
geometry, no chip, no node, no edge, no transform; `tests/run_golden_regression.py` re-derives this
cut's 11 windows / 28 keyframes / 234 stops at max deviation **0.0000 pp** after the amendment. One
caption BOX width was re-baked (a longer string needs a wider card — the box is a function of the
measured text, never hand-nudged); the box is scenery, not timeline.

### Before / after — every string that named the key

| # | channel | slot | before | after |
|---|---|---|---|---|
| 1 | on-canvas | `shard-router` `text.node__sub` (`x=80 y=64`) | `by hash(user_id)` | `by hash(key)` |
| 2 | on-canvas | `.cap-a5a` caption text | `hash(user_id) picks the owner: this write is 7c, so only shard 2 sees it.` | `hash(shard key) picks the owner: this write is 7c, so only shard 2 sees it.` |
| 3 | a11y | `shard-router` `<title>` | `Shard router — picks the owning shard from the hash of the user id` | `… from the hash of the shard key` |
| 4 | a11y | `<desc id="d">`, act 5 sentence | `…picks the owning shard from the hash of the user id; this write hashes to 7c…` | `…from the hash of the shard key; this write hashes to 7c…` |

**Already generic, deliberately untouched:** the routed-path edge label `hash 7c`, the three shard
subs `hash 00–55` / `hash 56–aa` / `hash ab–ff`, and every shard `<title>` ("owns hash range 00 to
55; idle for this write"). They name a hash SPACE and a position in it, which is the mechanism
itself. The routed value `7c` is likewise not a key, it is the key's hash — the amendment does not
touch it, and the caption still points at it.

### Why the sub is `by hash(key)` and not `by hash(shard key)`

The `shard-router` shape is `shape-hexagon`, and `verify-text-containment` measures a hexagon at
the text's OWN y-band (`inset = |Δy from mid| × 20/40`), not at its widest point. The sub sits at
`y=64`, 24px below the mid-line, so its budget is **120 world px**, not the 148 a 160-wide
rectangle would give. Measured at 1920×1080 through the server:

| candidate | width | budget @ y=64 | verdict |
|---|---|---|---|
| `by hash(user_id)` *(frozen, before)* | 117.91 | 120 | fits — **by 1.05px** |
| `by hash(shard key)` *(first choice)* | 135.36 | 120 | **overflows by 7.68px — rejected** |
| `by hash(shard-key)` | 138.05 | 120 | overflows by 9.02px — rejected |
| `by shard-key hash` | 131.31 | 120 | overflows by 5.66px — rejected |
| `hash(shard key)` *(drops the preposition)* | 113.81 | 120 | fits by 3.09px — not taken |
| **`by hash(key)`** *(shipped)* | **91.34** | 120 | **fits by 14.33px** |

Recorded because it is the load-bearing fact: the frozen string had **1.05px** of clearance, so
this slot could never have absorbed a longer word. `by hash(key)` was the fallback named in the
authorization, and it is the only candidate that leaves the slot with real headroom for a fork
whose `--font-label` runs wider (mono runs ~20% wider at equal size — the caption-rebake header's
own warning). `hash(shard key)` also fits, but it drops the `by` that makes the sub a routing
CLAUSE ("routes … by hash of the key") rather than a bare expression, and 3px of clearance is the
same trap the frozen string was already sitting in.

The sub and the caption therefore read at two different lengths on purpose: the sub is the
mechanism in the narrowest slot in the cut (`by hash(key)`), the caption spells the same thing at
full width one beat later (`hash(shard key) picks the owner`). Both are universal; neither names a
column.

### Why the caption is a token swap, not the sentence from the authorization

The authorization suggested *"The shard key's hash picks the owner: this write is 7c, so only shard
2 sees it."* — **17 words** in `.cap-a5a`'s unchanged 3200ms window = **5.31 wps**, over this
repo's golden-calibrated **~5 wps** ceiling (`references/camera-beat.md` → Caption pace) and above
the cut's own densest caption (4.69, `cap-a2`). Swapping the token in place keeps the sentence at
its frozen **14 words / 4.38 wps** and says the same thing, so the pace table below is unchanged in
every column but one. Caption pace is a timing property; the amendment is a wording one.

### The one geometry byte: `.cap-a5a`'s box

`scripts/browser-checks/rebake-caption-boxes.mjs` re-measured all nine caption cards against the
running page. Eight re-baked byte-identical; only `a5a` moved, because only `a5a`'s text changed:

| | x | width |
|---|---|---|
| before | 693.6 | 532.8 |
| after | **684.9** | **550.1** |

+17.3px of text (`shard key` for `user_id`), split evenly around the centred `x=960` anchor
(PAD_X=14 each side, as for every other card). `y`, `height`, `rx`, `ry` untouched; the card runs
`x 684.9..1235.0`, so it clears the 1920 canvas by 684.9px left / 685.0px right, stays narrower
than `cap-a5b` (633.4 wide) and `cap-r` (903.6) which already sit in the same band, and
`verify-caption-boxes` reports all nine captions inside their card. The other eight cards re-baked
**byte-identical**, which is the check
that the rebake measured the same page and changed only what the amendment changed.

---

## The four TRIALLED design principles (each a deliberate choice, with its rationale)

**P1 — Foreground budget: ≤ ~5 nodes at full weight per beat; veterans render one step receded.**
`flat-minimal` ships exactly one stroke step (`.node--primary` = `calc(var(--stroke-w) * 1.4)`).
This cut walks that same ×1.4 step in BOTH directions rather than inventing a second language:

| tier | stroke | opacity | derived from |
|---|---|---|---|
| new in this act | `3.2px` | 1 | the frozen golden's `.node--new` (`examples/progressive-500k-ccu.html:58`) |
| base | `1.8px` (`--stroke-w`) | .9 | flat-minimal `:root` |
| veteran (receded) | `calc(var(--stroke-w) / 1.4)` = **1.286px** | **.65** on `.node__body` | the ×1.4 step, inverted; .65 is flat-minimal's own `.node__detail` ink tier |
| replica ghosts, receded | — | .3 × .65 = **.2** / .5 × .65 = **.33** | the same .65 factor applied to the existing ghost tiers |

The opacity rides `.node__body` only — the idiom `.is-idle` already uses — so a veteran's LABEL
keeps full ink and stays AA-legible. `.65` sits one step back from ink and well clear of the
`.is-idle` floor (`.35`), which is correct: a veteran is still running, not idle.

**P2 — Solved lessons compress.** In T5, `auth-svc`, `auth-db` and `catalog-svc` keep their slots
and drop to the supporting `scale(0.85)` box SKILL.md already defines, with labels/subs at
flat-minimal's OWN base sizes (`--fs-label:16px` / `--fs-sub:13px`) instead of this cut's primary
sizes (18/15). At the T5 territory k of 1.3431 the compressed sub renders 17.5 frame-px, just above
the landscape supporting floor of 17. No new value is introduced. `auth-db` compresses with its
owner — a store left at full detail while its only client shrinks would break the pair.

**P3 — Fixed canvas zoning across all five acts.** Columns and rows below. A component keeps its
column in every act it appears in; `redis` is the one component that changes ROW (R1→R2 at T4)
because its reader changes from `app` to `catalog-svc` — zone kept, row follows the client.
`shard-router` deliberately inherits the primary's exact slot (C5/R3) so the box that was the
ceiling visibly becomes a routing decision. Consequence: every act hold frames the same rectangle,
so growth reads as boxes APPEARING in fixed slots rather than as a re-drawn diagram.

**P4 — No grouping frame around the services** (user decision after the v2 A/B). The a4a spotlight
beat plus the `MICROSERVICES` act title card carry the grouping; there is no hull, no cell, no
dashed container anywhere in the file.

### The zone map (world coordinates, identical in every act)

| column | x | contents by act |
|---|---|---|
| C1 clients | 350 (0.85 box → 486) | users, T1–T5 |
| C2 edge | 590 | cdn, T3–T5 |
| C3 front door | 830 | app-monolith T1 · alb T2–T3 · api-gateway T4–T5 |
| C4 compute | 1070 | app T2–T3 · auth-svc / catalog-svc / order-svc T4–T5 |
| C5 primary data | 1330 | redis T2–T3 · auth-db T4–T5 (R1) · redis T4–T5 (R2) · postgres T1–T4 / shard-router T5 (R3) · pg-shard 2/3 T5 (R4) |
| C6 far data | 1560 | read replicas T3–T5 (R2) · pg-shard 3/3 T5 (R4) |
| async rail | 550 / 830 / 1090 | workers (550, R3) · queue (830, R3) · pub/sub stream (830, R4, 200 wide) · pg-shard 1/3 (1090, R4) |

Rows: **R1 y=250** (users 256) · **R2 y=375** · **R3 y=500** · **R4 y=640**.
Act identity block, fixed top-left in every act: title y=140, load-band sub y=166, verdict pill
y=180–208. Caption slot fixed at y=767.6–802.8 (y=758–803 for the recap card).

**Where P3 lost to geometry (recorded, not absorbed):** the queue/worker pair sits in the
lower-LEFT (x 550/830) rather than the lower-MIDDLE the directive names. The drain edge has to be
short and horizontal for `1 job → 1 worker` (104px of label) to clear both boxes; every
lower-middle arrangement tried put a diagonal there whose label touched a node. The rail still
runs along the lower band, left of the data column.

---

## Phase 1 — COMPONENTS

| name | role | responsibility (a claim) | count | guarantees enforced HERE |
|---|---|---|---|---|
| users | client | browsers issuing the request mix | N (CCU per tier) | — |
| app-monolith | service | one deployable owning every domain | 1 (T1 only) | — |
| postgres | data | the single primary datastore | 1 (T1–T4) | durability of every write |
| alb | service | spreads requests across app replicas | 1 (T2–T3) | even fan-out |
| app | service | stateless request handler pool, still ONE deployable | 6 (T2), 12 (T3) | none — stateless by design |
| redis | data | read-through cache, 90% hit | 1 (T2–T5) | absorbs 9 of every 10 reads |
| cdn | infra | static + API edge cache | 1 (T3–T5) | first-hop read absorption |
| queue | async | durable buffer for emails and exports | 1 (T3–T5) | at-least-once delivery of a job to ONE worker |
| workers | service | drains the queue off the request path; also a stream subscriber | 4 (T3–T5) | one job is handled by exactly one worker |
| read replicas | data | serve the reads that miss the cache | 3 (T3–T5) | read scale-out; eventual consistency only |
| api-gateway | service | one front door, routes each path prefix | 1 (T4–T5) | single entry, per-path routing |
| auth-svc | service | sessions and tokens | 4 (T4), 6 (T5) — AMENDMENT #2 | owns auth data — nobody else reads auth-db |
| auth-db | data | auth-svc's private store | 1 (T4–T5) | service-private data boundary |
| catalog-svc | service | read-heavy catalog domain | 30 (T4), 50 (T5) — AMENDMENT #2 | — |
| order-svc | service | every order write, and the events it emits | 4 (T4), 6 (T5) — AMENDMENT #2 | publishes exactly one `order.created` per order |
| pub/sub stream | async | one publish reaches every subscriber | 1 (T4–T5) | fan-out; 2 subscribers drawn |
| shard-router | service | picks the owning shard from hash(shard key) | 1 (T5) | a key is owned by exactly ONE shard |
| pg-shard 1/3, 2/3, 3/3 | data | disjoint hash ranges of the order store | 3 (T5) | no key lives in two shards |

**Singularity by design (never stacked):** app-monolith, redis, auth-db, queue, pub/sub stream, and
each individual shard (three shards are three DIFFERENT key ranges, not N copies) — plus the
edge/routing tier drawn as one managed symbol: alb, cdn, api-gateway, shard-router
(AMENDMENT #2 records why the router stays singular).
**Stacked (count N → `shape-replica-stack` ghosts):** app (×6/×12), workers (×4), read replicas
(×3), and — AMENDMENT #2 — every domain service: catalog-svc (×30/×50), order-svc (×4/×6),
auth-svc (×4/×6). *Corrected:* this line previously read "each domain service" under Singularity,
which taught that decomposition replaces replication. It does not.

## Phase 1 — FLOWS

- **Happy read (all tiers):** users → [cdn] → [alb | api-gateway] → app/catalog-svc → redis
  (90% hit) → on miss → postgres (T1–T2) / read replicas (T3–T5).
- **Happy write:** users → … → app/order-svc → postgres primary (T1–T4) /
  shard-router → exactly ONE pg-shard (T5).
- **Async point-to-point (T3–T5):** app/order-svc → queue → workers (1 job → 1 worker).
- **Fan-out (T4–T5 only):** order-svc → pub/sub stream → catalog-svc (`invalidate cache`) and
  workers (`send receipt`). One publish, two subscribers.
- **Replication (T3):** postgres → read replicas (`replica sync`, binary-stream), 1.8s behind.

## Phase 1 — NUMBERS (the only place numbers live)

Display rule fixed once: abbreviate to K/M in every display string; small numbers stay exact.

**The load model, stated once and used everywhere:** ~1 operation per user per 15s, mixed
**10 reads : 1 write** — so 1 of every 11 operations is a write.

```
ops/s    = CCU / 15
writes/s = ops/s / 11 = CCU / 165
reads/s  = ops/s × 10/11
```

| CCU | ops/s | reads/s | writes/s | reads that miss a 90% cache |
|---|---|---|---|---|
| 1K | 67 | 61 | 6 | 6 |
| 10K | 667 | 606 | 61 | 61 |
| 100K | 6.7K | 6.1K | 606 | 606 |
| **300K** | 20K | 18.2K | **1.8K** | 1.8K |
| **330K** | 22K | 20K | **2.0K ← the single-primary ceiling** | 2.0K |
| 500K | 33K | 30K | 3.0K | 3.0K |

| figure | value | where it renders |
|---|---|---|
| read : write ratio | **10 : 1** | edge labels `read ×10` / `write ×1`, cap-a1, legend, `<desc>` |
| cache hit rate | 90% | redis sub `90% hit`, cap-a2 |
| reads that survive the cache | 1 unit of 10 | edge label `miss ×1` |
| T1 ceiling | 1K CCU | act-1 sub, users sub, verdict, cap-a1 |
| T1 break | 100/100 connections | chip `100/100 CONNS`, cap-a1 |
| monolith size | 4 vCPU | node sub |
| T2 ceiling | 10K CCU | act-2 sub, users sub, verdict |
| T2 fleet | 6 app replicas, 8 boxes total | app sub `x6 replicas`, verdict `8 boxes`, cap-a2 |
| T2 break | half the primary's work is reads | chip `READS 50%`, cap-a2 |
| T3 ceiling | 100K CCU | act-3 sub, users sub, verdict |
| T3 fleet | 12 app replicas, 4 workers, 3 read replicas | node subs, verdict, cap-a3a/b |
| T3 break | one deployable, three domains | verdict `1 deployable`, app sub `x12 · one deploy`, cap-a4a, cap-r |
| replica lag | 1.8s | chip `LAG 1.8s`, legend |
| T4 ceiling | 300K CCU | act-4 sub, users sub, verdict |
| T4 shape | 3 domain services, 1 event rail | verdict `3 services`, cap-a4a/b |
| T4 service fleet (AMENDMENT #2) | catalog ×30, order ×4, auth ×4 (38 total) | service subs `x30 · read-heavy`, `x4 · order writes`, `x4 · sessions` |
| T5 service fleet (AMENDMENT #2) | catalog ×50, order ×6, auth ×6 (62 total) | service subs `x50 · read-heavy`, `x6 · order writes`, `x6 · sessions` |
| per-replica capacity (AMENDMENT #2) | ~556 ops/s (= T3's 6.7K ops/s ÷ 12 replicas) | nothing on screen; it is the divisor behind every `xN` above |
| T4 seed | the write path never moved | chips `HOT ROW` + `2K WPS`, cap-a4b |
| T5 ceiling | 500K CCU | act-5 sub, users sub, verdict |
| shard key | hash(shard key) — universal by AMENDMENT #3; the key COLUMN is a per-system choice, never named on screen | shard-router sub `by hash(key)`, cap-a5a `hash(shard key)` |
| shard ranges | `00–55`, `56–aa`, `ab–ff` | shard subs |
| the routed key in this frame | `7c` (∈ 56–aa → shard 2/3) | edge label `hash 7c`, cap-a5a |
| per-shard write load at 500K | ~1K writes/s of a ~2K ceiling | cap-a5b, `<desc>` |
| stream fan-out | 1 publish → 2 subscribers | pub/sub sub `1 publish → 2 subs` |

**Derivations behind the two chips a reader could challenge.**
- `100/100 CONNS` (T1): 67 ops/s × ~1.5s per op while the 4-vCPU box is CPU-bound ⇒ ~100 requests
  in flight at once ⇒ the 100-connection pool is exactly full.
- `READS 50%` (T2): at 10K, 61 miss-reads/s + 61 writes/s reach the one primary. Half of its work
  is reads a replica could serve — which is precisely the argument for T3's read/write split.
- `2K WPS` (T4 seed): the boundary arithmetic. writes/s = CCU/165 crosses 2 000/s at
  **CCU = 2000 × 165 = 330 000 ≈ 300K**. That is the T4→T5 boundary and the only place `2K WPS`
  appears in the cut.

## Phase 1 — GUARANTEE OWNERSHIP (one owner each)

| guarantee | owner | mechanism |
|---|---|---|
| every write is durable | postgres (T1–T4) / the owning pg-shard (T5) | the primary of that key range |
| a key lives in exactly one shard | shard-router | hash(shard key) → disjoint range |
| a job runs once, on one worker | queue | point-to-point delivery; workers is the only consumer |
| an event reaches every interested party | pub/sub stream | fan-out to all subscribers |
| 9 of 10 reads never touch a database | redis | read-through, 90% hit |
| auth data is private to auth-svc | auth-db | no other service edge touches it |
| reads scale without touching the write path | read replicas | followers of the write stream |

**Audits.**
- *Race*: the only check-then-act is shard selection, and it is a pure function of the key — no
  race. Order writes are single-shard, so no cross-shard transaction is claimed anywhere.
- *Recovery*: every acquired resource returns — a queue job is acked by the worker that took it
  (`1 job → 1 worker`); a cache entry is released by the stream's `invalidate cache`.
- *Pre-condition*: shard ranges and the routing table exist before t=0; the first write does not
  create them. The cache is cold-start safe because a miss falls through to a replica.

## Phase 1 — TIER BOUNDARIES

| tier | model | what broke | what T(n+1) added |
|---|---|---|---|
| T1 0–1K | MONOLITH | 67 ops/s × 1.5s ⇒ the single 100-connection pool is full | alb + 6 app replicas + redis |
| T2 1K–10K | HORIZONTAL SCALE-OUT | 61 miss-reads/s + 61 writes/s share one primary — half its work is reads | cdn + queue + 4 workers + 3 read replicas |
| T3 10K–100K | READ / WRITE SPLIT | **nothing is saturated.** One deployable owns auth, catalog and orders: one release, one blast radius, one schema, one scaling knob for three workloads whose read:write ratios differ 10× | api-gateway + 3 domain services + auth-db + pub/sub stream |
| T4 100K–300K | MICROSERVICES | the split moved the code, not the write path: 1.8K writes/s at 300K against one primary's ~2K/s ceiling (crossed at 330K) | shard-router + 3 pg-shards |
| T5 300K–500K | SHARD THE WRITES | holds: 3.0K writes/s over 3 primaries ≈ 1.0K each, ~2× headroom | — |

**The T3→T4 boundary is deliberately NOT a throughput number, and that is the cut's sharpest
teaching point.** Four of the five boundaries are load arithmetic; one is coupling. A junior dev's
most common wrong model is "microservices are a performance fix", and drawing a fake saturation
chip at 100K would have taught exactly that. `cap-r` names the asymmetry outright.

**Known semantic simplification (recorded, not hidden):** `HOT ROW` is used for *the orders table's
single write hotspot* — one primary, one WAL, one lock queue for every order — which is what
`hash(shard key)` sharding splits into three. A literal single hot row (one shared stock counter) is
a schema fix, not a topology fix; the cut does not claim otherwise anywhere, and the `<desc>` and
`<title>` strings say "every order write still lands on ONE Postgres primary".

---

## Phase 2 — ACT DELTA

The MACHINE TWIN of the TIER BOUNDARIES table above. That table is the argument — *what broke*,
*what T(n+1) added* — and stays exactly as it is, because no parser can check an argument. This one
says the same story in `data-node-id`s, and it is the only path from this sheet to the manifest:
`emit_timeline.py --acts-table <this sheet> --format json` prints `acts[]`, and
`scripts/verify_act_delta.py` then re-derives `added`/`removed` from the ids the cut actually draws
and fails the run if the two disagree. Separator `·`; `—` is empty. `changed` cells are `id:what`
(`topology` | `semantic` | `scope` | `moved`); `caption-alias` cells are `id=surface form`, the
escape hatch for a caption that names a component in prose rather than by its id.

| act | window | added | removed | changed | ghost-of | caption-alias |
|---|---|---|---|---|---|---|
| 1 | 5,15 | users · app-monolith · postgres | — | — | — | app-monolith=One box |
| 2 | 15,25 | alb · app · redis | app-monolith | — | app-monolith | app=Six replicas · redis=cache |
| 3 | 25,41.6667 | cdn · read-replicas · workers · queue | — | — | — | — |
| 4 | 41.6667,56.6667 | api-gateway · auth-svc · auth-db · catalog-svc · order-svc · pubsub-stream | alb · app | redis:moved | alb · app | api-gateway=gateway |
| 5 | 56.6667,75 | shard-router · pg-shard-1 · pg-shard-2 · pg-shard-3 | postgres | — | postgres | shard-router=hash(shard key) · pg-shard-2=shard 2 |

**Why `redis:moved` is declared and nothing else is.** The zone rule compares 4×3 viewbox grid
cells, not coordinates, so the identity gate frees every nudge inside a cell — `users` sits at
y=256 in all five acts, `postgres` holds C5/R3 from T1 to T4. `redis` is the one component that
genuinely changes row: C5/R1 in T2–T3 (y=250), C5/R2 from T4 (y=375), because `auth-db` takes R1
when the services get their own stores. That move is deliberate and is declared here; an
undeclared one fails `acts/identity-zone-drift`.

**`app` → `catalog-svc` is a removal plus an addition, not a rename.** The T4 boundary is the
coupling break: one deployable becomes three services with three stores. Writing it as a rename
would claim the same component survived, which is the opposite of the tier's lesson. Archify's
rule — a rename is a removal plus an addition — is adopted verbatim, and `alb`/`app` are therefore
`removed` in act 4 while the six services and the stream are `added`.

## Phase 2 — ACT MAP / STORYBOARD

Master **48000ms** = 10 × 4800ms beat. Every ambient loop divides it: flow 2400 (×20),
fill 2400 (×20), pulse 1600 (×30), dash 1200 (×40), shake 120 (×400).
Same master as v2 while carrying **one more act and three more captions**, so the per-beat pace is
tighter; below 48s the captions cross the ~5 wps ceiling (see the pace table).

| beat | act window (ms) | camera hold | k / tx / ty | gate | caption |
|---|---|---|---|---|---|
| intro | — | 0–1600 | 1 / 0 / 0 | overview | — |
| act 1 | 2400–7200 | a1 2400–6600 | 1.4388 / −364 / −115 | territory | cap-a1 |
| act 2 | 7200–12000 | a2 7200–11400 | 1.4388 / −364 / −115 | territory | cap-a2 |
| act 3 | 12000–20000 | a3a 12000–16400 · a3b 16800–19400 | 1.3431 / −430 / −72 | territory | cap-a3a, cap-a3b |
| act 4 | 20000–27200 | a4a 20000–23400 · a4b 23600–26600 | 1.3431 / −430 / −72 | territory | cap-a4a, cap-a4b |
| act 5 | 27200–36000 | **a5a 27200–31600** · a5b 32200–35400 | **1.8083 / −984 / −412** (read) · 1.3431 / −430 / −72 | **read** · territory | cap-a5a, cap-a5b |
| recap | 36000–48000 | r1..r5, 2400ms each | 1 / 0 / 0 | overview | cap-r |

Recap slots, in act order: act1 36000–38400, act2 38400–40800, act3 40800–43200,
act4 43200–45600, act5 45600–**48000** (the final act's last window runs to 100%, so the loop parks
on the finished design and frame 100% == frame 0%). Per `output-manifest.md`, the recap declares
**five separate camera holds r1..r5**, never one spanning hold.

**One camera hold per BEAT, not per act.** Acts 3, 4 and 5 each carry two captions, so each declares
two camera holds at the same transform. The reason is the same one that forces `r1..rN`: a hold
spanning two beats puts its own midpoint between them, and both `verify-hold-geometry` and the
contact sheet shoot exactly there. Caught live — with one `a4` hold, the T4 end-of-act seed
(`HOT ROW` + `2K WPS`) never appeared on the contact sheet at all, because the spanning hold's
midpoint (48.5%) fell 1.9% before the seed's window.

**Camera k is constant inside a tier band** (1.4388 for the two sparse acts, 1.3431 for the three
full ones, 1.8083 for the T5 write-path read beat). That falls out of P3: if every act frames the
same rectangle, the camera has no reason to move between them, and the act crossfade becomes the
scene change. The one real camera move inside the story is the T5 zoom-in on the write path.

**PRIMARY vs SUPPORTING.** `users` is the only supporting node (context, not mechanism): 0.85 box,
16px display label. The compressed T5 trio uses the same 0.85 box for a different reason (P2).

**Storyboard audit.** (1) Coverage: every sheet component appears in ≥1 act and every act is at
least one camera hold; every new component is a spotlight subject in the beat that introduces it.
(2) Upstream: every act frame contains the whole request path from `users`; the a5a read beat frames
`api-gateway` as the upstream of the write path it zooms on. (3) Ownership: no caption claims a
guarantee at a non-owner — `1 job → 1 worker` sits on the queue's drain edge, `hash 7c` on the
router's outgoing path, `1 publish → 2 subs` on the stream itself. (4) Counts: every N matches
NUMBERS. (5) Cluster/singleton: as listed under COMPONENTS. (6) Spotlight: all 8 content beats have
a non-empty set, each exactly its caption's subjects, none containing an upstream context node.

### Foreground budget, per act and per beat

| act | foreground (`.node--new`) | veterans receded | compressed | nodes drawn | max per BEAT |
|---|---|---|---|---|---|
| T1 | 3 (users, app-monolith, postgres) | 0 | 0 | 3 | 3 |
| T2 | 3 (alb, app, redis) | 2 | 0 | 5 | 3 |
| T3 | 4 (cdn, read replicas, queue, workers) | 5 | 0 | 9 | a3a 2 · a3b 2 |
| T4 | **6** (api-gateway, auth-svc, auth-db, catalog-svc, order-svc, pub/sub stream) | 7 | 0 | 13 | **a4a 5 · a4b 1** |
| T5 | 4 (shard-router, 3 shards) + order-svc at base | 8 | 3 | 16 | a5a 2 · a5b 4 |

T4 is the one act over the ~5 budget. It is not split, because the pub/sub stream must be
introduced in the same act as the decomposition — *decoupled services are what create the need for
events*, and that causality is the act's whole lesson. The budget is honoured per BEAT instead;
see the report's principles section.

### Event table
The machine copy is `tests/fixtures/progressive-500k-5tier.timeline.tsv`; `scripts/emit_timeline.py --master 48000ms --beat 4800ms`
emitted every `@keyframes`, every `data-window` and the manifest's `holds`/`captions` fragments from
it. No percent in the cut was computed by hand. `scripts/solve_camera.py --gate …` produced every
`k`/`tx`/`ty`; the cut and its manifest were assembled by two build scripts kept with the authoring scratch, not shipped.

### Caption strings (verbatim; the manifest carries the same bytes)

| element | window (ms) | words | wps | text | claim it restates |
|---|---|---|---|---|---|
| .cap-a1 | 3400–6600 | 13 | 4.06 | One box takes every request; ten reads per write share one 100-connection pool. | T1 row + read:write + T1 break |
| .cap-a2 | 8200–11400 | 15 | 4.69 | Six replicas and a 90% cache clear the pool; half the primary's work is reads. | T1→T2 row + T2 break |
| .cap-a3a | 13200–16400 | 12 | 3.75 | Reads leave the primary: CDN first, then cache, then three read replicas. | T2→T3 row (read half) |
| .cap-a3b | 16800–19400 | 11 | 4.23 | Slow work leaves too — one queue, four workers, one job each. | T2→T3 row (async half) + queue guarantee |
| .cap-a4a | 21200–23600 | 11 | 4.58 | One gateway routes to three services; each owns its own store. | T4 shape + auth-db ownership |
| .cap-a4b | 24200–26600 | 11 | 4.58 | They publish instead of calling — but writes still hit one primary. | fan-out guarantee + T4 seed |
| .cap-a5a | 28400–31600 | 14 | 4.38 | hash(shard key) picks the owner: this write is 7c, so only shard 2 sees it. | shard-router guarantee + routed key |
| .cap-a5b | 32400–35400 | 13 | 4.33 | Three primaries, about 1K writes each per second; replicas still serve catalog reads. | T5 headroom + replicas retained |
| .cap-r | 36600–40400 | 11 | 2.89 | One system, five architectures — and one boundary was coupling, not load. | tier-boundary rule + the T3→T4 asymmetry |

Measured from the manifest's own windows: densest **4.69 wps** (cap-a2), mean **4.28 wps**, every
caption under the golden-calibrated ~5 wps ceiling (`references/camera-beat.md` → Caption pace).

---

## Phase 2 — VIEWER PERSONA AUDIT
Persona: **junior dev, builds basic web apps, has never scaled one.** Walked through the rendered
contact sheet beat by beat. Every row's answer was checked ON SCREEN, not in intent.

### Act 1
| what I see | what I ask | what answers it |
|---|---|---|
| two lines from one box to one drum | why two lines to the same database? | the two mono edge labels `read ×10` / `write ×1` — different cargo, different volume |
| `read ×10` | ten of what? | cap-a1 "ten reads per write"; legend row `read ×10 / write ×1 = load ratio on that edge` |
| amber trembling drum + `100/100 CONNS` | is that bad? | the chip's number is the pool, full; legend "amber body + shake = overloaded" |
| a mostly empty canvas | is something missing? | the act title `MONOLITH` and verdict `1K CCU · 1 box` say this IS the whole system; the empty slots fill in later acts |

### Act 2
| what I see | what I ask | what answers it |
|---|---|---|
| three ghost outlines behind `app` | is that one server or many? | sub `x6 replicas` + the stack idiom |
| `users` and `postgres` drawn thinner and paler than `alb`/`app`/`redis` | did they get worse? | legend: `thicker outline = new in this act` / `thinner + faded = already solved, still running` |
| `read ×10` into redis, `miss ×1` into postgres | why does the DB line carry less? | redis sub `90% hit` — nine of ten reads stop at the cache |
| postgres goes amber with `READS 50%` | didn't we just fix it? | cap-a2 "half the primary's work is reads" — a different problem from a full pool, and the reason act 3 is called READ / WRITE SPLIT |
| the pale postgres suddenly looks heavy again | why? | its STATE overlay is a separate channel from the weight ladder: receded means "not this act's new lesson", the amber replica means "this is what's breaking" |

### Act 3
| what I see | what I ask | what answers it |
|---|---|---|
| purple box with a filling bar labelled `queue` | what is in it? | sub `emails · exports` — the work is named, not "async work" |
| a dashed arrow into it labelled `enqueue` | who puts work in? | the arrow's tail is on `app`; the edge is dashed = async path (legend) |
| the queue has an arrow out | who takes work out? | `workers · x4 consumers`, and the drain edge says `1 job → 1 worker` |
| `1 job → 1 worker` | so two workers can't send the same email twice? | that is exactly the claim; it is the queue's guarantee row |
| `read replicas · x3 · reads` with `LAG 1.8s` | is stale data a bug? | the chip carries the measured lag; the double line rides the sync edge; cap-a3a says reads moved there |
| nothing is red in this act | so why change anything? | verdict `100K CCU · 1 deployable` + app sub `x12 · one deploy`; cap-a4a and cap-r name the coupling. This is the one boundary that is not a load number |

### Act 4
| what I see | what I ask | what answers it |
|---|---|---|
| `api-gateway` where the `alb` used to be | did the load balancer disappear? | same slot, same role colour; sub `routes by path`; the act title names the model |
| three orange boxes named `-svc` | why three apps now? | the `/auth` `/catalog` `/orders` path labels on the gateway's three edges; cap-a4a |
| the `-svc` boxes carry stacks and `x30 / x4 / x4` | *(standing question: how does the PREVIOUS act's lesson show on this node?)* did we stop replicating when we split? | no — each service keeps the T2 stack idiom and its own count; the three counts are 7.5× apart, which is what "one deployable, three workloads" cost. **This row is AMENDMENT #2: it was the missing row, and the missing drawing.** |
| `auth-db · auth-svc only` | can catalog read it? | no edge from any other service touches it; the sub says so; cap-a4a "each owns its own store" |
| a pub/sub stream appears only NOW | why not earlier? | there was nothing to decouple before: cap-a4b "They publish instead of calling". One deployable calls itself; three services cannot |
| `pub/sub stream · 1 publish → 2 subs` | who are the 2? | the two outgoing dashed edges, each naming its own cargo: `invalidate cache` → catalog-svc, `send receipt` → workers |
| both a queue AND a stream | what's the difference? | the queue's drain edge says `1 job → 1 worker`; the stream's sub says `1 publish → 2 subs`. Point-to-point vs broadcast, stated on screen |
| `HOT ROW` and `2K WPS` on the primary at the end | I thought we fixed things? | cap-a4b "but writes still hit one primary"; the numbers table says 1.8K writes/s at 300K against a ~2K ceiling |

### Act 5
| what I see | what I ask | what answers it |
|---|---|---|
| `shard-router · by hash(key)` where postgres used to be | how does it choose? | the sub names the MECHANISM — hash a key, get an owner — and the routed path is labelled `hash 7c`, so the abstract sub and the concrete value are one glance apart. It deliberately does not name a key column (AMENDMENT #3): which column you shard on is this reader's next decision, not this cut's |
| three drums `hash 00–55 / 56–aa / ab–ff` | do all three get the write? | only the middle path carries a packet and only shard 2/3 wears the accent outline; `7c` falls in `56–aa`. The other two paths are drawn at reduced opacity and their `<title>` says "idle for this write" |
| auth-svc, auth-db and catalog-svc are suddenly small | were they removed or downgraded? | legend `smaller = lesson compressed`; their labels and subs still carry the same claims, so the architecture claim is identical — only the drawing's attention moved |
| the small `auth-svc` / `catalog-svc` still show a stack, and `x6` / `x50` | *(standing question: how does the PREVIOUS act's lesson show on this node?)* did compressing them drop the replicas? | no — the stack and the `xN` ride the same 0.85 box; compression drops DETAIL, never a lesson. The counts went UP (×4→×6, ×30→×50) because the load did. **AMENDMENT #2.** |
| `order-svc · x6 · order writes`, at full size | why does the shard client have replicas but the router does not? | the count answers "who sends the writes"; the router is drawn as one managed routing tier, like `alb`/`cdn`/`api-gateway` before it (AMENDMENT #2 records the decision) |
| `order-svc` did NOT shrink | why is it different? | it is the shard client — the beat is about what it does with a write |
| `read replicas · x3 · catalog reads` | why keep them if we sharded? | cap-a5b "replicas still serve catalog reads" — sharding split the WRITES |
| the camera zooms in for the first time | what am I meant to look at? | the write path only: gateway → order-svc → shard-router → shard 2/3, at 27 frame-px |

No mechanism on the canvas is left without an on-screen answer.

---

## Phase 3 — COMPONENT MAPPING TABLE
Every drawn shape traces to a row. v3 draws exactly v2's component set, so every row below is
**CARRIED** from v2's table (one `--domain components -n 1` query per sheet component, the query
text being the sheet's own words). No component is new in v3, so no component query was re-run.

| Sheet component | query run (v2) | Component ID | Snippet Ref | Role | States used | status |
|---|---|---|---|---|---|---|
| users | `browser client users` | `browser` | `snippets/node-shapes.html#shape-device` | client | — | carried |
| app-monolith | `app monolith one deployable` | `monolith` | `snippets/node-shapes-glyphs.html#shape-monolith-frame` | service | — | carried |
| postgres | `postgres sql database primary` | `sql-database` | `snippets/node-shapes.html#shape-cylinder` | data | is-overloaded, is-degraded | carried |
| auth-db | `postgres sql database primary` | `sql-database` | `snippets/node-shapes.html#shape-cylinder` | data | — | carried |
| alb | `application load balancer` | `load-balancer` | `snippets/node-shapes-glyphs.html#shape-lb-fork` | service | — | carried |
| app (×6/×12) | `microservice domain service` | `microservice` | `snippets/node-shapes.html#shape-rounded-rect` + `#shape-replica-stack` | service | — | carried |
| auth-svc / catalog-svc / order-svc | `microservice domain service` | `microservice` | `snippets/node-shapes.html#shape-rounded-rect` + `#shape-replica-stack` | service | — | carried; stack ref added by AMENDMENT #2 (same row, same snippet file as `app`) |
| redis | `redis read-through cache` | `cache` | `snippets/node-shapes.html#shape-cache` | data | — | carried |
| cdn | `cdn edge static` | `cdn` | `snippets/node-shapes-glyphs.html#shape-cdn-globe` | infra | — | carried |
| queue | `message queue durable buffer` | `message-queue` | `snippets/node-shapes.html#shape-pipe` | async | — | carried |
| workers (×4) | `background worker draining queue` | `worker` | `snippets/node-shapes.html#shape-gear` + `#shape-replica-stack` | service | — | carried |
| read replicas (×3) | `read replica follower` | `read-replica` | `snippets/node-shapes.html#shape-cylinder` + `#shape-replica-stack` | data | is-syncing | carried |
| pub/sub stream | `pub/sub topic fan-out stream` | `pubsub-topic` | `snippets/node-shapes.html#shape-pipe` | async | — | carried |
| api-gateway | `api gateway single front door routing` | `api-gateway` | `snippets/node-shapes.html#shape-hexagon` | service | — | carried |
| shard-router | `shard router directing writes by key` | `shard-router` | `snippets/node-shapes.html#shape-hexagon` | service | — | carried |
| pg-shard 1/3 · 2/3 · 3/3 | `database shard partition by hash range` | `db-shard` | `snippets/node-shapes.html#shape-cylinder` | data | **is-selected** (2/3 only) | carried shape, NEW state |

`worker`'s row carries semantic role **service** (not async) — the queue is the async plumbing, the
worker is compute that drains it. `shard-router` and `api-gateway` both carry role **service** per
the dataset, which is why two hexagons sit among data-coloured drums.

### Queries run for v3 (targeted, exploration, and 0-results — all three are findings)

| query (verbatim) | mode | result | what it decided |
|---|---|---|---|
| `coupled single deployable shared release blast radius` `--domain states -n 1` | targeted | **0 results** (best score 0.0, domain floor 3.0) | recorded |
| `coupled single deployable shared release blast radius` `--domain states -n 5` | exploration (mandated retry) | **0 results again** | `NO ROW — stated in text, not as a state.` T3's coupling break therefore gets NO staged state: it is carried by the act-3 verdict pill `100K CCU · 1 deployable`, the `app` sub `x12 · one deploy`, cap-a4a and cap-r. Nothing near-looking was substituted — no `is-degraded` on a healthy tier |
| `component idle not chosen for this request` `--domain states -n 1` | targeted | **`is-selected`** (score 5.8451) | ADOPTED for pg-shard 2/3. Its Use When cell literally reads "shard chosen by the router"; its Don't cell ("never accent-color alone — the weight step is the second channel; pair with the routing weight label") is honoured by accent stroke + weight step + the `hash 7c` edge label. The two unrouted shards get no state — they are base, and their `<title>` says "idle for this write" |

The v2 miss/false-friend rows below still stand and were NOT re-litigated (that is why they are
written down): `polling` → 0 results, model on the edge, `cron-job` not reached for;
`app replica pool identical instances` → REJECTED `read-replica`; `stateless app server horizontal
scale out` → REJECTED `autoscaling-group` (a scaling mechanism, not a running service);
`consumer group subscriber` → REJECTED `pubsub-topic`, resolved to `worker`;
`shard distribute routing key to one shard` → REJECTED `shard-distribute` (Runtime `needs-js`,
illegal for an artifact target) — single-shard routing is drawn with css-only `packet-travel` on
the ONE routed path.

### Other domain rows carried (unchanged from v2)
- `--domain states`: `is-overloaded`, `is-degraded`, `is-syncing` (+ `is-selected`, new above).
- `--domain payloads`: `request`, `event`, `binary-stream`.
- `--domain motion`: `packet-travel`, `dash-flow`, `queue-fill`, `camera-beat`, `state-timeline`,
  `shake-stress`, `replication-sync`.
- `--domain layouts`: `progressive-tiers`. `--domain styles`: `flat-minimal` (Template Status
  usable, Runtime css-only). `--domain colors`: the 7-role `house` palette, used unmodified.
  The only non-CSV colours are the educational-register state tints `--role-warn #fef3c7`,
  `--ink-warn #b45309`, `--role-degrade #fef2f2`, carried from the frozen golden with its
  hand-checked contrast note (4.80:1 / 4.51:1 / 4.27:1 / 4.35:1).

### One deviation from a dataset cell, stated
`is-selected`'s Static Encoding read "role-accent stroke at **+1px** weight" when this cut was
built. The shard row is already at this act's `--new` weight (3.2px), so +1px over the BASE 1.8px
would have rendered the chosen shard THINNER than its two unchosen siblings. The step is taken
against the act weight instead (3.2 → 5px in `--accent-data`), which preserves the row's actual
rule — two channels, weight plus accent, never colour alone. **The row has since been reworded to
say exactly that** (a weight step is relative to the element's CURRENT weight, never a fixed step
over `--stroke-w`), so this is no longer a deviation; it is recorded here because it is the finding
that produced the rewording. Its Motion Ref `pulse-glow` carries a `drop-shadow` filter, and
SKILL.md forbids a filter on an element that animates under a moving camera, so the intensity rides
the same opacity-only `ring-pulse` every other state overlay in this cut uses; the row's
reduced-motion cell ("accent stroke persists; glow stops") is satisfied exactly.

---

## Reduced-motion contract
`prefers-reduced-motion: reduce` renders the **informative end state**: act 5 alone, at rest
(acts 1–4 parked off-canvas), camera at the overview, chrome and legend visible, captions and
spotlights hidden, every packet parked at its destination, queue and stream bars at their resting
fill, async edges solid-dashed, no shake, no ring pulse, no sync drift. The failure states are all
hidden — act 5 is healthy, and a frozen amber drum would misrepresent the finished design — but
**`stage-a5` stays lit with its pulse stopped**, because `is-selected` is not a failure: it is the
end state of a write that has already chosen its owner, and hiding it would make the shard beat
motion-only. The full act-by-act narration lives in the SVG `<desc>`, and every caption's key fact
also exists statically as a node sub, an edge label or a chip.

## Loop-seam contract
- master 48000ms; every ambient loop divides it (checked by `verify_all` stage B `master-divisors`).
- **Every `animation-delay` is negative** (−600 / −800 / −1200 / −1600 / −1800ms), so frame 0 and
  frame 100% are byte-identical.
- Act 5 is lit at 0% and its final window runs to 100% (`seam 1600ms`), so the loop parks on the
  finished architecture rather than on a fade. `stage-a5` carries the same seam, so the routed
  shard's accent ring is also lit at 0%.
- No other staged state is open at 100%: `stg-a1/a2/a3/a4` all close by 96.25% at the latest.

## Motion budget
Animated edges on screen at any instant: act 1 → 3, act 2 → 5, act 3 → 11 (9 request/stream
packets + 2 dashed async runs, 9 distinct edges), act 4 → 12, act 5 → 12.
All ≤ `MAX_ANIMATED_EDGES` (12). In act 5 the `writes` edge (auth-svc → auth-db) is deliberately
static — a solved lesson does not need to keep moving — and the two unrouted shard paths carry no
packet at all: that silence is the argument of the shard beat.

## Known deviations
1. **Act 5 draws 16 nodes**; `layouts.csv → progressive-tiers` gives a sweet spot of 4–12 per tier
   (the ≤20 hard ceiling is respected). Carried from v2 and unchanged: gateway + three domain
   services + a private store + three individually named shards + router + queue + workers + stream
   + retained replicas do not fit 12. The tier still passes the layout's hard gate (CONTAINED in one
   camera frame at k=1.3431 with 20.15 frame-px subs) and every clearance floor.
2. **Act 4 carries 6 foreground nodes**, one over the trialled ~5 budget. Honoured per beat instead
   (a4a = 5, a4b = 1). See the report.
3. **The veteran ladder collided with `verify_edge_anchors.py`.** Moving replica-ghost opacity
   from an inline `style=` to a CSS class — which the ladder needs, because a veteran's ghosts must
   re-scale by the same .65 factor — silently changed which shape the checker measures. Its
   solid-body heuristic tested for the literal substring `opacity` inside an inline `style=`; without
   it, the ghost's box (offset −14px) became the node's box and five correctly-anchored endpoints
   reported FLOATING. The cut resolved it by keeping opacity inline as `opacity:var(--ghost)` and
   letting the class set the custom property; the checker has since been re-keyed on structure
   (ghost class, else the last `.node__shape` in painter's order), so the collision cannot recur.
4. **One edge crossing** in acts 4 and 5: `invalidate cache` (stream → catalog-svc) crosses the
   enqueue run near (1040, 540). It is topologically unavoidable with the queue left of order-svc
   and the stream below it; both are async dashed edges, neither label is pierced, and no edge
   crosses a node or any text anywhere in the file.
5. **The `enqueue` run was re-anchored after promotion (user-caught).** As authored it ran
   `M 1070 520 L 920 500` in acts 4 and 5: the head landed mid-way across the QUEUE's top border
   while the edge arrived from the RIGHT, so the connector wrapped over a corner to reach a side
   that does not face its source. `verify_edge_anchors.py` passed it — the endpoint *was* on the
   node boundary — which is why this is a second defect class (wrong side), now checked by the same
   script's nearest-side rule. Re-anchored to `M 1070 540 L 990 540`: order-svc's left side to the
   queue's right side, at both boxes' vertical centre, so the async rail
   `order-svc → queue → workers` is one continuous horizontal line at y=540. The `enqueue` label
   moved with it to `x=1020 y=508` (`text-anchor:middle`), which is the only slot in the 80px gap
   that clears the queue box and the `invalidate cache` diagonal on both sides.
