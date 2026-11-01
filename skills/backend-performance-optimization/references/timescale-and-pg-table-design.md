# PostgreSQL Table Design & TimescaleDB Hypertable Scoring (`timescale/pg-aiguide`)

Synthesized from [`timescale/pg-aiguide`](https://github.com/timescale/pg-aiguide) (`design-postgres-tables` & `find-hypertable-candidates`). Load this reference when designing new PostgreSQL tables, choosing column types, tuning update-heavy/insert-heavy workloads, or evaluating tables for TimescaleDB hypertable conversion.

---

## 1. Canonical PostgreSQL Data Type Rules

| Domain | Mandatory Type (`✅ DO`) | Forbidden Type (`❌ DO NOT USE`) | Why |
|---|---|---|---|
| **Primary Keys (OLTP)** | `BIGINT GENERATED ALWAYS AS IDENTITY` | `SERIAL`, `BIGSERIAL`, `INT` | SQL-standard identity prevents manual sequence out-of-sync errors and 32-bit overflow |
| **Distributed / Opaque IDs** | `UUID` via `uuidv7()` (PG18+ / extension) or `gen_random_uuid()` | `VARCHAR(36)` | Native 16-byte binary storage + time-ordered B-tree locality with `uuidv7` |
| **Timestamps** | `TIMESTAMPTZ` (unbounded precision) | `TIMESTAMP` (without tz), `TIMESTAMPTZ(0)`, `TIMETZ` | Always store UTC-normalized instants; `TIMESTAMPTZ(0)` rounds `.999s` into the next second/day |
| **Strings** | `TEXT` (with `CHECK (LENGTH(col) <= n)` if bounded) | `CHAR(n)`, `VARCHAR(n)` | Identical storage engine in Postgres (`varlena`), avoids table metadata lock when changing length cap |
| **Money / Financial** | `NUMERIC(p, s)` or integer minor units (`BIGINT`) | `MONEY`, `REAL`, `DOUBLE PRECISION` | Prevents IEEE-754 rounding drift and locale-dependent `MONEY` formatting bugs |
| **Case-Insensitive Unique** | `TEXT` + `CREATE UNIQUE INDEX ON tbl (LOWER(email))` | Unindexed `ILIKE` | Enables B-tree index seeks on normalized strings |
| **Semi-Structured Data** | `JSONB` + `CHECK (jsonb_typeof(col) = 'object')` | `JSON` | Binary decomposition supports GIN indexing (`@>`, `?`) |

---

## 2. Critical PostgreSQL Storage & Constraint Gotchas

1. **`UNIQUE` Constraints and `NULL`s (`PG15+`)**:
   - Standard SQL allows multiple `(user_id, NULL)` rows inside a `UNIQUE (user_id, deleted_at)` index.
   - Use **`UNIQUE NULLS NOT DISTINCT (user_id, deleted_at)`** when `NULL` should be treated as a single deduplicated value.
2. **`CHECK` Constraints Use Three-Valued Logic**:
   - `CHECK (price > 0)` **passes when `price IS NULL`**. Always pair with `NOT NULL`: `price NUMERIC(12,2) NOT NULL CHECK (price > 0)`.
3. **Update-Heavy Tables & HOT Updates (`fillfactor = 90`)**:
   - PostgreSQL's MVCC writes a new tuple version on every `UPDATE`. If no indexed column is modified and free space exists on the same 8KB heap page, Postgres performs a **Heap-Only Tuple (HOT) update** (zero index maintenance!).
   - On high-churn status/counter tables:
     ```sql
     ALTER TABLE public.sessions SET (fillfactor = 90);
     ```
     Avoid putting unnecessary indexes on frequently mutated columns so HOT updates stay active.
4. **`JSONB` GIN Index Selection (`default` vs `jsonb_path_ops`)**:
   - `USING GIN (attrs)`: Supports both containment (`@>`) and key existence (`?`, `?|`, `?&`).
   - `USING GIN (attrs jsonb_path_ops)`: **30–50% smaller index size and faster writes**, supporting `@>` containment queries exclusively.
   - For frequent range/equality queries on a single JSONB field (`attrs->>'price'`), extract a `GENERATED ALWAYS AS ((attrs->>'price')::NUMERIC) STORED` column and index it with a standard B-tree.

---

## 3. TimescaleDB Hypertable Candidacy Scoring Matrix (`8+ Points = Convert`)

Before converting a PostgreSQL table to a TimescaleDB hypertable, score it across 3 axes:

| Criterion | Points | SQL / Schema Signal |
|---|---|---|
| **1. Has `TIMESTAMPTZ` time dimension** | **`+3`** | `created_at`, `recorded_at`, `bucket_time` |
| **2. Chronological append-mostly inserts** | **`+2`** | `n_tup_ins / GREATEST(n_live_tup, 1) > 0.85`, rare historical updates |
| **3. Queries consistently filter by time range** | **`+2`** | `WHERE created_at >= NOW() - INTERVAL '...'` |
| **4. Time-bucket aggregations / OHLCV rollups** | **`+2`** | `GROUP BY date_bin(...)` / `time_bucket(...)` |
| **5. Table scale (`>= 1M rows` or `>= 100MB`)** | **`+2`** | `pg_total_relation_size(relid) > 100 * 1024 * 1024` |
| **6. Segmentable entity key (`symbol`, `device_id`, `tenant_id`)** | **`+1`** | Ideal for `timescaledb.compress_segmentby` (`90%+` columnar compression) |

- **Score `>= 8`**: Strong hypertable candidate (`create_hypertable` + compression policy after hot window).
- **Score `< 5` (e.g. `users`, `organizations`, `settings`)**: Keep as standard OLTP B-tree heap table.
