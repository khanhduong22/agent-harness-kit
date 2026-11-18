# 2024–2026 Schema, Transport/Stack CVE, Hreflang, SXO & Drift Playbook

Distilled from `AgriciDaniel/claude-seo` (`seo-schema`, `seo-technical`, `seo-hreflang`, `seo-sxo`, `seo-drift`, `hooks/validate-schema.py`, MIT). Zero paid APIs or plugin installer dependencies.

---

## 1. JSON-LD `@graph` Validation & 2024–2026 Deprecated Schema Types

### `@graph` Singleton & Validation Invariants (`hooks/validate-schema.py`)
1. **Container vs Entity Semantics**: A top-level `@graph` object/array is a container and **does NOT require `@type`**. Its member objects inherit `@context` (`https://schema.org` or `http://schema.org`, string/list/`@vocab`) from the enclosing graph and MUST each declare `@type` and a stable `@id` URI (`https://domain.com/#person`, `#organization`, `#webpage`) for entity triangulation.
2. **Critical Failure Gates (Fix Before Shipping)**:
   - Invalid JSON syntax or non-object/non-list root; malformed `@type` (empty string/array).
   - Unfilled template placeholders (`[Business Name]`, `[City]`, `[URL]`, `REPLACE_*`).
   - Relative URLs in `@id`, `url`, `image`, or `sameAs` (always use absolute HTTPS URLs).
   - **SSR vs JS-Injected Structured Data**: Dynamically JS-injected `Product`/`Offer` schema degrades Shopping crawl reliability; emit time-sensitive and identity `@graph` markup in **initial SSR HTML** within Googlebot's first **2 MB**.

### Google 2023–2026 Rich Result Deprecations & Active Replacements
| Type | Retirement Date | Status / Severity | Replacement & Guidance |
|---|---|---|---|
| **`HowTo`** | Sep 2023 | **Deprecated (Error)** | Rich result removed everywhere. Use clear `<h2>` step headings in `Article`. |
| **`VehicleListing` / `Vehicle`** | Jun 12, 2025 | **Retired (Error)** | No dealer inventory card. Use `Product` if sold online. |
| **`ClaimReview`** | Jun 12, 2025 | **Retired from Search** | Keep only for Fact Check Explorer publishers; use `Article` + `dateline` for news. |
| **`EstimatedSalary`** | Jun 12, 2025 | **Retired (Error)** | No replacement; `JobPosting` with `baseSalary` remains active for specific roles. |
| **`LearningVideo`** | Jun 12, 2025 | **Retired (Error)** | Replace with standard `VideoObject`. |
| **`CourseInfo`** | Jun 12, 2025 | **Retired (Error)** | Docs removed `2025-09-09`; use **Course list** (`Course` + `ItemList` carousel). |
| **`SpecialAnnouncement`** | Jul 31, 2025 | **Deprecated (Error)** | COVID emergency card retired; use `Event` (time-bounded) or `Article`/`WebPage`. |
| **`Practice Problem`** | Nov 2025 notice / Jan 2026 sunset | **Retired (Error)** | Tooling/docs removed Jan 2026 (`Quiz` / `eduQuestionType=Flashcard` remains live). |
| **`FAQPage`** | Aug 2023 (restricted); **May 7, 2026 (fully retired)** | **Info Only (Not Critical)** | Google retired FAQ rich results for **all** sites (`2026-05-07`); docs removed `2026-06-15`. Do not add for SERP gains; flag existing markup as Info only; use `QAPage` for genuine single-question Q&A threads. |

**Active / Do-Not-Flag Schemas**: `Book Actions` (phase-out reversed `2025-11-05`), `Dataset` (active for Dataset Search), `ProductGroup` (`variesBy`/`hasVariant`), `Certification` (replaced `EnergyConsumptionDetails` Apr 2025), `hasAdultConsideration` (required May 2026 for adult products), `QAPage`, `DiscussionForumPosting`, `ProfilePage`, `SoftwareSourceCode`, `BroadcastEvent`, `Clip`, `SeekToAction`.

---

## 2. Technical Transport, Security Headers & Passive Stack CVE Exposure

> **SEO Weight Discipline**: Security headers protect trust and users — they are **not** a confirmed Google ranking signal. HTTPS is a lightweight signal; CWV (`LCP <= 2.5s`, `INP <= 200ms` — **never** cite retired FID, `CLS <= 0.1`) is the direct page-experience ranking input. Search Console's standalone Page Experience report is retired.

### Transport & Security Header Grading
- **TLS & Redirect Consolidation**: Cert valid, `>= 14 days` to expiry, `TLS >= 1.2`, SAN covers host; `http://` -> `https://` in **1 hop (`301`/`308`)** on same host first; `www` and apex consolidate to one final URL.
- **HSTS (`Strict-Transport-Security`)**: Must appear once without duplicate directives (RFC 6797: duplicate directives invalidate HSTS). Preload minimum: `max-age >= 31536000; includeSubDomains; preload`.
- **CSP (`Content-Security-Policy`)**: Enforced (not `-Report-Only`); defines `script-src`/`default-src` without `'unsafe-eval'`, un-nonced `'unsafe-inline'`, or wildcards (`*`, `https:`, `data:`); sets `object-src 'none'` and `base-uri`.
- **Clickjacking, MIME & Referrer**: `X-Content-Type-Options: nosniff`; `X-Frame-Options: DENY|SAMEORIGIN` or restrictive CSP `frame-ancestors`; `Referrer-Policy` present and not `unsafe-url`; `Permissions-Policy` present; cookies set `Secure`, `HttpOnly`, and explicit `SameSite`.

### 2025–2026 Technical SEO Rules
- **Googlebot Fetch Caps**: **2 MB** uncompressed HTML, **64 MB** PDF. Bloated inline CSS/JS/base64 pushes JSON-LD or body content out of the index.
- **JS SEO (Dec 2025)**: Canonical mismatches between raw HTML and JS-rendered DOM let Google pick either; raw HTML `<meta name="robots" content="noindex">` may persist even if JS removes it; Google does **not** render JS on non-200 pages; dynamic rendering is technical debt.
- **Back-Button Hijacking**: `pushState`/`replaceState` trapping navigation (including ad scripts) is a live Google spam violation since `2026-06-15` (**Critical**).
- **Crawl Rate & AMP**: Manual GSC crawl-rate control was removed Jan 2024; AMP has zero ranking boost and since `2026-07-01` routes directly to publisher URLs.

### Passive Read-Only Stack Fingerprinting & CVE Exposure
- **Scope Boundary**: Read **only** normal HTTP response headers/HTML for the audited URL (`Server`, `X-Powered-By`, `X-AspNet-Version`, `Set-Cookie` names like `PHPSESSID`, `Link: <...wp-json/>`, `<meta name="generator">`, `_next/static`). **Never** fuzz, brute-force, or probe unauthorized paths (`/wp-login.php`, `/xmlrpc.php`) without explicit site-owner authorization.
- **PHP Critical RCE Reference (`CVE-2026-109618` / `CVE-2026-109619`, CVSS 9.2)**:
  - Fixed in **PHP `8.5.12`, `8.4.27`, `8.3.36`, `8.2.35`** (`<= 8.1` EOL).
  - *Reporting Band*: Exposed `X-Powered-By: PHP/<ver>` below fixed threshold = **High ("likely exposed, confirm with host")** because OS distros backport patches without bumping the banner; **Critical** only when owner confirms an unpatched build; static/Next.js/Vercel/Netlify hosts with zero PHP signals = **Pass**.

---

## 3. Hreflang, Content Parity & Machine-Translation QA

1. **Structural Invariants**:
   - **Self-Canonical + Self-Hreflang**: Every localized URL MUST carry a self-referencing `<link rel="canonical">` and a self-referencing `hreflang` pointing to that exact canonical URL (trailing slash and HTTPS protocol identical). Canonicalizing `/en/post` to `/post` de-indexes `/en/post`.
   - **Full-Mesh Bidirectional Return Tags + Single `x-default`**: Every alternate `A → B` requires `B → A` across all variants plus one `x-default` fallback.
   - **BCP 47 / ISO Validation**: `language[-Script][-REGION]` — lowercase ISO 639-1 language (`en`, `vi`, `ja` not `jp`/`eng`), optional TitleCase ISO 15924 script (`zh-Hans`, `zh-Hant`), optional UPPERCASE ISO 3166-1 Alpha-2 region (`en-GB` not `en-uk`; never `EU`/`UN`/`LA` or bare country code like `be`).
   - **Method Choice**: `<head>` `<link>` tags (`<50` variants), HTTP `Link` headers (PDFs/non-HTML), or XML `xhtml:link` sitemap (`>=50` variants / cross-domain; `<=50k` URLs or `50MB` per file). GSC International Targeting report was removed in 2022.
2. **Content Parity Matrix (`0–100`: Page Existence 30, SEO Elements 30, Structure 25, Freshness 15)**:
   - Compare page existence, H2/H3 count (`±1`), FAQ count (`±2`), image/chart parity, localized title/meta/schema, and expected expansion ratios vs English (`DE +25–35%`, `FR/ES +15–25%`, `JA -10–25%`, `ZH -20–30%`).
   - Freshness deltas: `<=7d` Fresh, `8–30d` Aging, `31–90d` Stale, `>90d` Outdated. Check locale numbers, dates, currencies, and local legal/brand references.
3. **Machine-Translation QA (Sept 2025 QRG §4.6.5 & May 2026 Spam Policy)**:
   - Unreviewed bulk MT is **scaled content abuse**. Flag: identical body across `hreflang` variants (**Critical**), `<html lang>` mismatch with body language (**High**), untrimmed MT `<meta name="description"> > 160 chars` (**Medium**), missing/wrong Schema `inLanguage` (**Medium**), `.goog-te-banner-frame` widget on pages needing citations. Human-reviewed or explicitly labeled fallback MT is permitted.

---

## 4. Search Experience Optimization (SXO) Gates

SXO Score (`0–100`) measures **SERP-intent & UX fit**, reported separately from Technical SEO Health (`95 SEO + 30 SXO = wrong page type`).

1. **8-Class Page-Type Taxonomy (Classification Priority)**:
   `1. Tool/Interactive` > `2. Local Page` > `3. Comparison Page` > `4. Product Page` > `5. Landing Page` > `6. Service Page` > `7. Hybrid (Service+Content)` > `8. Blog Post`.
2. **SERP Consensus & Mismatch Gate**: Inspect top 10 organic SERP results (`>60%` strong consensus, `40–60%` mixed, `<40%` fragmented). Blog post targeting Product or Tool SERPs = **CRITICAL mismatch**; Blog targeting Comparison or Product targeting Informational = **HIGH mismatch**.
3. **7-Dimension SXO Gap Score (`0–100`)**: Page Type (`15`), Content Depth (`15`), UX Signals (`15`), Schema Markup (`15`), Media Richness (`15`), Authority Signals (`15`), Freshness (`10`).
4. **SERP-Grounded User Stories & Persona Scoring**: Derive `3–5` user stories (`As a [persona], I want [goal], because [driver], blocked by [barrier]`) strictly from observable PAA, Ads, Related Searches, Snippets, and AI Overviews. Score `4–7` derived personas across **Relevance (`25`) + Clarity (`25`, <10s answer) + Trust (`25`) + Action (`25`)** (`80–100` Excellent, `60–79` Good, `40–59` Needs Work, `0–39` Critical Mismatch). Fix weakest high-volume persona first using concrete IST → SOLL wireframes.

---

## 5. SEO Drift & Regression Diffing Rules

Normalize URLs (lowercase scheme/host, strip `:80`/`:443`, strip UTM params, sort query, normalize trailing slash) and diff current snapshots against pre-deploy baselines using SHA-256 `html_hash`/`schema_hash` and the **17 deterministic rules**:

| Severity | Triggered Drift Rules |
|---|---|
| **CRITICAL** (Immediate) | **1.** JSON-LD completely removed (exclude retired FAQ/HowTo losses) · **2.** Canonical URL changed · **3.** Canonical removed · **4.** `noindex` added in meta/headers · **5.** H1 removed · **6.** First H1 `SequenceMatcher` similarity `< 0.5` · **7.** Title removed · **8.** HTTP 2xx changed to 4xx/5xx |
| **WARNING** (Within 1 wk) | **9.** Title text changed · **10.** Meta description changed · **11.** CWV p75 (`LCP`/`INP`/`CLS`) regressed `> 20%` · **12.** Lighthouse Performance dropped `>= 10` pts · **13.** OG tags removed · **14.** `schema_hash` changed |
| **INFO** (Review) | **15.** New JSON-LD added · **16.** H2 count/text changed · **17.** `html_hash` content changed |
