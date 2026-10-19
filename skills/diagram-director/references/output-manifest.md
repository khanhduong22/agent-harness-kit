# Output manifest — what a delivered diagram declares about itself

Every delivered diagram ships `<diagram>.manifest.json` beside its HTML. The manifest is what a
verifier reads BEFORE it opens a browser, so it can tell the two failures apart:

- a declared feature that renders empty on screen → **hard fail** (the cut lost a layer),
- an undeclared feature that renders nothing → **N/A** (this cut never had one).

Without it, "no spotlight brackets found" is unarguable both ways. Hand-author it today (all
four frozen goldens carry one); `diagram-director/scripts/emit_timeline.py` and `diagram-director/scripts/solve_camera.py` already print
the `holds`/`captions` fragments, so most of it is paste, not typing.

## Shape

| Key | Type | Rule |
|---|---|---|
| `manifest` | int | schema version, currently `1` |
| `genre` | string | optional; the cut's cast, from `genre_registry.GENRES`. **Absent = `system-design`** |
| `target` | object | see below — identity + timeline constants |
| `features` | string[] | closed vocabulary below; declaring one makes its check mandatory |
| `holds` | object[] | every camera hold and every windowed element |
| `captions` | object[] | one per caption, with its verbatim string |
| `glyphs` | string[] | payload glyph ids actually drawn (subset of `sources.payloads`) |
| `sources` | object | domain → dataset row ids the diagram draws from |
| `acts` | object[] | optional; one entry per act — its window and the id delta it declares |

`genre` is what the cut's BOXES ARE (SKILL.md → STEP 0): `system-design` (deployed software
components) or `process` (participants, work items, steps). It is optional, and **absent means
`system-design`** — every manifest written before the field existed is a system-design cut, so the
three system-design goldens carry no field and are read exactly as they always were; the process
golden's manifest is the one that declares it, and
`diagram-director/scripts/verify_all.py` dispatches its HTML-mode checks off exactly that field. Declaring it buys one
check: `validate_manifest.py` resolves every cited row against the datasets *and* against genre
membership, so a cut cannot claim a component from a genre it does not draw.

`target`: `file`, `title`, `type` (diagram-types.csv id), `layout` (layouts.csv id), `style`
(styles.csv id), `palette`, `register` (`reference` \| `educational`), `viewbox` `[x,y,w,h]`,
`master_ms`, `beat_ms`. Every ambient loop must divide `master_ms` — camera-beat.md's divisor rule.

`holds[]`: `kind` is one of `camera`, `act`, `state`, `spotlight`, `traffic`.
- `camera` (from `solve_camera.py`): `id`, `window` `[a,b]`, `k`, `tx`, `ty`, `center`, `bbox`,
  `fs_min`, `p_min`, and `gate` — `read` (default; the `k_read` text floor is a hard gate),
  `territory` (a pane or tier, gated per territory), or `overview` (camera-beat.md waives the
  floor: "legibility is judged per territory, never on the overview"). One **optional** field:
  `fs_min_source`, the label or selector of the text element that SET `fs_min`
  (`solve_camera.py --fs-min-source ".cap-b3 text"` copies it into the fragment). Without it a
  failing floor says only "the smallest essential text is too small" and leaves the author
  hunting for which text that is; the runner copies it into the diagnostic's evidence. It is
  optional, so the four frozen manifests stay valid unchanged. A second optional field,
  `anchor`, names the `data-node-id` this hold is held ON — see *The anchor hold* below.
- the rest (from `emit_timeline.py`): `element` (the selector carrying `data-window`), `keyframe`,
  `windows` `[[a,b], …]`, optional `source`. Percents are of the master, and MUST equal the
  element's `data-window` in the HTML — that equality is the verifier's cheapest check.
- a `spotlight` hold may carry one further optional field, `lens` `[roleA, roleB]` — the two
  `data-role` values a role-lens beat is about. Declaring it turns on the `role-lens` gates.

**One camera hold per BEAT, never per act.** A beat is a caption plus the spotlight set it names;
an act may contain several, and each one gets its own `holds[]` entry ending where the next begins.
Declaring several holds at the SAME `k/tx/ty` is normal and expected — a camera that does not move
across an act still owes one entry per beat, because the entry is what the checks measure, not what
the camera does. A hold spanning two beats puts its own midpoint in no beat's land, and two checks
read exactly that midpoint: `solve_camera --check` / hold-geometry measure the frame there, and the
contact sheet shoots its frame there. Observed in the five-tier golden's build: a single `a4` hold's
midpoint (48.5%) fell 1.9% short of the T4 end-of-act seed window, so the `HOT ROW` + `2K WPS`
payoff was missing from the contact sheet and the geometry reading was taken on a frame no beat
owned. Splitting into `a4a`/`a4b` at an identical transform fixed both and changed nothing on
screen. The recap rule below is this rule applied to the replay windows.

**Recap holds: one hold PER act-recap window, never one hold spanning them.** When the `recap`
feature replays acts near the end, the camera usually sits at the same overview for the whole
replay, and the tempting shorthand is a single hold whose window covers every recap act at once.
Declare `r1..rN` instead — one hold per act-recap window, each ending where the next act begins.
A spanning hold puts its own midpoint on an act CROSSFADE, and two checks read that midpoint:
hold-geometry measures the frame with two acts half-drawn over each other, so it reports one act's
must-show set against the other's coordinates, and the contact sheet shoots its frame there and
returns a ghost — two acts at partial opacity, which reviews as a rendering defect that is not
there. The acceptance cut hit exactly this: a single recap hold spanning the act windows produced
a ghost contact-sheet frame and a hold-geometry reading against the wrong act. Splitting it into
per-act recap holds fixed both, and changes nothing on screen — the camera transform is identical
across all of them, which is the point: the split exists so every hold's midpoint lands inside one
act, where "what is on screen during this hold" has a single answer.

`captions[]`: `element`, `text` (verbatim, byte-for-byte what the SVG renders), `window` `[a,b]`.

The `holds`/`captions` arrays are exactly what `diagram-director/scripts/emit_timeline.py --format json` prints from
the sheet's event table, plus one `solve_camera.py --json` fragment per camera hold. Emitting them
is therefore the same act as emitting the CSS: both come out of one table, so the manifest cannot
drift from the keyframes.

**The event table's columns** (copied here so this spec stands alone — a fresh agent should not
have to open the emitter to know what feeds the manifest; the emitter's own header comment is the
authority if they ever disagree):

| Column | Meaning | Required |
|---|---|---|
| `element` | selector the window rides on (`.stage-oload-a1`) | yes |
| `kind` | `state` \| `spotlight` \| `traffic` \| `act` \| `caption` | yes |
| `keyframe` | `@keyframes` name | yes |
| `windows` | space-separated `START:END[:LEAD[:TAIL]]` | yes |
| `lead` | row-default fade-in duration (default 600ms) | — |
| `tail` | row-default fade-out duration (default = `lead`) | — |
| `park` | the act's parked transform, e.g. `translate(0px,-2400px)` | act only |
| `seam` | fade-out duration for the 0% loop-seam segment | act/traffic |
| `wipe` | clip-path wipe duration (default 600ms) | caption only |
| `eps` | LEGACY no-op — the opacity-snap epsilon of the pre-2026-08-27 caption block. The caption is clip-only now, so there is no opacity stop for it to precede. Still accepted so the frozen goldens' tables parse. | caption only |
| `text` | the VERBATIM caption string from the sheet | caption only |
| `source` | dataset row id (`states:is-overloaded`), copied to the manifest | — |

Endpoints and durations carry a unit: `42.8571%`, `4000ms`, or `b2.5` (beats, needs `--beat`).

`sources`: keys are dataset domains — `types`, `layouts`, `styles`, `components`, `states`,
`motion`, `payloads` — each a list of row ids. Every id must resolve; an unresolvable id means the
diagram invented a component, a state or a motion. Colour is declared by `target.style` +
`target.palette`, not listed row by row.

## Node identity and the act delta

**Every cut declares its own graph — acts or no acts.** From this revision on, every
`<g class="node …">` in any cut carries a `data-node-id` (kebab-case, unique and stable inside the
file) and every `<path class="edge …">` carries `data-from`/`data-to` naming ids that exist in it.
It is the difference between a file a gate can measure and a file a gate can READ: without ids and
endpoints the checks see shapes and text but never the graph, and nothing can compare what the cut
draws with what the manifest claims. `node-identity` is therefore declarable by ANY cut, including
a single-act or act-less one, and its evidence is the DOM rather than `acts[]`
(`diagram-director/scripts/verify_plain_identity.py` for a cut with no act groups: every node id present and unique,
every edge endpoint resolving; `acts/node-id-missing` and `edge/endpoint-unknown` when not).

**A node's `data-node-id` is its identity across acts.** A rename is a removal plus an addition —
never a quiet edit; if the id changes, the cut is no longer claiming it is the same system. Every
`<g class="node …">` inside an act carries one: kebab-case, unique inside its act, and the SAME
string in every act the component survives. Without it the continuity rule
(`references/multi-pane.md`) can only be read, never checked — nothing in the file says the
`postgres` drum in act 4 is the drum act 1 introduced.

`acts[]` is what the cut DECLARES about that identity, one entry per act:

```json
"acts": [
  {"act": 4, "window": [41.6667, 56.6667],
   "delta": {"added":   ["api-gateway", "auth-svc", "order-svc"],
             "removed": ["alb", "app"],
             "changed": [{"id": "redis", "what": "moved"}]},
   "captionAliases": {"api-gateway": "gateway"},
   "ghostOf": ["app-monolith"]}
]
```

| Key | Rule |
|---|---|
| `act` | int, unique, ascending; matches the group's `data-act` |
| `window` | `[a, b]`, equal to that act's FIRST `data-window` pair |
| `delta.added` | exactly `ids(act N) − ids(act N−1)` — checked, not trusted |
| `delta.removed` | exactly `ids(act N−1) − ids(act N)` — checked, not trusted |
| `delta.changed` | `[{id, what}]`, `what` ∈ `topology` \| `semantic` \| `scope` \| `moved`; author-declared, checked only for id existence — no gate can infer semantics |
| `captionAliases` | id → the surface form the caption uses; keys must be delta ids |
| `ghostOf` | OPTIONAL documentation: extra ids that must also render a `.is-ghost` outline here. The requirement itself is derived — see below |

`added`/`removed` are DERIVED facts written down, so `diagram-director/scripts/verify_tier_identity.py` can refuse a
manifest that disagrees with the DOM (`acts/delta-mismatch`). That is what stops `acts[]` from being
decorative prose in JSON clothing.

**The retirement ghost is derived too, and that is the point.** An act that DROPS a component owes
it one outline farewell in that act (`references/camera-beat.md`). The set that owes one is
`ids(act N−1) − ids(act N)`, read off the DOM — not `ghostOf`, which is documentation on top. If the
requirement came from `ghostOf` alone, deleting the sheet's `ghost-of` cell and the ghost group
together would leave a green table over a cut that buried nobody: fix by deletion.
`diagram-director/scripts/verify_retired_ghost.py` therefore fails `acts/retired-ghost-missing` for any derived
retirement with no `.is-ghost[data-ghost-of=<id>]` group in that act, for a ghost whose shapes carry
a fill, and for a cut whose `<style>` has no rule scoping `.is-ghost` with `fill:none` — one deleted
rule repaints every ghost in the file solid. Declaring an id in `ghostOf` adds it to the required
set; extra ghosts beyond the derived ones are free.

**A declared `moved` waives the neighbouring cell, never the frame.** `changed: {what: "moved"}`
rebases an id's zone baseline only when the new 4×3 cell is ADJACENT (|Δcol| + |Δrow| ≤ 1). A
blanket `id:moved` must not switch `acts/identity-zone-drift` off: a component that crosses the
frame is a removal plus an addition, and the gate says so with both cells in its evidence.

**The zone rule, and its tolerance.** The continuity rule says a surviving component "anchors NEAR
its previous position". *Near* is mechanised as the **4×3 grid cell of `target.viewbox`** the node's
origin lands in — a quarter of the frame wide and a third of it tall — so a 60px nudge between acts
is free and a jump across the canvas is not. A move the author MEANT is declared:
`delta.changed` naming the id with `"what": "moved"` waives the zone check for that act, and
nothing else does.

**Caption ↔ delta is matched three ways**, because ids are kebab-case and captions are prose (and
sometimes Vietnamese): the id itself, the node's RENDERED label (its `<title>` or `.node__label`
text), or a `captionAliases` entry. The gate fails only when NONE of the act's delta ids appear in
any caption inside that act's window — the mechanical form of *"a tier caption that only restates
the CCU number has said nothing"*.

**The delta chip is one rendering of the fact, not the fact.** The sheet's `## Phase 2 — ACT
DELTA` row — and the `acts[]` entry emitted from it — IS the delta. The `+N −N` pill some cuts print
on an act title card is one optional way of *showing* it: `templates/snippets/act-delta-chip.html`
plus the `cb-delta-chip` block in `templates/snippets/camera-beat.css` ship it as OPT-IN scenery, and
the frozen goldens render none. So `acts/delta-chip-mismatch` fires only when a chip EXISTS and its
numbers disagree with `len(added)` / `len(removed)`; a cut that renders no chip reports the
`delta-chip` row (`diagram-director/scripts/verify_act_delta_chip.py`) as **N-A** — *"no chip rendered — optional scenery"* — never FAIL and never a quiet
PASS, because there was nothing there to measure.

### The anchor hold

**Before an act crossfade, hold on a node that exists in BOTH acts** — a `read`-gate hold on the
shared anchor, preferring the last active beat's subject. The crossfade then changes the system
around a fixed point instead of replacing the frame. The hold carries `anchor: "<node-id>"`, and
`acts/anchor-not-shared` fails when that id is absent from either of the two acts the hold sits
between — the act its window sits in, and the one that follows. Its `fs_min` is the anchor's own
LABEL size (not the sub), because what the beat exists to keep readable is the component's name, so
`fs_min_source` is worth declaring here more than anywhere else. Carve the window out of the
outgoing beat's tail and END IT BEFORE THE NEXT ACT UN-PARKS: a hold whose midpoint lands in the
crossfade overlap is measured and photographed with two acts drawn over each other
(`references/camera-beat.md` → The anchor hold).

### The role-lens beat

**A role-lens beat answers one question — how do these two roles talk?** Declare
`lens: [roleA, roleB]` on the spotlight hold. Every node outside those roles goes `.is-idle`;
dash-flow runs only on edges whose endpoints span the two roles. Nothing else moves; a lens that
animates a third role is teaching a different lesson than the one it announced. Edge contract: in a
`role-lens` cut every `path.edge` carries `data-from`/`data-to` node ids, which is also what makes
the lens gate stdlib — it never needs a browser to know which edge joins which roles. That contract
is ENFORCED, not assumed: an edge in a lens act that declares neither endpoint fails
`lens/edge-unattributed`, and the set comparison is reported as unrun rather than run on a shrunken
graph — stripping the attributes is otherwise a way to shrink the cross-role set until it matches
whatever is animated. And a lens hold with no window is a declared feature with no evidence:
`manifest/feature-empty` on both sides, never a PASS over zero comparisons.

### Legend as fact

**Legend entries are derived from what the DOM contains, never hand-written.** When a cut declares
both `legend` and `node-identity`, every legend entry that stands for a role says so —
`<text data-legend-role="data">data ×6 …</text>` — and the gate holds it to it: the role must
be one the DOM really draws, and the `×N` must equal the number of nodes carrying that
`data-role` in the FINAL act. The attribute is the contract because a legend also carries state
swatches and a weight ladder, which are not claims about the cast. A legend is a claim about the cast; an unbacked entry is a claim the cut cannot pay.

## Feature vocabulary (closed)

| Feature | Declared when | Mandatory evidence |
|---|---|---|
| `beats` | the cut has a camera timeline | ≥1 `camera` hold |
| `acts` | temporal act groups own the canvas in turn | ≥1 `act` hold |
| `recap` | acts replay near the end | every `act` hold has ≥2 windows, in act order; camera holds split per recap window (`r1..rN`, see above) |
| `staged-states` | state overlays ride the master | ≥1 `state` hold |
| `spotlight` | corner-bracket lock-on | ≥1 `spotlight` hold |
| `captions` | narrator cards | ≥1 entry in `captions` |
| `act-titles` | display-size act title cards | `acts` also declared |
| `payload-glyphs` | packets carry cargo glyphs | `glyphs` non-empty |
| `state-chips` | states are labelled with chips | `sources.states` non-empty |
| `replica-stack` | outline ghosts stand for counts | — |
| `legend` | a visible legend is drawn | — |
| `multi-pane` | comparison panes or load tiers | layout is `split-compare`/`progressive-tiers` |
| `reduced-motion-mode` | a `prefers-reduced-motion` block exists | always, per SKILL.md Output Rules |
| `node-identity` | every node carries a stable `data-node-id` and every edge its `data-from`/`data-to` | the DOM itself — `acts[]` is NOT a precondition; when `acts[]` is present the cross-act checks run too |
| `act-delta` | each act declares what it added and retired | `acts[]` non-empty |
| `role-lens` | a beat isolates the traffic between two roles | ≥1 `spotlight` hold with a `lens` AND ≥1 window |

`diagram-director/scripts/validate_manifest.py` enforces the shape, the vocabulary and the source ids.
`diagram-director/scripts/verify_all.py` enforces the on-screen half: it reads this file's `features` list to decide
which render-side check is MANDATORY for this cut, so a declared feature that renders empty is a
hard fail and an undeclared one is printed as `N-A` rather than silently skipped.

## Example (abridged from a shipped comparison cut's manifest)

```json
{
  "manifest": 1,
  "target": {
    "file": "compare-chat-pubsub.html",
    "title": "Realtime chat fanout",
    "type": "comparison", "layout": "split-compare",
    "style": "flat-minimal", "palette": "house",
    "register": "educational",
    "viewbox": [0, 0, 1920, 1080], "master_ms": 33600, "beat_ms": 4800
  },
  "features": ["beats", "staged-states", "spotlight", "captions", "payload-glyphs",
               "state-chips", "legend", "multi-pane", "reduced-motion-mode"],
  "holds": [
    { "id": "b3-b5", "kind": "camera", "window": [30.3571, 69.6429],
      "k": 2.2, "tx": -74, "ty": -714, "center": [470, 570],
      "bbox": [88, 422, 804, 318.4], "fs_min": 13, "p_min": 28, "gate": "read" },
    { "element": ".stage-oload-a1", "kind": "state", "keyframe": "w-oload-a1",
      "windows": [[28.5714, 42.8571]], "source": "states:is-overloaded" }
  ],
  "captions": [
    { "element": ".cap-b3", "window": [30.3571, 39.2857],
      "text": "Every server links to every other: 190 standing connections at 20 servers." }
  ],
  "glyphs": ["message", "event"],
  "sources": {
    "types": ["comparison"], "layouts": ["split-compare"], "styles": ["flat-minimal"],
    "components": ["browser", "websocket-server", "event-bus"],
    "states": ["is-overloaded", "is-down", "flow-broken", "flow-backpressure"],
    "motion": ["dash-flow", "packet-travel", "queue-fill", "camera-beat"],
    "payloads": ["message", "event"]
  }
}
```

## Governance

A manifest is governed exactly like the sheet it derives from: it states what the diagram claims,
so it is wrong the moment the diagram stops matching it. Each frozen cut's manifest is frozen with
it. Regenerating a diagram means regenerating its manifest in the same change.

**A manifest's `features` and `holds` may shrink only with a dated AMENDMENT in the sheet naming
each removed item. Deleting a declaration is not a repair — it converts a FAIL into an N-A and the
cut still has the defect.** Every render-side gate is keyed off this file: a declared feature that
renders empty is a hard fail, an undeclared one prints `N-A`. So the cheapest way to turn a red
runner green is to delete the claim, and that is exactly what this rule forbids. `verify_all.py`
stage A mechanises it (`diagram-director/scripts/manifest_shrink_gate.py`): it compares the manifest on disk with
the one committed at HEAD and fails with `manifest/shrink-unamended` when `features` or a
`holds[].id` went missing and the cut's `<cut>.sheet.md` carries no `## AMENDMENT <YYYY-MM-DD>`
section naming each removed item verbatim **on a line that says it went** (`removed`, `dropped`,
`retired`, `no longer`) — naming it anywhere in the section is not enough, because these sheets
already carry amendments about other things and the word would turn up there as ordinary prose. Growth is free. A rename is a removal plus an addition,
so it needs the amendment too — an id is what every gate and the contact sheet address a hold by.
Where there is no committed predecessor (a fresh cut, a scratch copy, no git) the row is `N-A` with
that reason: absence of history is not a skipped check, and never a pass by accident.
