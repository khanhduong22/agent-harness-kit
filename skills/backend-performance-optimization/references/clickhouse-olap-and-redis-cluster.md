# ClickHouse OLAP, Redis Cluster & Horizontal Database Scaling

> Distilled from `ClickHouse/agent-skills`, `redis/agent-skills`, and `planetscale/database-skills`. Use when designing analytical/time-series schemas (`MergeTree`), diagnosing `CROSSSLOT` or hot keys on Redis Cluster, or planning multi-tenant relational sharding.

---

## 1. ClickHouse `MergeTree` Architecture & Query Laws

ClickHouse is a columnar OLAP engine with **sparse granule indexes (`index_granularity = 8192`)**—NOT an OLTP B-tree database. General Postgres intuition destroys ClickHouse performance:

### Schema & Sorting Key Design (`ORDER BY` & `PARTITION BY`)
1. **Plan `ORDER BY` Before Table Creation**: Sorting keys are immutable without table rewrites. Put the **most frequently filtered equality columns in lowest-to-highest cardinality order**, finishing with truncated timestamp buckets (`ORDER BY (tenant_id, event_type, toStartOfHour(created_at), created_at)`).
2. **`PRIMARY KEY` Is Sparse, NOT Unique**: ClickHouse does NOT enforce uniqueness on `PRIMARY KEY`. For idempotent upserts/updates, insert new versioned rows into **`ReplacingMergeTree(updated_at)`** and query with `argMax(col, updated_at) GROUP BY id` (avoid `FINAL` on huge hot tables unless strictly benchmarked).
3. **Partitioning Discipline**: Partition strictly for data lifecycle (`PARTITION BY toYYYYMM(created_at)` + `TTL`), **never** by high-cardinality IDs (`user_id`, `tenant_id`) or hourly buckets—keep total active partitions `< 100` per table to prevent "Too many parts" crashes. Small tables (`< 10M` rows) need NO `PARTITION BY` at all.
4. **Native Types & Encoding**: Avoid `Nullable(T)` wrappers inside hot filter columns (`Nullable` allocates a separate null-mask file and skips some vector optimizations; prefer default zero-values or sentinel values). Wrap repetitive strings (`< 10k` distinct values) in `LowCardinality(String)`, use `DateTime64(3, 'UTC')`, and minimize integer bitwidth (`UInt8` / `UInt16`).

### Ingestion, Mutations & Incremental Materialized Views
- **Batch Inserts Only (`10k–100k` rows/flush)**: Never issue single-row OLTP `INSERT` loops synchronously; use `async_insert=1, wait_for_async_insert=0` or batched streams (`RowBinary` / `JSONEachRow` over gzip HTTP in Node.js/TypeScript).
- **Ban Frequent OLTP `UPDATE` / `DELETE` Mutations**: `ALTER TABLE ... UPDATE/DELETE` rewrites entire column data parts asynchronously. Model updates as append-only event versions (`ReplacingMergeTree` / `CollapsingMergeTree`) and deletes via lightweight tombstones or partition drops.
- **Pre-Aggregate with Incremental Materialized Views**: Attach an `ON INSERT` Materialized View writing pre-aggregated `AggregateFunction` states into an explicit **`SummingMergeTree`** or **`AggregatingMergeTree`** target table (`-State` / `-Merge` combinators) instead of scanning raw billion-row tables per dashboard request.
- **Query Optimization**: Filter on leading `ORDER BY` keys so granule pruning triggers; move lightweight indexed predicates to **`PREWHERE`** (automatically done in modern ClickHouse for selective filters); prefer `ANY JOIN` or dictionary lookups (`dictGet`) over large distributed many-to-many `JOIN`s, and filter *before* joining.

---

## 2. Redis Cluster, Connections & Hot-Key Engineering (`redis/agent-skills`)

### Hash-Tag Slot Co-Location (Eliminating `CROSSSLOT`)
In a sharded Redis Cluster (`16,384` hash slots), multi-key operations (`MGET`, `MSET`, `SDIFF`, `SUNION`, Lua scripts, and cluster `MULTI`/`EXEC` transactions) fail with `CROSSSLOT Keys in request don't hash to the same slot` unless all keys share a **hash tag `{...}`**:
```text
❌ CROSSSLOT: user:42:profile  &  user:42:permissions   (hashed on full string -> different slots)
✅ Co-located: {user:42}:profile  &  {user:42}:permissions (hashed only on `user:42` -> identical slot)
```
- **Caveat**: Never use coarse global hash tags (like `{global}:...`) or every key lands on a single shard and bottlenecks cluster throughput. Keep hash tags scoped to a tenant, entity, or session ID.

### Connection Pooling, Timeouts & Read Replicas
- **Singleton Multiplexed Clients**: Never allocate per-request connections (`new Redis()` inside route handlers). Use one shared multiplexed connection pool per process with explicit `connectTimeout`, per-command timeout (`commandTimeout`), and bounded exponential jittered reconnect backoff.
- **Ban O(N) Production Footguns**: Never execute `KEYS *`, unbounded `SMEMBERS`, or unbounded `HGETALL` on production traffic (blocks Redis's single-threaded command loop). Always iterate via cursor-based `SCAN ... COUNT 200` and fetch hashes incrementally via `HSCAN` / `HMGET`.
- **Scaling Read-Heavy Fan-Out & Hot Keys**:
  - Enable `readFromReplicas` (`scaleReads: "slave"`) for cache-aside read bursts tolerant of sub-millisecond replication lag.
  - Neutralize hot-key saturation using **RESP3 client-side invalidation caching** or a tiny in-process L1 LRU cache (`1–3s` TTL) + key sharding (`hot:config:{0..7}`) read randomly.
  - Monitor `SLOWLOG GET 20` and command latency histograms (`redis_commands_duration_seconds`) before adding nodes.

---

## 3. Horizontal Relational Sharding & Pooling (`planetscale/database-skills`)

When single-primary Postgres/MySQL saturates write IOPS or table sizes cross multi-terabyte scale:
- **Choose High-Cardinality Uniform Shard Keys (`Vindex` / Citus Distribution Key)**: Shard by `organization_id` or `account_id` alongside primary lookup keys so `95%+` of hot transactional queries route to a **single shard** cleanly inside a single local ACID transaction. Avoid monotonically increasing timestamps as primary shard keys (creates write hotspots on the tail shard).
- **Quarantine Cross-Shard Joins & Online DDL**: Keep hot read/write endpoints single-shard; push cross-tenant analytics into ClickHouse/read replicas or maintain small **reference tables** replicated to every shard.
- **Transaction-Mode Pooling Hygiene (PgBouncer / VTGate)**: Inside transaction-mode pools, **never** depend on session-level state (`SET LOCAL` outside a transaction, session-scoped prepared statements if unsupported, `LISTEN/NOTIFY`, or advisory session locks across statements). Keep database transactions sub-`50ms` and move external HTTP/LLM calls strictly outside `BEGIN ... COMMIT`.
