# Workflow: Solve, Storyboard, then Draw

Five phases, in order. The failure mode this workflow exists to prevent is **text/solution drift**:
a guarantee written on the wrong node, a caption stating a fact the architecture does not deliver, a
count that disagrees between a sub-label and a beat caption. Every one of those was observed before
this workflow existed. The cure is one artifact — the **solution sheet** — that every later string
derives from.

For a quick static diagram, phases 1–2 collapse into a mini-sheet (components + numbers + owners,
five minutes of thinking). They are never skipped: a diagram of an unsolved solution is a drawing of
a guess.

---

## Phase 1 — Solve before you draw

Derive the actual architecture from the prompt. No visual decisions belong here.

**Ask when it changes the solution.** If the prompt leaves these undecidable AND the answers
lead to materially different results, ask (one round, 2–4 questions). The subject-matter half of
that list is genre-owned — for the default genre it is
`references/genres/system-design.md` → *Phase 1 — the questions that change the architecture*
(scale, core guarantee, simple vs distributed). These two are asked in every genre:
- Destination: teaching content, real project docs, short video? (drives beats vs static later)
- **Format: landscape or vertical?** Orientation is presentation, never architecture: the solution
  sheet, component count, beats and captions are identical across formats — only the layout system,
  camera targets and platform safe area change (see SKILL.md → Output Format). Decide now;
  retro-fitting a landscape layout into 9:16 produces an unreadable diagram, not a small one.

**Produce the solution sheet** (in your working notes; it does not ship):

```
COMPONENTS
name | role | one-line responsibility (a claim) | count: 1 or N + why | guarantees enforced HERE

FLOWS
happy path: ordered hops. rejection path(s): where, why, status. async path(s): what, when.

NUMBERS  (the only place numbers live; everything else quotes this list)
every figure that will appear anywhere: users, RPS caps, TTLs, replica counts, timeouts.
Display format: abbreviate to K/M in every display string (50,000 -> 50K; 2,000/s -> 2K/s;
1,200,000 -> 1.2M), decided ONCE here so every fork renders the same form. Small numbers
stay exact (40 pods, 15 min, TTL 60s, HTTP 409). Never abbreviate inside literal code or
commands (`SET {sale}:stock 1000` is the real command) or where rounding changes the claim.
Headline numerals may take the style's accent (a tspan/span) -- the numbers ARE the story.

GUARANTEE OWNERSHIP  (one owner per guarantee, exactly)
guarantee -> the single component that enforces it, and the mechanism.

EVIDENCE LINKS  (when the genre requires a source lock)
source-lock ID -> the solution-sheet claim(s) it constrains. The lock owns evidence and qualifiers;
the solution sheet remains the single source of truth for render strings.
```

**Audit the solution itself** before any storyboard — the audit CHECKLIST is genre-owned, because
what can go wrong is a property of the cast: `references/genres/system-design.md` → *Solution
audits* (race / recovery / pre-condition).

## Phase 2 — Storyboard (for animated/beats output; one line each for static)

From the sheet, not from imagination:

- **Beat budget.** ~1 beat per two components, plus overview bookends. Every mechanism drawn gets a
  beat; a node no beat visits is one the viewer decodes alone.
- **Per beat, write down:** components in frame (always including the upstream node it receives
  from; next hop may peek at the frame edge) · caption · **spotlight set** (the caption's subjects,
  one or two components, highlighted for the hold; never the upstream context node) · optional interior
  morph (only to reveal a mechanism: a script, a lock, slots — never a bigger copy of the label) ·
  zoom k (≤3).
- **Classify PRIMARY vs SUPPORTING, then size accordingly.** Primary components are the mechanism
  the diagram argues (the funnel, the guard, the backstop); supporting ones are context —
  pre-conditions, third parties, recovery jobs. Supporting components render **~15% smaller** (box
  and display label together; body/sub text never drops below the `k_read` floor) and may take the
  muted stroke treatment. The 15% is an AREA target — a shape whose text already fills its width
  (a hexagon holding a long mono sub) shrinks height-only rather than overflowing its own label
  (measured: a proportional shrink pushed a 20-char sub 11px through the slant). Exactly one size
  tier apart — a three-tier ladder reads as noise, equal
  sizes read as an unweighted list. This matters most in the vertical format, where every world-px
  of width a supporting node gives up goes straight into the primary nodes' zoom headroom.
- **Give every PRIMARY component a figurative glyph; decide it here, with the primary/supporting
  split.** For each primary row write down the pictogram that says what the component IS (agent →
  bot face, text model → chat bubble with a cursor, decision model → probability bars with a
  tick) and where it comes from: a dataset shape, or a custom glyph — which is then a Phase 3
  mapping-table row (`custom glyph on <row>` / `NO ROW — custom shape`). One glyph per KIND, not
  per node; supporting components stay plain. Budget the width now: a glyph seat widens the card
  by ~30px, which moves hold bboxes and zoom (SKILL.md → Output Rules).
- **Captions restate the sheet.** Each caption is one claim copied (compressed) from the solution
  sheet — never a fact that is not on the sheet. Length ≤ what the hold carries (~5 words/second, the measured golden ceiling — camera-beat.md).
- **Story order = the request's own path**, with pre-conditions first and recovery last.

**Viewer persona audit (mandatory for educational output).** The sheet declares the audience level
("junior backend dev, builds web apps, new to scaling"). Then ROLE-PLAY that viewer through every
beat and act, in order, and write down three columns per mechanism on screen: *what am I seeing* ·
*what do I ask* · *which element or caption answers it*. The audit table lives in the sheet next to
the storyboard. Four questions are STANDING — asked of every mechanism, in every act, whether or
not they feel obvious:
1. *What is this FOR?* (a component with no named work is a defect — see the observed failure below)
2. *Who is on the other end?* (a producer with no consumer, a queue with no drain)
3. *Is this one box or many, and how do I know?* (count N → stack + `xN`; count 1 → say so)
4. **In any multi-act or multi-pane cut: *how does the PREVIOUS act's lesson show on THIS node?***
   A lesson taught in an earlier act must still be legible, in compressed form, on every later
   node it applies to — the ghost stack and its `xN`, the cache's hit rate, the delivery guarantee.
   Dropping it silently UN-TEACHES it, and no mechanical gate in this repo can catch that
   (`references/multi-pane.md` → *Attention budget* carries the rule and the golden's worked
   failure). Any on-screen mechanism whose naive question has no on-screen answer is a
**storyboard defect, fixed before the build** — either the answer gets drawn (a consumer, a cargo
label, a sub-label) or the mechanism comes off the canvas. Observed failure (2026-08-26 review): a
queue drawn with the sub-label `async work`, no consumer and no named work, sailed through every
geometry gate in the repo — none of them can ask "what is this FOR". The fix was a `worker` node
with `emails · exports` and a `drain` edge, which only a viewer walkthrough could have demanded.

**Storyboard audit — before any pixel:**
1. Coverage: every sheet component appears in ≥1 beat.
2. Upstream rule: no beat opens on a component without its source in frame.
3. Ownership: no caption or label claims a guarantee at a component that is not its sheet owner.
4. Counts: every N in the storyboard matches the sheet's NUMBERS list.
5. Cluster/singleton: count N → replica stack; count 1-by-design → never stacked, and if singularity
   IS the guarantee, say so in that beat's caption.
6. Spotlight: every content beat has a non-empty spotlight set, each set is a subset of that beat's
   caption subjects, and no set contains the beat's upstream context node.

## Phase 3 — Visual system

Only now do aesthetics enter:
- Target decision (artifact | local) — SKILL.md STEP 1. Then `--blueprint` with the scenario, and
  the Priority Routing Table for follow-ups.
- **What the blueprint decides, and what it does not.** Authoritative: diagram **type**, **layout**,
  **style**, **palette** tokens, edge semantics, motion set, anti-patterns. **Not** authoritative:
  its section-2 **component catalog**, which is one worked example of the archetype (the type's
  `Node Kinds` cell) and is labelled as such in the output. If the blueprint ABSTAINS, no type
  cleared the floor — re-run with `--type <type-id>` or rephrase; never proceed on a type picked
  from memory without saying so.
- Style per user preference / purpose (`styles.csv`); a monochrome style shifts role-carrying onto
  labels and chips and drops the colour legend.
- **Component mapping table — ONE `--domain components` query PER SHEET COMPONENT, always.**
  The component list comes from those queries and from nowhere else: not from the blueprint's
  catalog, not from memory. Run

  ```bash
  python3 diagram-director/scripts/search.py "<what this component IS, in the sheet's words>" --domain components -n 1
  ```

  for every row of the sheet's COMPONENTS block, and paste the hit into the table:

  | Sheet component | Component ID | Snippet Ref | Role | States used |
  |---|---|---|---|---|

  The build phase may only draw shapes that appear in this table, copied from the anchored
  snippet — a node with no table row is a defect. Two observed failures, both green on every
  geometry gate: shapes reasoned from memory (browsers as plain rounded-rects when
  `browser → shape-device`, an event-bus as a hand-invented drum when `event-bus → shape-pipe`),
  and the blueprint's catalog pasted in wholesale (an *auction* comparison prompt drew the
  chat-fanout example — browser, websocket-server, event-bus, cache — because the `comparison`
  type's `Node Kinds` cell froze that worked example as if it were schema). A catalog entry earns
  a table row only when the SAME Component ID comes back from the component query for that sheet
  row. If the dataset genuinely has no row (search returned 0 after the retry), record
  "NO ROW — custom shape" in the table and say so in delivery; that is the only path to a
  hand-made shape.

  `-n 1` is the default and the point: one query, one answer. If you want to see the alternatives,
  ask for them with `-n 5` — every row that comes back has cleared the domain score floor on its
  own and prints its raw score, so a short list is a short list, not a truncation.
- **The sheet records misses, not just hits.** Two kinds of row belong in the mapping table
  alongside the successful lookups, and both are findings a reader needs:

  | What happened | Table row | Why it must be written down |
  |---|---|---|
  | search returned 0 after the `-n 5` retry | `NO ROW — custom shape` (or `NO ROW — cadence on edge`) | it is the only licence for a hand-made shape, and it tells the next pass not to re-search |
  | a plausible row came back and you REJECTED it | `REJECTED <id> — <one line why>` | a false friend rejected silently gets re-proposed every session. `polling` → `cron-job` has been proposed and rejected repeatedly |

  Say both in the delivery message too. A sheet that shows only the hits reads as though the
  dataset covered everything.
- **Cadences are edges, not rows in this table.** Polling, heartbeats and health checks never get a
  component row: the interval goes in the edge label (`GET /price · every 1s`), payload `request`,
  motion `round-trip` (or staggered `packet-travel` for many clients). A 0-result search for
  `polling` means "model it on the edge" — never substitute `cron-job`, which is a scheduled
  component doing work, a different claim entirely.
- Count N → `shape-replica-stack` (ghosts outline-only). States per `data/states.csv` rows,
  named in the table's last column.

## Phase 4 — Build

Copy the style's base template; hand-place per the layout's `Spacing Rules`; motion within budget;
beats keyframes generated by a loop from the storyboard's percentages (master = multiple of every
ambient loop; negative delays; camera math in `references/camera-beat.md`).

## Phase 5 — Verify and deliver

- Render and LOOK at every beat hold — geometry checks pass on visibly broken layouts.
- Run `references/pre-delivery-checklist.md`, every item.
- The render-side gates live in `diagram-director/scripts/browser-checks/` (caption cards, text containment,
  glyph/label clearance, staged windows and acts) — puppeteer-optional, served over HTTP, and each
  one fails rather than reports green when it finds nothing to measure.
- **Text-sync sweep:** grep every number and every guarantee-claim in the delivered file(s) and
  match each against the sheet. On any fork (layout, aspect, language), diff all strings against the
  source cut.
- Video export via the deterministic seeker (compositor warm-up first) when asked.

---

**The sync rule, stated once:** the solution sheet is the single source of truth for every string in
every deliverable. A solution change never edits a caption directly — it edits the sheet, then
re-flows: sheet → storyboard → labels/captions/morphs/desc → every fork. If a string cannot be
traced to a sheet line, it does not ship.
