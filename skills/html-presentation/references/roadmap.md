Skill 200Lab «Trình bày kết quả AI Tutor thành file HTML: trang lộ trình, báo cáo review, flashcard, slide, diễn hoạt cơ chế» v1 · phần roadmap «Roadmap or checklist page: data shape, layout, progress» — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài.

# Roadmap or checklist page

The job: the learner knows what to study this week and sees how far they are. A checklist is the
same page with one group instead of weeks.

## Data

```json
{
  "kind": "roadmap",
  "title": "Lộ trình 8 tuần: tự viết agent bằng TypeScript",
  "lede": "Tuần này: …",
  "builtOn": "2026-10-14",
  "profile": { "goal": "…", "weeklyHours": 6, "deadline": "2026-12-20" },
  "catalogFit": "strong",
  "gaps": ["prompt injection"],
  "courses": [
    { "slug": "…", "title": "…", "url": "https://200lab.io/courses/…",
      "access": "owned | free_claim | paid | not_on_sale", "price": 1290000,
      "freeOpening": { "title": "…", "url": "https://learn.200lab.io/courses/…/lessons/…" },
      "usedFor": "Tuần 1–3: nền tảng harness" }
  ],
  "weeks": [
    { "id": "w1", "title": "Tuần 1", "focus": "…",
      "steps": [
        { "id": "w1-s1", "source": "200Lab", "title": "…", "course": "<course slug>",
          "lessons": [{ "title": "…", "url": "…", "minutes": 15 }], "hours": 1 },
        { "id": "w1-s2", "source": "own", "title": "…", "hours": 2 },
        { "id": "w1-s3", "source": "external", "title": "…", "url": "https://…", "hours": 1 }
      ],
      "checkpoint": { "id": "w1-cp", "text": "Một script gửi prompt và in kết quả" } }
  ]
}
```

- A week's hours are the sum of its steps; total hours, the 200Lab / own / external split and
  the number of weeks are computed, never typed.
- A week whose sum exceeds `profile.weeklyHours` gets a visible note in that week; do not move
  steps around, the roadmap is the answer's.
- A checklist uses `"kind": "checklist"` and `groups` (title + items) in place of `weeks`.

## Layout

1. Header: title, lede, then a facts row: weeks, total hours, hours per week, deadline as
   dd/mm/yyyy. Under it one progress bar: checkpoints done out of total.
2. A gaps note when `catalogFit` is `partial` or `none` or `gaps` is not empty: one line naming
   what 200Lab does not cover and how the roadmap fills it.
3. Courses: one row each, three columns `Khóa` · `Trạng thái` · `Dùng cho` (stacked into a small
   card per course on a phone). The access state in the learner's words:
   - `owned`: "Bạn đã có khóa".
   - `free_claim`: "Miễn phí: bấm Học miễn phí", linked to the course page.
   - `paid`: the free opening lesson first ("Học thử: {title}"), then the price and the course
     page, in that order.
   - `not_on_sale`: "Chưa mở bán".
4. Weeks as a vertical timeline: a rail with one node per week; the node fills with the accent
   when the week's checkpoint is ticked. Each week is a card: heading "Tuần 1 · 5 giờ" plus its
   focus, then one row per step: a checkbox, the source chip, the title with its lesson links
   (lesson title linked, minutes after it in muted text), the hours right-aligned. The checkpoint
   is the last row, set apart by a top hairline and the label `Checkpoint`.
5. Desktop: a mini-TOC listing the weeks, each with a small done tick, and the progress bar
   repeated at its top.

## Interaction

- Checkboxes on steps and checkpoints, saved under one key (`roadmap:<title slug>`); the progress
  bar and the timeline nodes update at once.
- The current week is the first with an unticked checkpoint: open it and mark it "Đang học";
  earlier finished weeks collapse to their heading, later ones stay open.
- A toolbar with "Ẩn bước đã xong" and "Mở tất cả" toggles, and a reset that asks for
  confirmation in the page (no `confirm()` dialog).
- Each week heading has a copy-link button for its anchor.

## Traps

- Lesson rows carry the title, minutes and link only; a `requires_course` lesson is its title
  with the course name, linked to the course page, never described.
- A price shows only for `paid`, formatted with `Intl.NumberFormat('vi-VN', { style: 'currency',
  currency: 'VND' })`.
- On a phone a step's first line holds the source chip and the hours, the title below it at full
  width; a title beside both wraps into a narrow strip and pushes the hours under it.
- Below 640 px the timeline rail and nodes go away (they cost 40 px of a 360 px column); the
  week card carries its state.
