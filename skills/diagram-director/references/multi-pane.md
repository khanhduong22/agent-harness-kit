# Multi-Pane Workflows: Comparison & Progressive Tiers

Two diagram workflows that partition ONE canvas into self-contained territories and let the
camera patrol them. Layout rows: `data/layouts.csv → split-compare, progressive-tiers`. Type
rows: `comparison`, `scaling-story`. Camera machinery: `references/camera-beat.md` (this file
only adds the territory rules). Workflow context (solution sheet → storyboard → build):
`references/workflow-phases.md`.

**Registers.** Spatial partition — the split-compare and progressive-band forms in this file — is
the **reference register**: every pane or tier on screen at once, the artefact readable as a still.
The **educational register** answers a different ask ("explain it", "show me what breaks") and
replaces spatial partition with temporal acts: one canvas at a time, states changing on the master
timeline, the weakness demonstrated rather than diagrammed. Its contract lives in
`references/camera-beat.md` → "Scenario timeline — staged states and acts"; `comparison` and
`scaling-story` default to it when the user asks to explain or teach.

## Shared territory machinery

Both modes build on the same base; the mode-specific sections only add rules.

- **A territory (pane or tier) is a self-contained mini-diagram**: its own nodes, its own edges,
  no edge ever crosses a gutter. Territories never share a node.
- **Camera patrol.** Each territory gets at least one beat; one overview beat sees everything.
  The overview may zoom far out — that is accepted, and for progressive mode expected.
  **Hard gate: every territory fits ONE camera frame — CONTAINED, with its pane heading
  readable.** Declare those beats `gate: territory` in the manifest. The node-label text floor
  does NOT apply to them: a whole pane does not fit a frame at `k_read`, and the frozen goldens
  frame their panes at a constant k below it, so a `k_read` floor here would fail correct work.
  Per-territory legibility past containment is a contact-sheet judgement
  (`references/camera-beat.md` → "P_min is per-format AND per-gate"). Legibility is judged
  per-territory, never on the overview.
- **One shared title band and one shared legend** for the whole canvas. Captions follow the
  existing caption rules (text face, baked boxes, and a fixed slot inside the hold's frame —
  adjacency to the spotlight set only where a fixed slot would fall outside it).
- **Territory separation**: gutter ≥80px plus a 1px rule line in the muted stroke token.
- **A cadence is an EDGE property, never a node** — and multi-pane work is where this breaks first,
  because "polling vs pub/sub" and "poll every 1s vs push" are two of the most common comparisons
  asked for. The polling pane does NOT gain a poll-client box: it is the same client, with the
  interval written in the edge label (`GET /price · every 1s`), payload `request`, motion
  `round-trip` — or staggered `packet-travel` when N clients poll one endpoint, which is exactly
  the cost the pane is arguing about. Never reach for `cron-job` here: a cron job is a scheduled
  component that wakes and does work, a different claim from a client asking again on an interval,
  and swapping one in silently changes what the comparison proves. Under the sameness rule this
  matters doubly: an invented node in one pane is a rendering difference the reader must diff
  before they can reach the architecture.
- **The solution sheet grows a per-territory section.** Every displayed string still traces to
  the sheet — including per-territory verdict numbers and transition captions.

## Comparison mode (`comparison` type, `split-compare` layout)

Each pane is one solution to the SAME problem, drawn at pattern altitude.

- **2–6 panes.** 2 panes split the canvas along ONE axis — which axis is decided by the orientation
  rule below, not by the canvas. 3–4 use a 2×2 grid; 5–6 use 2×3 (landscape) or 3×2 (vertical).

### The orientation rule — pane axis ⟂ pane flow

**The pane axis is PERPENDICULAR to the panes' own internal flow axis.** A pane whose internal
flow runs HORIZONTALLY — a protocol timeline, a left-to-right hop chain, a sequence read as time
running rightward — stacks TOP/BOTTOM. A pane whose internal flow runs VERTICALLY — a request
falling through layers, a client-down-to-store path — sits SIDE-BY-SIDE. Side-by-side is the
default only because most panes flow downward; it is not the rule, and 2 panes split *the axis the
flow does not use*.

Two reasons, and both are measurable rather than aesthetic:

- **A wide timeline in a half-width pane starves its label room.** Split a 1920 canvas vertically
  and each pane gets ~920 world px for a chain that wants the full run. The nodes survive the
  squeeze; the *labels between* them do not — a protocol timeline's whole content is on its edges
  (`GET /events · Accept: text/event-stream`, `Last-Event-ID: 42`, `ping/pong · every 20s`), and
  those strings do not compress. What follows is the familiar failure loop: shrink the label under
  the `k_read` floor, or let it touch a node, or drop the claim the pane exists to make.
- **A territory beat wants the pane to fill the frame's long axis.** `k_fit` is
  `min((W−2m)/bbox_w, (H−2m)/bbox_h)`, so a pane's zoom is bound by whichever of its own dimensions
  is proportionally worse against the frame. A wide pane in a tall half-canvas binds on width and
  strands the camera low; the same pane across a full-width band binds on the axis it actually
  wants, and the territory hold frames it with margins to spare. Stacking is what buys the zoom
  back — the same move `camera-beat.md` prescribes for an over-stuffed `read` beat ("restack the
  pair along the frame's long axis"), applied one level up, to territories.

The sameness rule does not change under stacking, only its geometry: identical components are
pinned to a shared **x** across the top and bottom panes, so the reader diffs straight DOWN a
column. The gutter (≥80px + the 1px rule line) becomes horizontal, and the pane rule line runs
across the canvas rather than down it. Worked shape (SSE vs WebSocket, 2 stacked panes,
landscape): each pane a horizontal `browser → reverse proxy → app server` timeline, the delta =
what happens after the proxy drops the connection. A stacked territory hold may legitimately show
the neighbouring pane's edge and the gutter — a pane band cannot fill a 16:9 frame vertically, the
containment gate is about the hold's OWN must-show set, and for a comparison the neighbour's edge
in frame is orientation, not a defect.
- **3–8 nodes per pane.** If a pane needs more, the comparison is at the wrong altitude —
  compare the pattern, not the full system. Cut scenery until the delta is the biggest thing.
- **The sameness rule (the core rule).** A component that appears in more than one pane is drawn
  identically everywhere: same shape, same role colour, same relative position. Only the delta
  differs, and the delta takes the accent. The reader must diff the ARCHITECTURE; the moment they
  have to diff the rendering, the diagram has failed. Verify by diffing the rendered panes, not
  your intent (checklist).
- **Verdict chip per pane**: the one number that decides — connection count, fanout cost
  O(N²) vs O(N), p99. From the solution sheet, formatted by the sheet's number rules.
- **Pane order = argument order**: worse → better, or before → after. The reading direction is
  the conclusion.
- **Beat map**: overview (all panes) → one beat per pane in argument order → final delta beat
  framing the differing regions of two panes side by side.
- **States earn their keep here**: the pain the delta removes is shown with the state vocabulary
  (`data/states.csv`) — e.g. the without-pubsub pane's server `is-overloaded` at high N, the
  with-pubsub pane healthy.
- **In the educational register the beats DEMONSTRATE the weakness as a scenario** rather than
  touring it: load rises → the weak pane's node overloads → it dies → the failure dominoes, while
  the strong pane absorbs the same load unmoved. The states and their windows come from the sheet's
  event table; the machinery is `camera-beat.md` → Scenario timeline.

Worked example, with a system-design cast (realtime chat fanout):
`references/genres/system-design.md` → *Comparison panes — worked example*.

## Progressive mode (`scaling-story` type, `progressive-tiers` layout)

One system narrated across load thresholds — "0 → 500K CCU" — as stacked tier bands.

- **What DERIVES the tiers is genre-owned** — a tier boundary is a break in the cast's own model,
  and this file only says how tiers are drawn and patrolled. For the default genre:
  `references/genres/system-design.md` → *Progressive tiers — a tier boundary is an architecture
  break point*. Whatever the genre, a tier exists because something broke, never because a number
  is round, and the derivation is recorded in the solution sheet.
- **As few tiers as the story needs, hard max 5.** Each tier is a self-contained sub-diagram
  within the layout's node sweet spot, and must pass the per-territory containment gate above.
  The sweet spot is advisory guidance for the default case; a tier that clears the hard gates
  (containment at its hold, the per-gate text floor, clearance) may exceed it when the storyboard
  demands — and the solution sheet then records why. The containment gate is not negotiable.
- **The continuity rule.** A component alive across tiers keeps its shape, role colour and
  relative position in every tier — the reader should watch the system GROW, not meet four
  strangers. Each tier's NEW components take the accent. Retired components never reappear.
  MECHANISED: `diagram-director/scripts/verify_tier_identity.py` reads each tier's `data-node-id` set and fails
  `acts/identity-role-drift`, `acts/identity-shape-drift`, `acts/identity-zone-drift`,
  `acts/retired-id-returns` and `acts/debut-accent-missing` — the five ways this one sentence
  can be broken. *Relative position* is a 4×3 viewbox grid cell, and a deliberate move is
  declared as `changed: [{id, what: "moved"}]` (`references/output-manifest.md`).
- **Transition captions carry the story.** Between tiers, the caption names what broke and what
  was added: "DB pool cạn ở ~5K CCU → thêm read replica + cache". The break point is content,
  not decoration; a tier caption that only restates the CCU number has said nothing.
  MECHANISED: `acts/delta-caption-empty` fails a tier whose captions name none of the ids that
  tier added, removed or changed — matched by id, rendered label or a declared caption alias.
- **The trigger is shown, not told**: the component that broke wears `is-overloaded` (or the
  fitting state) in tier N and stands healthy in tier N+1. State + caption together make the
  transition argument.
- **Beat map**: overview (far zoom, the whole growth arc) → one beat per tier, low to high →
  optional delta beats on the most instructive break points. Overview legibility is explicitly
  NOT a gate; per-tier legibility is.

### Attention budget in the educational register (the five-tier rules)

When the tiers become temporal ACTS rather than stacked bands, every act redraws the whole system,
so by act 4 the reader is looking at thirteen boxes to learn about two. These five rules were
trialled and validated on the five-act scaling story (five acts, 48s master); the
principle behind all of them is that **the act's lesson must be the loudest thing in the frame**,
and everything else is graded down to whatever still keeps it legible and honest.

- **Foreground budget: ≤ ~5 foreground nodes per BEAT — per beat, not per act.** The budget is a
  reading-load limit, and what the reader reads at once is a beat, not an act. The five-tier build
  proved the distinction rather than assuming it: its T4 act genuinely needs SIX new components,
  because the pub/sub stream has to land in the same act as the decomposition — *decoupled services
  are what create the need for events*, and that causality is the act's entire lesson. Splitting the
  act would have taught the wrong thing. So the act runs at 6 and the budget is honoured per beat
  instead: `a4a` introduces 5 (gateway + three services + the private store), `a4b` introduces 1
  (the stream). An act over the per-beat budget is a defect; an act over the per-act count with
  every beat inside it is a design, and **the solution sheet must justify it explicitly** — naming
  the causal reason the components cannot be separated, and showing the per-beat split.
- **Veterans recede — down the STYLE'S OWN stroke ladder, never an invented tier.** A component
  taught in an earlier act renders one step back in later acts. Derive that step from a step the
  style already has. Worked example, `flat-minimal`, which ships exactly one stroke step
  (`.node--primary` = `calc(var(--stroke-w) * 1.4)`) — the cut walks that same ×1.4 factor in both
  directions instead of inventing a second language:

  | tier | stroke | opacity | derived from |
  |---|---|---|---|
  | new in this act | `3.2px` | 1 | the older golden's `.node--new` |
  | base | `1.8px` (`--stroke-w`) | .9 stroke-opacity | flat-minimal `:root` |
  | veteran (receded) | `calc(var(--stroke-w) / 1.4)` = 1.286px | **.65 on `.node__body` only** | the ×1.4 step inverted; .65 is flat-minimal's own `.node__detail` ink tier |
  | replica ghosts, receded | — | existing ghost tiers × .65 | the same factor, so a stack recedes with its node |

  The opacity rides `.node__body` ONLY — the idiom `.is-idle` already uses — so a veteran's LABEL
  keeps full ink and stays AA-legible. Floor: never below the style's `.is-idle` value (`.35` here),
  because a veteran is still running, not idle.
- **Solved lessons compress.** A prior act's RESOLVED cluster may shrink to the sanctioned
  supporting `scale(0.85)` box with the style's own base type sizes — C4-zoom thinking: detail
  follows the current lesson, and a subsystem whose argument is finished does not need to be read
  word for word. It must still clear the supporting-text floor at that act's `k` (in the golden, a
  13px sub at k=1.3431 renders 17.5 frame px against a landscape supporting floor of 17). Compress a
  whole ownership pair, never half of one — a store left at full detail while its only client shrinks
  breaks the pair.
- **Fixed canvas zoning across all acts.** Fix the columns and rows once — clients → edge → compute
  → async → data — and let a component keep its zone, and where possible its exact coordinates, in
  every act it appears in. Growth then reads as boxes APPEARING in fixed slots rather than as a
  re-drawn diagram, and a component that inherits a predecessor's exact slot (the golden's
  `shard-router` taking the primary's) says "this became that" with no caption at all. Two honest
  limits the golden hit: (a) a **label-length-driven exception is allowed when the sheet documents
  it** — its queue/worker pair sits lower-LEFT rather than lower-middle because `1 job → 1 worker`
  needs 104px of horizontal run to clear both boxes, and every lower-middle arrangement put a
  diagonal there whose label touched a node; (b) a **constant `k` inside a tier band is a virtue,
  not a stuck camera** — if every act frames the same rectangle the camera has no reason to move,
  and the act crossfade becomes the scene change. Reserve real camera moves for the one beat that
  earns a closer look.
- **A lesson once taught PERSISTS, in compressed form, on every later act's relevant nodes.**
  Receding and compressing are allowed to drop DETAIL. They are never allowed to drop a claim the
  reader was taught to read. If act 2 taught scale-out with replica-stack ghosts and an `xN` sub,
  then **every compute node in every later act carries its own stack and its own `xN`** — the
  number coming from the solution sheet's arithmetic, not from a repeated constant. Drop it
  silently and the sequence teaches the opposite of what it says: a T4 act that redraws three
  freshly-decomposed services as three plain boxes reads as *decomposition REPLACED replication*,
  which is exactly the wrong model for a reader who has never scaled anything. The idiom persists
  at whatever scale the node is drawn at — a compressed `scale(0.85)` node wraps its ghosts in the
  same 0.85, because the compressed form is what carries the lesson forward. Same rule for any
  taught idiom, not just replica stacks: a cache's hit rate, a queue's delivery guarantee, a
  follower set's lag. Observed failure (2026-08-26, user-caught on the five-tier golden, fixed in
  its AMENDMENT #2): the three T4/T5 domain services were drawn as single boxes for two whole acts,
  and every mechanical gate in the repo passed them — containment, anchors, windows, camera. No
  geometry checker can ask "what did the previous act teach about this node". Only the persona
  audit can, which is why that question is now one of its standing four
  (`references/workflow-phases.md` → Phase 2).
  Two boundaries, so the rule does not turn into decoration on everything: (a) it applies to nodes
  the earlier lesson is ABOUT — a fleet of a thing you scale — not to a tier deliberately drawn as
  one managed symbol (the golden keeps `alb` / `cdn` / `api-gateway` / `shard-router` singular, and
  says so in its sheet); (b) a count that is 1 **by design** still answers the question — it is
  stated, in the sheet and, where the singularity IS the guarantee, in that beat's caption.
- **Promotion is the state channel's job, not the recede ladder's.** A receded veteran is brought
  back to attention ONLY by its state overlay — chips, amber, the failure encoding — never by
  quietly restoring its stroke weight. The two channels are independent and mean different things:
  **receded = "not this act's lesson"**, **state = "what is breaking"**. Mixing them makes a
  weight change ambiguous between "pay attention" and "this is now healthy".

Worked example, with a system-design cast (4 tiers, 0→500K CCU):
`references/genres/system-design.md` → *Progressive tiers*.

## Delivery checks (both modes)

Beyond the standard checklist: (a) rendered panes diffed — identical components identical to
the pixel-level idiom, delta accented; (b) every territory verified CONTAINED in its beat frame
(`diagram-director/scripts/verify_all.py` stage D does the frame math over every declared hold; the contact sheet
is the screenshot half); (c) each tier caption names its break point; (d) no edge crosses a
gutter; (e) shared legend covers every role and state used in ANY territory.
