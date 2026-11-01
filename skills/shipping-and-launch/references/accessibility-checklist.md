# WCAG 2.1 AA Accessibility Checklist

Companion reference for `shipping-and-launch/SKILL.md` and `frontend-ui-engineering/SKILL.md`.

## 1. Perceivable (Contrast & Alternatives)
- [ ] Normal body text meets `≥ 4.5:1` contrast ratio; large text (`≥18pt` or `≥14pt bold`) and UI borders/icons meet `≥ 3:1` across both light and dark modes.
- [ ] Every informative `<img>` and `<svg>` has descriptive `alt` text or `role="img"` + `aria-label`; decorative visuals use `aria-hidden="true"`.
- [ ] State is never conveyed by color alone (always paired with text badge, icon, or pattern).

## 2. Operable (Keyboard, Focus & Target Size)
- [ ] All interactive controls are reachable via `Tab` / `Shift+Tab` in logical DOM order with zero keyboard traps; modals trap focus while open and restore focus to the trigger on close.
- [ ] Every interactive element displays a high-contrast `:focus-visible` ring (`focus-visible:ring-2`).
- [ ] Pointer/touch targets measure at least `24×24px` (WCAG 2.5.8 minimum) and `44×44px` on mobile touch bars.
- [ ] Animations respect `@media (prefers-reduced-motion: reduce)`.

## 3. Understandable & Robust (Landmarks & ARIA)
- [ ] Page has `<html lang="...">`, a descriptive `<title>`, and exactly one `<main>` landmark with sequential headings (`h1` -> `h2` -> `h3`).
- [ ] Every `<input>`, `<select>`, and `<textarea>` has a programmatic `<label htmlFor="...">` or `aria-label`, and icon-only `<button>` elements have explicit `aria-label`.
