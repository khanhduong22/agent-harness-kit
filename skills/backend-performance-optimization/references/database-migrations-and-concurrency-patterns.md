# Advanced PostgreSQL Indexing, Singleflight Warmers, TimescaleDB & Zero-Downtime SQL Migrations

Companion reference for `backend-performance-optimization/SKILL.md` (§8.6 – §8.13).

---

## 8.6. Cross-Domain & Bi-Directional Cache Invalidation Coupling (REST / CQRS / Cron)
Centralize domain eviction helpers (`invalidatePayrollCache()`, `invalidateScheduleCache()`, `invalidateTaskSummaryCache(userId)`) and invoke cross-domain wildcard patterns atomically via `Promise.all` on every mutating route (staff actions, admin reviews, and background cron jobs):
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
Share global meta cache keys (`meta:lucky-wheel:prizes`, `meta:holidays:all`, `meta:documents:all`, `meta:task-definitions:*`) across staff, admin, and AI/RAG fallback routers, and synchronize bi-directional marketplace caches (`tasks:items:*`, `staff:tasks:*`, `admin:tasks:*`, `user:tasks:my:*`).

---

## 8.7. Composite B-Tree Index Synthesis: Equality First, Range/Sort Second & FK Cascades
1. **Equality First, Range/Sort Second**: Order composite B-Tree index columns with exact equality predicates (`=`) first, followed by range (`BETWEEN`, `>=`, `<=`) or sort (`ORDER BY ... DESC`) columns:
   ```prisma
   model WorkShift {
     // WHERE userId = $1 AND status = $2 AND start >= $3 AND end <= $4
     @@index([userId, status, start, end])
   }
   model UserTask {
     // WHERE status = $1 AND taskDefId = $2 ORDER BY submittedAt DESC
     @@index([status, taskDefId, submittedAt])
   }
   ```
2. **Explicit Foreign Key Child Indexes**: Always declare `@@index([parentId])` or `@@index([parentId, createdAt])` on child tables participating in `onDelete: Cascade` or sorted child lookups.

---

## 8.8. Multi-Table Read/Write Parallelization, SingleFlight Coalescing & Dynamic State-Aware TTL
1. **Parallelize Independent Reads, Writes & Cache Evictions (`Promise.all`)**: Overlap independent DB queries and `invalidateCachePattern` calls.
2. **SingleFlight Coalesced Caching (`getOrSetCache`)**: Wrap multi-query aggregations in `getOrSetCache(cacheKey, ttl, fetcher)` with in-flight promise deduplication and ±15% TTL jitter.
3. **Immutable Closed-Period Fast Path & Dynamic State-Aware TTL**: Serve frozen snapshots directly when `period.status === "CLOSED"` with state-aware TTL (`ttlSeconds: (data) => data.isClosed ? 300 : 60`).

---

## 8.9. Container Runtime, PostgreSQL `shm_size` & Blue-Green Rollout
Delegated to `infra-performance-optimization` (§3, §5, and §6).

---

## 8.10. Perpetual Background Singleflight Cache Warmer & Detached SWR Revalidation (Sub-10ms SSR TTFB)
1. **Detach SWR Revalidation from Request Context**: Schedule background revalidation on the macrotask queue via `setTimeout(..., 0)` so Next.js Server Components return `entry.value` in `<0.1ms` without blocking the RSC HTTP stream:
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
2. **Perpetual Background Cache Warmer (`.unref()`)**: Register a singleton background interval (`45s` interval for a `120s` TTL) with `.unref()` and `idle_timeout: 120` on the DB pool to keep L1 RAM hit rate at 100% and DB sockets warm.
3. **Non-Reentrant Singleflight Key Discipline**: Never wrap a function in `singleflight.execute(key, ...)` using the same `key` that the inner function already uses (`route:gold:v1` vs `data:gold:v1`), preventing circular Promise deadlocks.

---

## 8.11. TimescaleDB Compressed Hypertable Chunk Exclusion & High-Frequency Cron Short-Circuiting
1. **Always Bound the Partition Column (`created_at`) on Latest-Row Queries**:
   Add `AND created_at > NOW() - INTERVAL '14 days'` on `DISTINCT ON (symbol)` / `MAX(created_at)` queries so TimescaleDB prunes 80+ compressed historical chunks (`480.9ms` $\to$ `27.4ms`), with an unbounded fallback if empty:
   ```javascript
   let data = await sql`
     SELECT DISTINCT ON (symbol) symbol, price, created_at
     FROM price_ticks
     WHERE symbol LIKE 'METAL/%'
       AND created_at > NOW() - INTERVAL '14 days'
     ORDER BY symbol ASC, created_at DESC
   `;
   if (data.length === 0) {
     data = await sql`
       SELECT DISTINCT ON (symbol) symbol, price, created_at
       FROM price_ticks
       WHERE symbol LIKE 'METAL/%'
       ORDER BY symbol ASC, created_at DESC
     `;
   }
   ```
2. **Co-Filter by `created_at` on Epoch `timestamp` Reads, `WHERE NOT EXISTS`, and `UPDATE` Statements**:
   Include `created_at >= minIso AND created_at <= maxIso` on lookups (`126.8ms` $\to$ `0.21ms`) and `WHERE id = $1 AND created_at = $2` on `UPDATE` statements so `ModifyHypertable` prunes chunks at startup.
3. **Short-Circuit Background Alert Jobs**: Check `push_subscriptions` and `alert_cooldown` eligibility before querying `price_ticks` or `daily_ohlc`.

---

## 8.12. Pure Native PostgreSQL Time-Series Bucketing (`date_bin`), Window-Partitioned Batching (`ANY($1)`), and Deduplicated Bulk Upserts
1. **Native `date_bin` + Ordered `array_agg` Replacement**:
   ```sql
   SELECT
     date_bin('1 day', created_at, TIMESTAMPTZ '2000-01-01 00:00:00+00') AS bucket,
     (array_agg(price ORDER BY created_at DESC))[1] AS close
   FROM price_ticks
   WHERE symbol = $1 AND created_at > NOW() - INTERVAL '2 days'
   GROUP BY bucket
   ```
2. **Single-Query Window-Partitioned Batch History (`WHERE symbol = ANY($1)`)**:
   Coalesce N symbol history reads into 1 query using `ROW_NUMBER() OVER (PARTITION BY symbol ORDER BY bucket DESC)` to cap `limit` rows per symbol in a single round-trip.
3. **In-Memory Conflict-Key Deduplication Before Single Bulk `ON CONFLICT DO UPDATE`**:
   Deduplicate batch arrays via `new Map(...)` by composite conflict key before executing bulk `INSERT ${sql(deduped)} ON CONFLICT (...) DO UPDATE` to avoid `ON CONFLICT DO UPDATE command cannot affect row a second time`.

---

## 8.13. Non-Destructive Materialized View & Hash-Gated SQL Migration Deploy Guard (Eliminating 10m+ Deploy Stalls)

### Layer 1: Idempotent, Non-Destructive SQL Migrations
1. **Never `DROP MATERIALIZED VIEW ... CASCADE` in recurring setup scripts**: Use `CREATE MATERIALIZED VIEW IF NOT EXISTS` and `CREATE UNIQUE INDEX IF NOT EXISTS`.
2. **Conditional `REPLICA IDENTITY` & Incremental Publication Membership**: Check `pg_class.relreplident <> 'd'` before `ALTER TABLE ... REPLICA IDENTITY DEFAULT`, and check `pg_publication_tables` before `ALTER PUBLICATION ... ADD TABLE` to avoid `AccessExclusiveLock` contention with `walsender`.
3. **Guard TimescaleDB Compression Policy Alterations**: Check `timescaledb_information.hypertables WHERE compression_enabled = false` before `ALTER TABLE ... SET (timescaledb.compress)`.

### Layer 2: Zero-Table Content-Hash Gate in PostgreSQL Catalog (`COMMENT ON SCHEMA`) + `ispopulated` Guard
1. Compute SHA-256 over sorted `.sql` migration files and store/read via `COMMENT ON SCHEMA public IS 'app-setup:v1:{"hash":"..."}'` (`pg_catalog.obj_description('public'::regnamespace, 'pg_namespace')`).
2. Check `SELECT matviewname, ispopulated FROM pg_matviews WHERE schemaname = 'public'` and only run `REFRESH MATERIALIZED VIEW CONCURRENTLY` when `ispopulated` is `false`.
3. Gate CLI seed/migration entry points with `require.main === module` / `import.meta.url` so importing helper functions never calls `process.exit(0)`.

### Layer 3: Zero-Downtime `deploy.sh --check` Fast-Path
```bash
if bun run setup --check >/dev/null 2>&1; then
  echo "✓ PostgreSQL schema & materialized views up-to-date (hash match). Skipping migration stop-window."
else
  echo "Schema deltas detected. Running idempotent migrations..."
  bun run setup
fi
```
