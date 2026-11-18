# Google Stitch MCP Prompt Engineering Guide

> Preserved from `stitch-prompt-engineering` into `frontend-ui-engineering/references/` (`+0 tokens/turn`). Standards and prompt engineering patterns for Google Stitch MCP to generate high-fidelity mobile and desktop screens matching existing design systems without visual artifacts or blown-up canvases.

---

## 1. The 5-Part Anatomy of a High-Fidelity Stitch Prompt

Every prompt sent to Stitch `generate_screen_from_text` or `edit_screens` MUST follow this 5-part architecture:

```
┌────────────────────────────────────────────────────────┐
│ 1. VIEWPORT & CONTAINER FRAMING (Strict dimensions)    │
├────────────────────────────────────────────────────────┤
│ 2. DESIGN SYSTEM & TOKEN CONSTRAINTS (Colors, Glass)   │
├────────────────────────────────────────────────────────┤
│ 3. SCREEN CHASSIS (Status Bar, Header, Sticky Nav)     │
├────────────────────────────────────────────────────────┤
│ 4. CONTENT SECTIONS & COMPONENT HIERARCHY (Real data)  │
├────────────────────────────────────────────────────────┤
│ 5. ANTI-HALLUCINATION & NEGATIVE CONSTRAINTS           │
└────────────────────────────────────────────────────────┘
```

### Canonical Template Structure

```markdown
[Device Viewport Frame & Role Context]
A high-fidelity [MOBILE/DESKTOP] application screen ([390px mobile viewport / 1440px desktop], [Platform e.g. iPhone standard], [Theme e.g. Spartan Dark Obsidian]) for [Project Name]: "[Screen Title]".

[Theme & Styling Tokens]
- Background: Solid dark obsidian #0B0F15 and surface #10141A (or exact project tokens).
- Accent Palette: Primary / Secondary / Tertiary / Warning hex values from active design system.
- Typography: Display/numeric font (`tabular-nums`) and readable body font.
- Surfaces & Elevation: Card surface opacity, backdrop-filter blur, and subtle hairline borders.

[Layout Hierarchy (Top-to-Bottom)]
1. Top Chassis: Native status bar + header with real product state badges.
2. Hero Section: Primary focus card with real copy and action triggers.
3. Core Data & Interactive Matrix: Structured cards/rows with realistic metrics and active toggles.
4. Summary / Telemetry Banner: Completion metric or status chip.
5. Bottom Navigation / Action Bar: Docked 4-tab bar with active state indicator.

[Anti-Hallucination & Quality Rules]
- Strictly lock viewport width (e.g., 390px mobile layout). Do NOT generate a desktop banner or freeform poster.
- Zero oversized clip-art shapes, zero raw unstyled drawings.
- Use polished micro-typography, crisp Lucide/Material/Phosphor glyphs, and verbatim product domain copy.
```

---

## 2. Mandatory Stitch MCP Parameters

When invoking `generate_screen_from_text` via Stitch MCP, ALWAYS supply:

| Parameter | Type | Value Example | Why It Is Mandatory |
|---|---|---|---|
| `projectId` | String | `"3529453464823562204"` | Stitch project ID without `projects/` prefix |
| `designSystem` | String | `"assets/7f97cbfe467240289e5eb6fe8f1ea964"` | **CRITICAL**. Omitting this causes Stitch to ignore project tokens and fall back to generic white palettes |
| `deviceType` | String | `"MOBILE"` or `"DESKTOP"` | Locks the target aspect ratio |
| `modelId` | String | `"GEMINI_3_8_FLASH"` (or active Stitch default) | Target Stitch rendering model |
| `prompt` | String | Structured 5-part prompt | Full viewport, chassis, copy, and negative rules |

---

## 3. Common Stitch Failure Modes & Fixes

1. **Component-Only Prompt $\to$ Giant Graphic Poster**:
   - *Cause*: Prompting `"Quote Card component"` makes Stitch output a standalone `1280x2864` graphic poster with clip-art shapes.
   - *Fix*: Frame the prompt as a **complete application screen** with the target component embedded as the Hero card inside a locked `390px` (or `1440px`) chassis with status bar and nav.
2. **Missing `designSystem` Parameter $\to$ White Palette Drift**:
   - *Cause*: Omitting `designSystem` lets the generator invent default colors and light backgrounds.
   - *Fix*: Call `list_design_systems` or `get_project`, extract the `assets/...` ID, and pass it explicitly on every call.
3. **Vague Copy $\to$ Lorem Ipsum & Empty Boxes**:
   - *Cause*: Writing `"card with some motivation text and stats"` generates placeholder text and blank rectangles.
   - *Fix*: Supply **verbatim real UI copy**, concrete numbers/metrics, and exact action labels in the prompt.
