# BunnyCDN Migration Cutover & Tier-1 Docker BuildKit Acceleration

Companion reference for `infra-performance-optimization/SKILL.md` (§7 and §8).

---

## 7. BunnyCDN Pull Zone Architecture & Server Migration Cutover Standard (Zero `0-Byte` Cache Poisoning)

When fronting latency-sensitive Vietnam/Asia web applications with **Bunny.net CDN (`*.b-cdn.net`, DNS-Only `proxied: false` on Cloudflare)** while connecting directly to a VPS Origin IP (`OriginUrl: "https://<VPS_IP>"` + `OriginHostHeader: "<domain>"`):

### 7.1. The Delayed 35-Hour LRU Eviction & `0-Byte` Immutable Chunk Poisoning Trap
- **Failure Mode**: Updating Cloudflare DNS `A` records alone does **not** update a Bunny Pull Zone whose `OriginUrl` is set to the raw VPS IP (`https://<OLD_VPS_IP>`).
- **Why It Hides for 24–36 Hours**:
  1. Immediately after stopping the container on the old VPS, Bunny's regional edge PoP (`BunnyCDN-VN1`) and client PWA Service Workers continue serving cached HTML and `/_next/static/chunks/*.js` bundles.
  2. Hours later (24–36 hours), Bunny's edge LRU cache evicts a subset of `/_next/static/chunks/*.js` files and pulls them from `OriginUrl` (`https://<OLD_VPS_IP>`).
  3. If the old VPS reverse proxy returns `HTTP 200` with `Content-Length: 0` (`0 bytes`), Bunny caches those **`0-byte` JS files for 1 year (`max-age=31536000, immutable`)**, silently breaking React hydration across all users.

### 7.2. Mandatory 5-Step Server / VPS Migration Cutover Checklist
1. **Update Cloudflare DNS (`A` / `CNAME`)**: Update `A` records for API/Admin/Origin hostnames while keeping user-facing `CNAME *.b-cdn.net` (`proxied: false`) intact.
2. **Update Bunny Pull Zone `OriginUrl` & `OriginShield` via REST API**:
   ```bash
   curl -sS -X POST "https://api.bunny.net/pullzone/${PULLZONE_ID}" \
     -H "AccessKey: ${BUNNY_API_KEY}" \
     -H "Content-Type: application/json" \
     -d "{\"OriginUrl\": \"https://${NEW_VPS_IP}\", \"OriginHostHeader\": \"${ORIGIN_HOST}\", \"EnableOriginShield\": false}"
   ```
3. **Purge Bunny Pull Zone Cache Immediately**:
   ```bash
   curl -sS -i -X POST "https://api.bunny.net/pullzone/${PULLZONE_ID}/purgeCache" \
     -H "AccessKey: ${BUNNY_API_KEY}"
   # Must return HTTP/2 204
   ```
4. **Verify All Referenced Static Chunks via Real `GET` Requests (Never `HEAD` Alone)**:
   ```bash
   python3 -c '
   import urllib.request, re
   domain = "https://your-domain.com"
   html = urllib.request.urlopen(domain + "/").read().decode("utf-8", errors="ignore")
   urls = set(re.findall(r"/_next/static/[^\x22\x27\s>]+", html))
   zeros = [u for u in sorted(urls) if len(urllib.request.urlopen(domain + u).read()) == 0]
   print(f"HTML={len(html)}B, Assets={len(urls)}, Zero-byte={len(zeros)}", zeros)
   assert len(zeros) == 0, f"Poisoned 0-byte assets detected: {zeros}"
   '
   ```
5. **Migrate Host Crontabs & CI/CD Targets**: Audit `crontab -l` on the old VPS and GitHub Actions secrets (`SSH_HOST`).

---

## 8. Tier-1 Docker BuildKit & Self-Hosted CI/CD Acceleration (Sub-2-Minute Builds)

### 8.1. Eliminating the 120s+ BuildKit Post-Build `contenthash` Scan Bottleneck (And Avoiding the `overlay2` Lowerdir Whiteout Trap)
- **CRITICAL TRAP — Never `rm -rf node_modules` on a Lowerdir (`FROM deps AS builder`)**:
  Deleting `/app/node_modules` inherited from `FROM deps AS builder` forces Linux `overlay2` to create 120,000+ character-device whiteout files in `upperdir` (+50–80s synchronous disk I/O). Delete **only** same-layer build outputs (`.next/standalone/node_modules`).
- **Three-Part Fix**:
```dockerfile
# --- Stage 2: Builder ---
FROM deps AS builder
WORKDIR /app
COPY . .

# Merge static and delete ONLY same-layer standalone node_modules (zero overlay2 whiteouts)
RUN bun run build && \
    cp -r .next/static .next/standalone/.next/static && \
    rm -rf .next/standalone/node_modules .next/server .next/types .next/diagnostics

# --- Stage 3: Runner ---
FROM base AS runner
WORKDIR /app

# 1. Dependency layer reused from deps FIRST (cached 0.0s on application code changes)
COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules

# 2. Configs and static assets from context (cached 0.0s independent of builder)
COPY package.json entrypoint.sh otel.js ./
COPY --chown=nextjs:nodejs public ./public
COPY --chown=nextjs:nodejs messages ./messages

# 3. Single narrow COPY from builder (scans only ~35MB standalone dir in ~2s)
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
```

### 8.2. Per-Environment BuildKit Cache Namespace (`id=next-cache-${CACHE_ENV}`)
Isolate BuildKit cache mounts per environment (`ARG CACHE_ENV=dev`, `--mount=type=cache,id=next-cache-${CACHE_ENV},target=/app/.next/cache`) to eliminate cache ping-pong between Dev, Staging, and Prod on shared self-hosted runners.

### 8.3. Zero-Copy `FROM deps AS builder` & Direct Runner Layering
Place `COPY --from=deps /app/node_modules ./node_modules` in `runner` before copying application code so the 1.5 GB dependency layer resolves as `CACHED [0.0s]` whenever lockfiles are untouched.

### 8.4. Pre-Source Prisma Client Generation Layer
Copy `prisma/` and run `bun prisma generate` **before** `COPY src ./src` so Prisma generation is cached (`0.0s`) when `schema.prisma` is unchanged.

### 8.5. Blue-Green Deployment Zombie Container & Concurrency Guard
1. Enforce `concurrency: { group: deploy-${{ github.ref }}, cancel-in-progress: false }`.
2. If both `blue` and `green` containers are running at startup, inspect `.State.StartedAt`, keep the newer container, and stop/remove the stale one.
3. On candidate healthcheck failure, explicitly `docker compose stop "$INACTIVE_SERVICE" && docker compose rm -f "$INACTIVE_SERVICE"` before `exit 1`.

### 8.6. Alpine Container Healthcheck IPv4 & Next.js 16 RSC OpenTelemetry Guard
1. **Alpine IPv4 Healthcheck**: Always use `http://127.0.0.1:3000/api/health` instead of `localhost` in Alpine `HEALTHCHECK` so BusyBox `wget` never fails on IPv6 `[::1]`.
2. **Next.js 16 RSC OpenTelemetry `Math.random` Guard**: Capture `const nativeMathRandom = Math.random.bind(Math)` in `otel.js` before Next.js static prerendering monkey-patches `Math.random()`, and inject a custom `SafeDeterministicIdGenerator` into `NodeSDK`.

### 8.7. Hash-Gated Database Migrations & Zero-Downtime Deploy Guard (`deploy.sh --check`)
Run `if bun run setup --check >/dev/null 2>&1; then ... else bun run setup; fi` to skip processor stop-windows when SQL migration SHA-256 hashes match `COMMENT ON SCHEMA public`. See `backend-performance-optimization` (`references/database-migrations-and-concurrency-patterns.md` §8.13).
