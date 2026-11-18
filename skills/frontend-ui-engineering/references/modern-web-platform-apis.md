# Modern Web Platform APIs & Baseline Standards

> Distilled from `GoogleChrome/modern-web-guidance` (Chrome, Edge, Firefox, MDN). Replaces heavy JS polyfills and fragile layout hacks with Baseline 2024–2026 native browser primitives.
> Full offline guide corpus synced at `~/.agent-harness/upstream-cache/googlechrome__modern-web-guidance/skills/modern-web-guidance/guides/`.

---

## 1. Declarative Top-Layer Controls (`<dialog>`, `[popover]`, Invokers, Anchors)

### Invoker Commands API (`commandfor` + `command`)
Replace custom click listeners for toggling dialogs and popovers with declarative HTML attributes:

```html
<!-- Popover toggle / explicit manual control -->
<button commandfor="filters-popover" command="toggle-popover">Filters</button>
<div id="filters-popover" popover>
  <!-- Use command="hide-popover" if manual; restore focus to trigger via JS when closing internally -->
</div>

<!-- Modal dialog control (command="show-modal" | "close") -->
<button commandfor="confirm-dialog" command="show-modal">Delete</button>
<dialog id="confirm-dialog" closedby="any" aria-labelledby="confirm-title">
  <h2 id="confirm-title">Confirm deletion</h2>
  <button commandfor="confirm-dialog" command="close" value="cancel">Cancel</button>
</dialog>
```

- **Hard Trap**: NEVER combine `popovertarget` and `commandfor` on the same `<button>` for the same popover—it double-toggles and breaks state.
- **Focus Recovery**: Closing a `popover="manual"` via a button inside the popover removes focus from the DOM; script `.focus()` back to the invoker button.
- **Light-Dismiss Modals**: Add `closedby="any"` on `<dialog>` opened via `dialog.showModal()` (enables backdrop clicks, `Esc`, and `.close()`). Default modal behavior is `closerequest` (`Esc` + `.close()`); use `closedby="none"` for forced confirmation flows.

### Top-Layer Entry & Exit Animations (`@starting-style`, `allow-discrete`, `overlay`)
```css
dialog[open],
[popover]:popover-open {
  opacity: 1;

  /* Place @starting-style inside or after the open rule for cascading */
  @starting-style { opacity: 0; }

  @media (prefers-reduced-motion: no-preference) {
    transform: scale(1);
    @starting-style { transform: scale(0.95); }
  }
}

dialog,
[popover] {
  opacity: 0;
  /* MANDATORY: include display and overlay for top-layer retention during exit */
  transition-property: opacity, transform, display, overlay;
  transition-duration: 0.2s;
  transition-timing-function: cubic-bezier(0.23, 1, 0.32, 1);
  /* Place OUTSIDE transition shorthand so older browsers don't drop the whole declaration */
  transition-behavior: allow-discrete;

  @media (prefers-reduced-motion: no-preference) {
    transform: scale(0.95);
  }
}

dialog::backdrop,
[popover]::backdrop {
  background-color: rgba(0, 0, 0, 0);
  transition: background-color 0.2s ease-out, display 0.2s, overlay 0.2s;
  transition-behavior: allow-discrete;
}

dialog[open]::backdrop {
  background-color: rgba(0, 0, 0, 0.5);
  @starting-style { background-color: rgba(0, 0, 0, 0); }
}

@media (prefers-reduced-motion: reduce) {
  dialog, [popover] { transition-duration: 0.1s; }
}
```

### CSS Anchor Positioning & Anchored Container Queries
Invoking a popover via `popovertarget` or `commandfor` creates an implicit anchor connection without manual `anchor-name` wiring:

```css
@supports (anchor-name: --a) {
  [popover][role="tooltip"] {
    inset: auto;
    margin: unset;
    position: fixed;
    position-area: block-start;
    position-try-fallbacks: flip-block;
    container-type: anchored;
  }

  .tooltip-content::before {
    content: "▼" / "";
    position: absolute;
    inset-block-end: -0.75rem;
    inset-inline-start: 1rem;
  }

  /* Flip tooltip arrow when browser flips placement below trigger */
  @container anchored(fallback: flip-block) {
    .tooltip-content::before {
      content: "▲" / "";
      inset-block-end: auto;
      inset-block-start: -0.75rem;
    }
  }
}
```

> **ARIA Trap**: Plain button groups inside a `[popover]` must NOT declare `role="menu"` or `aria-haspopup` unless you also implement full roving arrow-key navigation.

---

## 2. Modern CSS Architecture, Color Spaces & WCAG Typography

### Intrinsic Size Transitions (`interpolate-size` & `calc-size()`)
Replace JS height measurement and `max-height` hacks for accordions and disclosures:
```css
:root { interpolate-size: allow-keywords; }

.disclosure {
  block-size: 0;
  overflow: hidden;
  transition: block-size 0.25s cubic-bezier(0.23, 1, 0.32, 1);
}
.disclosure.is-open { block-size: auto; }
/* Dynamic math on intrinsic size: block-size: calc-size(auto, size + 1rem); */
```

### Scoping, State Queries & Individual Transforms
- **`@scope` Containment**: Prefer `@scope (.card) to (.card-slot)` over brittle `:not()` exclusion chains for nested subtrees.
- **State Queries**: Style parent wrappers via `:has()` (e.g., `form:has(:user-invalid) button[type="submit"]`) and compose size/scroll/anchored queries (`@container (inline-size > 32rem)`).
- **Individual Transforms**: Use `translate`, `rotate`, and `scale` CSS properties directly instead of overwriting a single `transform:` chain across `:hover` / `:active` states.

### Zero-FOUC Dark Mode & Color Mixing Pitfalls
1. **Declare Light/Dark Early**: Include `<meta name="color-scheme" content="light dark">` in `<head>` AND apply `color-scheme: light dark;` directly on `:root` or `html` (NOT only `body`, or root scrollbars and initial viewport canvas flash light).
2. **Adaptive Tokens**: Define paired tokens with `light-dark(var(--surface-light), var(--surface-dark))`.
3. **Chromium `oklch` Neutral Bug**: Use semantic tokens first. When generating dynamic tints/shades with `color-mix()`, use **`in oklab`**, NEVER `in oklch` with neutrals (`white`, `black`, grays) — low-chroma colors (`chroma < 0.02`) resolve powerless hue to `0deg` in Chromium and shift grays toward pink/magenta-red. Avoid shifting `L` alone in `oklch(from ...)` beyond `30%` (lacks browser gamut mapping).
4. **Forced Colors & Non-Text Contrast**: Ensure `>= 3:1` contrast for interactive UI borders/states (WCAG 1.4.11). In `@media (forced-colors: active)`, replace box-shadow outlines with real CSS `border` / `outline` using system keywords (`CanvasText`, `Highlight`); reserve `forced-color-adjust: none` solely for color pickers and syntax swatches.

### WCAG Typography, Zoom & Wrapping
- **Relative Sizing**: Use `rem` (never `px`) for `font-size`. Avoid fixed `height` / `block-size` on text-bearing controls (buttons, tabs, badges, cards) — use `min-block-size` so WCAG 1.4.12 text spacing overrides never clip labels.
- **Zoom-Safe `clamp()`**: Keep `max <= 2.5 * min` in `clamp(minRem, rem + vw, maxRem)` (e.g., `clamp(1.25rem, 1rem + 2vw, 2.5rem)`) so 500% browser zoom can still double text size (WCAG 1.4.4).
- **Targeted Wrapping**: Use `text-wrap: balance` on headings/captions (never on `*` or bordered/shaded cards where trailing gap looks lopsided) and `text-wrap: pretty` on body prose (`max-width: 65ch`).

---

## 3. Modern Native Forms, Customizable `<select>` & IME Safety

### Customizable Native `<select>` (`appearance: base-select`)
Preserve keyboard navigation, form integration, and top-layer collision handling while fully styling the select dropdown:
```css
.custom-select,
.custom-select::picker(select) {
  appearance: base-select;
}
.custom-select::picker(select) { border-radius: 0.5rem; }
.custom-select option::checkmark { content: "✓"; }
```
Put a `<button><selectedcontent></selectedcontent></button>` as the first child of `<select>` to mirror rich option markup inside the closed button trigger, and style `select::picker-icon` for custom carets.

### Auto-Sizing Fields (`field-sizing: content`)
```css
input.autosize {
  field-sizing: content;
  width: auto;
  min-inline-size: 15ch; /* Prevent 0px collapse when empty */
  max-inline-size: 50ch; /* Prevent runaway expansion */
}
textarea.autosize {
  field-sizing: content;
  height: auto;
  width: 100%;          /* Keep horizontal width locked against placeholder jumps */
  min-block-size: 3lh;
}
```

### Post-Interaction Validation & Semantic Forms
- **Wait for Blur/Submit (`:user-invalid`)**: Style invalid inputs using `:user-invalid` / `:user-valid` instead of eager `:invalid` (which turns inputs red on the first keystroke).
- **Hint Placement & ARIA**: Render format hints *above* inputs so browser autofill popovers don't cover them. Attach the error element ID to `aria-describedby` dynamically only while invalid, and pair red borders with visible icons/text.
- **Form Hygiene**: Wrap search/filter blocks in `<search>`, set `type="button"` on all non-submit buttons inside `<form>`, and apply standard `autocomplete` tokens (`one-time-code`, `email`, `current-password`, `new-password`, `username webauthn`).

### IME-Safe Enter-to-Submit (Vietnamese, Japanese, Chinese, Korean)
Any custom `keydown` handler intercepting `Enter` on `<textarea>` or single-line `<input>` (chat inputs, inline renames, command palettes, search bars) **MUST check `event.isComposing`**:
```js
input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    if (event.isComposing) return; // Never submit mid-IME character composition
    form.requestSubmit();          // Use requestSubmit() so constraint validation & submit event fire
  }
});
```

---

## 4. Modern JS Primitives, Scroll Motion, WebMCP & Legacy Scans

### Built-in Platform Primitives (Skip Redundant Utilities)
| Legacy Workaround | Native Platform Replacement | Notes |
|---|---|---|
| `JSON.parse(JSON.stringify(x))` | `structuredClone(x)` | Preserves `Date`, `Map`, `Set`, cyclic refs |
| `[...arr].sort(...)` / splice | `arr.toSorted()`, `toReversed()`, `toSpliced()`, `with()` | Non-mutating copy methods |
| `.reduce()` grouping buckets | `Object.groupBy()` / `Map.groupBy()` | Null-prototype safe grouping |
| Deferred promise wrapper | `Promise.withResolvers()` | Clean external resolve/reject handles |
| Manual timer + abort cleanup | `AbortSignal.any([userSignal, AbortSignal.timeout(ms)])` | Composite cancellation & timeouts |
| Error wrapping losing root trace | `new Error('Context failed', { cause: err })` | Native cause chain |
| `el.innerHTML = ''` / append loop | `el.replaceChildren(...nodes)` | Atomic child swap without HTML parser |
| Moving DOM nodes losing state | `parent.moveBefore(node, refChild)` | Preserves iframe, video, CSS animation, & focus state |
| Ad-hoc `Date` timezone math | `Temporal` (`PlainDate`, `ZonedDateTime`, `Instant`) | Exact calendar & IANA DST arithmetic |

### Off-Main-Thread Scroll & View Transitions
- **Scroll-Driven CSS**: Prefer CSS `animation-timeline: scroll()` and `view()` over JS scroll listeners so animations stay on the compositor thread.
- **SPA & MPA View Transitions**: Wrap DOM state swaps in `document.startViewTransition(() => updateDOM())` with unique `view-transition-name` per morphed element (`>1` matching element aborts the transition). For MPAs, opt into same-origin cross-document morphs via `@view-transition { navigation: auto; }` gated inside `@media (prefers-reduced-motion: no-preference)`.

### Framework Integration, Fallbacks & WebMCP
- **JSX/TypeScript Attributes**: Spread/cast new HTML attributes (`{...({ commandfor: id, command: 'toggle-popover', closedby: 'any', popover: 'hint' } as Record<string, unknown>)}`) rather than dropping native behavior. Call `.showModal()` / `.moveBefore()` via refs outside VDOM reconciliation; keep `:root` and `@starting-style` top-level/unscoped; generate unique IDs with `useId()`.
- **Baseline Fallback Policy**: Assume **Baseline Widely Available** APIs need zero fallback. Feature-detect Newly Available APIs (`@supports`, `'setHTML' in Element.prototype`) unless a project `AGENTS.md` / `CLAUDE.md` specifies a stricter Baseline year.
- **WebMCP (Chromium 146+ Early Preview)**: Expose client UI actions to browser AI agents declaratively with `<form toolname="..." tooldescription="...">` or via framework hooks (`useWebMCP` in React/Vue — never raw `document.modelContext.registerTool()` inside component bodies).

### Opt-In Legacy Modernization Scan (Broad Audits Only)
Do **not** run `legacy-scan` on scoped component edits. Only when asked for a full-repo modernization audit:
```bash
DISABLE_TELEMETRY=1 npx --yes modern-web-guidance@latest legacy-scan src/ --json
```
Verify every finding against its `keepWhen` / `dropWhen` rubric before refactoring, or inspect individual topic files locally under `~/.agent-harness/upstream-cache/googlechrome__modern-web-guidance/skills/modern-web-guidance/guides/`.
