# Anthropic Official Design System Audit, Anti-AI-Slop & UX Playbook

Consolidated from Anthropic's official repositories:
1. **`anthropics/knowledge-work-plugins`** (`design/skills/design-system`, `design-critique`, `design-handoff`, `ux-copy`, `accessibility-review`)
2. **`anthropics/skills`** (`skills/frontend-design/SKILL.md` — Anti-AI-Slop Studio Direction)

---

## Part 1: Official `/design-system` Modes (`audit | document | extend`)

### Mode A: `audit` — Design System Health & Consistency Audit
When auditing a codebase or component library, inspect across 3 pillars:

1. **Naming Consistency**:
   - Are tokens named following a single predictable pattern (`--color-surface-primary`, `--space-4`, `--radius-md`)?
   - Flag deviations (e.g., mixing `--blue-500`, `--primaryColor`, and `--brand_accent`).
2. **Token Coverage (Zero Hardcoded Magic Values)**:
   - Flag raw hex values (`#1e293b`), raw `rgb()/hsl()`, or arbitrary Tailwind brackets (`p-[13px]`, `text-[15px]`, `bg-[#f4f1ea]`) in component files that bypass semantic tokens.
3. **Component Completeness (`6 Mandatory States`)**:
   - Every interactive component (`Button`, `Input`, `Select`, `Card`, `Dialog`, `Table`, `Tabs`) must account for:
     - `Default`
     - `Hover` (`hover:`)
     - `Focus-Visible` (`focus-visible:`)
     - `Active / Pressed` (`active:`)
     - `Disabled` (`disabled:` + `aria-disabled`)
     - `Loading` (`isLoading` / `aria-busy` skeleton or spinner)
     - `Error` (`aria-invalid` + error message slot)

#### Official Audit Output Format
```markdown
## Design System Audit: [Target] ([Score]/100)

### Summary
- **Components reviewed**: [X]
- **Tokens defined**: [X]
- **Consistency score**: [High / Medium / Low] ([Score]/100)

### Issues Found

#### Naming Inconsistencies
| Current | Suggested | Reason |
|---|---|---|
| `[current name]` | `[suggested name]` | `[why]` |

#### Missing Token Coverage (Hardcoded Values)
- `[file:line]` — hardcoded `[value]` -> replace with `[semantic-token]`

#### Incomplete Components (State Matrix)
| Component | Default | Hover | Active | Focus | Disabled | Loading | Error |
|---|---|---|---|---|---|---|---|
| `Button` | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | N/A |
| `Input` | ✓ | ✓ | ✓ | ✓ | ✓ | N/A | ✗ |

### Priority Fixes
1. **[Highest-impact fix]** — [why it matters and what it unblocks]
2. **[Second priority]**
3. **[Third priority]**
```

---

### Mode B: `document` — Component Documentation Spec
When documenting a component (`--mode document`), produce:
1. **Overview**: 1–2 sentences on what the component does and when to use it (and when NOT to use it).
2. **Variants Table**: `Variant | Use Case | Visual Difference`.
3. **Props / API Table**: `Prop | Type | Default | Required | Description`.
4. **States Matrix**: Visual and behavioral description of Default, Hover, Focus, Active, Disabled, Loading, Error.
5. **Usage Guidelines**: Paired **Do** vs **Don't** rules (minimum 3 pairs).
6. **Accessibility Spec**: Keyboard keys (`Enter`, `Space`, `Escape`, `ArrowUp/Down`), ARIA roles/attributes, focus restoration.

---

### Mode C: `extend` — Proposing New Tokens or Components
Before adding a new token or component, evaluate whether existing primitives can compose it. If a new addition is justified:
- **New Tokens**: Define `Token Name | Value | Semantic Purpose | Light & Dark Mode Mapping`.
- **New Components**: Define `Purpose`, `Variants`, `Anatomy (Container -> Header -> Body -> Footer -> Actions)`, `Tokens Consumed`, `States`, and `Accessibility Contract`.

---

## Part 2: Anthropic's Official Anti-AI-Slop Studio Direction (`frontend-design`)

Anthropic's internal design team documented the exact visual and structural tells that betray LLM-generated interfaces ("AI Slop"). Enforce these calibration rules on every UI task:

### 1. The 5 Forbidden AI-Slop Tells
1. **The "Claude / SaaS Default" Palettes**:
   - **Tell A**: Warm cream background (`#F4F1EA` / `#FAF8F5`) paired with terracotta/coral accent (`#D97757`).
   - **Tell B**: Near-black (`#0B0B0B`) paired with acid-green (`#CCFF00`) or generic indigo-to-purple gradient (`from-indigo-500 via-purple-500 to-pink-500`).
   - **Fix**: Derive palettes from the product's actual domain and brand tokens.
2. **Stock Card & Shadow Monotony**:
   - **Tell**: Uniform 3-column rounded cards (`rounded-2xl`) with soft drop shadows (`0 8px 24px rgba(0,0,0,0.08)`) and gradient icon badges repeated down the page.
   - **Fix**: Vary section rhythm. Mix borderless typographic rows, 1px hairline grids (`divide-y divide-border`), split asymmetric panels, and high-density tables.
3. **Tracked-Out Uppercase Eyebrows Everywhere**:
   - **Tell**: Placing a tiny `text-xs uppercase tracking-widest` eyebrow label above every single `<h2>` and card title, or formatting metadata as `CATEGORY · SUBCATEGORY · 2026`.
   - **Fix**: Use at most **1–2 eyebrow labels per page** (e.g., Hero and primary section transition). Let headings stand on their own hierarchy.
4. **Formulaic Punctuation & CTA Arrows**:
   - **Tell**: Appending `→` (`&rarr;`) to every button and link, numbering non-sequential cards `01 / 02 / 03`, or italicizing/coloring one "magic word" in every headline.
   - **Fix**: Reserve `→` strictly for external navigation or pagination links. Never number cards unless order is a strict step-by-step sequence.
5. **The "3 Stat Pills in the Hero" Cliché**:
   - **Tell**: Stacking `99.9% Uptime | 10x Faster | 24/7 Support` stat cards directly underneath every hero CTA.
   - **Fix**: Ground the hero in the actual product artifact — a live interactive preview, a real command/search bar, or a high-signal architectural visual.

### 2. The Two-Pass Token Discipline
Before writing component markup, define a strict **Two-Pass Token Plan**:
- **Pass 1 (Base Scale)**: Choose **1 background**, **1 elevated surface**, **1 primary text**, **1 muted text**, **1 primary accent**, and **1 hairline border token**.
- **Pass 2 (Coco Chanel Restraint Rule)**: Before shipping, audit the screen and **remove one decorative treatment** (drop a redundant gradient, remove an unnecessary pill badge, or flatten a nested card-inside-a-card).

### 3. Aesthetic Archetype Calibration
Match the visual mechanics to the product archetype rather than applying one style to everything:

| Archetype | Surface & Border Mechanics | Typography & Density | Motion & Interaction |
|---|---|---|---|
| **Developer / Infra Tooling** (Linear, Vercel, Raycast, Stripe) | Crisp `1px` borders, subtle surface steps (`#090A0F` -> `#11131A`), zero drop-shadows on cards | Monospace for IDs/timestamps/shortcuts (`tabular-nums`), tight `13px–14px` body copy | Instant (`100ms–150ms` `cubic-bezier(0.22, 1, 0.36, 1)`), keyboard-first (`Cmd+K`) |
| **Editorial / Technical Publishing** (Stripe Press, Works in Progress) | Warm high-contrast paper/ink, hairline rules, generous margin notes | High-contrast display serif or humanist sans + `60ch–70ch` measure, `1.65+` line-height | Minimal motion; focus on reading cadence, footnotes, and scannable TOC |
| **Financial / Data Workbench** (Bloomberg, Mozyfin, TradingView) | High-density tabular layouts, right-aligned numbers, muted gridlines | `font-variant-numeric: tabular-nums` mandatory on all prices/deltas/percentages | Zero layout shift on live ticks; subtle flash on cell delta |

---

## Part 3: Design Critique (`design-critique`) & Handoff (`design-handoff`)

### 4-Layer Design Critique Framework
When reviewing an existing screen or PR:
1. **Hierarchy & Squint Test**: Blur the screen — is the primary action and #1 information priority immediately unmistakable within 2 seconds?
2. **Interaction & State Coverage**: What happens on empty data (`0 items`), massive data (`10,000 items` / 80-char German usernames), slow 3G (`2s` loading), and server failure (`500`)?
3. **System Alignment**: Does this introduce any one-off spacing, font size, or color that breaks existing tokens?
4. **UX Copy & Microcopy (`ux-copy`)**:
   - **Buttons**: Use specific `[Verb] + [Object]` (`Create API key`, `Export CSV`) — never vague labels (`Submit`, `Confirm`, `OK`, `Yes`).
   - **Error Messages**: State **(1) What went wrong** + **(2) How to fix it** in plain human language (`"API key expired. Generate a new key in Settings -> API."`), never raw status codes (`"Error 401: Unauthorized"`).
   - **Empty States**: Explain **what lives here** + **why it matters** + **1 primary CTA to create the first item**.
   - **Destructive Confirmations**: Name the exact consequence (`"Delete 'production-db'? This permanently erases 42 GB of snapshots and cannot be undone."`) and match the button verb (`Delete database`).
