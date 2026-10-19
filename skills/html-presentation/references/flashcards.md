Skill 200Lab «Trình bày kết quả AI Tutor thành file HTML: trang lộ trình, báo cáo review, flashcard, slide, diễn hoạt cơ chế» v1 · phần flashcards «Flashcards: own-words recall cards, flip, marks, drill the missed» — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài.

# Flashcards

The job: the learner recalls a lesson's key ideas without looking, finds out which ones did not
stick, and drills only those.

## Source

- Cards come from lessons you read with `get` in this conversation, usually during study help.
  When the learner asks for cards on a lesson you have not read and they can open, one `get` of
  that lesson is the exception the body allows. A lesson they cannot open gets no cards.
- Write each card in your own words from the lesson's key ideas: a recall prompt on the front,
  a short answer on the back. Never paste a lesson paragraph, a table or a code block.
- Quizzes stay on the platform. No multiple-choice cards and no worked scenario with a single
  right answer ("in this situation, which response is correct?"): that is a quiz question.
  Ask for the idea itself: what it is for, why, when, what it costs, what it does not cover.
- At most 20 cards per deck, one idea per card. The front never contains its answer.

## Data

```json
{
  "kind": "flashcards",
  "title": "Ôn bài: Idempotency key",
  "lede": "13 thẻ, mỗi thẻ một ý chính của bài",
  "builtOn": "2026-10-14",
  "lessons": [
    { "id": "l1", "title": "…", "course": "…", "url": "https://learn.200lab.io/courses/…/lessons/…" }
  ],
  "cards": [
    { "id": "c1", "lesson": "l1", "front": "Idempotency key giải quyết vấn đề gì?",
      "back": "Cho phép retry một thao tác có side effect mà side effect chỉ xảy ra một lần." }
  ]
}
```

Fronts at most 120 characters, backs at most 240; `code` spans allowed for names.

## Layout

1. Header: title, lede, the source lesson(s) linked with the `200Lab` chip, and a progress line:
   "Thẻ 4 / 13 · Nhớ rồi 6 · Chưa nhớ 2".
2. One card at a time, centred, at most 640 px wide and at least 260 px tall, the front in
   20 to 24 px type. The back shows the answer and, under a hairline, its lesson title linked
   with the `200Lab` chip. A small "Mặt trước" / "Mặt sau" label tells which side is up.
3. Under the card: "Chưa nhớ" and "Nhớ rồi" as two equal buttons (shown once the card is
   flipped), then previous / flip / next. On a phone the controls sit at the bottom within thumb
   reach, every target at least 44 px.
4. Below the controls, never above the card: "Trộn thẻ", "Chỉ ôn thẻ chưa nhớ (n)", "Làm lại
   từ đầu". Above the card they push the mark buttons below the fold on a phone.
5. End of deck: a summary card with the counts, a button to run the missed cards again, and the
   list of missed fronts each linked to its lesson.

## Interaction

- Flip on click or tap, Space or Enter; ← and → move; 1 marks "Chưa nhớ", 2 marks "Nhớ rồi" and
  moves on. Keys are ignored while focus is in a text field, and Space never also scrolls.
- The card is clickable, but the accessible control is the flip button: the back holds a link,
  so the card itself is not `role="button"`.
- The flip is a 3D `rotateY` of 200 to 250 ms on the card (its cause is the click); under
  reduced motion the faces swap with no rotation. Hide the back face with
  `backface-visibility: hidden` and give the card `aria-live="polite"` so the answer is read out.
- Marks persist in `localStorage` per deck and card id, with the current position; shuffle is a
  fresh order kept for the session, not a re-render on every move.
- Show a visible hint of the keys once, on desktop only ("Space: lật thẻ · ← →: chuyển thẻ").

## Traps

- Height jumps when the back is longer than the front: size the card to the longer face.
- A deck built from several lessons groups the progress by lesson in the summary, so the
  learner knows which lesson to reread.
- Print: every card as a two-column row, front and back side by side, no controls.
