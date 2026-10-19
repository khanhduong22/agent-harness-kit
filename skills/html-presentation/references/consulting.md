Skill 200Lab «Trình bày kết quả AI Tutor thành file HTML: trang lộ trình, báo cáo review, flashcard, slide, diễn hoạt cơ chế» v1 · phần consulting «Consulting page: decision, options, diagram, next steps» — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài.

# Consulting page

The job: the learner sees the decision first, why it beats the alternatives for their case, and
what to do next, with the 200Lab lessons that back it.

## Data

```json
{
  "kind": "consulting",
  "title": "Retry thanh toán an toàn cho service checkout",
  "lede": "Khuyến nghị: …",
  "builtOn": "2026-10-14",
  "context": { "problem": "…", "stack": "Go, Postgres, Stripe", "constraints": ["…"] },
  "catalogFit": "strong",
  "decision": { "choice": "opt-b", "summary": "…", "source": "200Lab" },
  "options": [
    { "id": "opt-a", "name": "…", "summary": "…",
      "scores": { "Độ an toàn": "…", "Công sức": "…", "Vận hành": "…" },
      "pros": ["…"], "cons": ["…"], "source": "own" }
  ],
  "diagram": { "nodes": [{ "id": "api", "label": "Checkout API" }],
               "edges": [{ "from": "api", "to": "db", "label": "ghi idempotency key" }] },
  "nextSteps": [{ "id": "s1", "text": "…", "source": "200Lab", "lesson": "…" }],
  "risks": [{ "text": "…", "mitigation": "…", "source": "own" }],
  "lessons": [{ "title": "…", "course": "…", "url": "…", "access": "open | requires_course",
                "usedFor": "…" }]
}
```

`scores` hold the words the answer used (for example "Cao", "Trung bình"); never turn them into
numbers the answer did not give.

## Layout

1. Header: title, the lede stating the decision in one sentence, the learner's context as a
   small facts row (stack, constraints).
2. Decision card: the chosen option's name, why it wins for this case in two to four lines, and
   its source chip. Accent rule on the left edge; no glow, no badge animation.
3. Options compared: a table with options as columns and criteria as rows on desktop, the chosen
   column tinted and headed "Khuyến nghị". On a phone, one card per option, the chosen one
   first, criteria as label and value lines. Pros and cons collapse under each option.
4. Diagram, only when the answer describes three or more components and how they talk: inline
   SVG with a `viewBox`, at most 8 nodes, boxes in `--surface-2` with `--line` strokes, the
   changed or new component in the accent, edges with their labels as real `text`, a `title` and
   `desc` for screen readers. It scales to the column width; on a phone it may scroll inside its
   own box. No decorative diagram, no isometric art.
5. Next steps: an ordered checklist with checkboxes saved in `localStorage`; each step carries its
   source chip and, for `200Lab`, the lesson title linked.
6. Risks and trade-offs: short rows of risk and mitigation.
7. Lessons: the lessons the answer applied, linked, with the course; a `requires_course` lesson
   is its title, its course and the course page, never described.

## Traps

- The decision appears once at the top and once in the decision card; do not repeat it as a
  closing summary.
- A diagram that only restates a list is noise; drop it.
- When `catalogFit` is `partial` or `none`, say under the header that 200Lab does not cover the
  core of the problem and that the answer is mainly `own` and `external`.
