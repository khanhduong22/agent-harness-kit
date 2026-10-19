# Solution Sheet — 0 → 500K CCU (progressive-tiers, scaling-story)

Single source of truth for every displayed string. Type `scaling-story`, layout
`progressive-tiers`, style flat-minimal (Default Palette), landscape 1920x1080, camera-beat.

## Tier derivation (boundary = what BROKE, never arithmetic)

| Tier | CCU band | Architecture | What breaks at the top of the band |
|---|---|---|---|
| T1 | 0–1K | monolith (4 vCPU) + 1 Postgres | **PG connection pool exhausted** — 100 conns, one per request thread; p99 cliffs when the pool queues |
| T2 | 1K–10K | ALB + app x6 replicas + Redis cache (90% hit) + same PG | **single PG write ceiling** — ~2K wps sustained; cache can't absorb writes |
| T3 | 10K–100K | + CDN (static/API cache) + queue for async work + 3 read replicas | **hot rows + replica lag** — one viral row serializes writes; lag breaks read-your-writes |
| T4 | 100K–500K | 16 shards by user_id + pub/sub stream fan-out + 3 cells | target tier — headroom stated, nothing shown broken |

FORM (decided 2026-08-26, user direction): **temporal act-based storyboard**, NOT spatial
territories. Each tier is an ACT that owns the whole canvas; the canvas is cleared between acts
(scene-group visibility windows on the master timeline — same machinery as captions/spotlights/
staged states). The spatial 2x2-grid note moves to comparison mode only. Act layout is free per
act (T1 layered-tb 2 nodes; T4 its own layered composition) — no territory gutters.
Continuity across acts: a surviving component keeps identity (shape/role/label) and anchors NEAR
its previous position so the eye reads growth, not four strangers.

## Continuity map (identity held across tiers; new components take accent)

| Component | T1 | T2 | T3 | T4 |
|---|---|---|---|---|
| Users (browser) | 1K chip | 10K chip | 100K chip | 500K chip |
| App (service) | monolith | app x6 (replica stack) | app x12 | app x24 per cell |
| Postgres | pg (single) | pg (single, overloaded) | pg + 3 read replicas | 16 shards |
| ALB | — | NEW | kept | kept (per cell) |
| Redis | — | NEW | kept | kept |
| CDN | — | — | NEW | kept |
| Queue | — | — | NEW | kept |
| Pub/sub stream | — | — | — | NEW |
| Worker | — | — | NEW | kept |

Retired: none reappear. Every NEW component in its tier takes the accent.

## Transition captions (each names the break + the fix; restate sheet claims only)

- b1 overview: `One system, four architectures: what broke decided every boundary.`
- b2 T1: `To 1K CCU a monolith and one Postgres hold — until the 100-connection pool queues.`
- b3 T2: `Pool fixed by 6 replicas and a 90% cache; now the single Postgres caps at ~2K writes/s.`
- b4 T3: `Reads move to CDN and 3 replicas, async work to a queue; one hot row still serializes writes.`
- b5 T4: `16 shards spread the hot row; a pub/sub stream fans out; 3 cells cap the blast radius. 500K holds.`

## States (trigger shown, not told)

- T1 pg: `is-overloaded`, chip `100/100 CONNS`
- T2 pg: `is-overloaded`, chip `2K WPS`
- T3 pg-shard-hot? No — T3 shows pg + replicas with hot-row: pg `is-degraded`, chip `HOT ROW`;
  replicas paired `is-syncing` chip `LAG 1.8s`
- T4: all healthy — the healthy final tier IS the payoff; no state marks
- Edges: primary flow `flow-active`; T3 queue edge async dashed; T4 stream fan-out async

## Numbers policy

CCU chips: K abbreviation (1K/10K/100K/500K). Pool/wps exact small numbers (100, 2K wps ok as
K-form since sheet says so). Per-tier node counts within progressive-tiers sweet spot (4-12).

## Verdict chips (per tier, top-right of territory)

T1 `1K CCU · 1 box`, T2 `10K CCU · 8 boxes`, T3 `100K CCU · +CDN +queue`, T4 `500K CCU · 16 shards · 3 cells`
(final wording may tighten at build; every number traces here)

## Act map (temporal storyboard; master TBD at build — every window a divisor-true %)

- a1 T1 (~6s): intro + load climbs (CCU chip counts up via staged chips) + pg -> is-overloaded
  `100/100 CONNS` -> transition caption -> CANVAS CLEARS
- a2 T2 (~6s): upgraded design fades in (new components take accent on entry) + load climbs ->
  pg is-overloaded `2K WPS` -> caption -> clear
- a3 T3 (~6s): same arc -> hot row is-degraded + replica lag -> caption -> clear
- a4 T4 (~6s): final design, load 500K, all healthy — the payoff hold
- a5 RECAP (~3s per act = 12s): each act's scene re-shown briefly in order (opacity windows on
  the same groups; camera holds overview) -> ends parked on a4's design as the resting overview
Reduced-motion contract: ONLY a4 visible, resting states — the informative end state is the
final architecture, not a frozen montage.
Hard gates (script): per-act isolation (during act i's window no element of act j renders),
recap windows fire in order, reduced-motion shows exactly a4. Extends verify-staged-states.

## Component mapping table (from `--blueprint` + `--domain components` queries, 2026-08-26)

Blueprint meta: scaling-story · progressive-tiers · flat-minimal · Palette house · local · css-only.

| Sheet component | Component ID | Snippet Ref | Role | States used |
|---|---|---|---|---|
| Users | browser | snippets/node-shapes.html#shape-device | client | — (CCU chip is a count, not a state) |
| Monolith (a1) | monolith | snippets/node-shapes-glyphs.html#shape-monolith-frame | service | — |
| App replicas (a2+) | microservice | snippets/node-shapes.html#shape-rounded-rect | service | — (count via shape-replica-stack ghosts) |
| ALB (a2+) | load-balancer | snippets/node-shapes-glyphs.html#shape-lb-fork | service | — |
| Redis (a2+) | cache | snippets/node-shapes.html#shape-cache | data | — |
| Postgres | sql-database | snippets/node-shapes.html#shape-cylinder | data | is-overloaded (a1,a2) · is-degraded HOT ROW (a3) |
| Read replicas (a3) | read-replica | snippets/node-shapes.html#shape-cylinder | data | is-syncing LAG 1.8s (a3) |
| CDN (a3+) | cdn | snippets/node-shapes-glyphs.html#shape-cdn-globe | infra | — |
| Queue (a3+) | message-queue | snippets/node-shapes.html#shape-pipe | async | — |
| Pub/sub stream (a4) | pubsub-topic | snippets/node-shapes.html#shape-pipe | async | — |
| Shards x16 (a4) | sql-database (+replica-stack ghosts) | snippets/node-shapes.html#shape-cylinder | data | — |
| Cells x3 (a4) | availability-zone | snippets/node-shapes-glyphs.html#shape-az-pin | infra | — (sub-label "cell") |

Payload map (data/payloads.csv): user traffic edges → `request` (dot); queue edge → `event`
(packet-ping); stream fan-out → `event`; a3 replication edge → `binary-stream` (packet-bits).

---

# ADDENDUM v2 — 2026-08-26 (user review): dramatic states, act titles, queue/pubsub clarity, persona audit

## Act title cards (sheet-owned strings; staged with their act, display-size type)

| Act | Title | Sub |
|---|---|---|
| a1 | ONE BOX | 0–1K CCU |
| a2 | CLONE THE APP | 1K–10K CCU |
| a3 | SPLIT READS FROM WRITES | 10K–100K CCU |
| a4 | SHARD & FAN OUT | 100K–500K CCU |

## State intensity (educational register)

- is-overloaded: colored overlay replica (amber fill/stroke over base) + `shake-stress` + chip+bar
- is-degraded (HOT ROW): colored replica (error-tint stroke) + chip
- death (if used): `collapse-death` one-shot at window start, then STILL forever
- All via overlays with data-window; base paint never mutates; reduced-motion: replicas visible
  at rest where the state is the resting truth, shake/collapse off.

## Queue & pub/sub made concrete (fixes "unclear/incomplete")

- a3 queue gains a consumer: **worker** (Component ID `worker`,
  snippets/node-shapes.html#shape-gear, role **service** — corrected at build 2026-08-26: the
  addendum said "async per dataset" but `components.csv → worker` carries Semantic Role `service`.
  The queue is the async plumbing; the worker is the compute that drains it) — label `workers`,
  sub `emails · exports`, edge queue→worker label `drain`, payload `event`.
- The worker is KEPT in a4 as well (the sheet retires nothing): a queue drawn without its consumer
  in the FINAL architecture re-opens the exact question a3 just closed.
- a3 queue sub stays `async work`; the WORK is named by the worker's sub.
- a4 stream fan-out cargo named ON the edges: `invalidations · events`; stream sub gains
  `every cell subscribes`.
- NUMBERS: no new figures.

## Viewer persona audit (mandatory for educational register)

Audience: **junior backend dev — builds web apps, new to scaling**.

| Act | Viewer's naive question | Answered by |
|---|---|---|
| a1 | "Why does it break at 1K?" | chip 100/100 CONNS + caption (pool queues) |
| a2 | "Why not just more app servers forever?" | caption: single PG write ceiling + chip 2K WPS |
| a3 | "What is the queue FOR?" | worker node `emails · exports` + `drain` edge |
| a3 | "Why replicas if there's a cache?" | caption: reads move; LAG chip shows the cost |
| a4 | "What does the stream actually carry?" | edge label `invalidations · events` |
| a4 | "What is a cell?" | az-pin sub `x3 · blast radius` + caption blast-radius claim |

## Persona walkthrough, run against the built cut (2026-08-26)

Role-played the declared viewer (junior backend dev, new to scaling) through b1 + all four acts +
the recap. Rows marked FIXED had no on-screen answer before the walkthrough.

| Act | What I see | What I ask | What answers it |
|---|---|---|---|
| b1 | title + four-architecture subtitle | "what is this?" | caption b1: what broke decided every boundary |
| a1 | ONE BOX; users → monolith → postgres, amber and trembling | "why does it break at 1K?" | chip `100/100 CONNS` + edge label `1 conn / request thread` + caption |
| a1 | `4 vCPU` sub | "is the app the bottleneck?" | the state marks are on postgres, not the monolith; caption names the pool |
| a2 | CLONE THE APP; alb + app x6 + redis, postgres amber again | "why not just add app servers forever?" | caption (single-PG write ceiling) + chip `2K WPS` on the ONE postgres |
| a2 | `alb` | "what is an alb?" | **FIXED** — sub `load balancer`; a bare three-letter acronym answered nothing for this viewer (a4 keeps `per cell`, by then the term is known) |
| a3 | SPLIT READS FROM WRITES | "where is the split?" | **FIXED** — a `reads` edge app → read replicas. Only `writes` and `replica sync` were drawn, so the act's own title named a mechanism the canvas did not show |
| a3 | queue, sub `async work` | "what is the queue FOR?" | worker node `emails · exports` + `drain` edge |
| a3 | read replicas, `LAG 1.8s` | "why replicas if there's a cache?" | caption (reads move) + the LAG chip as the price |
| a3 | postgres red, dashed, `HOT ROW` | "the cache and replicas didn't fix it?" | caption: one hot row still serializes writes |
| a4 | SHARD & FAN OUT; postgres `x16 shards` | "how does a write find its shard?" | edge label `by user_id` |
| a4 | pub/sub stream | "what does it carry, and to whom?" | edge `invalidations · events` + sub `every cell subscribes` |
| a4 | cells | "what is a cell?" | sub `x3 · blast radius` + caption |
| a4 | queue, still here | "who does that work now?" | **FIXED** — the worker is kept in a4; it had been dropped, orphaning the queue again in the final design |

OPEN (not fixed, needs a sheet decision): a4 drops the three read replicas with no on-screen
reason. A viewer who just learned the read path in a3 asks where it went. The tier table's T4 row
does not list replicas, so this is a solution question, not a drawing one.
