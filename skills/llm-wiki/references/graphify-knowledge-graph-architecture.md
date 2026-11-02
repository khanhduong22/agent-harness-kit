# Codebase & Corpus Knowledge Graph Architecture (`Graphify-Labs/graphify`)

Distilled from `Graphify-Labs/graphify` (`★ 140k+`, `ARCHITECTURE.md` & `graphify/skill.md`). Use when designing or operating persistent knowledge graphs and agent-compiled wikis over mixed corpora (source code, SQL schemas, architecture docs, ADRs, and papers).

---

## 1. When to Build/Query a Knowledge Graph vs Plain `grep`

| Scenario | Recommended Tool | Why |
|---|---|---|
| Single symbol lookup ("where is `X` defined", "what calls `Y`") in a known repo | `grep` / `Read` / `codebase-memory-mcp` | Zero indexing latency, deterministic exact match |
| Cross-artifact tracing (linking ADRs/docs/SQL schemas to code modules) | **Knowledge Graph + Wiki (`llm-wiki`)** | Surfaces semantic and structural edges invisible to lexical search |
| Architectural onboarding & refactor blast-radius analysis | **Graph Community Clustering & God-Node Analysis** | Identifies high-coupling hubs (`god_nodes`), import cycles, and cross-community bridges |

---

## 2. 7-Stage Hybrid AST + Semantic Graph Pipeline

Separate deterministic code parsing from model-assisted document extraction so code updates stay zero-token and instant:

```
detect(root) -> extract(paths) -> build(nx.Graph) -> cluster(communities) -> analyze() -> report.generate() -> export.to_wiki()
```

1. **`detect(root)`**: Classify corpus files into deterministic code/schema files vs semantic prose docs. Never decode raw binary media bytes just to count corpus words.
2. **`extract(paths)`**:
   - **Code & Schemas**: Parse deterministically via Tree-sitter AST (zero LLM tokens, 100% local).
   - **Prose Docs & Papers**: Run content-addressed semantic extraction cached by file SHA-256 (`check_semantic_cache`) so unchanged files are never re-extracted.
3. **`build()` & Epistemic Edge Tagging**:
   Every relationship edge in the knowledge graph must carry an explicit epistemic provenance tag:
   - `EXTRACTED`: Explicitly stated in the source AST, import statement, foreign key, or direct citation.
   - `INFERRED`: Derived via cross-document semantic resolution or call-chain transitivity.
   - `AMBIGUOUS`: Multiple candidate targets found; flagged for human or lint review.
4. **`cluster(G)`**: Partition the graph into cohesive domain communities without mutating raw nodes, generating one `llm-wiki` article per community plus a compact `index.md`.

---

## 3. High-Signal Structural Graph Analyses

Run four deterministic graph analyses whenever auditing system architecture or compiling `GRAPH_REPORT.md`:
- **`god_nodes(G)`**: Rank nodes by degree/betweenness centrality to expose overloaded modules and central bottlenecks.
- **`find_import_cycles(G)`**: Detect circular module dependencies before they break bundler tree-shaking or clean layering.
- **`surprising_connections(G)`**: Highlight high-weight edges crossing between otherwise distant communities (often hidden architectural coupling or undocumented side effects).
- **`graph_diff(G_old, G_new)`**: Compute added/removed nodes, new cross-community edges, and cohesion drift across PRs.
