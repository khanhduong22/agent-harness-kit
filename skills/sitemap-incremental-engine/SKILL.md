---
name: sitemap-incremental-engine
description: High-performance Cold/Hot incremental sitemap generation and zero-copy Nginx static serving. Eliminates SSR CPU spikes, 504 timeouts during bot crawling, pre-gzips static XML, and serves with <1ms TTFB via Nginx sendfile.
---

# High-Performance Incremental Sitemap Engine & Nginx Zero-Copy Serving

## Overview & The Bot-Crawl Bottleneck

When large content websites (blogs, e-commerce, news platforms with 10k–500k+ URLs) rely on framework-level dynamic SSR routes (e.g. Next.js `src/app/api/sitemaps/.../route.ts` or Nuxt/Remix route handlers) to generate XML sitemaps on-demand:

1. **Massive CPU & Database Thrashing**: When Googlebot, Bingbot, or Ahrefs crawl sitemaps, they request dozens of weekly/monthly archive XML files concurrently. Each request triggers database pagination (fetching thousands of rows), JSON serialization, and heavy XML string concatenation in Node.js/Bun.
2. **Gateway Timeouts (504s) & De-indexing**: The Node.js event loop blocks, database connections exhaust, and responses take 5–15 seconds or timeout, causing search engines to abandon indexing.
3. **95% Waste on Immutable Historical Data**: Articles published in past months/years are **closed and immutable**. Recomputing them dynamically on every crawl is pure waste.

This skill standardizes the **Cold/Hot Incremental Generation + Nginx Zero-Copy Static Serving** pattern to achieve **sub-second delta builds** and **< 1ms TTFB** under infinite crawler concurrency.

---

## Architectural Principles

> [!IMPORTANT]
> **Service Placement Rule (CMS/Backend-Driven, Zero-FE Overhead)**:
> Always place the sitemap generator engine, database queries, and `.sitemap-manifest.json` state inside the **CMS / Backend service** that owns the database and content lifecycles (e.g., `index-admin-cms`), **never** inside the Frontend SSR app (`index-web`):
> 1. **Event-Driven Auto-Sync**: Hook debounced incremental regeneration (`scheduleIncrementalSitemapSync`) directly into CMS publish/update/delete lifecycles (`lifecycles.ts`) right before CDN cache purge.
> 2. **Trigger & Status API**: Expose `POST /api/articles/sitemap/trigger` and `GET /api/articles/sitemap/status` on the CMS so Frontend or Ops only makes a single lightweight HTTP call if a manual trigger is needed.
> 3. **Zero Frontend Loops**: Remove multi-query `lastmod` probes and unbounded `Promise.all` pagination loops from Frontend SSR routes to prevent socket pool exhaustion and Cloudflare 524 timeouts.

```mermaid
flowchart TD
    subgraph Serving["1. Edge / Nginx Request Path"]
        Bot["Search Engine Crawler (Googlebot)"] -->|GET /sitemap-vi-2026-05-w2.xml| Nginx["Nginx Reverse Proxy"]
        Nginx -->|Check Static Disk| CacheCheck{"Exists in /www/wwwroot/sitemaps/?"}
        CacheCheck -->|YES (99.9% requests)| StaticFile["Nginx sendfile + gzip_static<br/>⚡ TTFB: 0.5ms | CPU: ~0%"]
        CacheCheck -->|NO (Uncached / Dynamic)| AppFallback["Fallback to Next.js / Backend Proxy (:3000)"]
    end

    subgraph Generation["2. Incremental Background Engine (Cron)"]
        CronTrigger["Cron (Every 15m)"] --> Script["Sitemap Engine (Native Bun.sql / SQL Stream)"]
        Script --> DB[(PostgreSQL / Database)]
        
        Script --> ColdRule["Cold Check: If past closed week exists on disk -> SKIP (0 DB queries)"]
        Script --> HotRule["Hot Delta: Query only active week + 48h Google News"]
        Script --> IndexRule["Index Update: Update root sitemap.xml & locale indexes"]
        
        HotRule --> AtomicWrite["Atomic Write (.tmp -> fs.renameSync)"]
        IndexRule --> AtomicWrite
        AtomicWrite --> GzipCompress["Pre-Gzip (Level 9 .xml.gz)"]
        GzipCompress --> DiskStorage[("/www/wwwroot/sitemaps/*.xml & *.xml.gz")]
    end
```

### 1. Cold vs Hot Partitioning (The 0-Query Rule)
- **Cold Partition (Closed Past Weeks/Months)**: Once a week or month has concluded, its article URLs and timestamps are finalized. If `sitemap-[locale]-[YYYY-MM]-w[X].xml` already exists on disk, **skip querying the database entirely**. Read `<lastmod>` from the existing file for parent index references.
- **Hot Partition (Active Period & News)**: Only regenerate:
  - The current active week (`sitemap-[locale]-[current_year]-[current_month]-w[current_week].xml`).
  - Google News sitemaps (`sitemap-news.xml` / `sitemap-news-manual.xml` for articles published in the last 48 hours).
  - Parent index sitemaps (`sitemap.xml`, `sitemap-vi.xml`, `sitemap-en.xml`) to reflect updated child `<lastmod>` timestamps.
- **Result**: Execution drops from 60s+ scanning hundreds of thousands of rows to **< 1.5s** scanning only recent rows.

### 2. Atomic Writes (Corruption Prevention)
Never write directly to the active `.xml` file path with `fs.writeFileSync`. If a crawler hits the file while it is halfway written, the crawler receives malformed XML.
- Always write to `${filePath}.tmp`.
- Atomically swap using `fs.renameSync(tmpPath, filePath)`. The Linux VFS ensures readers either see the old complete file or the new complete file.

### 3. Pre-compressed Gzip (`gzip_static on;`)
XML files containing 1,000–5,000 URLs are typically 200KB–2MB.
- Compress static files during generation using zlib level 9 into `.xml.gz`.
- Configure Nginx with `gzip_static on;`. Nginx checks for `.gz` file presence and streams it directly to clients supporting `Accept-Encoding: gzip`, bypassing on-the-fly CPU compression.

### 4. Nginx Zero-Copy with Dynamic Fallback
- Serves static XML via Linux kernel `sendfile` (zero context switching between user and kernel space).
- If any sitemap has not yet been generated (e.g. newly added route or dynamic real-time price sitemaps), Nginx seamlessly forwards to the application via `try_files $uri @app_fallback`.

---

## Nginx Configuration Template

Place this drop-in configuration into your Nginx vhost or extension directory (e.g. `/etc/nginx/conf.d/sitemaps.conf` or `/www/server/panel/vhost/nginx/extension/<domain>/sitemap.conf`):

```nginx
# ==============================================================================
# SITEMAP ZERO-COPY STATIC SERVING WITH APPLICATION FALLBACK
# ==============================================================================
location ^~ /sitemap {
    root /www/wwwroot/sitemaps;
    default_type application/xml;
    gzip_static on;
    expires 1h;
    add_header Cache-Control "public, max-age=3600, stale-while-revalidate=600";
    add_header X-Served-By "Nginx-Static-Sitemap" always;
    try_files $uri @app_sitemap_fallback;
}

location @app_sitemap_fallback {
    proxy_pass http://127.0.0.1:3000; # Upstream application port
    proxy_set_header Host $http_host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Real-Port $remote_port;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_connect_timeout 60s;
    proxy_send_timeout 600s;
    proxy_read_timeout 600s;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    add_header X-Served-By "App-Dynamic-Fallback" always;
}
```

> [!CAUTION]
> **Nginx Worker Directory Permissions**:
> Nginx worker processes typically run as user `www`, `nginx`, or `www-data`.
> Never place sitemaps under `/root/sitemaps` directly because the `/root` home folder is mode `750` (`dr-xr-x---`), which worker processes cannot traverse, causing immediate **403 Forbidden** errors.
> **Standard Practice**: Use `/www/wwwroot/sitemaps` or `/var/www/sitemaps` with `chmod 755` and `chown -R www:www`, then symlink `/root/sitemaps -> /www/wwwroot/sitemaps`.

---

## TypeScript Generator Implementation Pattern

Using native `Bun.sql` or standard PostgreSQL streaming:

```typescript
import * as fs from 'node:fs';
import * as path from 'node:path';
import * as zlib from 'node:zlib';
import { SQL } from 'bun';

// 1. Timezone & Week Partitioning Helpers
const VN_OFFSET_MS = 7 * 60 * 60 * 1000; // GMT+7

function formatVnDate(dateInput: string | Date): string {
  const d = typeof dateInput === 'string' ? new Date(dateInput) : dateInput;
  if (Number.isNaN(d.getTime())) return '';
  const shifted = new Date(d.getTime() + VN_OFFSET_MS);
  const year = shifted.getUTCFullYear();
  const month = String(shifted.getUTCMonth() + 1).padStart(2, '0');
  const day = String(shifted.getUTCDate()).padStart(2, '0');
  const hours = String(shifted.getUTCHours()).padStart(2, '0');
  const mins = String(shifted.getUTCMinutes()).padStart(2, '0');
  const secs = String(shifted.getUTCSeconds()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${mins}:${secs}+07:00`;
}

function getWeekDateRange(yearMonth: string, week: number) {
  const [yearStr, monthStr] = yearMonth.split('-');
  const yearNum = parseInt(yearStr || '0', 10);
  const monthNum = parseInt(monthStr || '1', 10);
  const startDay = (week - 1) * 7 + 1;
  let endDay = week * 7;
  if (week === 4) endDay = new Date(Date.UTC(yearNum, monthNum, 0)).getUTCDate();
  return {
    start: new Date(Date.UTC(yearNum, monthNum - 1, startDay)),
    end: new Date(Date.UTC(yearNum, monthNum - 1, endDay, 23, 59, 59, 999)),
  };
}

// 2. Atomic Writer with Gzip Level 9
function writeAtomic(outDir: string, filename: string, content: string) {
  const targetPath = path.join(outDir, filename);
  const tmpPath = `${targetPath}.tmp`;
  fs.writeFileSync(tmpPath, content, 'utf-8');
  fs.renameSync(tmpPath, targetPath);

  // Pre-gzip
  const gzTmp = `${targetPath}.gz.tmp`;
  const gzipped = zlib.gzipSync(Buffer.from(content, 'utf-8'), { level: 9 });
  fs.writeFileSync(gzTmp, gzipped);
  fs.renameSync(gzTmp, `${targetPath}.gz`);
}
```

---

## Production Deployment Checklist & Automation

1. **Directory Preparation**:
   ```bash
   mkdir -p /www/wwwroot/sitemaps
   chown -R www:www /www/wwwroot/sitemaps
   chmod -R 755 /www/wwwroot/sitemaps
   ln -sfn /www/wwwroot/sitemaps /root/sitemaps
   ```

2. **Full Initial Backfill**:
   Run full generation once to populate historical archives:
   ```bash
   bun run scripts/generate-sitemaps.ts --full
   ```

3. **Crontab Scheduling (Every 15 Minutes)**:
   Add to system crontab (`crontab -e`):
   ```cron
   */15 * * * * cd /path/to/project && /usr/local/bin/bun run sitemap:incremental >> /var/log/sitemap-cron.log 2>&1
   ```

4. **Nginx Live Benchmark Verification**:
   ```bash
   # Verify static response header
   curl -skI -H "Host: yourdomain.com" https://127.0.0.1/sitemap.xml | grep -E 'x-served-by|content-encoding'
   # Expected:
   # x-served-by: Nginx-Static-Sitemap
   # content-encoding: gzip
   ```
