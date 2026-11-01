# Next.js 16 Turbopack, Font Hygiene & Production Build Patterns

Companion reference for `frontend-performance-lighthouse/SKILL.md`. Contains full implementation templates and production war-story remediations for Auth Guest Isolation, Self-Hosted Font Hygiene, Vite/Rollup Chunk Splitting, Next.js 16 RSC/Turbopack Manifest Isolation, `bf-cache`, and PWA Service Worker SWR.

---

## 0. Pure Interaction-Driven Lossless Telemetry (`TelemetryDeferredLoader.tsx`)

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

  if (!initializedQueues.current && typeof window !== 'undefined') {
    window.dataLayer = window.dataLayer || [];
    if (!window.gtag) {
      window.gtag = function () {
        window.dataLayer.push(arguments);
      };
      window.gtag('js', new Date());
      if (gaMeasurementId) {
        window.gtag('config', gaMeasurementId, {
          send_page_view: false,
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

## 1. Invisible Auth Iframes Elimination (Guest Isolation & Instant Rehydration)

The Firebase Auth Web SDK initializes a hidden cross-origin iframe (`/__/auth/iframe`), creating a 1.2s–3.5s waterfall that stalls mobile CPU and network threads on public landing pages where users are not logged in.

1. **Guest Isolation**: Do NOT instantiate Auth SDK on public routes. Instantiate only upon explicit user action (clicking "Login" or navigating to protected dashboard).
2. **Instant Rehydration**: Read cached profile synchronously in `useEffect` from fast local storage to render the user state immediately, deferring heavy SDK verification to idle time:

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
    const cached = localStorage.getItem('auth_user_cache');
    if (cached) {
      try {
        setUser(JSON.parse(cached));
      } catch {
        // Ignore corrupt cache
      }
    }

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

## 2. Font Preconnect, Self-Hosted WOFF2 & Critical CSS Inlining

### A. Next.js `next/font/google` Clean Configuration (No Unused Preconnects)
When using `next/font/google`, Next.js downloads font files at build time and serves them from `/_next/static/media/`. Never add manual `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />` in `app/layout.tsx`, as it triggers Lighthouse's *Unused preconnect* warning and wastes TLS handshakes.

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

### B. Static & Multi-Page Sites: Eliminating Font-Swap CLS (`0.259` $\to$ `0.000`)
1. **Self-Host WOFF2 Fonts on Same Origin**: Place subsetted font files in `/fonts/` (`inter-latin.woff2`, `jetbrains-mono-latin.woff2`).
2. **Preload Primary Subsets in `<head>`**:
   ```html
   <link rel="preload" href="/fonts/inter-latin.woff2" as="font" type="font/woff2" crossorigin />
   ```
3. **Use `font-display: optional`**:
   ```css
   @font-face {
     font-family: 'Inter';
     font-style: normal;
     font-weight: 100 900;
     font-display: optional; /* Guarantees Zero Layout Shift */
     src: url('/fonts/inter-latin.woff2') format('woff2');
   }
   ```
4. **Critical CSS Inlining**: Never ship `cdn.tailwindcss.com` (126 KB runtime JIT). Compile via Tailwind CLI (`--minify`) and inline `<30 KB` critical CSS in `<style id="critical-css">`, loading secondary stylesheets with `media="print" onload="this.media='all'"`.

---

## 3. Production Build Hygiene & Web Server Delivery (§9.1 – §9.18)

### 9.1. Production Console & Debugger Stripping (`esbuild.drop`)
In `vite.config.ts`, strip `console` and `debugger` calls during production builds so mobile CPUs never serialize large objects on the main thread:
```typescript
export default defineConfig(({ mode }) => ({
  esbuild: {
    drop: mode === "production" ? ["console", "debugger"] : [],
  },
}));
```

### 9.2. Non-Blocking Google Fonts & TCP/TLS Socket Warming (Non-Self-Hosted)
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
```

### 9.3. Public Asset Hygiene, Favicon Sizing & Multi-SPA Subpath Parity Guard
- Never reference raw PNGs (>100KB) as favicons (`≤16KB` target).
- Evict unreferenced `public/` hero/mascot PNGs (>500KB) and convert static icons to WebP (<20KB).
- **Multi-SPA Subpath Reverse Proxy Parity Guard**: When two SPAs share a domain (e.g. `/admin*` and `/*`), prefix subpath SPA assets with `import.meta.env.BASE_URL` (`/admin/icons/...`), mirror shared icons, add an Nginx `.png` $\to$ `.webp` rewrite rule, and bump PWA Workbox `cacheName`.

### 9.4. Reverse Proxy & Edge CDN Headers
Delegated to `infra-performance-optimization` (§2 and §4).

### 9.5. Tier 1 Dynamic Overlays, Conditional Mount Gating & Constant Isolation (`React.lazy`)
1. Extract shared constants (`REQUEST_TYPES`, status badges) out of modal files into `*-constants.ts` so importing constants never pulls the modal chunk into the parent route.
2. Gate `<React.Suspense>` behind the boolean open state (`{modalOpen && <React.Suspense ...>}`) and prefetch on button `onMouseEnter` / `onTouchStart`:
```tsx
import { REQUEST_TYPES } from "./request-constants";
const loadDetailsModal = () => import("./ShiftDutyDetailsModal");
const ShiftDutyDetailsModal = React.lazy(loadDetailsModal);

<button onMouseEnter={loadDetailsModal} onTouchStart={loadDetailsModal} onClick={() => setModalOpen(true)}>
  Xem chi tiết
</button>
{modalOpen && (
  <React.Suspense fallback={null}>
    <ShiftDutyDetailsModal modalOpen={modalOpen} setModalOpen={setModalOpen} />
  </React.Suspense>
)}
```

### 9.6. Non-Recursive Image Error Fallback & CLS Avatar Guard
Always declare `width`, `height`, `loading="lazy"`, `decoding="async"`, and clear `e.currentTarget.onerror = null` before setting a fallback `src` to prevent infinite microtask error loops (`INP > 1000ms`):
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
    e.currentTarget.onerror = null;
    if (!e.currentTarget.src.endsWith("/icons/default-avatar.webp")) {
      e.currentTarget.src = "/icons/default-avatar.webp";
    }
  }}
/>
```

### 9.7. Tier 2 Heavy Vendor Engines, Secondary Tabs & Below-the-Fold Quarantine
Quarantine `react-markdown`, `highlight.js`, `react-big-calendar`, `@fullcalendar/react`, `@tanstack/react-table`, `recharts`, `lightweight-charts`, `canvas-confetti`, `xlsx`, `exceljs`, and `jspdf` behind `React.lazy()` with fixed-height skeleton fallbacks (`h-96`), and dynamically `await import("@/lib/payrollExport")` inside click handlers.

### 9.8. Barrel Re-Export (`index.ts`) Decoupling & Nested Overlay Quarantine
Never mix static and lazy imports from the same folder barrel (`components/tasks/index.ts`), and never import lightweight hooks from UI component barrels. Always import directly from constituent module files (`@/components/tasks/staff/StaffTasksTable`).

### 9.9. Next.js 16 RSC `<Suspense>` `div[hidden]#S:0` & React 19 Fizz `$RV` 2.3s Paint-Holding Trap
When a Server Component (`app/page.tsx`) has already awaited its data, never wrap the returned synchronous view in `<Suspense>` or call `useSearchParams()` in a top-level Client Component (`HomeTabs`). Doing so triggers a CSR bailout (`<div hidden id="S:0">`) and React 19's `setTimeout($RV, 2300)` delay on Slow 4G. Pass `initialTab={searchParams?.tab || 'overview'}` from the Server Component and verify `curl -s https://your-domain.com | grep -c 'id="S:0"'` outputs `0`.

### 9.10. Next.js 16 Turbopack Server-to-Client Manifest Merging (`entryJSFiles` Pollution)
Turbopack merges client dependencies of all modules imported by `app/page.tsx` into `page_client-reference-manifest.js`. Keep the default landing tab (`OverviewTab`) as a pure Server Component (pure `<svg><polyline>` sparklines, native `<a href="/?tab=...">` with event delegation) and quarantine secondary tab `'use client'` trees behind a dynamic client loader (`LazyTabContent.tsx`), cutting initial `entryJSFiles` by **94.6%** (`760 KB` $\to$ `41.1 KB`).

### 9.11. RSC Flight Payload (`self.__next_f.push`) Diet & Pre-Computed SSR Summaries
Never pass raw 365-day historical series (`36.5 KB`) as props from a Server Component to a `'use client'` component. Pre-compute compact server summaries (`~350 bytes`) for initial SSR and fetch full time series on client interaction (`showChart === true`).

### 9.12. `next/font/google` `latin-ext` (`84.37 KiB`) vs `vietnamese` (`10.8 KiB`) Cascade Overlap Trap
`next/font/google` declares `latin-ext` (`84.37 KiB`) after `vietnamese` (`10.8 KiB`) with overlapping Vietnamese codepoints (`Ă, ă, Đ, đ, Ơ, ơ, Ư, ư, Ỳ-Ỹ`), forcing Chrome to download the `84.37 KiB` `latin-ext` file at depth 3 (`Element render delay = 1,540 ms`). Self-host only `inter-latin.woff2` (`~48 KB`) and `inter-vietnamese.woff2` (`~10.8 KB`) in `public/fonts/`, preload both in `<head>`, inline only those 2 `@font-face` blocks, and replace `transition-all` on above-the-fold buttons with `transition-colors` / `transition-transform`.

### 9.13. Unlocking `bf-cache` on Dynamic Next.js Routes (`send-payload.js` `Cache-Control` Override)
Configure explicit `Cache-Control` headers in `next.config.mjs` `async headers()` (`public, max-age=0, s-maxage=30, stale-while-revalidate=3600` for `/` without `?tab`, and `private, no-cache, max-age=0, must-revalidate` without `no-store` for `/?tab=*`) so `send-payload.js` preserves them and unlocks 100% `bf-cache` (`score = 1`).

### 9.14. PWA Service Worker (`sw.js`) Instant HTML SWR, RSC Bypass & 404 Chunk Self-Healing
1. Bypass `_rsc`, `rsc: 1`, `next-router-prefetch: 1`, `text/x-component`, and `/api/*`.
2. Guard navigation cache with `contentType.includes('text/html')`.
3. Use canonical URLs (stripping `?fbclid=`, `?zarsrc=`, `?utm_*`) with instant `Stale-While-Revalidate` (`<10ms` TTFB from device storage).
4. If any `/_next/static/chunks/*.js` returns HTTP 404 after a deploy, evict cached HTML navigation entries in `CACHE_NAME` to prevent reload loops.

### 9.15. In-Memory Multi-Route Coordinator Shell Navigation (`history.replaceState`)
Use `window.history.replaceState({ tab: target }, '', targetRoute)` instead of `router.replace()` for initial smart tab routing in shared coordinator shells, and set `prefetch={false}` on `<Link>` tabs that switch state in memory.

### 9.16. React 19 Hydration Error `#418` DOM-Wipe Trap
Never read `localStorage` synchronously inside Zustand/Redux store initializers (`create(() => getInitialCachedState())`). Initialize with SSR-identical defaults on Frame 0 and rehydrate inside `useEffect` wrapped in `React.startTransition`.

### 9.17. Next.js 16 Turbopack Synchronous Preload Cache (`createPreloadableTab`)
Wrap `next/dynamic` loaders in a single-importer memory cache (`createPreloadableTab`) and trigger `preload()` on `<BottomNav>` `onPointerEnter` / `onTouchStart` or after `≥ 3,600ms` idle (never via `80ms–200ms` mount timers that pollute Lighthouse TBT).

### 9.18. Hidden Root Bundle Leaks (`app/global-error.tsx` & Transitive Auth Imports)
In `app/global-error.tsx`, dynamically `import("@sentry/nextjs")` inside `useEffect` instead of a top-level import (`~51 KB` saved). In API helpers, check `localStorage` session tokens before dynamically importing `@/lib/firebase/firebaseConfig` (`152 KB` saved).
