# Motion Rules Reference (200Lab Motion-UI)

> Direct source: [motion-ui.200lab.io/#agents](https://motion-ui.200lab.io/#agents)

Decide first whether the animation should exist.
- Animate to give feedback, to show where something came from or went, or to mark a state change. Otherwise do not animate.
- Do not animate actions a person repeats all day or triggers from the keyboard. They must feel instant.

## Timing
- Press and hover feedback: 100 to 150 ms.
- Small elements entering (tooltip, menu, toast): 150 to 250 ms.
- Dialogs and panels: 200 to 300 ms. Large surfaces: 300 to 400 ms.
- Exits are shorter than enters: about two thirds of the enter.
- Respond to a press within 100 ms, before any network result.

## Easing
- Entering, and anything the person started: ease-out. Default `cubic-bezier(0.23, 1, 0.32, 1)`.
- Leaving the screen: ease-in. Moving within the screen: ease-in-out.
- Linear only for colour, opacity or constant rotation.
- Use a spring for gestures and for anything that can be interrupted. Keep bounce between 0 and 0.3.
- Never overshoot opacity or colour.

## Space
- Scale from 0.9 or above, never from 0.
- Set transform-origin to the element that triggered the change.
- Stagger list items 20 to 60 ms apart and keep the whole sequence under 500 ms.

## Performance
- Animate `transform`, `opacity`, `filter` and `clip-path`. Do not animate `width`, `height`, `top`, `left` or `margin`.
- For auto height, animate `grid-template-rows` from `0fr` to `1fr`.
- No `transition: all`. Use `will-change` only while an animation runs.
- Never start above-the-fold content at `opacity: 0`: it delays the largest paint.

## Accessibility
- Under `prefers-reduced-motion: reduce`, replace movement with a short fade or an instant change. Keep the state change visible.
- Anything that moves on its own for more than 5 seconds needs a pause control.
- Motion is never the only signal. Pair it with text, an icon or colour.
