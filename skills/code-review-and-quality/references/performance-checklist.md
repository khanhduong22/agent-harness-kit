# Performance Review Checklist

Companion reference for `code-review-and-quality` and `shipping-and-launch`.

## 1. Database & Backend Hot Paths
- [ ] Zero N+1 queries inside loops (`for ... await db.query`); batch with `WHERE id = ANY($1)` or `Promise.all` for independent reads.
- [ ] High-frequency `WHERE` and `ORDER BY` clauses are backed by composite B-Tree indexes (equality columns first, range/sort columns second).
- [ ] Paginated endpoints enforce a hard upper `limit` ceiling (e.g. `Math.min(limit, 100)`) and avoid unbounded `SELECT *`.
- [ ] Expensive aggregations or external API calls use SingleFlight in-flight deduplication and TTL jitter.

## 2. Frontend Bundle & Core Web Vitals
- [ ] Interactive overlays (modals, drawers, dialogs, confetti) are dynamically imported (`next/dynamic` or `React.lazy`) and gated behind open state.
- [ ] Below-the-fold heavy widgets (`recharts`, calendars, rich-text editors, `xlsx`) are lazy-loaded inside fixed `min-height` wrappers (`CLS = 0`).
- [ ] Images declare explicit `width` and `height`; above-the-fold LCP hero image uses `fetchpriority="high"` without `loading="lazy"`.
- [ ] Zero synchronous `localStorage` reads during SSR initial state that would trigger React hydration error `#418`.
