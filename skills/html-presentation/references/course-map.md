Skill 200Lab «Trình bày kết quả AI Tutor thành file HTML: trang lộ trình, báo cáo review, flashcard, slide, diễn hoạt cơ chế» v1 · phần course-map «Course map page: course cards, access states, lesson hits» — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài.

# Course map page

The job: the learner sees which 200Lab courses fit their goal, what each costs them to start, and
which lessons answer their question, in the order of the answer.

## Data

```json
{
  "kind": "course-map",
  "title": "Khóa 200Lab cho mục tiêu: …",
  "lede": "…",
  "builtOn": "2026-10-14",
  "catalogFit": "strong | partial | none",
  "gaps": ["…"],
  "courses": [
    { "slug": "…", "title": "…", "url": "https://200lab.io/courses/…",
      "access": "owned | free_claim | paid | not_on_sale", "price": 1290000,
      "totalMinutes": 640, "freeOpening": { "title": "…", "url": "…" },
      "why": "Vì sao khóa này hợp với bạn, một hoặc hai câu",
      "hits": [
        { "title": "…", "url": "https://learn.200lab.io/courses/…/lessons/…", "minutes": 15,
          "access": "open | requires_course", "summary": "…", "query": "…" }
      ] }
  ],
  "otherCourses": [{ "slug": "…", "title": "…", "url": "…", "access": "…" }]
}
```

- Keep the answer's order of courses and hits; do not re-rank.
- `summary` is the hit summary from the tool output, only on an `open` hit; a `requires_course`
  hit has none.
- `why` is the reason you gave in the answer, labelled `own`; leave it out if the answer gave none.

## Layout

1. Header: title, lede, a facts row (courses that fit, lessons matched, how many you can open
   now). A gaps note under it when `catalogFit` is `partial` or `none`.
2. Filter chips by access: "Tất cả", "Đã có", "Miễn phí", "Có phí", "Chưa mở bán", each with its
   count; hidden chips for states no course has.
3. Course cards, one column on a phone, two from 900 px. A card holds:
   - the title linked to `url`, the `200Lab` chip, total reading time in hours;
   - an access line with one clear next action: "Vào học" (owned), "Học miễn phí" (free_claim),
     "Học thử bài mở đầu" then the price (paid), "Chưa mở bán" (not_on_sale) with no button;
   - `why` as one or two lines;
   - its lesson hits as a compact list: title linked, minutes, a lock glyph with
     "Cần khóa" for `requires_course`; an `open` hit's summary sits in a collapsible line under it.
4. "Khóa khác của 200Lab": `otherCourses` as a plain list of linked titles with their access,
   collapsed by default.

## Traps

- The next action and the price never compete: one primary button per card, the price as text
  beside it.
- A `requires_course` lesson is its title only; never write what it teaches.
- Do not show a match score or similarity number; the order already carries it.
