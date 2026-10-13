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

### 8.6. Cross-Domain Invalidation Coupling in REST / CQRS APIs
When aggregate administrative dashboards (`GET /api/admin/requests`, `GET /api/admin/tasks`, `GET /api/manager-tasks/checklist`) cache system state with long TTLs:
- **Problem**: Staff client actions (submitting a leave/wfh request `POST /api/requests`, submitting a task `POST /api/staff/tasks/submit`, or toggling a checklist item) only invalidate staff-scoped keys, leaving admin/management dashboards displaying stale queues until TTL expiration.
- **Implementation Standard**: Mutating actions MUST cross-invalidate parent oversight cache patterns:
```typescript
// When staff submits a request:
await invalidateCachePattern(`user:requests:${userId}*`);
await invalidateCachePattern("admin:requests:*"); // Proactively invalidate admin queue
```

### 8.7. Composite Index Ordering for Filter + Sort Access Patterns
In relational databases (PostgreSQL), queries that filter by tenant or user and sort by creation timestamp (`WHERE user_id = $1 ORDER BY created_at DESC`):
- **Problem**: Separate single-column indexes on `userId` and `createdAt` force the query planner into a Bitmap Index Scan followed by an explicit memory/disk sort (`Sort Key: createdAt` in EXPLAIN ANALYZE).
- **Implementation Standard**: Define a composite B-Tree index with the equality filter column first and the sort column second:
```prisma
model UserTask {
  // ...
  @@index([userId, createdAt])
  @@index([createdAt]) // Retained for global chronological feeds
}
```
- Completely eliminates explicit sort operations from execution plans, reducing query timing from ~45ms down to <1ms on high-cardinality tables.

### 8.8. Multi-Table Aggregation Dashboard Caching & SingleFlight Coalescing
High-level management dashboards (`GET /api/admin/dashboard`, `GET /api/admin/dashboard-stats`) routinely aggregate 8+ distinct database queries in a single HTTP request (`Promise.all([findMany, count, count, findMany...])`).
- **Problem**: When multiple administrators or automated monitors refresh simultaneously, running 8 heavy multi-table aggregations concurrently leads to database lock contention, memory spikes, and degraded throughput.
- **Implementation Standard**:
  1. Wrap the entire aggregated response calculation with `getOrSetCache(key, ttl)` backed by in-flight deduplication (`singleflight`):
     ```typescript
     const cacheKey = `admin:dashboard:${dateStr}`;
     const data = await getOrSetCache(cacheKey, 30, async () => {
       const [shifts, checkins, requests, kpis] = await Promise.all([...]);
       return { shifts, checkins, requests, kpis };
     });
     ```
  2. Use a short base TTL (30s) with pseudo-random jitter. This prevents stale operational visibility while completely shielding the database from burst concurrency.
  3. **Atomic Wildcard Prefix Invalidation Pattern**: Mutating operations (check-in creation, shift adjustments, request approvals) must invalidate both the overview and sub-stats keys in a single atomic Valkey/Redis call:
     ```typescript
     // Purges both "admin:dashboard:<date>" and "admin:dashboard-stats:<date>" atomically
     await invalidateCachePattern("admin:dashboard*");
     ```

### 8.9. Read-Heavy Master Configuration & Meta-Data Caching
System configuration tables and reference data (such as company holidays, allowed IP ranges, task definitions, and prize catalogs) exhibit read-to-write ratios exceeding 1,000:1.
- **Problem**: Querying PostgreSQL on every incoming API request for static configurations adds unnecessary connection latency and pool contention.
- **Implementation Standard**: Cache master configuration endpoints with long TTLs (600s - 1800s / 10-30 minutes) and wire direct invalidations on administrative mutations:
  ```typescript
  // Master read path
  const holidays = await getOrSetCache("meta:holidays:all", 1800, async () => {
    return prisma.holiday.findMany({ orderBy: { date: "asc" } });
  });

  // Mutating path (Create / Update / Delete)
  await prisma.holiday.create({ data });
  await invalidateCachePattern("meta:holidays:*");
  ```
- Ensures sub-millisecond retrieval of organizational rules and zero database load for static master lookups.

### 8.10. Foreign Key Reverse Cascade & User Activity Composite Indexing
In relational databases (PostgreSQL), foreign keys do NOT automatically create backing indexes for reverse lookups or cascade operations.
- **Problem**: When a parent record is deleted or updated in tables with `onDelete: Cascade` (e.g. `ManagerChecklistCompletion` referencing `ManagerChecklistTask` via `taskId`), PostgreSQL must execute a sequential scan on the child table to locate referencing rows, creating write locks and transaction stalls.
- **Implementation Standard**:
  1. Always declare explicit indexes on child foreign key columns:
     ```prisma
     model ManagerChecklistCompletion {
       id     String @id @default(cuid())
       taskId String
       // ...
       @@index([taskId])
     }
     ```
  2. For user-scoped activity feeds sorted by recent updates (`WHERE userId = $1 ORDER BY updatedAt DESC`):
     ```prisma
     model UserTask {
       // ...
       @@index([userId, updatedAt])
     }
     ```
  - Eliminates table-wide sequential scans during cascade operations and enables zero-cost backwards Index Scans for user activity streams.

### 8.11. Composite Query Caching with Compound Temporal Keys
For multi-dimensional operational metrics and recurring checklist calculations (`GET /api/manager-tasks/stats-history`, `GET /api/manager-tasks/weekly`):
- **Problem**: Queries aggregate daily details across date ranges, user assignments, and completion states, creating expensive multi-table scans on every client polling interval.
- **Implementation Standard**:
  1. Scope compound cache keys with normalized ISO temporal intervals:
     ```typescript
     const statsHistoryKey = `manager-tasks:stats-history:${targetUserId}:${monthStr}`;
     const weeklyKey = `manager-tasks:weekly:${targetUserId}:${weekStartStr}`;
     ```
  2. Implement dual-pattern cross invalidation on task state mutations (toggle, carry-over, CRUD):
     ```typescript
     await invalidateCachePattern("manager-tasks:weekly:*");
     await invalidateCachePattern("manager-tasks:stats-history:*");
     ```
  - Yields instant sub-millisecond retrieval on repeated manager console loads while ensuring live data freshness upon mutation.

### 8.12. Background Cron Cache Coupling & Active Feed Compound Indexing
In multi-tier systems with automated background processes and real-time status feeds:
- **Problem A (Cron Cache Desync)**: Background scheduled jobs (cron handlers, event consumers) that generate bonuses, reconcile timesheets, or close fiscal periods operate outside user-facing HTTP request flows. If user-facing endpoints cache financial summaries (`payroll:*`, `staff:payroll:*`) or operational KPI metrics (`stats:*`), background DB mutations leave frontend caches stale until TTL expiration.
- **Implementation Standard**:
  1. Every automated cron handler modifying financial adjustments or entity states MUST invoke domain cache eviction promises before returning:
     ```typescript
     await Promise.all([
       invalidatePayrollCache(),
       invalidateCachePattern("staff:payroll:*"),
       invalidateCachePattern("stats:*"),
     ]).catch(() => {});
     ```
- **Problem B (Active Feed Indexing)**: Status-filtered chronological feeds (`WHERE active = true ORDER BY createdAt DESC`) incur costly sequential scans or slow heap fetches if indexed solely on `createdAt`.
- **Implementation Standard**:
  2. Implement composite index with Equality First, Range/Sort Second:
     ```prisma
     model Announcement {
       active    Boolean  @default(true)
       createdAt DateTime @default(now())
       // ...
       @@index([active, createdAt])
       @@index([createdAt])
     }
     ```
### 8.13. Multi-Table Aggregation Caching & Compound Reverse Audit Indexing
In administrative management platforms and audit-heavy operational workflows:
- **Problem A (Multi-Table Aggregation Bottleneck)**: Comprehensive detail endpoints (such as `GET /api/admin/employees/:id` or monthly user balance inspections) repeatedly compute multi-table metrics (aggregating checkins, shifts, overtime adjustments, penalties, and bonuses) on every modal open or route transition. This creates multiple sequential database queries and high CPU serialization overhead.
- **Implementation Standard**:
  1. Scope compound cache keys with entity identifier and temporal periods:
     ```typescript
     const cacheKey = `admin:employee-detail:${id}:${month}:${year}`;
     const data = await getOrSetCache(cacheKey, 60, async () => {
       const user = await prisma.user.findUnique({ where: { id } });
       const stats = await calculateUserMonthlyStats(id, targetDate);
       return { user, stats };
     });
     ```
  2. Implement cross-domain invalidation triggers across all modifying routes:
     - User profile/status changes (`PATCH /api/admin/employees/:id/status`, `PATCH /api/admin/users/:id`).
     - Shift modifications, attendance adjustments, and bonus allocations.
     ```typescript
     await invalidateCachePattern("admin:employee-detail:*");
     ```
- **Problem B (Reverse Audit Query Sort Overhead)**: Audit logs (`ShiftAuditLog`, `SecurityLog`) are frequently queried by entity (`userId`, `shiftId`) with reverse chronological ordering (`ORDER BY createdAt DESC`). Without compound keys, the database performs an index scan followed by an external memory/disk sort.
- **Implementation Standard**:
  3. Implement compound indexes matching Filter First, Sort Order Second:
     ```prisma
     model ShiftAuditLog {
       userId    String
       shiftId   String?
       createdAt DateTime @default(now())
       // ...
       @@index([userId, createdAt])
       @@index([shiftId, createdAt])
     }
     ```
  - Eliminates explicit sort operations entirely, executing sub-millisecond Index Scans directly in order.

### 8.14. Bulk Multi-User Calculation Caching & Dual Composite Shift Indexing
In multi-tenant operations dashboards, attendance aggregators, and payroll modules:
- **Problem A (Bulk Iterative Stats Bottleneck)**: Overview endpoints (such as `GET /api/admin/payroll`) iterate over all active and historic staff members to compute live monthly metrics (`calculateUserMonthlyStats`) concurrently. A single request executes dozens or hundreds of sub-queries (checkins, shifts, deductions, bonuses).
- **Implementation Standard**:
  1. Scope composite period cache keys for both organization-wide overviews and individual user inspects:
     ```typescript
     const payrollOverviewKey = `admin:payroll:${month}:${year}`;
     const userPayrollKey = `admin:payroll-user:${userId}:${month}:${year}`;
     ```
  2. Centralize eviction inside domain cache flush functions (`invalidatePayrollCache`):
     ```typescript
     await Promise.all([
       invalidateCachePattern("admin:payroll:*"),
       invalidateCachePattern("admin:payroll-user:*"),
       invalidateCachePattern("admin:employee-detail:*"),
       invalidateCachePattern("staff:payroll:*"),
     ]);
     ```
  - Reduces multi-user payroll calculation time from ~2500ms down to sub-5ms on subsequent requests.
- **Problem B (Status & Schedule Filter Overhead)**: High-frequency shift and task queries frequently combine status equality with temporal ranges or user identifiers (`WHERE status = 'APPROVED' AND start >= ...`). Single-column indexes force post-index heap filter steps.
- **Implementation Standard**:
  3. Implement dual composite indexes for equality filtering and range ordering:
     ```prisma
     model WorkShift {
       // ...
       @@index([status, start])
       @@index([userId, status])
     }

     model ShiftDuty {
       // ...
       @@index([shiftId, isCompleted])
       @@index([date, isCompleted])
     }
     ```
  - Enables PostgreSQL to execute Index Only / Bitmap Index Scans directly, bypassing heap filter passes.

### 8.15. Marketplace & Activity Summary Caching with Unit Key Compound Indexes
In task marketplaces, piece-rate incentive platforms, and worker activity trackers:
- **Problem A (Marketplace & Incentive Summary Thrashing)**: Endpoints fetching available marketplace tasks (`GET /api/tasks/items`) or computing piece-rate bonus summaries (`GET /api/staff/tasks/packing-summary`, `GET /api/staff/tasks/carrying-summary`) run repetitive multi-table joins and in-memory aggregation loops across task records.
- **Implementation Standard**:
  1. Scope cache keys by domain and worker identifier:
     ```typescript
     const marketplaceKey = "tasks:items:all";
     const packingSummaryKey = `staff:tasks:packing-summary:${userId}`;
     const carryingSummaryKey = `staff:tasks:carrying-summary:${userId}`;
     ```
  2. Implement cross-domain eviction upon task claim, submission, or review:
     ```typescript
     await invalidateCachePattern("tasks:items:*");
     await invalidateCachePattern("staff:tasks:*");
     ```
- **Problem B (Definition & Task Item Status Lookups)**: Queries frequently filter definitions by unit and active status (`WHERE unit = '...' AND active = true`), and task items by assignee and status.
- **Implementation Standard**:
  3. Implement composite indexes matching unit/status filtering:
     ```prisma
     model TaskDefinition {
       // ...
       @@index([unit, active])
       @@index([active])
     }

     model TaskItem {
       // ...
       @@index([assigneeId, status])
       @@index([status])
     }
     ```
  - Reduces marketplace query latency from table scans to instant Index Scans with zero sequential scan overhead.


### 8.16. Security Audit Log Caching & Multi-Filter Event Compound Indexing
In system audit logs, access control event trackers, and enterprise security streams:
- **Problem A (Security Stream Query Latency)**: Audit endpoints (`GET /api/auth/audit-logs`) query hundreds of thousands of events, frequently paginated and filtered by multiple dimensions (`action`, `status`, `userId`, `search`). Uncached queries repeatedly execute full table counts and findMany joins on every page navigation.
- **Implementation Standard**:
  1. Scope multi-dimensional filter cache keys with short TTLs (30s):
     ```typescript
     const cacheKey = `auth:audit-logs:${page}:${limit}:${action || "ALL"}:${status || "ALL"}:${userId || "ALL"}:${search || "NONE"}`;
     const result = await getOrSetCache(cacheKey, 30, async () => {
       const [total, logs] = await Promise.all([
         prisma.sessionAuditLog.count({ where }),
         prisma.sessionAuditLog.findMany({ where, take: limit, skip: (page - 1) * limit, orderBy: { createdAt: "desc" } }),
       ]);
       return { total, logs, totalPages: Math.ceil(total / limit) };
     });
     ```
  2. Invalidate audit caches dynamically upon logging security events (`recordSecureAuditLog`):
     ```typescript
     await invalidateCachePattern("auth:audit-logs:*");
     ```
  - Yields sub-5ms response times on audit log pagination while ensuring immediate reflection of new security events.
- **Problem B (Action & Status Multi-Column Filter Sort)**: Security teams routinely audit failed logins or specific operational actions (`WHERE action = 'LOGIN' AND status = 'FAILED' ORDER BY createdAt DESC`). Without matching multi-column indexes, database engines perform multiple single-column index intersections followed by expensive external sorting.
- **Implementation Standard**:
  3. Implement compound indexes covering action, status, and chronological order:
     ```prisma
     model SessionAuditLog {
       action    String
       status    String   @default("SUCCESS")
       createdAt DateTime @default(now())
       // ...
       @@index([action, status, createdAt])
     }

     model UserTask {
       status      TaskStatus @default(PENDING)
       submittedAt DateTime?
       // ...
       @@index([status, submittedAt])
     }

     model Request {
       status    String   @default("PENDING")
       createdAt DateTime @default(now())
       // ...
       @@index([status, createdAt])
     }
     ```
  - Allows PostgreSQL to satisfy multi-column equality filters and reverse ordering via a single B-tree index scan, eliminating filesorts and reducing query execution time from >100ms down to <1ms.


### 8.17. Meta Resource Cross-Route Shared Caching & Cron Dashboard Eviction
In interactive features, gamified reward systems, and background cron aggregators:
- **Problem A (Duplicate Cache Keys & Redundant Querying)**: Shared entities (such as prize lists and recent winner feeds in lucky wheel / gacha) are frequently queried from multiple distinct route files (e.g. `lucky-wheel.route.ts` and `staff.route.ts`). If routes define independent or uncached queries, client traffic hits the database directly and invalidation in one route fails to update the other.
- **Implementation Standard**:
  1. Unify shared meta resources under consistent global keys across all routes:
     ```typescript
     const prizes = await getOrSetCache("meta:lucky-wheel:prizes", 300, () =>
       prisma.luckyWheelPrize.findMany({ where: { active: true }, orderBy: { createdAt: "asc" } })
     );
     const recentWinners = await getOrSetCache("meta:lucky-wheel:recent-winners", 60, () =>
       prisma.luckyWheelHistory.findMany({ take: 20, orderBy: { createdAt: "desc" }, include: { user: { select: { id: true, name: true, image: true } } } })
     );
     ```
  2. Invalidate shared keys and administrative endpoints on any mutation (spin, claim, update):
     ```typescript
     await invalidateCachePattern("meta:lucky-wheel:recent-winners");
     await invalidateCachePattern("admin:lucky-wheel:*");
     ```
- **Problem B (Cron Job Stale Overview Metrics)**: Background cron jobs (e.g. automatic monthly payroll closure, birthday bonuses, top performer rewards) insert adjustments and update period statuses, but frequently only invalidate specific payroll caches. Administrative dashboards (`admin:dashboard*`, `admin:dashboard-stats*`) continue serving cached pre-cron metrics.
- **Implementation Standard**:
  3. Include overview dashboard cache patterns in all cron invalidation batches:
     ```typescript
     await Promise.all([
       invalidatePayrollCache(),
       invalidateCachePattern("staff:payroll:*"),
       invalidateCachePattern("stats:*"),
       invalidateCachePattern("admin:dashboard*"),
     ]).catch(() => {});
     ```
  - Guarantees immediate real-time dashboard updates when automated cron background jobs complete.
