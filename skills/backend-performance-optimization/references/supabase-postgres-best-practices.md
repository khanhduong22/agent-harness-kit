# Supabase Postgres & Row-Level Security (RLS) Best Practices (`supabase/agent-skills`)

Synthesized from [`supabase/agent-skills`](https://github.com/supabase/agent-skills) (`★ 44k+` — `supabase-postgres-best-practices`). Load this reference when designing PostgreSQL schemas, writing migrations, tuning Row-Level Security (RLS) policies, or diagnosing connection/lock bottlenecks.

---

## 1. Priority Matrix (8 Categories by Production Impact)

| Priority | Category | Impact | Core Invariant |
|---|---|---|---|
| **1** | **Query Performance (`query-`)** | CRITICAL | Every foreign key and RLS predicate column must be indexed; use `EXPLAIN (ANALYZE, BUFFERS)` |
| **2** | **Connection Management (`conn-`)** | CRITICAL | Route serverless/edge/multi-container traffic through transaction poolers (PgBouncer/Supavisor) with bounded `connection_limit` |
| **3** | **Security & RLS (`security-`)** | CRITICAL | Wrap `auth.uid()` / session functions in `(SELECT auth.uid())` so Postgres caches the scalar per-query instead of evaluating per-row |
| **4** | **Schema Design (`schema-`)** | HIGH | Prefer `TIMESTAMPTZ` over `TIMESTAMP`, `BIGINT` or `UUIDv7` for high-insert PKs, and `TEXT` over arbitrary `VARCHAR(255)` |
| **5** | **Concurrency & Locking (`lock-`)** | MEDIUM-HIGH | Always use `CREATE INDEX CONCURRENTLY` and short lock timeouts (`SET lock_timeout = '2s'`) in production migrations |
| **6** | **Data Access Patterns (`data-`)** | MEDIUM | Use cursor/keyset pagination (`WHERE (created_at, id) < ($1, $2)`) and batch upserts (`UNNEST` / `ON CONFLICT`) |
| **7** | **Monitoring (`monitor-`)** | LOW-MEDIUM | Track `pg_stat_statements` (`total_exec_time`, `shared_blks_read`) and unused/duplicate indexes |
| **8** | **Advanced Features (`advanced-`)** | LOW | Use `pgvector` HNSW indexes with tuned `ef_search` and partial indexes for active status subsets |

---

## 2. Critical Row-Level Security (RLS) Performance Rules

Unoptimized RLS policies are the #1 hidden cause of `100x` query slowdowns in multi-tenant Postgres databases.

### Rule 2.1: Wrap Session/Auth Functions in `(SELECT ...)` (`InitPlan` Caching)
Calling `auth.uid()` or `current_setting('app.tenant_id')` directly in a `USING` clause forces PostgreSQL to invoke the function **once for every scanned row**. Wrapping it in `(SELECT ...)` turns it into an `InitPlan` evaluated **once per query**:

```sql
-- ❌ BAD: Evaluates auth.uid() 100,000 times on a 100k-row scan
CREATE POLICY "users_read_own_orders" ON public.orders
FOR SELECT TO authenticated
USING (user_id = auth.uid());

-- ✅ GOOD: InitPlan caches (SELECT auth.uid()) once per query (up to 100x faster)
CREATE POLICY "users_read_own_orders" ON public.orders
FOR SELECT TO authenticated
USING (user_id = (SELECT auth.uid()));
```

### Rule 2.2: Index Every Column Referenced in an RLS `USING` or `WITH CHECK` Clause
PostgreSQL does not automatically create indexes on foreign keys or RLS tenant columns.
```sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_user_id ON public.orders (user_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_orders_tenant_id ON public.orders (tenant_id);
```

### Rule 2.3: Avoid Correlated Subqueries in RLS Policies Without `SECURITY DEFINER` Helpers
When an RLS policy checks membership in a join table (`team_members`), use an indexed `IN (SELECT team_id FROM team_members WHERE user_id = (SELECT auth.uid()))` rather than a per-row correlated join.

---

## 3. Schema & Migration Safety Rules

1. **Foreign Keys Must Have Explicit Indexes**:
   - Without an index on the child table's FK column, `DELETE` or `UPDATE` on the parent table triggers a **full sequential scan** of the child table while holding locks.
2. **Partial Indexes for Hot Subsets**:
   - When 95% of rows are `ARCHIVED` or `COMPLETED` and active queries only filter `WHERE status = 'PENDING'` or `WHERE deleted_at IS NULL`, create a partial index:
   ```sql
   CREATE INDEX CONCURRENTLY idx_jobs_pending
   ON public.jobs (scheduled_at ASC)
   WHERE status = 'PENDING' AND deleted_at IS NULL;
   ```
3. **Zero-Downtime Column Addition & Constraints**:
   - Never add a column with a volatile default or validate a `FOREIGN KEY` / `CHECK` constraint with a full table lock during peak traffic. Add the constraint `NOT VALID` first, then run `VALIDATE CONSTRAINT` in a separate step (which only takes a `SHARE UPDATE EXCLUSIVE` lock allowing concurrent reads and writes).
