# Pattern-to-Prod Reference: GonnaCrash Spec, `@kido/*` Suite Map & LimArt Wiring

> Companion reference for [`../SKILL.md`](../SKILL.md). Zero always-on context tax (`+0 tokens/turn`); load only when executing `/pattern-to-prod` or `/ship-pattern`.

---

## 1. GonnaCrash SQLite Fast-Path Queries (`~/profile/systemdesign-200lab/gonnacrash.db`)

Always query the compiled SQLite database (`< 1ms`) rather than reading raw JSON bundles.

### Verified Tables & Columns
- **`worlds`**: `campaign_key`, `world_order`, `folder_name`, `title_vi`, `title_en`, `level_count`
  - `1 = foundation` (20), `2 = high_load` (27), `3 = ai_apps` (27), `4 = agent_harness` (16), `5 = new_world` (53), `6 = hell_on_earth` (45)
- **`levels`**: `level_key`, `campaign_key`, `world_order`, `level_index`, `title_vi`, `title_en`, `budget_uc`, `budget_usd`, `best_cost_uc`, `best_cost_usd`, `tick_s`, `ticks`, `users_json`, `traffic_kinds_json`, `phases_json`, `palette_json`, `limits_json`, `scoring_json`, `concept_keys_json`, `cost_buckets_json`, `md_path`, `solution_md`
- **`fts_knowledge`**: FTS5 index over `(entity_type, entity_key, title, body_vi, body_en, concepts)`

### Fast Lookup Commands
```bash
# 1. Exact level SLA + best_cost_uc by level_key or world_order/level_index
sqlite3 ~/profile/systemdesign-200lab/gonnacrash.db \
  "SELECT world_order, level_index, level_key, title_en, budget_uc, best_cost_uc, scoring_json, traffic_kinds_json, concept_keys_json FROM levels WHERE level_key = 'cheap_model_first';"

# 2. Extract full 3-Star architecture solution markdown
sqlite3 ~/profile/systemdesign-200lab/gonnacrash.db \
  "SELECT solution_md FROM levels WHERE world_order = 3 AND level_index = 15;"

# 3. Full-text search across concepts & nodes
sqlite3 ~/profile/systemdesign-200lab/gonnacrash.db \
  "SELECT entity_type, entity_key, title FROM fts_knowledge WHERE fts_knowledge MATCH 'router OR cascade OR structured' LIMIT 15;"
```

### World 3 (`ai_apps`) Shipped Reference Patterns
| Level | `level_key` | Pattern Shipped | `@kido/ai-stream` Subpath | `best_cost_uc` (`budget_uc`) |
|---|---|---|---|---|
| L02 | `faster_answers` | SSE Streaming + Edge Anti-Buffering (`TTFT < 350ms`) | `.` (`sse-protocol`, `readable-stream-engine`) | `27,289` (`39,000`) |
| L03 | `rpm_ceiling` | Dual RPM/TPM Token Bucket + Full Jitter Backoff | `./rpm-rate-guard` | `540,275` (`630,000`) |
| L07 | `public_launch` | Multi-Provider Circuit Breaker, Hedging & Fallback Mesh | `./provider-fallback` | `356,759` (`420,000`) |
| L08 | `internal_docs_qa` | 3-Tier Hybrid RAG Cascade + Grounded Citations | `./rag-pipeline` | `941,357` (`1,090,000`) |
| L09 | `find_the_right_chunk` | Two-Stage Retrieval + Cross-Encoder Reranker | `./rag-pipeline` | `1,041,357` (`1,200,000`) |
| L10 | `fresh_docs_hourly` | Async Queue + Rate-Paced Worker + Micro-Batch Upsert | `./rag-pipeline` | `951,361` (`1,100,000`) |
| L12 | `bloated_tickets` | Multilingual Context Sanitizer & Email Chain Truncation | `./rag-pipeline` | `108,592` (`130,000`) |
| L13 | `budget_burning_chatbot` | 3-Layer EDoS Shield & Per-User Token Quota | `./quota-manager` | `27,266` (`32,000`) |
| L14 | `same_question_new_words` | Entity-Aware Strict Semantic Cache + Prompt Prefix Cache | `./semantic-cache` | `355,889` (`410,000`) |
| L15 | `cheap_model_first` | Complexity Classifier + FrugalGPT Model Router | `./model-router` | `659,856` (`760,000`) |

---

## 2. High-Star GitHub OSS Benchmark Extraction Table

Use these upstream benchmarks during Stage 1 to extract exact heuristics, failure modes, and data structures before writing zero-dependency TypeScript:

| Repository / Paper | Pattern Focus | Concrete Algorithms & Guardrails to Harvest |
|---|---|---|
| `BerriAI/litellm` | Multi-Provider AI Gateway | Provider cooldown states, EWMA latency routing, fallback order arrays, RPM/TPM header parsing |
| `Portkey-AI/gateway` | Resilient AI Proxy & Guardrails | Conditional routing rules, retry/backoff policies, semantic cache headers (`x-portkey-cache-status`), token accounting |
| `lm-sys/RouteLLM` | Cost-Saving Model Router | Calibrated router threshold `tau` on query difficulty score (`calibrateRouteThreshold`), matrix/embedding separation of easy vs hard prompts |
| `vllm-project/semantic-router` | Signal-Driven Model Routing | Dual heuristic + embedding classifier signals, per-tier model pool selection, fallback guardrails |
| `aurelio-labs/semantic-router` | Fast Utterance Intent Layer | Utterance centroid cosine similarity (`RouteLayer`), `< 15ms` deterministic intent classification before LLM calls |
| `stanford-futuredata/FrugalGPT` | LLM Cascade & Confidence Scoring | Sequential `small -> large` escalation triggered by deterministic answer confidence scorer (`evaluateAnswerConfidence`) |
| `qdrant/qdrant` | Vector Search & Isolation | `is_tenant: true` payload partitioning, Scalar (`int8`) / Binary quantization + `rescore: true`, pre-filter `must` clauses |
| `redis/redis` | Atomic Rate Limit, Cache & Streams | Atomic Lua scripts (`PEXPIRE`, `HINCRBY`, bounded ZSET caps), sliding-window counters, singleflight locks |
| `explodinggradients/ragas` | RAG & Agent Evals | Context precision/recall, faithfulness groundedness checks, structured regression metrics for CI release gates |
| `instructor-ai/instructor` / `dottxt-ai/outlines` | Structured JSON Outputs | Schema validation + bounded repair loop with exact validation error feedback (L16 `json_or_nothing`) |

---

## 3. `@kido/*` 39-Suite Mapping & Wiring Protocol (`~/Workspace/kido-packages`)

### Domain-to-Suite Routing (Zero Package #40 Fragmentation)
Map new slices into the existing 39 Domain Combo Suites in `packages/PACKAGES_REGISTRY.md`:

| Pattern Family | Target Package (`#`) | Example Slice Path (`src/<slice>/`) |
|---|---|---|
| AI streaming, SSE, RPM/TPM rate guard, fallback, RAG, reranking, ingestion pacing, sanitizer, EDoS quota, semantic cache, model routing, structured JSON, prompt-injection defense, evals | `@kido/ai-stream` (`#39`) | `packages/ai-stream/src/<slice>/` |
| L1/L2 SingleFlight SWR cache, sliding-window rate limiter, flash-sale Lua, proxy crawler, general RRF/vector cache | `@kido/resilient-cache` (`#5`) | `packages/resilient-cache/src/<slice>/` |
| Multi-tenant RLS, ABAC/RBAC, snapshot integrity, demo sandbox | `@kido/tenant-guard` (`#1`) | `packages/tenant-guard/src/<slice>/` |
| SimHash dedupe, anti-spam velocity, content refinery | `@kido/anti-spam` (`#3`) | `packages/anti-spam/src/<slice>/` |
| Postgres CDC/WAL, partition archiver, Litestream PITR, outbox | `@kido/async-sync` (`#7`) | `packages/async-sync/src/<slice>/` |
| MurmurHash sharding, consistent hash ring, compound partitions | `@kido/db-sharding` (`#12`) | `packages/db-sharding/src/<slice>/` |
| Write coalescing, Valkey write-behind, slotted counters, HLL | `@kido/hot-counter` (`#13`) | `packages/hot-counter/src/<slice>/` |
| K-way heap cursor merge, hybrid fanout, Valkey timeline mixer | `@kido/hybrid-feed` (`#38`) | `packages/hybrid-feed/src/<slice>/` |
| React AI Elements (`ChainOfThought`, `SourcesCitation`), sparklines, tour | `@kido/admin-ui` (`#16`) | `packages/admin-ui/src/components/<slice>/` |
| Double-entry ledger, crypto reconciliation, referral clawback, NAV | `@kido/wallet-ledger` (`#20`) | `packages/wallet-ledger/src/<slice>/` |

### Required Package Wiring Files
1. **Slice implementation (`packages/<combo>/src/<slice>/`)**:
   - Export barrel `src/<slice>/index.ts` with collision-safe symbol names (inspect `src/index.ts` and sibling slices first; prefix shared helpers like `Router...`, `SchemaGuard...` so `tsc` and `tsup` DTS report 0 duplicate export errors).
   - Export `simulateLevelXX<TitlePascal>(options?)` returning deterministic metrics (`answeredPct`, `ttftMs` / `latencyMs`, `accuracyPct`, `costPerTaskUc`, `passedSla`, `isThreeStarRecord`).
2. **`packages/<combo>/tsup.config.ts`**: Add `'<slice>': 'src/<slice>/index.ts'` under `entry`.
3. **`packages/<combo>/package.json`**: Add `"./<slice>"` in `exports`, update `description`, and append `test/<slice>.test.ts` to `scripts.test`.
4. **`packages/<combo>/src/index.ts`**: Add `export * from './<slice>/index.js';`.
5. **`packages/PACKAGES_REGISTRY.md`**: Update the matching combo suite row (`<br>• **\`src/<slice>/\`** (\`./<slice>\`): ...`) without adding a 40th package.
6. **`packages/cli/src/data/registry.json`**: Add a `slices` entry inside the target package object matching `@kido/cli`'s schema and bump `totalSlices` + `updatedAt`:
   ```json
   {
     "name": "<slice>",
     "path": "src/<slice>/",
     "type": "directory",
     "packageName": "@kido/<combo>",
     "packagePath": "packages/<combo>",
     "exports": ["SymbolOne", "SymbolTwo", "simulateLevelXX..."],
     "description": "src/<slice>/ (./<slice>)"
   }
   ```
7. **Docs & MDX**: Update `packages/<combo>/README.md`, `packages/<combo>/AGENTS.md` (if present), and `apps/docs/content/docs/packages/<pillar-dir>/<combo>.mdx` (e.g., `02-concurrency-and-caching/ai-stream.mdx`).
8. **OPSEC Zero-Leak Scan (Public Repo Mandatory Gate)**:
   ```bash
   cd ~/Workspace/kido-packages
   grep -riE "limart|hoaculimart|capy|vantoi|winter[- ]arc|linkpul|<CONTABO_VPS_IP>|<OVH_VPS_IP>" packages/<combo> packages/PACKAGES_REGISTRY.md packages/cli apps/docs
   git diff | grep -E "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" || true
   ```
   Verify every match is either absent (`0` lines for proprietary terms) or strictly benign documentation examples (e.g., RFC 5737 `203.0.113.x` or `127.0.0.1`).

---

## 4. LimArt Store Mode A Wiring Blueprint (`~/Workspace/limart`)

LimArt consumes `@kido/*` patterns via **Mode A Surgical Cherry-Pick** (copy/adapt cleanly into `apps/api/src/lib/` with zero `@kido/*` workspace imports and zero new npm dependencies).

### Exact Integration Surface Map
| Layer | File Path | Exact Responsibilities & Contracts |
|---|---|---|
| **Core Mode A Lib** | `apps/api/src/lib/<feature>.ts` | `< 350–400` lines; reuse `./cache` (`getRedisClient`), `./ip-utils` (`getClientIP`), `./auth` (`verifyAccessToken`), `./capy-rpm-rate-guard` (`rankCapyCandidatePools`, `executeWithCapyRateGuard`), `./capy-sse-stream` (`createCapySseStreamResponse`, `isSseStreamRequested`). Export `_reset*` test helpers. |
| **RAG / Search Orchestrator** | `apps/api/src/lib/store-rag-search.ts` (`askCapyArtAdvisor`) & `apps/api/src/lib/capy-rag-cache.ts` | Wire after semantic cache lookup / RRF retrieval and before or around Gemini generation. Preserve `searchMode: "hybrid-meili-vector-rrf"` and attach optional additive metadata fields (`cacheStatus`, `modelRouting`, etc.). |
| **LLM Fallback Pool** | `apps/api/src/routes/documents.route.ts` (`generateWithGeminiFallback`) | Keep existing 3-arg signature `(genAI, systemInstruction, prompt)` 100% backwards-compatible; add an optional 4th `options` param or dedicated tier-aware helper (`generateWithGeminiTieredPool`). |
| **Hono Store Route** | `apps/api/src/routes/store.route.ts` (`handleStoreAiAdvisor` for `POST` & `GET /ai-advisor`) | Preserve empty-query fast-path (`0` quota consumed); propagate `meta` in `createCapySseStreamResponse` and JSON payloads; emit `X-*` diagnostic headers on both JSON and SSE responses. |
| **CORS Expose/Allow** | `apps/api/src/app.ts` | Add custom request headers (`X-Capy-Session-Id`) to `allowHeaders` and custom response headers (`X-Quota-Blocked`, `X-Quota-Remaining-Requests`, `X-Quota-Remaining-Tokens`, `X-Semantic-Cache`, `X-AI-Model-Tier`, `X-AI-Model`, `X-AI-Escalated`, `Retry-After`) to `exposeHeaders`. |
| **Next.js API Proxy** | `apps/store-web/src/app/api/store/ai-advisor/route.ts` | Forward `cf-connecting-ip`, `x-forwarded-for`, `x-real-ip`, `x-capy-session-id`, `authorization`, `cookie`; forward `X-*` headers on `200` (SSE + JSON); short-circuit `413` or `429` (`x-quota-blocked === "1"`) without retry or `createFallbackSseResponse`. |
| **Storefront UI** | `apps/store-web/src/components/CapyArtAdvisorWidget.tsx` | Update `buildStoreTraceSteps(...)` and `buildStoreSources(...)` so `ChainOfThought` (`TraceLine`) and `SourcesCitation` display live backend trace (`meta` / `done` / JSON) with zero CLS. |
| **Admin SOP UI** | `apps/admin-spa/src/components/help/HelpChatTab.tsx` | Update `buildSopTraceSteps(...)` / `buildSopSources(...)` when pattern affects internal SOP RAG (`/api/documents/chat` or ingestion). |
| **API Integration Tests** | `apps/api/tests/<feature>.test.ts` | Reset state in `beforeEach`, isolate requests using RFC 5737 test IPs (`203.0.113.x`), verify JSON + SSE `meta`, `X-*` headers, and edge/fallback invariants. |

---

## 5. `/swarm` Disjoint Execution & Verification Playbook

When dispatching a multi-repo implementation swarm (`workspace: "inherit"`):

1. **Disjoint Ownership (Never Overlap Files or Repos)**:
   - **Author 1 (`kido-pkg-<topic>`)**: owns `~/Workspace/kido-packages` ONLY.
   - **Author 2 (`limart-<topic>`)** (or `limstore-<topic>`): owns `~/Workspace/limart` ONLY.
   - **Author 3 (`kit-<topic>` / `blog-<topic>`, optional)**: owns `~/Workspace/agent-harness-kit` or `~/kido-blog` ONLY.
   - **Verifier (`verifier`)**: **strictly read-only** across all touched repos; waits for `@verifier` mentions from all authors before posting consolidated pass report to `@coordinator`.
2. **Prohibited inside Worker Briefs**:
   - Never touch sibling repositories outside assigned repo.
   - Never run `git commit` or `git push`.
   - Never weaken assertions or leave failing `tsc --noEmit` errors in touched files.
3. **Exact Verification Commands**:
   ```bash
   # Repo 1: kido-packages
   cd ~/Workspace/kido-packages
   pnpm --filter @kido/<combo> typecheck && pnpm --filter @kido/<combo> build && pnpm --filter @kido/<combo> test
   pnpm --filter @kido/cli build && pnpm --filter @kido/cli test
   pnpm --filter docs build

   # Repo 2: limart
   cd ~/Workspace/limart/apps/api && bun test tests/<feature>.test.ts <related-tests>
   cd ~/Workspace/limart/apps/api && bun x tsc --noEmit   # verify 0 errors in touched files
   cd ~/Workspace/limart/apps/store-web && bun x tsc --noEmit

   # Repo 3: agent-harness-kit (when skills/rules updated)
   cd ~/Workspace/agent-harness-kit
   ./scripts/verify.sh && bash tests/test_harness.sh
   ./scripts/install.sh --targets all
   python3 ~/Workspace/agent-harness-kit/skills/skill-doctor/scripts/skill_doctor.py
   ```
