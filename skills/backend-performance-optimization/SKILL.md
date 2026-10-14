---
name: backend-performance-optimization
description: Backend and database performance optimization. Focuses on PostgreSQL EXPLAIN ANALYZE, query indexing, N+1 query elimination, Redis multi-tier caching, in-flight deduplication, Thundering Herd prevention, Node.js/Bun event loop non-blocking, and API TTFB latency reduction.
---

# Backend & Database Performance Optimization

## Overview

Measure before optimizing. Performance work without empirical profiling is guessing — and guessing leads to premature optimization that adds architectural complexity without moving latency metrics.

This skill governs 100% backend, database, server runtime, and API performance. It equips AI agents and backend engineers with rigorous patterns to minimize Time to First Byte (TTFB), eliminate database bottlenecks, protect Node.js/Bun event loops, and design resilient caching architectures.

---

## When to Use

- API response time (TTFB / p95 / p99) violates SLA budgets (>200ms).
- PostgreSQL queries suffer from sequential scans, buffer misses, or lock contention.
- N+1 query cascades detected in ORM data access (Prisma, TypeORM, Drizzle, Kysely).
- High throughput causes cache stampedes / thundering herds against backing stores.
- Heavy CPU operations or synchronous I/O freeze the Node.js / Bun single-threaded event loop.
- Database connection pool exhaustion or transaction timeouts occur under load.

**When NOT to use:**
- Frontend DOM, Core Web Vitals, CSS, or browser asset bundling — use [`frontend-performance-lighthouse`](../frontend-performance-lighthouse/SKILL.md).

---

## Latency & Performance SLA Targets

| Target Metric | Production Standard | Critical / Poor | Primary Root Cause & Fix |
|:---|:---|:---|:---|
| **API Response Time (p95)** | **≤ 150ms** | > 500ms | Slow queries, missing indexes, un-cached read paths |
| **API Response Time (p99)** | **≤ 300ms** | > 1000ms | GC pauses, event loop blocking, lock contention |
| **Database Query (p95)** | **≤ 15ms** | > 100ms | Sequential scans, N+1 cascades, missing compound index |
| **Buffer Cache Hit Ratio** | **≥ 99%** | < 95% | Insufficient shared buffers, missing indexes, cold cache |
| **TTFB (Server Processing)** | **≤ 50ms** | > 200ms | Heavy middleware, synchronous template/JSON serialization |
| **Event Loop Lag (p99)** | **≤ 10ms** | > 50ms | Sync crypto, heavy regex, giant JSON parse on main thread |

---

## 1. PostgreSQL Optimization & EXPLAIN ANALYZE

Every database query optimization MUST be proven with `EXPLAIN (ANALYZE, BUFFERS, TIMING, FORMAT TEXT)`. Do not claim an index improved performance without showing buffer and timing deltas.

### Reading Execution Plans
```sql
EXPLAIN (ANALYZE, BUFFERS, TIMING)
SELECT u.id, u.email, o.total_amount
FROM users u
JOIN orders o ON o.user_id = u.id
WHERE o.status = 'COMPLETED' AND o.created_at >= '2026-01-01'
ORDER BY o.created_at DESC
LIMIT 50;
```

**Key Signals to Scrutinize:**
1. **`Seq Scan` vs `Index Scan` / `Bitmap Index Scan`**: A sequential scan over a table with >1,000 rows indicates a missing index.
2. **`Buffers: shared hit=... read=...`**:
   - `hit`: Page found in PostgreSQL shared buffers (RAM, ~100ns).
   - `read`: Page fetched from OS page cache or disk (~1-10ms).
   - High `read` count proves the query is I/O-bound.
3. **`Rows Removed by Filter`**: High count indicates the index did not filter rows early enough; compound indexing is required.
4. **Sort Method**: `external merge Disk` means `work_mem` was exceeded; sort spilled to disk.

### Compound Index Ordering Rule (Equality First, Range Second)
When designing composite B-Tree indexes:
1. Columns tested with equality (`=`) come **FIRST**.
2. Columns tested with range operators (`<`, `>`, `<=`, `>=`, `BETWEEN`, `IN`) come **SECOND**.
3. Columns used in `ORDER BY` come **LAST** (matching the sort direction).

```sql
-- Query filters by tenant_id (=), status (=), and created_at (range/sort)
-- ❌ Inefficient: Range first prevents B-Tree traversal on tenant_id
CREATE INDEX idx_bad ON orders (created_at, tenant_id, status);

-- ✅ Optimal: Equality first, range and sort last
CREATE INDEX idx_orders_tenant_status_created 
ON orders (tenant_id, status, created_at DESC);
```

### Covering Indexes (Index-Only Scans)
Use the `INCLUDE` clause to pack projection columns into the index leaf pages, avoiding random heap access entirely:

```sql
-- Allows PostgreSQL to satisfy the query strictly from index leaf pages
CREATE INDEX idx_orders_lookup
ON orders (user_id, status)
INCLUDE (total_amount, created_at);
```

---

## 2. N+1 Query Elimination

N+1 query cascades occur when an application executes 1 initial query to fetch parent records, followed by N separate queries to fetch related child records.

```
Parent Query (1):  SELECT * FROM tasks WHERE team_id = 10; (Returns 200 tasks)
Child Queries (N): SELECT * FROM users WHERE id = ?;       (Executed 200 times)
Total: 201 database round-trips. Latency: 201 * 2ms = 402ms.
```

### Solutions by Data Access Layer

#### Prisma ORM
```typescript
// ❌ BAD: N+1 queries in loops
const tasks = await prisma.task.findMany({ where: { teamId } });
for (const task of tasks) {
  task.owner = await prisma.user.findUnique({ where: { id: task.ownerId } });
}

// ✅ GOOD: Single joined query with include
const tasksWithOwners = await prisma.task.findMany({
  where: { teamId },
  include: { owner: true },
});

// ✅ GOOD: Relation batching with where in
const tasks = await prisma.task.findMany({ where: { teamId } });
const ownerIds = [...new Set(tasks.map(t => t.ownerId))];
const owners = await prisma.user.findMany({ where: { id: { in: ownerIds } } });
const ownerMap = new Map(owners.map(o => [o.id, o]));
```

#### Drizzle / Raw SQL
```typescript
// ✅ GOOD: Relational Join in single query
const results = await db
  .select()
  .from(tasks)
  .innerJoin(users, eq(tasks.ownerId, users.id))
  .where(eq(tasks.teamId, teamId));
```

#### GraphQL / Microservices (DataLoader Pattern)
In GraphQL or distributed architectures where joins are impossible, use `dataloader` to coalesce individual IDs into a single batched array query within the same event loop tick:

```typescript
import DataLoader from 'dataloader';

const userLoader = new DataLoader<string, User>(async (userIds) => {
  const users = await db.users.findMany({
    where: { id: { in: [...userIds] } },
  });
  const userMap = new Map(users.map((u) => [u.id, u]));
  return userIds.map((id) => userMap.get(id) ?? null);
});

// Resolvers call userLoader.load(task.ownerId) - automatically batched into 1 query
```

---

## 3. High-Performance Caching & Thundering Herd Prevention

### Multi-Tier Caching Architecture (L1 Memory + L2 Redis)
- **L1 In-Memory Cache** (LRU / TTL, e.g., in-process heap): ~50ns access, micro-caching hot objects.
- **L2 Distributed Cache** (Redis Cluster): ~1ms access, shared across all backend replica pods.

```mermaid
flowchart TD
    Req["Incoming API Request"] --> L1{"L1 Heap Cache?"}
    L1 -- Hit (~50ns) --> Ret["Return Data"]
    L1 -- Miss --> L2{"L2 Redis Cache?"}
    L2 -- Hit (~1ms) --> PopL1["Populate L1"] --> Ret
    L2 -- Miss --> InFlight{"In-Flight Singleflight?"}
    
    InFlight -- "Duplicate Request" --> AwaitPromise["Await Running Fetcher Promise<br/>(ZERO extra DB load)"] --> Ret
    InFlight -- "First Request" --> DB["Query PostgreSQL (EXPLAIN Optimized)"]
    DB --> CacheWrite["Write to L2 (with jittered TTL) + L1"] --> Ret
```

### Thundering Herd & Cache Stampede Mitigation
When a popular cache key expires under heavy traffic, thousands of concurrent requests miss simultaneously and overwhelm the database.

**Invariant Pattern: In-Flight Request Deduplication (Singleflight)**:
Coalesce identical concurrent cache misses onto a single shared Promise.

```typescript
// Implementation of in-flight promise deduplication
class RequestDeduplicator {
  private inFlight = new Map<string, Promise<any>>();

  async execute<T>(key: string, fetcher: () => Promise<T>): Promise<T> {
    const existing = this.inFlight.get(key);
    if (existing) {
      return existing as Promise<T>;
    }

    const promise = (async () => {
      try {
        return await fetcher();
      } finally {
        this.inFlight.delete(key);
      }
    })();

    this.inFlight.set(key, promise);
    return promise;
  }
}

export const singleflight = new RequestDeduplicator();
```

### Jittered TTL (Eliminating Synchronized Expirations)
Never set static TTLs on batch-seeded caches. Always add pseudo-random jitter:
```typescript
function getJitteredTTL(baseTTLSeconds: number, jitterPercent = 0.15): number {
  const variation = baseTTLSeconds * jitterPercent * (Math.random() * 2 - 1);
  return Math.floor(baseTTLSeconds + variation);
}
// 3600s with 15% jitter -> distributed uniformly between 3060s and 4140s
```

---

## 4. Node.js & Bun Event Loop Protection

Node.js and Bun execute JavaScript application code on a single thread. Synchronous CPU-bound tasks block the event loop, causing all concurrent HTTP requests to stall and spiking p99 latency.

### The Cardinal Event Loop Rules
1. **Never parse multi-megabyte JSON synchronously on the main thread**. Stream or chunk parse large payloads.
2. **Chunk Large Iterations with `setImmediate` or Macro-tasks**:
   ```typescript
   async function processLargeBatch<T>(items: T[], batchSize: number, processor: (item: T) => Promise<void>) {
     for (let i = 0; i < items.length; i += batchSize) {
       const chunk = items.slice(i, i + batchSize);
       await Promise.all(chunk.map(processor));
       // Yield event loop to let I/O and health checks execute
       await new Promise((resolve) => setImmediate(resolve));
     }
   }
   ```
3. **Move CPU-Intensive Tasks to Worker Threads**:
   Password hashing (Argon2 / Scrypt), PDF/image generation, complex calculations, or large CSV generation MUST run in `worker_threads` or dedicated background workers (BullMQ / RabbitMQ).

---

## 5. Unbounded Queries & Resilient Pagination

### Offset vs Keyset (Cursor) Pagination
`OFFSET 100000 LIMIT 20` forces the database to read 100,020 rows, sort them, and discard the first 100,000. It scales $O(N)$ with page depth.

```
OFFSET 10:      Read 30 rows     → ~1ms
OFFSET 10000:   Read 10,020 rows → ~45ms
OFFSET 500000:  Read 500,020 rows → ~1,850ms (Disk I/O Spike)
```

**Keyset Pagination Standard ($O(1)$ constant time)**:
Filter against the index on the last retrieved cursor:

```sql
-- Keyset cursor query: constant time regardless of page depth
SELECT id, created_at, title
FROM articles
WHERE (created_at, id) < ('2026-10-12 14:30:00', 49201)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

---

## 6. TTFB Optimization & Server-Timing Headers

Server response latency directly gates the entire downstream client rendering waterfall.

### Server-Timing Header Standard
Instrument every critical API endpoint with the standard `Server-Timing` HTTP header. This surfaces micro-benchmarks directly in browser DevTools Network waterfalls without exposing internal logs:

```typescript
export async function handleRequest(req: Request, res: Response) {
  const startTotal = performance.now();

  const startDb = performance.now();
  const data = await fetchFromDatabase();
  const dbDur = (performance.now() - startDb).toFixed(1);

  const startCache = performance.now();
  await updateSessionCache();
  const cacheDur = (performance.now() - startCache).toFixed(1);

  const totalDur = (performance.now() - startTotal).toFixed(1);

  res.setHeader(
    'Server-Timing',
    `db;dur=${dbDur};desc="PostgreSQL Query", cache;dur=${cacheDur};desc="Redis Ops", total;dur=${totalDur}`
  );

  return res.json(data);
}
```

---

## 7. Systematic Measurement & Verification Workflow

```
1. MEASURE  → Establish baseline with EXPLAIN ANALYZE, wrk, autocannon, or APM
2. IDENTIFY → Pinpoint root cause (Disk read, N+1 cascade, Event Loop lag, missing index)
3. FIX      → Apply targeted index, singleflight cache, or query restructuring
4. VERIFY   → Re-measure using identical command, sample size, and concurrency
5. GUARD    → Add regression test or query execution time assertions
```

### Verification Rules
1. **Re-measure the way you measured the baseline**: Same tool (`autocannon`, `k6`, `EXPLAIN ANALYZE`), same dataset volume, same concurrency.
2. **Beat the noise, not just the mean**: An optimization that drops latency from 45ms to 43ms inside ±4ms variance is a placebo. Revert it.
3. **Correctness gates the metric**: An optimization that wins by skipping validation, omitting transactions, or risking stale reads is a regression. Revert immediately.

### Verification Checklist
- [ ] `EXPLAIN (ANALYZE, BUFFERS)` confirms zero sequential scans on large tables.
- [ ] Buffer cache hit ratio is ≥ 99% for hot read paths.
- [ ] No N+1 query loops present in ORM or service resolvers.
- [ ] Caches use request deduplication (singleflight) and jittered TTL.
- [ ] Endpoints return `Server-Timing` headers for visibility.
- [ ] Keyset/cursor pagination used for unbounded collections.
- [ ] Event loop lag remains under 10ms during peak load tests.
- [ ] Healthcheck endpoints (/health) bypassed in request loggers to eliminate disk I/O.
- [ ] Postgres connection pools bounded via connection_limit and pool_timeout parameters.
- [ ] Multi-entity list cache keys sorted deterministically.

---

## 8. Production Runtime & Database Pool Guardrails

### 8.1. Healthcheck Log Noise & Disk I/O Suppression
In containerized architectures behind reverse proxies (Caddy, Nginx, AWS ALB, Docker healthcheck probing `/health` every 10-15s):
- **Problem**: Default request logging middleware (`console.log(<-- GET /health)`) generates thousands of log lines daily, flooding terminal log stream viewers (Dozzle, CloudWatch) and creating continuous disk I/O on limited VPS SSDs.
- **Implementation Standard**: Request logging middleware MUST explicitly bypass `/health` before timing evaluation:
```typescript
app.use("*", async (c, next) => {
  if (c.req.path === "/health") {
    return next();
  }
  const start = performance.now();
  await next();
  console.log(`--> ${c.req.method} ${c.req.path} ${c.res.status} ${(performance.now() - start).toFixed(1)}ms`);
});
```

### 8.2. PostgreSQL Connection Pool Boundary Constraints
Prisma and standard ORMs often default to unbounded connection pools or scale with CPU count. On memory-constrained VPS instances (e.g. 4 vCPUs, 8GB RAM):
- **Problem**: When multiple worker containers, subagents running test suites, or concurrent CLI instances run simultaneously, database connection counts explode past PostgreSQL's `max_connections`, causing catastrophic fatal crashes: `FATAL: remaining connection slots are reserved for non-replication superuser connections`.
- **Implementation Standard**: All container manifests and production `DATABASE_URL` strings MUST explicitly bound pool parameters:
```text
postgresql://user:pass@host:5432/db?sslmode=disable&connection_limit=10&pool_timeout=15
```
- `connection_limit=10`: Restricts maximum concurrent client connection pool size per instance.
- `pool_timeout=15`: Sets maximum wait time (15 seconds) before throwing error if pool is saturated, preventing unbounded connection queues.

### 8.3. Valkey/Redis Fast-Path for Chained Audit Trails (SHA-256)
Tamper-evident audit trails with cryptographic block chaining require retrieving the preceding record's hash to compute `Hash = SHA256(PrevHash + Data)`.
- **Problem**: Executing `prisma.sessionAuditLog.findFirst({ orderBy: { createdAt: 'desc' } })` on every single mutating operation creates heavy database read contention and adds 10-25ms to API write latency.
- **Fast-Path Implementation Standard**:
  1. Upon successful audit log creation, cache the newly generated hash to Valkey: `await redis.set("audit:latest_hash", hash, "EX", 86400)`.
  2. For subsequent records, read `audit:latest_hash` directly from Valkey first. Fallback to PostgreSQL `findFirst` only on cache miss. This drops hash resolution from 15ms down to <0.5ms.

### 8.4. Deterministic Multi-Entity Cache Keys
For endpoints querying multiple entity IDs (e.g. `?userIds=userB,userA` vs `?userIds=userA,userB`):
- **Implementation Standard**: ALWAYS sort entity IDs lexicographically before constructing the cache key:
```typescript
const sortedIds = [...targetUserIds].sort().join(",");
const cacheKey = `staff-tasks:stats:${role}:${sortedIds}`;
```
- Eliminates duplicate cache entries caused by parameter order permutations and maximizes the cache hit ratio.

### 8.5. Integer Lower-Bound Jitter Range Assertion in Tests
When verifying Jittered TTL in unit test suites (e.g. base TTL 30s with ±15% jitter):
- In JavaScript, `30 * (1 - 0.15)` produces `25.499999999999996` in IEEE-754 double precision, which integer rounding or random generators can evaluate to `25`.
- **Testing Standard**: Always apply `Math.floor()` for lower bound assertions to prevent IEEE-754 test flakiness:
```typescript
expect(actualTTL).toBeGreaterThanOrEqual(Math.floor(baseTTL * (1 - jitterRatio)));
expect(actualTTL).toBeLessThanOrEqual(Math.ceil(baseTTL * (1 + jitterRatio)) + 1);
```

### 8.6. Cross-Domain & Bi-Directional Cache Invalidation Coupling (REST / CQRS / Cron)
When read endpoints cache domain or aggregate state (dashboards, monthly reports, shift calendars, task summaries, or gamified reward eligibility):
- **Problem**: Mutations performed in one actor's namespace (e.g. a worker checking in on `POST /api/checkins`, submitting a task on `POST /api/tasks/submit`, swapping a shift, or an automated cron job closing a payroll period) often only invalidate narrow route-local keys, leaving cross-cutting views (`admin:dashboard*`, `staff:home:*`, `staff:reports:*`, `staff:rewards:leaderboard:*`, `lucky-wheel:status:*`, `gacha:status:*`) serving stale state until TTL expiry.
- **Implementation Standard**:
  1. Centralize domain eviction helpers (`invalidatePayrollCache()`, `invalidateScheduleCache()`, `invalidateTaskSummaryCache(userId)`) and invoke cross-domain wildcard patterns atomically via `Promise.all` on every mutating route (staff actions, admin reviews, and background cron jobs):
     ```typescript
     await Promise.all([
       invalidatePayrollCache(),
       invalidateScheduleCache(),
       invalidateCachePattern(`staff:tasks:carrying-summary:${userId}*`),
       invalidateCachePattern(`lucky-wheel:status:${userId}:*`),
       invalidateCachePattern(`gacha:status:${userId}:*`),
       invalidateCachePattern("staff:reports:*"),
       invalidateCachePattern("staff:rewards:leaderboard:*"),
       invalidateCachePattern("staff:home:*"),
       invalidateCachePattern("admin:dashboard*"),
     ]).catch(() => {});
     ```
  2. Share global meta cache keys (`meta:lucky-wheel:prizes`, `meta:holidays:all`, `meta:documents:all`, `meta:task-definitions:*`) across staff, admin, and AI/RAG fallback routers (e.g. `POST /api/documents/chat` keyword fallback) so a single admin mutation or cached catalog serves all consumer views without uncached table scans.
  3. Synchronize bi-directional task marketplace caches (`tasks:items:*`, `staff:tasks:*`, `admin:tasks:*`, `user:tasks:my:*`) across both admin definition/item mutations and staff task-claim actions (`POST /api/staff/tasks/claim`).

### 8.7. Composite B-Tree Index Synthesis: Equality First, Range/Sort Second & FK Cascades
In PostgreSQL, single-column indexes on high-cardinality operational tables (`CheckIn`, `WorkShift`, `UserTask`, `TaskDefinition`, `StaffTask`, `SessionAuditLog`, `Payslip`, `Request`) force the planner into Bitmap Index Scans followed by expensive heap rechecks or in-memory/disk `Sort Key` operations. Furthermore, PostgreSQL does **not** automatically index child Foreign Key columns, causing sequential table scans during `onDelete: Cascade`.
- **Implementation Standard**:
  1. **Equality First, Range/Sort Second**: Always order composite B-Tree index columns with exact equality predicates (`=`) first, followed by range (`BETWEEN`, `>=`, `<=`) or sort (`ORDER BY ... DESC`) columns:
     ```prisma
     model CheckIn {
       // WHERE userId = $1 AND type = $2 AND timestamp BETWEEN $3 AND $4
       @@index([userId, type, timestamp])
     }

     model WorkShift {
       // WHERE userId = $1 AND status = $2 AND start >= $3 AND end <= $4
       @@index([userId, status, start, end])
     }

     model TaskDefinition {
       // WHERE unit = $1 AND active = true ORDER BY baseReward ASC
       @@index([unit, active, baseReward])
       @@index([active, name])
     }

     model UserTask {
       // WHERE status = $1 AND taskDefId = $2 ORDER BY submittedAt DESC
       @@index([status, taskDefId, submittedAt])
       @@index([userId, taskDefId, createdAt])
       @@index([userId, status, submittedAt])
     }

     model SessionAuditLog {
       // WHERE action = $1 AND status = $2 ORDER BY createdAt DESC
       @@index([action, status, createdAt])
       @@index([userId, action, createdAt])
     }
     ```
  2. **Explicit Foreign Key Child Indexes**: Always declare `@@index([parentId])` on child tables participating in `onDelete: Cascade` (e.g. `ManagerChecklistCompletion.taskId`) to prevent table locks during parent deletion.

### 8.8. Multi-Table Aggregation Caching, SingleFlight Coalescing & Dynamic State-Aware TTL
High-level dashboards, payroll summaries, and multi-sheet data exports routinely execute 4–10 queries per request:
- **Implementation Standard**:
  1. **Parallelize Independent Queries (`Promise.all`)**: Never `await` independent entity queries sequentially; overlap database I/O with `const [users, checkins, shifts, requests] = await Promise.all([...])`.
  2. **SingleFlight Coalesced Caching (`getOrSetCache`)**: Wrap multi-query aggregations in `getOrSetCache(cacheKey, ttl, fetcher)` with in-flight promise deduplication and ±15% TTL jitter so burst traffic coalesces into 1 DB query batch.
  3. **Immutable Closed-Period Fast Path & Dynamic State-Aware TTL**: When querying historical financial or payroll periods (`GET /api/admin/payroll`, `GET /api/staff/payroll`), check if `period.status === "CLOSED"`. If closed, serve the frozen `Payslip` snapshot directly without recalculating live attendance/shift joins, and assign a longer TTL via a state-aware resolver (`ttlSeconds: (data) => data.isClosed ? 300 : 60`).

### 8.9. Container Runtime, PostgreSQL `shm_size` & Blue-Green Rollout (Delegated to `infra-performance-optimization`)
- For dual-network Blue-Green container attachment (`ops_bridge` + `<project>-infra`), strict `"status":"ok"` health probes, PostgreSQL container `shm_size: 512mb` + `random_page_cost=1.1`, and Linux kernel TCP BBR tuning, refer to the companion **`infra-performance-optimization`** skill (§3, §5, and §6).

### 8.10. Perpetual Background Singleflight Cache Warmer & Detached SWR Revalidation (Sub-10ms SSR TTFB)
In SSR dashboards (Next.js App Router Server Components) backed by remote PostgreSQL databases:
- **Problem A (Synchronous SWR Revalidation Blocking RSC Stream Completion)**:
  In an in-memory Singleflight + Stale-While-Revalidate (SWR) cache (`singleflight.execute(key, fn, { ttlMs, staleTtlMs })`), when a request arrives in the stale window (`now >= entry.expiresAt && now < entry.staleUntil`), calling `this._revalidate(key, fn, ttlMs, staleTtlMs)` synchronously inside the Server Component's execution context can cause Next.js's async context tracking to wait for the spawned promise before closing the HTTP response stream — resulting in a `1.2s–2.3s` TTFB spike whenever the cache is stale.
- **Problem B (DB Connection Pool Idle Drop + Cold Cache Expiry)**:
  If PostgreSQL client `idle_timeout` is short (`30s`) and cache `ttlMs` is `60s`, 60 seconds of quiet traffic causes all pooled TCP connections to close **and** the L1 cache entry to expire simultaneously. The next visitor pays the full TCP/TLS handshake + multi-query penalty.
- **Implementation Standard**:
  1. **Detach SWR Revalidation from the Request Context**: Schedule background revalidation on the macrotask queue via `setTimeout(..., 0)` so the current Server Component returns `entry.value` in `<0.1ms` without attaching the DB promise to the active request span:
     ```javascript
     if (now < entry.staleUntil) {
       if (!this.inFlight.has(key)) {
         setTimeout(() => {
           if (!this.inFlight.has(key)) {
             this._revalidate(key, fn, ttlMs, staleTtlMs);
           }
         }, 0);
       }
       return entry.value;
     }
     ```
  2. **Perpetual Background Cache Warmer (`.unref()`)**: Register a singleton background interval (`interval < ttlMs`, e.g. `45s` interval for a `120s` TTL) that proactively refreshes critical landing payloads (`overview:page:v1`, `matrix:365`) in the background, paired with `idle_timeout: 120` on the DB connection pool:
     ```javascript
     if (typeof setInterval !== 'undefined' && !globalThis.__overviewWarmer) {
       globalThis.__overviewWarmer = setInterval(() => {
         warmOverviewCache().catch(() => {});
       }, 45_000);
       if (typeof globalThis.__overviewWarmer.unref === 'function') {
         globalThis.__overviewWarmer.unref();
       }
     }
     ```
  - Guarantees `now < entry.expiresAt` is permanently true (`100%` L1 RAM hit rate) and keeps DB sockets warm, delivering consistent `<10ms` server compute time and `<100ms` end-to-end TTFB even after hours of zero visitor traffic.
