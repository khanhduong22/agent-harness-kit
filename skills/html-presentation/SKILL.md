---
name: html-presentation
description: "Transform structured reviews, learning roadmaps, architecture consulting proposals, flashcards, slide decks, and step-by-step system mechanisms into a single self-contained interactive HTML file (dark/light mode, responsive 390px-1440px, JSON-driven rendering, zero external dependencies). Includes 7 specialized parts in references/: roadmap, course-map, consulting, review-report, flashcards, slides, and mechanism."
---

Skill 200Lab «Trình bày kết quả AI Tutor thành file HTML: trang lộ trình, báo cáo review, flashcard, slide, diễn hoạt cơ chế» v1 — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài. Parts: roadmap, course-map, consulting, review-report, flashcards, slides, mechanism.

# HTML presentation (200Lab)

Turns an answer you already gave the learner into one self-contained HTML file they keep: a
page, a report, flashcards, slides or an animated explainer. It presents; it adds no facts.
Build it from the tool output already in this conversation, with no new call to enrich it
(reads spend the learner's budget); flashcards are the one exception, see their part.
Not for a project the `ai_tutor` rules' "Lawful use only" excludes (attacking systems or accounts not the learner's, gambling, fraud or spam, content breaking Vietnamese law); for one, stop and decline as those rules say.

Write the copy in the learner's language; in Vietnamese use mình/bạn and "khóa", and keep
status and technical labels in English where the answer did.

## Pick the format by what the learner will do, then read exactly one part

| They will | Format | Part |
|---|---|---|
| follow a learning roadmap or tick off a checklist | page | `roadmap` |
| choose courses: recommendations, a knowledge map, lesson hits | page | `course-map` |
| decide on their project: options, an architecture, next steps | page | `consulting` |
| fix what a review or audit found | report | `review-report` |
| study and recall a lesson or topic | flashcards | `flashcards` |
| present it to a team: a design proposal, a review readout | slides | `slides` |
| understand how a mechanism works step by step | animated explainer | `mechanism` |

A mixed answer takes the part of its main job; the rest becomes one section of that file.

## Think before you build

- **One reader, one job.** The learner opens this later, often on a phone, sometimes to show a
  lead. Name the one thing they must get from it and make that the lede or first slide.
- **Answer first.** Above the fold at 390 px: title, the verdict or summary in one or two
  sentences, two to four headline facts. Detail follows in the order the reader acts on it.
- **Data, then render.** Put the content in one `<script type="application/json" id="page-data">`
  shaped as the part says, and render every list, count, total and filter from it. A number
  typed in prose that the data also holds will drift; compute it.
- **Never invent.** Course and lesson titles, URLs, prices, access states and minutes come from
  tool output in this conversation; a missing field is left out, never filled. No placeholder
  text, no `#` links, no stock images, no score the answer did not compute.
- **200Lab rules.** Every item carries a provenance chip: `200Lab`, `own` or `external`. Lessons
  appear as title + link; never paste lesson paragraphs or a quiz question into the file. The
  footer reads "Nguồn: 200Lab AI Tutor · dd/mm/yyyy" (the build day), then the ai_tutor rules'
  disclaimer in the learner's language: 200Lab gives the knowledge, applying it is the learner's call.

## Visual system

Not the AI look: no purple, indigo, pink or blue gradients, no neon on near-black, no glass blur
or glow, no rainbow accents, no gradient text, no emoji or sparkle icons as bullets or headings,
no decorative blobs. Instead: a warm neutral ramp, one accent, status colours only for status.

| Accent | Light | Dark | APCA Lc on page bg (light / dark) |
|---|---|---|---|
| Ink green (default) | `#1a6544` | `#9fe0bd` | 79 / 78 |
| Deep teal | `#0d5960` | `#98dbe1` | 82 / 77 |
| Ochre | `#7d5200` | `#f2cb82` | 78 / 77 |
| Brick | `#963722` | `#fcc6b6` | 79 / 79 |

One accent per file; with severity colours on screen use green or teal, since ochre and brick
read as high and critical. Body text at least Lc 75 (the neutrals give 98 light, 90 dark), muted
text at least Lc 70; never `#fff` on `#000`.

- Type: Be Vietnam Pro with a system fallback, both with Vietnamese diacritics; 16 px body,
  line-height 1.6, prose at most 72ch, headings 600 to 700, `tabular-nums` on figures.
- Surfaces: tonal steps, 1 px hairlines, radius 10, one soft shadow max; icons inline SVG `currentColor`.
- Pages and reports: one column on a phone; from 1024 px a sticky mini-TOC beside a content
  column of at most 1120 px. A table stacks into rows on a phone or scrolls inside its own box.

## Interaction and motion

- Interact only where it saves effort: filter chips, `details` sections, tabs, checkboxes saved
  in `localStorage` (one key per file, every access in try/catch), copy buttons
  (`navigator.clipboard`, falling back to a selected textarea and `execCommand('copy')` under
  `file://`), keyboard keys where the part names them, a mini-TOC marking the section in view.
- Motion has a cause: one staggered reveal on load (at most 8 items, 40 ms apart), a bar filling
  when its value changes, a tick drawing when checked, a count-up on at most three numbers.
  150 to 250 ms ease-out on `transform` and `opacity`. Hover changes colour only: cards never
  lift, scale or move. Nothing loops or pulses. The reveal starts from a class the script adds,
  so a script error never hides content.

## File contract

Keep this head and these tokens; add the component CSS the part needs.

```html
<!doctype html><html lang="vi"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark"><title>…</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;600;700&display=swap">
<script>try{const t=localStorage.getItem('theme');if(t)document.documentElement.dataset.theme=t}catch(e){}</script>
<style>
:root{--bg:#f7f6f3;--surface:#fff;--surface-2:#efede8;--line:#dcd9d2;--text:#1c1f1d;--muted:#53585a;
 --accent:#1a6544;--on-accent:#fff;--crit:#b3261e;--high:#9c4400;--med:#7a5c00;--low:#4b5563;
 --font:"Be Vietnam Pro",system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#141615;--surface:#1c1f1d;
 --surface-2:#252927;--line:#363b39;--text:#e3e6e7;--muted:#c0c6c3;--accent:#9fe0bd;--on-accent:#141615;
 --crit:#ffbdb5;--high:#f9c08a;--med:#ecd68c;--low:#c3cad3}}
:root[data-theme=dark]{/* the same dark values */}
html{scroll-padding-top:72px}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 var(--font)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
@media print{.toc,.toolbar,button{display:none!important}body{background:#fff;color:#000}}
</style></head>
```

A theme toggle stores the choice and names the next theme in its `aria-label`. Chip tints are
`color-mix(in srgb, var(--x) 14%, var(--surface))`.

## Deliver

- With files and a shell: save to `docs/200lab/<topic-slug>.html` in the learner's workspace
  (ASCII kebab-case; a rebuild overwrites it), open it, and tell the learner the path.
- In a chat client: one HTML artifact with the same content.

## Done-check

- `meta charset` and viewport present; Vietnamese renders without mojibake; no console errors; late fonts shift nothing; the file works opened by double-click.
- No horizontal scroll at 360 px; light and dark both readable; print shows every section.
- Every link comes from tool output and opens in a new tab with `rel="noopener"`.
- Anchors land below the sticky header; focus is visible; every `button` has a `type`, and an
  icon-only one an `aria-label`; touch targets at least 44 px.
- Figures use tabular numbers; dates read dd/mm/yyyy in Vietnamese; prices use `vi-VN` VND.
- Counts and totals match the data; nothing in the file was not in the answer.


## Local Reference Parts

All 7 format specifications are bundled locally in `references/`:
- `references/roadmap.md`
- `references/course-map.md`
- `references/consulting.md`
- `references/review-report.md`
- `references/flashcards.md`
- `references/slides.md`
- `references/mechanism.md`
