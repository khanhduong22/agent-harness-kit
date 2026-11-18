# Modern Browser Scheduling, Speculation Rules & Resource Priority

> Distilled from `GoogleChrome/modern-web-guidance` (Performance guides). Complements `SKILL.md` with platform-level INP main-thread scheduling, speculative prerendering, fetch priority, and passive event primitives.

---

## 1. Prioritized Task Scheduling (`scheduler.postTask()` & `scheduler.yield()`)

Keep Interaction to Next Paint (**INP <= 200ms**, target **<= 50ms**) green by separating urgency across queues (`postTask`) and slicing long loops (`yield`).

### Three Priority Tiers with `scheduler.postTask()`
- `'user-blocking'`: Input handling, focus restoration, immediate UI state updates.
- `'user-visible'`: Above-the-fold secondary rendering (default when omitted).
- `'background'`: Analytics, prefetch prep, search index building, telemetry.

```js
// Dynamic cancellation + priority promotion via TaskController
const controller = new TaskController({ priority: 'background' });

// CRITICAL TRAP: Do NOT pass `{ priority, signal: controller.signal }` together!
// Passing an explicit `priority` overrides `controller.signal` and ignores `controller.setPriority()`.
const taskPromise = scheduler.postTask(async () => {
  await buildSearchIndex();
}, { signal: controller.signal });

// Later, promote immediately if the user opens search, or cancel on navigation
controller.setPriority('user-blocking');
```

### Breaking Long Tasks (> 50ms) with `scheduler.yield()`
`scheduler.postTask()` only orders when tasks *start*. Once a loop runs past 50ms, periodically `await scheduler.yield()` using a time deadline so pending input events and paints flush immediately while preserving continuation priority (unlike `setTimeout(0)` which demotes to the back of the macrotask queue):

```js
async function processLargeDataset(items) {
  let deadline = performance.now() + 50; // 50ms Long Task threshold

  for (const item of items) {
    processItem(item);

    if (performance.now() >= deadline) {
      if ('scheduler' in window && 'yield' in window.scheduler) {
        await window.scheduler.yield();
      } else {
        await new Promise((r) => setTimeout(r, 0));
      }
      deadline = performance.now() + 50;
    }
  }
}
```

> **Continuation Inheritance**: Calling `await scheduler.yield()` inside a `scheduler.postTask()` callback automatically inherits the enclosing task's priority and `TaskSignal` abort state.

---

## 2. Speculation Rules API (`<script type="speculationrules">`)

Eliminate navigation TTFB for likely next pages using browser-managed prefetch and prerender rules instead of ad-hoc JS hover prefetchers.

### `prefetch` vs `prerender` Trade-offs
| Mode | What It Does | Resource Cost | Best Fit |
|---|---|---|---|
| `prefetch` | Downloads navigation HTML doc only | Low (no JS exec or subresources) | Broad link sets, dynamic pages, `eager` rules |
| `prerender` | Downloads & renders in a hidden background tab | Higher (CPU/memory/subresources) | High-confidence next pages, `moderate` (hover) / `conservative` (pointerdown) |

### Eagerness Settings
- `immediate`: Speculate right away (pair with narrow `urls` list rules only).
- `eager`: On small cursor/scroll hints toward matching links.
- `moderate`: After ~200ms hover / focus signal (safest default for `prerender`).
- `conservative`: On pointerdown / mousedown right before navigation completes.

### Safe Production Document Rule with Exclusions
```html
<script type="speculationrules">
{
  "prefetch": [{
    "tag": "nav-prefetch",
    "where": {
      "and": [
        { "href_matches": "/*" },
        { "not": { "href_matches": "/api/*" } },
        { "not": { "href_matches": "/logout*" } },
        { "not": { "href_matches": "/*\\?*(^|&)add-to-cart=*" } },
        { "not": { "selector_matches": "[data-no-prerender], [download]" } }
      ]
    },
    "eagerness": "eager"
  }],
  "prerender": [{
    "tag": "nav-prerender",
    "where": {
      "and": [
        { "href_matches": "/*" },
        { "not": { "href_matches": "/api/*" } },
        { "not": { "href_matches": "/logout*" } },
        { "not": { "selector_matches": "[data-no-prerender], [download], [target=_blank]" } }
      ]
    },
    "eagerness": "moderate"
  }]
}
</script>
```
- **Server Observability**: Speculation requests send the `Sec-Speculation-Tags` header matching `"tag"` (and `Sec-Purpose: prefetch;anonymous-client-ip` / `prefetch;prerender`). Never trigger state-mutating GET routes or count ad impressions until `document.prerendering` becomes `false` (`prerenderingchange` event).

---

## 3. Fetch Priority, Native `scrollend`, Containment & Analytics

### Resource Fetch Priority (`fetchpriority` & Fetch `priority`)
- **LCP Hero Image**: Add `fetchpriority="high"` on the single LCP hero `<img>`. **NEVER** combine `fetchpriority="high"` with `loading="lazy"`.
- **Hidden Above-the-Fold Media**: Add `fetchpriority="low"` on hidden carousel slides, closed modals, or mega-menu images. Omit `fetchpriority` (never set `auto`) for standard images.
- **Background Fetches**: Pass `{ priority: 'low' }` to `fetch()` calls for telemetry, logging, or speculative background sync so they don't contend with critical API requests. Never use the deprecated `importance` key.

### Replace Scroll Debounce Timers with `scrollend`
Use the native `scrollend` event instead of fragile `scroll` + `setTimeout()` heuristics before triggering heavy DOM queries or telemetry:
```js
scroller.addEventListener('scrollend', () => {
  const activeSection = findMostVisibleSection(scroller);
  syncVisibleState(activeSection);
});
```

### Offscreen Rendering & Reliable Telemetry Exit Flushing
- **Offscreen Containment**: Apply `content-visibility: auto; contain-intrinsic-size: auto 500px;` to long-page sections and feeds so browsers skip layout/paint offscreen while preserving scrollbar stability and in-page find (`hidden="until-found"` for expandable collapsed regions).
- **Batched Telemetry Without Breaking `bfcache`**:
  - Prefer `fetchLater(url, { activateAfter: 10_000, body, signal })` (where supported) to debounce and batch analytics events with guaranteed browser transmission on tab close.
  - Otherwise flush on `document.addEventListener('visibilitychange', ...)` when `document.visibilityState === 'hidden'` using `fetch(..., { keepalive: true })` or `navigator.sendBeacon()`. **NEVER** register `unload` (or unnecessary `beforeunload`) handlers, as they disable the browser back/forward cache (`bfcache`).
