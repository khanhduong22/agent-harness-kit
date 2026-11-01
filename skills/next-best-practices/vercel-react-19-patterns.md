# Vercel React 19 & Next.js Performance Rules (`vercel-labs/agent-skills`)

Synthesized from [`vercel-labs/agent-skills`](https://github.com/vercel-labs/agent-skills) (`★ 82k+` — `vercel-react-best-practices`, 70 rules across 8 priority categories). Apply these rules alongside `SKILL.md` when writing or reviewing React 19 and Next.js App Router code.

---

## 1. Eliminating Async Waterfalls (`CRITICAL`)

| Rule ID | Anti-Pattern (`❌`) | Production Pattern (`✅`) |
|---|---|---|
| **`async-cheap-condition-before-await`** | `const session = await getSession(); if (!isEnabled) return null;` | Check synchronous flags, params, and headers **before** executing any `await` |
| **`async-defer-await`** | Awaiting 3 queries at the top of a handler when 2 are only used inside an `else` branch | Start promises early or move `await` into the exact conditional branch that consumes the value |
| **`async-parallel`** | Sequential `await getUser(); await getPosts(); await getMetrics();` (`3 × RTT`) | `const [user, posts, metrics] = await Promise.all([getUser(), getPosts(), getMetrics()]);` (`1 × RTT`) |
| **`server-after-nonblocking`** | Awaiting analytics, audit logs, or webhook notifications before returning the HTTP response | Use Next.js `after(() => logAuditEvent(...))` so the user receives the response immediately |

---

## 2. Bundle Size & Dynamic Loading (`CRITICAL`)

| Rule ID | Anti-Pattern (`❌`) | Production Pattern (`✅`) |
|---|---|---|
| **`bundle-barrel-imports`** | Importing from giant barrel index files (`import { X } from '@/components'`) in client entry points | Import directly from the leaf module or configure `optimizePackageImports` in `next.config` |
| **`bundle-dynamic-imports`** | Statically importing modals, drawers, charts, rich-text editors, or confetti into page entry bundles | Use `next/dynamic(() => import('./ChartModal'), { ssr: false })` |
| **`bundle-defer-third-party`** | Loading Sentry, GA4, Clarity, or chat widgets synchronously during initial hydration | Defer telemetry and analytics until `requestIdleCallback` or first user interaction (`pointerdown`/`keydown`) |
| **`bundle-preload`** | Waiting until modal click to start downloading a heavy chunk | Preload the dynamic chunk on button `onMouseEnter` / `onFocus` for instant perceived response |

---

## 3. React Server Components (RSC) & Serialization (`HIGH`)

1. **`server-cache-react`**: Wrap shared server-side data fetchers (`getCurrentUser`, `getTenantConfig`) in `React.cache(fn)` so Layout, Page, and `generateMetadata` deduplicate them within a single request tick.
2. **`server-serialization`**: Never pass an entire 50-field database row or ORM model across the RSC-to-Client boundary (`<ClientCard user={fullDbUser} />`) when the client component only renders `user.name` and `user.avatarUrl`. Pick only the required primitive fields to shrink HTML flight payloads.
3. **`server-no-shared-module-state`**: Never store request-scoped state (current user, locale, auth token) in a mutable module-level variable inside SSR/RSC modules — concurrent requests on the same Node/Bun worker will leak data across users.
4. **`server-auth-actions`**: Treat every `'use server'` Server Action as a public HTTP POST endpoint: verify authentication, tenant authorization, and Zod input schema inside the action body itself.

---

## 4. Client Re-Render & Rendering Optimization (`MEDIUM-HIGH`)

1. **`rerender-derived-state-no-effect`**: Never use `useEffect(() => setFiltered(items.filter(...)), [items])` to compute derived state (which causes a double render pass). Compute derived values directly during render (`const filtered = useMemo(...)` or inline).
2. **`rerender-no-inline-components`**: Never declare `function SubComponent() {}` inside another component's body — React sees a new component reference on every render and unmounts/remounts its entire DOM subtree and focus state.
3. **`rendering-conditional-render`**: Prefer `count > 0 ? <Badge count={count} /> : null` over `count && <Badge count={count} />` (which renders a literal `0` in the DOM when `count === 0`).
4. **`rendering-content-visibility`**: Apply `content-visibility: auto; contain-intrinsic-size: 0 400px;` to long below-the-fold feed items or table sections to skip offscreen layout/paint work.
5. **`rerender-transitions`**: Wrap non-urgent tab switches, filter updates, and heavy chart re-renders in `startTransition(() => setFilter(next))` so typing and clicking stay `< 200ms INP`.
