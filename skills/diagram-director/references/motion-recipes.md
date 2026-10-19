# Motion Recipes

Full cookbook for every `Motion ID` in `data/motion.csv`. Each `## <motion-id>` heading below is a
cross-reference anchor (`motion.csv → Recipe Ref`) — the heading text must stay byte-identical to the
`Motion ID` cell. Do not rename, reorder columns of meaning, or add prose between the heading and the
`Semantics` line.

Read this file only after `search.py --domain motion` or `--blueprint` has told you which motion IDs
apply — do not read it end to end for a single diagram.

Global rules that apply to every recipe below (see `docs/code-standards.md`):
- Animate only `transform`, `opacity`, `clip-path`, `stroke-dashoffset`, `offset-distance`. Never
  animate `width`, `height`, `top`, `left`, or `box-shadow` — those trigger layout/paint, not compositing.
- Every recipe needs a `@media (prefers-reduced-motion: reduce)` block that renders the **informative
  end state** described below, not a mid-animation freeze frame.
- `css-only` recipes work in both `--target local` and `--target artifact`. `needs-js` recipes are
  `local`-only — see `style-guides.md` for the artifact-safe substitute for each style.

---

## dash-flow

**Semantics.** Data is actively flowing between two connected services along this edge — a continuous
transfer, not a one-time event.

**Technique.** `stroke-dashoffset` marching-ants loop on the connector path.

**Runtime.** `css-only`.

**Full snippet.**
```css
.edge--dash-flow {
  stroke-dasharray: 8 6;
  stroke-dashoffset: 56;
  animation: dashflow 1.2s linear infinite;
}
@keyframes dashflow {
  to { stroke-dashoffset: 0; }
}
```

**Tuning.** Duration 1200ms, easing `linear`, no stagger (single continuous line per edge).

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .edge--dash-flow { animation: none; stroke-dasharray: none; stroke-dashoffset: 0; }
}
```
Renders a solid stroke with no dash pattern — the informative end state (the connection exists and is
active) survives without motion.

**Performance note.** GPU-compositable. Keep the dash segment count low on paths over 500px to avoid jank.

**Do / Don't.** Do use for connectors representing continuous data transfer. Don't use for a single
one-time event — use `connection-draw-in` instead.

---

## packet-travel

**Semantics.** A single discrete request or message unit is moving from sender to receiver right now.

**Technique.** `offset-path` + `offset-distance` travel animation.

**Runtime.** `css-only`.

**Full snippet.**
```css
.packet {
  offset-path: path('M0 0 L240 0');
  offset-distance: 0%;
  animation: travel 1.4s ease-in-out infinite;
}
@keyframes travel {
  to { offset-distance: 100%; }
}
```

**Tuning.** Duration 1400ms, easing `ease-in-out`. For concurrent packets, offset each one's
`animation-delay` by 150–300ms so they don't visually overlap.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .packet { animation: none; offset-distance: 100%; }
}
```
Packet icon parked at the destination node; the path itself renders as a static solid line.

**Performance note.** Cheap — runs on the compositor when only `offset-distance` is animated.

**Do / Don't.** Do use for a single discrete message or request unit. Don't use for aggregate/bulk
continuous transfer — use `stream-continuous` instead.

---

## pulse-glow

**Semantics.** This node is currently active, healthy, and processing work.

**Technique.** Opacity + `filter: drop-shadow` breathing loop.

**Runtime.** `css-only`.

**Full snippet.**
```css
.node--pulse-glow {
  animation: pulseglow 1.6s ease-in-out infinite;
}
@keyframes pulseglow {
  0%, 100% { opacity: 1;  filter: drop-shadow(0 0 3px currentColor); }
  50%      { opacity: .6; filter: drop-shadow(0 0 10px currentColor); }
}
```

**Tuning.** Duration 1600ms, easing `ease-in-out`. No stagger by default, or 200ms per node when
highlighting a group simultaneously.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .node--pulse-glow { animation: none; opacity: 1; filter: drop-shadow(0 0 6px currentColor); }
}
```
Node rendered at full opacity with a fixed static glow — no pulsing.

**Performance note.** `drop-shadow` is GPU-accelerated but costly at scale; limit to under 10
simultaneously pulsing nodes.

**Do / Don't.** Do use to mark a currently active, healthy, or processing node. Don't use to represent
an error state — use `error-propagation` or `circuit-breaker-flicker` instead.

---

## queue-fill

**Semantics.** Messages are accumulating in a buffer while waiting to be consumed.

**Technique.** `clip-path` inset fill-level bar.

**Runtime.** `css-only`.

**Full snippet.**
```css
.bar--queue-fill {
  clip-path: inset(0 100% 0 0);
  animation: queuefill 2s ease-out forwards;
}
@keyframes queuefill {
  to { clip-path: inset(0 var(--empty, 20%) 0 0); }
}
```

**Tuning.** Duration 2000ms, easing `ease-out`, no stagger.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .bar--queue-fill { animation: none; clip-path: inset(0 var(--empty, 20%) 0 0); }
}
```
Bar rendered at its current fill level — no growth animation.

**Performance note.** `clip-path` insets are compositor-friendly; avoid animating `box-shadow` alongside it.

**Do / Don't.** Do use for message queue, buffer, or bucket depth. Don't use for binary on/off
states — use `pulse-glow` or a plain opacity transition instead.

---

## round-trip

**Semantics.** A request left this service and its response is coming back — visualizes round-trip latency.

**Technique.** JS-driven two-leg timeline (outbound then return) along an `offset-path`.

**Runtime.** `css-only`. (Was `needs-js` until its CSS class shipped; the JS form only adds
runtime dynamism this skill never uses — see the note below.)

> **CSS-only fallback (2026-08).** CSS-only approximation shipped as `.anim-round-trip` (one hop, out-dwell-back on a loop). JS adds variable hop count, an event trigger and a distinct response token. See `templates/snippets/motion-blocks.css`.

**Full snippet (CSS legs, JS-triggered).**
```css
.leg {
  offset-distance: 0%;
  animation: leg .6s ease-in forwards paused;
}
.leg.play { animation-play-state: running; }
@keyframes leg {
  to { offset-distance: 100%; }
}
```
```js
// JS variant: play the outbound leg, then the return leg after it lands.
function playRoundTrip(outboundEl, returnEl, outboundMs = 600) {
  outboundEl.classList.add('play');
  setTimeout(() => returnEl.classList.add('play'), outboundMs);
}
```

**Tuning.** Total 1200ms. Return-leg `animation-delay` equals the outbound duration (e.g. 600ms) so the
response starts only after the request arrives.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .leg { animation: none; offset-distance: 100%; }
}
```
Both legs shown as static solid arrows; the response arrow is already parked at the origin.

**Performance note.** authored statically because hop count varies per scenario; keep to 4 or fewer hops to
avoid jank. **Local-file only** — do not select for `--target artifact`.

**Do / Don't.** Do use for request/response pairs to visualize latency. Don't use for fire-and-forget
async messages — use `dash-flow` or `fanout-broadcast` instead.

---

## retry-loop

**Semantics.** A failed call is being retried automatically after backoff; expect repeated attempts.

**Technique.** JS-computed attempt sequence, each attempt a scale/opacity pop-in.

**Runtime.** `css-only`. (Was `needs-js` until its CSS class shipped; the JS form only adds
runtime dynamism this skill never uses — see the note below.)

> **CSS-only fallback (2026-08).** CSS-only approximation shipped as `.anim-retry-loop` (author 3-5 attempt markers, `--i` each; delay grows as `i*dur + i^2*backoff`). JS adds the real attempt count, real backoff/jitter and a failure trigger. See `templates/snippets/motion-blocks.css`.

**Full snippet.**
```css
.attempt {
  opacity: 0;
  transform: scale(.8);
  animation: retry .5s ease-out forwards paused;
}
.attempt.play { animation-play-state: running; }
@keyframes retry {
  to { opacity: 1; transform: scale(1); }
}
```
```js
// JS computes attempt count and backoff gap per scenario, then plays each .attempt in turn.
function playRetries(attempts, backoffMs = 300) {
  attempts.forEach((el, i) => setTimeout(() => el.classList.add('play'), i * (500 + backoffMs)));
}
```

**Tuning.** 500ms per attempt, easing `ease-out`. Each attempt is delayed by the previous attempt's
duration plus a backoff gap; JS computes the attempt count.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .attempt { animation: none; opacity: 1; transform: scale(1); }
}
```
Single arrow shown looping back to the origin with a static retry-count badge.

**Performance note.** authored statically because attempt count is variable per scenario; cap rendered attempts
at 3–5. **Local-file only.**

**Do / Don't.** Do use to show automatic retry-with-backoff behavior. Don't use for a single manual
retry — a plain `connection-draw-in` is enough.

---

## circuit-breaker-flicker

**Semantics.** The circuit breaker is toggling between closed and open state to protect a failing dependency.

**Technique.** Stepped opacity + stroke-color toggle.

**Runtime.** `css-only`.

**Full snippet.**
```css
.cb {
  animation: flicker 1.8s steps(2, jump-none) infinite;
}
@keyframes flicker {
  0%, 49%  { opacity: 1;  stroke: var(--ok); }
  50%, 100% { opacity: .5; stroke: var(--err); }
}
```

**Tuning.** Duration 1800ms, easing `steps(2, jump-none)`, no stagger.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .cb { animation: none; opacity: 1; stroke: var(--err); }
}
```
Breaker shown in its current state color with no flicker.

**Performance note.** Cheap — opacity and stroke-color swap only.

**Do / Don't.** Do use to show a breaker actively tripping between closed and open. Don't use for a
permanently open or closed breaker — use a static color instead.

---

## cache-hit-miss

**Semantics.** A lookup just resolved from cache (hit) or fell through to the source of truth (miss).

**Technique.** One-shot opacity flash on the result badge.

**Runtime.** `css-only`.

**Full snippet.**
```css
.result--cache-hit-miss {
  transform-box: fill-box; transform-origin: center;
  animation: hitmiss .8s ease-out 1 both;
}
@keyframes hitmiss {
  0%   { opacity: 0; transform: scale(.9); }
  40%  { opacity: 1; transform: scale(1);  }
  100% { opacity: 1; transform: scale(1);  }
}
```

> **Corrected 2026-08.** The badge used to fade back to `opacity: 0` at 100% with no fill-mode, so it
> ended invisible and then snapped back to full opacity the instant the animation finished — and that
> contradicted its own reduced-motion end state below. It now pops in and settles visible.
> Shipped as `.anim-cache-hit-miss` in `templates/snippets/motion-blocks.css`.

**Tuning.** Duration 800ms, easing `ease-out`, plays once (not looping), no stagger.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .result--cache-hit-miss { animation: none; opacity: 1; }
}
```
Static hit or miss badge shown next to the cache node — no flash.

**Performance note.** Cheap opacity flash only.

**Do / Don't.** Do use immediately after a lookup to show hit vs. miss outcome. Don't use for ongoing
cache warm-up — use `batch-tick` or `stream-continuous` instead.

---

## fanout-broadcast

**Semantics.** One event was published and is being delivered to every subscriber simultaneously.

**Technique.** JS-generated per-branch reveal (opacity + `stroke-dashoffset`).

**Runtime.** `css-only`. (Was `needs-js` until its CSS class shipped; the JS form only adds
runtime dynamism this skill never uses — see the note below.)

> **CSS-only fallback (2026-08).** CSS-only approximation shipped as `.anim-fanout-broadcast` (one authored `<path>` per subscriber, `--i` = publish order). JS adds branch generation from the subscriber list and replay per publish. See `templates/snippets/motion-blocks.css`.

**Full snippet.**
```css
.branch {
  opacity: 0;
  animation: branch .5s ease-out forwards paused;
}
.branch.play { animation-play-state: running; }
@keyframes branch {
  to { opacity: 1; stroke-dashoffset: 0; }
}
```
```js
// JS generates N branch elements (one per subscriber) and staggers their reveal.
function playFanout(branches, stepMs = 100) {
  branches.forEach((el, i) => setTimeout(() => el.classList.add('play'), i * stepMs));
}
```

**Tuning.** 500ms per branch, easing `ease-out`. Each subscriber branch delayed 80–120ms in publish order.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .branch { animation: none; opacity: 1; stroke-dashoffset: 0; }
}
```
All branch lines drawn solid and fully visible at once.

**Performance note.** authored statically because subscriber count is scenario-variable; batch DOM writes for
over 10 targets. **Local-file only.**

**Do / Don't.** Do use for pub/sub or event broadcast to multiple consumers. Don't use for
point-to-point request/response — use `round-trip` instead.

---

## backpressure

**Semantics.** Downstream is signaling it cannot keep up, so the flow rate is being throttled back.

**Technique.** `transform: scaleX` narrowing loop on the connector.

**Runtime.** `css-only`.

**Full snippet.**
```css
.flow--backpressure {
  animation: backpressure 1.4s ease-in-out infinite;
}
@keyframes backpressure {
  0%, 100% { transform: scaleX(1); }
  50%      { transform: scaleX(.4); }
}
```

**Tuning.** Duration 1400ms, easing `ease-in-out`, no stagger.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .flow--backpressure { animation: none; transform: scaleX(.4); }
}
```
Connector rendered narrowed to its throttled width, static.

**Performance note.** `transform: scaleX` is compositor-friendly.

**Do / Don't.** Do use when downstream signals it cannot keep up with the inbound rate. Don't use for
a hard rejection — use `load-shedding` instead.

---

## heartbeat

**Semantics.** This node is periodically confirming it is alive to a health monitor.

**Technique.** `transform: scale` double-beat pulse.

**Runtime.** `css-only`.

**Full snippet.**
```css
.node--heartbeat {
  transform-origin: center;
  animation: heartbeat 1s ease-in-out infinite;
}
@keyframes heartbeat {
  0%, 100% { transform: scale(1); }
  25%      { transform: scale(1.15); }
  40%      { transform: scale(1); }
  55%      { transform: scale(1.1); }
}
```

**Tuning.** Duration 1000ms, easing `ease-in-out`. No stagger, or 300ms offset per node in a
health-check group.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .node--heartbeat { animation: none; transform: scale(1); }
}
```
Node shown with a static heartbeat icon, no scaling.

**Performance note.** `transform: scale` is cheap and compositor-friendly.

**Do / Don't.** Do use for periodic liveness or health-check signals. Don't use for one-time boot
confirmation — use `node-boot-sequence` instead.

---

## connection-draw-in

**Semantics.** A new connection or dependency between two components was just established.

**Technique.** `stroke-dashoffset` one-shot draw-in.

**Runtime.** `css-only`.

**Full snippet.**
```css
.edge--connection-draw-in {
  stroke-dasharray: 200;
  stroke-dashoffset: 200;
  animation: drawin .8s ease-out forwards;
}
@keyframes drawin {
  to { stroke-dashoffset: 0; }
}
```

**Tuning.** Duration 800ms, easing `ease-out`, plays once, no stagger.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .edge--connection-draw-in { animation: none; stroke-dashoffset: 0; }
}
```
Connector rendered fully drawn, solid stroke.

**Performance note.** `stroke-dashoffset` draw-in is compositor-friendly for paths under roughly 1000px.

**Do / Don't.** Do use once when a new dependency or connection first appears in the diagram. Don't
use for a connector already part of the steady-state topology.

---

## node-boot-sequence

**Semantics.** Components are starting up in a defined order during system initialization.

**Technique.** `animation-delay` stagger, one fade-in per node in boot order.

**Runtime.** `css-only`.

**Full snippet.**
```css
/* --i = boot order, set in the markup */
.node--boot {
  opacity: 0;
  animation: boot .4s ease-out forwards;
  animation-delay: calc(var(--i, 0) * .4s);
}
@keyframes boot {
  to { opacity: 1; }
}
```

> **Corrected 2026-08.** Same reason as `error-propagation`: `--i` keeps boot order explicit in the
> markup instead of tying it to sibling position (which also breaks when non-node siblings such as
> `<defs>` or edges share the parent). Shipped as `.anim-node-boot-sequence` in
> `templates/snippets/motion-blocks.css`.

**Tuning.** 400ms per node, easing `ease-out`. Each subsequent node delayed by 400ms via
`nth-child(n)` at `n * 0.4s`.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .node--boot { animation: none; opacity: 1; }
}
```
All nodes shown fully opaque and present — no sequential reveal.

**Performance note.** Opacity fade-in only; cheap even for 10+ nodes.

**Do / Don't.** Do use to show system startup or deployment order. Don't use for a steady-state
running system.

---

## error-propagation

**Semantics.** A failure in one component is cascading to the components that depend on it. (Covers
the "cascade-ripple" framing.)

**Technique.** `animation-delay` stagger outward from the failing node, `filter: drop-shadow` in the error color.

**Runtime.** `css-only`.

**Full snippet.**
```css
/* --i = hop distance from the failing node, set in the markup */
.node--err {
  animation: errorprop .5s ease-in forwards;
  animation-delay: calc(var(--i, 0) * .5s);
}
@keyframes errorprop {
  to { filter: drop-shadow(0 0 6px var(--err, var(--ink-error, currentColor))); opacity: .8; }
}
```

> **Corrected 2026-08.** `:nth-child()` staggers by DOM order, but a cascade travels the DEPENDENCY
> graph — the two agree only by luck. `--i` makes hop distance explicit and survives DOM reordering.
> `--err` also falls back to `--ink-error`, which is the token base templates actually declare.
> Shipped as `.anim-error-propagation` in `templates/snippets/motion-blocks.css`.

**Tuning.** 500ms per hop, easing `ease-in`. Each downstream hop delayed 500ms from the failing node outward.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .node--err { animation: none; filter: drop-shadow(0 0 6px var(--err)); opacity: .8; }
}
```
All affected nodes shown in the error color at once — no sequential reveal.

**Performance note.** `drop-shadow` filter per node; limit propagation depth to 6 or fewer nodes for smoothness.

**Do / Don't.** Do use to show a fault spreading through dependent services. Don't use for an
isolated single-node failure — use `pulse-glow` with the error color instead.

---

## load-shedding

**Semantics.** Excess requests are being deliberately dropped to protect system stability.

**Technique.** Fade-and-fall opacity + translateY on the dropped request icon.

**Runtime.** `css-only`.

**Full snippet.**
```css
.dropped {
  animation: shed .6s ease-in forwards;
}
@keyframes shed {
  0%   { opacity: 1; transform: translateY(0); }
  100% { opacity: 0; transform: translateY(12px); }
}
```

**Tuning.** Duration 600ms, easing `ease-in`, plays once, no stagger.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .dropped { animation: none; opacity: 0; }
}
```
Dropped request shown as a static, faded, crossed-out icon.

**Performance note.** Opacity plus transform fade; cheap.

**Do / Don't.** Do use to show requests deliberately rejected under overload. Don't use for requests
queued for later processing — use `queue-fill` instead.

---

## replication-sync

**Semantics.** Data written to the primary is being copied to replica nodes to keep them consistent.

**Technique.** JS-generated per-replica opacity fade-in.

**Runtime.** `css-only`. (Was `needs-js` until its CSS class shipped; the JS form only adds
runtime dynamism this skill never uses — see the note below.)

> **CSS-only fallback (2026-08).** CSS-only approximation shipped as `.anim-replication-sync` (one authored element per replica, `--i` = replication order). JS adds replica generation from the topology and replay per write. See `templates/snippets/motion-blocks.css`.

**Full snippet.**
```css
.replica {
  opacity: .3;
  animation: sync .6s ease-out forwards paused;
}
.replica.play { animation-play-state: running; }
@keyframes sync {
  to { opacity: 1; }
}
```
```js
// JS generates N replica elements per topology and staggers their sync fade-in.
function playReplication(replicas, stepMs = 125) {
  replicas.forEach((el, i) => setTimeout(() => el.classList.add('play'), i * stepMs));
}
```

**Tuning.** 600ms per replica, easing `ease-out`. Each replica fade-in delayed 100–150ms in
replication order.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .replica { animation: none; opacity: 1; }
}
```
All replicas shown fully opaque and in sync — no fade sequence.

**Performance note.** authored statically because replica count varies by topology; opacity-only animation
keeps it cheap. **Local-file only.**

**Do / Don't.** Do use to show data propagating from a primary to replica nodes. Don't use for a
one-off manual data copy — use `dash-flow` once instead.

---

## batch-tick

**Semantics.** Work is accumulating and will be processed together on the next scheduled interval.

**Technique.** `steps()` timing counter/track loop.

**Runtime.** `css-only`.

**Full snippet.**
```html
<g clip-path="url(#batchClip)"><g class="batch"><!-- 5 slots --></g></g>
```
```css
.batch {
  transform-box: fill-box;   /* so -100% = the track's own width, not the viewBox */
  animation: tick 3s steps(5, end) infinite;
}
@keyframes tick {
  to { transform: translateX(-100%); }
}
```

**Tuning.** Duration 3000ms, easing `steps(5, end)`, no stagger. The step count must equal the slot
count in the markup, otherwise the conveyor slides by fractions of a slot and stops reading as ticks.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .batch { animation: none; transform: none; }
}
```
Batch parked on a slot boundary with every job visible in the track.

> **Corrected 2026-08.** Two fixes. (1) Without `transform-box: fill-box`, `-100%` resolves against the
> SVG viewBox, so the conveyor jumps by the whole canvas width. (2) The reduced-motion fallback used to
> be `translateX(-100%)`, which shifts the whole track out of its clip and leaves an empty box — the
> opposite of informative. It now rests at its untransformed position.
> Shipped as `.anim-batch-tick` in `templates/snippets/motion-blocks.css`.

**Performance note.** `transform: translateX` with `steps()` is compositor-friendly.

**Do / Don't.** Do use for scheduled or cron-driven batch processing intervals. Don't use for
continuous unbounded streams — use `stream-continuous` instead.

---

## stream-continuous

**Semantics.** Data is flowing continuously and indefinitely, not as discrete events.

**Technique.** Linear translate loop over a tiled group (one tile per cycle).

**Runtime.** `css-only`.

**Full snippet.**
```html
<g clip-path="url(#streamClip)">
  <g class="stream"><!-- ticks every --stream-tile units, ONE extra tile of overhang --></g>
</g>
```
```css
.stream {
  animation: streamflow 2s linear infinite;
}
@keyframes streamflow {
  to { transform: translateX(calc(-1 * var(--stream-tile, 40px))); }
}
```

> **Corrected 2026-08.** The snippet used to animate `background-position`. SVG elements have no CSS
> background, so it did nothing on the only elements this library targets, and `background-position` is
> a paint property in any case. Replaced with the translate loop the performance note already named as
> the alternative. `--stream-tile` MUST equal the tick spacing or the loop jumps at every wrap.
> Shipped as `.anim-stream-continuous` in `templates/snippets/motion-blocks.css`.

**Tuning.** Duration 2000ms, easing `linear`, no stagger.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .stream { animation: none; transform: none; }
}
```
Connector shown as a solid line with a static flow-direction arrow.

**Performance note.** Translate or `background-position` loop is cheap and compositor-friendly.

**Do / Don't.** Do use for unbounded, always-on data streams such as event streams or log tailing.
Don't use for a bounded discrete transfer — use `dash-flow` or `packet-travel` instead.

---

## throttle-gate

**Semantics.** Requests above the allowed rate are being held back at a gate before entering the system.

**Technique.** `clip-path` gate-narrowing loop.

**Runtime.** `css-only`.

**Full snippet.**
```css
.gate {
  clip-path: inset(0 0 0 0);
  animation: throttle 1.2s ease-in-out infinite;
}
@keyframes throttle {
  50% { clip-path: inset(0 40% 0 40%); }
}
```

**Tuning.** Duration 1200ms, easing `ease-in-out`, no stagger.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .gate { animation: none; clip-path: inset(0 40% 0 40%); }
}
```
Gate shown in its current open or closed width, static.

**Performance note.** `clip-path` is compositor-friendly.

**Do / Don't.** Do use to show a rate limiter admitting or blocking requests. Don't use for total
request rejection — use `load-shedding` instead.

---

## scale-out-spawn

**Semantics.** New instances are being created to handle increased load.

**Technique.** JS-generated per-instance scale/opacity pop-in.

**Runtime.** `css-only`. (Was `needs-js` until its CSS class shipped; the JS form only adds
runtime dynamism this skill never uses — see the note below.)

> **CSS-only fallback (2026-08).** CSS-only approximation shipped as `.anim-scale-out-spawn` (one authored element per instance, `--i` = spawn order). JS adds instance count from the scenario and replay per scaling event. See `templates/snippets/motion-blocks.css`.

**Full snippet.**
```css
.replica--spawn {
  opacity: 0;
  transform: scale(.5);
  animation: spawn .5s var(--ease-spring-snappy, ease-out) forwards paused;
}
.replica--spawn.play { animation-play-state: running; }
@keyframes spawn {
  to { opacity: 1; transform: scale(1); }
}
```
```js
// JS generates N new-instance elements per scenario and staggers their spawn-in.
function playScaleOut(instances, stepMs = 125) {
  instances.forEach((el, i) => setTimeout(() => el.classList.add('play'), i * stepMs));
}
```

**Tuning.** 500ms per instance, easing `var(--ease-spring-snappy)` — the damped-spring `linear()`
token from `templates/snippets/motion-blocks.css` (snippet: spring-easing-tokens), one ~9.5%
overshoot so the instance *lands* instead of arriving dead. `ease-out` is the var() fallback for a
stylesheet that did not copy the token block. Each new instance delayed 100–150ms in spawn order.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .replica--spawn { animation: none; opacity: 1; transform: scale(1); }
}
```
All new instances shown fully present at final scale — no spawn sequence.

**Performance note.** authored statically because instance count is scenario-variable; opacity plus scale keeps
each spawn cheap. **Local-file only.**

**Do / Don't.** Do use to show autoscaling adding capacity under load. Don't use for scale-down or
termination — invert the keyframe direction instead.

---

## token-bucket-refill

**Semantics.** Capacity tokens are being replenished over time and consumed by incoming requests.

**Technique.** `steps()` opacity/translate tick animation.

**Runtime.** `css-only`.

**Full snippet.**
```css
.token {
  opacity: 0;
  animation: refill 2s steps(4, end) infinite;
}
@keyframes refill {
  to { opacity: 1; transform: translateY(-16px); }
}
```

**Tuning.** Duration 2000ms, easing `steps(4, end)`, no stagger.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .token { animation: none; opacity: 1; transform: translateY(-16px); }
}
```
Bucket shown at its current token count, static tick marks.

**Performance note.** Opacity plus transform step animation; cheap.

**Do / Don't.** Do use to visualize rate-limiting via token accumulation and consumption. Don't use
for hard throttling with no accumulation — use `throttle-gate` instead.

---

## leader-election-pulse

**Semantics.** Nodes are voting and one candidate is becoming the new leader.

**Technique.** Finite candidate flicker followed by a continuous leader-glow loop on the winner.

**Runtime.** `css-only`.

**Full snippet.**
```css
.candidate {
  animation: elect 1s ease-in-out 2;
}
.leader {
  animation: leaderglow 1.6s ease-in-out infinite;
}
@keyframes elect {
  50% { opacity: .5; }
}
@keyframes leaderglow {
  0%, 100% { filter: drop-shadow(0 0 3px gold); }
  50%      { filter: drop-shadow(0 0 10px gold); }
}
```

**Tuning.** 1000ms per flicker cycle, easing `ease-in-out`. Candidate flicker plays twice, then the
winning node switches to the continuous leader-glow loop.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .candidate { animation: none; opacity: 1; }
  .leader { animation: none; filter: drop-shadow(0 0 6px gold); }
}
```
Winning node shown with a static leader badge and glow; others shown as plain followers.

**Performance note.** Cheap opacity and filter animation; limit to the candidate set size, typically
3–5 nodes.

**Do / Don't.** Do use for Raft or Paxos leader election, or primary promotion. Don't use for routine
heartbeats between an already-elected leader and followers — use `heartbeat` instead.

---

## state-transition-arrow

**Semantics.** The system just moved from one defined state to another in response to an event.

**Technique.** `stroke-dashoffset` draw-in plus color swap to the active-transition color.

**Runtime.** `css-only`.

**Full snippet.**
```css
.arrow--transition {
  stroke: var(--active, var(--ink-data, currentColor));
  stroke-dasharray: 40;
  stroke-dashoffset: 40;
  animation: transition .5s ease-out forwards;
}
@keyframes transition {
  to { stroke-dashoffset: 0; }
}
```

> **Corrected 2026-08.** The keyframe used to interpolate `stroke`. Stroke colour is a paint property —
> it repaints every frame and cannot be composited. The arrow is now set to `--active` statically and
> only `stroke-dashoffset` animates; the visible result and the end state are identical. `--active`
> falls back to the template's `--ink-data` (success ink), since no base template declares `--active`.
> Shipped as `.anim-state-transition-arrow` in `templates/snippets/motion-blocks.css`.

**Tuning.** Duration 500ms, easing `ease-out`, plays once, no stagger.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .arrow--transition { animation: none; stroke-dashoffset: 0; stroke: var(--active); }
}
```
Arrow shown fully drawn in the active-transition color; current state highlighted.

**Performance note.** `stroke-dashoffset` plus color swap; cheap.

**Do / Don't.** Do use to show a state machine or workflow moving between defined states. Don't use
for continuous flow with no discrete states — use `stream-continuous` instead.

---

## failover-reroute

**Semantics.** Traffic that was going to a failed node is being redirected to a healthy standby.
(Covers the "split-brain"/"partition-split" framing.)

**Technique.** Old-path fade-out followed by new-path draw-in.

**Runtime.** `css-only`.

**Full snippet.**
```css
.old-path {
  animation: fadeout .4s ease-in forwards;
}
.new-path {
  opacity: 0;
  stroke-dashoffset: 60;
  animation: reroute .6s ease-out .4s forwards;
}
@keyframes fadeout {
  to { opacity: .2; }
}
@keyframes reroute {
  to { opacity: 1; stroke-dashoffset: 0; }
}
```

**Tuning.** Total ~1000ms, easing `ease-out`. New-path `animation-delay` equals the old-path fade-out
duration (400ms) so reroute starts after failure is visible.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .old-path { animation: none; opacity: .2; }
  .new-path { animation: none; opacity: 1; stroke-dashoffset: 0; }
}
```
Failed path shown dimmed and crossed-out; new path shown solid and fully drawn.

**Performance note.** Opacity plus `stroke-dashoffset` on two elements only; cheap.

**Do / Don't.** Do use to show traffic switching from a failed node to a healthy standby. Don't use
for planned/manual traffic shifting — use `dash-flow` with a label instead.

---

## shard-distribute

**Semantics.** Data is being partitioned and routed to the specific shard that owns it. (Covers the
"split-brain"/"partition-split" framing for consistent hashing.)

**Technique.** JS-generated per-shard `offset-path` travel with opacity reveal.

**Runtime.** `needs-js`.

**Full snippet.**
```css
.shard {
  offset-distance: 0%;
  opacity: 0;
  animation: distribute .6s ease-out forwards paused;
}
.shard.play { animation-play-state: running; }
@keyframes distribute {
  to { offset-distance: 100%; opacity: 1; }
}
```
```js
// JS generates N shard-travel paths (one per shard key) staggered in shard-key order.
function playShardDistribute(shards, stepMs = 100) {
  shards.forEach((el, i) => setTimeout(() => el.classList.add('play'), i * stepMs));
}
```

**Tuning.** 600ms per shard, easing `ease-out`. Each shard's `animation-delay` staggered by 100ms in
shard-key order.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .shard { animation: none; offset-distance: 100%; opacity: 1; }
}
```
Each data row shown already parked at its owning shard — no travel animation.

**Performance note.** `needs-js` because shard count is scenario-variable; offset-path per shard
target. **Local-file only.**

**Do / Don't.** Do use to show consistent-hashing or range-based data partitioning. Don't use for
simple replication — use `replication-sync` instead.

---

## ttl-expiry

**Semantics.** A cached or session item has reached its time-to-live limit and is being evicted.

**Technique.** Delayed fade-and-shrink on the expiring item.

**Runtime.** `css-only`.

**Full snippet.**
```css
.item--ttl {
  animation: expire 3s ease-in forwards;
}
@keyframes expire {
  0%, 80% { opacity: 1; transform: scale(1); }
  100%    { opacity: 0; transform: scale(.7); }
}
```

**Tuning.** Duration 3000ms, easing `ease-in`, plays once, no stagger.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) {
  .item--ttl { animation: none; opacity: 0; }
}
```
Expired item shown removed or greyed-out immediately — no fade sequence.

**Performance note.** Opacity plus transform scale on a single element; cheap.

**Do / Don't.** Do use to show a cache entry or session reaching its time-to-live limit. Don't use for
manual/explicit eviction — use `load-shedding` or a plain fade instead.

## camera-beat

**Semantic.** The diagram narrates itself in timed acts ("beats"): the camera zooms to one or a few
components in story order, explains them with a caption and/or an interior detail view, then
returns to the full overview. Auto-plays on an infinite loop; no scroll, click, or hover control
(locked product decision).

**Technique.** One `transform` animation on a single `.camera` wrapper group (`transform-origin:
0 0`), keyed off one master duration that every ambient loop divides. Never animate `viewBox`.

**This entry is a stub by design.** Beats mode is a build mode, not a single effect — its full
contract (computed zoom `k_read`/`k_fit`, caption cards and wipe, beat spotlight, heading fade,
interior morph, language, reduced-motion, video export warm-up and sound) lives in
**`references/camera-beat.md`**. Read that file before building any beats diagram; use this row
only to discover the mode from `data/motion.csv`.

## state-timeline

**Semantic.** A component's condition CHANGES over the story — healthy → overloaded → down, and the
failure dominoes to its neighbours — with every transition keyed to the master timeline. The
educational counterpart to `camera-beat`: the camera tours, the state timeline *demonstrates*.

**Technique.** One overlay group per stage, `opacity` keyed to a window of the master duration
(`animation-duration: var(--master)`, `linear`, `infinite`). The base node is never mutated — paint
properties come off the compositor, same law as the beat spotlight. Each staged element also carries
`data-window="A,B"` (percent of master), which is what the render-side gate reads.

**This entry is a stub by design.** Staged states are a build mode, not a single effect — the full
contract (the window annotation contract, domino ordering, acts as temporal tiers, the recap pass,
reduced-motion, and the hard gates) lives in **`references/camera-beat.md` → "Scenario timeline —
staged states and acts"**. Read that section before staging any failure; use this row only to
discover the mode from `data/motion.csv`.

## shake-stress

**Semantic.** A component is trembling under a load it cannot absorb. This is the *educational*
register's intensity for `is-overloaded` — the reference register states the condition (chip, bar,
dash), this one makes it felt.

**Technique.** A tiny `transform` loop on the state's OVERLAY group (or a body group), never on the
base paint. It lives inside the state's `data-window`, so it starts and stops with the condition.

**Runtime.** `css-only`.

**Full snippet.**
```css
.anim-shake-stress { animation: shake-stress 120ms linear infinite; }
@keyframes shake-stress {
  0%, 100% { transform: translate(-1.5px, 0) }
  25%      { transform: translate(1.2px, -.6px) }
  50%      { transform: translate(-1.1px, .6px) }
  75%      { transform: translate(1.5px, 0) }
}
```

**Tuning.** 90–120ms per tremble is the legible band; below it the node blurs, above it the shake
reads as a slow wobble. Under a master timeline snap to a divisor first — 120ms divides a 38.4s
master 320 times. Amplitude is capped at ±1.5px: the node carries its own label, and past ~2px the
label stops being readable. One component trembles at a time; two in the same window need a
half-cycle offset or they read as mechanically linked.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) { .anim-shake-stress { animation: none; transform: none } }
```
The fill-level bar and the numeric chip carry the overload on their own — as they must anyway, since
motion is never the only channel.

**Performance note.** `transform` on one overlay group; the layer stays on the compositor.

**Do / Don't.** Do pair it with the chip that carries the number — the shake is the feeling, the
number is the story. Don't shake a dead node: stillness is death's meaning. Don't displace more than
2px.

## collapse-death

**Semantic.** The dying moment. The node buckles once as it goes down, then is permanently still.

**Technique.** A ONE-SHOT `transform` with `forwards` fill, played at the START of an `is-down`
window. What follows is the static dead state from `states.csv` (sparse dash, 40% fill, error
stroke, DOWN chip) — the collapse is the transition into it, not a condition of its own.

**Runtime.** `css-only`.

**Full snippet.**
```css
.anim-collapse-death { animation: collapse-death 480ms cubic-bezier(.3,.8,.4,1) 1 forwards; }
@keyframes collapse-death {
  0%   { transform: none }
  60%  { transform: translateY(6px) scale(.94) rotate(-1.5deg) }
  100% { transform: translateY(4px) scale(.96) rotate(-1deg) }
}
```

**Tuning.** 480ms, once — a divisor of a 38.4s master 80 times over. The easing does the work: fast
buckle, slow settle. In a domino, each victim's collapse starts at its own `is-down` onset, spaced
from the upstream one by that edge's propagation time in the sheet's event table.

**Reduced-motion fallback.**
```css
@media (prefers-reduced-motion: reduce) { .anim-collapse-death { animation: none; transform: none } }
```
The `is-down` static encoding is the resting truth; there is nothing to see collapse.

**Performance note.** One transform on the node body inside the window; `forwards` holds the settled
pose, so the rest of the window costs nothing.

**Do / Don't.** Do play it exactly once, at the window's start. Don't loop it — a node cannot die
twice — and don't animate paint (fill/stroke) alongside it; that takes the node off the compositor.
