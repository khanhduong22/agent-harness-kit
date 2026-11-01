# Scroll-Craft & Universal Motion Design (`nateherkai/scroll-craft` + `LottieFiles/motion-design-skill`)

Synthesized from [`nateherkai/scroll-craft`](https://github.com/nateherkai/scroll-craft) (`★ 4.3k+`) and [`LottieFiles/motion-design-skill`](https://github.com/LottieFiles/motion-design-skill) (`★ 2.6k+`). Load this reference when building scrollytelling landing pages, dimensional layered heroes, micro-interactions, or choreographed UI animations.

---

## 1. Scroll-Craft: Narrative Journey & Dimensional Hero Layering

### 1.1 The 6-Beat Scrollytelling Spine
Never build a landing page where 5 sections repeat the same centered heading + 3-card grid. Map the page to a **6-Beat Emotional Curve** where **no two adjacent sections use the same scroll device**:

| Beat | Visitor State Shift | Recommended Scroll Device |
|---|---|---|
| **1. Recognition** | Visitor sees their exact problem/world immediately | **Dimensional Layered Hero** (3–4 independent depth planes) |
| **2. Tension** | The concrete cost of the status quo, named plainly | **Pin + Kinetic Ledger** (copy/metrics assemble while frame holds) |
| **3. Turn** | The core mechanism or breakthrough that changes state | **Interactive State Wipe / Live Diff Reveal** |
| **4. Substance** | Why the engineering/product holds up under scrutiny | **Macro Inspection / Interactive Architecture Explorer** |
| **5. Range** | What they can configure, explore, or choose | **Lateral Pan / Tabbed Matrix** (lateral reads as options; vertical reads as argument) |
| **6. Commitment** | One decisive action with zero competing clutter | **Calm Static Close** (page stops moving and responds to pointer) |

### 1.2 Dimensional 4-Plane Hero Architecture
A flat background image with faded text on top is not a studio hero. Construct flagship heroes with **3 to 4 depth planes**:
1. **Plane 0 (Background Plate)**: Environment/grid/canvas moving at `0.85x` scroll rate.
2. **Plane 1 (Typography / Display Layer)**: Crisp `h1` (`<= 2 lines`) anchored with guaranteed contrast scrim.
3. **Plane 2 (Primary Subject / Interactive Artifact)**: Real product UI fragment or alpha cutout with subtle occlusion over Plane 1's edge (`1.0x` scroll rate).
4. **Plane 3 (Foreground / Ambient Detail)**: Subtle telemetry indicator, lighting grain, or live cursor response (`1.08x` scroll rate).
- **Mandatory Reduced-Motion Fallback**: Under `@media (prefers-reduced-motion: reduce)`, lock all plane transforms to their composed static resting frame (`transform: none !important`).

---

## 2. Universal Motion Design System (`LottieFiles`)

### 2.1 Choose ONE Motion Personality Per Project

| Archetype | Duration Range | Signature Easing (`cubic-bezier`) | Overshoot | Best For |
|---|---|---|---|---|
| **Corporate / SaaS** | `180–350ms` | `cubic-bezier(0.2, 0, 0, 1)` | `0–3%` | Dashboards, IDEs, FinTech, Enterprise tools |
| **Premium / Editorial** | `350–600ms` | `cubic-bezier(0.4, 0, 0.2, 1)` | `0%` | Luxury brands, Engineering Monographs, Portfolios |
| **Playful / Consumer** | `150–300ms` | `cubic-bezier(0.175, 0.885, 0.32, 1.275)` | `10–20%` | Consumer apps, Onboarding celebrations, Games |
| **Energetic / Launch** | `100–250ms` | `cubic-bezier(0.16, 1, 0.3, 1)` | `10–15%` | High-tempo product launches, Reels |

### 2.2 Deterministic Duration & Directional Easing Table

| UI Element | Duration | Easing Direction Rule |
|---|---|---|
| **Hover / Tooltip micro-feedback** | `80–120ms` | Instant response (`ease-out`) |
| **Button press / Toggle switch** | `120–180ms` | Scale `0.97` on press (`50ms`), settle `1.0` (`150ms`) |
| **Card / Drawer entrance** | `220–350ms` | **Decelerate (`ease-out`)**: fast entry, gentle landing |
| **Card / Drawer exit** | `150–250ms` | **Accelerate (`ease-in`)**: exits 30% faster than entrances |
| **Modal / Page transition** | `300–500ms` | Smooth `ease-in-out` (`cubic-bezier(0.2, 0, 0, 1)`) |

### 2.3 The 4 Cardinal Laws of Motion Quality
1. **Never use `linear` easing for spatial movement** (`linear` is strictly for continuous spinners or progress bars).
2. **Never use `opacity` alone for primary state changes** — pair opacity with a subtle `12–20px` `translateY` or `0.98 -> 1.0` `scale`.
3. **The `1/3` Choreography Rule**:
   - With 3+ elements on screen, **no more than 1/3 may be in active autonomous motion simultaneously**.
   - **Total Stagger Ceiling**: Cascade delays (`30–60ms` per item) must complete within **`< 450ms` total** so the UI never feels sluggish.
4. **GPU Compositor Only**: Animate `transform` (`translate3d`, `scale`, `rotate`) and `opacity` exclusively — never animate `top`, `left`, `width`, `height`, or `box-shadow` on scroll.
