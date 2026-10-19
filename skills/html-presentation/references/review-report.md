Skill 200Lab «Trình bày kết quả AI Tutor thành file HTML: trang lộ trình, báo cáo review, flashcard, slide, diễn hoạt cơ chế» v1 · phần review-report «Review report page: verdict strip, findings by severity, fixes» — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài.

# Review report page

The job: the learner sees the verdict, what to fix first and the evidence for each finding, and
can tick fixes off as they go.

## Data

```json
{
  "kind": "review",
  "title": "Review: chatbot bán hàng theo khóa Agent Harness Foundations",
  "lede": "Kết luận: …",
  "builtOn": "2026-10-14",
  "subject": { "name": "sales-bot", "path": "~/code/sales-bot", "commit": "a1b2c3d" },
  "yardstick": { "course": "…", "url": "https://200lab.io/courses/…" },
  "criteria": [
    { "id": "c1", "text": "…", "status": "met | partly | not_met",
      "lesson": { "title": "…", "url": "…" }, "evidence": "agent/loop.go:Run" }
  ],
  "findings": [
    { "id": "f1", "severity": "critical | high | medium | low", "area": "Tool gate",
      "title": "…", "evidence": "internal/tools/refund.go:Execute", "detail": "…",
      "fix": "…", "source": "200Lab",
      "lesson": { "title": "…", "url": "…", "access": "open | requires_course" } }
  ]
}
```

- Severity and status counts, and the area list for the filters, are computed from the data.
- A score shows only when the review computed one; criteria met out of total is always safe.

## Layout

1. Header: title, the verdict as the lede, the subject (name, path or commit in `code`), the
   yardstick course linked.
2. Summary strip: criteria met / partly / not met as one segmented bar with counts, then one chip
   per severity with its count. The severity chips are the filters below; a chip with zero
   findings is shown dimmed and disabled.
3. Criteria table, only for a review against a course: criterion, status, evidence, lesson.
   Status is a word plus a glyph (tick, half, cross), never colour alone.
4. Findings, critical first, then by the order of the answer. Filter by severity chips and by an
   area select; a line "Hiển thị 4 / 11" updates with the filter. Each finding is a card:
   - first line: severity chip, area, the "Đã sửa" checkbox at the right;
   - title, then evidence in `code` (file:function) with a copy button;
   - detail in one or two lines; the fix as its own labelled block;
   - the lesson that sets the criterion, linked, with its source chip.
   A finding marked fixed dims and moves to the bottom of its severity group.
5. Desktop: a mini-TOC with "Tổng quan", "Tiêu chí", and one entry per severity group with counts.

## Severity colours

Critical `--crit`, high `--high`, medium `--med`, low `--low`; each chip is the word plus the
colour on its tint, never colour alone. Keep the page accent green or teal so it never reads as
a severity.

## Interaction

- Filters combine (severity and area) and persist in the URL hash, so a link the learner shares
  opens the same view; an empty result says so and offers "Bỏ lọc".
- "Copy as Markdown" on each finding copies title, severity, evidence, fix and the lesson link,
  ready for an issue tracker.
- "Đã sửa" ticks persist in `localStorage` per finding id; the summary strip counts fixed items
  separately.

## Traps

- Evidence paths stay as the review wrote them and break only after a `/` (insert `<wbr>`
  after each slash): `overflow-wrap: anywhere` alone splits file names mid-word in a table.
- A finding without a 200Lab lesson is labelled `own` or `external`, not left blank.
