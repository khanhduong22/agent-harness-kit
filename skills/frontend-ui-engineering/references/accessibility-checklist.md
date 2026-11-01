# WCAG 2.1 AA Accessibility Review & Audit Reference

 Distilled from Anthropic's official `accessibility-review` plugin (`anthropics/knowledge-work-plugins/design/skills/accessibility-review`) and W3C WCAG 2.1 Level AA engineering standards.

---

## 1. Visual & Color Contrast Requirements

| Element Category | Minimum Contrast Ratio (AA) | Enhanced Contrast (AAA) | Notes |
|---|---|---|---|
| **Normal Body Text** (`< 18pt` / `< 24px`, or `< 14pt` bold) | **4.5 : 1** | 7.0 : 1 | Applies to placeholders, helper text, table cells, and badges |
| **Large Text** (`>= 18pt` / `24px`, or `>= 14pt` / `18.66px` bold) | **3.0 : 1** | 4.5 : 1 | Headings and hero titles |
| **UI Components & Graphical Objects** | **3.0 : 1** | — | Input borders, focus rings, icons, chart series, toggle tracks |
| **Disabled Elements** | Exempt (WCAG 1.4.3) | — | Still keep readable (`>= 2.5:1` recommended) with `cursor-not-allowed` |

### Color Independence Rules (WCAG 1.4.1)
- **Never use color alone to convey status**: Pair red/green/amber states with an icon (`CheckCircle`, `AlertTriangle`, `XCircle`), text label (`Error:`, `Active`), or pattern.
- **Link distinguishability**: Links inline with body copy must have an underline or a `3:1` contrast differential plus a non-color hover/focus indicator.
- **High Contrast & Dark Mode**: Test both `:root` and `.dark` token sets, plus `@media (forced-colors: active)`.

---

## 2. Keyboard Navigation & Focus Management (WCAG 2.1.1, 2.4.3, 2.4.7)

- **100% Keyboard Operability**: Every interactive control must be reachable via `Tab` / `Shift+Tab` and actionable via `Enter` or `Space`.
- **No `<div onClick>`**: Always use native `<button>`, `<a href="...">`, `<input>`, `<select>`, or `<summary>`.
- **Visible Focus Ring (`:focus-visible`)**:
  - Never use `outline: none` or `focus:outline-none` without an explicit high-contrast replacement (`focus-visible:ring-2 focus-visible:ring-offset-2`).
- **Logical Tab Order**: DOM order must match visual reading order (left-to-right, top-to-bottom). Never use `tabIndex > 0`.
- **Modal / Drawer Focus Lifecycle**:
  1. When opened: Move focus to the first interactive element or dialog container.
  2. While open: Trap `Tab` and `Shift+Tab` inside the modal (`aria-modal="true"`, `role="dialog"`).
  3. On `Escape`: Close the modal and restore focus to the exact trigger element that opened it.
- **Skip Link**: Pages with complex navigation must include a `<a href="#main-content" className="sr-only focus:not-sr-only">Skip to main content</a>` as the first focusable node.

---

## 3. Screen Reader & Semantic Structure (WCAG 1.3.1, 4.1.2)

- **Landmark Regions**: Every page needs `<header>`, `<nav>`, `<main id="main-content">`, and `<footer>`.
- **Strict Heading Hierarchy**: Exactly one `<h1>` per view; never skip levels (`h1` -> `h2` -> `h3`, never `h1` -> `h4`).
- **Accessible Names**:
  - Icon-only buttons MUST have `aria-label="Close modal"` or `<span className="sr-only">...</span>`.
  - Decorative SVGs/icons MUST have `aria-hidden="true"`.
  - Informative images MUST have descriptive `alt="..."`; purely decorative images MUST have `alt=""`.
- **Form Association**:
  - Every `<input>`, `<select>`, and `<textarea>` requires an explicit `<label htmlFor="id">` or `aria-label`.
  - Validation errors must bind to the input via `aria-invalid="true"` and `aria-describedby="field-error-id"`.
- **Dynamic Live Regions**:
  - Toast notifications, search result counts, and async form errors must use `aria-live="polite"` (`role="status"`) or `aria-live="assertive"` (`role="alert"`).

---

## 4. Touch Targets, Motion & Cognitive Load (WCAG 2.5.5, 2.3.3)

- **Touch Target Minimum**: At least `44x44px` (`min-h-11 min-w-11`) on mobile/touch viewports with `>= 8px` gap between adjacent targets.
- **Reduced Motion**: Wrap all decorative entrance animations, parallax, and infinite marquees in `@media (prefers-reduced-motion: no-preference)` or disable transitions under `motion-reduce:transition-none motion-reduce:animate-none`.
- **200% Text Zoom**: Layouts must not clip text or require horizontal scrolling when browser zoom is set to `200%` at `1280px` viewport width.

---

## 5. Official Accessibility Audit Output Template

When running an accessibility review, structure findings using this severity-ranked format:

```markdown
# Accessibility Review: [Feature / Page / Component]

### Summary
- **Overall compliance**: [Pass / Partial / Fail] against WCAG 2.1 AA
- **Critical issues**: [X] (blocks access for a user group)
- **Major issues**: [X] (significant difficulty for a user group)
- **Minor issues**: [X] (usability degradation, workarounds exist)

### Critical Issues
1. **[Issue title]** — WCAG [X.X.X] ([Criterion Name], Level [A/AA])
   - **Location**: `[file.tsx:line]`
   - **Impact**: [Who is affected and how — e.g., keyboard-only users cannot submit the form]
   - **Fix**: [Exact code change required]
```
