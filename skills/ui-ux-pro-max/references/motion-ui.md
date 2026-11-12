# Motion UI & Micro-Interaction Specifications

> Sourced from [motion-ui.200lab.io](https://motion-ui.200lab.io/#agents), Apple HIG fluid animations, Material 3 Motion, and production component libraries (Sonner, Radix, DaisyUI).

---

## 1. Decision Framework: When to Animate

Before adding any motion, verify against the **3 Invariant Triggers**:
1. **Feedback**: Confirms user input was received (press, toggle, success, error).
2. **Spatial Continuity**: Shows where an element originated or exited (dialog, sheet, menu).
3. **State Mutation**: Highlights a meaningful change in data or layout (stagger, counter, progress).

> [!IMPORTANT]
> **Zero-Motion Rule**: Never animate actions a user repeats frequently throughout the day or initiates via keyboard shortcuts (code editor typing, tab switches, terminal commands). They must feel **instant (0ms)**.

---

## 2. Timing Standards Matrix

| Element / Interaction | Enter Duration | Exit Duration | Easing Curve | Target Properties |
|---|---|---|---|---|
| **Press & Hover Feedback** | 100–120ms | 150–200ms (or spring) | `cubic-bezier(0.23, 1, 0.32, 1)` | `transform: scale(0.97)` |
| **Small Overlays** (Tooltip, Toast, Badge) | 150–250ms | 100–150ms | `cubic-bezier(0.23, 1, 0.32, 1)` | `opacity`, `translateY` |
| **Dialogs, Drawers & Popovers** | 200–300ms | 150–200ms | `cubic-bezier(0.16, 1, 0.3, 1)` | `scale(0.95→1)`, `opacity` |
| **Large Surfaces / Sheets / Pages** | 300–400ms | 200–250ms | `cubic-bezier(0.32, 0.72, 0, 1)` | `translateY`, `clip-path` |
| **List Stagger Sequences** | 25–50ms interval | — | `ease-out` (cap: ≤ 500ms total) | `opacity`, `translateY(8px→0)` |

### Golden Timing Rules:
- **Exits Are Faster**: Exit durations must be approximately **two-thirds ($\approx 66\%$)** of enter durations. People don't wait for things to leave.
- **Touch Responsiveness**: Touch/press feedback must trigger within **$< 100\text{ms}$**, well before any network response resolves.

---

## 3. Easing & Spring Mathematical Constants

```css
:root {
  /* Enters & User-Triggered Movements (Ease-Out) */
  --ease-enter: cubic-bezier(0.23, 1, 0.32, 1);
  --ease-enter-snappy: cubic-bezier(0.16, 1, 0.3, 1);

  /* Exits (Ease-In) */
  --ease-exit: cubic-bezier(0.4, 0, 1, 1);

  /* Internal Screen Repositioning (Ease-In-Out) */
  --ease-move: cubic-bezier(0.65, 0, 0.35, 1);

  /* Standard Spring for Feedback (Bounce 0.3, Overshoot 4.6%) */
  --spring-bounce: linear(
    0, 0.028, 0.1, 0.199, 0.311, 0.427, 0.539, 0.642, 0.734, 0.813,
    0.878, 0.93, 0.97, 1, 1.021, 1.035, 1.043, 1.046, 1.045, 1.043,
    1.039, 1.034, 1.028, 1.023, 1.018, 1.014, 1.01, 1.007, 1.004, 1.002,
    1, 0.999, 0.999, 0.998, 0.998, 0.998, 0.998, 0.998, 0.998, 1
  );

  /* Subtle Spring for Tabs/Pills (Bounce 0.15, Overshoot 0.6%) */
  --spring-subtle: linear(
    0, 0.036, 0.121, 0.231, 0.349, 0.464, 0.57, 0.663, 0.742, 0.807,
    0.86, 0.901, 0.933, 0.957, 0.974, 0.986, 0.995, 1, 1.004, 1.005,
    1.006, 1.006, 1.006, 1.005, 1.004, 1.004, 1.003, 1.002, 1
  );
}
```

### Spring Rules:
- Use springs for **gestures** (drag, swipe) and **interruptible interactions**.
- Keep bounce between **0.0 and 0.3**.
- **Never overshoot opacity or color**: Opacity > 1.0 or non-physical colors cause visual flashing.

---

## 4. Performance & CSS Engine Rules

1. **Composite-Only Properties**: Animate ONLY `transform`, `opacity`, `filter`, and `clip-path`.
2. **Never Animate Layout Properties**: NEVER animate `width`, `height`, `top`, `left`, `right`, `bottom`, or `margin`.
3. **Smooth Auto-Height**: Animate `grid-template-rows` from `0fr` to `1fr` instead of JS height measuring:
   ```css
   .accordion-content {
     display: grid;
     grid-template-rows: 0fr;
     transition: grid-template-rows 300ms var(--ease-enter);
   }
   .accordion-content[data-open="true"] {
     grid-template-rows: 1fr;
   }
   .accordion-inner { overflow: hidden; }
   ```
4. **No Blanket `transition: all`**: Explicitly declare transitioned properties (`transition: transform 150ms, opacity 150ms`).
5. **Protect Core Web Vitals (LCP)**: Never start above-the-fold content at `opacity: 0` — this delays Largest Contentful Paint.

---

## 5. Accessibility & Reduced Motion (WCAG 2.1)

Every animated component MUST include a `@media (prefers-reduced-motion: reduce)` fallback:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

- **Graceful Degradation**: Replace spatial movements (slide, bounce) with an instant cut or a quick opacity fade ($\le 100\text{ms}$).
- **State Preservation**: Ensure the final state (open, active, checked) is clearly visible even with zero animation.
- **Autoplay Limits**: Any continuous movement running $> 5\text{s}$ requires a user pause control.
- **Multi-Modal Signaling**: Never convey state solely through motion; always pair with text, color, or icon changes.

---

## 6. The 18 Canonical Patterns

### Feedback Patterns
1. **Heart / Like Pop ("Pop on yes")**:
   - `aria-pressed="true"` toggles a 630ms spring pop (`scale(0.6→1)` with 4.6% overshoot) + 6-particle radial burst over 400ms.
2. **Button Press ("Sink, then spring")**:
   - Press down: `scale(0.97)` inside 120ms (`cubic-bezier(0.23, 1, 0.32, 1)`).
   - Release: Spring return over 550ms `var(--spring-bounce)`.
3. **Success Checkmark ("Draw the win")**:
   - Circle outline: 300ms `cubic-bezier(0.65, 0, 0.35, 1)` stroke-dashoffset (`pathLength="1"`).
   - Checkmark tick: 170ms `cubic-bezier(0.23, 1, 0.32, 1)` after 300ms delay. Total: 470ms.
4. **Error Shake ("Shake, don't shout")**:
   - 400ms, 3 decaying horizontal swings ($\pm 6\text{px} \to \pm 4\text{px} \to 0$). Always pair with visible inline error text.

### Control Patterns
5. **Switch Toggle ("Stretch, then glide")**:
   - Thumb travel: 150ms `cubic-bezier(0.4, 0, 0.2, 1)`. Press stretch: 100ms `scaleX(1.25)`.
6. **Tab Segmented Control ("Slide the pill, don't swap")**:
   - Single shared sliding background pill moving between tabs using 300ms spring (`var(--spring-subtle)`).
7. **Accordion Expand ("Fast, then slow")**:
   - Animate `grid-template-rows: 0fr → 1fr` over 300ms `cubic-bezier(0.23, 1, 0.32, 1)`. Zero layout recalculation.
8. **Menu Icon Morph ("Meet, then turn")**:
   - 3-bar hamburger to X: 150ms bars meet in center + 150ms rotate 45° (`cubic-bezier(0.65, 0, 0.35, 1)`). Reverse on close.

### Overlay Patterns
9. **Tooltip Delay ("Wait once, then follow")**:
   - Open delay: 600ms hover wait. Skip window: 300ms (instant switch between adjacent tooltips). Enter: 150ms `scale(0.95→1)` + fade. Exit: 100ms.
10. **Toast Stack ("Slide in, step back")**:
    - New toast: `translateY(100% → 0)` over 400ms ease. Preceding toasts: `translateY(-10px)` and `scale(-0.05)` per stack depth. Exit: 200ms.
11. **Dropdown / Dialog Origin ("Grow, don't pop")**:
    - Anchor `transform-origin` to trigger coordinate. Scale $0.95 \to 1.0$ over 220ms ease-out. Exit: 150ms. Never scale from 0.

### Data & Loading Patterns
12. **Rolling Number Counter ("Roll, don't jump")**:
    - `font-variant-numeric: tabular-nums`. 500ms spring, digits staggered 60ms apart.
13. **Page Progress Bar ("Crawl, then finish")**:
    - Jump to 8% in 80ms. Non-linear trickle every 200ms, capped at 99.4% until network completion. Finish: 200ms to 100%, 150ms fade-out.
14. **Skeleton Shimmer ("Shimmer, then settle in place")**:
    - 1.5s `ease-in-out` infinite gradient sweep. Settle: fade skeleton into real content over 200ms.
15. **List Item Stagger ("Stagger, then stop")**:
    - 30–50ms interval between items. 250ms each (`translateY(8px→0)` + fade). Cap delay at 5 items ($\le 250\text{ms}$ total delay).

### Gesture Patterns
16. **Bottom Sheet Snap ("Follow, then snap")**:
    - Drag: 1:1 finger tracking. Release settle: 500ms `cubic-bezier(0.32, 0.72, 0, 1)`. Flick threshold: 0.4 px/ms to snap to next detent.
17. **Swipe to Dismiss ("Past the line, let go")**:
    - Threshold: 45px or 0.11 px/ms velocity. Exit: 200ms ease-out. Container gap collapse: 200ms transition after item exits.
18. **Rubber Band Overscroll ("Resist the pull")**:
    - Resistance coefficient $c = 0.55$ (pulling 100px moves content 35px). Return: 590ms critically damped spring (zero bounce).

---

## 7. 200Lab MCP Integration

When the `200lab` MCP server is connected in your workspace, agents can query the live database of 726+ verified records and 528 patterns:

```json
// Find pattern by interaction intent:
search({
  "query": "toast slide in",
  "types": ["motion"]
})

// Read full record with observed source values:
get({
  "entity": "motion",
  "slug": "sonner-toast-enter"
})
```
