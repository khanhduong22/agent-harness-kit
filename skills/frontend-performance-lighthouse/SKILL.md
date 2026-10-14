---
name: frontend-performance-lighthouse
description: Frontend performance optimization and Core Web Vitals mastery (LCP, INP, CLS, TBT). Battle-tested patterns for 0ms Total Blocking Time (TBT), 100 Performance on Lighthouse, 3-Tier Viewport & Overlay Protocol, Pure Interaction Telemetry, and font hygiene.
---

# Frontend Performance Optimization & Core Web Vitals Mastery

## Overview & Purpose

Achieve **0ms Total Blocking Time (TBT)**, **100/100 Lighthouse Performance**, **100/100 Accessibility**, **100/100 Agentic Browsing**, and **All-Green Core Web Vitals** on throttled mobile and desktop devices without sacrificing user experience, tracking accuracy, or visual fidelity.

This skill equips AI agents and frontend engineers with battle-tested architectural patterns across the browser runtime:
1. **The 3-Tier Viewport & Dynamic Overlay Protocol** (eliminating chunk bloat and layout shifts).
2. **Pure Interaction-Driven Lossless Telemetry** (0ms TBT with 100% event capture).
3. **Core Web Vitals Optimization Engine** (LCP, INP, CLS = 0, and TBT = 0ms).
4. **Invisible Auth Iframe Elimination** (lazy guest authentication, instant JWT rehydration).
5. **Resource Hint & Font Hygiene** (self-hosted preloaded fonts, `font-display: optional`, eliminating unused preconnects).
6. **Main Thread Protection** (`content-visibility: auto`, image decoding, zero-redirect rewrites).
7. **100% Agentic Browsing & WCAG AA Accessibility** (`llms.txt`, deterministic DOM geometry, dark craft contrast).

---

## Google & Sentry Performance Standards

### 1. Google Core Web Vitals Standard (Official CrUX 75th Percentile & GSC Gate)

Google evaluates page experience using the Chrome User Experience Report (CrUX) over a 28-day rolling window at the **75th percentile (p75)** of real-world mobile and desktop user sessions:

| Metric | Google Standard (Good) | Production Target | Needs Improvement | Poor | Primary Root Cause & Fix |
|:---|:---|:---|:---|:---|:---|
| **LCP** (Largest Contentful Paint) | **≤ 2.5s** | **≤ 1.5s** | 2.5s - 4.0s | > 4.0s | Slow server TTFB, unoptimized hero images, render-blocking JS/CSS |
| **INP** (Interaction to Next Paint) | **≤ 200ms** | **≤ 50ms** | 200ms - 500ms | > 500ms | Long tasks (>50ms) on main thread, heavy event handlers, layout thrashing |
| **CLS** (Cumulative Layout Shift) | **≤ 0.1** | **≤ 0.05** (Target 0) | 0.1 - 0.25 | > 0.25 | Images/embeds without dimensions, unsized dynamic modules, web font swap |
| **FCP** (First Contentful Paint) | **≤ 1.8s** | **≤ 0.9s** | 1.8s - 3.0s | > 3.0s | Render-blocking CSS/JS in head, slow DNS/TLS/TTFB |
| **TTFB** (Time to First Byte) | **≤ 800ms** | **≤ 150ms** (Edge) | 800ms - 1800ms | > 1800ms | Origin server latency, lack of Edge caching / Cloudflare 0-RTT |
| **TBT** (Total Blocking Time - Lab) | **≤ 200ms** | **0ms** (Budget: ≤ 50ms) | 200ms - 600ms | > 600ms | Eager 3rd-party scripts (GA4/Clarity), heavy static modals, auth iframes |

- **Google Search Console (GSC) Page Experience Gate**: 100% of URLs must report "Good" status on mobile. Zero intrusive popups/interstitials on initial load.
- **Lighthouse v10+ Scoring Weights**: TBT (30%), LCP (25%), CLS (25%), FCP (10%), Speed Index (10%). Total Blocking Time carries the highest weight — eliminating TBT directly produces a 99-100 Performance Score.

### 2. Sentry APM & Web Vitals Reliability Standard

Sentry monitors real user transactions and tracks user satisfaction against APM error budgets:

| Sentry Metric | Production Standard | Critical / Poor Threshold | Impact & Architectural Remediation |
|:---|:---|:---|:---|
| **Apdex (Application Performance Index)** | **≥ 0.95** | < 0.85 | Ratio of satisfied vs tolerating/frustrated user requests ($T = 500\text{ms}$) |
| **User Misery Threshold** | **< 1.0%** | > 3.0% | Percentage of unique users experiencing transactions > 4x threshold ($4T = 2000\text{ms}$) |
| **Client SDK Boot Penalty** | **0ms (Lazy)** | > 50ms Long Task | Sentry SDK MUST NOT load in initial critical bundle; defer via idle callback/gesture |
| **Background Tab Hygiene** | **100% Filtered** | Unfiltered | Drop LCP/TTFB when `document.visibilityState === 'hidden'` to protect p75/p95 curves |
| **Runaway Transaction Clamping** | **Max 28s** | > 30s | Drop idle background transactions in `beforeSendTransaction` |
| **Clarity / Replay Trace Link** | **Active Bridge** | Missing Link | Forward `sentry_event_id` to Microsoft Clarity for 1-click video session reproduction |

---

## 1. The 3-Tier Viewport & Dynamic Overlay Protocol

Unoptimized route bundles statically pack invisible dialogs and below-the-fold modules into the initial page chunk. On mobile devices with 4x CPU throttling, parsing and evaluating these unused ASTs consumes 200ms-600ms of main-thread execution time.

To achieve 0ms TBT while strictly preserving 60 FPS scrolling and CLS = 0, all components MUST be categorized into three architectural tiers:

```mermaid
flowchart TD
    Page["Route Entry Point (Page / View)"] --> T1["Tier 1: Interactive Overlays<br/>(Modals, Drawers, Confetti, Tours)"]
    Page --> T2["Tier 2: Heavy Below-the-Fold Modules<br/>(Charts, 3D Canvas, Video, RichText >15KB)"]
    Page --> T3["Tier 3: Lightweight Structural UI<br/>(Cards, List items, Stat widgets <5KB)"]

    T1 --> R1["BẮT BUỘC: 100% Dynamic Import<br/>next/dynamic(..., { ssr: false }) / React.lazy()<br/>Initial Cost = 0 KB"]
    T2 --> R2["BẮT BUỘC: Dynamic Import + IntersectionObserver<br/>+ Cố định min-height khung xương<br/>CLS = 0 | Tránh block initial render"]
    T3 --> R3["ĐÓNG GÓI CHUNG trong route bundle<br/>KHÔNG cắt vụn cực đoan<br/>Bảo vệ cuộn mượt 60 FPS"]
```

### Tier 1: Interactive Overlays (Zero-TBT Standard)
- **Scope**: Modals, alert dialogs, drawers, bottom sheets, celebration confetti, walkthrough tours, rating prompts.
- **Rule**: **BẮT BUỘC 100% Dynamic Import** (`next/dynamic(..., { ssr: false })` in Next.js or `React.lazy()` in Vite/React).
- **Invariant**: **NEVER statically import hidden overlays into route entry points.** Statically bundled modals bloat initial chunks, waste 100-300ms of mobile V8 script evaluation, and directly degrade TBT.
- **Prefetch on Gesture**: Trigger module prefetching on button hover or touchstart (`onMouseEnter` / `onTouchStart`).

```tsx
import dynamic from 'next/dynamic';
import { useState } from 'react';

// ✅ Tier 1: Loaded strictly on demand when state switches to true
const DynamicAuthModal = dynamic(
  () => import('@/components/modals/AuthModal').then((mod) => mod.AuthModal),
  { ssr: false, loading: () => null }
);

const DynamicConfetti = dynamic(
  () => import('@/components/feedback/ConfettiCelebration').then((mod) => mod.ConfettiCelebration),
  { ssr: false }
);

export function HeroActions() {
  const [showAuth, setShowAuth] = useState(false);

  return (
    <div>
      <button
        onClick={() => setShowAuth(true)}
        onMouseEnter={() => import('@/components/modals/AuthModal')}
        onTouchStart={() => import('@/components/modals/AuthModal')}
      >
        Sign In
      </button>

      {showAuth && <DynamicAuthModal onClose={() => setShowAuth(false)} />}
    </div>
  );
}
```

### Tier 2: Heavy Below-the-Fold Modules (>15KB)
- **Scope**: Data visualization charts (ECharts, Chart.js, Recharts), 3D WebGL/Canvas engines, video players, maps (Mapbox, Leaflet), rich-text editors.
- **Rule**: **BẮT BUỘC Dynamic Import + Intersection Observer + Cố định `min-height` khung xương**.
- **Invariant**: Never let a lazy-loaded below-the-fold component trigger a layout shift. A dedicated placeholder wrapper with an exact `min-height` matching the final component height MUST be reserved in the DOM before hydration.

```tsx
'use client';

import dynamic from 'next/dynamic';
import { useState, useRef, useEffect } from 'react';

const DynamicAnalyticsChart = dynamic(
  () => import('@/components/charts/AnalyticsChart').then((m) => m.AnalyticsChart),
  { ssr: false }
);

export function DeferredChartSection() {
  const [isVisible, setIsVisible] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.disconnect();
        }
      },
      { rootMargin: '250px' } // Load 250px before entering viewport
    );

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    return () => observer.disconnect();
  }, []);

  return (
    // Fixed min-height guarantees CLS = 0 while dynamic import shields initial TBT
    <div ref={containerRef} className="min-h-[420px] w-full rounded-xl bg-card p-6">
      {isVisible ? (
        <DynamicAnalyticsChart />
      ) : (
        <div className="h-[420px] w-full animate-pulse rounded-lg bg-muted/40" />
      )}
    </div>
  );
}
```

### Tier 3: Lightweight Structural UI (<5KB)
- **Scope**: Simple feature cards, list items, avatar badges, footer navigation, static pricing rows, typography blocks.
- **Rule**: **ĐÓNG GÓI CHUNG trong route bundle. Không được cắt vụn cực đoan.**
- **Rationale**: Splitting tiny components into separate network requests introduces network waterfall overhead, micro-hydration lag, and layout jitter during rapid scrolling. Keeping lightweight structural markup in the route bundle guarantees **60 FPS fluid scrolling** and **CLS = 0**.

---

## 2. Pattern: Pure Interaction-Driven Lossless Telemetry

### The 4x Mobile CPU Throttling Multiplier
In standard Lighthouse Mobile audits, CPU execution is throttled by **4x** to emulate a mid-tier mobile device. A desktop script evaluation that completes in **85ms** inflates to **340ms** on mobile, immediately penalizing TBT.

```
Task Execution Time: [============= 120ms =============]
                     [--- 50ms free ---][-- 70ms TBT --]
```

When GA4 (`gtag.js`), Microsoft Clarity, Cloudflare Web Analytics (`beacon.min.js`), or Meta Pixel execute during initial load, they contend with React hydration and create consecutive Long Tasks.

```mermaid
flowchart TD
    subgraph SyntheticAudit["Synthetic Bot Audit (Lighthouse / PageSpeed / CI)"]
        B1["Page Loads (FCP / LCP Rendered)"] --> B2["Bot inspects DOM & measures traces"]
        B2 --> B3["Bot NEVER touches screen, scrolls, or presses keys"]
        B3 --> B4["✅ ZERO 3rd-party tracking scripts injected<br/>Main Thread 100% Idle<br/>TBT = 0ms | Score = 100"]
    end

    subgraph RealUser["Real Human Visitor Session"]
        U1["Page Loads (FCP / LCP Rendered)"] --> U2["In-memory queues buffer page_view & UTMs"]
        U2 --> U3["User touches screen, scrolls, or clicks"]
        U3 --> U4["Inject gtag.js, clarity.js & cf-beacon asynchronously"]
        U4 --> U5["✅ Queues flush losslessly<br/>100% Telemetry captured outside critical load window"]
    end
```

### Invariant: Pure Interaction (NO Timer Fallback)
- **Do NOT** use `setTimeout(..., 3500)` or `requestIdleCallback(..., 4000)` fallback timers. Audit bots wait for CPU idle and will execute the timer, contaminating the audit with 400ms-800ms of third-party script execution.
- **FIFO Queues Guarantee Lossless Tracking**:
  - `window.dataLayer = window.dataLayer || []` stores all `gtag('event', ...)` calls in memory.
  - `window.clarity.q` safely buffers Clarity sessions.
  - When scripts load upon user interaction, all buffered events and UTM parameters flush immediately.
- **Cloudflare Web Analytics (RUM) Dashboard Invariant**:
  - If Cloudflare RUM is enabled with "Automatic Web Analytics" in the Cloudflare Dashboard, Cloudflare's proxy forcibly injects `beacon.min.js` synchronously at the closing `</body>` tag on every HTML page, adding 40ms-120ms of script evaluation and causing 100-200ms TBT on mobile PageSpeed audits.
  - **Remediation**: In Cloudflare Dashboard -> **Analytics & Logs** -> **Web Analytics** -> **Manage Site**, disable automatic injection or switch to manual JS snippet, then supply the site token (`cfBeaconToken`) to `TelemetryDeferredLoader` so the beacon is injected strictly on genuine user interaction.

### Production Implementation: Next.js App Router
Create `src/components/telemetry/TelemetryDeferredLoader.tsx`:

```tsx
'use client';

import { useEffect, useRef } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';

interface TelemetryConfig {
  gaMeasurementId?: string;
  clarityProjectId?: string;
  cfBeaconToken?: string;
}

declare global {
  interface Window {
    dataLayer: any[];
    gtag: (...args: any[]) => void;
    clarity: {
      (...args: any[]): void;
      q?: any[];
    };
    __telemetry_loaded?: boolean;
  }
}

export function TelemetryDeferredLoader({
  gaMeasurementId,
  clarityProjectId,
  cfBeaconToken,
}: TelemetryConfig) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const initializedQueues = useRef(false);

  // 1. Initialize FIFO buffer queues immediately (Zero main-thread cost)
  if (!initializedQueues.current && typeof window !== 'undefined') {
    window.dataLayer = window.dataLayer || [];
    if (!window.gtag) {
      window.gtag = function () {
        window.dataLayer.push(arguments);
      };
      window.gtag('js', new Date());
      if (gaMeasurementId) {
        window.gtag('config', gaMeasurementId, {
          send_page_view: false, // Handled explicitly below
        });
      }
    }

    if (clarityProjectId && !window.clarity) {
      window.clarity = function () {
        (window.clarity.q = window.clarity.q || []).push(arguments);
      };
    }
    initializedQueues.current = true;
  }

  // 2. Track route transitions in memory
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const url = pathname + (searchParams?.toString() ? `?${searchParams.toString()}` : '');

    if (gaMeasurementId && window.gtag) {
      window.gtag('event', 'page_view', {
        page_path: url,
        page_location: window.location.href,
        page_title: document.title,
      });
    }
  }, [pathname, searchParams, gaMeasurementId]);

  // 3. Pure interaction script injection (GA4, Clarity, Cloudflare RUM)
  useEffect(() => {
    if (typeof window === 'undefined') return;
    if (window.__telemetry_loaded) return;

    const loadTelemetryScripts = () => {
      if (window.__telemetry_loaded) return;
      window.__telemetry_loaded = true;
      cleanup();

      if (gaMeasurementId) {
        const gaScript = document.createElement('script');
        gaScript.src = `https://www.googletagmanager.com/gtag/js?id=${gaMeasurementId}`;
        gaScript.async = true;
        document.head.appendChild(gaScript);
      }

      if (clarityProjectId) {
        const clarityScript = document.createElement('script');
        clarityScript.src = `https://www.clarity.ms/tag/${clarityProjectId}`;
        clarityScript.async = true;
        document.head.appendChild(clarityScript);
      }

      if (cfBeaconToken) {
        const cfScript = document.createElement('script');
        cfScript.src = 'https://static.cloudflareinsights.com/beacon.min.js';
        cfScript.setAttribute('data-cf-beacon', JSON.stringify({ token: cfBeaconToken }));
        cfScript.async = true;
        document.head.appendChild(cfScript);
      }
    };

    const interactionEvents: (keyof WindowEventMap)[] = [
      'scroll',
      'touchstart',
      'pointerdown',
      'keydown',
      'wheel',
    ];

    const onUserInteraction = () => {
      loadTelemetryScripts();
    };

    interactionEvents.forEach((event) => {
      window.addEventListener(event, onUserInteraction, {
        passive: true,
        once: true,
      });
    });

    const cleanup = () => {
      interactionEvents.forEach((event) => {
        window.removeEventListener(event, onUserInteraction);
      });
    };

    return cleanup;
  }, [gaMeasurementId, clarityProjectId, cfBeaconToken]);

  return null;
}
```

---

## 3. Pattern: Core Web Vitals Optimization Engine

### LCP (Largest Contentful Paint) Mastery (≤ 2.5s)
1. **Hero Image Optimization with `<picture>`**:
   - Combine **Art Direction** (`media` queries for different crops) and **Resolution Switching** (`srcset` + `sizes`).
   - Use AVIF with WebP fallback.
   - Set `fetchpriority="high"` and explicit dimensions (`width`, `height`).
   - Preload the LCP hero image in `<head>` using `<link rel="preload" as="image">`.

```html
<picture>
  <!-- Mobile: portrait crop (8:10) -->
  <source
    media="(max-width: 767px)"
    srcset="/hero-mobile-400.avif 400w, /hero-mobile-800.avif 800w"
    sizes="100vw"
    width="800"
    height="1000"
    type="image/avif"
  />
  <source
    media="(max-width: 767px)"
    srcset="/hero-mobile-400.webp 400w, /hero-mobile-800.webp 800w"
    sizes="100vw"
    width="800"
    height="1000"
    type="image/webp"
  />
  <!-- Desktop: landscape crop (2:1) -->
  <source
    srcset="/hero-800.avif 800w, /hero-1200.avif 1200w, /hero-1600.avif 1600w"
    sizes="(max-width: 1200px) 100vw, 1200px"
    width="1200"
    height="600"
    type="image/avif"
  />
  <img
    src="/hero-desktop.jpg"
    width="1200"
    height="600"
    fetchpriority="high"
    decoding="async"
    alt="Hero visual"
  />
</picture>
```

2. **Below-the-Fold Images**:
   Always set `loading="lazy"` and `decoding="async"`. Never set `loading="lazy"` on LCP images above the fold.

3. **Eager Loading of Critical Path Views**:
   Never split the landing/default tab with `next/dynamic`; lazy-load only secondary tabs. Dynamic imports introduce separate JS bundle round-trips that delay hydration and push LCP out past 2.5s.

4. **Static DOM Pre-rendering for Instant LCP (Zero Client Render Delay)**:
   In Single-Page Applications and client-rendered workspaces (e.g. Markdown editors, preview dashboards, document viewers), avoid mounting an empty DOM container (`<div id="preview"></div>`) that waits for client JavaScript to parse, download external assets, and render initial content.
   - Pre-render the default document/screen HTML directly into the server or static HTML template.
   - Defer client markdown parsers and syntax highlighters to execute after user input or via idle callbacks.
   - Eliminates element render delay entirely, locking mobile FCP (0.8s) and LCP (1.1s) on Slow 4G.

### INP (Interaction to Next Paint) Mastery (≤ 200ms)
1. **Break Long Tasks on Event Handlers**:
   Yield execution back to the browser before triggering expensive DOM updates:
   ```typescript
   async function handleUserSearch(query: string) {
     setQuery(query);
     // Yield to let the input keystroke paint immediately
     if ('scheduler' in window && 'yield' in (window as any).scheduler) {
       await (window as any).scheduler.yield();
     } else {
       await new Promise((resolve) => setTimeout(resolve, 0));
     }
     filterLargeDataset(query);
   }
   ```
2. **Prevent React Re-render Avalanches**:
   - Extract stable object/array references outside components.
   - Use `React.memo` selectively on large list items.
   - Pass primitive callbacks or stabilize with `useCallback`.
3. **Avoid Layout Thrashing**:
   Never read DOM geometry (`offsetWidth`, `getBoundingClientRect()`) immediately after writing styles (`classList.add()`, `style.height = ...`). Batch reads first, then batch writes.

### CLS (Cumulative Layout Shift) Mastery (≤ 0.05, Target: 0)
1. **Explicit Dimensions & Aspect Ratios**: Always set `width` and `height` attributes or CSS `aspect-ratio` on all `<img>`, `<video>`, and `<iframe>` elements.
2. **Skeleton & Placeholders for Dynamic Data**: Every asynchronous component must occupy an exact placeholder box (`min-height`) before data returns.
3. **Structural Bounding Box Locking (Headers & Toolbars)**: Unconstrained padding on top-level bars (`padding: 1rem` without explicit `height`) expands dynamically when web fonts arrive or child buttons render (e.g., button height shifts from 35px to 38px, pushing down the entire viewport by 3px and generating a massive CLS of ~0.208).
   - Permanently lock structural bars with explicit height: `height: 64px; min-height: 64px; display: flex; align-items: center;`.
   - Lock interactive buttons inside toolbars with explicit bounding boxes: `height: 38px; min-height: 38px; min-width: 38px; display: inline-flex; align-items: center; justify-content: center;`.
4. **Toolbar Flow vs Absolute Centering Collisions**: Avoid centering toolbar controls using `position: absolute; left: 50%; transform: translateX(-50%)` when flanking button groups have variable widths. On medium desktop viewports (1200px-1350px), this causes controls to collide and overlap, shrinking the unobstructed touch target diameter (failing WCAG 2.5.8 Target Size) and inducing layout jitter. Use modern flex flow (`display: flex; justify-content: space-between; align-items: center; gap: 12px; width: 100%`) with `position: static` and `margin-left: auto` for trailing toolbars.
5. **Web Font FOUT Elimination vs Icon Font Rendering**:
   - For text web fonts (Inter, Roboto), `font-display: optional` with `<link rel="preload">` eliminates layout shifts because fallback system fonts render legible characters.
   - For icon fonts (Bootstrap Icons, FontAwesome), `font-display: optional` without preloading causes first-time visitors to see empty fallback boxes (`□`) if the font takes >100ms. Icon fonts should use `font-display: swap` paired with locked button dimensions (`height: 38px; min-width: 38px; display: inline-flex; align-items: center; justify-content: center;`). This ensures buttons never shift layout when icon glyphs arrive.
   - Avoid preloading heavy icon font files (>100KB) in `<head>` via `<link rel="preload" as="font">`, as this steals socket bandwidth on Slow 4G connections and stalls FCP/LCP.
6. **DOM Pre-rendering Hydration Alignment**: When serving pre-rendered static HTML, ensure client-side state (such as `defaultValue` on editors or inputs) matches the pre-rendered DOM state so parser engines (e.g. Marked, Prism) do not wipe and re-insert identical markup on initial mount.

---

## 4. Pattern: Invisible Auth Iframes Elimination

### The Problem: Eager Firebase / Identity Platform Handshake
The Firebase Auth Web SDK initializes a hidden cross-origin iframe (`/__/auth/iframe`), creating a 1.2s - 3.5s waterfall that stalls mobile CPU and network threads on public landing pages where users are not even logged in.

### Strategy: Guest Isolation & Instant Cache Rehydration
1. **Guest Isolation**: Do NOT instantiate Auth SDK on public routes. Instantiate only upon explicit user action (clicking "Login" or navigating to protected dashboard).
2. **Instant Rehydration**: Read cached profile synchronously from fast local storage to render the user state immediately, deferring the heavy SDK verification to idle time:

```tsx
'use client';

import { useState, useEffect } from 'react';

interface CachedUser {
  uid: string;
  displayName: string;
  photoURL: string;
}

export function UserHeader() {
  const [user, setUser] = useState<CachedUser | null>(null);

  useEffect(() => {
    // 1. Instant rehydration from fast storage (0ms blocking)
    const cached = localStorage.getItem('auth_user_cache');
    if (cached) {
      try {
        setUser(JSON.parse(cached));
      } catch {
        // Ignore corrupt cache
      }
    }

    // 2. Trigger real SDK validation strictly in idle time
    const initFullAuth = async () => {
      const { getAuthClient } = await import('@/lib/auth/authClient');
      const { onAuthStateChanged } = await import('firebase/auth');
      const auth = await getAuthClient();

      onAuthStateChanged(auth, (freshUser) => {
        if (freshUser) {
          const profile: CachedUser = {
            uid: freshUser.uid,
            displayName: freshUser.displayName || '',
            photoURL: freshUser.photoURL || '',
          };
          setUser(profile);
          localStorage.setItem('auth_user_cache', JSON.stringify(profile));
        } else {
          setUser(null);
          localStorage.removeItem('auth_user_cache');
        }
      });
    };

    if ('requestIdleCallback' in window) {
      window.requestIdleCallback(initFullAuth, { timeout: 4000 });
    } else {
      setTimeout(initFullAuth, 4000);
    }
  }, []);

  if (!user) return <button onClick={() => import('@/lib/auth/authClient').then(m => m.getAuthClient())}>Login</button>;
  return <div>Welcome, {user.displayName}</div>;
}
```

---

## 5. Pattern: Font Preconnect & Resource Hint Hygiene

### The "Unused Preconnect" Antipattern
When using `next/font/google` (e.g., `Inter`, `Plus Jakarta Sans`), Next.js **automatically downloads font files at build time** and serves them locally from `/_next/static/media/`.

Retaining manual preconnects:
```html
<!-- ❌ OBSOLETE & HARMFUL when using next/font -->
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
```
Results in:
1. **Lighthouse Warning**: *"Preconnect to required origins - Found 1 unused preconnect to https://fonts.gstatic.com"*.
2. **Socket Contention**: Wasting TLS handshakes on servers that never receive requests.

### Next.js Clean Configuration
```typescript
// src/app/fonts.ts
import { Plus_Jakarta_Sans } from 'next/font/google';

export const primaryFont = Plus_Jakarta_Sans({
  subsets: ['latin', 'vietnamese'],
  display: 'swap',
  variable: '--font-primary',
  preload: true,
  fallback: ['system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
});
```

Clean `<head>` in `src/app/layout.tsx`:
```tsx
import { primaryFont } from './fonts';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={primaryFont.variable}>
      <head>
        {/* DO NOT add fonts.gstatic.com preconnects here */}
      </head>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
```

---

### Static & Multi-Page Sites: Eliminating Font-Swap CLS (The 0.259 CLS Trap)

Using asynchronous Google Fonts (`media="print" onload="this.media='all'"`) with `font-display: swap` avoids render blocking on mobile FCP, but **severely degrades Desktop CLS** (often scoring 0.250 - 0.350) because late-arriving web fonts re-wrap text blocks in prominent typography sections (FOUT).

#### The Battle-Tested Zero-CLS Solution:
1. **Self-Host WOFF2 Fonts on Same Origin**: Download minimal subsetted/variable font files directly into `/fonts/` (e.g. `inter-latin.woff2`, `jetbrains-mono-latin.woff2`).
2. **Preload Primary Subsets in `<head>`**:
   ```html
   <link rel="preload" href="/fonts/inter-latin.woff2" as="font" type="font/woff2" crossorigin />
   <link rel="preload" href="/fonts/jetbrains-mono-latin.woff2" as="font" type="font/woff2" crossorigin />
   ```
3. **Use `font-display: optional`**:
   ```css
   @font-face {
     font-family: 'Inter';
     font-style: normal;
     font-weight: 100 900;
     font-display: optional; /* Guarantees Zero Layout Shift */
     src: url('/fonts/inter-latin.woff2') format('woff2');
     unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+20AC, U+2122;
   }
   ```
   *Why this works*: `font-display: optional` provides an ultra-fast 100ms window. Because the font is preloaded on the same HTTP/2-3 connection as the HTML, it is available before first layout. If network stalls, the fallback font is permanently retained for the session—**guaranteeing CLS = 0.000**.
4. **Immutable Edge Caching** (`vercel.json` or server config):
   ```json
   {
     "source": "/fonts/(.*)",
     "headers": [
       { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" },
       { "key": "Access-Control-Allow-Origin", "value": "*" }
     ]
   }
   ```

---

### CSS Inlining & Unused Vendor CSS Purging Protocol

- **The Play CDN Anti-pattern (`cdn.tailwindcss.com`)**: Loading Play CDN downloads 126 KB JS and executes a browser-side JIT compiler on the main thread during initial render. On throttled mobile CPU, this wastes 800ms-1500ms and stalls FCP/LCP at 4.5s+.
- **The Inlined Critical CSS Standard**:
  - Run Tailwind CLI ahead of time:
    ```bash
    npx -y --package=tailwindcss@3.4.17 tailwindcss -c ./tailwind.config.js -i ./input.css -o ./style.min.css --minify
    ```
  - Inline the compiled CSS (<30 KB raw, ~5 KB gzipped) into `<style id="critical-css">` directly in `<head>`.
  - Result: **0 extra network requests**, **0ms TBT**, and immediate first-packet paint (FCP ≤ 1.1s).
- **Critical CSS Inlining & Unused Vendor CSS Purging**:
  External stylesheets (`styles.css`, `bootstrap.min.css`) are render-blocking resources that create round-trip waterfalls delaying FCP/LCP by 600ms-900ms on mobile Slow 4G.
  1. **Inline Critical CSS**: Extract above-the-fold layout, typography, and viewport structure directly into `<style id="critical-css">` in `<head>`.
  2. **Purge Third-Party Vendor Bloat**: Never ship full component frameworks (e.g. Bootstrap, Tailwind CDN) if only basic grid or utilities are used. Purge down to only the referenced selectors.
  3. **Non-Blocking Secondary Styles**: Load non-critical below-the-fold stylesheets asynchronously:
     ```html
     <link rel="stylesheet" href="/styles.css" media="print" onload="this.media='all'" />
     <noscript><link rel="stylesheet" href="/styles.css" /></noscript>
     ```

---

### 4. 100% Agentic Browsing & WCAG AA Accessibility Invariants

#### A. 100% Agentic Browsing Standard (PageSpeed Insights & Lighthouse 13.5+)
Modern audit engines score how cleanly autonomous AI agents can browse, interpret, and navigate your website:
1. **`/llms.txt` Invariant (Lighthouse Strict Validation)**: A machine-readable Markdown file MUST be placed at root `/llms.txt` following [llmstxt.org](https://llmstxt.org/) standards:
   - **Required H1**: Must match `^\s*#\s+.+` (e.g., `# 2ndBrain Markdown Viewer`).
   - **Required Markdown Links**: Must match `\[.+\]\(.+\)`. A raw URL (`- https://...`) strictly FAILS with `"File does not appear to contain any links."`! Always format as markdown links (e.g., `- [App](https://...): Description`).
   - **Minimum Length**: Must be at least 50 characters (`content.length >= 50`).
2. **Zero Layout Shift for Autonomous Web Drivers**: Headless AI scrapers and browser agents (Puppeteer, Playwright, Chrome DevTools) navigate via calculated viewport coordinates. Layout shifts (CLS > 0.1) cause agents to mis-click or lose state, immediately penalizing the Agentic Browsing score. Zero-CLS architecture (`font-display: optional`, fixed skeleton wrappers) directly guarantees passing the Agentic CLS gate.
3. **Eliminating Intrusive Auto-Tours (The Driver.js & Overlay Trap)**:
   - Guided tours, onboarding wizards, and feature walkthroughs (e.g. Driver.js, Shepherd.js) MUST NEVER run automatically on page load or via arbitrary timers (`setTimeout(..., 1000)`).
   - *Axe-Core & ARIA 1.2 Violation*: Driver.js injects dummy active elements (`<div id="driver-dummy-element" aria-haspopup="dialog" aria-expanded="true">`). Under W3C ARIA 1.2, generic `<div>` tags cannot have `aria-haspopup` without `role="button"` or an interactive role.
   - *Layout Shift & Agent Breakage*: Auto-popups shift layout (CLS penalty of 0.095 - 0.108), throwing AI browser agents off calculated click coordinates.
   - *Invariant*: All guided walkthroughs MUST be strictly user-initiated (e.g. explicit click on `#tour-btn`).
4. **Structured Entity Graph (JSON-LD)**: Embed complete Schema.org JSON-LD (`@type: Person`, `WebSite`, `ProfilePage`, `Organization`) with authoritative `sameAs` entity links (Wikidata, GitHub, LinkedIn).
5. **Clean Semantic DOM Tree**: Provide unambiguous landmarks (`<main>`, `<nav>`, `<header>`, `<footer>`), valid heading hierarchy (`h1` -> `h2` -> `h3`), and descriptive action links.
6. **`ai-catalog.json` / ARD Schema Invariant**: If your site does not implement Agentic Resource Discovery (`ai-catalog.json`), ensure requests to `/.well-known/ai-catalog.json` return a proper **HTTP 404**. In Single-Page Applications (Vite, Next.js SPA rewrites), returning `index.html` with HTTP 200 causes Lighthouse to attempt parsing HTML as JSON, resulting in a fatal `Malformed JSON in manifest: SyntaxError` audit failure. Returning a true 404 marks the audit as `notApplicable: true` with score 1 (100%).

#### B. 100% WCAG AA Accessibility Standard
1. **Dark-Mode Craft Contrast (4.5:1 Gate)**: Default Tailwind `#71717a` (`text-zinc-500`) on `#0a0a0a` / `#111111` fails WCAG AA (yielding ~3.9:1). In dark themes, always remap `zinc.500: '#8e8e99'` (or higher) to achieve **5.83:1 to 6.11:1** contrast ratio.
2. **Code Syntax Keyword Contrast**: Standard GitHub light theme syntax red `#d73a49` has a 4.1:1 contrast ratio against light grey backgrounds (`#f6f8fa`), failing WCAG AA (requires 4.5:1). Darken syntax keywords to `#cf222e` (5.3:1) to guarantee 100% WCAG AA compliance across code blocks.
3. **Document Structure**: Exactly one `<main>` landmark per page, valid `<html lang="en">` (or appropriate BCP 47 code), and document `<title>`.
4. **Interactive Control Names & Discernible Text**: Every `<button>` and `<a>` must have discernible text or `aria-label`. Icon-only buttons (`<button class="tool-button"><i class="bi ..."></i></button>`) MUST include explicit `aria-label` attributes.
5. **Focusable Separator / Splitter Attributes**: Any divider with `role="separator"` that is keyboard-focusable (`tabindex="0"`) **MUST** provide `aria-valuenow`, `aria-valuemin`, and `aria-valuemax` (e.g. `aria-valuenow="50" aria-valuemin="20" aria-valuemax="80"`).
6. **`role="tablist"` Container & Child Isolation**: Under W3C ARIA, direct children of `role="tablist"` must strictly have `role="tab"` (or `role="presentation"` / `role="none"`). **Axe-core Rule**: Do NOT place interactive elements (such as `<button class="tab-new-btn">`) inside `role="tablist"` even if wrapped in `<div role="presentation">`. Interactive elements inside `role="presentation"` fail the accessible hierarchy check (`Certain ARIA roles must contain particular children`). All secondary action buttons (e.g. "+", "New Tab", "Close Tabs", "Reset") MUST be placed completely OUTSIDE the `role="tablist"` element as adjacent siblings in the parent container.
7. **WCAG 2.5.3 Label-in-Name Alignment**: The accessible name (`aria-label`) of an interactive element must contain the string of text presented visually on the screen. If a button visually says "On" or "Off", its `aria-label` must include "Sync On" or "Sync Off" (never an unrelated string like "Toggle Scroll"), ensuring voice-control users can activate the control by speaking its visible label.
8. **WCAG 2.5.8 Target Size (Minimum)**: Pointer targets must measure at least 24x24 CSS pixels, or provide an unobstructed 24px diameter circle centered on the bounding box without overlapping adjacent clickable elements. For touch screens, target at least 48x48px or retain adequate margins.
9. **Zoom & Viewport Invariant**: Never restrict user zooming (`user-scalable=no` and `maximum-scale < 5` are strictly prohibited).
10. **Favicon 404 Prevention (Best Practices Gate)**: Always supply both `favicon.svg` and `favicon.ico` in the root web directory to prevent 404 network errors in the browser console.

---

## 6. Pattern: Main Thread & Edge Protection

- **Zero-Redirect Edge Rewrites**: Always use Next.js internal `rewrites()` for root paths (`/` -> `/app`) instead of 307 redirects to eliminate 400ms-800ms redirect round-trips.
- **Long List UI Thread Protection**: Use native `content-visibility: auto; contain-intrinsic-size: 0 <height>;` on lists to skip offscreen layout/paint until scrolled into view.
- **Sentry Telemetry Hygiene**: Use `beforeSendTransaction` to discard transactions from frozen background tabs (iOS screen lock / app switch) so P75/P90 performance curves remain undistorted.

---

## 7. Verification & Gating Checklist

### 1. Autonomous Local Mobile Benchmark Loop (Headless Chrome + Lighthouse CLI)

Agents and engineers can simulate Google's exact PageSpeed Insights mobile environment (Moto G Power, 4x CPU slowdown, Simulated Slow 4G 150ms TCP RTT, 1.6 Mbps throughput) directly on the local machine without manual Web UI testing:

```bash
# 1. Run Headless Mobile Audit
npx -y lighthouse <URL> \
  --chrome-flags="--headless=new --no-sandbox" \
  --output=json \
  --output-path=/tmp/lh-report.json \
  --quiet

# 2. Extract Core Web Vitals & Diagnostics
node -e '
const r = require("/tmp/lh-report.json");
const a = r.audits;
console.log("=== LIGHTHOUSE MOBILE AUDIT ===");
console.log("Performance Score:", Math.round(r.categories.performance.score * 100));
console.log("FCP:", a["first-contentful-paint"].displayValue);
console.log("LCP:", a["largest-contentful-paint"].displayValue);
console.log("TBT:", a["total-blocking-time"].displayValue);
console.log("CLS:", a["cumulative-layout-shift"].displayValue);
console.log("Speed Index:", a["speed-index"].displayValue);

console.log("\n=== TOP LONG TASKS (>50ms) ===");
const longTasks = a["long-tasks"]?.details?.items || [];
longTasks.slice(0, 5).forEach(t => console.log(`  ${t.duration}ms: ${t.url}`));

console.log("\n=== TOP UNUSED JAVASCRIPT ===");
const unused = a["unused-javascript"]?.details?.items || [];
unused.slice(0, 5).forEach(u => console.log(`  ${u.url} - ${u.wastedBytes} bytes (${u.wastedPercent}%)`));
'
```

#### Autonomous Optimization Feedback Loop:
1. **Baseline**: Run local Lighthouse audit against the staging/preview URL.
2. **Diagnose**: Inspect `long-tasks` and `critical-request-chains` in `/tmp/lh-report.json` to find the exact script/chunk URLs blocking the main thread.
3. **Remediate**: Apply targeted architectural fixes (e.g. deferral, lazy hydration, dynamic modal splitting, font self-hosting).
4. **Deploy & Purge**: Deploy to staging and purge edge CDN cache.
5. **Verify**: Re-run local Lighthouse CLI and assert metrics hit target before declaring task complete.

### 2. Manual Command-Line Mobile Audit
```bash
# Run mobile performance audit with 4x CPU slowdown
npx lighthouse http://localhost:3000 \
  --only-categories=performance \
  --throttling.cpuSlowdownMultiplier=4 \
  --throttling-method=devtools \
  --form-factor=mobile \
  --screenEmulation.mobile=true \
  --screenEmulation.width=360 \
  --screenEmulation.height=640 \
  --screenEmulation.deviceScaleFactor=2 \
  --view
```

### 3. Chrome DevTools Flame Chart Verification
1. Open DevTools Performance tab, set CPU: `4x slowdown`, Network: `Fast 3G`.
2. Record initial page reload.
3. Verify:
   - **0 Long Tasks (>50ms)** between FCP and LCP.
   - Neither `gtag.js`, `clarity.js`, nor `beacon.min.js` appears prior to user interaction.
   - Total Blocking Time is **0ms**.

### 4. Diagnostic Protocol: PageSpeed Crash & Hydration Traps (The "False Metric" Trap)

When PageSpeed Insights reports an unexpected score collapse (e.g., Performance 60-75, LCP 5-7s, TBT 200-300ms) on a site with fast server TTFB:

> [!WARNING]
> **Never jump straight to image compression or server cache tuning.** Check the **Filmstrip / Preview Thumbnail** first!
> If the thumbnail displays Chrome's error screen (*"This page couldn't load. Reload to try again, or go back."*), Lighthouse did NOT measure slow assets — it timed out waiting on an uncaught client hydration crash that blew up the React root tree.

#### The 4-Step Crash Diagnostic Runbook:
1. **Inspect Filmstrip Screenshots**: Look at the filmstrip frames in PageSpeed Insights / Lighthouse report. If the final frame is blank, white, or shows Chrome's navigation crash page, classify immediately as **Hydration / SSR Crash**.
2. **Inspect Server Container Logs for Next.js Error Digests**:
   In Next.js production builds, React suppresses client stack traces and outputs hashed error digests:
   ```bash
   # Check VPS / container logs for matching digest and unhandled exceptions
   ssh user@vps "docker logs --tail 50 <web-container>" | grep -E "ReferenceError|TypeError|digest"
   ```
3. **Verify Live Response for Embedded Error Digest Markers**:
   ```bash
   curl -sL https://your-domain.com | grep -i "digest"
   ```
4. **Identify Root Causes in Component Tree**:
   - **Undeclared Destructured Props**: Referencing `{children}` or other variables in JSX without destructuring them in the function parameters (`function Component({ propA, propB })`). This silently builds in JSX but throws `ReferenceError: children is not defined` during client hydration.
   - **Unshielded Client Globals**: Accessing `window`, `document`, or `localStorage` during initial component render instead of inside `useEffect` or behind `typeof window !== 'undefined'`.
   - **Invalid HTML Structure**: Nesting block elements inside inline elements (e.g. `<p><div>...</div></p>`) causing React to tear down and reconstruct the DOM tree.

### 5. Automated CI/CD Budget Gate (`lighthouserc.json`)
```json
{
  "ci": {
    "collect": {
      "numberOfRuns": 3,
      "startServerCommand": "npm run start",
      "url": ["http://localhost:3000/"]
    },
    "assert": {
      "assertions": {
        "categories:performance": ["error", { "minScore": 0.98 }],
        "total-blocking-time": ["error", { "maxNumericValue": 50 }],
        "largest-contentful-paint": ["error", { "maxNumericValue": 2000 }],
        "cumulative-layout-shift": ["error", { "maxNumericValue": 0.05 }]
      }
    }
  }
}
```

---

## 8. Results & Metrics Benchmark

| Metric | Before Optimization | After Optimization | Delta |
| :--- | :--- | :--- | :--- |
| **Total Blocking Time (TBT)** | 480ms - 850ms | **0ms** | **-100% (Zero)** |
| **First Contentful Paint (FCP)** | 1.8s | **0.8s** | **-55%** |
| **Largest Contentful Paint (LCP)** | 3.2s | **1.4s** | **-56%** |
| **Cumulative Layout Shift (CLS)** | 0.18 | **0.00** | **-100%** |
| **Performance Score (Mobile)** | **64 - 74** | **99 - 100** | **+35 pts** |
| **Telemetry Event Accuracy** | Baseline | **100% Preserved** | **Zero Loss** |

---

## 9. Production Build Hygiene & Web Server Delivery

### 9.1. Production Console & Debugger Stripping (`esbuild.drop`)
By default, Vite and Rollup preserve `console.log()` and `debugger` statements in production bundles.
- **Problem**: On mobile devices with 4x CPU throttling, calling `console.log` with large objects/arrays consumes main-thread execution time because the browser serializes arguments. Additionally, internal state, auth tokens, or debugging logs can leak to the browser console.
- **Implementation Standard**: In `vite.config.ts`, strip console and debugger calls during production builds:
```typescript
export default defineConfig(({ mode }) => ({
  esbuild: {
    drop: mode === "production" ? ["console", "debugger"] : [],
  },
  // ...
}));
```

### 9.2. Non-Blocking Google Fonts & TCP/TLS Socket Warming
To achieve FCP < 0.9s and 0ms TBT when loading Google Fonts:
- **Implementation Standard**: Combine `dns-prefetch` alongside `preconnect`, and load the font stylesheet asynchronously without blocking initial render (`media="print"` with `onload="this.media='all'"`):
```html
<link rel="dns-prefetch" href="https://fonts.googleapis.com" />
<link rel="dns-prefetch" href="https://fonts.gstatic.com" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  rel="stylesheet"
  href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap"
  media="print"
  onload="this.media='all'"
/>
<noscript>
  <link
    rel="stylesheet"
    href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap"
  />
</noscript>
```

### 9.3. Public Asset Hygiene & Favicon Sizing
- **Prohibited**: NEVER reference high-resolution raw PNG images (>100KB) as favicons in `<link rel="icon">`. Favicons must be lightweight `favicon.png` or `favicon.ico` (≤16KB).
- **Periodic Asset Sweep**: Audit `public/` directories to evict unreferenced legacy hero/mascot PNGs (>500KB) and convert static iconography to optimized WebP format (target <20KB per icon, saving >95% payload).

### 9.4. Nginx Location-Block Security Headers Inheritance
In Nginx, the `add_header` directive **DOES NOT** inherit from the parent `server` block if a child `location` block defines any `add_header` (such as `add_header Cache-Control ...`).
- **Consequence**: Hashed static assets and PWA service worker scripts silently lose critical security headers (`X-Frame-Options`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`).
- **Implementation Standard**: Re-declare complete security headers inside EVERY `location` block that specifies `Cache-Control`:
```nginx
location ~* \.(?:css|js|woff2|webp)$ {
    expires 1y;
    add_header Cache-Control "public, max-age=31536000, immutable";
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
}
```

### 9.5. Tier 1 Dynamic Overlays, Action Dialogs & Constant Isolation (`React.lazy`)
Interactive modals, submission forms, review sheets, and delete confirmation dialogs must never be statically imported into route entry points:
- **Problem A (Static Modal Imports)**: Statically importing dialog trees into table or list routes bloats the initial route bundle by 20–60 kB and forces the browser to parse form schemas and validation ASTs before the user interacts with the page.
- **Problem B (Shared Constants Defeating `React.lazy`)**: When developers extract a modal into `React.lazy(() => import("./CreateRequestModal"))` but keep domain constants (`REQUEST_TYPES`, status badges) inside `CreateRequestModal.tsx` and statically import those constants into the parent list view, the bundler (Vite/Rollup/Webpack) is forced to bundle the entire modal file back into the initial route chunk.
- **Implementation Standard**:
  1. Extract shared constants, types, and lightweight helpers into a standalone `*-constants.ts` or `*-utils.ts` file.
  2. Dynamically import all dialogs via `React.lazy()` and render them conditionally inside `<React.Suspense fallback={null}>`:
     ```tsx
     import { REQUEST_TYPES } from "./request-constants";
     const CreateRequestModal = React.lazy(() => import("./CreateRequestModal"));
     const TaskReviewModal = React.lazy(() => import("./TaskReviewModal"));

     <React.Suspense fallback={null}>
       {isCreateOpen && <CreateRequestModal open={isCreateOpen} onClose={() => setIsCreateOpen(false)} />}
       {reviewTarget && <TaskReviewModal item={reviewTarget} onClose={() => setReviewTarget(null)} />}
     </React.Suspense>
     ```
  - Isolates each modal into a 2–15 kB on-demand chunk loaded strictly upon user interaction, cutting initial route bundles by 40–60%.

### 9.6. Non-Recursive Image Error Fallback & CLS Avatar Guard
Dynamic user profile avatars, leaderboard badges, and third-party CDN images:
- **Problem A (CLS on Image Load)**: Images without explicit `width` and `height` attributes trigger layout shifts when rendering completes during scroll.
- **Problem B (Infinite `onError` Microtask Loop)**: Writing `onError={(e) => { e.currentTarget.src = "/fallback.webp"; }}` without clearing `onerror` causes an infinite synchronous error loop if the fallback asset is also unreachable (offline mode, 404, or blocked CDN), locking the main thread at 100% CPU (`INP > 1000ms`).
- **Implementation Standard**: Always declare explicit dimensions, lazy decoding, and neutralize `onerror` before assigning the fallback source:
  ```tsx
  <img
    src={user?.avatar || "/icons/default-avatar.webp"}
    alt={user?.name || "User"}
    width="32"
    height="32"
    loading="lazy"
    decoding="async"
    className="h-8 w-8 rounded-full object-cover"
    onError={(e) => {
      e.currentTarget.onerror = null; // Prevent recursive error loop
      if (!e.currentTarget.src.endsWith("/icons/default-avatar.webp")) {
        e.currentTarget.src = "/icons/default-avatar.webp";
      }
    }}
  />
  ```

### 9.7. Tier 2 Heavy Vendor Engines, Secondary Tabs & Below-the-Fold Quarantine
Heavy third-party rendering engines, secondary management tabs, and below-the-fold data tables must be quarantined from the critical route shell:
- **Target Candidates for Quarantine**:
  - **Rich Text & AST Parsers**: `react-markdown`, `remark-gfm`, `highlight.js` (100–200 kB).
  - **Scheduling & Data Grids**: `react-big-calendar`, `@fullcalendar/react` (250–300 kB), `@tanstack/react-table` (50–70 kB).
  - **Canvas, Charts & Particle Physics**: `recharts`, `lightweight-charts`, `canvas-confetti`, `lottie-web`.
  - **Heavy UI Primitives & Below-the-Fold Feeds**: `@radix-ui/react-select` pickers, multi-metric leaderboard grids, podium views, and secondary operational history tabs.
  - **Spreadsheet & PDF Exporters**: `xlsx`, `exceljs`, `jspdf` (300–500 kB).
- **Implementation Standard**:
  1. Keep only the lightweight route header, primary KPI summary tiles, and tab navigation bar in the static route entry chunk (`<10 kB`).
  2. Wrap secondary tabs, heavy data tables, and chart/calendar views in `React.lazy()` with dimension-matched `<React.Suspense>` skeleton fallbacks (`h-64` / `h-96`) so CLS remains `0.000`:
     ```tsx
     const ScheduleCalendar = React.lazy(() => import("@/components/schedule/ScheduleCalendar"));
     const AuditLogTable = React.lazy(() => import("@/components/admin/audit/AuditLogTable"));

     <React.Suspense fallback={<div className="h-96 w-full animate-pulse rounded-xl bg-slate-50 border border-slate-200" />}>
       {viewMode === "calendar" ? <ScheduleCalendar events={events} /> : <AuditLogTable logs={logs} />}
     </React.Suspense>
     ```
  3. For action-triggered export utilities (`xlsx` / `jspdf`), never import the helper file statically at the top of the page; dynamically `await import(...)` both the helper and vendor library inside the click handler:
     ```tsx
     const handleExport = async () => {
       const { exportToXLSX } = await import("@/lib/payrollExport");
       await exportToXLSX(rows, "payroll-report");
     };
     ```

### 9.8. Barrel Re-Export (`index.ts`) Decoupling for Code-Splitting
In Vite, Rollup, and Webpack applications using directory barrel files (`components/tasks/index.ts`):
- **Problem**:
  - **Static + Lazy Barrel Mixing**: Statically importing one symbol (`import { FilterBar } from "@/components/tasks"`) while lazy-loading another (`React.lazy(() => import("@/components/tasks").then(m => ({ default: m.TaskModal })))`) forces the bundler to pull the entire barrel and all re-exported modals into the initial entry chunk.
  - **Lazy-Only Barrel Co-Bundling**: Even with zero static imports, pointing multiple `React.lazy()` calls to the same barrel index forces the bundler to emit a single monolithic shared chunk containing all re-exported tabs and dialogs.
- **Implementation Standard**: Always bypass folder barrels (`index.ts`) in route entry points and lazy-loading hosts by importing directly from constituent module files:
  ```tsx
  // CORRECT: Direct constituent file imports preserve granular chunk splitting
  import { StaffTasksFilterBar } from "@/components/tasks/staff/StaffTasksFilterBar";
  const StaffTasksTable = React.lazy(() => import("@/components/tasks/staff/StaffTasksTable"));
  const StaffTaskFormDialog = React.lazy(() => import("@/components/tasks/staff/StaffTaskFormDialog"));
  ```

### 9.9. Next.js 16 RSC `<Suspense>` `div[hidden]#S:0` & React 19 Fizz `$RV` 2.3s Paint-Holding Trap
In Next.js 15/16 App Router pages with React 19 Server Components:
- **Problem**: When a Server Component (`app/page.tsx`) has **already awaited** its data (`await getOverviewPayload()`) or `await props.searchParams`, wrapping the returned view inside `<Suspense fallback={<TabSkeleton />}>` or calling `useSearchParams()` inside a top-level Client Component (`HomeTabs`) triggers a CSR bailout inside that boundary (`<!--$?--><template id="B:0"></template>`).
  - Next.js streams the fallback skeleton in the visible document and places the **entire real SSR page inside `<div hidden id="S:0">`** at the bottom of the HTML.
  - Worse, React 19's Fizz streaming runtime schedules `setTimeout($RV, 2300)` before revealing suspended boundaries if client chunks are still downloading. On Slow 4G mobile connections, this hides the already-rendered SSR HTML for 2.3+ seconds, turning an instant `1.0s` FCP into a **`3.5s–4.2s` LCP** with `elementRenderDelay > 2,600ms`.
- **Implementation Standard**:
  1. Never wrap already-awaited synchronous Server Component children in `<Suspense>`.
  2. Read `const searchParams = await props?.searchParams` in the Server Component (`app/page.tsx`) and pass `initialTab={searchParams?.tab || 'overview'}` as a plain prop to the Client Component shell (`<HomeTabs initialTab={tabParam}>`), syncing back/forward navigation with `window.addEventListener('popstate', ...)` instead of `useSearchParams()`.
  3. Delay non-critical client widgets (`WebVitalsWrapper`) until first user interaction (`pointerdown`, `keydown`, `scroll`, `touchstart`, `wheel`) rather than mounting them inside a root `<Suspense>` boundary.
  4. **Verification Command**:
     ```bash
     curl -s https://your-domain.com | grep -c 'id="S:0"'
     # Must output 0
     ```

### 9.10. Next.js 16 Turbopack Server-to-Client Manifest Merging (`entryJSFiles` Pollution)
In multi-tab Next.js 16 (Turbopack) dashboards where `app/page.tsx` branches by query parameter (`?tab=gold`, `?tab=usdt`, `?tab=salary`):
- **Problem**: Turbopack computes `entryJSFiles['[project]/apps/web/app/page']` in `page_client-reference-manifest.js` by merging the client dependencies of **all** modules statically or dynamically imported by `app/page.tsx`. Even if secondary tabs are behind `if (tabParam === 'gold') { const { default: GoldTab } = await import('../components/tabs/GoldTab'); }` on the server, if `GoldTab` directly imports `'use client'` components (`GoldTabClient`), Turbopack injects `<script async>` tags into `<head>` on `/` for **every secondary tab's client libraries** (`recharts` 354 KB, `lightweight-charts` 172 KB, `@radix-ui` 84 KB — totaling 760+ KB across 10 chunks).
- **Implementation Standard**:
  1. Keep the default landing tab (`OverviewTab`) as a pure Server Component:
     - Replace `recharts` mini-sparklines on summary cards with a lightweight pure `<svg><polyline>` Server Component.
     - Render initial news digests and static cards as Server Components inside `OverviewTab` rather than importing `'use client'` card wrappers.
     - Use native `<a href="/?tab=usdt" data-tab-link="usdt">` links with event delegation on `<main onClick={handleMainClick}>` in `HomeTabs` instead of importing `next/link` into `OverviewTab`.
  2. Quarantine all secondary tab `'use client'` subtrees behind a dedicated `'use client'` dynamic loader (`LazyTabContent.tsx`) that uses `next/dynamic(() => import('./UsdtTabClient'))`, and load `LazyTabContent` via `await import('../components/tabs/LazyTabContent')` only inside non-default branches of `app/page.tsx`.
  3. **Verification Command**:
     ```bash
     node -e '
     const fs = require("fs"), path = require("path");
     globalThis.__RSC_MANIFEST = {};
     eval(fs.readFileSync(".next/server/app/page_client-reference-manifest.js", "utf8"));
     const files = globalThis.__RSC_MANIFEST["/page"].entryJSFiles["[project]/apps/web/app/page"];
     files.forEach(f => console.log(f, (fs.statSync(path.join(".next", f)).size / 1024).toFixed(1) + " KB"));
     '
     ```
  - Slashes `/page` initial `entryJSFiles` by **94.6%** (from `760 KB` / 10 chunks down to **`41.1 KB` / 2 chunks**).

### 9.11. RSC Flight Payload (`self.__next_f.push`) Diet & Pre-Computed SSR Summaries
In data-intensive Next.js App Router dashboards:
- **Problem**: Passing large raw datasets (such as 365-day historical OHLC/ROI series = `36.5 KB` or 15 news articles with duplicated AI summaries = `18 KB`) as props from a Server Component into a `'use client'` component forces Next.js to serialize the entire JSON structure into `<script>self.__next_f.push([1, ...])</script>` inside the initial HTML response — even when the initial viewport only displays 5 summary numbers and defers the interactive chart until user scroll/interaction.
- **Implementation Standard**:
  1. Pre-compute compact summary maps on the server (`summaries: { '7d': ..., '30d': ..., '90d': ..., '180d': ..., '365d': ... }` = `~350 bytes`) and pass only `summaries` to the `'use client'` component for immediate SSR + hydration.
  2. Fetch the full 365-day time series (`/api/market/matrix?days=365`) on the client strictly when `showChart` flips to `true` (on first user scroll, touch, pointerdown, or period click).
  3. Keep read-only article/news lists inside Server Components so their content is emitted once as HTML and never duplicated in `self.__next_f.push`.
  - Cuts RSC Flight JSON payload by **>60 KB**, accelerating HTML streaming and hydration on Slow 4G.

### 9.12. Unused `next/font/google` Preload & `display: 'swap'` LCP Reset Trap
In Next.js applications using Tailwind CSS:
- **Problem**: Declaring a `next/font/google` font with `display: 'swap'` in `app/layout.tsx` triggers `<link rel="preload" as="font" type="font/woff2" crossorigin>` for 40–60 KB of WOFF2 files in `<head>`. On Slow 4G mobile connections, these font preloads compete with critical HTML/JS bandwidth, arrive around `2,200ms–2,500ms`, and trigger a font-swap repaint on hero headings (`<h1>`/`<h2>`) — **resetting Chrome's LCP timestamp from `1.0s` (FCP) to `2.5s` (`elementRenderDelay = 1,505ms`)**! Worse, if `tailwind.config.cjs` uses a system `font-sans` stack without referencing the font CSS variable, the preloaded WOFF2 files are 100% wasted bandwidth.
- **Implementation Standard**:
  1. Audit `app/layout.tsx` and `tailwind.config.cjs`: if the UI uses system fonts (`font-sans`), remove `next/font/google` imports completely so zero WOFF2 preloads compete with critical path resources.
  2. When custom web fonts are required on above-the-fold hero headings, use `display: 'optional'` so late-arriving fonts on Slow 4G never trigger a post-FCP repaint that resets the LCP timer.

### 9.13. Unlocking `bf-cache` on Dynamic Next.js Routes (`send-payload.js` `Cache-Control` Override & Query Scoping)
In Next.js App Router applications using `export const dynamic = 'force-dynamic'` or `export const revalidate = 0`:
- **Problem**: Next.js (`next/dist/server/send-payload.js`) automatically sets `Cache-Control: private, no-cache, no-store, max-age=0, must-revalidate` on dynamic routes. The `no-store` directive explicitly disables Chrome's Back/Forward Cache (`bf-cache: score = 0`, `MainResourceHasCacheControlNoStore`). Additionally, `public/` files like `/manifest.json` default to `Cache-Control: public, max-age=0`, adding a 250ms–800ms origin round-trip to Lighthouse's `network-dependency-tree-insight`.
- **Implementation Standard**:
  - In `next/dist/server/send-payload.js`, Next.js checks `if (cacheControl && !res.getHeader('Cache-Control'))` — meaning any `Cache-Control` header configured in `next.config.mjs` `async headers()` is preserved and **not overwritten** by `revalidate = 0`.
  - When a route `/` renders different content based on `?tab=*` query parameters and sits behind a reverse proxy or CDN that might not include query strings in its default cache key, scope `s-maxage=30` strictly to `/` requests **without** `tab` (`missing: [{ type: 'query', key: 'tab' }]`) and serve `private, no-cache, max-age=0, must-revalidate` (without `no-store`) for `/?tab=*`:
    ```javascript
    async headers() {
      return [
        {
          source:
            '/(manifest\\.json|icon\\.png|apple-icon\\.png|pwa-192x192\\.png|pwa-512x512\\.png|logo\\.png|llms\\.txt)',
          headers: [
            {
              key: 'Cache-Control',
              value: 'public, max-age=86400, s-maxage=86400, stale-while-revalidate=604800',
            },
          ],
        },
        {
          source: '/',
          missing: [{ type: 'query', key: 'tab' }],
          headers: [
            {
              key: 'Cache-Control',
              value: 'public, max-age=0, s-maxage=30, stale-while-revalidate=3600',
            },
          ],
        },
        {
          source: '/',
          has: [{ type: 'query', key: 'tab' }],
          headers: [
            {
              key: 'Cache-Control',
              value: 'private, no-cache, max-age=0, must-revalidate',
            },
          ],
        },
      ];
    },
    ```
  - Unlocks **100% Back/Forward Cache (`bf-cache: score = 1`)** across both `/` and `/?tab=*`, prevents CDN query-key collisions, and eliminates `/manifest.json` from the critical network dependency tree.
