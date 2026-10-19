Skill 200Lab «Diagram director: vẽ sơ đồ system design có chuyển động thành một file HTML/SVG tự chứa, kèm kit miễn phí của 200Lab» v1 · phần lean-verify «Lean verify: the pre-delivery checklist with evidence per item, text-sync sweep, bounded repair (own)» — hướng dẫn do 200Lab soạn cho agent; ai_tutor rules vẫn quyết ngân sách, footer và việc hoàn thành bài.

# Lean verify: the pre-delivery checklist, each item with its evidence

Phase 5 without the kit (`own`: the engine's pre-delivery checklist, condensed). Run every item
before handing the file over. Each item names its evidence: a command and its output, a screenshot
you looked at, or a value read from the file. In a chat app without a shell, preview the artifact
if your client can and say what you saw, and ask the learner to open the file and confirm the
visual items. An item without evidence is reported as `not verified`, with the reason.

## Mechanical checks (with a shell)

Save this helper outside the learner's repo (a temp folder) and run it on the cut and its sheet:

```python
# usage: python3 dd_check.py docs/diagrams/<slug>.html docs/diagrams/<slug>.sheet.md
import re, sys, html
page, sheet = open(sys.argv[1], encoding="utf-8").read(), open(sys.argv[2], encoding="utf-8").read()
hosts = sorted(set(re.findall(r"(?:https?:)?//([\w-]+(?:\.[\w-]+)+)", page)) - {"www.w3.org"})
print("hosts named anywhere (advisory):", hosts or "none")
print("script src tags:", len(re.findall(r"<script[^>]*\bsrc\s*=", page)))
print("reduced-motion blocks:", page.count("prefers-reduced-motion"))
has = lambda *xs: [bool(re.search(x, page)) for x in xs]
print("a11y system-design (role=img, title, desc):", *has(r"role=[\"']img", r"<title\b", r"<desc\b"))
print("a11y process (figure label, figcaption, hidden overlay):",
      *has(r"<figure[^>]*aria-label", r"<figcaption\b", r"class=[\"']edges[^>]*aria-hidden=[\"']true"))
nodes = re.findall(r"data-node-id=[\"']([^\"']+)", page)
edges = re.findall(r"data-from=[\"']([^\"']+)[\"'][^>]*data-to=[\"']([^\"']+)", page)
dupes = sorted({n for n in nodes if nodes.count(n) > 1})
dangling = [e for e in edges if e[0] not in nodes or e[1] not in nodes]
print(f"nodes {len(nodes)} (duplicates {dupes or 'none'}), edges {len(edges)}, dangling {dangling or 'none'}")
sec = lambda v, u: float(v) / (1000 if u == "ms" else 1)
TIME = r"(?<![-\w.])(\d+(?:\.\d+)?)(ms|s)\b"
durs = {sec(*m) for d in re.findall(r"animation-duration\s*:([^;{}]+)", page) for m in re.findall(TIME, d)}
durs |= {sec(*re.findall(TIME, item)[0]) for d in re.findall(r"animation\s*:([^;{}]+)", page)
         for item in d.split(",") if re.findall(TIME, item)}
print("durations (s):", sorted(durs), "· time tokens:", sorted(set(re.findall(r"(--[\w-]+)\s*:\s*(\d[\d.]*m?s)\b", page))))
body = re.sub(r"<style.*?</style>|<script.*?</script>", "", page, flags=re.S)
strings = sorted({html.unescape(t).strip() for t in re.findall(r">([^<>]+)<", body) if t.strip()})
print("\nTEXT-SYNC: each string must appear in the sheet (or map to a sheet line by hand)")
for s in strings:
    print("  ok  " if s in sheet else "  ??  ", s)
```

| # | Check | Pass when |
|---|---|---|
| 1 | Self-contained | the render below logs `external requests: none` with the network blocked (kit mode: only the two Google Fonts hosts) and `script src tags: 0`; the source host list is advisory: explain each host it names |
| 2 | Reduced motion exists | at least one block, and it neutralises every animation (read it) |
| 3 | Accessible structure | the line for the cut's genre all `True`; system-design: every node group has a `<title>`; a visible legend |
| 4 | The graph is declared | node count equals the sheet's COMPONENTS rows (a component drawn once per pane or act repeats its id there only), no dangling edge, every sheet flow hop drawn |
| 5 | Loop seams | every duration (or time token) divides the master loop; at most 12 animated edges (count the animated edge classes) |
| 6 | Compositor-only motion | every `@keyframes` animates only `transform`, `opacity`, `clip-path`, `stroke-dashoffset`, `offset-distance` (read each block) |
| 7 | Text-sync | every `??` line is either mapped to a sheet line in the table below or removed from the file |

Text-sync table (paste into the delivery notes, or the sheet's end):

```markdown
| on screen | sheet line | owner check |
|---|---|---|
| "1 per user" (store sub-label) | GUARANTEE OWNERSHIP row 2 | owner = stock-store ✓ |
```

Every number on screen is in NUMBERS in its display form; every guarantee sits on its owner.

## Visual checks: render and look

Take a full-size screenshot (and, in beats mode, one per hold) and look at it, with the network
blocked so the request log proves item 1. Any headless browser works; with Playwright (Python):

```python
from playwright.sync_api import sync_playwright
SMALLEST = """() => Math.min(...[...document.querySelectorAll('body *')].filter(e => e.getClientRects().length
  && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()))
  .map(e => parseFloat(getComputedStyle(e).fontSize) * (e.getScreenCTM?.()?.a ?? 1)))"""
GAP = """() => { const r = [...document.querySelectorAll('[data-node-id]')].map(e => e.getBoundingClientRect());
  let m = Infinity; r.forEach((a, i) => r.slice(i + 1).forEach(c => m = Math.min(m,
  Math.max(c.left - a.right, a.left - c.right, c.top - a.bottom, a.top - c.bottom)))); return m; }"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1600, "height": 900}); ext, errs = [], []
    pg.route("**/*", lambda r: r.continue_() if r.request.url.startswith(("file:", "data:", "blob:"))
             else (ext.append(r.request.url), r.abort()))
    pg.on("console", lambda m: m.type == "error" and errs.append(m.text))
    pg.goto("file:///abs/path/docs/diagrams/<slug>.html")
    for t_ms in [0, 4800, 9600]:          # hold midpoints from the storyboard; static: [0]
        pg.evaluate("t => document.getAnimations().forEach(a => { a.pause(); a.currentTime = t; })", t_ms)
        pg.screenshot(path=f"/tmp/hold-{t_ms}.png")
        print(t_ms, "smallest text px:", pg.evaluate(SMALLEST), "· min node gap px:", pg.evaluate(GAP))
    pg.emulate_media(reduced_motion="reduce"); pg.reload(); pg.screenshot(path="/tmp/reduced.png")
    print("external requests:", ext or "none", "· console errors:", errs or "none"); b.close()
```

| # | Check | Pass when |
|---|---|---|
| 8 | Nothing collides | `min node gap px` at least 40 at the overview (negative = overlap); on the shot no edge through a node or any text, no label touching a node, text at least 6 px inside its shape |
| 9 | Edges attach right | each edge ends on its node, on the side facing the far end, not a hair off a corner |
| 10 | Legible | `smallest text px` at least 14 static (the engine's flat-minimal floor, `own`); at each hold, 24 landscape or 28 vertical |
| 11 | Reduced motion | the reduced-motion shot shows the informative end state: final overview, packets parked, queues at level, captions hidden |
| 12 | Not colour or motion alone | the reduced-motion shot in greyscale still tells roles and states apart (labels, chips, line styles) |
| 13 | Contrast | every text and stroke colour listed with its background and the computed WCAG ratio, each at least 4.5:1 |
| 14 | Beats | each hold frames its subject and its upstream node; the spotlight brackets sit on the caption's subjects; the caption card covers no edge or label it talks about; the last hold is the overview |
| 15 | Vertical cut | every readable element inside x 60-890, y 150-1540 |
| 16 | Labels are true (review) | each label and caption names its sheet line in the text-sync table; note any that reads wrong on the shot |
| 17 | Persona audit (review, teaching) | the sheet's persona table names an on-screen element for every standing question |
| 18 | Console clean | `console errors: none` |

Items 8-9, 11-12 and 14-17 rest on looking: report what you saw and who looked (`observed by the
builder` or `by an independent reviewer`); 16-17 are review observations, never a PASS.

## Independent look

When your client can start a subagent, hand a fresh read-only one the sheet, the HTML, the
screenshots and this checklist. It reports PASS, FAIL or `not verified` per item (16-17 as
observations) with the evidence and edits nothing; a builder grading its own frames is the gap the mechanical checks do
not close. Composition and taste are advisory notes, never a FAIL.

## Repair and delivery

- Count failing items. Repair while the count reaches a new minimum; after two rounds without
  one, stop and report what still fails. A check removed or loosened to pass is not a repair.
- After the last edit, re-run the helper and re-take the screenshots: a pass is only for the
  file as delivered.
- The delivery message lists: what the diagram shows in one sentence, the results by item number
  (passed, failed, not verified and why), custom shapes, assumptions shown on screen, and the
  labels of every claim's source (`200Lab`, `own`, `external`).
