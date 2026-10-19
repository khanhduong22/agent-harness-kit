// Pre-delivery item 17, mechanised: the file opens with ZERO console errors.
// A broken CDN script, a malformed offset-path or a missing <defs> reference all
// fail silently in the DOM -- the page still renders, just without the thing the
// reference pointed at, and every geometry sweep stays green because the element
// it would have measured is simply not there.
//
// Captures three channels a human opening devtools would see:
//   console.error / console.warn   -- warnings are REPORTED, only errors fail
//   pageerror                      -- uncaught exceptions
//   requestfailed                  -- a subresource that never arrived
//
//   node verify-console-clean.mjs <url>                 (serve over HTTP)
import puppeteer from "./resolve-puppeteer.mjs";

const url = process.argv[2];
if (!url) { console.error("usage: verify-console-clean.mjs <url>"); process.exit(2); }

// /favicon.ico is requested by the BROWSER, not by the page: no diagram links one and
// no server that serves one file has one, so counting its 404 would make every honest
// cut fail. Everything else that fails to load is a hole the page is rendering.
const isBrowserNoise = (u) => /\/favicon\.(ico|png)(\?|$)/i.test(u || "");

const errors = [], warnings = [];
const browser = await puppeteer.launch({ headless: true });
const page = await browser.newPage();
page.on("console", (m) => {
  if (isBrowserNoise(m.location()?.url)) return;
  const line = `console.${m.type()}: ${m.text()}`.slice(0, 200);
  if (m.type() === "error") errors.push(line);
  else if (m.type() === "warning") warnings.push(line);
});
page.on("pageerror", (e) => errors.push(`pageerror: ${String(e.message).slice(0, 200)}`));
page.on("requestfailed", (r) => {
  if (isBrowserNoise(r.url())) return;
  errors.push(`requestfailed: ${r.url().slice(0, 120)} (${r.failure()?.errorText})`);
});
page.on("response", (r) => {
  if (r.status() >= 400 && !isBrowserNoise(r.url()))
    errors.push(`HTTP ${r.status()}: ${r.url().slice(0, 120)}`);
});

await page.goto(url, { waitUntil: "networkidle2" });
await page.evaluate(() => document.fonts.ready);
await new Promise(r => setTimeout(r, 600));
// Nothing to assert a non-empty set against here -- the "check that finds nothing"
// house rule is instead enforced by asserting the page HAS a document element and
// some SVG, so a 404 page cannot report a clean console.
const shape = await page.evaluate(() => ({
  svg: document.querySelectorAll("svg").length,
  title: document.title || "",
}));
await browser.close();

if (!shape.svg) {
  console.error(`FAIL: no <svg> on the page -- wrong url or broken page (title ${JSON.stringify(shape.title)})`);
  process.exit(1);
}
warnings.forEach(w => console.log(`  warn  ${w}`));
if (errors.length) {
  console.log("CONSOLE ERRORS:");
  errors.forEach(e => console.log(`  ${e}`));
  process.exit(1);
}
console.log(`console clean (${shape.svg} svg, ${warnings.length} warning(s), 0 errors)`);
process.exit(0);
