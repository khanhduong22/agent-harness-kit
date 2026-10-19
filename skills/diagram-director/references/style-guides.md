# Style Guides

Deep spec for every `Style ID` in `data/styles.csv`. Read this file after `search.py --domain styles`
or `--blueprint` has told you which style applies — don't read the whole file for one diagram.

`Template Status=shipped` means a working base template exists at `templates/base/<style-id>.html`.
`Template Status=planned` means no template exists yet — **never cite a template path for a planned
style.** Compose the diagram from `templates/snippets/` plus the tokens and rendering rules below
instead, and say plainly that no base template exists for that style.

Third-party CDN URLs are recorded here (not in CSV cells) per the repo's security rule: URLs live in
this human-reviewed file so they get eyes before being trusted.

---

## hand-drawn-sketch

**Template Status.** shipped — `templates/base/hand-drawn-sketch.html`.

**Visual DNA.** Wobbly, hand-jittered strokes (roughness 1–2 on the rough.js scale), multiple
overlapping passes per line, hachure/cross-hatch fills instead of solid fills. Warm, informal,
whiteboard-marker mood with muted pastel fills and dark ink outlines. Off-white paper background
(`#fdfaf3`) with faint grain, no grid.

**Fonts.** `Caveat`, `Gochi Hand` (fallback: `'Comic Sans MS', cursive`). Handwritten feel on labels.

**Stroke / fill.** Rounded rectangles drawn with jittered path points and a double-stroke outline for
emphasis. Connectors: single wobbly bezier line with a hand-drawn arrowhead, slight overshoot at endpoints.

**Motion affinity.** `connection-draw-in`, `dash-flow`, `pulse-glow`, `node-boot-sequence`, `round-trip`, `packet-travel`, `queue-fill`, `retry-loop`, `cache-hit-miss`, `error-propagation`, `scale-out-spawn`, `state-transition-arrow`.

**Runtime — two paths.**
- **Local (`--target local`):** `needs-js`, CDN dependency `roughjs@4`.
  ```html
  <script src="https://cdn.jsdelivr.net/npm/roughjs@4/bundled/rough.js"></script>
  ```
  Use `rough.svg(svgRoot)` to redraw each shape with `roughness: 1.5, bowing: 1`.
- **Artifact (`--target artifact`), css-only fallback:** rough.js is unavailable (no CDN scripts
  allowed). Approximate the jitter with an SVG filter instead:
  ```svg
  <filter id="sketchy">
    <feTurbulence type="fractalNoise" baseFrequency="0.02" numOctaves="2" seed="3" result="noise"/>
    <feDisplacementMap in="SourceGraphic" in2="noise" scale="4"/>
  </filter>
  ```
  Apply `filter: url(#sketchy)` to path/rect elements; use `stroke-linecap: round` and
  `stroke-linejoin: round` for a softer hand-drawn line quality. Keep the Google Fonts `<link>` —
  `fonts.googleapis.com`/`fonts.gstatic.com` are the one external host the Artifact sandbox permits
  (SKILL.md → Scope & Safety) — and put the system handwriting stack
  `font-family: 'Segoe Print', 'Bradley Hand', cursive` behind it as the fallback, as every font
  needs one. What an artifact cannot have is rough.js, not the font.

**Dark mode.** Supported — invert paper to a warm dark gray, keep ink strokes light.

**Accessibility.** Jittered strokes must stay high-contrast against the paper background. Labels stay
real text, never baked into the path. Roughness must not obscure text legibility.

**Best for.** Brainstorming sessions, early-stage architecture docs, workshop collab boards, informal
proposals. **Avoid for** formal client-facing deliverables, print-ready technical specs, diagrams over
40 nodes.

---

## flat-minimal

**Template Status.** shipped — `templates/base/flat-minimal.html`.

**Visual DNA.** Thin 1.5–2px solid strokes, no roughness, crisp geometric lines. Flat solid fills, zero
gradients, zero shadows. Restrained 2–3 brand accents plus neutral grays; generous whitespace reads
calm and professional (Stripe/Vercel-style).

**Fonts.** `Inter`, `Geist` (fallback: `-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`).
Medium weight for node names, regular for annotations.

**Stroke / fill.** Rounded rectangles with an icon glyph plus label, consistent 8px corner radius.
Connectors: clean orthogonal or smooth bezier lines, solid stroke, simple arrowhead.

**Motion affinity.** `dash-flow`, `packet-travel`, `pulse-glow`, `queue-fill`, `heartbeat`, `connection-draw-in`, `round-trip`, `state-transition-arrow`, `fanout-broadcast`, `cache-hit-miss`, `failover-reroute`, `replication-sync`, `retry-loop`, `error-propagation`, `ttl-expiry`, `scale-out-spawn`, `node-boot-sequence`, `stream-continuous`, `batch-tick`.

**Runtime.** `css-only`, no CDN dependency — safe for both `local` and `artifact` targets unmodified.

**Artifact fallback.** None needed; this style is already css-only with a system-safe font stack.

**Dark mode.** Supported.

**Accessibility.** High contrast by default; pair accent color with icon shape, never color alone.
Label text at least 14px.

**Best for.** Public-facing architecture docs, SaaS product docs, investor decks, onboarding guides.
**Avoid for** dense low-level infra topology, playful/informal contexts, retro/nostalgic themes.

---

## blueprint

**Template Status.** shipped — `templates/base/blueprint.html`.

**Visual DNA.** Rigid orthogonal lines only, no curves, uniform 1px hairline strokes. No fill or a very
light tinted fill — nodes read as outlined schematic symbols. Cyan/white lines on dark navy
(`#0a1a2f`), or navy lines on white; formal, precise, cold. Faint 1px grid at 10–20% opacity.

**Fonts.** `JetBrains Mono`, `IBM Plex Mono` (fallback: `ui-monospace, 'Courier New', monospace`).
Uppercase node titles.

**Stroke / fill.** Rectangular schematic symbols with hatched/cross-hatched fill accents and corner
tick marks. Connectors: strict orthogonal Manhattan-style routing, right-angle bends only, open arrowhead.

**Motion affinity.** `dash-flow`, `connection-draw-in`, `heartbeat`, `state-transition-arrow`, `replication-sync`, `failover-reroute`, `batch-tick`, `queue-fill`, `scale-out-spawn`, `packet-travel`, `stream-continuous`, `error-propagation`, `node-boot-sequence`.
`replication-sync`.

**Runtime.** `css-only`, no CDN dependency — safe for both `local` and `artifact` targets.

**Techniques.** `repeating-linear-gradient` for the grid background, `stroke-dasharray` for hatched
fill accents.

**Dark mode.** Native (this style's default is already dark navy).

**Accessibility.** High native contrast (cyan-on-navy). Grid lines kept under 20% opacity so they never
compete with strokes. Monospace aids alignment for screen magnifiers.

**Best for.** Hardware schematics, electrical/network diagrams, formal spec documents, RFC-style docs.
**Avoid for** casual brainstorms, consumer-facing marketing pages, playful storytelling flows.

---

## neon-dark

**Template Status.** shipped — `templates/base/neon-dark.html`.

**Visual DNA.** Thin bright strokes with an outer glow (2px core line plus blurred glow halo).
Near-black fill with translucent neon tint on active nodes. Cyan, magenta, lime on pure black
(`#000`); high saturation, high contrast, futuristic (cyberpunk/synthwave/DevOps mood).

**Fonts.** `Orbitron` (headers), `Space Mono` / `JetBrains Mono` (body labels), fallback
`ui-monospace, monospace`.

**Stroke / fill.** Dark panel with a neon border glow; icon glyph rendered in the accent neon color.
Connectors: glowing stroke with a `drop-shadow` halo, animated pulse along active paths.

**Motion affinity.** `pulse-glow`, `dash-flow`, `heartbeat`, `error-propagation`, `packet-travel`, `failover-reroute`, `stream-continuous`, `fanout-broadcast`, `scale-out-spawn`, `ttl-expiry`, `round-trip`, `retry-loop`.
`error-propagation`, `packet-travel`.

**Runtime.** `css-only`, no CDN dependency — safe for both `local` and `artifact` targets.

**Techniques.** `filter: drop-shadow` for glow, `text-shadow` layering; `prefers-reduced-motion` swaps
flicker for a static glow.

**Dark mode.** Native (pure black is the only mode).

**Accessibility.** Glow filters must not reduce text contrast below 4.5:1. Provide a reduced-motion
static-glow fallback. Avoid pure color-only status signaling — pair neon color with a label or icon.

**Best for.** Conference demos, DevOps infra maps, dark-themed dashboards, tech marketing. **Avoid
for** print/paper deliverables, accessibility-first public docs, low-power mobile devices at scale.

---

## isometric-2.5d

**Template Status.** shipped — copy `templates/base/isometric-2.5d.html` and substitute between its markers.

**Visual DNA.** Clean 1.5px outline on each 3D face, consistent 30-degree edge angles. Three-tone flat
shading per block (top/left/right face) to fake depth, no gradients. Cool blues/grays for infra
blocks, warm accent per service tier.

**Fonts.** `Inter`. Labels kept horizontal, never skewed with the block.

**Stroke / fill.** Extruded 3D block per component using CSS 3D transforms (`rotateX`/`rotateY`),
stacked for depth. Connectors: isometric-projected lines following the same 30-degree grid,
arrowhead flattened to match perspective.

**Motion affinity.** `dash-flow`, `packet-travel`, `connection-draw-in`, `node-boot-sequence`, `scale-out-spawn`, `pulse-glow`, `queue-fill`, `replication-sync`, `batch-tick`, `stream-continuous`.

**Runtime.** `css-only`, no CDN dependency.

**Techniques.** `CSS 3D transforms` (`transform-style: preserve-3d`, `rotateX`/`rotateY`) built from
flat SVG faces — no WebGL.

**Dark mode.** Supported.

**Accessibility.** 3D perspective must not be the only cue for hierarchy; keep labels horizontal and
readable; face-shading contrast must meet AA against labels.

**Best for.** Cloud infrastructure topology, deployment diagrams, presentation slides. **Avoid for**
sequence/request-response flows, diagrams needing more than ~25 nodes, text-heavy specs.

---

## glassmorphic

**Template Status.** shipped — copy `templates/base/glassmorphic.html` and substitute between its markers.

**Visual DNA.** Thin translucent white border (1px, 20–30% opacity) outlining each panel.
`backdrop-filter` blur with 10–30% opacity color tint, layered semi-transparent panes. Soft pastel
tints over a vivid blurred background gradient — airy, premium, modern.

**Fonts.** `Inter` or an SF-Pro-style sans-serif, medium weight for legibility over blur.

**Stroke / fill.** Rounded glass card with `backdrop-filter: blur(10px)` and a subtle inner highlight.
Connectors: soft translucent line with a light glow, subtle drop-shadow for depth separation.

**Motion affinity.** `pulse-glow`, `queue-fill`, `fanout-broadcast`, `ttl-expiry`, `dash-flow`, `packet-travel`, `heartbeat`, `cache-hit-miss`, `connection-draw-in`, `state-transition-arrow`.

**Runtime.** `css-only`, no CDN dependency.

**Artifact-safe fallback.** `backdrop-filter` is CSS-only and CSP-safe, so this style already works in
an artifact — but some older headless renderers lack `backdrop-filter` support; provide a solid-fill
`rgba()` panel as the `@supports not (backdrop-filter: blur(1px))` fallback.

**Dark mode.** Supported.

**Accessibility.** `backdrop-filter` blur can reduce text contrast — test the `On Color` token against
the actual blurred backdrop, not just the `Fill` token.

**Best for.** Premium product UI overlays, card-based architecture views, modal/overlay-style
diagrams. **Avoid for** low-power mobile targets, print output, diagrams needing crisp small text.

---

## ascii-terminal

**Template Status.** shipped — copy `templates/base/ascii-terminal.html` and substitute between its markers.

**Visual DNA.** Unicode box-drawing characters form all lines; no vector strokes. No fill — interior
is whitespace or repeated fill characters. Monochrome, single foreground color on terminal background,
optional ANSI accent colors.

**Fonts.** Monospace only — `JetBrains Mono`, `IBM Plex Mono`, or the system terminal font
(fallback: `ui-monospace, monospace`). Fixed-width grid alignment.

**Stroke / fill.** Box-drawn rectangle built from box-drawing characters wrapping the label text.
Connectors: box-drawing line/arrow characters routed on a fixed character grid.

**Motion affinity.** `batch-tick`, `stream-continuous`, `state-transition-arrow`, `heartbeat`, `dash-flow`, `packet-travel`, `queue-fill`, `node-boot-sequence`, `retry-loop`.

**Runtime.** `css-only`, no CDN dependency.

**Techniques.** `white-space: pre` for the fixed-width grid; text color transitions via opacity for
tick/stream motion.

**Dark mode.** Native (terminal black `#0c0c0c` is the default).

**Accessibility.** Best-in-class screen-reader support since content is real text. Box-drawing
characters need adequate `line-height` so glyphs don't visually merge.

**Best for.** README docs, code comments, terminal UIs, lightweight version-controlled specs. **Avoid
for** visually rich presentations, diagrams needing color-coded roles, non-technical audiences.

---

## pixel-retro

**Template Status.** shipped — copy `templates/base/pixel-retro.html` and substitute between its markers.

**Visual DNA.** No anti-aliasing; hard-edged 2–4px stepped outlines; `image-rendering: pixelated`.
Flat blocky fills from a limited 16–256 color palette, dithered gradients where shading is needed.
Saturated primary colors reminiscent of 1980s–90s consoles.

**Fonts.** Pixel bitmap font, e.g. `Press Start 2P` (fallback: monospace). All-caps short labels.

**Stroke / fill.** Blocky sprite-style rectangle built from a fixed pixel grid, chunky 4x4-minimum
block size. Connectors: stepped stair-line connectors, no diagonals, pixel-grid-aligned.

**Motion affinity.** `dash-flow`, `pulse-glow`, `packet-travel`, `queue-fill`, `batch-tick`.

**Runtime.** `css-only`, no CDN dependency.

**Techniques.** `image-rendering: pixelated`; `animation-timing-function: steps()` for chunky stepped motion.

**Dark mode.** Supported.

**Accessibility.** Small pixel fonts can fail minimum text size — provide a larger label overlay or
tooltip. Keep `steps()` animation timing predictable for motion-sensitive users.

**Best for.** Educational content, game-dev architecture, nostalgia-themed demos, indie community
content. **Avoid for** formal enterprise docs, dense diagrams needing fine text, accessibility-critical
audiences.

---

## metro-map

**Template Status.** shipped — copy `templates/base/metro-map.html` and substitute between its markers.

**Visual DNA.** Thick uniform-width colored lines (route lines) with rounded line joins at stops.
Solid color per route line; stops rendered as filled or ring-outline circles. Distinct saturated color
per route for quick visual differentiation, light neutral background.

**Fonts.** `Inter` or a Helvetica-style sans-serif. Stop labels set perpendicular or alongside the line.

**Stroke / fill.** Circular stop markers at line intersections/endpoints; interchange stops use larger
ring markers. Connectors: route line runs continuously through stops, 45/90-degree bends only,
transit-map style simplification.

**Motion affinity.** `dash-flow`, `packet-travel`, `replication-sync`, `failover-reroute`, `stream-continuous`.

**Runtime.** `css-only`, no CDN dependency.

**Techniques.** `stroke-linejoin: round` for line joins; `stroke-dashoffset` for travel-along-route motion.

**Dark mode.** Supported.

**Accessibility.** Route color must be paired with a route label or legend, never color alone.
Interchange stops need a distinct shape, not just a larger size.

**Best for.** Data pipeline routes, bioinformatics workflows, network topology overviews, multi-path
routing stories. **Avoid for** precise geographic accuracy, single-linear sequence flows, dense
component-level detail.

---

## comic-storytelling

**Template Status.** shipped — copy `templates/base/comic-storytelling.html` and substitute between its markers.

**Visual DNA.** Bold 3–4px outlines with slight ink-brush variation on panel borders and speech
bubbles. Flat cel-shaded fills with occasional halftone dot pattern for shading. Bright, high-energy
comic-book palette with bold primary colors and black ink outlines.

**Fonts.** A comic lettering font, e.g. `Bangers`, for speech bubbles; clean sans-serif for technical
labels.

**Stroke / fill.** Component drawn inside a speech-bubble or panel frame, tail points toward the
acting node. Sequential panel grid with white gutters between panels. Connectors: bold directional
arrow with a motion-line flourish, panel-to-panel sequence implied left-to-right.

**Motion affinity.** `connection-draw-in`, `pulse-glow`, `state-transition-arrow`, `fanout-broadcast`, `node-boot-sequence`.

**Runtime.** `css-only`, no CDN dependency.

**Techniques.** `clip-path` for the speech-bubble tail shape; `animation-delay` stagger to reveal
panels in sequence.

**Dark mode.** Not recommended — comic palette relies on bright paper-white gutters.

**Accessibility.** Speech-bubble text must remain real selectable text, not baked into artwork.
Sequential panel order needs explicit reading-order via DOM order or `aria-flowto`.

**Best for.** Onboarding walkthroughs, tutorial flows, user journey maps, non-technical stakeholder
narratives. **Avoid for** formal architecture review docs, dense multi-service topologies, enterprise
compliance decks.

---

## Cross-style rendering rule (all styles)

Regardless of style, class names and CSS custom-property names are identical across every template —
only token *values* and the SVG `<defs>` differ. Colors, spacing, and timing values always come from
`:root` custom properties, never hardcoded in element styles, so a diagram can be re-skinned by
swapping the token block. See `data/color-semantics.csv` for the per-style, per-role token values
(`--color-<role>-fill`, `-stroke`, `-accent`, `-on`, and `-dark-*` variants) and
`pre-delivery-checklist.md` for the contrast gate on those tokens.

## hud-monochrome

**Name.** HUD Monochrome. **Aliases.** fui, hud, tron, sci-fi-hud, mission-control, linear-dark.

**Essence.** Sci-fi HUD / FUI: midnight navy, ONE electric-cyan hue doing every job, hairline 1px
strokes, glass cards, mono status chips. The discipline is the aesthetic — resist adding hues.

**Tokens.** Canvas `#0d1420` (single-theme, `Dark Mode: native` — no media query, no data-theme
stamps; paint every colour explicitly). Panels `#13202e`. Cyan family: stroke `#67e8f9`, accent
`#22d3ee`, on-colour `#e0f2fe`, muted `#7da2b8`. The one exception: `error` strokes `#fbbf24` /
accent `#f59e0b` / on `#fef3c7` (amber alarm). Grid: 44px hairlines at 6% cyan.

**Role encoding — the defining rule.** All seven roles share the cyan palette, so **colour carries
no role meaning and no colour legend is rendered** (the legend requirement is waived for
deliberately monochrome styles — see the pre-delivery checklist). Role lives in the label, the
shape, and the mono status chips (`ACTIVE`, `LIVE`, `BUFFERING`…). Async stays dashed; error is
amber *plus* long-short dash, never amber alone.

**Typography.** Inter for node labels; JetBrains Mono for edge labels, chips, subs and data
readouts. Chips: 9px mono, `letter-spacing .08em`, uppercase.

**Rendering rules.** Node borders at `stroke-opacity .55`; only `.node--primary` gets full opacity
plus a soft `drop-shadow` glow — one glowing node per diagram, it marks the busy component. Edges at
`.55` opacity, primary `.9`. Keep `drop-shadow` off everything else; the glow budget is one node.

**Motion affinity.** dash-flow, packet-travel, pulse-glow, queue-fill, heartbeat,
connection-draw-in, node-boot-sequence, camera-beat. This style is the natural home of beats mode —
the HUD look reads as a mission-control camera by default.

**Artifact-safe.** `css-only`, zero CDN scripts; Google Fonts only. **Template Status.** shipped
(`templates/base/hud-monochrome.html`).
