// Staged states and acts are the educational register's machinery: a component's
// condition changes over the story, and a progressive story may clear the whole
// canvas per design-generation. Both are opacity windows on ONE master timeline,
// and both are invisible to every existing sweep -- the caption, containment and
// glyph checks all measure a single instant, so a stage that never appears, an
// act that bleeds through its successor, or a recap running out of order all
// ship green. This check seeks the timeline and looks.
//
// The contract it reads is `data-window="A,B"` on every staged element -- A,B
// are percent of the master where the element is visible; an element that
// returns carries several, space-separated: data-window="10,20 85,88". The
// build emits the keyframes AND the annotations from the same storyboard table,
// so a green run here means the storyboard is what actually renders.
// See references/camera-beat.md -> "Scenario timeline -- staged states and acts".
//
//   node verify-staged-windows.mjs <url> [--acts] [--reduced-motion] [--master <ms>]
//
// Serve over HTTP, never file://.
import puppeteer from "./resolve-puppeteer.mjs";

const VISIBLE_MIN = 0.9;   // inside its window an overlay must be fully on
const HIDDEN_MAX = 0.1;    // outside it must be fully off, not merely dimmed
const OFF_PROBE = 3;       // percent of master outside each edge, past the ~0.6s crossfade

const argv = process.argv.slice(2);
let url = null, wantActs = false, wantReduced = false, masterFlag = null;
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  if (a === "--acts") wantActs = true;
  else if (a === "--reduced-motion") wantReduced = true;
  else if (a === "--master") masterFlag = Number(argv[++i]);
  else if (!url) url = a;
}
if (!url) {
  console.error("usage: verify-staged-windows.mjs <url> [--acts] [--reduced-motion] [--master <ms>]");
  process.exit(2);
}

const fails = [];
const note = (m) => console.log(`  ${m}`);

const browser = await puppeteer.launch({ headless: true });
const page = await browser.newPage();
if (wantReduced) await page.emulateMediaFeatures([{ name: "prefers-reduced-motion", value: "reduce" }]);
await page.goto(url, { waitUntil: "networkidle2" });
await page.evaluate(() => document.fonts.ready);
await new Promise(r => setTimeout(r, 400));

// --- the annotated set --------------------------------------------------
// Index into document order is the handle: every later probe re-queries the
// same selector, so the i-th opacity always belongs to the i-th spec.
const raw = await page.evaluate(() => [...document.querySelectorAll("[data-window]")].map(el => ({
  win: el.getAttribute("data-window") || "",
  act: el.getAttribute("data-act"),
  cls: (el.getAttribute("class") || "").trim(),
  tag: el.tagName.toLowerCase(),
})));

// House rule: a check that finds nothing FAILS. An un-annotated staged cut is
// an unverified one, and silence is exactly what it would report.
if (!raw.length) {
  console.error("FAIL: zero [data-window] elements found -- wrong url, or the build never emitted the window annotations");
  await browser.close();
  process.exit(1);
}

const specs = raw.map((r, i) => {
  const windows = [];
  for (const pair of r.win.split(/\s+/).filter(Boolean)) {
    const [a, b] = pair.split(",").map(Number);
    if (!Number.isFinite(a) || !Number.isFinite(b) || b <= a || a < 0 || b > 100)
      fails.push(`[${i}] ${label(r)}: malformed data-window segment "${pair}" (want A,B with 0 <= A < B <= 100)`);
    else windows.push([a, b]);
  }
  if (!windows.length) fails.push(`[${i}] ${label(r)}: data-window="${r.win}" yielded no usable window`);
  return { ...r, i, windows };
});

function label(r) {
  return `${r.tag}${r.cls ? "." + r.cls.split(/\s+/).join(".") : ""}${r.act != null ? ` (act ${r.act})` : ""}`;
}

// --- master duration ----------------------------------------------------
// Read it from the page so the check cannot disagree with the file it checks;
// --master is the escape hatch for a cut with no .camera wrapper.
const cameraDur = await page.evaluate(() => {
  const cam = document.querySelector(".camera");
  if (!cam) return null;
  const d = getComputedStyle(cam).animationDuration.split(",")[0].trim();
  if (d.endsWith("ms")) return parseFloat(d);
  if (d.endsWith("s")) return parseFloat(d) * 1000;
  return null;
});
const master = (cameraDur && cameraDur > 0) ? cameraDur : masterFlag;
// Reduced-motion mode never seeks -- a correct reduced-motion block sets
// `animation: none`, which is exactly the state that makes the master
// unreadable. Demanding it there would fail every well-behaved page.
if (!wantReduced && !(master > 0)) {
  console.error("FAIL: cannot determine the master duration -- no animated .camera on the page; pass --master <ms>");
  await browser.close();
  process.exit(1);
}

console.log(`${url}`);
console.log(`  ${wantReduced ? "prefers-reduced-motion: reduce" : `master ${master}ms`}` +
            `, ${specs.length} annotated element(s)`);

// --- reduced-motion mode ------------------------------------------------
// Nothing to seek here: the informative end state is the finished architecture,
// so exactly ONE act -- the last -- may be on screen, at rest.
if (wantReduced) {
  const acts = specs.filter(s => s.act != null);
  if (!acts.length) {
    console.error("FAIL: --reduced-motion needs act groups; no element carries data-act");
    await browser.close();
    process.exit(1);
  }
  const opacities = await readOpacities(null);
  const lastAct = Math.max(...acts.map(s => Number(s.act)));
  for (const s of acts) {
    const o = opacities[s.i];
    if (Number(s.act) === lastAct) {
      if (!(o >= VISIBLE_MIN)) fails.push(`reduced-motion: final act ${s.act} is not visible (opacity ${fmt(o)})`);
    } else if (!(o <= HIDDEN_MAX)) {
      fails.push(`reduced-motion: act ${s.act} still visible (opacity ${fmt(o)}) -- only the final act may render`);
    }
  }
  note(`final act = ${lastAct}; ${acts.length} act group(s) checked at rest`);
  await finish();
}

// --- per-window visibility ----------------------------------------------
// One probe list, deduped by time: seeking is the expensive part, reading every
// element's opacity at a seeked instant is free.
const probes = new Map();   // time% -> [{i, want}]
const add = (t, i, want) => {
  const key = round(t);
  if (!probes.has(key)) probes.set(key, []);
  probes.get(key).push({ i, want });
};
const inAnyWindow = (s, t) => s.windows.some(([a, b]) => t >= a && t <= b);

for (const s of specs) {
  for (const [a, b] of s.windows) {
    add((a + b) / 2, s.i, "on");
    for (const t of [mod100(a - OFF_PROBE), mod100(b + OFF_PROBE)]) {
      // An element with several windows legitimately sits ON just outside one
      // of them -- skip a probe that lands inside any window it owns, rather
      // than reporting the neighbour window as a leak.
      if (!inAnyWindow(s, t)) add(t, s.i, "off");
    }
  }
}

for (const [t, wants] of [...probes.entries()].sort((x, y) => x[0] - y[0])) {
  const opacities = await readOpacities(t);
  for (const { i, want } of wants) {
    const o = opacities[i], s = specs[i];
    if (want === "on" && !(o >= VISIBLE_MIN))
      fails.push(`t=${t}% : ${label(s)} should be VISIBLE inside window ${winStr(s)} but opacity is ${fmt(o)}`);
    if (want === "off" && !(o <= HIDDEN_MAX))
      fails.push(`t=${t}% : ${label(s)} should be HIDDEN outside window ${winStr(s)} but opacity is ${fmt(o)}`);
  }
}
note(`${probes.size} timeline probes across ${specs.reduce((n, s) => n + s.windows.length, 0)} window(s)`);

// --- acts mode ----------------------------------------------------------
if (wantActs) {
  const acts = specs.filter(s => s.act != null && s.windows.length);
  if (!acts.length) {
    console.error("FAIL: --acts asked for, but no element carries data-act");
    await browser.close();
    process.exit(1);
  }
  acts.sort((a, b) => Number(a.act) - Number(b.act));

  // Isolation: an act owns the WHOLE canvas, so at any instant one act holds,
  // every other act is off. A bleed-through reads as two designs at once.
  for (const s of acts) {
    for (const [a, b] of s.windows) {
      const t = round((a + b) / 2);
      const opacities = await readOpacities(t);
      for (const other of acts) {
        if (other === s) continue;
        if (!(opacities[other.i] <= HIDDEN_MAX))
          fails.push(`t=${t}% (act ${s.act} holding): act ${other.act} is not cleared -- opacity ${fmt(opacities[other.i])}`);
      }
    }
  }

  // Order: acts enter in act order, and their recap windows replay in the same
  // order. Comparing first-starts and last-starts catches both.
  for (let k = 1; k < acts.length; k++) {
    const prev = acts[k - 1], cur = acts[k];
    if (!(cur.windows[0][0] > prev.windows[0][0]))
      fails.push(`act ${cur.act} opens at ${cur.windows[0][0]}%, not after act ${prev.act} at ${prev.windows[0][0]}% -- acts must appear in order`);
    const pLast = prev.windows[prev.windows.length - 1][0], cLast = cur.windows[cur.windows.length - 1][0];
    if (!(cLast > pLast))
      fails.push(`act ${cur.act}'s last window opens at ${cLast}%, not after act ${prev.act}'s at ${pLast}% -- recap must replay in act order`);
  }

  // Parking: the loop must come to rest on the finished design, not on a fade.
  const final = acts[acts.length - 1];
  const finalEnd = final.windows[final.windows.length - 1][1];
  if (finalEnd < 100)
    fails.push(`final act ${final.act} ends at ${finalEnd}% -- its last window must run to 100% so the loop parks on the finished design`);
  note(`${acts.length} act(s) checked for isolation, order and parking`);
}

await finish();

// --- helpers ------------------------------------------------------------
async function readOpacities(tPercent) {
  const ms = tPercent == null ? null : (tPercent / 100) * master;
  return page.evaluate((ms) => {
    if (ms != null) {
      // Pause everything and hard-seek. Ambient loops have their own durations;
      // they are periodic, so the same absolute time lands them consistently.
      for (const a of document.getAnimations()) {
        try { a.pause(); a.currentTime = ms; } catch { /* finite fill-less animation */ }
      }
      document.documentElement.getBoundingClientRect();   // force a style flush
    }
    return [...document.querySelectorAll("[data-window]")]
      .map(el => parseFloat(getComputedStyle(el).opacity));
  }, ms);
}

function mod100(t) { return ((t % 100) + 100) % 100; }
function round(t) { return Math.round(t * 1000) / 1000; }
function fmt(o) { return Number.isFinite(o) ? o.toFixed(3) : String(o); }
function winStr(s) { return s.windows.map(([a, b]) => `${a},${b}`).join(" "); }

async function finish() {
  await browser.close();
  if (fails.length) {
    console.log("STAGED-WINDOW VIOLATIONS:");
    fails.forEach(f => console.log(`  ${f}`));
    process.exit(1);
  }
  console.log("  OK -- every staged window renders when and only when it should");
  process.exit(0);
}
