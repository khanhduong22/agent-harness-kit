---
name: est-point
description: "Use when estimating Story Points for User Stories, Tasks, Subtasks, or Bugs under the TechPulse 2026 Engineering Standard (1 Point = 1 Standard Day, Junior 1.0x / Senior 0.5x, Learning Curve 1.0x / 0.7x / 0.4x, 0.2 - 3.0 Point benchmark table, synced with github-task-breakdown for GitHub Projects V2). Triggers on 'est point', 'story point', or 'calculate point'."
license: MIT
metadata:
  version: 2.1.0
  author: TechPulse Engineering & Architecture Team
  category: agile-engineering
  domain: task-estimation
  tags: [story-point, agile, scrum, estimation, techpulse, sprint-planning, standard-day]
---

# EST POINT — TechPulse 2026 Operating Standard (`1 Point = 1 Standard Working Day`)

Standardized engineering estimation framework for **Story Points** governed by the **[TechPulse 2026 Operating Standard](https://docs.google.com/presentation/d/15YZOTSmp-PWgte3DsmVwN01hmZzXV0w32INu84Lt0ug/edit?slide=id.p2#slide=id.p2)** (*Productivity & Performance Measurement Guide*).

---

## 1. Philosophy & Foundational Baseline (Slide 2)

1. **The Nature of Story Points:** Points measure **problem complexity**, technical scope, and architectural risk—not administrative timesheets or pure man-hours.
2. **Foundational Baseline (`TechPulse Baseline`):**
   $$\text{1.0 Point} = \text{1 Standard Working Day}$$
   - **`1.0 Point`** represents the baseline scope and complexity an engineer completely delivers in **1 normal working day**.
   - **NEVER** use an integer Fibonacci scale starting at 1 (`1, 2, 3, 5, 8...`) for minor tasks (assigning `1.0 - 2.0 Points` to a 1–2 hour bugfix completely distorts the 1 standard day baseline).
3. **Standardized Decimal Scale (`TechPulse Standard Point Scale`):**
   - Standard benchmark increments:
     `[0.2, 0.25, 0.3, 0.4, 0.5, 0.7, 1.0, 1.5, 2.0, 2.5, 3.0]`
4. **Role 01 — Point Governance (ETA Validation & Approval - Slide 5):**
   - **Task History Audit:** Review whether the engineer has executed similar tasks before to reduce points according to the **Learning Curve**.
   - **Level-Based Approval:** Allocate points based on engineering seniority: **Junior (`1.0x`)** vs. **Senior (`0.5x`)**.
5. **Role 02 — Epic as a Feature & Anti-Double Counting (Slide 5):**
   - **Anti-Fragmentation:** Do not fracture tasks into trivial micro-slices just to inflate count. Every estimated task must deliver tangible feature value.
   - **Single-Tier Accounting (`No Double Counting`):** Points are recorded **strictly on leaf execution sub-issues** (or standalone issues without sub-issues). If a parent Epic/Story is decomposed into estimated sub-issues, the parent must set `Point Est = null / 0` (or purely summary aggregation) to prevent double counting.

---

## 2. Conversion Multipliers by Level & Learning Curve (Slide 2 & Slide 3)

### A. Seniority Level Multipliers (Slide 2)
| Seniority Level | Level Multiplier | Example Task A (Basic Login / CRUD Feature) | Description |
| :--- | :---: | :---: | :--- |
| **Junior Level** | `1.0x` | **`1.0 Point`** | Unfamiliar domain, requires onboarding / ramp-up |
| **Senior Level** | `0.5x` | **`0.5 Point`** | Domain mastery, existing architecture, blueprints & templates |

### B. Productivity Optimization via Experience — Learning Curve (Slide 3)
| Execution Frequency | Learning Curve Multiplier | Example CRUD API Module (1.0 Pt Baseline) | Description |
| :--- | :---: | :---: | :--- |
| **1st Time (New Task)** | `1.0x` | **`1.0 Point`** | Building the CRUD module for the first time |
| **2nd Time (Similar Task)** | `0.7x` | **`0.7 Point`** | Equivalent CRUD module for another domain entity |
| **3rd+ Time (Standardized)** | `0.4x` | **`0.4 Point`** | Reusing established templates, components, and automated scripts |

> **Standard TechPulse Point Calculation Formula:**
> $$\text{Point} = \text{Junior Base Point} \times \text{Level Factor} \times \text{Learning Curve Factor}$$
> *(Or look up directly from the **Mandatory Task Pricing Benchmark Table** in Section 3 below).*

---

## 3. Mandatory Task Pricing Benchmark Table (Slide 6 — PM & Tech Lead)

This is the **mandatory reference benchmark** from Slide 6 of the TechPulse 2026 Operating Standard:

| Task Category | Complexity | Junior Point (1st) | Senior Point (1st) | 2nd+ (Repeat / Template Available) |
| :--- | :---: | :---: | :---: | :---: |
| **1. Standard Bugfix / Minor Refactoring / Small UI-CSS-Layout Tweak** | Low | **`0.5 Point`** | **`0.25 Point`** | **`0.2 Point`** |
| **2. Basic CRUD API / Simple Form / 1 UI Section or Component** | Low | **`1.0 Point`** | **`0.5 Point`** | **`0.3 - 0.4 Point`** |
| **3. Payment Gateway / Third-party Integration / Full Page + API / Multi-flow** | Medium | **`2.0 Points`** | **`1.0 Point`** | **`0.7 Point`** |
| **4. Architectural Optimization / Core Service System / Complex Engine** | Very High | *Not Assigned* | **`2.0 - 3.0 Points`** | **`1.5 Points`** |

---

## 4. Role-Specific Casebook Catalog (`1 Point = 1 Standard Working Day`)

### A. Frontend Development (`FE`)
| Code | Work Case | Junior (1st) | Senior (1st) | 2nd+ (Repeat) | Standard Conditions / Scope Boundary |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `FE-01` | Copy, label, link, color, spacing, hide scrollbar | `0.5` | **`0.25`** | **`0.2`** | UI tweak / CSS / no architecture changes |
| `FE-02` | Add Button / Input / Pill Tab / Header aligned with Figma | `0.5` | **`0.25`** | **`0.2`** | Design System available |
| `FE-03` | Simple Modal / Popup / Bottom Sheet | `1.0` | **`0.5`** | **`0.3 - 0.4`** | Design and foundation components exist |
| `FE-04` | Dark Mode for 1 Section / Component (Home / Profile) | `1.0` | **`0.5`** | **`0.3 - 0.4`** | 1st: `0.5 pt` (Senior); subsequent repeat sections: `0.3 pt` |
| `FE-05` | Data Entry Form / CRUD UI (Alerts, Watchlist) | `1.0` | **`0.5`** | **`0.3 - 0.4`** | Validation, submit, loading, error states |
| `FE-06` | Listing Page / Detail Page / Data Table with API | `1.0` | **`0.5`** | **`0.4`** | Existing API, pagination, empty/loading states |
| `FE-07` | Complex Flow / Multi-condition Filter / State Matrix (e.g. 13 Notification flows, Featured Stocks Full Page) | `2.0` | **`1.0`** | **`0.7`** | Multi-state, complex filter/sort/routing or new API integration |
| `FE-08` | Realtime UI Architecture / WebSocket / Core State Engine | — | **`2.0`** | **`1.5`** | WebSocket, reconnect, multi-channel state sync |

### B. Backend & Database Development (`BE` / `DB`)
| Code | Work Case | Junior (1st) | Senior (1st) | 2nd+ (Repeat) | Standard Conditions / Scope Boundary |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `BE-01` | Add DB field / adjust query / minor API mapping, sort, or filter | `0.5` | **`0.25`** | **`0.2`** | Simple migration, single endpoint |
| `BE-02` | Basic CRUD API / Event Listener (e.g. `@mention` notification, Watchlist CRUD) | `1.0` | **`0.5`** | **`0.3 - 0.4`** | Validation, unit tests, full error handling |
| `BE-03` | Third-Party Integration / Multi-channel Notification (In-App + Email + Telegram) / Aggregation API | `2.0` | **`1.0`** | **`0.7`** | Multi-service connectivity, webhooks, multi-table joins |
| `BE-04` | Core Service System / Worker Engine / Dockerfile & Architecture Optimization / Multi-Portfolio NAV Engine | — | **`2.0 - 3.0`** | **`1.5`** | Core architecture, cron/worker matching, high throughput |

### C. Bug Fixing & Refactoring (`BUG`)
| Code | Work Case | Junior (1st) | Senior (1st) | 2nd+ (Repeat) | Standard Conditions / Scope Boundary |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `BUG-01` | Fix UI Bug / CSS / Layout / Link / Modal auto-close / Scrollbar | `0.5` | **`0.25`** | **`0.2`** | Scoped to 1–2 FE components |
| `BUG-02` | Medium Logic Bug / API mapping / Zustand cache tab / Mozyfin fallback | `0.5 - 1.0` | **`0.25 - 0.5`** | **`0.2 - 0.3`** | State management or FE & API data contract reconciliation |
| `BUG-03` | Fullstack Bug (FE + BE) / Multi-module sync (e.g. 3 Community tabs FE+BE, Market Index sync) | `1.0 - 2.0` | **`0.5 - 1.0`** | **`0.4 - 0.7`** | Touches both FE and BE or multiple asynchronous data flows |
| `BUG-04` | Race Condition / Data Loss / Core Architectural Bug | — | **`1.5 - 2.0`** | **`1.0`** | Requires deep diagnostic tracing and strict data integrity guarantees |

---

## 5. Productivity Assessment Model Across Timeframes (Slide 4)

Productivity across a Sprint or Month is evaluated based on the correlation between **Total Story Points** and **Number of Completed Tasks** (measured against a standard 5-day work week baseline $\approx 5.0\text{ Points}$):
- **Scenario 1 — Low Productivity:** Accumulated points fall well below timeframe expectations $\rightarrow$ *Requires coaching & technical support*.
- **Scenario 2 — Increasing Efficiency:** Total points remain consistent with previous cycles, but **task volume increases** (due to the Learning Curve reducing points on standardized tasks) $\rightarrow$ *Demonstrable performance improvement*.
- **Scenario 3 — High Outperformance:** Both **total points** and **completed task volume** increase substantially $\rightarrow$ *Commendation & recognition*.

---

## 6. CLI Support Tool (`scripts/estimate.js`)

```bash
# 1. Search Casebook catalog by keyword
node ~/.gemini/config/skills/est-point/scripts/estimate.js search "crud"

# 2. List all cases by domain group (frontend, backend, bug)
node ~/.gemini/config/skills/est-point/scripts/estimate.js list

# 3. Calculate points under TechPulse 2026 standards (JuniorBasePoint, Level [senior|junior], Repeat [1|2|3])
node ~/.gemini/config/skills/est-point/scripts/estimate.js calc 1.0 senior 1
# Output: {"juniorBasePoint": 1, "level": "senior", "repeatCount": 1, "rawPoint": 0.5, "standardPoint": 0.5}

node ~/.gemini/config/skills/est-point/scripts/estimate.js calc 0.5 senior 2
# Output: {"juniorBasePoint": 0.5, "level": "senior", "repeatCount": 2, "rawPoint": 0.18, "standardPoint": 0.2}
```

---

## 7. Synchronization with `github-task-breakdown` & GitHub Projects V2

When creating or updating Tasks, Sub-issues, or Bugs on GitHub Projects V2 (`Index` — `PVT_kwDODcsuC84BDOQk`):
1. **Apply the Standard `1 Point = 1 Standard Working Day` Baseline**:
   - For **Senior Developer (`khanhduong22`)**:
     - Minor UI / CSS / Layout Bug (`BUG-01`, `FE-01`): **`0.2 - 0.25 Point`**
     - Logic Bug / API mapping / Repeated Dark Mode section (`BUG-02`, `FE-04 repeat`): **`0.3 - 0.4 Point`**
     - Standard CRUD API / Form / Feature / Fullstack Bug (`BE-02`, `FE-05`, `BUG-03`): **`0.5 Point`**
     - Medium-Large Feature / 13 Notification flows / Full API-connected New Page (`FE-07`, `BE-03`): **`0.7 - 1.0 Point`**
     - Core Engine / Major Architectural System (`BE-04`): **`1.5 - 2.0 Points`**
2. **Prevent Double Counting on Parent Stories (`No Double Counting`)**:
   - When a parent Issue (e.g. `#3881`, `#3924`, `#3929`, `#3996`, `#3999`, `#4016`) is decomposed into sub-issues, points must be recorded strictly on the **leaf execution sub-issues**. Set parent `Point Est` / `Point Act` to `null` to avoid double-counting.
3. **Synchronize with GitHub Projects V2 Fields**:
   - **`Point Est`** (`PVTF_lADODcsuC84BDOQkzhoOFI0`, `NUMBER`): Standard decimal increments (`0.2`, `0.25`, `0.3`, `0.5`, `0.7`, `1.0`, `1.5`, `2.0`).
   - **`Point Act`** (`PVTF_lADODcsuC84BDOQkzhoOFJM`, `NUMBER`): Populated when task transitions to `Ready for QA` / `Done`.
4. **Distinguish Morning Planning Cap (`Planned Cap`) vs. Actual Velocity (`Actual Delivery`)**:
   - The `<= 1.0 Point/day` (`0.9 - 1.0 Pt`) standard cap applies strictly to **morning pre-flight planning** (Morning Standup / Daily Report scope saturation).
   - When urgent bugs, production hotfixes, or ad-hoc tasks arise during the day, they are estimated at their true standalone engineering weight (`0.2 - 0.5+ Pt/task`) via `est-point`, **without being constrained or compressed by the 1.0 Pt planning ceiling**. Total actual delivered points (`Point Act`) for the day can naturally reach **`1.2 - 1.5+ Points`**.
