// Gap this closes: text-containment checks text against NODE shapes, and the
// safe-area sweep checks text against the frame -- neither looks at a caption
// against its own card. A restyled fork whose label font changed spills the
// card silently, and a spilled word lands on raw canvas at card-text polarity
// (dark on dark). Assert every caption text sits inside its own rect.
//
//   node verify-caption-boxes.mjs <url> [<url> ...]      (serve over HTTP)
import puppeteer from "./resolve-puppeteer.mjs";

const urls = process.argv.slice(2);
if (!urls.length) { console.error("usage: verify-caption-boxes.mjs <url> [...]"); process.exit(2); }

const b = await puppeteer.launch({ headless: true });
let bad = 0;
for (const u of urls) {
  const p = await b.newPage();
  await p.goto(u, { waitUntil: "networkidle2" });
  await p.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 500));
  const found = await p.evaluate(() => document.querySelectorAll(".beat-caption").length);
  const out = await p.evaluate(() => {
    const res = [];
    for (const g of document.querySelectorAll(".beat-caption")) {
      const r = g.querySelector("rect"), t = g.querySelector("text");
      if (!r || !t) continue;
      const rb = r.getBBox(), tb = t.getBBox();
      const over = Math.max(rb.x - tb.x, tb.x + tb.width - (rb.x + rb.width),
                            rb.y - tb.y, tb.y + tb.height - (rb.y + rb.height));
      if (over > 0.5) res.push({ cap: r.getAttribute("data-cap"),
        txt: t.textContent.trim().slice(0, 34), over: Math.round(over * 10) / 10 });
    }
    return res;
  });
  await p.close();
  const name = u.split("/").pop();
  // A check that finds nothing must FAIL -- an empty element set is the shape a
  // wrong url and a broken page both take, and both used to report green.
  if (found === 0) { bad++; console.log(`${name}: NO CAPTIONS FOUND -- wrong url or broken page`); }
  else if (out.length) { bad++; console.log(`${name}: SPILLS`, out.map(o => `${o.cap} +${o.over}px "${o.txt}"`).join(" | ")); }
  else console.log(`${name}: all ${found} captions inside their card`);
}
await b.close();
process.exit(bad ? 1 : 0);
