# Solution Sheet — Realtime Chat Fanout: Server Mesh vs Pub/Sub (comparison, 2 panes)

Single source of truth for every displayed string. Type `comparison`, layout `split-compare`,
style `flat-minimal`, landscape 1920x1080, camera-beat narration.

## Problem (shared title band)

- Title: `Realtime chat fanout`
- Subtitle: `20 WebSocket servers, one room, one message — mesh vs pub/sub`

## Architecture facts (both panes share these)

- N = 20 WebSocket servers (3 drawn + replica chip `x20 servers` on the middle one? NO —
  each pane draws ws-1, ws-2, ws-3 as individual named nodes; the x20 lives in the verdict
  math and a sub-label `3 of 20 shown`). DECISION: sub-label on pane, not per node.
- User A connects to ws-1. User B connects to ws-3. A sends one message to room #general;
  B must receive it. Delivery-to-all-members has exactly ONE owner per pane.

## Pane A — "Without pub/sub" (left)

- Owner of delivery: the ORIGIN SERVER (ws-1) — app-code fanout loop.
- Standing server-server links: N(N-1)/2 = 20*19/2 = **190** (drawn: 3 links among the 3
  shown servers).
- Per message, origin sends **19 copies** (one per peer server — it cannot know which
  servers host room members without shared state).
- Verdict chip A: `190 mesh links · O(N^2)`
- State: ws-1 `is-overloaded`, chip `19 sends/msg` (the number IS the overload cause).
- Edge labels: `1 msg` (A -> ws-1), `copy 1..19` on mesh edges (rendered: `x19 copies`),
  `deliver` (ws-3 -> B).

## Pane B — "With pub/sub" (right)

- Owner of delivery: the STREAM (broker fanout). Origin publishes ONCE.
- Standing links: N subscriptions = **20** (drawn: 3 subscribe edges).
- Per message, origin sends **1 publish**; broker delivers to subscribers.
- Verdict chip B: `20 subscriptions · O(N)`
- New (delta, accent): `event stream` node (drum), its publish edge, its subscribe edges.
- Edge labels: `1 msg` (A -> ws-1), `PUBLISH room:#general` (ws-1 -> stream),
  `fan-out` (stream -> ws-2/ws-3), `deliver` (ws-3 -> B).
- All servers healthy (no state marks) — the contrast with pane A's is-overloaded IS the point.

## Sameness map (rendered identically in both panes, same relative positions)

| Component | Pane pos (relative) | Role |
|---|---|---|
| User A (browser) | top-left | client |
| User B (browser) | bottom-right | client |
| ws-1 | left-mid | service |
| ws-2 | center | service |
| ws-3 | right-mid | service |

Delta (accent, pane B only): event stream + publish/subscribe edges.
Delta (pane A only, NOT accent — it is the pain, error-tinted at beat 3): mesh links.

## Numbers policy

Small integers exact (19, 20, 190). Big-O literal `O(N^2)` / `O(N)` — mono face,
font-variant-ligatures none (no ligature rewrites).

## Beats (master 24s, 5 beats x 4.8s)

| Beat | Frame | Caption (verbatim) | Spotlight |
|---|---|---|---|
| b1 | overview both panes | `One message must reach every room member on every server.` | none (overview) |
| b2 | pane A flow | `Without pub/sub, the origin server forwards a copy to each of the 19 peers itself.` | ws-1(A) + its mesh edges |
| b3 | pane A mesh | `Every server links to every other: 190 standing connections at 20 servers.` | mesh region (union) + verdict chip A |
| b4 | pane B flow | `With pub/sub the origin publishes once; the stream fans out to all subscribers.` | stream(B) + publish edge |
| b5 | delta close | `19 sends per message becomes 1 publish; 190 links become 20 subscriptions.` | verdict chips A+B (union spans panes) |

Caption face: Inter (text face). All captions restate sheet claims — no new facts.

## Legend

client / service / async (stream) roles + state chip meaning (`overloaded`) + solid = message
path, thin grey = standing link, accent = the delta.

---

# ADDENDUM 2026-08-26 — Educational-register upgrade: the domino scenario

Register: educational (camera-beat.md → Scenario timeline). Same architecture, same strings
above; this addendum ONLY adds the failure scenario. Master grows 24s → **33.6s** (7 x 4800ms),
7 beats x 4.8s. All prior beat %s recompute.

## Beat map v2

| Beat | Window | Frame | Caption (verbatim; b1/b2/b3/b7 reuse existing lines) |
|---|---|---|---|
| b1 | 0–14.3% | overview | (existing b1 line) |
| b2 | ~14.3–28.6% | pane A flow | (existing b2 line) |
| b3 | ~28.6–42.9% | pane A mesh | (existing b3 line) — load rises during this hold |
| b4 | ~42.9–57.1% | pane A mesh | `ws-1 dies. Every copy it owed now re-routes through its peers.` |
| b5 | ~57.1–71.4% | pane A mesh | `ws-2 inherits the load and follows — the mesh dominoes.` |
| b6 | ~71.4–85.7% | pane B flow | `The same server dies in B: clients reconnect; the stream never notices.` |
| b7 | ~85.7–100% | delta overview | `190 links become 20 subscriptions — and a dead server becomes a non-event.` |

## Event table (single source for data-window + keyframes; % of 33600ms)

| Window (%) | Subject | Transition (states.csv) | Caption claim it serves |
|---|---|---|---|
| 28.6–42.9 | ws-1-A | is-overloaded overlay ON (chip `19 SENDS/MSG` + bar) | b3 |
| 42.9–98.5 | ws-1-A | is-down overlay ON (overloaded OFF at 42.9) | b4 |
| 42.9–98.5 | pA mesh edges from ws-1 | flow-broken (gap stubs overlay) | b4 |
| 50.0–57.1 | ws-2-A | is-overloaded overlay ON; m12 flow-backpressure | b5 |
| 57.1–98.5 | ws-2-A | is-down overlay ON | b5 |
| 71.4–98.5 | ws-1-B | is-down overlay ON | b6 |
| 71.4–98.5 | pane B | staged reconnect edge User A → ws-2-B, label `reconnect` | b6 |

## Loop-seam contract

At 0% the frame equals 100%: ALL failure overlays fade out during 98.5–100% so the loop
restarts healthy. The video exporter's frame-0-vs-frame-end hash is the check.

## Reduced-motion contract (differs from act cuts)

Resting state = the ORIGINAL reference cut: healthy panes, static `is-overloaded` on ws-1-A
(chip + bar), captions/spotlights/failure overlays hidden. A frozen mid-domino would
misrepresent the design as permanently dead.

## New strings introduced (none elsewhere)

`reconnect` (edge label, pane B). Captions b4/b5/b6/b7 as tabled above. No new numbers.

## Revision 2 — camera re-solve at b6 and b3-b5 (2026-08-27)

User-approved, off the queued visual review in `plans/reports/gates-260827-1408-three-gate-debts.md`
→ Unresolved 1. **CAMERA ONLY**: no cast, no edge, no string, no window, no `k`, no caption moved.

| hold | was | now | why |
|---|---|---|---|
| `b3-b5` | `2.2 / -74 / -703` | `2.2 / -74 / **-714**` | the frame's top edge sat on world y 319.5 = User A's bottom border, so the incoming `1 msg` edge ENDED 1 frame px inside the top instead of arriving from off-frame (painted band −1.2px past it). The frame now starts 4.5 world px below that border: the edge crosses the side, User A is wholly outside, and the box no longer shows as a 1px sliver along the top. |
| `b6` | `1.4 / -1063 / -216`, bbox `1080,240,730,540` | `1.4 / **-783** / -216`, bbox `**680,240,1130,598.4**` | the frame's left edge sat on world x 759.3, which is where pane A's ws-3 → User B delivery line is drawn. That 204-frame-px line ran 0.4px over the boundary for its whole length, between two stations the same edge cut in half. The bbox now names the pane-A pair the frame would otherwise halve (and `cap-b6`'s card); the pair clears the left edge by 169 frame px and its delivery line by 281. |

**What was NOT done, and why.**

- **`k` is untouched (1.4 on both pane beats).** `multi-pane.md` cites this cut for "the frozen
  goldens frame their panes at a constant k"; solving b6 from its bbox would have put it at 1.63–1.85
  and shown pane B ~20% larger than b2 showed pane A, which is the one comparison a comparison cut
  may not make.
- **A territory frame is wider than its pane** (730 world px of pane in a 1371px frame at k 1.4), so
  the neighbour is in shot at any centre — `multi-pane.md`: *"for a comparison the neighbour's edge in
  frame is orientation, not a defect"*. The defect was slicing it, not showing it.
- **b3-b5's bbox could not take the same treatment.** Adding User A makes the must-show set 500.4
  world px tall against a 490.9px frame at k 2.2; the k that fits (≈2.0) widens the frame to world
  x 1450 and pulls half of pane B into the pane-A mesh beat. So b3-b5 got the minimum honest
  alternative — drop the frame until the edge crosses — recorded here as a deviation from "widen the
  bbox until the anchor station is whole".
- **Cost, stated:** at b3-b5 the `User A → ws-1` edge is now SCENERY to the frame-margin gate (one
  station fully off-frame) where it used to be measured-and-waived. Net measured instances 43 → 42.
