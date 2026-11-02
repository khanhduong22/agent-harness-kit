# UI Finish-Gate Reviewer & Screen Design Contract (`msitarzewski/agency-agents`)

Distilled from `msitarzewski/agency-agents` (`★ 165k+`, `design/design-ui-finish-gate-reviewer.md`). Use before shipping any new screen, dashboard, onboarding flow, or mobile layout to catch interchangeable "AI-generated SaaS" defaults and enforce a hard `PASS` / `HOLD` finish gate.

---

## 1. Establish the Product Lens & Screen Design Contract

Before writing or critiquing UI pixels, define the **Screen Design Contract** so every layout decision serves the user's real workflow rather than component-library defaults:

```markdown
# [Screen Name] Design Contract
- **User + Job**: [Who uses this screen and what concrete task they must finish]
- **First-Read Object**: [The single metric, status, or domain object the eye must find in <1s]
- **Primary Action**: [One observable primary CTA above the fold]
- **Density Decision**: [Compact / Balanced / Spacious — justified by daily scan frequency]
- **Visual Hierarchy**: [1. Primary Signal -> 2. Action Controls -> 3. Supporting Context]
- **Interaction Model**: [Data table, canvas, split-pane editor, timeline, command queue, form]
- **Responsive Priority (390px)**: [What stays pinned in the compact row vs collapses into detail drawer]
- **Forbidden Defaults**: [Interchangeable patterns banned on this screen]
```

### Common Forbidden Generic Defaults
- **Four Equal-Weight Top Metric Cards**: Makes every number look equally urgent while burying the actual operational decision below the fold.
- **Decorative Card Grids for Linear Decisions**: Using 3-column marketing cards with stock icons where the user needs a direct configuration chooser with live preview.
- **Naive Mobile Column Stacking**: Stacking 8 desktop table columns into tall vertical cards on `390px` mobile, hiding the status/action operators scan for.

---

## 2. The 6-Axis Pre-Ship Implementation Audit

Audit the rendered implementation across both desktop (`1440px`) and mobile (`390px`) viewports in this strict order:

| Audit Axis | Pass Requirement | Hold Trigger |
|---|---|---|
| **1. Product Legibility** | A new user can identify the domain object and primary workflow in the first viewport without reading body paragraphs. | Screen looks like an interchangeable template that could belong to any SaaS. |
| **2. Visual Weight Hierarchy** | Contrast, size, and placement follow user decision priority. | Secondary metadata or decorative chrome competes with the primary signal. |
| **3. Pattern Fit** | Layout structure matches task frequency (e.g., dense scannable rows for daily ops; guided steps for rare high-risk setup). | Using a hero banner or card gallery for a high-frequency operational tool. |
| **4. Complete State Matrix** | `loading` (skeleton matching layout), `empty` (with direct creation CTA), `error` (actionable retry), `focus-visible`, and `disabled` states are intentional. | Blank white flash on load, raw error strings, or dead-end empty states. |
| **5. Narrow-Viewport Job Preservation (`390px`)** | Preserves status, owner, and primary action in a compact prioritized row (`>= 44x44px` touch targets); moves secondary history to a detail sheet. | Horizontal overflow or tall stacked cards that require excessive scrolling to compare items. |
| **6. Token & System Fidelity** | Uses semantic design tokens, consistent radius/border rhythm, and tabular numerals (`tabular-nums`) for all numeric columns. | Arbitrary magic hex colors, mixed icon styles, or jittering number widths. |

---

## 3. Hard `PASS` / `HOLD` Finish Gate Verdict

Never conclude a UI review with vague adjectives ("looks clean and modern"). Emit an explicit `PASS` or `HOLD` gate:
- **Return `HOLD`** whenever the first-read object is buried, forbidden generic defaults remain, or mobile/empty/error states are unverified. List exact required code changes and the viewport/state verification method for each.
- **Return `PASS`** only when the primary object, primary action, state matrix, and `1440px`/`390px` viewports are verified with runtime evidence.
