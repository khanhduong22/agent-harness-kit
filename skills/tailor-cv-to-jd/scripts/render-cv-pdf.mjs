#!/usr/bin/env node
/**
 * Deterministic 2-Page A4 Vector PDF Compiler, Layout Density Auditor & ATS Verifier.
 *
 * Usage:
 *   node render-cv-pdf.mjs \
 *     --input <path/to/CV.md> \
 *     --output <path/to/Out.pdf> \
 *     [--downloads <path/in/Downloads.pdf>] \
 *     [--jd-keywords "python,fastapi,rest,redis,postgresql,typescript,react"]
 */

import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { createRequire } from "node:module";

const homeDir = os.homedir();
const mdPreviewDir = process.env.MD_PREVIEW_DIR || path.join(homeDir, "md-preview");
const distDir = path.join(mdPreviewDir, "dist");

const requireFromMdPreview = createRequire(path.join(mdPreviewDir, "package.json"));
const { chromium } = requireFromMdPreview("playwright");

function parseArgs(argv) {
  const args = { input: "", output: "", downloads: "", jdKeywords: [] };
  for (let i = 2; i < argv.length; i++) {
    const token = argv[i];
    if (token === "--input" && argv[i + 1]) {
      args.input = path.resolve(argv[++i]);
    } else if (token === "--output" && argv[i + 1]) {
      args.output = path.resolve(argv[++i]);
    } else if (token === "--downloads" && argv[i + 1]) {
      args.downloads = path.resolve(argv[++i]);
    } else if (token === "--jd-keywords" && argv[i + 1]) {
      args.jdKeywords = argv[++i]
        .split(",")
        .map((k) => k.trim())
        .filter(Boolean);
    }
  }
  if (!args.input || !args.output) {
    console.error(
      "Usage: node render-cv-pdf.mjs --input <CV.md> --output <Out.pdf> [--downloads <Downloads/Out.pdf>] [--jd-keywords \"kw1,kw2\"]"
    );
    process.exit(1);
  }
  return args;
}

const MIME_TYPES = {
  ".html": "text/html",
  ".js": "application/javascript",
  ".css": "text/css",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
};

async function main() {
  const { input, output, downloads, jdKeywords } = parseArgs(process.argv);
  if (!fs.existsSync(input)) {
    throw new Error(`Input markdown file not found: ${input}`);
  }
  if (!fs.existsSync(distDir)) {
    throw new Error(`md-preview dist directory not found at ${distDir}. Run 'npm run build' in ${mdPreviewDir}.`);
  }

  const cvMarkdown = fs.readFileSync(input, "utf8");

  const server = http.createServer((req, res) => {
    const reqPath = req.url === "/" ? "index.html" : req.url.split("?")[0].replace(/^\/+/, "");
    const filePath = path.join(distDir, reqPath);
    if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      res.writeHead(404);
      res.end();
      return;
    }
    const ext = path.extname(filePath);
    res.writeHead(200, { "Content-Type": MIME_TYPES[ext] || "application/octet-stream" });
    fs.createReadStream(filePath).pipe(res);
  });

  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const port = server.address().port;
  const browser = await chromium.launch();

  try {
    const page = await browser.newPage({ viewport: { width: 1280, height: 2600 } });
    await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: "networkidle" });

    // 1. Measure exact A4 2-page layout metrics and check invariants
    const metrics = await page.evaluate((md) => {
      const html = window.marked.parse(md);
      const sanitizedHtml = window.DOMPurify.sanitize(html, {
        ADD_TAGS: ["mjx-container", "svg", "path", "g", "marker", "defs", "pattern", "clipPath"],
        ADD_ATTR: ["id", "class", "style", "viewBox", "d", "fill", "stroke", "transform", "marker-end", "marker-start"],
      });

      document.documentElement.style.height = "auto";
      document.documentElement.style.overflow = "visible";
      document.body.innerHTML = "";
      document.body.style.background = "#ffffff";
      document.body.style.margin = "0";
      document.body.style.padding = "0";
      document.body.style.height = "auto";
      document.body.style.minHeight = "0";
      document.body.style.overflow = "visible";

      const article = document.createElement("div");
      article.className = "markdown-body pdf-export";
      article.innerHTML = sanitizedHtml;
      article.style.padding = "0";
      article.style.margin = "0";
      article.style.width = "210mm";
      article.style.minWidth = "210mm";
      article.style.maxWidth = "none";
      article.style.fontSize = "14px";
      article.style.backgroundColor = "#ffffff";
      article.style.color = "#24292e";
      document.body.appendChild(article);

      const width = article.getBoundingClientRect().width;
      const pageHeightCssPx = width * (277 / 190);
      const breakEl = article.querySelector('[style*="page-break-before"], [style*="break-before"]');
      const rootRect = article.getBoundingClientRect();
      const page1UsedPx = breakEl ? Math.round(breakEl.getBoundingClientRect().top - rootRect.top) : 0;

      let page2UsedPx = 0;
      if (breakEl && breakEl.nextElementSibling) {
        const p2Top = breakEl.nextElementSibling.getBoundingClientRect().top;
        const p2Bottom = article.getBoundingClientRect().bottom;
        page2UsedPx = Math.round(p2Bottom - p2Top);
      }

      const contactP = article.querySelector("p");
      const contactHeightPx = contactP ? Math.round(contactP.getBoundingClientRect().height) : 0;
      const tableEl = article.querySelector("table");
      const hasRawBackticksInTable = tableEl ? tableEl.textContent.includes("`") : false;
      const links = Array.from(article.querySelectorAll("a[href]")).map((a) => a.getAttribute("href"));
      const fullText = article.innerText || article.textContent || "";

      return {
        width: Math.round(width),
        pageHeightCssPx: Math.round(pageHeightCssPx),
        page1UsedPx,
        page1FillPct: Math.round((page1UsedPx / pageHeightCssPx) * 100),
        page2UsedPx,
        page2FillPct: Math.round((page2UsedPx / pageHeightCssPx) * 100),
        contactHeightPx,
        hasRawBackticksInTable,
        links,
        fullText,
      };
    }, cvMarkdown);

    // 2. Generate Native Vector PDF with selectable ATS text and clickable /URI links
    fs.mkdirSync(path.dirname(output), { recursive: true });
    await page.pdf({
      path: output,
      format: "A4",
      printBackground: true,
      scale: 190 / 210,
      margin: { top: "10mm", right: "10mm", bottom: "10mm", left: "10mm" },
    });

    if (downloads) {
      fs.mkdirSync(path.dirname(downloads), { recursive: true });
      fs.copyFileSync(output, downloads);
    }

    // 3. Audit generated PDF binary for page count, /URI annotations, JD keyword coverage, and file size
    const pdfBuf = fs.readFileSync(output);
    const pdfStr = pdfBuf.toString("latin1");
    const pageMatches = pdfStr.match(/\/Type\s*\/Page\b/g) || [];
    const uriMatches = (pdfStr.match(/\/URI\s*\([^)]+\)/g) || []).map((u) =>
      u.replace(/^\/URI\s*\(/, "").replace(/\)$/, "")
    );

    const lowerText = metrics.fullText.toLowerCase();
    const matchedKeywords = [];
    const missingKeywords = [];
    for (const kw of jdKeywords) {
      if (lowerText.includes(kw.toLowerCase())) {
        matchedKeywords.push(kw);
      } else {
        missingKeywords.push(kw);
      }
    }

    const report = {
      status: "SUCCESS",
      outputPdf: output,
      downloadsPdf: downloads || null,
      fileSizeKB: Math.round(pdfBuf.length / 1024),
      pdfPagesCount: pageMatches.length,
      page1FillPct: `${metrics.page1FillPct}% (${metrics.page1UsedPx}/${metrics.pageHeightCssPx}px)`,
      page2FillPct: `${metrics.page2FillPct}% (${metrics.page2UsedPx}/${metrics.pageHeightCssPx}px)`,
      contactSingleLine: metrics.contactHeightPx <= 26,
      hasRawBackticksInTable: metrics.hasRawBackticksInTable,
      clickableUrisCount: uriMatches.length,
      clickableUris: uriMatches,
      jdKeywordAudit:
        jdKeywords.length > 0
          ? {
              total: jdKeywords.length,
              matched: matchedKeywords.length,
              coveragePct: `${Math.round((matchedKeywords.length / jdKeywords.length) * 100)}%`,
              missingKeywords,
            }
          : undefined,
    };

    const errors = [];
    if (report.pdfPagesCount !== 2) {
      errors.push(`Expected strictly 2 PDF pages, but got ${report.pdfPagesCount}.`);
    }
    if (metrics.page1FillPct < 85 || metrics.page1FillPct > 98) {
      errors.push(`Page 1 fill (${metrics.page1FillPct}%) is outside the optimal 85%–98% density band.`);
    }
    if (metrics.page2FillPct < 85 || metrics.page2FillPct > 98) {
      errors.push(`Page 2 fill (${metrics.page2FillPct}%) is outside the optimal 85%–98% density band.`);
    }
    if (!report.contactSingleLine) {
      errors.push(`Contact bar wrapped onto multiple lines (height: ${metrics.contactHeightPx}px).`);
    }
    if (report.hasRawBackticksInTable) {
      errors.push("Raw markdown backtick (`) found inside HTML <table>. Use <code>...</code> instead.");
    }
    if (report.clickableUrisCount < 5) {
      errors.push(`Expected at least 5 clickable /URI links in PDF, found ${report.clickableUrisCount}.`);
    }
    if (missingKeywords.length > 0) {
      errors.push(`Missing target JD keywords in rendered CV: ${missingKeywords.join(", ")}`);
    }

    if (errors.length > 0) {
      report.status = "FAILED_INVARIANTS";
      report.errors = errors;
      console.error(JSON.stringify(report, null, 2));
      process.exit(1);
    }

    console.log(JSON.stringify(report, null, 2));
  } finally {
    await browser.close();
    server.close();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
