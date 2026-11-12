---
name: motion-ui
description: "Motion UI and micro-interaction specifications: timing, easing curves, spring parameters, CSS/Tailwind patterns, and accessibility fallbacks for coding agents."
---

# Motion UI: Production Motion Specs for Coding Agents

Sourced interface motion specifications with exact durations, easing curves, springs, and accessibility fallbacks. Eliminates vague "make it smooth" guesses by giving agents verifiable numbers derived from top design systems (Apple HIG, Material 3, Tailwind, Radix, Sonner, DaisyUI).

---

## 1. The Core Decision Framework

Before adding any motion, verify against the **3 Invariant Triggers**:
1. **Feedback**: Confirms user input received (press, toggle, success, error).
2. **Spatial Continuity**: Shows where an element originated or exited (dialog, sheet, menu).
3. **State Change**: Highlights meaningful mutation in data or layout (stagger, counter, progress).

> [!IMPORTANT]
> **Zero-Motion Rule**: Never animate actions a person repeats frequently throughout the day or initiates via keyboard shortcuts (code editor typing, tab switches, terminal commands). They must feel **instant (0ms)**.

---

## 2. Timing Standards Matrix

| Element / Interaction | Enter Duration | Exit Duration | Easing Curve | Target Properties |
|---|---|---|---|---|
| **Press & Hover Feedback** | 100–120ms | 150–200ms (or spring) | `cubic-bezier(0.23, 1, 0.32, 1)` | `transform: scale(0.97)` |
| **Small Overlays** (Tooltip, Toast, Badge) | 150–250ms | 100–150ms | `cubic-bezier(0.23, 1, 0.32, 1)` | `opacity`, `translateY` |
| **Dialogs, Drawers & Popovers** | 200–300ms | 150–200ms | `cubic-bezier(0.16, 1, 0.3, 1)` | `scale(0.95→1)`, `opacity` |
| **Large Surfaces / Sheets / Page** | 300–400ms | 200–250ms | `cubic-bezier(0.32, 0.72, 0, 1)` | `translateY`, `clip-path` |
| **List Stagger Sequences** | 25–50ms interval | — | `ease-out` (cap: ≤ 500ms total) | `opacity`, `translateY(8px→0)` |

### Golden Timing Rules:
- **Exits Are Faster**: Exit durations must be approximately **two-thirds ($\approx 66\%$)** of enter durations. People don't wait for things to leave.
- **Touch Responsiveness**: Touch/press feedback must trigger within **$< 100\text{ms}$**, well before any network response resolves.

---

## 3. Easing & Spring Curves

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
- Use springs for **gestures** (drag, swipe) and **interruptible user interactions**.
- Keep bounce between **0.0 and 0.3**.
- **Never overshoot opacity or color**: Opacity > 1.0 or non-physical colors cause visual flashing.

---

## 4. Performance & Hardware Acceleration

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

## 6. The 18 Canonical Patterns Quick Index

| Category | Pattern | Key Spec | Implementation File |
|---|---|---|---|
| **Feedback** | 1. Heart / Like Pop | 630ms spring pop (bounce 0.3) + 400ms burst | `references/patterns.md#1-heart-like-pop` |
| | 2. Button Press | Press: 120ms scale(0.97); Release: 550ms spring | `references/patterns.md#2-button-press` |
| | 3. Success Checkmark | Ring 300ms + tick 170ms (`pathLength="1"`) | `references/patterns.md#3-success-checkmark` |
| | 4. Error Shake | 400ms, 3 swings decaying from 6px | `references/patterns.md#4-error-shake` |
| **Controls** | 5. Switch Toggle | Thumb travel 150ms + 100ms stretch (1.25x) | `references/patterns.md#5-switch-toggle` |
| | 6. Tab Segmented Control | 300ms shared pill spring (bounce 0.15) | `references/patterns.md#6-tab-segmented-control` |
| | 7. Accordion Expand | 300ms `grid-template-rows: 0fr→1fr` | `references/patterns.md#7-accordion-expand` |
| | 8. Menu Hamburger to X | 150ms meet + 150ms rotate 45° | `references/patterns.md#8-menu-icon-morph` |
| **Overlays** | 9. Tooltip Delay | 600ms hover delay, 300ms skip window | `references/patterns.md#9-tooltip-delay` |
| | 10. Toast Stack (Sonner) | 400ms slide up, scale -0.05 on stack | `references/patterns.md#10-toast-stack` |
| | 11. Dropdown / Dialog Origin | Scale 0.95→1 from trigger origin over 220ms | `references/patterns.md#11-dropdown-dialog-origin` |
| **Data/Load** | 12. Rolling Numbers | 500ms spring, 60ms digit stagger | `references/patterns.md#12-rolling-numbers` |
| | 13. Page Progress Bar | Start 8% at 80ms, trickle cap 99.4% | `references/patterns.md#13-page-progress-bar` |
| | 14. Skeleton Shimmer | 1.5s linear sweep, 200ms content settle | `references/patterns.md#14-skeleton-shimmer` |
| | 15. List Item Stagger | 30–50ms apart, cap at 5 steps (≤ 500ms) | `references/patterns.md#15-list-item-stagger` |
| **Gestures** | 16. Bottom Sheet Snap | 1:1 drag, 500ms settle, flick threshold 0.4px/ms | `references/patterns.md#16-bottom-sheet-snap` |
| | 17. Swipe to Dismiss | 45px / 0.11px/ms threshold, 200ms gap collapse | `references/patterns.md#17-swipe-to-dismiss` |
| | 18. Rubber Band Overscroll | Resistance $c=0.55$, 590ms no-bounce return | `references/patterns.md#18-rubber-band-overscroll` |

*For complete CSS, Tailwind utilities, and React/Framer Motion code snippets for each pattern, consult [patterns.md](./references/patterns.md).*

---

## 7. 200Lab MCP Integration

When the `200lab` MCP server is connected, search the full library of 726+ verified motion records and 528 patterns:

```json
// Find motion specifications by interaction intent:
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

See [mcp-integration.md](./references/mcp-integration.md) for full MCP workflow examples and prompt templates.
