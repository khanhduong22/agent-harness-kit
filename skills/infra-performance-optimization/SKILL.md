---
name: infra-performance-optimization
description: Infrastructure, Edge CDN (Cloudflare), Reverse Proxy (Caddy/Nginx), Docker container runtime, and Linux VPS kernel (TCP BBR, sysctl, PostgreSQL shm_size) performance optimization. Use when diagnosing high network TTFB, cf-cache-status DYNAMIC misses, transcontinental latency, proxy bottlenecks, or container rollouts.
---

# Infrastructure, Edge CDN & Linux Kernel Performance Optimization

A production-grade playbook for eliminating network, edge CDN, reverse proxy, container runtime, and Linux kernel bottlenecks. Together with `frontend-performance-lighthouse` (Browser/CWV) and `backend-performance-optimization` (App/DB/Cache), this skill completes the **Full-Stack Performance Triad** used by `/op-goal`.

```mermaid
flowchart LR
    User["Client Browser<br/>(Vietnam / Global)"] -->|"<25ms Edge HIT<br/>HTTP/3 + 0-RTT"| CF["1. Cloudflare Edge CDN<br/>(Cache Rules + RSC Bypass)"]
    CF -->|"TCP BBR + Keepalive<br/>(When Cache Miss)"| Proxy["2. Reverse Proxy<br/>(Caddy / Nginx Zstd)"]
    Proxy -->|"Unix / Loopback Pool"| App["3. App Container<br/>(Next.js / Bun / Node)"]
    App -->|"Internal Infra Net"| DB["4. PostgreSQL / Valkey<br/>(shm_size + NVMe Tuning)"]
```

---

## 1. Automated Infra & Edge Diagnostic Runbook (Measure First)

Before tuning server code, always isolate **Network RTT (`Connect` + `TLS`)** from **Server Compute (`TTFB - TLS`)** and inspect Edge CDN headers:

### 1.1. Dissect Network RTT vs. Server Compute Time
```bash
# Run 2 sequential requests on a single HTTP/2 connection:
# Request 1 measures cold TCP + TLS + TTFB; Request 2 (Connect=0, TLS=0) isolates pure 1-RTT + Server Compute
curl -s -w "URL=%{url_effective} Connect=%{time_connect}s TLS=%{time_appconnect}s TTFB=%{time_starttransfer}s Total=%{time_total}s\n" \
  -o /dev/null "https://your-domain.com/" \
  -o /dev/null "https://your-domain.com/"
```
- **Interpretation**:
  - If `Request 2 TTFB` $\approx$ `Request 1 Connect` (1 network RTT, e.g. `220ms–400ms` between Vietnam and Europe/US), **server compute is already `<10ms`** — the remaining latency is pure geographic distance (`cf-cache-status: DYNAMIC`).
  - If `Request 2 TTFB` $\gg$ `Request 1 Connect`, the bottleneck is inside the origin server or database (use `backend-performance-optimization`).

### 1.2. Inspect Cloudflare Edge Cache & PoP Routing (`cf-ray`, `cf-cache-status`)
```bash
curl -sI https://your-domain.com/ | grep -iE "^(http/|cache-control|cdn-cache-control|cf-cache-status|cf-ray|vary|alt-svc)"
```
- Check the 3-letter IATA airport code at the end of `cf-ray` (e.g. `-SIN` Singapore, `-HKG` Hong Kong, `-HAN` Hanoi, `-SGN` Ho Chi Minh City vs. `-DFW` Dallas when a local VPN is active).
- If `cf-cache-status: DYNAMIC` appears despite `s-maxage=30`, Cloudflare is bypassing edge cache because HTML caching is disabled by default unless an explicit Cache Rule is active.

---

## 2. Cloudflare Edge Caching for SSR / Next.js App Router (`<25ms` Global TTFB)

### 2.1. Why `s-maxage` Alone Returns `cf-cache-status: DYNAMIC` on HTML
By default, Cloudflare only caches static file extensions (`.js`, `.css`, `.png`, `.woff2`, `.webp`) and marks all HTML routes (`content-type: text/html`) as `cf-cache-status: DYNAMIC`, forwarding every request across the ocean to the origin VPS.

### 2.2. The Next.js App Router RSC Cache Poisoning Trap (`Vary: RSC`)
In Next.js App Router, client-side `<Link>` transitions send `GET /?tab=gold` with header `RSC: 1` (expecting a `text/x-component` Flight payload), whereas a browser reload sends `GET /?tab=gold` without `RSC: 1` (expecting `text/html`).
- **Danger**: If you blindly enable "Cache Everything" on Cloudflare without accounting for the `RSC` request header, Cloudflare caches the HTML response and serves it to an RSC client navigation (or vice versa), breaking client routing!

### 2.3. Safe SSR HTML Edge Caching Standard (`CDN-Cache-Control` + Cache Rule)
1. **Origin Headers (`next.config.mjs`) — Scope Edge Caching to Pure HTML Document Requests**:
   Use Next.js header matching (`missing: [{ type: 'header', key: 'rsc' }, { type: 'header', key: 'next-router-prefetch' }]`) and emit explicit `CDN-Cache-Control` / `Cloudflare-CDN-Cache-Control` headers so Cloudflare knows exact edge TTLs while browsers always revalidate (`max-age=0`, preserving `bf-cache = 1.0`):
   ```javascript
   // next.config.mjs
   async headers() {
     return [
       {
         source: '/',
         missing: [
           { type: 'query', key: 'tab' },
           { type: 'header', key: 'rsc' },
           { type: 'header', key: 'next-router-prefetch' },
         ],
         headers: [
           {
             key: 'Cache-Control',
             value: 'public, max-age=0, s-maxage=30, stale-while-revalidate=3600',
           },
           {
             key: 'CDN-Cache-Control',
             value: 'public, max-age=30, stale-while-revalidate=3600',
           },
         ],
       },
       {
         source: '/',
         has: [{ type: 'header', key: 'rsc' }],
         headers: [
           {
             key: 'Cache-Control',
             value: 'private, no-cache, max-age=0, must-revalidate',
           },
         ],
       },
     ];
   }
   ```
2. **Cloudflare Cache Rule (Dashboard or API)**:
   Create a single Cache Rule for public SSR HTML pages:
   - **Expression**:
     ```text
     (http.host eq "your-domain.com" and http.request.method eq "GET" and not http.request.uri.path starts_with "/api/" and not http.request.uri.path starts_with "/_next/" and not any(http.request.headers["rsc"][*] ne "") and not any(http.request.headers["authorization"][*] ne ""))
     ```
   - **Action**: `Eligible for cache` $\rightarrow$ **Edge TTL**: `Use cache-control header if present, bypass cache if not`.
3. **Cloudflare Speed & Protocol Checklist**:
   - **HTTP/3 (with QUIC)**: `ON` (eliminates head-of-line blocking on lossy mobile 4G networks).
   - **0-RTT Connection Resumption**: `ON` (eliminates 1 full TLS round-trip for returning visitors).
   - **Early Hints (`103`)**: `ON` (allows Cloudflare to push `<link rel="preload">` CSS/JS headers while fetching HTML from origin).
   - **Brotli / Zstandard Compression**: `ON`.

---

## 3. Linux VPS Kernel & Network Stack Tuning (`sysctl`)

When an origin VPS in Europe or North America serves users in Asia (or communicates with external APIs), default Linux kernel TCP settings (`cubic` congestion control and small socket buffers) severely throttle throughput upon minor packet loss.

### 3.1. Production `/etc/sysctl.d/99-infra-performance.conf`
Apply these non-destructive kernel optimizations on every Linux production VPS (`sudo sysctl --system`):

```ini
# 1. Google TCP BBR Congestion Control (30-60% lower transcontinental latency)
net.core.default_qdisc = fq
net.ipv4.tcp_congestion_control = bbr

# 2. TCP Fast Open (TFO) & Time-Wait Socket Reuse
net.ipv4.tcp_fastopen = 3
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_keepalive_time = 300
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 5

# 3. High-Concurrency Ephemeral Ports & SYN Backlog
net.core.somaxconn = 8192
net.ipv4.tcp_max_syn_backlog = 8192
net.ipv4.ip_local_port_range = 10240 65535

# 4. UDP Socket Buffers for HTTP/3 (QUIC) on Caddy / Nginx
net.core.rmem_max = 7500000
net.core.wmem_max = 7500000

# 5. Memory & Valkey/Redis Background Save Resilience
vm.swappiness = 10
vm.overcommit_memory = 1
```

### 3.2. Verification Command (Read-Only SSH Check)
```bash
ssh user@vps "sysctl net.ipv4.tcp_congestion_control net.core.default_qdisc vm.swappiness vm.overcommit_memory"
```

---

## 4. Reverse Proxy Optimization (Caddy & Nginx)

### 4.1. Caddy High-Performance Reverse Proxy Standard (`Caddyfile`)
By default, Caddy enables HTTP/3 and automatic HTTPS, but explicit `encode zstd gzip` and upstream keepalive pooling reduce CPU overhead and eliminate internal loopback TCP handshakes:

```caddyfile
your-domain.com {
    encode zstd gzip

    # Immutable static assets caching
    @static path /_next/static/* /favicon.ico /icon.png /apple-icon.png /pwa-*.png
    header @static Cache-Control "public, max-age=31536000, immutable"

    reverse_proxy 127.0.0.1:3002 {
        transport http {
            keepalive 120s
            keepalive_idle_conns 64
             keepalive_idle_conns_per_host 64
        }
    }
}
```

### 4.2. Nginx Upstream Keepalive & `add_header` Inheritance Standard
1. **Upstream Keepalive Pool**: Without `keepalive 64;` and `proxy_http_version 1.1; proxy_set_header Connection "";`, Nginx opens and closes a new ephemeral TCP socket to Node.js/Bun on **every single request**.
2. **Location-Block Security Header Inheritance**: In Nginx, defining any `add_header` (such as `add_header Cache-Control ...`) inside a child `location` block **silently drops all security headers** (`X-Frame-Options`, `X-Content-Type-Options`) defined in the parent `server` block. Always re-declare security headers inside every `location` block that sets `Cache-Control`:
   ```nginx
   location ~* \.(?:css|js|woff2|webp|svg)$ {
       expires 1y;
       add_header Cache-Control "public, max-age=31536000, immutable" always;
       add_header X-Frame-Options "SAMEORIGIN" always;
       add_header X-Content-Type-Options "nosniff" always;
       add_header Referrer-Policy "strict-origin-when-cross-origin" always;
   }
   ```

---

## 5. Docker Runtime, PostgreSQL Shared Memory & Disk Hygiene

### 5.1. PostgreSQL Container `shm_size` & NVMe Planner Tuning
Docker defaults container `/dev/shm` to **64 MB**. When PostgreSQL executes parallel analytical queries, CTE window functions, or multi-asset ROI joins, exceeding 64 MB of shared memory crashes the query with `ERROR: could not resize shared memory segment: No space left on device`.
- **Implementation Standard (`docker-compose.yml`)**:
  ```yaml
  services:
    postgres:
      image: postgres:16-alpine
      shm_size: 512mb
      command:
        - "postgres"
        - "-c"
        - "shared_buffers=512MB"
        - "-c"
        - "effective_cache_size=2GB"
        - "-c"
        - "work_mem=16MB"
        - "-c"
        - "random_page_cost=1.1" # Crucial on SSD/NVMe so PG favors Index Scans over Seq Scans!
      logging:
        driver: "json-file"
        options:
          max-size: "10m"
          max-file: "3"
  ```
  - Setting `random_page_cost=1.1` (down from PostgreSQL's legacy spinning-disk default of `4.0`) instructs the query planner that random SSD I/O is nearly as fast as sequential I/O, making PostgreSQL strongly favor composite B-Tree Index Scans.

### 5.2. Docker Log Rotation & Build Cache Hygiene
Unbounded `json-file` container logs and dangling Docker build caches are the #1 cause of `ENOSPC: no space left on device` production outages on 40–80 GB VPS disks.
- Always declare `logging.options.max-size: "10m"` and `max-file: "3"` on all services.
- In CI/CD deployment scripts (`deploy.sh`), prune dangling images after successful promotion:
  ```bash
  docker image prune -f --filter "until=24h" >/dev/null 2>&1 || true
  ```

---

## 6. Zero-Downtime Blue-Green Rollout & Dual-Network Isolation

In containerized production architectures where reverse proxies (Caddy/Nginx) live on a DMZ network (`ops_bridge`) and databases/caches (PostgreSQL/Valkey) reside on an isolated internal network (`<project>-infra`):
- **Problem**: Launching the candidate container (`<service>_next`) solely on `--network ops_bridge` leaves it unable to reach PostgreSQL or Valkey. If the deployment script's health check only tests `grep -q '"status":'`, a degraded response (`{"status":"degraded","db":"disconnected"}`) falsely passes and promotes a broken container into production.
- **Implementation Standard**:
  1. Connect the candidate container to the internal backing network **before** running migrations or health probes:
     ```bash
     docker run -d --name "${CANDIDATE_CONTAINER}" --network "${EDGE_NETWORK}" ...
     if docker network inspect "${INFRA_NETWORK}" >/dev/null 2>&1; then
       docker network connect "${INFRA_NETWORK}" "${CANDIDATE_CONTAINER}" 2>/dev/null || true
     fi
     ```
  2. Assert strictly on `"status":"ok"` before swapping traffic and tearing down the old container:
     ```bash
     if docker exec "${CANDIDATE_CONTAINER}" wget -q -O - http://127.0.0.1:3000/api/health 2>/dev/null | grep -q '"status":"ok"'; then
       CANDIDATE_HEALTHY=true
     fi
     ```
