---
name: stitch-prompt-engineering
description: Standards and prompt engineering patterns for Google Stitch MCP to generate high-fidelity mobile and desktop screens matching existing design systems without visual artifacts or blown-up canvases.
---

# Google Stitch MCP Prompt Engineering Guide

## Overview

Google Stitch is an AI-powered design generation system capable of generating pixel-perfect HTML/CSS screens and UI designs via Gemini. However, unconstrained or vague prompts often cause Stitch to hallucinate standalone desktop graphic banners (e.g. 1280x2864 or 2560x5742), render oversized clip-art icons, or default to generic white canvases.

This skill defines the mandatory prompt engineering structure, design system binding rules, and anti-hallucination guardrails required to generate consistent, production-grade screens on Stitch.

---

## 1. The Anatomy of a High-Fidelity Stitch Prompt

Every prompt sent to Stitch `generate_screen_from_text` or `edit_screens` must follow this 5-part architecture:

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

### Template Structure

```markdown
[Device Viewport Frame & Role Context]
A high-fidelity [MOBILE/DESKTOP] application screen ([390px mobile viewport / 1440px desktop], [Platform e.g. iPhone standard], [Theme e.g. Spartan Dark Obsidian]) for [Project Name]: "[Screen Title]".

[Theme & Styling Tokens]
- Background: Solid dark obsidian #0B0F15 and surface #10141A.
- Accent Palette: Primary #38BDF8 (Radiant Ice Cyan), Secondary #00F0FF (Electric Cyan), Tertiary #A3E635 (Kinetic Lime), Warning #EA580C (Ember Orange).
- Typography: Sora (Headlines, display stats, numeric tabular-nums) and Manrope (Body text, captions).
- Surfaces & Elevation: Frosted glassmorphism panels (rgba(18, 24, 36, 0.75)), backdrop-filter blur(16px), subtle hairline border (1px solid rgba(56, 189, 248, 0.25)).

[Layout Hierarchy (Top-to-Bottom)]
1. Top Chassis (Mobile Status Bar & Header):
   - Native status bar: 09:41, WiFi, Battery indicator.
   - Header: User greeting, dynamic gamified streak badge ("🔥 18 NGÀY"), milestone pill ("DAY 18 / 100").
2. Hero Section:
   - Primary focus card (e.g. Daily Stoic Motivation Card with real quote copy, author pill, action triggers).
3. Core Data & Interactive Matrix:
   - Structured vertical cards or grid items with real metrics, XP rewards, active toggle switches, and progress rings.
4. Summary / Telemetry Metric Banner:
   - Daily score, completion percentage, or competitive leaderboard tier chip.
5. Bottom Navigation / Action Bar:
   - Fixed docked 4-tab bar (Home, Leaderboard, Journal, Profile) with active state glow.

[Anti-Hallucination & Quality Rules]
- Strictly mobile 390px layout. Do NOT generate a desktop banner or freeform poster.
- Zero oversized clip-art shapes, zero raw black/white vector drawings.
- Use polished micro-typography, crisp Material/Phosphor icon glyphs, and real Vietnamese/English domain copy.
```

---

## 2. Critical MCP Parameters

When invoking `generate_screen_from_text` via Stitch MCP, ALWAYS provide these parameters:

| Parameter | Type | Value | Why It Is Mandatory |
| :--- | :--- | :--- | :--- |
| `projectId` | String | e.g. `"3529453464823562204"` | Stitch project ID without `projects/` prefix. |
| `designSystem` | String | e.g. `"assets/7f97cbfe467240289e5eb6fe8f1ea964"` | **CRITICAL**. Omitting this causes Stitch to ignore project tokens and default to generic white palettes. |
| `deviceType` | String | `"MOBILE"` or `"DESKTOP"` | Locks the target viewport ratio. For mobile apps, always set `"MOBILE"`. |
| `modelId` | String | `"GEMINI_3_8_FLASH"` | Uses Gemini 3.8 Flash for high-speed, high-fidelity UI rendering. |
| `prompt` | String | Detailed structured prompt | Must contain full viewport and component breakdown. |

---

## 3. Why Stitch Prompts Fail & How to Fix Them

### Failure Mode 1: Component Prompt vs Full Screen
- **Problem**: Prompting `"Daily Stoic Motivation Quote Card component"` makes Stitch think you want an isolated graphic illustration. It renders a 1280x2864 canvas with massive clip-art shapes.
- **Fix**: Always frame the prompt as a **complete mobile screen** with the component embedded as the Hero card inside a 390px mobile container with status bar and navigation.

### Failure Mode 2: Missing `designSystem` Parameter
- **Problem**: When `designSystem` is omitted, the model generates arbitrary random colors and light-mode backgrounds.
- **Fix**: Inspect existing design systems via `list_design_systems` or `get_project`, grab the asset ID (e.g. `assets/...`), and pass it explicitly.

### Failure Mode 3: Placeholder Copy & Empty Containers
- **Problem**: Using phrases like `"A card with some motivation text and some habits"` produces generic "Lorem Ipsum" and empty gray boxes.
- **Fix**: Write **verbatim copy** in the prompt (e.g. Marcus Aurelius quote in Vietnamese and English, specific habit names like "Dậy sớm 05:00 AM", XP rewards like "+25 XP").

---

## 4. Design System Token Reference (Spartan Dark / Winter Arc)

For projects using the **Spartan Dark Obsidian** theme:

- **Foundation**: Solid `#0B0F15` or `#10141A`.
- **Card Fill**: `rgba(18, 24, 36, 0.70)` to `rgba(27, 34, 52, 0.85)` with `backdrop-filter: blur(16px)`.
- **Borders**: `1px solid rgba(56, 189, 248, 0.20)` (Ice Cyan) or `1px solid rgba(255, 255, 255, 0.08)`.
- **Accent Glow**: `box-shadow: 0 0 16px rgba(56, 189, 248, 0.45)`.
- **Fonts**: `Sora` for headers/scores, `Manrope` for body/descriptions.
- **Mobile Viewport**: Base width `390px` (renders as `780px` retina @2x).
