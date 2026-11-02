# CDP Accessibility-Tree Targeting & Browser Daemon Isolation (`browser-use/browser-use`)

Distilled from `browser-use/browser-use` (`★ 119k+`, `skills/browser-use/SKILL.md`). Use when automating Chrome via Chrome DevTools Protocol (`CDP`), inspecting live DOM/Accessibility states, or coordinating browser tabs across parallel tasks.

---

## 1. Escalation Rule: Plain HTTP First, Browser Second

Never launch or attach to a browser if a plain HTTP request (`curl` / `fetch`) can verify the public page, API payload, or static asset headers. Escalate to CDP browser control only when the task requires:
- Interactive state transitions (`click`, `type`, drag-and-drop, modal flows).
- Client-side JS hydration, WebGL/Canvas rendering, or Core Web Vitals profiling.
- Authenticated session cookies or bot-protected origins.

---

## 2. Accessibility-Tree First Element Targeting (`Accessibility.getFullAXTree`)

Prefer querying the CDP Accessibility Tree over taking repeated full-page screenshots or writing fragile CSS/XPath selectors:

1. **Query AX Tree**: Call `Accessibility.getFullAXTree` and filter nodes by `role`, `name`, and `backendDOMNodeId` (filter in script before printing — raw trees contain thousands of nodes).
2. **Compute Viewport Box Center**:
   ```python
   box = cdp("DOM.getBoxModel", backendNodeId=node_id)["model"]["content"]
   x, y = sum(box[0::2]) / 4, sum(box[1::2]) / 4
   ```
   *(If `x` or `y` is negative or outside viewport bounds, scroll the element into view first.)*
3. **Compositor-Level Coordinate Click**: Dispatch mouse events at `(x, y)` via `Input.dispatchMouseEvent`. Compositor-level coordinate clicks naturally pierce **Shadow DOM** boundaries and **cross-origin iframes** without needing custom JS walkers.
4. **Verify State Mutation**: Confirm the interaction succeeded via a targeted DOM/AX check or network response assertion before proceeding.

---

## 3. Background Tab Discipline & Focus Emulation

- **Never Steal OS Window Focus**: Do not call `Target.activateTarget` / `bringToFront` automatically during background verification — it yanks Chrome in front of the user's active window.
- **Handling Focus-Gated Pages in Background**: If a page pauses timers, animations, or blur-sensitive dropdowns while backgrounded, enable CDP focus emulation inside a `try / finally` block:
  ```python
  try:
      cdp("Emulation.setFocusEmulationEnabled", enabled=True)
      # Perform interaction and assert expected DOM state
  finally:
      cdp("Emulation.setFocusEmulationEnabled", enabled=False)
  ```
- **Tab Reuse & Cleanup**: Reuse existing matching tabs instead of spawning duplicate tabs for the same URL. Close temporary tabs created by the agent upon task completion, but never close pre-existing user tabs.

---

## 4. Multi-Agent Browser Serialization vs Isolation

- **Single Local Chrome = Shared Serialized Lane**: A local Chrome instance shares one active profile and cookie jar. If multiple subagents switch tabs and dispatch CDP inputs concurrently on the same local browser, they will race and click inside each other's tabs.
- **Concurrency Rule**: Either serialize browser verification steps through a single coordinator agent, or run parallel Playwright E2E workers in isolated headless browser contexts (`browser.newContext()`).
