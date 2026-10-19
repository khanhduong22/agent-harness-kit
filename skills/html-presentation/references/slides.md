Skill 200Lab «Trình bày kết quả AI Tutor thành file HTML: trang lộ trình, báo cáo review, flashcard, slide, diễn hoạt cơ chế» v1 · phần slides «Slides: one idea per slide, 16:9 stage, keyboard and hash navigation» — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài.

# Slides

The job: the learner presents a design proposal or a review readout to their team, and a
teammate who opens the file later without them still gets the argument.

## Readable without a narrator

- One idea per slide. The headline is a full sentence stating that idea ("Thêm idempotency key
  chặn được lần trừ tiền thứ hai"), never a topic label ("Idempotency").
- Under the headline, the evidence for it: at most 3 bullets of at most 12 words, or one
  diagram, one comparison, or one number with its unit and baseline. No paragraphs.
- 6 to 12 slides: title, the problem in one slide, the proposal or verdict, one slide per
  supporting point, risks, the ask or next steps, sources. The decision or verdict comes by
  slide 3, not at the end.
- The sources slide lists every 200Lab lesson and external link the deck relies on, linked,
  with its provenance chip. Lesson content is never put on a slide.

## Data

```json
{
  "kind": "slides",
  "title": "Đề xuất: idempotency key cho POST /payments",
  "builtOn": "2026-10-14",
  "slides": [
    { "id": "title", "layout": "title", "headline": "…", "sub": "Team Checkout · 14/10/2026" },
    { "id": "van-de", "layout": "point", "headline": "…", "bullets": ["…"], "source": "own" },
    { "id": "so-sanh", "layout": "compare", "headline": "…",
      "columns": [{ "name": "…", "items": ["…"] }, { "name": "…", "items": ["…"], "chosen": true }] },
    { "id": "co-che", "layout": "diagram", "headline": "…", "nodes": [], "edges": [] },
    { "id": "so-lieu", "layout": "number", "headline": "…", "value": "37", "unit": "khách",
      "context": "bị trừ tiền hai lần sau đợt sale" },
    { "id": "nguon", "layout": "sources", "headline": "Nguồn", "items": [
      { "title": "…", "url": "https://…", "source": "200Lab" }] }
  ]
}
```

## Stage

- A 16:9 stage of 1280 × 720 CSS px, scaled with `transform: scale()` to fit the viewport and
  centred on `--bg`; type is set in stage pixels: headline 48 to 56 px, body 28 to 32 px, no
  text under 22 px.
- Below 700 px of viewport width the deck turns into reading mode: the slides stack as full-width
  cards in page type sizes, scrolled like a page, because a scaled stage is unreadable on a
  phone. The same data renders both modes.
- Layout per kind: `title` (headline, sub, nothing else); `point` (headline top-left, bullets
  below with generous space); `compare` (two or three columns, the chosen one with an accent
  rule and "Khuyến nghị"); `diagram` (inline SVG under the headline, at most 8 nodes);
  `number` (the value at 160 px or more in the accent, its unit and context beside it);
  `sources` (a linked list).
- Each slide carries a quiet footer: the deck title and "3 / 9" in `tabular-nums`.

## Navigation

- → ↓ Space PageDown next; ← ↑ PageUp previous; Home and End; a click on the right two thirds
  of the stage goes next, the left third back; swipe on touch.
- `location.hash` is `#3` for slide 3, read on load and on `hashchange`, so a link opens on
  that slide and the browser back button steps back.
- A 3 px progress bar along the bottom edge; prev and next buttons and a fullscreen button
  (`requestFullscreen`, hidden where unsupported) appear in a corner toolbar.
- The slide change is a 200 ms opacity crossfade, nothing else; no per-bullet builds, no
  zooms, no 3D. Under reduced motion it is an instant switch.

## Print

`@page { size: 1280px 720px; margin: 0 }`, every slide visible, one per page
(`break-after: page`), the toolbar hidden, the stage unscaled.

## Traps

- Keyboard handlers ignore keys while focus is inside a link or button that needs them.
- A slide that needs more than three bullets is two slides.
