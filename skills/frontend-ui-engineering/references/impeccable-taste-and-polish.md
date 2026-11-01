# Impeccable Taste & Studio Craft Rules (`pbakaus/impeccable` + `Leonxlnx/taste-skill`)

Synthesized from [`pbakaus/impeccable`](https://github.com/pbakaus/impeccable) (`★ 98k+`) and [`Leonxlnx/taste-skill`](https://github.com/Leonxlnx/taste-skill) (`★ 107k+`, empirical study of 247 gallery and Awwwards sites). Use this reference alongside `references/claude-design-system-and-anti-slop.md` whenever designing, critiquing, or polishing marketing pages, editorial blogs, and dense application screens.

---

## 1. The 4 Surface Modes (`pbakaus/impeccable`)

Before choosing layout, type scale, or density, classify the surface into one of four modes:

| Surface Mode | Primary Goal | Typography & Density | Motion & Color Restraint |
|---|---|---|---|
| **1. Persuade** (Marketing, Landing, Launch) | Earn conviction and drive one clear action in 5 seconds | Dramatic display ratio (`4.3x–8.4vw` hero vs `16–18px` body), max 2 lines per headline | 1 signature scroll/interactive moment, 1 dominant real visual (≥50% of first viewport) |
| **2. Operate** (Dashboards, Admin, IDE, Trading) | Zero-latency scanability and high-frequency execution | Dense tabular alignment (`tabular-nums`), `12–14px` controls, 1px hairline grids (`divide-y`) | Near-zero decorative motion; instant state feedback (`hover`, `focus-visible`, optimistic UI) |
| **3. Read** (Engineering Blogs, Docs, Chronicles) | Effortless sustained comprehension over 10–30 minutes | `17–20px` body, `1.5–1.65` line-height, `55–72ch` measure, crisp code/diagram contrast | Zero layout-shifting chrome; quiet margin notes and clean table of contents |
| **4. Experience** (Interactive Stories, 3D/Canvas, MV) | Immersion and emotional pacing | Minimal HUD chrome, full-bleed stage, chapter-driven color/tone shifts | Choreographed camera/scroll beats with `prefers-reduced-motion` static fallback |

---

## 2. Empirical Craft Laws from 247 Studied Sites (`Leonxlnx/taste-skill`)

### 2.1 The Subject Inventory & Competitor Test (Before Writing HTML/JSX)
1. **Subject Inventory (8–12 Concrete Facts)**: List 8–12 specific, verifiable facts about the product/subject (dates, exact CLI commands, latency numbers, architecture diagrams, real file formats). Never invent testimonials, fake `99.9%` stat pills, or fictional customer logos.
2. **The Competitor Test**:
   - Complete this sentence: *"On this page, `[specific subject fact]` becomes `[visual/interactive device]`."*
   - If you could swap the client's name for a competitor and the hero/page still makes sense, the design is generic AI slop — redesign it around the real artifact.
3. **One Live Interactive Thing**:
   - Every persuasive or technical showcase page needs **one real interactive element** on the first or second screen (e.g., a live command switcher, interactive latency calculator, filterable benchmark matrix, or live token inspector) — not a static screenshot of grey placeholder bars.

### 2.2 The Two-Line Headline Arithmetic
- **Every `h1`–`h6` must fit in 2 lines or fewer at every viewport (`1440px`, `768px`, `390px`).**
- At `clamp(2.5rem, 5.5vw, 5.5rem)`, a two-line `h1` holds **26–34 characters total (5–7 words)**.
- When a headline wraps to 3–4 lines:
  1. **Cut words first.**
  2. **Widen the measure second.**
  3. **Shrink font-size last.**
- Statements longer than ~8 words belong in a `<p>` lead paragraph (`20–28px`), never inside an `<h1>`.

### 2.3 Space, Frame & Rhythm Laws
- **Equal Outer Margins & No Half-Empty Screens**:
  - The left and right outer frame margins (`16–32px` mobile, `32–64px` desktop) must match.
  - Never leave an off-center heading huddled on the left with a dead void on the right — balance the far side of the grid with the artifact, a figure, a specification list, or a code block.
- **Section Variety (Zero Repeated Card Grids)**:
  - No two adjacent sections may share the same layout blueprint. If Section 2 is a 3-column comparison, Section 3 must be a split architectural diagram, a full-width ledger table, or an interactive terminal.
  - Among the 247 studied sites, pages scoring `≥ 7.5/10` used icon-topped 3-card feature rows **1% of the time** (vs **28%** on weak sites `< 6.5/10`).
- **Tone Steps Over Borders & Shadows**:
  - Separate resting surfaces with a subtle step in background tone (`--bg-primary` $\to$ `--bg-elevated`), reserving shadows strictly for floating layers (modals, popovers, command palettes).

---

## 3. The 17 Impeccable Steering Verbs (`pbakaus/impeccable`)

When the user asks to refine an existing UI, apply the matching steering lens:

| Steering Verb | Concrete Engineering Action |
|---|---|
| **`critique`** | Score Hierarchy, Token Discipline, Anti-Slop Compliance, and Accessibility; name the top 3 highest-leverage fixes |
| **`audit`** | Run `python3 scripts/audit_design_system.py` + check all 7 interactive states (`default/hover/focus/active/disabled/loading/error`) |
| **`polish`** | Fix sub-pixel alignment, inconsistent border radii, awkward line wraps, optical icon centering, and missing `:focus-visible` rings |
| **`distill`** | Strip redundant badges, secondary glows, nested cards-in-cards, and verbose helper copy until only the core signal remains |
| **`bolder`** | Increase headline-to-body scale contrast (`4.5x+`), tighten display tracking (`-0.03em`), and make the hero artifact cover ≥50% of the viewport |
| **`quieter`** | Reduce accent color usage to `< 5%` of pixels, replace loud borders with subtle background tone steps, and calm competing CTAs |
| **`typeset`** | Enforce max 2 font families, ≤ 5 font sizes per page, `tabular-nums` on all numeric columns, and `45–75ch` reading measure |
| **`colorize`** | Enforce `1 ground + 1 elevated surface + 1 primary ink + 1 muted ink + 1 semantic accent`; verify WCAG AA `4.5:1` contrast |
| **`layout`** | Align text blocks to 2–3 shared vertical axes; set section vertical rhythm (`96–160px` desktop, `56–80px` mobile) |
| **`harden`** | Test long unbroken strings, empty arrays, `500` API errors, `320px` narrow screens, slow 3G skeletons, and double-click submission guards |
| **`clarify`** | Rewrite vague buttons (`Submit`, `Continue`) into `[Verb] + [Object]` (`Deploy to Production`, `Export Audit CSV`) |
| **`animate`** | Add staggered section entrances (`60–90ms`, `translateY(16px)` + `opacity` only) and tactile control feedback with `prefers-reduced-motion` support |
| **`adapt`** | Convert desktop multi-column tables and toolbars into touch-friendly (`≥44×44px`) mobile drawers and responsive cards at `390px` |
