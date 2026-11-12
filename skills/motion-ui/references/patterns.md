# 18 Canonical Motion Patterns Reference

Detailed timing, easing, keyframes, and implementation snippets for modern web stacks (CSS / Tailwind / React / Framer Motion).

---

## 1. Heart / Like Pop ("Pop on yes")
- **Category**: Feedback
- **Sourced Values**: Pop 400–630ms spring (bounce: 0.3, overshoot: 4.6%), 6 burst dots 400ms.
- **Accessibility**: Under reduced motion, omit scale pop and burst; change color instantly.

```css
.m-like[aria-pressed="true"] svg {
  fill: var(--color-danger, #ff8f85);
  stroke: var(--color-danger, #ff8f85);
  animation: m-pop 630ms linear(
    0, 0.022, 0.078, 0.157, 0.251, 0.35, 0.45, 0.546, 0.636, 0.717,
    0.788, 0.849, 0.9, 0.942, 0.975, 1, 1.019, 1.032, 1.04, 1.045,
    1.046, 1.045, 1.043, 1.039, 1.035, 1.03, 1.026, 1.021, 1.017, 1.013,
    1.01, 1.007, 1.005, 1.003, 1.001, 1, 0.999, 0.999, 0.998, 0.998, 0.998, 1
  );
}
@keyframes m-pop { from { transform: scale(0.6); } }

.m-like-burst i {
  position: absolute; left: 50%; top: 50%; width: 6px; height: 6px; margin: -3px;
  border-radius: 50%; background: var(--color-danger, #ff8f85);
  rotate: var(--angle); opacity: 0;
}
.m-like[aria-pressed="true"] .m-like-burst i {
  animation: m-burst 400ms cubic-bezier(0.23, 1, 0.32, 1);
}
@keyframes m-burst {
  from { opacity: 1; transform: translateY(-10px) scale(1); }
  to { opacity: 0; transform: translateY(-26px) scale(0.4); }
}
```

---

## 2. Button Press ("Sink, then spring")
- **Category**: Feedback
- **Sourced Values**: Press inside 120ms to `scale(0.97)`, release springs back over 550ms with 4.6% overshoot.

```css
.m-press {
  transform: scale(1);
  transition: transform 550ms linear(
    0, 0.028, 0.1, 0.199, 0.311, 0.427, 0.539, 0.642, 0.734, 0.813,
    0.878, 0.93, 0.97, 1, 1.021, 1.035, 1.043, 1.046, 1.045, 1.043,
    1.039, 1.034, 1.028, 1.023, 1.018, 1.014, 1.01, 1.007, 1.004, 1.002, 1
  );
}
.m-press:active, .m-press[data-pressed="true"] {
  transform: scale(0.97);
  transition: transform 120ms cubic-bezier(0.23, 1, 0.32, 1);
}
```

---

## 3. Success Checkmark ("Draw the win")
- **Category**: Feedback
- **Sourced Values**: Ring stroke draws in 300ms (`cubic-bezier(0.65, 0, 0.35, 1)`), tick path starts after 300ms and draws in 170ms (`cubic-bezier(0.23, 1, 0.32, 1)`). Total: 470ms.

```css
.m-check circle, .m-check path {
  stroke-dasharray: 1; stroke-dashoffset: 1; opacity: 0;
}
.m-check circle { transform: rotate(-90deg); transform-origin: center; }
.m-check.is-done circle {
  animation: m-draw 300ms cubic-bezier(0.65, 0, 0.35, 1) forwards;
}
.m-check.is-done path {
  animation: m-draw 170ms cubic-bezier(0.23, 1, 0.32, 1) 300ms forwards;
}
@keyframes m-draw {
  from { opacity: 1; }
  to { opacity: 1; stroke-dashoffset: 0; }
}
```

---

## 4. Error Shake ("Shake, don't shout")
- **Category**: Feedback
- **Sourced Values**: Amplitude $\pm 6\text{px}$, 3 decaying swings over 400ms. Always accompany with visible text error.

```css
.m-shake.is-error {
  animation: m-shake-anim 400ms cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
}
@keyframes m-shake-anim {
  10%, 90% { transform: translateX(-6px); }
  20%, 80% { transform: translateX(6px); }
  30%, 50%, 70% { transform: translateX(-4px); }
  40%, 60% { transform: translateX(4px); }
  100% { transform: translateX(0); }
}
```

---

## 5. Switch Toggle ("Stretch, then glide")
- **Category**: Controls
- **Sourced Values**: Thumb travel 150ms `cubic-bezier(0.4, 0, 0.2, 1)`. Stretch $1.25\times$ on press (100ms).

```css
.m-switch-thumb {
  width: 20px; height: 20px; border-radius: 9999px;
  transform: translateX(0) scaleX(1);
  transition: transform 150ms cubic-bezier(0.4, 0, 0.2, 1);
}
.m-switch:active .m-switch-thumb {
  transform: scaleX(1.25);
  transition: transform 100ms cubic-bezier(0.23, 1, 0.32, 1);
}
.m-switch[aria-checked="true"] .m-switch-thumb {
  transform: translateX(20px) scaleX(1);
}
```

---

## 6. Tab Segmented Control ("Slide the pill, don't swap")
- **Category**: Controls
- **Sourced Values**: 1 shared sliding background pill moving across buttons with spring 300ms (bounce 0.15, overshoot 0.6%).

```css
.m-pill {
  transition: transform 300ms var(--spring-subtle), width 300ms var(--spring-subtle);
}
```

---

## 7. Accordion Expand ("Fast, then slow")
- **Category**: Controls
- **Sourced Values**: `grid-template-rows: 0fr` to `1fr` over 300ms `cubic-bezier(0.23, 1, 0.32, 1)`. Zero layout recalculation.

```css
.m-accordion-panel {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 300ms cubic-bezier(0.23, 1, 0.32, 1);
}
.m-accordion-panel[data-state="open"] {
  grid-template-rows: 1fr;
}
.m-accordion-content { overflow: hidden; }
```

---

## 8. Menu Icon Morph ("Meet, then turn")
- **Category**: Controls
- **Sourced Values**: 3-bar hamburger to X. 150ms translate bars to center + 150ms rotate 45°. Total: 300ms `cubic-bezier(0.65, 0, 0.35, 1)`. Reverse on close.

```css
.m-bar { transition: transform 150ms cubic-bezier(0.65, 0, 0.35, 1); }
.m-menu[aria-expanded="true"] .m-bar-top {
  transform: translateY(6px) rotate(45deg);
}
.m-menu[aria-expanded="true"] .m-bar-mid { opacity: 0; }
.m-menu[aria-expanded="true"] .m-bar-bot {
  transform: translateY(-6px) rotate(-45deg);
}
```

---

## 9. Tooltip Delay ("Wait once, then follow")
- **Category**: Overlays
- **Sourced Values**: 600ms hover delay. Enter 150ms fade + scale(0.95→1). Skip window: 300ms between adjacent tooltips. Exit: 100ms.

```css
.m-tooltip {
  opacity: 0; transform: scale(0.95);
  transition: opacity 100ms ease-in, transform 100ms ease-in;
}
.m-tooltip[data-state="visible"] {
  opacity: 1; transform: scale(1);
  transition: opacity 150ms cubic-bezier(0.23, 1, 0.32, 1),
              transform 150ms cubic-bezier(0.23, 1, 0.32, 1);
}
```

---

## 10. Toast Stack ("Slide in, step back")
- **Category**: Overlays (Sonner style)
- **Sourced Values**: New toast: `translateY(100% → 0)` over 400ms ease. Preceding toasts: `translateY(-10px)` and `scale(-0.05)` per stack depth. Exit: 200ms.

```css
@keyframes toast-enter {
  from { transform: translateY(100%); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
.m-toast {
  animation: toast-enter 400ms cubic-bezier(0.23, 1, 0.32, 1) both;
}
.m-toast[data-index="1"] { transform: translateY(-10px) scale(0.95); opacity: 0.8; }
.m-toast[data-index="2"] { transform: translateY(-20px) scale(0.90); opacity: 0.6; }
```

---

## 11. Dropdown / Dialog Origin ("Grow, don't pop")
- **Category**: Overlays
- **Sourced Values**: Origin anchored at trigger coordinate. Scale 0.95 to 1.0 over 220ms ease-out. Exit: 150ms.

```css
.m-dialog {
  transform-origin: var(--trigger-x, center) var(--trigger-y, center);
  animation: dialog-enter 220ms cubic-bezier(0.16, 1, 0.3, 1) both;
}
@keyframes dialog-enter {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}
```

---

## 12. Rolling Number Counter ("Roll, don't jump")
- **Category**: Data & Loading
- **Sourced Values**: `font-variant-numeric: tabular-nums`. 500ms spring (bounce 0.15). Stagger digits 60ms apart.

```css
.m-rolling-digit {
  display: inline-block;
  font-variant-numeric: tabular-nums;
  transition: transform 500ms var(--spring-subtle);
  transition-delay: calc(var(--digit-index) * 60ms);
}
```

---

## 13. Page Progress Bar ("Crawl, then finish")
- **Category**: Data & Loading
- **Sourced Values**: Jump to 8% at 80ms. Trickle step every 200ms. Cap at 99.4% until network completion. Finish: 200ms to 100%, then 150ms fade-out.

```css
.m-progress-bar {
  height: 2px;
  background: var(--color-accent);
  transition: width 200ms cubic-bezier(0.23, 1, 0.32, 1), opacity 150ms ease-out;
}
```

---

## 14. Skeleton Shimmer ("Shimmer, then settle in place")
- **Category**: Data & Loading
- **Sourced Values**: Sweep cycle 1.5s ease-in-out infinite. Content reveal: fade out skeleton into real content over 200ms.

```css
.m-skeleton {
  background: linear-gradient(
    90deg,
    var(--color-surface-2) 0%,
    var(--color-surface-3) 50%,
    var(--color-surface-2) 100%
  );
  background-size: 200% 100%;
  animation: m-shimmer 1.5s ease-in-out infinite;
}
@keyframes m-shimmer {
  from { background-position: 200% 0; }
  to { background-position: -200% 0; }
}
```

---

## 15. List Item Stagger ("Stagger, then stop")
- **Category**: Data & Loading
- **Sourced Values**: 30–50ms apart. 250ms each (`translateY(8px→0)` + opacity `0→1`). Cap delay at 5 items (max 250ms total delay).

```css
.m-list-item {
  animation: item-enter 250ms cubic-bezier(0.23, 1, 0.32, 1) both;
  animation-delay: calc(min(var(--index), 5) * 40ms);
}
@keyframes item-enter {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
```

---

## 16. Bottom Sheet Snap ("Follow, then snap")
- **Category**: Gestures
- **Sourced Values**: 1:1 finger follow during drag. Release settle: 500ms `cubic-bezier(0.32, 0.72, 0, 1)`. Flick threshold: 0.4 px/ms to snap to next detent.

```css
.m-bottom-sheet {
  transition: transform 500ms cubic-bezier(0.32, 0.72, 0, 1);
}
.m-bottom-sheet[data-dragging="true"] {
  transition: none; /* raw tracking */
}
```

---

## 17. Swipe to Dismiss ("Past the line, let go")
- **Category**: Gestures
- **Sourced Values**: Threshold: 45px or 0.11 px/ms velocity. Exit: 200ms ease-out. Container gap collapse: 200ms transition after item exits.

```css
.m-swipe-item.is-dismissing {
  transform: translateX(100%);
  opacity: 0;
  transition: transform 200ms cubic-bezier(0.4, 0, 1, 1), opacity 200ms ease-in;
}
.m-swipe-wrapper.is-collapsed {
  height: 0;
  margin-bottom: 0;
  transition: height 200ms cubic-bezier(0.23, 1, 0.32, 1) 200ms,
              margin-bottom 200ms cubic-bezier(0.23, 1, 0.32, 1) 200ms;
}
```

---

## 18. Rubber Band Overscroll ("Resist the pull")
- **Category**: Gestures
- **Sourced Values**: Resistance coefficient $c = 0.55$. Pulling 100px moves content 35px ($x_{\text{disp}} = (1 - \frac{1}{cx/d + 1}) \cdot d$). Return: 590ms critically damped spring (zero bounce).

```css
.m-overscroll-container {
  transition: transform 590ms cubic-bezier(0.16, 1, 0.3, 1);
}
```
