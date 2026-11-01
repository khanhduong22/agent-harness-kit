# Editorial SVG Diagram Laws & 6 Connector Rules (`cathrynlavery/diagram-design`)

Synthesized from [`cathrynlavery/diagram-design`](https://github.com/cathrynlavery/diagram-design) (`★ 63k+`). Apply these 6 mandatory connector geometry rules, complexity budgets, and accessibility contracts whenever generating standalone HTML/SVG architecture schematics.

---

## 1. The 6 Non-Negotiable SVG Connector Geometry Rules

Every broken AI-generated diagram fails because of diagonal spaghetti lines and labels colliding with strokes. Enforce all 6 rules:

```text
Rule 1 (Orthogonal r=8 Elbows)         Rule 2 (Label Mask Gap 6–10px)        Rule 4 (Fan Attach Points)
┌────────┐                             ┌────────┐      ┌──────────┐          ┌────────────────────┐
│ Node A │──────┐                      │ Node A │─────▶│  STEP 1  │─────▶    │       Node A       │
└────────┘      │ r=8 rounded elbow    └────────┘      └──────────┘          └──┬──────┬──────┬───┘
                ▼                                    Opaque bg mask rect        │      │      │
           ┌────────┐                                hides stroke behind text   ▼      ▼      ▼
           │ Node B │                                                        L*1/4  L*2/4  L*3/4
           └────────┘                                                        (>=12px apart on edge)
```

1. **Rule 1 — Orthogonal Only (`r=8` Rounded Elbows)**:
   - Connectors between off-axis nodes MUST use orthogonal horizontal/vertical segments joined by `r=8` (`Q` or `A` SVG path arcs).
   - Straight `<line>` elements are permitted **only** when both endpoints share the exact same `x` or `y` coordinate. Diagonal slants are an automatic fail.
2. **Rule 2 — Opaque Label Masks with `6–10px` Stroke Clearance**:
   - Every arrow label (`<= 14 chars`, uppercase monospace) must sit on top of an opaque `<rect fill="{paper-bg}">` mask drawn *after* the arrow path and *before* the `<text>`, leaving a visible `6–10px` gap around the text so the line never bleeds through glyphs.
   - For vertical connector segments, place the label **beside** the line (`dx="+8"`), never rotated vertically (`writing-mode: vertical-rl` is banned).
3. **Rule 3 — Zero Overlapping or Stacked Strokes**:
   - Parallel routes must be offset by **`>= 12px`**. If two orthogonal connectors must cross, draw a small semi-circular bridge/hop (`A 6 6 0 0 1 ...`) at the intersection.
4. **Rule 4 — Fan Attach Points Along Shared Box Edges**:
   - Never attach 2+ arrows to the exact same `(x, y)` center point of a box edge. Distribute `N` attach points along edge length `L` at `L * k / (N + 1)` for `k = 1..N` (minimum `12px` apart).
5. **Rule 5 — Never Transit Behind a Non-Endpoint Node**:
   - Route connectors around intermediate boxes in the gutter (`>= 24px` clearance).
6. **Rule 6 — Draw Order (`Background -> Zones -> Arrows -> Label Masks -> Nodes`)**:
   - Always render `<path>` connectors before `<g class="node">` boxes so arrowheads meet box borders cleanly without overlapping node interiors.

---

## 2. Editorial Complexity Budget & Focal Hierarchy

- **Complexity Budget (Per Diagram)**:
  - **Max Nodes**: `9` (for overview diagrams) or `<= 16` (for zoned architecture blueprints). Above that, split into *Overview* + *Detail* diagrams.
  - **Max Connectors**: `12–16`. If two nodes always travel together with a single arrow and no branching, merge them into one deeper node.
  - **Max Focal Accent Nodes**: **`1–2 nodes maximum`**. Color the critical bottleneck or primary change in the focal accent (`coral` / `amber` / `emerald`); keep all other nodes in calm `ink` / `muted` / `paper-2` tones. Highlighting 5+ nodes destroys visual hierarchy.
- **4px Structural Grid**:
  - Snap all node `(x, y)` coordinates, `width`, `height`, and gutter gaps to multiples of `4px` (`16px`, `24px`, `32px`, `48px`).
- **Typography Pairing**:
  - **Node Titles**: Sans-serif `600` (`Geist`, `Inter`, or `Plus Jakarta Sans`).
  - **Technical Sublabels (Ports, SQL, Protocols, Latency)**: Monospace (`Geist Mono` or `JetBrains Mono`, `11–12px`).
  - **Diagram Header / Callout**: Editorial Serif or Display Sans.

---

## 3. Accessible & Responsive SVG Contract

1. **Accessible Figure Markup**:
   ```xml
   <div style="overflow-x: auto; -webkit-overflow-scrolling: touch;">
     <svg viewBox="0 0 960 540" style="min-width: 720px; width: 100%; height: auto;"
          role="img" aria-labelledby="arch-diagram-title arch-diagram-desc">
       <title id="arch-diagram-title">Singleflight L1/L2 Cache Architecture</title>
       <desc id="arch-diagram-desc">Request flow from API gateway through L1 heap cache, L2 Redis, and Singleflight promise deduplicator to PostgreSQL.</desc>
       <!-- defs, zones, connectors, masks, nodes, bottom legend strip -->
     </svg>
   </div>
   ```
2. **Legend Placement**:
   - Place the legend in a reserved horizontal strip at the bottom of the `viewBox` (`height: ~56px`), never floating inside the active routing canvas where it can collide with connectors.
