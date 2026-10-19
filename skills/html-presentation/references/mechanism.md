Skill 200Lab «Trình bày kết quả AI Tutor thành file HTML: trang lộ trình, báo cáo review, flashcard, slide, diễn hoạt cơ chế» v1 · phần mechanism «Mechanism explainer: SVG steps from one data array, play, step, scenarios» — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài.

# Mechanism explainer

The job: the learner watches how a mechanism behaves step by step (an agent loop, a retry with
an idempotency key, an outbox, cache invalidation, a reconnect with sequence numbers) and sees
each cause produce its effect.

## Data

One array of steps drives everything; the SVG never holds state of its own.

```json
{
  "kind": "mechanism",
  "title": "Retry thanh toán với idempotency key",
  "lede": "…",
  "builtOn": "2026-10-14",
  "nodes": [
    { "id": "app", "label": "App checkout", "x": 20, "y": 20, "w": 150, "h": 56 },
    { "id": "keys", "label": "idempotency_keys", "x": 230, "y": 140, "w": 170, "h": 56, "store": true }
  ],
  "edges": [{ "id": "app-api", "from": "app", "to": "api" }],
  "scenarios": [
    { "id": "with-key", "name": "Có idempotency key",
      "steps": [
        { "caption": "App gửi POST /payments kèm Idempotency-Key k1.",
          "message": { "edge": "app-api", "label": "POST k1" },
          "active": ["app", "api"],
          "state": { "keys": "k1 · in_progress" },
          "outcome": null }
      ] }
  ],
  "lesson": { "title": "…", "url": "https://learn.200lab.io/courses/…/lessons/…", "source": "200Lab" }
}
```

- `state` holds only what changed in that step; the renderer folds steps 1..n to get the state
  at step n, so going back is exact.
- `outcome` marks a step's result as `ok` or `bad` (a second charge, a lost message); it tints
  the node that shows it with `--ok` or `--crit` and adds a word, never colour alone.
- When the point is a failure the mechanism prevents, give two scenarios over the same diagram
  (without and with), shown as tabs; the learner flips between them at the same step.

## Diagram

- Inline SVG with a `viewBox` 400 units wide and labels of 15 units or more: a 360 px phone
  draws it about 320 px wide, so text lands at 12 px. Lay nodes out top to bottom, at most two
  per row, at most 7 nodes, and leave at least 80 units of bare line on every edge so the
  message never covers a box.
- Nodes are boxes in `--surface` with `--line` strokes; a data store gets a cylinder or a
  double top line; the active nodes take an accent stroke; state text sits inside or under its
  node as real `text`.
- The message is a small labelled pill that travels along its edge (500 to 700 ms,
  ease-in-out) and comes to rest on the line about 70% of the way to its target, not on the
  box. It travels because the step sends it; it is the only thing that moves.
- A node a scenario does not use is dimmed with its edges, and its state reads "không dùng".
- A state change fades its new text in over 200 ms with a brief tint on the node that changed.
- `title` and `desc` in the SVG, and the caption in an `aria-live="polite"` region.

## Layout

1. Header: title, lede, the scenario tabs.
2. The stage: diagram above the caption on a phone; from 900 px the diagram on the left and a
   step list on the right with every caption numbered, the current one marked, each clickable.
3. Controls under the diagram: previous, play / pause, next, and "Bước 3 / 7"; a progress bar
   of the steps. Targets at least 44 px.
4. Under the stage: a short "Điểm cần nhớ" list in your own words, then the lesson linked with
   its chip.

## Playback

- The file opens paused on step 1 with its state drawn; nothing plays until the learner asks.
- Play advances one step after the message lands plus reading time (about 60 ms per character
  of the caption, at least 2.5 s); it stops at the last step. Space plays or pauses, ← and →
  step, Home goes to step 1.
- Changing the scenario keeps the step number when the other scenario has it.
- Under reduced motion there is no tweening: the message appears at its destination, the state
  switches at once, and Play is hidden; stepping still works.

## Traps

- Nothing on the whole frame pulses, glows or loops; an idle diagram is still.
- Every step changes something visible; a step that only adds words is merged into its
  neighbour.
- A mechanism the answer did not explain is not drawn: the steps come from the answer and the
  lessons you read, labelled with their source.
