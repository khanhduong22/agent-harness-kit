# Top-100 & Official Vendor BE / Infra / AI Skill Catalog (2026-11-18 Audit)

> Curated from live GitHub Star-Band Sharding (`--limit 120`) plus 21 official engineering vendor organizations (`cloudflare`, `ClickHouse`, `redis`, `planetscale`, `temporalio`, `docker`, `grafana`, `qdrant`, `openai`, `google`, `google-gemini`, `hashicorp`, `huggingface`). Consult this backlog before searching GitHub from scratch.

---

## 1. Audit Summary & Portfolio Rebalance Baseline

- **Problem Diagnosed (2026-11-18)**: Always-on frontmatter token audit showed `Design / UI` consuming `~30%` of context budget (`14` skills / `993 tokens`) — driven by top-level UI wrappers (`shadcn`, `stitch-prompt-engineering`), while Staff **Backend**, **Infrastructure/SRE**, and **AI Engineering** had deep `references/` but lacked ClickHouse OLAP, Temporal Sagas, Redis Cluster/Semantic Cache, Qdrant Hybrid RAG, OpenTelemetry/Grafana SLOs, and Context Engineering.
- **Resolution Executed (Phase 1)**:
  - Folded narrow UI wrappers (`shadcn`, `stitch-prompt-engineering`) into [`frontend-ui-engineering/references/`](../../frontend-ui-engineering/SKILL.md) (`-181 tokens/turn`).
  - Added 1 net-new AI runtime skill [`ai-agent-and-rag-engineering`](../../ai-agent-and-rag-engineering/SKILL.md) (`+~82 tokens/turn`).
  - Deepened BE (`backend-performance-optimization/references/`) and Infra (`infra-performance-optimization/references/`) with `+0 tokens/turn` progressive disclosure.
  - Net result: **`~100 tokens/turn` lower always-on tax** while covering all Staff BE / Infra / AI domains.

---

## 2. AI Engineering & Context / RAG Repositories

| Repository | Stars | License | 8-Point Gate Status | High-Signal Skills / Modules | Status & Target |
|---|---:|---|---|---|---|
| `muratcankoylan/Agent-Skills-for-Context-Engineering` | `★ 18.4k` | `MIT` | **PASS (✓)** | `context-compression`, `context-degradation`, `tool-design`, `memory-systems`, `multi-agent-patterns`, `advanced-evaluation` | **ABSORBED ✓** $\to$ `ai-agent-and-rag-engineering` |
| `qdrant/skills` | `★ 270+` | `Apache-2.0` | **PASS (✓)** (`3` minor stubs skipped) | `qdrant-multitenancy`, `qdrant-performance-optimization` (`search-speed`, `memory-usage`), quantization & segment tuning | **ABSORBED ✓** $\to$ `ai-agent-and-rag-engineering` |
| `redis/agent-skills` | `★ 177+` | `MIT` | **PASS (✓)** | `redis-semantic-cache` (LangCache), `add-intent-router`, `add-context-gateway`, `add-agent-memory`, `redis-clustering`, `redis-connections` | **ABSORBED ✓** $\to$ `ai-agent-and-rag-engineering` + `backend-performance-optimization/references/` |
| `openai/skills` | `★ 28.8k` | Unlisted / Custom | **PASS (✓)** | `.curated/security-threat-model`, `gh-fix-ci`, `gh-address-comments`, `sentry`, `openai-docs` | **WATCHLIST (Phase 2)** $\to$ `security-and-hardening/references/`, `ai-agent-and-rag-engineering/references/` |
| `google/skills` | `★ 24.4k` | `Apache-2.0` | **PASS (✓)** | `gcloud`, `google-cloud-recipe-auth`, GCP/ADK developer skills (`213` skills) | **WATCHLIST (Phase 2)** $\to$ `infra-performance-optimization/references/` |
| `google-gemini/gemini-skills` | `★ 4.5k` | `Apache-2.0` | Check before merge | Official Gemini API / structured output / Live API SDK patterns | **WATCHLIST (Phase 2)** $\to$ `ai-agent-and-rag-engineering/references/` |
| `huggingface/skills` | `★ 11.4k` | `Apache-2.0` | Check before merge | HF Hub model workflows, fine-tuning & inference tooling | **WATCHLIST (Phase 3)** (if training/hosting open-weight models) |
| `wanshuiyin/Auto-claude-code-research-in-sleep` (`ARIS`) | `★ 19.4k` | `MIT` | Check before merge | Autonomous ML experiment iteration loops | **WATCHLIST (Phase 3)** (research workflows only) |

---

## 3. Backend, Databases & Distributed Systems Repositories

| Repository | Stars | License | 8-Point Gate Status | High-Signal Skills / Modules | Status & Target |
|---|---:|---|---|---|---|
| `ClickHouse/agent-skills` | `★ 572+` | `Apache-2.0` | **PASS (✓)** | `clickhouse-best-practices` (`36` schema/query/insert rules), `clickhouse-architecture-advisor`, `clickhouse-managed-postgres-rca` | **ABSORBED ✓** $\to$ `backend-performance-optimization/references/clickhouse-olap-and-redis-cluster.md` |
| `planetscale/database-skills` | `★ 743+` | `MIT` | **PASS (✓)** | `postgres`, `mysql`, `vitess` (horizontal sharding, online DDL, replication lag, locking gotchas) | **ABSORBED ✓** $\to$ `backend-performance-optimization/references/clickhouse-olap-and-redis-cluster.md` |
| `temporalio/skill-temporal-developer` | `★ 239+` | `MIT` | **PASS (✓)** | History replay determinism, `startToClose` + heartbeat checkpoints, LIFO Sagas, `patched` versioning, `continueAsNew` | **ABSORBED ✓** $\to$ `backend-performance-optimization/references/temporal-durable-workflows-and-sagas.md` |
| `alibaba/open-code-review` | `★ 54.0k` | `Apache-2.0` | **PASS (✓)** | `open-code-review`, `open-code-review-delegate`, enterprise concurrency & PR blast-radius checks | **ABSORBED ✓** $\to$ `backend-performance-optimization/references/temporal-durable-workflows-and-sagas.md` |
| `pydantic/skills` | `★ 155+` | `MIT` | Check before merge | Typed agent validation & structured Pydantic AI patterns (Python) | **WATCHLIST (Phase 2)** $\to$ `ai-agent-and-rag-engineering/references/` |

---

## 4. Infrastructure, Cloud, SRE & Code Quality Repositories

| Repository | Stars | License | 8-Point Gate Status & Sanitization Notes | High-Signal Skills / Modules | Status & Target |
|---|---|---|---|---|---|
| `cloudflare/skills` | `★ 3.4k` | `Apache-2.0` | **PASS (✓)** | `workers-best-practices` (Smart Placement, Hyperdrive, `128MB` streaming), `durable-objects` (sharded DOs, SQLite storage, hibernation) | **ABSORBED ✓** $\to$ `infra-performance-optimization/references/otel-grafana-sre-and-cloudflare-workers.md` |
| `grafana/skills` | `★ 313+` | `Apache-2.0` | **PASS (✓)** | `app-observability` (Alloy OTLP, `traces_spanmetrics_*` RED metrics, Exemplars -> Tempo/Loki, burn-rate SLOs, adaptive cardinality) | **ABSORBED ✓** $\to$ `infra-performance-optimization/references/otel-grafana-sre-and-cloudflare-workers.md` |
| `docker/skills` | `★ 640+` | `Apache-2.0` | **PASS with Sanitization**: Scanner caught sandbox permission-bypass flags (`MEDIUM`) in `docker-agent-run` and local AWS credential path mention (`MEDIUM`) in `docker-build-strategies` — **both stripped** | `docker-build-strategies` (`--mount=type=secret`, non-root, `.dockerignore`), `docker-compose-patterns`, `docker-destructive-guardrails` | **ABSORBED ✓** $\to$ `infra-performance-optimization/references/otel-grafana-sre-and-cloudflare-workers.md` |
| `hashicorp/agent-skills` | `★ 931+` | `MPL-2.0` | **PASS with Note**: local AWS credential path reference flagged (`MEDIUM`) in `packer/aws-ami-builder` | Terraform modules, provider configuration, Packer image pipelines | **WATCHLIST (Phase 2)** $\to$ `infra-performance-optimization/references/terraform-opentofu-iac-guardrails.md` |
| `google/elephant-goldfish-model` | `★ 20.9k` | `Apache-2.0` | **PASS (✓)** | `egm-bootstrap`, `egm-brainstorm`, `egm-drift-report` (architecture-vs-code drift auditing) | **WATCHLIST (Phase 2)** $\to$ `code-simplification/references/` |
| `NVIDIA/SkillSpector` | `★ 26.7k` | `Apache-2.0` | Static skill scanner | Security scanning inspiration for `harvest_github_skills.py` | **WATCHLIST (Phase 2)** $\to$ `skill-harvester/scripts/` |

---

## 5. Already Absorbed Tier-1 Foundations (Reference Check)

Already integrated prior to 2026-11-18 (do NOT re-harvest): `anthropics/skills`, `mattpocock/skills`, `addyosmani/agent-skills`, `cloudflare/security-audit-skill`, `trailofbits/skills`, `supabase/agent-skills`, `timescale/pg-aiguide`, `antonbabenko/terraform-skill`, `affaan-m/ECC`, `paperclipai/paperclip`, `dmmulroy/anti-slop`, `leonxlnx/unlazy`, `GoogleChrome/modern-web-guidance`, `emilkowalski/skills`.
