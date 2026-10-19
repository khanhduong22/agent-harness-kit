Skill 200Lab «Diagram director: vẽ sơ đồ system design có chuyển động thành một file HTML/SVG tự chứa, kèm kit miễn phí của 200Lab» v1 — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài. Parts: kit-mode, solve-and-storyboard, lean-build, lean-verify.

# Diagram director (200Lab)

200Lab's method for drawing how a software system behaves as one self-contained HTML file with
inline SVG and CSS motion: architecture, request lifecycle, data flow, pub/sub, queue and worker,
scaling story, failure cascade, a with-vs-without comparison, or a process whose boxes are people
and documents. Motion shows behaviour (packets travel, queues fill, nodes pulse), never decoration.
The method is the owner's diagram-director engine (`own`); a free 200Lab kit ships the whole engine
for agents with a shell. The `ai_tutor` rules still decide budgets, the provenance footer and
lesson completion; read them first if you have not this session.
Not for a project the `ai_tutor` rules' "Lawful use only" excludes (attacking systems or accounts not the learner's, gambling, fraud or spam, content breaking Vietnamese law); for one, stop and decline as those rules say.
Drawing a botnet, DDoS or phishing infrastructure, malware command and control, a casino or betting
platform, or a flow that bypasses someone else's payment or access control is that project.

Talk to the learner in their language; in Vietnamese use mình/bạn and write "khóa".

## Route

- **Draw a system that is already decided** (the learner's own app or repo, a design another skill
  produced, the architecture a lesson describes) → this skill.
- **The architecture is still open** (which components, how many, sizing, which database or queue)
  → `system-design` first, then draw its answer. A diagram of an unsolved design is a drawing of a
  guess.
- Elsewhere: a tutor answer as a page, slides, flashcards or a click-through mechanism stepper →
  `html-presentation`; checks that the code still matches the diagram (layers, imports) →
  `architecture-conformance`; structure and coupling → `code-architecture-review`; interview
  practice → `mock-interview`. Data charts (bars, lines, dashboards), UI mockups, strict UML
  class/ER notation and a multi-scene narrated video with a script are not this skill, and 200Lab
  has no skill for them: say so in one line. Tell the learner in one line which skill fits and
  continue under it instead of this one.

## Start: choose the mode

| The client | Mode | Read |
|---|---|---|
| has a shell and files (Claude Code, Codex, Cursor's agent, any CLI agent) and the learner accepts a ~1.1 MB download | **Kit mode**: the full engine runs locally: dataset search, blueprint, templates, verify scripts | part `kit-mode` |
| a chat app without a shell, or the learner declines the kit | **Lean mode**: you hand-write one file from this method | parts `solve-and-storyboard`, `lean-build`, `lean-verify` |

A kit already on this machine is used as is, with no 200Lab MCP call to fetch it again (part
`kit-mode`, step 0); otherwise offer the kit once when the client has a shell, without pushing.
Phases 1-2 and this skill's rules hold in both modes; in kit mode the kit's SKILL.md drives 3-5.
Ask one round, at most four questions, only for what changes the drawing and you cannot read:
destination (docs, teaching, short video), format (landscape by default, vertical 9:16 for a short
video), static or narrated beats, a style the learner wants. For the learner's own system, read
the code (entry points, outbound calls, stores, queues) instead of asking what it contains.

## The method (part `solve-and-storyboard` for 1-2)

1. **Solve.** Write the solution sheet `<slug>.sheet.md`: components with one responsibility each,
   counts, flows, every number, one owner per guarantee, a source per claim. Audit it (race,
   recovery, pre-condition) before drawing.
2. **Storyboard.** Beats with frame, spotlight and caption (one sheet claim each) and the persona
   audit for teaching output; a static diagram gets a layout note, never skips the sheet.
3. **Visual system.** Genre, target, type, layout, style, shapes by component kind.
4. **Build.** One file; hand-placed coordinates; motion within budget.
5. **Verify.** Render and look; the checklist with evidence per item; text-sync sweep.

## How 200Lab draws a system

- **The sheet is the single source of every string**: labels, sub-labels, edge labels, captions,
  `<desc>`. A change edits the sheet first, then re-flows; a string that traces to no sheet line
  does not ship.
- **Decide what the boxes are before anything else.** Deployed software → `system-design` genre;
  people, documents, work items and approvals → `process` genre, drawn as cards with connectors,
  never as services and queues. A CI pipeline or a rollout is still software.
- **A label is a claim.** A guarantee written on the wrong node tells the viewer a race is closed
  where it is still open (a per-user limit on the gateway when only the store's atomic step
  enforces it). One owner per guarantee; a sub-label and its edge label never restate each other.
- **Motion means something.** Each animated edge says what travels (request, event, stream); each
  pulsing node says it is working. At most 12 animated edges: animate the primary path, keep the
  rest solid and static. Polling and heartbeats are a cadence on an edge label, never a node.
- **Many is a stack, one is a box.** N identical instances get two offset outline ghosts and `×N`;
  a component whose singularity is the point (a leader) is never stacked.
- **Meaning survives without colour and without motion.** Every colour role has a label or line
  style; `prefers-reduced-motion` renders the informative end state (packets parked, queues at
  their level, the final overview), never a frozen mid-frame.
- **Draw from evidence.** For the learner's repo, components and calls come from the code; a
  diagram drawn from memory drifts from the import graph.
- **Render and look**: geometry maths passes on visibly broken pictures. **Repair is bounded**:
  go on while the failing count hits a new minimum; after two rounds without one, stop and report.

## Getting 200Lab lessons

- Call only when the diagram explains a concept a 200Lab course teaches (a request path, cache,
  queue, pub/sub, a scaling story, a cascade, a race timeline) or the learner wants the lesson
  beside the diagram. Drawing the learner's own system needs no call.
- Read part `retrieval-200lab` of skill `agent-harness` before your first `ai_tutor_recommend`;
  call it at most once, with `skill: diagram-director` and up to three queries, one subtopic each,
  for example `"request đi qua những chặng nào và state đang nằm ở đâu"`,
  `"hệ thống lớn dần thì thêm thành phần nào, khi nào và vì sao"`,
  `"lỗi ở một service phụ lan ra cả hệ thống như thế nào"`. At most 3 lesson reads.
- Courses for diagram CONTENT: Thiết kế hệ thống (request path, load balancer, cache, queue,
  replicas, scaling, comparing two designs); Thiết kế hệ thống event-driven (queue vs pub/sub vs
  event log, saga); Thiết kế hệ thống chịu tải cao (rate limiting, load shedding, circuit breaker);
  Xử lý timeout, retry và crash (race and recovery timelines); Thiết kế dữ liệu phân tán
  (replication, leader election, failover); Nền tảng về Design Patterns (a diagram that disagrees
  with the import graph). Check each hit's `courseSlug`: courses share lesson titles. Gap: no
  200Lab lesson teaches drawing, SVG or motion; label that `own` (this method) or `external`.

## Output

- In the learner's workspace, by default `docs/diagrams/`: `<slug>.html`, `<slug>.sheet.md`, and in
  kit mode `<slug>.manifest.json` beside them. In a chat app: the HTML as an artifact or canvas
  (or a code block to save) and the sheet as a second block.
- Every sheet claim carries `200Lab` (lesson title + `url`), `own` or `external` (linked); an
  `assumption` is said as one on screen.
- Tell the learner what the diagram shows, the checklist result (kit mode: verify output and exit
  code), custom shapes or missing dataset rows, and what was not verified.

## Done-check

- The HTML file exists and a render with the network blocked requests no external host (kit mode:
  Google Fonts only; a `local` cut the learner asked for is reported as needing the network).
- The solution sheet exists, and every label, caption, number and `<desc>` sentence in the file
  traces to a sheet line: the text-sync table of part `lean-verify` is filled, no row unmatched.
- Each checklist item of part `lean-verify` has its evidence (a command and its output, a
  screenshot looked at, or `not verified` with the reason); reduced motion was rendered, not
  assumed. Kit mode: `verify_all.py` ran, its exit code is reported, and exit 3 is called
  UNVERIFIED with the stages that did not run.
- `ai_tutor_recommend` ran at most once with `skill: diagram-director`; lesson reads within 3;
  every item labelled `200Lab`, `own` or `external`.
