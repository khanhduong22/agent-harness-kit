# Context Compression, Multi-Agent Memory & Vector Tuning Playbook

> Reference companion for `ai-agent-and-rag-engineering/SKILL.md`. Consolidates operational schemas and tuning rules from `muratcankoylan/Agent-Skills-for-Context-Engineering`, `qdrant/skills`, and `redis/agent-skills`.

---

## 1. Lossless Context Compaction & Probe Evaluation

Whenever a long-running coding or research session crosses ~70% context budget:

### Mandatory Summary Schema (Artifact Trail Preservation)
Never compress into loose prose paragraphs—require structured sections so resumed turns never re-read or break edited files:

```markdown
## Session Intent
- Exact user objective and non-negotiable acceptance criteria.

## Files Modified (Artifact Trail)
- `<path/to/file>` — exact symbol/function changed + why (never guess uninspected files).

## Decisions Made & Rejected Alternatives
- Chosen approach, tradeoffs accepted, and constraints discovered.

## Current State & Verification
- Last executed command/test + exact observed exit status/counts.

## Next Steps
- Ordered remaining atomic actions with exact target files.
```

### Evaluating Compaction Quality with Probes (Not ROUGE/Token Count)
Validate context compression pipelines using functional probe suites across held-out trajectories:
1. **Artifact-Trail Probe**: *"Which exact files and symbols did the agent modify before compaction?"*
2. **Constraint-Retention Probe**: *"Which invariants or banned approaches still govern the next step?"*
3. **Decision-Recall Probe**: *"Why was approach A rejected in favor of approach B?"*
4. **Continuation Probe**: Resume execution from only the compacted summary and assert passing task completion without re-discovering already-verified facts.

---

## 2. Multi-Agent Coordination Topologies & Telephone-Game Defense

Subagents exist to **isolate noisy context**, not to invent organizational hierarchy:

| Pattern | Topology | Best Fit | Failure Mode to Guard |
|---|---|---|---|
| **Supervisor / Worker** | 1 Orchestrator -> N File-Partitioned Workers | Parallel implementation, multi-angle PR audit, multi-service slices | **Telephone Game**: Orchestrator paraphrases worker outputs poorly. **Fix**: Pass artifact paths + exact tool outputs (`pass-through`), never prose summaries of code diffs |
| **Staged Pipeline** | Stage A -> Disk Contract -> Stage B -> Verify | Spec -> Implementation -> QA/E2E -> Release | **Premature Serialization**: Downstream guesses upstream schema. **Fix**: Write durable OpenSpec/JSON contracts to disk between stages |
| **Map-Reduce Swarm** | Fan-out independent shards -> Deterministic Aggregate | Scanning 50+ files, eval matrix runs, migration audits | **Runaway Token Fan-Out**: Unbounded nesting or duplicate searches. **Fix**: Enforce strict scope partition, `max_turns` cap, and schema-enforced worker JSON output |

---

## 3. Temporal Agent Memory Architecture

| Layer | Lifetime | Storage Engine | What Goes Here |
|---|---|---|---|
| **Working Context** | Single turn / active session | In-memory prompt + scratch disk files | Active task contract, recent tool results, open diff slices |
| **Episodic Memory** | Days to months | Postgres JSONB / Redis Streams + vector index | Timestamped debugging outcomes, user corrections, runbooks ("fix worked on commit X") |
| **Semantic Memory** | Durable / cross-session | Graph + Vector (`valid_from`, `valid_to`, `superseded_by`) | Architectural preferences, deployment topologies, entity facts |

- **Temporal Invalidation Law**: Never simply `DELETE` or blindly `APPEND` conflicting facts (creates **Context Clash**). Mark outdated facts with `valid_to = NOW()` / `superseded_by = new_fact_id` so retrieval filters `WHERE valid_to IS NULL` by default while preserving full auditability.

---

## 4. Vector Database & HNSW Quantization Reference (`qdrant/skills`)

### Quantization Trade-Off Matrix
| Mode | Memory Footprint | Typical Recall Loss | Required Query Config | Best Fit |
|---|---|---|---|---|
| **Unquantized (`float32`)** | `1x` (~6 KB / 1536d vector) | `0%` baseline | Default | Small collections (`< 250k` vectors) fitting comfortably in RAM |
| **Scalar (`int8`)** | **`~0.25x` (`4x` smaller)** | `< 1%` | Keep quantized vectors in RAM; original vectors on disk | Default production choice for medium-to-large RAG corpora |
| **Binary (`1-bit`)** | **`~0.03x` (`32x` smaller)** | Moderate without rescore | **`always_ram: true`** + **`oversampling: 2.0–3.0`** + **`rescore: true`** | Multi-million scale collections (`dim >= 768`, normalized embeddings) |
| **4-bit (`turbo4`)** | `~0.125x` (`8x` smaller disk) | Lossy originals | Validate recall on held-out queries before enabling | Disk-I/O bound deployments on Qdrant `v1.19+` |

### Production Checklist Before Shipping Vector RAG
- [ ] **Resident RAM Budget**: Confirm resident RSS stays `< 80%` of node memory; move original full-precision vectors to disk (`on_disk: true`) once quantized index fits in RAM.
- [ ] **Pre-Indexed Tenant Filters**: Create keyword payload index (`is_tenant: true`) *before* inserting production volume; verify zero unscoped queries omit `tenant_id`.
- [ ] **No Unnecessary Payload Retrieval**: Pass `with_vectors: false` on normal RAG queries; fetch only needed payload keys (`payload_selector`) to prevent network serialization stalls.
- [ ] **Semantic Cache Isolation**: Scope Redis/LangCache lookup keys by `(tenant_id, workload_type, embedding_model)` and bypass on mutating requests or time-sensitive prompts.
