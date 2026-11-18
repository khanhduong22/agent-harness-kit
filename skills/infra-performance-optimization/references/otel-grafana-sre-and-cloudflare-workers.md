# OpenTelemetry Observability, SRE SLOs, Cloudflare Workers & Hardened Docker

> Distilled from `grafana/skills`, `cloudflare/skills`, and `docker/skills`. Covers end-to-end RED telemetry & burn-rate SLOs, Edge Workers / Durable Objects patterns, and production container safety guardrails.

---

## 1. OpenTelemetry & Grafana LGTM Observability (`grafana/skills`)

Unify metrics, logs, and traces through a single **Grafana Alloy / OTel Collector** pipeline instead of ad-hoc vendor agents:

### Semantic Instrumentation & RED Golden Signals
1. **Standard Resource Attributes**: Tag every service telemetry exporter with `service.name`, `service.version` (git SHA), `deployment.environment`, and `service.namespace`.
2. **Spanmetrics for Zero-Effort RED Metrics**: Generate Prometheus histograms (`traces_spanmetrics_calls_total`, `traces_spanmetrics_duration_bucket`) directly in the Collector/Alloy from OTel traces for **Rate**, **Errors**, and **Duration (`p50`/`p95`/`p99`)**, linking Prometheus **Exemplars** (`trace_id`) straight to Tempo traces and Loki JSON logs.
3. **USE Metrics for Backing Infra**: Track **Utilization**, **Saturation**, and **Errors** across Postgres connection pools, Redis memory fragmentation, CPU throttling (`container_cpu_cfs_throttled_periods_total`), and disk space (`node_filesystem_avail_bytes`).

### The Prometheus Cardinality Firewall
- **Hard Rule**: **NEVER** put high-cardinality or unbounded values (`user_id`, `email`, `request_id`, `order_id`, unnormalized `/users/12345` URL paths, or raw error strings) into Prometheus metric labels—unbounded label combinations cause time-series explosion and Prometheus/Mimir OOM crashes.
- Always normalize HTTP route labels via template (`/users/:id`), and keep high-cardinality IDs (`user_id`, `tenant_id`, `trace_id`) exclusively on **OTel Spans (Tempo)** and **Structured Logs (Loki)**.

### Multi-Window Burn-Rate SLO Alerting
Page on **user-facing SLO error budget burn**, not noisy transient CPU spikes:
- **Fast Burn Page (Critical)**: `14.4x` error-budget burn rate across both `1h` AND `5m` windows (exhausts 2% of monthly error budget within 1 hour).
- **Slow Burn Ticket (Warning)**: `6x` error-budget burn rate across `6h` AND `30m` windows.

---

## 2. Cloudflare Workers & Durable Objects Architecture (`cloudflare/skills`)

### Production Workers Standards
- **Keep Compatibility & Node Support Current**: Pin recent `compatibility_date` in `wrangler.jsonc` / `wrangler.toml` with `nodejs_compat` enabled; generate strict binding types via `wrangler types`.
- **Observability On by Default**: Enable `[observability] enabled = true` (plus structured JSON logs and traces) so edge exceptions never vanish silently.
- **Database Placement & Connection Reuse**: When a Worker talks to a regional PostgreSQL/MySQL database, enable **Smart Placement** (`placement: { mode: "smart" }`) and route queries through **Cloudflare Hyperdrive** (or edge-local D1) rather than opening cold TCP+TLS handshakes per request.
- **Stream Within the 128 MB Memory Ceiling**: Pass `response.body` streams directly (`return new Response(res.body, res)`) or compose with `TransformStream` for large payloads—calling `await res.text()` / `arrayBuffer()` on multi-MB downloads triggers isolate OOM crashes. Attach non-blocking post-response tasks explicitly via `ctx.waitUntil(...)` so promises never orphan silently.

### Durable Objects Rules (Stateful Edge Coordination)
- **Model One Durable Object Per Natural Unit of Coordination**: Create distinct DO instances via `idFromName(roomId)` / `tenantId` (chat room, collaborative doc, tenant rate-limiter, single user WebSocket session). **NEVER** route global application traffic into a single singleton DO (`idFromName("global")`), which serializes the entire app onto one thread.
- **Use SQLite Storage & WebSocket Hibernation**: Enable `new_sqlite_classes` in `wrangler` migrations for relational queries/ACID state inside DOs, use the **Hibernation API** (`ctx.acceptWebSocket(ws)`) to avoid idle billing, and schedule deferred retries with durable DO `storage.setAlarm(...)` (plus idempotent checks—remember storage gates allow external I/O interleaving unless carefully serialized).

---

## 3. Hardened Docker Builds & Destructive CLI Guardrails (`docker/skills`)

### Multi-Stage Dockerfile & Compose Hygiene
1. **Never Bake Secrets into Layers**: **NEVER** pass API keys, NPM tokens, or private certs via `ARG` or `ENV` (`docker history` leaks them permanently). Use BuildKit runtime secret mounts (`RUN --mount=type=secret,id=npmrc ...`) plus package cache mounts (`RUN --mount=type=cache,target=/root/.npm ...`) and strict `.dockerignore` files excluding `.git`, `.env*`, `node_modules`, and local artifacts.
2. **Pin & Drop Privileges**: Pin base image versions explicitly (tag + optional digest), combine multi-stage builds (`deps` -> `builder` -> `runner`), switch to an explicit non-root `USER node` / UID in the final stage, and configure `HEALTHCHECK` alongside Compose `depends_on: { db: { condition: service_healthy } }`.
3. **Isolate Internal Networks & Cap Logs**: Put Postgres/Redis/internal workers on `internal: true` Compose networks with explicit `logging.options.max-size: "10m"` & `max-file: "3"`.

### Mandatory Destructive Command Guardrails
Always state exact scope/data loss and require **explicit user confirmation** before executing any irreversible Docker cleanup in shared or production environments:
- **Blocked Without Explicit Approval**: `docker system prune -a --volumes`, `docker volume rm` / `docker volume prune`, `docker compose down -v` (destroys persistent DB volumes), `docker builder prune -a`, and running containers with `--privileged` or security-bypass flags.
- Prefer surgical single-resource targets (`docker container prune --filter "until=24h"`) over global `--all` wipes, and check `docker ps -a` / `docker volume ls` before removing stale state.
