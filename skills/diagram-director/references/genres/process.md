# Genre pack — `process`

The authoring rules that are true only when the CAST of the diagram is **participants, work items
and steps**: the roles involved, the documents and builds they hand each other, and the decisions
that send the work one way or the other. Selected by `--genre process` (SKILL.md → STEP 0); the CLI
default is `system-design`, so this genre is always chosen deliberately.

Everything else the skill knows is ENGINE and applies whatever the cast is — the phase contract
(`references/workflow-phases.md`), camera and beat math (`references/camera-beat.md`), the
multi-pane territory machinery, orientation rule, attention budget and taught-lessons-persist rule
(`references/multi-pane.md`), the manifest spec (`references/output-manifest.md`), and the
pre-delivery checklist. This file holds only what those files would be WRONG to assert about a
diagram whose boxes are work items and steps.

**Idiom authority for this genre** is the snippet set, shipped 2026-08-27, plus the PROCESS sheet
schema below. What it holds: HTML stations + SVG-overlay connectors, product-first stations, the
two-tier LOD, the mid-beat camera follow, the 2× closing recap, and the English-elements /
Vietnamese-explanation split. The doctrine reached this file after four user review rounds; the
record is
`plans/260826-1800-workflow-explainer-and-stacked-compare/phase-05-process-vignette-pivot-status.md`.

**Checklist item 16's style-fidelity diff, in this genre, runs against the snippets:**
`templates/snippets/process-stations.html` + `process-stations.css` +
`process-stage-and-edges.css` + `process-webapp-templates.html` + `.css`,
`templates/base/flat-minimal.html` for palette and neutrals, and — for a beats cut —
`templates/snippets/camera-beat.css` block by block.

**The element-board lineage stands, and it is the standing pipeline, not a one-off.** The snippets
above are not distilled from the golden; the golden was BUILT from them. They came out of two
user-approved ELEMENT BOARDS (sampler v2, 2026-08-26; sampler v3 with the webapp template contract
v2, 2026-08-27), each reviewed cheaply as a board before any cut was built. **Sampler-first** —
storyboard → element board → user review → full build — plus **rule-of-two harvest** (an element
enters the snippets or the dataset on its second appearance or on clear universality) is how this
genre's vocabulary grows, and it is now proven over two tranches. The system-design golden CUTS
remain authoritative for ENGINE idiom (caption wipe, heading fade, spotlight brackets, act/recap
structure, the negative-delay rule) and are **not** authoritative for how a process cast is drawn.

**One accepted cosmetic limitation, recorded not chased.** Under memory pressure a caption can blink
for one frame on loop 2+ (never on pass 1) — a stale compositor tile, rasterized while the caption's
`clip-path` was parked open during its ~30s at `opacity:0`. The STRUCTURAL fix shipped: the caption
is 100% clip-driven, `opacity` is a constant 1 and never appears in a keyframe, so there is no
compositor-side visibility gate for a stale tile to slip through (its exit is now a same-direction
wipe-out — sheet deviation 24). The residue is **invisible in a rendered video and the user accepted
it as cosmetic**. **That engine pass has since shipped (2026-08-27):
`diagram-director/scripts/timeline_css_idiom.py::caption_window` now emits this exact clip-only block, so this cut's
`cap-b*` keyframes are no longer an exemption — `tests/run_golden_regression.py` diffs them
stop-for-stop like every other row, and `PROCESS_OWN_IDIOM` is down to `lod-`.** The debt moved the
other way: the three system-design goldens still carry the OLD four-segment caption and are exempted
by name (`SD_LEGACY_CAPTION`), their re-bake deferred by the user. So when a new cut needs a caption,
copy the emitter's current block — not theirs.

**One rejected cut is already on the record.** The first acceptance attempt reused the
system-design element style — boxes with labels, silhouettes for people — and the user rejected it
outright: a process explainer that looks like an architecture diagram has not been drawn for its
audience. The doctrine below is the pivot that followed, and every rule in it came from that
rejection or from a build trap that actually cost time.

---

## Construction mode — HTML-first, SVG overlay for connectors only

**Stations are HTML. Connectors are a thin SVG overlay. There is no third option.**

This is probe-proven, not a preference. A process station is a small VIGNETTE — wrapped Vietnamese
text, a grid, a glass surface, inline mono texture — and all of those are painful-to-impossible in
SVG. Connectors are the mirror image: routing an orthogonal return arc through HTML boxes is
painful, and trivial as a `<path>`. So the layers split by what each is good at, and the seam
between them is a contract (`templates/snippets/process-stage-and-edges.css`, and the copy-ready
skeleton at `snippets/process-stations.html#station-stage-contract`):

1. `.stage` carries an **explicit pixel width AND height**.
2. Its `<svg class="edges">` carries `viewBox="0 0 <same w> <same h>"`. **1 SVG unit == 1 CSS px,
   forever** — no `preserveAspectRatio` guesswork, no drift after a text reflow, and edge endpoints
   stay CHECKABLE: a verifier reads the same numbers the eye does.
3. The stage hairline is `box-shadow: inset 0 0 0 1px`, **never a 1px `border`** — a border shrinks
   the 100%-sized svg by 2px and the viewBox silently drifts off the stations it points at.
4. `.edges` sits **under** the stations (z-index 1) and is `pointer-events:none`. Edges may run
   straight through a station's footprint and be occluded by it — no manual path clipping.
5. The overlay is **geometry only. Never a `<text>`.** Every word on the canvas is HTML, where it is
   crisp, wraps, and keeps its stacked diacritics.
6. Markers are declared **inline per `<svg>` with a suffixed id** (`arrow-fwd-b3`, `arrow-back-b3`).
   A shared `<defs>` living in another stage is a cross-document reference waiting to break.

**Edge semantics are carried by colour, and there are exactly three**, so the frame needs no legend:

| Edge | Means |
|---|---|
| gray solid (`.edge`) | forward handoff — the work moves on |
| orange dashed (`.edge--back`) | return / loop — it comes back for another pass |
| green (`.edge--pull`) | derivation — this was READ FROM that |

A fourth colour is a new claim; make it in the sheet before you make it on the canvas. The
annotation tie (`.edge--soft`, dashed grey, **no marker**) is not a fourth semantic: nothing travels
along it, which is exactly why it carries no arrowhead.

## Object-vignette doctrine — no human figures

**No silhouettes. No heads, no shoulders, no figures of any kind.** Objects only: a brief sheet, a
screen, a data jar, a phone, a sticky note, a URL pill, a table. The reason is not squeamishness —
figures are hard to draw consistently at three sizes, they pull the eye to the person and away from
the work, and a stylised human reads as a character in a story the sheet never wrote. Objects are
repeatable, and a process diagram's subject is the WORK, not the office.

**The escape hatch, when a source insists on naming a person or a team, is the ROLE CHIP**
(`snippets/process-stations.html#station-role-chip`): a flat-minimal labelled chip carrying the role
word, an optional one-line qualifier, and — only where the source states one — a count in its own
slot as a NUMBER. Never repeated glyphs: three copies of anything reads "three identical things",
which is a claim no process sheet makes.

The old silhouettes in `snippets/node-shapes-actors.html` stay on disk for history and for any other
genre that wants them. **Nothing in `process` points at them any more**; `person-actor` and
`team-stakeholder` resolve to `role-chip` / `role-chip-count`.

**The AI spark is allowed, because it is an object.** `ai-assistant` is a four-point spark in the
left cell of a box on the rail — a tool the work passes through, with an input side and an output
side. It is not a mascot and it is never a face.

## Station anatomy

A station is an **HTML block on the rail with an input side and an output side**. Three properties
make it one:

- **The title carries a VERB where the station acts.** "AI · dựng ra UI", "AI · suy ra DB + BE" —
  never a bare noun. A station named only by its identity has not said what happens there, and a
  still frame of it teaches nothing.
- **It is short and narrow enough to sit on a line.** A full-height sheet reads as a poster; the
  brief sheet is deliberately cropped to station height for exactly this reason.
- **Colour enters through `data-role` only.** No literal hex in markup. Semantic Role stays the
  engine's 7 slots; the pack-local kind lives in `components.Category`.

**The AI station ships in three sizes, one glyph**: full (rail hero), `--sm` (a busy beat where the
spark is one of several stations), `--xs` (the process strip). Below ~26px the companion star
degrades into a "+" — the `--xs` rule drops it and grows the first. Do not invent a fourth size.

**The 15px body-text floor holds, with ONE exemption: texture-class text.** The JSON rows in a data
jar, the mono rows in a code card, the button label on a strip-scale phone — these are read as
PATTERN, not as words, and are allowed down to 12px. The test is whether a viewer is expected to
read it. If yes, it is 15px or larger, and no argument about density changes that.

**Shape-cue rule.** `infra` fill (`#f1f5f9`) and `external` fill (`#f3f4f6`) are near-identical
greys. When two such stations sit ADJACENT, colour is not a distinction — one of them borrows a
GLYPH from the sheet's existing vocabulary (the strip's deploy station borrows the teal seam key —
`.st__key`, inherited from the retired `css-station-snap-seam`; at strip scale a 15px key still
reads, which is why the cartridge dropped it at full scale and the strip kept it). **Never invent a
new colour to solve an adjacency problem**: a new colour is a new semantic, and the palette is a
fixed 7.

## Product-first, diagram-second

**When a station is an artifact the audience would recognise on a screen, draw the artifact — not a
labelled box for it.** A brief is a one-page document with a header, sections and a struck-out scope
line; an app is a browser window with a tab, an address bar and real UI inside it; a phone is a
phone. The user's word for the box-with-a-label version was that it read as a diagram of a product
rather than as the product, and the diagram of a thing teaches less than the thing.

Two stations carry this today, and both are in `snippets/process-webapp-templates.html` unless said
otherwise:

- **`station-brd-doc`** (in `process-stations.html`) — the brief as a real one-page DOCUMENT: a
  label column and a value column. The grid is load-bearing, not decoration: only a grid lets the
  far LOD tier skeletonise the values while the section names still read as structure. Keep
  `station-brief-sheet` for a brief that only ever appears at strip scale.
- **`station-webapp`** + a skin — the app as a browser window. See the contract below.

The limits are unchanged: it is still a station on the rail, not a poster; it still carries no human
figure; its numbers are still texture-class SEED DATA (`128`, `$12`, `2h`) rather than claims the
source made, exactly the licence the data jar's fake JSON already has. Seed data inside a mock
product is not a figure in the sheet's `NUMBERS` block, and it must never be read out in a caption.

## Level of detail — two tiers, one switch

**The 15px body floor is authored in WORLD px, and the overview hold is at k≈0.80 — so a compliant
15px line PAINTS at 12px.** The overview has always been showing text as texture; it just was not
admitting it. LOD admits it: at the FAR tier the line IS texture (a skeleton bar), and at the beat
zoom the real words cross-fade in. Copy-source: `snippets/process-stage-and-edges.css` →
`css-process-lod`.

One switch, `data-lod-tier="far|close"`, on an ANCESTOR — the beat wrapper, never a per-element
toggle, so one camera hold flips every station in the frame together. Two mechanisms:
`[data-lod="close"]` is a plain reveal for text that simply is not there at the far tier (chart tick
labels, card meta, a KPI delta); `.lod` + `.lod__near`/`.lod__far` is a crossfade for a line that is
a skeleton bar far and words near.

- **Animate `opacity` only.** The near text stays in flow and defines the box height; the skeleton is
  absolutely positioned over it. Station height is IDENTICAL at both tiers — a station that changes
  height on a tier flip has broken the mechanism, and the eye reads the reflow as an error.
- **The fade runs after the camera stops, not during the move.** 0.34s. Two motions overlapping and
  the eye tracks neither; the whole reading time then sits inside the hold.
- **LOD is a licence to REVEAL MORE, never a licence to author SMALLER.** Close-tier text still
  honours the 15px world floor. The only sub-15px text on a process canvas is texture-class, and it
  was exempt with or without LOD.
- **The close tier must PAY.** "Core flow" resolving into three numbered steps is a reward; the same
  sentence in bigger type is not. A zoom that only enlarges has not earned the beat.

## Webapp template contract (v2)

**One shell, many skins.** Every webapp station in this genre is the same station wearing a
different skin: `snippets/process-webapp-templates.html#station-webapp` plus one of
`#station-webapp-dashboard` / `-social` / `-ecom`. What is fixed is small, and everything else is
free.

**INVARIANT — true of every flavour:**

1. **Browser chrome + the address.** A tab strip and an address bar carrying `my-app.pages.dev`.
   This is what says "it runs on the web, you open it with a link" — before the deploy beat says it.
2. **Exactly THREE semantic anchors.** Three UI elements a viewer can SEE are showing data, each
   marked `data-anchor="<column>"`, each measured, each the departure point of one green derivation
   pull-line to the table beat.
3. **The two-tier LOD discipline** (above).
4. **Flat-minimal tokens.** Colour through `data-role` only; no gradient ON a station.

**VARIABLE — the entire content layout.** Each skin lays itself out the way that kind of app really
lays out: a dashboard gets a toolbar over KPIs and a list, a feed gets a composer over full-width
cards, a shop gets a filter rail beside a product grid. **A feed that docks a form beside itself is
not a feed.**

**A FORM IS ONLY ONE POSSIBLE ANCHOR SOURCE.** Version 1 of this contract required a docked
three-field "Add new …" panel on every flavour, and the user rejected it — *"nhìn cứng quá"* — with a
correction that goes deeper than the taste call: *"Từ UI element có thể suy ra được cấu trúc dữ liệu
chứ không nhất thiết là từ Form UI"* (2026-08-27). v1 bent dashboard, feed and shop into one shape
and made the story read as *"the AI reads the form"*. v2 says the true thing: **the AI reads the
interface itself** — an author line, a price pill, a "2h" — and infers the schema from it. The
`.panel` / `.fld` / `.cta` block is DELETED, not deprecated: with the anchor decoupled from the form
there is nothing left to dock, and a dead docked panel is exactly the rigidity that was rejected.

**ANCHOR RULES**

- **An anchor may never BE, or sit inside, a `[data-lod="close"]` element.** That element is
  `opacity:0` at the far tier, so its pull-line would leave from a box the viewer cannot see at
  overview and the three-anchor claim would be a zoom-only truth. When the field must be texture at
  overview, wrap it in the `.lod` CROSSFADE — that box is never gated.
- **The dot must touch its carrier.** A crossfade box that spans its whole row leaves the marker
  floating in empty space beside the words: shrink the box to the words (`display:inline-block`) and
  then force the far-tier skeleton to fill it, or the same gap re-opens at overview. A card carrying
  a right-edge anchor needs ≥11px of extra right padding (7px offset + a 2px ring).
- **The anchor set follows what the UI SHOWS, and the column sets differ per flavour** —
  `amount/name/created_at` for the dashboard, `name/created_at/content` for the feed,
  `name/stock/price` for the shop. That difference IS the lesson: the schema is read off the
  interface, so a product card yields `stock` and a post card does not. Do not force a common third
  column to make the flavours match. Two anchors on ONE row need two distinct right edges, or their
  pull-lines are collinear and read as one line — jog one path vertically while it is still under
  the station.
- **The teal anchor dot is a BOARD annotation, not cut vocabulary.** It is opt-in behind
  `[data-anchor-marks]` on an ancestor: an element board sets it, a cut never does. **In a cut the
  anchors are marked by the pull-lines themselves**, plus the spotlight bracket at the derivation
  beat if the beat needs more.
- **Write the path `d` from the MEASURED right edge**, never from arithmetic. Every pull-line on the
  approved board was re-measured and rewritten three times as the layout settled.

**FLAVOUR CHOICE.** *Pick the flavour that matches the story's domain, and never invent a brand to
get there.* If the source is about a shop, use the ecom skin — but the products stay "Product one",
the app stays "Your app" and the address stays `my-app.pages.dev`. A flavour is a SHAPE the viewer
recognises, not a company. **If no flavour matches, the dashboard skin is the neutral default**;
stretching a skin that does not fit is the same error as stretching an idiom that does not fit.

**WIDTH.** One token, `--win-w`, and two sanctioned values: **640** is the default a cut uses, and
**540** (`.win--flavor`) exists because an element board draws two flavours side by side at the
honest k pair 0.80 / 1.65 and 640 does not fit twice. Both are real; **mixing them inside one cut is
not** — every webapp station in a cut is one width.

**A SKIN'S BOUNDARY.** A skin may style anything inside its own `.webapp-skin--<name>` block, which
is always a class on `.win__main`. Styling `.win__addr`, `.win__tabs` or the `[data-anchor]` marker
from inside a skin is a contract break — the invariants are what let three flavours read as one
station family. A skin also OWNS ITS ANCHOR MAP: it declares in its snippet header which three UI
elements carry which columns.

**Mechanised.** `diagram-director/scripts/browser-checks/verify-html-edge-anchors.mjs` enforces the countable half of
this contract on every `--genre process` cut: `WEBAPP-CONTRACT` (exactly three `[data-anchor]`, a
`.win__url` in the chrome, and zero anchors on a `.win--deploy` station), `ANCHOR-GATED` and
`LOD-LEAK`. It is scoped to stations that carry `.win` or hold a `[data-anchor]`, so a cut with no
webapp station is untouched.

## The deploy beat — the same app, a narrower screen

The deploy beat is drawn as a **responsive pair**: the app window beside a small phone showing the
same app reflowed, plus the address pill under them (`snippets/process-webapp-templates.html#station-deploy-responsive`;
the user chose this over the window-alone option on 2026-08-27 — *"đầy đủ hơn"*). `deploy-url`'s
row still points at `#station-url-pill`, which is the pill INSIDE this station; the pair is the
composition the beat uses.

- **The window at this beat carries NO anchors and no toolbar** (`.win--deploy`). The claim here is
  "it is live at an address", not "here is what you can do" and not "this is where the data lives".
  Anchors belong to the derivation beat and nowhere else — the checker fails a `.win--deploy`
  station that carries one.
- **Three things make the phone read as the SAME app** rather than as a second product, and dropping
  any one of them breaks it: it carries the **same address string** in its own url bar; its content
  is a **re-stack** of the window's own KPI row and first card, with nothing invented for the phone;
  and the tie between them is `.edge--soft` — dashed, **no marker**, because nothing travels along
  it. The tag reads `Same app / narrower screen`.
- **The ripple is deliberately absent.** `station-phone-ripple`'s claim is "somebody just tapped
  it"; this beat's claim is a different one. Use the ripple phone when the beat really is about
  somebody using the thing.
- **The address must FIT.** At a 216px phone shell the url bar has 158px of text room for a 144px
  string. A clipped or wrapped address reads as a bug, not as an address — widen the box or shorten
  the string, never shrink the type below the floor.

## Semantic-tracing licence — creativity INSIDE stations

The efficiency framework this genre runs on: **content is unbounded, GRAMMAR is bounded.** The
dataset and the snippets capture the grammar — station shells, the stage contract, the edge
vocabulary, the proven idioms. What goes INSIDE a station is not enumerated anywhere and does not
need to be.

**The licence: a station's interior may be invented freely, as long as every element of it traces to
a line in the SOLUTION SHEET — not to a catalog row.** The three fields on a form trace to the
sheet's artifact description; the three columns in the table trace to the same line, which is why
the pull-lines pair one-to-one. A jar of fake JSON traces to "runs on seed data". An element that
traces to nothing is decoration, and decoration is what makes a process diagram look busy while
teaching less.

The inverse is also a rule: **do not stretch an idiom that does not fit.** When no vignette is
earned, `snippets/process-stations.html#station-stage-contract`'s plain titled box (`.node`) is the
honest drawing, and its title still carries the verb.

**A metaphor a cut invents ONCE is decoration; a metaphor with an entry here is vocabulary.** The
licence above is for a station's INTERIOR — what a form or a table or a jar contains. It is not a
licence to invent a new SHAPE LANGUAGE for a station's shell. A shell shape that carries meaning
(an interlock, a groove, a bay) must be named in the section below before a cut may use it, because
the next cut has to be able to reach the same shape for the same claim. One-off shell metaphors are
banned by exactly this clause.

## Vocabulary — mộng / ổ / port band (the cartridge idiom)

Snippet: `snippets/process-stations.html#station-snap-cartridge` +
`snippets/process-stations.css#css-station-snap-cartridge`.
Approved 2026-08-27 from the V2 snap-block enrichment board
(`plans/reports/designer-260827-1230-snap-block-enrichment-board.md`); shipped in the golden's b5.

**When several pieces of one product are BUILT SEPARATELY and then have to fit together, draw them
as cartridge modules — and let the joint and the flow be the same object.**

- **mộng / ổ — knob and socket.** Each piece carries a jigsaw **knob** (mộng) on its right edge,
  already seated in the next piece's **socket** (ổ). The knob wears the **LEFT** piece's role
  colour, never the right one's: the record *leaves* that piece and the next one *receives* it, and
  a joint painted in the receiver's colour reverses the sentence. The knob deforms the piece's own
  outline, which is why it survives the overview hold — a seam key laid ON a piece does not, and
  that is what retired `css-station-snap-seam`.
- **port band — the packet THROAT.** A full-bleed groove across the bottom of every piece, joining
  into one continuous run. **Once a multi-piece station has product interiors, the pieces must DRAW
  the channel the packet runs in**: a packet crossing three rich interiors at mid-height is
  untraceable, and the first thing enrichment costs you is the place the flow used to live.
- **They share a centre line.** The knob sits dead-centre on the port band, so the interlock and the
  throat are one object rather than two competing details. A cut's packet path is DERIVED from that
  line — `block bottom − 23px` at the shipped `--port-h:46px` — never eyeballed.
- **The band belongs to the PIECES, not to the stage.** Three pieces each draw their own edge-to-edge
  segment and the segments join. Do not also draw a stage-level rail under them: a block with both
  gets a seam in its own groove.
- **A station that contains other stations draws them as MINIATURES, and a miniature must re-use its
  full-size sibling's silhouette, not a new one.** The cartridge's three interiors are
  `#mini-dashboard` (the same browser window b3/b4 shows), `#mini-api-card`, `#mini-items-table` (the
  same `items` table `station-schema-table` draws). All their strings are texture-class.

**When NOT to use it.** If the beat teaches the *result* ("it is one app") rather than the *act of
snapping*, a single chassis with bays says that better and this idiom oversells the separation. And
the cost is real and must be budgeted before it is chosen: the cartridge is **152px taller** than
the flush-rects block it replaced, which in the golden moved the verdict banner, both overview
captions, the b5 spotlight bracket, the b5 packet path and the b6 edge.

## Rule-of-two harvest — how the library grows

**An element enters `templates/snippets/` (and, if it is a cast kind, `data/components.csv`) on its
SECOND appearance, or on a clear universality argument. Not on its first.**

A first appearance is a one-off that happened to be needed; a second is a pattern. This keeps the
library small enough to read and stops the dataset filling with shells nobody reuses. The list card
is the worked example: the back-end block and the acceptance checklist are one shell doing two jobs,
so the shell was harvested and both point at it. **Rules are harvested the same way, and only from
real build traps** — every clause in the trap list below cost time in an actual build. A rule
invented from imagination is a rule nobody can check.

**The webapp skins are the worked example of the second clause.** The shell and the dashboard skin
met rule-of-two on their own (the shell ships twice in one cut — the app beat and the deploy beat —
and the dashboard shipped in a cut). The social and ecom skins were FIRST appearances, and they
entered on the universality argument the doctrine allows: after "dashboard", "a feed" and "a shop"
are the two shapes a vibe-coded webapp most often is, and the board demonstrated all three are one
station with a swapped main region — so the harvest costs one shell plus three small content modules
rather than three stations. **That argument was only valid once the user approved the board**, and
they did (2026-08-27). Without that it would have been two one-offs waiting for a second appearance.
Their PRIMITIVES — KPI tile, mini chart, item / post / product card — did NOT enter as separate
snippets: each appears inside exactly one skin, so each is still a first appearance, and a snippet
nobody can reference from a CSV row is shelf-weight.

**The cartridge's three miniatures, 2026-08-27, are the second run of the same argument.**
`#mini-dashboard` and `#mini-items-table` cleared rule-of-two on their own — each is the SECOND
appearance of a silhouette the cut already draws full size (`station-webapp` + dashboard skin, and
`station-schema-table`). `#mini-api-card` was a **FIRST** appearance and entered on the universality
clause: an API card — a few routes with method badges — is what "a back-end" looks like in every
vibe-coded app, the same shape of argument that admitted the social and ecom skins. **And, as with
the skins, that argument was only valid once the user approved the board** — they did, and the
approval IS the ruling. Without it, `.mbe` waits for a second cut.

## The sampler-first phase — official for this genre

Between the storyboard and the full build, this genre inserts a phase the engine does not have:

**storyboard → ELEMENT BOARD → full build.**

The element board is a static sheet of every station the storyboard needs, at final style, with no
timeline and at most one animation. It is cheap to produce, the user reviews it BY EYE in one pass,
and a rejection at that point costs a sheet instead of a cut — which is the whole argument, since
the style rejection above cost a cut.

Rules for the board: real style, real palette, real copy, generic content, one card per station
family, and a final card showing the whole workflow at strip scale — **the five-second test**. If
the still strip is not legible in five seconds, the STORYBOARD is wrong, not the card.

**Derive the CORE WORKFLOW first, before any of this.** The lead's first output is not a storyboard,
it is the shortest path through the process that still teaches it. A cut that follows the structure
of its source article instead of the shape of its workflow will board beautifully and explain
nothing.

## Generic-content rule

**Examples stay generic.** "Your app", `items`, "Item one", `my-app.pages.dev`.

A concrete invented product — a named restaurant app, a named startup — steals attention from the
process: the viewer starts reasoning about the domain instead of the workflow, and every reviewer
comment comes back about the example rather than the steps. Use the audience's own domain ONLY when
the source supplies it and the cut is for that audience specifically.

**Matching a domain is a matter of SHAPE, never of brand.** The webapp station ships three skins for
exactly this reason: a story about a shop gets the ecom skin — and the products stay "Product one",
the app stays "Your app", the address stays `my-app.pages.dev`. See *Webapp template contract (v2)*
→ FLAVOUR CHOICE. Mock seed data inside a skin (`128`, `$12`, `2h`, `Mon…Sat`) is texture, not a
figure: it never enters the sheet's `NUMBERS` block and no caption ever reads it out.

**Keep the placeholder SHORT, and check it against its own box.** The first cut shipped
`app-cua-ban.example.dev` in a URL pill and the address wrapped onto two lines — a broken address
does not read as an address, it reads as a bug. A wrapped label is never fixed by shrinking the
type (the 15px floor is a floor): shorten the string or widen the box, and re-measure the station,
because its height is what the spotlight bracket was cut to.

## Language — element text is ENGLISH, explanatory text follows the audience

Two registers live on one canvas, and they do not take the same language.

| register | what it is | language |
|---|---|---|
| **ELEMENT text** | station titles and sub-labels, mock-UI chrome, table and column names, jar and pill labels, the diamond's question, sticky notes, snap sub-labels, tags on an edge, the banner headline | **English, always** |
| **EXPLANATORY text** | the beat captions, the narration (`<figcaption>`/`aria-label`), the page heading and subtitle, the banner's sub-line | **the audience's language** |

The elements are the *artifact* the process produces — a real screen, a real table, a real address —
and software artifacts are named in English in the world the audience is being shown. The captions
are a *person talking to that audience*, and they talk in the audience's language.

**Unaccented Vietnamese identifiers are banned outright.** `bang_du_lieu`, `ten`, `gia_tri`,
`thoi_gian` were on the first cut's schema table and the user rejected them on sight — *"text trên
các element đừng dùng tiếng Việt không dấu, kì lắm, cứ dùng English"* (2026-08-27). Stripped
diacritics are neither Vietnamese nor English; they read as a machine's transliteration and they
undercut the one thing the mock-up is claiming, which is that this is what your real database will
look like. `items` / `name` / `amount` / `created_at` is the register to write in.

**An explanatory caption may NAME an element**, and it should — that is how the viewer ties the
words to the box. Quote the element's own English name in mono inside the sentence
(`Từ bảng <code>items</code> vừa suy ra…`) exactly as a person would say it out loud. What it must
never do is translate the element's label, which leaves the caption naming a box that is not on
screen.

## Flat-minimal lock — and no handwriting fonts

The genre is locked to **flat-minimal**. No hand-drawn/sketch style, no wobble filter, no gradients
on stations.

**No handwriting font, ever.** Vietnamese stacked diacritics (ế, ộ, ữ) turn to mush in a script face
— the marks collide with the ascender above them and the word stops being readable at station
scale. This is a legibility fact about the writing system, not a taste call, and it does not soften
for a Latin-only cut of the same diagram: the vocabulary must be one vocabulary.

## HTML-mode contract

`process` cuts are HTML pages, not SVG documents, so three engine assumptions need restating:

- **a11y is `<figure aria-label>`, not `role="img"` + `<title>`/`<desc>`.** Each beat is a
  `<figure>` whose `aria-label` says what the frame SHOWS, with an optional `<figcaption>` carrying
  the caption a sighted viewer reads. The `<svg class="edges">` overlay is `aria-hidden="true"` —
  it is pure geometry and has nothing to announce.
- **The frame must be FIT to the viewport, and it is one CSS line.** An SVG-mode cut gets this
  free from `svg{width:min(100vw,177.8vh)}`; an HTML-mode `.frame` is a fixed `1920px × 1080px`
  box, so in any window narrower than 1920px its right and bottom edges are simply CUT OFF — the
  overview beats lose the end of the flow, and nothing in the headless gates sees it, because they
  all run at exactly 1920×1080. The rule, no JavaScript:
  `:root{--fit:calc(min(100vw,177.7778vh) / 1920px)}`, `html,body{height:100%;overflow:hidden}`,
  `.frame{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) scale(var(--fit))}`.
  **Centring is NOT `place-items:center`** — a grid does not centre an item WIDER than its track,
  it parks it at the start edge, and scaling about the element's own centre then leaves half the
  paint off-screen (measured: a 1920px frame at a 1280px viewport landed at x=320..1600).
  Keep the AUTHORED px layout box and scale only the paint: every station offset, every path `d`
  and every camera `tx/ty` is written in those px, and a fluid frame re-derives all of them per
  viewport until the overlay no longer agrees with the divs. The factor is exactly `1` at a
  1920×1080 viewport, so every gate measures unchanged pixels, and an ancestor scale is harmless to
  `verify-html-edge-anchors.mjs` — it divides the stage rect by the viewBox and reasons in
  stage-local units. Copy-source: `templates/snippets/process-stage-and-edges.css` →
  `css-process-fit` (contract clause 7).
- **The camera transform goes on a DIV wrapper**, never on the stage or on a station.
  `backdrop-filter` sampling is computed against the transformed ancestor's rect, so **any glass
  surface must live OUTSIDE the camera subtree** — inside it, the blur samples the wrong region and
  the surface changes appearance as the camera moves.
- **Edges must be CHECKABLE on the SVG overlay.** Because 1 svg unit == 1 css px and both endpoints
  are HTML boxes at known px offsets, every edge endpoint can be verified against the station it
  claims to touch — the same two defect classes `diagram-director/scripts/verify_edge_anchors.py` enforces for
  SVG-mode cuts. **The instrument is `diagram-director/scripts/browser-checks/verify-html-edge-anchors.mjs`**, and
  `verify_all.py` runs it in place of `verify-text-containment.mjs` whenever the manifest declares
  `"genre": "process"` (that checker reasons about `g.node`/`.node__shape` and finds nothing here).
  It adds the HTML mode's own third class, **DEAD GEOMETRY** — clause 4's cost, below — and carries
  the **webapp template contract** (`WEBAPP-CONTRACT` / `ANCHOR-GATED` / `LOD-LEAK`), scoped to
  stations that declare `.win` or hold a `[data-anchor]` so a cut without one is untouched. Mark
  every station with `data-station="<id>"`: that attribute is what the checker measures.
  This is the entire reason connectors are not drawn as HTML pseudo-elements: an unverifiable
  connector is one that will silently point at nothing after a copy edit.
- **a11y is checked accordingly.** `verify_all.py`'s stage-B `aria` check branches on the manifest's
  `genre`: for `process` it asserts a `<figure aria-label>`, an `aria-hidden` edge overlay and a
  narration element (`<figcaption>` or `[data-narration]`) instead of `role="img"` + `<title>`/
  `<desc>`. Keep the narration visually hidden with `clip-path`, never `display:none` — that
  removes it from the accessibility tree too, which is the opposite of the point.

## Build traps — encode as rules

Every one of these cost time in a real build. They are cheap to obey and expensive to rediscover.

- **`z-index` opens a stacking context.** A packet given a large z-index inside a station's subtree
  still cannot rise above a sibling station. Promote it to a stage-level child instead. (This
  trapped the travelling packet for an hour.)
- **Overlays on a grid are grid-area items, never `calc()` absolutes.** Positioning an overlay by
  arithmetic over the track sizes re-derives a number the grid already knows and drifts the moment
  a track changes.
- **Animate `transform` and `opacity` only.** `top`/`left` was used once: a re-layout per frame and
  a visibly different easing curve.
- **`transform-origin` is element-local.** A station already carrying `rotate(-2deg)` scales about
  its own centre, not the stage's — bake the existing rotation into the keyframes rather than
  fighting it.
- **`backdrop-filter` under a camera-transformed ancestor changes its sampling rect.** Keep glass
  out of the camera subtree (see HTML-mode contract above).
- **`background-attachment: fixed` is a loop-seam generator.** It re-anchors the dot grid to the
  viewport, so a camera move or a loop restart tears a visible seam across the stage.
- **Check for DEAD GEOMETRY.** Because edges pass under stations, an edge whose entire run is
  occluded is invisible. Every path must surface somewhere; a connector that exists only in the
  markup has not been drawn.
- **An edge that hugs the FRAME edge is the second way to draw an invisible line.** Dead geometry
  hides a path under a station; this hides it under the crop. A hold's must-show bbox contains an
  edge only if the author put it there, so a rerouted connector can end up 2px inside the frame with
  every camera number green. The rule and its M = 24 frame px are engine-general and live in
  `references/camera-beat.md` → "Keep the teaching line off the frame edge"; the gate is
  `diagram-director/scripts/browser-checks/verify-frame-edge-margin.mjs`, which `verify_all.py` runs on this genre
  because it reads stations as `[data-station]` divs (the `system-design` side has its own reader for
  the same rule, `verify-svg-frame-edge-margin.mjs`, in the same stage-E slot). The process-specific
  half: **an over-the-top
  return arc is the highest-risk shape this genre draws.** It is the one edge routed along the
  STAGE's own boundary rather than between stations, so the frame's top edge and the stage's top edge
  arrive together — and it is usually a beat's SUBJECT, wearing a halo that makes it 5x wider than its
  `d` says. Put its painted band (`run y ± half the halo`) into the bbox when you author the hold, not
  after a user reports it (cost: one re-bake of the frozen golden, REV 5).
- **Anchor a ripple to the button wrapper, not to the screen body.** The body's height depends on
  how many skeleton rows sit above the button, so a body-anchored ripple drifts off-centre every
  time the content changes.
- **`offset-path` already anchors the element's CENTRE to the path.** Any leftover centring —
  a `margin-left:-7px`, a `translate(-50%,-50%)`, an `inset` fudge that made the dot look right when
  it was statically positioned — is applied ON TOP and double-shifts the travelling dot off its own
  line. The packet rode 7px above its edge for a whole build this way, and it is invisible on a
  still: measure the dot against the path in-browser, not by eye on a screenshot.
- **Nothing inside an LOD subtree may set its own `opacity`.** `[data-lod="close"]` and a station
  rule have IDENTICAL specificity, and the station sheet loads later — so a plain `opacity:.72` wins
  the cascade and the element never hides at the far tier, while every audit that counts hidden
  elements reports it as hidden. **Dim with `color-mix`, and leave `opacity` to the tier switch.**
  Cost a rebuild (`.kpi__d`); gated now as `LOD-LEAK`.
- **A bezier control point can bribe the tangent rule.** A control point is authored and need not
  touch the curve, so bending it sideways makes the local tangent at an endpoint claim an approach
  the curve never makes — a line that truly arrives from below can be made to read as arriving from
  the left and still pass a left-side test. `verify-html-edge-anchors.mjs` therefore samples the
  REAL curve (an on-path point a quarter of the terminal segment back) instead of the adjacent
  control point; straight segments keep the vertex rule. The author's half of the same rule:
  **route a curve so its approach DIRECTION agrees with the side it lands on** — if the eye has to
  accept a landing the run does not support, the reader calls it a mis-attachment, and is right to.
- **A derivation line that crosses a lot of interface reads as a mis-attachment.** Pull-lines from
  anchors INSIDE a webapp station are drawn over that station's own UI. Two of them once climbed
  311px and 341px across a whole dashboard to reach a schema table parked at the top of the column,
  and the cut was reported twice as "wired to the wrong edge" when the endpoints were in fact
  correct. Place the target so the fan is SHALLOW — land the rows on the anchors' own vertical band,
  level the middle row with its anchor — and thread each run through the empty channels between
  cards rather than through their text. Legal geometry is not the bar; a reader who mistakes it is.
- **Every edge modifier must be able to stand alone.** `.edge--pull` is used WITHOUT `.edge`, and
  only `.edge` carried `fill:none` — a straight `M…H…` path encloses no area, so nothing showed
  until the day a pull-line got a jog and SVG painted a black triangle across the frame. A modifier
  that only works next to its base class is a latent defect with a delay fuse.

---

## Cast ontology — what earns a box

Three kinds, and the `Category` cell of every `process` row in `data/components.csv` is one of them.

- **Actors** (`Category: actor`) — the roles, teams, and the AI or external tool that produces work.
  A box per PARTICIPANT, labelled by ROLE, drawn as a ROLE CHIP (never a figure — see doctrine).
  The headcount in `team-stakeholder`'s count slot is OPTIONAL: where the source states no number,
  the slot carries context instead ("on their own device") and the sheet records
  `NO NUMBER IN SOURCE -- headcount`. Rows: `person-actor`, `team-stakeholder`, `ai-assistant`.
- **Artifacts** (`Category: artifact`) — the work items: a brief, a screen, a code change, a
  deployed URL, an acceptance checklist, a feedback note. A deployable is an artifact HERE — in this
  genre a release is a work item somebody produced, not a running service. Rows: `document-spec`,
  `prototype-screen`, `webapp-feed`, `webapp-shop`, `deploy-url`, `test-checklist`, `feedback-note`,
  `code-artifact`. The three webapp rows are one station with three skins, not three stations:
  `prototype-screen` → dashboard (the neutral default), `webapp-feed` → social, `webapp-shop` →
  ecommerce. **Their `Semantic Role` cell says `data`** because that is what the role table below
  says an artifact is; every cut shipped so far draws a running app at `client` (it is the surface
  the user touches) and the sheet's ROLE column records that, which is the same row-default /
  cut-drawn split the actor rows already use.
- **Actions** — **steps are NOT boxes.** A step is a BEAT (see below). What earns a node is the case
  where **the branch itself is the subject**: `decision-point`, the question whose two answers are
  what the diagram is explaining.

**The test for a decision node:** would erasing the branch change the story? If the work always goes
the same way, that is not a decision, it is a step, and a step is a beat. A diamond drawn per step
is a flowchart of verbs, and a flowchart of verbs has lost both facts this genre exists to carry —
WHO owns it and WHAT moves.

**AI is an actor, never a decider.** `ai-assistant` produces work (`external` role: not yours, not
on your clock). If a model's answer decides the branch, the DECIDER is the human who accepted it,
and that human is the node the diagram must show.

**A gate is not a row.** A gate every item simply passes through is drawn as a lane band behind the
step cards with role `infra`, and the sheet records `NO ROW — gate drawn as a lane band` (SKILL.md
Query Contract rule 9). A gate that IS the story — the approval the diagram exists to explain — is
either a decision diamond (when it branches) or a list card at role `service` showing the checks it
applies. Spending a node on an ordinary gate makes the ordinary look expensive.

## Role mapping — pack Category to engine Semantic Role

`Semantic Role` stays the engine's fixed 7-slot palette (`csv_schema.NODE_ROLES`); `Category`
carries the pack-local kind. This table is the whole bridge. **The rendered LEGEND text derives from
`Category` + `Name`, never from the role name** — a viewer of a process diagram reads "actor — PM",
never "client".

| Cast (pack) | Semantic Role | Why that slot |
|---|---|---|
| actor INSIDE the owning team, driving the process | `client` | the origin of intent, the same job a browser does in the other genre |
| actor OUTSIDE the owning team (the end user trying it, an external reviewer, a customer) | `external` | not on your clock and not yours to direct — the same reason the AI tool is |
| artifact (brief, URL, checklist, diff) | `data` | the thing that is produced, carried and read |
| artifact that is a SCREEN the user touches (`prototype-screen`, `webapp-feed`, `webapp-shop`) | `client` | the shipped cuts draw the app window blue, and rightly: it is the story's touchpoint, not its record — the record is the table it derives |
| feedback (the edge AND the note that rides it) | `async` | out of band, later, and nobody is blocked waiting on the wire |
| decision (branch point) | `service` | something happens TO the work here |
| AI / external tool | `external` | not yours, not on your clock, not yours to fix |
| gate-as-SUBSTRATE (every item passes through it) | `infra` | it recedes; it is the ground the steps stand on |
| gate-as-SUBJECT (the approval that IS the story) | `service` | it acts on the work, like a decision |

**The inside/outside split is the first dogfood's amendment.** The table used to send every human to
`client`, and the first cut drew its step-4 participant — one real user, outside the team, whose
whole narrative job is that nobody in the team controls what they do — in the same colour as the
founder running the process. `client` is now reserved for actors inside the owning team who drive
the work. The **row** keeps the inside-the-team default in its `Semantic Role` cell; the sheet's
ROLE column records the slot this cut actually draws it in, and an outside actor drawn `external` is
that record, not a deviation. **An 8th role is forbidden** until a cut proves seven insufficient — an
unmapped role means a station asking for a `var(--role-<role>)` token that no palette defines.

## Steps are BEATS

A step is an engine temporal unit, not a node. It is drawn as the camera moving to the artifact the
step is about, with the caption naming what happens. The process genre invents no new timeline
machinery — the engine unit a step maps to is the **BEAT**.

**Beat, not act, and the difference is mechanical** (`references/camera-beat.md`): an **ACT** is a
scene group that owns the whole canvas and clears by window handoff; a **BEAT** is a caption plus
the spotlight set it names, held by exactly one camera hold, over whatever is already on canvas.

A process step is the second thing. The cast **persists** — the stations are on canvas from t=0 to
the end — and what changes per step is which of them is `flow-active`, what the caption says, and
where the camera is. Nothing clears, so nothing is an act. A cut whose steps are beats declares
`beats` / `captions` / `spotlight` / `staged-states` in its manifest, **not** `acts`; declaring
`acts` for steps makes `verify-staged-windows.mjs --acts` measure a structure the file does not have.

**When a process cut MAY use true acts:** only for a major phase change that clears the canvas. The
test is the cast, not the story's importance: if the same stations are on both sides of the
boundary, the boundary is a beat. Consequences that are easy to get wrong:

- **Beat count is the step count** (plus whatever overview / verdict beats frame them). The beat
  budget in `references/workflow-phases.md` → Phase 2 is a floor here, not a formula.
- **One camera hold per beat, never one hold spanning two.** A spanning hold's midpoint is what
  `verify-hold-geometry.mjs` and the contact sheet both read, so it reports an instant no step owns.
- **Stations persist; they do not appear per step.** What changes per beat is `flow-active` and the
  camera. A caption per beat restates a sheet line; one that introduces a new fact does not ship.

## Artifact-passes-as-payload

**The artifact IS the packet.** The brief travels; the role that wrote it does not. Attention moves
(camera, `flow-attention`), the work item moves (a packet glyph on the edge), and every station
keeps its position from t=0 to the end.

- Pick the payload row for what actually moves: a written artifact travels as **`file`** (there is
  deliberately no separate `document` row — a second name for one cargo splits the vocabulary and
  neither half ranks); a review verdict or change request travels as **`feedback`**; a plain hop
  with no cargo worth drawing stays `request`, the legal default.
  **Query it as cargo, not as an object**: `"document transfer"` returns `file` at 4.22, while
  `"the spec document handed to the designer"` returns 0. **The false friend, measured and
  rejected:** `"a document moving between people"` ranks `message` (3.27) — the chat bubble —
  because that row's vocabulary is conversation. A brief is not a chat message.
- **The edge label names the cargo AND its version**: `Brief v2`, `PR #42`, `staging URL`. A bare
  arrow between two stations is the diagram refusing to say what they exchanged.
- `feedback` edges are the orange dashed return leg — not the same kind of edge as a handoff, and
  drawing them alike is what makes a loop look like a circle of equals.

## Branch convention

A decision has two outgoing edges and **both are always drawn**.

- The **taken** path is `flow-active`: full opacity, live motion, the packet on it.
- The **untaken** path is **parked at reduced opacity with its condition label still legible** —
  never erased, never unlabelled. An erased branch silently answers the question the diamond asked.
- **Both conditions live on the EDGES, never inside the diamond.** The diamond carries the QUESTION
  ("Looks right?"); the edges carry the answers, as `.pill` labels ("OK", "not yet").
- If a story shows the loop taking BOTH branches on different laps, that is two beats, not one frame
  with two live paths: the second lap re-lights the other edge and parks the first.
- Shape: `snippets/process-stations.html#station-decision-diamond` — a `rotate(45deg)` bordered
  SQUARE with a counter-rotated label. **Not a `clip-path` diamond**, which throws the border away,
  and not a rounded-rect: a rounded-rect "diamond" is no longer a decision.

## Loop-closure rule

An iterative process is only a LOOP if the closing edge teaches something.

- **The closing edge is drawn and labelled with the INCREMENT** — what is different on the next lap.
  "back to step 1" is not an increment; "sửa lại nút chính", "v2 of the brief", "one screen further"
  are. The sticky note on the arc (`station-sticky-note`) is where the increment is written.
- **A loop that teaches nothing new per cycle is decoration.** If you cannot name the increment, the
  honest drawing is a line: say the process is linear and draw it linear. The `LOOP` block of the
  sheet exists to force this answer before any drawing starts.
- **The return arc points back into the station that must ACT again**, never into the artifact. A
  loop that returns to the brief is a different (and usually wrong) claim from one that returns to
  the maker.
- **Cycle count belongs on the loop, not in prose**: "×3 laps before launch" on the closing edge,
  traced to the sheet's `NUMBERS` block. **If the source names no lap count, the closing edge
  carries the INCREMENT alone** and the sheet records `NO NUMBER IN SOURCE -- lap count`. An
  invented "×3" is a claim about somebody's process that nobody made.

## Persona audit — run before delivery, in place of nothing

The system-design genre audits the solution (race / recovery / pre-condition). The process genre
audits the AUDIENCE, because a process diagram's failure mode is not a wrong architecture, it is a
correct diagram its reader cannot act on.

- **Declare the audience in the sheet, in one line** ("non-technical founder", "a new hire on day
  one", "the approvals committee").
- **Per beat, answer: what does the viewer DO next?** Every step-beat must leave the declared
  audience with either an action or a correction to a belief they arrived with. A beat that leaves
  them with neither is a step you are narrating because it happened.
- **Every term the audience would not use is a defect**, not a simplification opportunity. For a
  founder, `PR`, `staging` and `acceptance criteria` each need a sub-label in their words or a
  different label. **Name the belief the cut is correcting**, if there is one, and check the verdict
  banner says it in the audience's words. Note that this audit runs on the EXPLANATORY register
  (see *Language* above): an element label stays English and is explained by the caption next to it,
  never translated into the audience's language on the box itself.
- **Read every string out loud, and cut the ones that are only a label.** Two whole classes of
  defect surface at this step and nowhere else. First, TRANSLATIONESE: a caption assembled word by
  word out of the sheet's own phrasing describes the ANIMATION rather than the idea ("dữ liệu chạy
  xuyên qua cả ba" says what the dot is doing; it does not say what the viewer should now believe).
  Second, TELEGRAPHESE: a caption clipped to three words to fit a slot leaves the beat unexplained,
  and the fix is a fuller sentence within the pace ceiling, never a smaller font.
- **A claim the cut cannot back up is a defect even when it is true.** "link công khai · ai có link
  đều mở được" was written as a plain description of a deploy URL, and the first reviewer read it as
  an access-control statement the diagram had no business making. State the PURPOSE ("share the link
  · opens on any phone") and let the security posture belong to whoever actually configures it.

## The PROCESS solution sheet

The engine's sheet-as-single-source-of-truth rule is unchanged (`references/workflow-phases.md` →
Phase 1: every string in the file traces to a sheet line, a solution change edits the sheet first).
What changes is the SCHEMA — a process has no components, flows or guarantee owners:

```
AUDIENCE
one line: who this is for, and the belief it corrects (if any).

CORE WORKFLOW
the shortest path through the process that still teaches it -- written BEFORE
the storyboard, and not derived from the structure of the source article.

CAST
actors:    role | who they are to this audience | which steps they own
artifacts: name + version | who OWNS it | which step produces it, which step consumes it

STEPS   (the step list, in order -- these are BEATS, not nodes)
n | step name (carries a VERB) | actor | artifact in -> artifact out | ENTRY | EXIT

DECISIONS
question (as drawn on the diamond) | branch A condition -> where it goes
                                   | branch B condition -> where it goes
                                   | which branch this cut draws as taken, and why

NUMBERS  (the only place numbers live; everything else quotes this list)
durations, counts, laps, people, checks. SAME display rules as the engine --
references/workflow-phases.md -> Phase 1, NUMBERS.
When the source states NO number, the row reads `NO NUMBER IN SOURCE -- <what>` and
the canvas omits it. Never invent one.

LOOP
what INCREMENTS per cycle (one line -- if this line cannot be written, it is not a loop)
how many laps the story shows, and what ends it
```

Audits over this sheet, before any storyboard:

- **Ownership.** Every artifact has exactly one owner. Two owners is the process defect the diagram
  is probably being drawn to expose — draw it, do not smooth it.
- **Continuity.** Every step's `artifact in` is some earlier step's `artifact out`, or it is an entry
  point named in `CAST`. An artifact that appears from nowhere is a missing step.
- **Entry/exit honesty.** A step whose EXIT condition is "it's done" has not been examined. What
  makes it done, and who says so?
- **Increment.** The `LOOP` line is written before the storyboard, not after.
- **No invented numbers.** Every figure on the canvas traces to a `NUMBERS` row, and a `NUMBERS` row
  traces to the source. Lap counts and headcounts are where this fails, because both this file and
  the label conventions ASK for a number — asking is not evidence.
- **Five-second test.** The overview frame, at strip scale, is legible in five seconds. If it is
  not, the CORE WORKFLOW is too long, and that is a sheet edit.

## Layout — why `timeline-sequence`, and when to leave it

`process-loop`'s `Default Layout` is `timeline-sequence`: steps are strictly ordered in time, which
is exactly what that row's Flow Direction ("a single axis progressing strictly by time/step order")
and its 5–20 event sweet spot describe. The closing edge is drawn as a return arc outside the axis
band; it does not break the axis, and it must not be routed through the step cards.

**Reading `timeline-sequence` when the axis is the FLOW.** `data/layouts.csv`'s spacing rules
describe a *passive time ruler* — a 40px disc marker on the axis, cards hung 60px above or below it,
alternating — a model that assumes the axis carries nothing but time. A process cut inverts that:
the handoff EDGES are the axis band and each is labelled with its cargo. The axis is not a ruler the
steps hang beside; **it is the flow.** Two departures to RECORD, not licence to re-space:

- **The disc-on-axis marker is dropped** — at every slot the axis position is already occupied by a
  run and its cargo label. The step NUMBER moves to a **badge on the station's own corner**
  (`.st__no`) — same information, same order, on a surface that is free.
- **Alternating sides is optional**, where the cargo labels live on the axis and the cards sit on
  one side: alternation exists to keep labels off each other, and that job is already done.

Everything else in the row's `Spacing Rules` still binds, and the sheet states the measured numbers.
A departure that cannot quote its own measurements is a re-space with a note attached. Two further
honest departures, both from `data/layouts.csv` rather than from taste:

- **`swimlane`** when several actors work CONCURRENTLY — exactly what timeline-sequence's "When NOT"
  cell sends you to. Lanes are actors, columns are steps.
- **`split-compare`** for a before/after process contrast ("with the review gate vs without"), under
  the engine's comparison rules in `references/multi-pane.md`.

**`ring-peer` is NOT the loop layout**, however circular the story is. Its own row says "circular, no
start or end" and rules out directional flows: a process loop has a first step, a direction and an
increment, and drawing it as a hash ring claims none of those exist.
