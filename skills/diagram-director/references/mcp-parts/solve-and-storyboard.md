Skill 200Lab «Diagram director: vẽ sơ đồ system design có chuyển động thành một file HTML/SVG tự chứa, kèm kit miễn phí của 200Lab» v1 · phần solve-and-storyboard «Solve and storyboard: genre, the solution sheet, solution audits, beats and the persona audit (own)» — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài.

# Solve and storyboard: the solution sheet before any pixel

Phases 1-2 of the method, the same in kit and lean mode (`own`: the diagram-director engine's
workflow). The failure they prevent is text drifting from the solution: a guarantee on the wrong
node, a caption stating a fact the system does not deliver, a count that differs between a label
and a caption. One file, the sheet, holds every claim; everything on screen quotes it.

## Phase 1: questions, only those that change the drawing

- Destination and format: docs or README (static or a calm loop), teaching (beats), short video
  (vertical 1080×1920, beats). Orientation is presentation: the cast, beats and captions stay the
  same in both formats; only layout and camera targets change. Decide it now.
- What the boxes are (the genre, below).
- Audience level for teaching output ("junior backend dev, new to scaling").
- Proposing a system rather than drawing one already decided (scale, the guarantee that must
  never break, monolith or distributed) is `system-design`'s job; route there first.
- The learner's own system: read the code. Entry points, outbound calls, stores, queues and
  workers are the cast; note the file each one comes from in the sheet's source column.

## Genre: what are the boxes?

| The boxes are | Genre | How it is built |
|---|---|---|
| services, gateways, queues, stores, caches, nodes: deployed software | `system-design` | SVG nodes and edges |
| people, roles, documents, work items, steps, approvals | `process` | HTML cards (stations) holding an object that stands for the step (a document, a screen, a ticket; no human figures), a thin SVG overlay for connectors only |

A tool's workflow (a CI pipeline, a Kubernetes rollout) is still `system-design`. A protocol or
algorithm (a handshake, a consensus round, a backoff) is `system-design` drawn as a sequence or
state machine. Never draw an approval chain as services and queues: every actor is mislabelled.

## The sheet: `<slug>.sheet.md`

```markdown
# <title> — solution sheet
Audience: … · Destination: … · Format: landscape | vertical · Genre: … · Mode: static | beats

## COMPONENTS
| id | name | role | responsibility (one claim) | count (1 or N, why) | guarantees enforced here | tier | source |

## FLOWS
happy path: browser → api → orders-db (ordered hops)
rejection: where, why, status (e.g. api → 409 when the stock key is 0)
async: what, when (e.g. orders-db → outbox → email-worker, after commit)

## NUMBERS   (the only place numbers live)
| figure | display form | source |

## GUARANTEE OWNERSHIP   (exactly one owner each)
| guarantee | owner | mechanism |

## STORYBOARD   (beats) or LAYOUT NOTE (static: one line per component, its position and why)
| beat | in frame (incl. upstream) | spotlight | caption | hold s |

## MAPPING · NO ROW · DEVIATIONS
```

- `id` is kebab-case and becomes the node's `data-node-id`; the flows' hops become the edges'
  `data-from`/`data-to`.
- `tier`: `primary` (the mechanism the diagram argues) or `supporting` (context: third parties,
  pre-conditions, recovery jobs).
- `source`: `200Lab` with the lesson title and `url`, `external` with the link, `own`, plus the
  evidence (`code: services/order/handler.go`) for the learner's system. A chosen workload or
  capacity is an `assumption` and is worded as one on screen ("assume 2K req/s").
- Numbers: abbreviate once, here (50,000 → 50K; 2,000/s → 2K/s; 1,200,000 → 1.2M); small numbers
  stay exact (40 pods, TTL 60s, HTTP 409); literal commands keep their real values.
- A quick static diagram still gets a mini-sheet: components, numbers, owners. Never skipped.

## Audit the solution before the storyboard

- **Race**: report one only with its evidence: the invariant (stock never below 0) and two
  concurrent executions whose interleaving breaks it. Check and effect on two components is a
  prompt to look, not a finding; a lock, a conditional write or a transaction that spans both
  closes it.
- **Recovery**: every resource acquired has a named return path (a hold expires: who returns the
  stock?). A documented TTL, a transactional rollback or a reaper all count; no path at all is the
  finding.
- **Pre-condition**: what must exist before t=0 (seeded counters, a published page). Lazy
  initialisation on the first request is fine when it is atomic or idempotent; draw that step.

A finding goes back to the learner, or to `system-design`, before drawing; never draw around it.

## Storyboard (beats mode)

- Budget: about one beat per two components, plus an opening overview and a closing one. Every
  mechanism drawn gets a beat; a node no beat visits is one the viewer decodes alone.
- Each beat's frame contains the upstream node the subject receives from; the next hop may peek
  at the frame edge. Story order is the request's own path: pre-conditions first, recovery last.
- Spotlight: the caption's subjects, one or two components, highlighted for the hold; never the
  upstream context node.
- Caption: one sheet claim, compressed; about 5 words per second of hold (a 12-word caption needs
  a hold of at least 2.4 s). A fact the sheet does not hold never appears in a caption.
- The last beat is the full overview with every ambient motion running.
- Primary components render about 15% larger than supporting ones (one size tier only) and wear a
  glyph of their kind left of the label (a drum for a database, a bot face for an agent): one glyph
  per kind, never on supporting nodes.
- Static mode: the layout note replaces beats; flows still decide which edges animate.

## Storyboard audit, before any pixel

1. Coverage: every sheet component appears in at least one beat (or the layout note).
2. Upstream: no beat opens on a component without its source in frame.
3. Ownership: no caption or label claims a guarantee at a component that is not its owner.
4. Counts: every N on screen matches the NUMBERS table.
5. Cluster or singleton: count N → a stack with `×N`; count 1 by design → never stacked, and when
   singularity is the guarantee, the caption says so.
6. Spotlight: each set is a non-empty subset of its caption's subjects.

## Viewer persona audit (teaching output)

Play the declared viewer through every beat. Per mechanism on screen, write three columns in the
sheet: what I see · what I ask · which element or caption answers it. Ask these every time:

- What is this FOR? A queue labelled `async work` with no consumer and no named work is a defect;
  the fix is a worker node with its jobs (`emails · exports`) and a drain edge.
- Who is on the other end? A producer with no consumer, a queue with no drain.
- One box or many, and how do I know?
- In a multi-act or multi-pane cut: does the lesson of the previous act still show on this node
  (the stack and `×N`, the cache hit rate, the delivery guarantee)? Dropping it un-teaches it.

A question with no on-screen answer is fixed before the build: draw the answer or remove the
mechanism.

## Comparisons and scaling stories

- **With vs without X**: two panes, the same components in the same positions drawn identically;
  only the delta takes the accent; each pane ends on a verdict chip with its number
  (`O(N²) conns` vs `O(N) conns`). Panes sit perpendicular to their internal flow: horizontal
  timelines stack top and bottom, vertical flows sit side by side.
- **0 → N users**: a tier exists because something broke (connection pool, write contention, read
  fan-out, one region, a hot shard), never because a number is round. Each tier's caption names
  what broke and what was added; components keep their identity and position across tiers, and
  each tier fits one frame at a readable zoom. Record the derivation in the sheet.
