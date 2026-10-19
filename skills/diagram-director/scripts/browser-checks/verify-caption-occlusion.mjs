// A caption card painted over the very thing its caption explains.
//
// THE GAP THIS CLOSES. `verify-caption-boxes.mjs` compares a caption's text with its own
// card. `verify-hold-geometry.mjs` sweeps edges against nodes and text but SKIPS
// `.beat-caption` by design ("caption cards ride above the scene", its sweep-2 filter), so
// nothing in the runner ever measured a card against the scene UNDER it. A delivered cut
// reached review with four beats whose card sat on the edge its own sentence named -- the
// worst hid both inputs the sentence named -- and one that covered an edge label until
// `outcomes` read as `outc...`. Every gate was green.
//
// THE RULE (references/camera-beat.md -> Captions). A caption card never covers an edge
// LABEL, and never covers an edge of its OWN beat's subjects. It may cross other scenery:
// a lower-third over plain background is the house idiom, so that case is reported and
// never fails.
//
// WHEN IT MEASURES. At an instant inside the caption's OWN window where the card is fully
// revealed -- after the wipe-in, before the wipe-out -- with the camera pinned to the hold
// that instant falls in, and only over elements actually VISIBLE then (act isolation and
// staged windows are respected because visibility is read off the computed style at that
// seeked instant, never assumed).
//
// SUBJECTS ARE DERIVED, NOT DECLARED. The beat already names its subjects on screen: the
// spotlight brackets lit in the same window enclose them. So the subject set is the
// `g.node[data-node-id]` whose shape sits inside a lit `.node__focus` bbox, and the subject
// edges are the `path.edge` whose `data-from`/`data-to` names one of them. No new manifest
// field, nothing for an author to forget to write down. A caption with no lit bracket (an
// overview beat, or a cut with captions and no spotlight) has NO subject set: the label
// rule still applies and the subject-edge rule is N-A for that caption, said out loud
// rather than counted as a pass.
//
//   node verify-caption-occlusion.mjs <url> [--manifest <path>] [--tol N] [--subject-pad N]
import puppeteer from "./resolve-puppeteer.mjs";
import { readManifest, cameraHolds, masterMs, freezeAt, pinCamera, parseArgs }
  from "./hold-frames.mjs";
import { installInk } from "./ink-box.mjs";
import { installGeometry } from "./page-geometry.mjs";
import { readCaptionState, measureCaption } from "./caption-occlusion-probe.mjs";

const USAGE = "usage: verify-caption-occlusion.mjs <url> [--manifest <path>] [--tol N] "
            + "[--subject-pad N]";
const { url, manifest: manifestPath, extra } = parseArgs(process.argv.slice(2), USAGE);
const TOL = Number(extra.tol ?? 0.5);              // screen px of overlap that still passes
const SUBJECT_PAD = Number(extra["subject-pad"] ?? 2);   // slack on "inside the bracket"
// Where inside its own window to look. The midpoint first, because a wipe lives at the
// ends; the rest are a ladder for a caption whose wipe eats more of its window than usual.
const FRACTIONS = [0.5, 0.65, 0.35, 0.8, 0.2];

const manifest = readManifest(manifestPath);
const captions = manifest.captions || [];
const holds = cameraHolds(manifest);
const master = masterMs(manifest);
if (!captions.length) {
  console.error(`FAIL: ${manifestPath} declares no captions -- nothing to evaluate`);
  process.exit(1);
}

/** The camera hold whose window contains `pct`, else the one overlapping it most. */
function holdFor(pct, window) {
  const inside = holds.find(h => Number(h.window[0]) <= pct && pct <= Number(h.window[1]));
  if (inside) return inside;
  let best = null, bestOverlap = 0;
  for (const h of holds) {
    const overlap = Math.min(Number(h.window[1]), window[1]) - Math.max(Number(h.window[0]), window[0]);
    if (overlap > bestOverlap) { best = h; bestOverlap = overlap; }
  }
  return best;
}

const browser = await puppeteer.launch({ headless: true });
const page = await browser.newPage();
const vb = (manifest.target || {}).viewbox || [0, 0, 1920, 1080];
await page.setViewport({ width: Math.round(vb[2]), height: Math.round(vb[3]) });
await page.goto(url, { waitUntil: "networkidle2" });
await page.evaluate(() => document.fonts.ready);
await new Promise(r => setTimeout(r, 500));
await installGeometry(page);
await installInk(page);

const errors = [], warnings = [], diags = [];
let measured = 0, noSubjects = 0, labelsEverSeen = 0, edgesEverSeen = 0, unrevealed = 0;

for (const caption of captions) {
  const sel = caption.element;
  const window = [Number(caption.window[0]), Number(caption.window[1])];
  let chosen = null, missing = false;
  for (const fraction of FRACTIONS) {
    const pct = window[0] + (window[1] - window[0]) * fraction;
    const hold = holdFor(pct, window);
    await freezeAt(page, (pct / 100) * master);
    if (hold) await pinCamera(page, hold);
    const state = await page.evaluate(readCaptionState, sel);
    if (!state.found) { missing = true; break; }
    if (state.revealed) { chosen = { pct, hold }; break; }
  }
  if (missing) {
    const why = `${sel}: the manifest names this caption; the page has no such element`;
    // Printed HERE, not only collected: if every caption is missing the run ends on the
    // empty-set rule below, and the selector that is actually wrong must still be on
    // screen for whoever has to fix it.
    console.log(`  ${why}`);
    errors.push(why);
    continue;
  }
  if (!chosen) {
    // Not a pass and not this gate's defect class: say it, count it, keep going.
    unrevealed++;
    console.log(`  ${sel.padEnd(12)} UNMEASURED -- never fully revealed at any sampled `
                + `instant inside its own window [${window[0]}, ${window[1]}]`);
    continue;
  }
  const out = await page.evaluate(measureCaption, {
    sel, tol: TOL, subjectPad: SUBJECT_PAD,
    bbox: (chosen.hold && chosen.hold.bbox) || null,
  });
  measured++;
  labelsEverSeen += out.labelsSeen;
  edgesEverSeen += out.edgesSeen;
  if (!out.subjects.length) noSubjects++;

  const holdId = (chosen.hold && chosen.hold.id) || "(none)";
  const tight = out.tightestSubject === null ? "n-a"
    : `${Math.round(out.tightestSubject * 10) / 10}px`;
  console.log(`  ${sel.padEnd(12)} t=${chosen.pct.toFixed(2)}%  hold ${holdId.padEnd(8)}`
    + `  card ${Math.round(out.card.right - out.card.left)}x`
    + `${Math.round(out.card.bottom - out.card.top)}`
    + `  brackets ${out.brackets}  subjects ${out.subjects.length}`
    + `  edges ${out.edgesSeen} (subject ${out.subjectEdgesSeen})`
    + `  edge-labels ${out.labelsSeen}  tightest-subject-clearance ${tight}`);

  const fixes = out.fix
    ? [`Move ${sel} by dx=${out.fix.dxPx}px on screen (${out.fix.dxWorld} world units): `
       + `measured at this hold, the shifted card clears every edge label and every subject `
       + `edge by >=1px and still lies inside hold ${holdId}'s must-show bbox.`]
    : [];
  for (const hit of out.labelHits) {
    errors.push(`${sel} covers edge label "${hit.text}" by ${hit.overlap}px `
                + `(measured on ${hit.measuredOn})`);
    diags.push({ code: "caption/occludes-edge-label",
                 subject: { element: sel, hold: holdId, text: hit.text },
                 evidence: { overlap_px: hit.overlap, measured_on: hit.measuredOn,
                             tol_px: TOL, card: out.card, at_pct: chosen.pct },
                 supportedFixes: fixes });
  }
  for (const hit of out.subjectHits) {
    errors.push(`${sel} covers its own beat's edge ${hit.name} by ${hit.overlap}px`);
    diags.push({ code: "caption/occludes-subject-edge",
                 subject: { element: sel, hold: holdId, edge: hit.name },
                 evidence: { overlap_px: hit.overlap, tol_px: TOL, card: out.card,
                             subjects: out.subjects, at_pct: chosen.pct },
                 supportedFixes: fixes });
  }
  for (const hit of out.otherHits) {
    warnings.push(`${sel} crosses ${hit.name} by ${hit.overlap}px -- scenery, not this `
                  + `beat's subject`);
    diags.push({ code: "caption/occludes-edge",
                 subject: { element: sel, hold: holdId, edge: hit.name },
                 evidence: { overlap_px: hit.overlap, tol_px: TOL, at_pct: chosen.pct } });
  }
}
await browser.close();

// ##DIAG: structured evidence for `verify_all.py --json` (README -> "The ##DIAG line").
// Severity is the RUNNER's, never declared here -- `caption/occludes-edge` is registered
// as a warning and the other two as errors, in diagram-director/scripts/diagnostic_codes.py.
for (const diag of diags) console.log("##DIAG " + JSON.stringify(diag));

// House rule: a check that finds nothing FAILS.
if (!measured) {
  console.error(`FAIL: measured zero captions of the ${captions.length} the manifest `
                + "declares -- wrong url, broken page, or selector drift");
  process.exit(1);
}
// The other empty set that used to read green: captions found, but nothing UNDER them.
// A diagram with no painted edge at any caption instant is a broken page or a selector
// that no longer matches, not a cut whose cards happen to sit over nothing.
if (!edgesEverSeen) {
  console.error("FAIL: measured zero painted edges at every caption instant -- the scene "
                + "under the cards is empty, which is selector drift or a broken page");
  process.exit(1);
}
if (noSubjects)
  console.log(`N/A: ${noSubjects} caption(s) had no lit spotlight bracket in their own `
              + "window, so they have no subject set -- the subject-edge rule is N-A for "
              + "them; the edge-label rule still applied");
if (!labelsEverSeen)
  console.log("N/A: no visible edge label at any caption instant -- this cut renders none, "
              + "so the edge-label rule had nothing to measure");
if (unrevealed)
  console.log(`N/A: ${unrevealed} caption(s) were never fully revealed inside their own `
              + "window at any sampled instant -- not measured, and not a pass");
for (const warning of warnings) console.log(`WARN [caption/occludes-edge] ${warning}`);

if (errors.length) {
  console.log("CAPTION-OCCLUSION VIOLATIONS:");
  errors.forEach(e => console.log(`  ${e}`));
  process.exit(1);
}
console.log(`all clear across ${measured} caption(s): no card covers an edge label or an `
            + `edge of its own beat's subjects (tol ${TOL}px); ${warnings.length} scenery `
            + "crossing(s) reported above");
process.exit(0);
