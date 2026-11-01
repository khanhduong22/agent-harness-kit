# Deep Modules, Deletion Test & Domain Modeling (`mattpocock/skills`)

Synthesized from [`mattpocock/skills`](https://github.com/mattpocock/skills) (`★ 308k+` — `improve-codebase-architecture` & `domain-modeling`) and John Ousterhout's *A Philosophy of Software Design*. Use this reference when decomposing God-files, designing module boundaries, or deciding whether a decision warrants an ADR.

---

## 1. Deep Modules vs Shallow Pass-Through Layers

Software complexity grows when a small conceptual change requires editing 6 files across 4 layers ("change amplification"). The cure is **Deep Modules**:

```text
┌─────────────────────────────────────┐      ┌─────────────────────────────────────┐
│   Shallow Module (Pass-Through)     │      │           Deep Module               │
│ ═══════════════════════════════════ │      │ ═══════════════════════════════════ │
│   Wide, complex public interface    │      │     Narrow, simple interface        │
├─────────────────────────────────────┤      ├─────────────────────────────────────┤
│   Thin 5-line pass-through body     │      │                                     │
└─────────────────────────────────────┘      │     Rich internal implementation    │
  ✗ High cognitive load, zero hiding         │     (hides concurrency, retries,    │
                                             │      serialization, caching, SQL)   │
                                             │                                     │
                                             └─────────────────────────────────────┘
                                               ✓ Maximum leverage, high locality
```

### Core Architectural Vocabulary
- **`Module`**: Any unit with an interface and an implementation (a function, class, repository slice, or package).
- **`Depth`**: The ratio of hidden internal complexity (implementation) to exposed surface area (interface).
- **`Locality`**: How much a developer can understand and safely modify inside a single module without jumping across the repo.
- **`Seam`**: A boundary where two modules meet cleanly via types/contracts and can be tested or swapped independently.
- **`Adapter`**: A thin boundary layer that isolates unstable external schemas (third-party webhooks, raw LLM responses, legacy APIs) from core domain types.
- **`Leverage`**: How many call sites become simpler because a single deep module absorbed a recurring policy (e.g., `singleflight.execute(key, fn)`).

---

## 2. The Deletion Test (Evaluating Module Boundaries)

Before creating a new abstraction, service class, or sub-module, apply **The Deletion Test**:

> *"If requirements change tomorrow and we delete this feature/policy, do we delete **one cohesive module**, or do we have to perform surgery across 12 scattered files?"*

### Signals of Shallow / Leaky Module Boundaries (Refactor Immediately)
1. **Pass-Through Methods**: `Controller.getUser(id)` $\to$ `UserService.getUser(id)` $\to$ `UserManager.getUser(id)` $\to$ `UserRepo.getUser(id)` where intermediate layers add zero validation, authorization, or domain logic.
2. **Temporal Coupling**: Callers must remember to call `init()`, then `validate()`, then `commit()` in a magic order or state corrupts. Combine them into a single atomic entry point.
3. **Configuration Leakage**: Passing raw `process.env` or framework `Request` objects deep into domain calculators instead of narrow typed value objects.
4. **God-File Gravity (`> 400 lines`)**: One file owns types, DB queries, caching, HTTP formatting, and cron scheduling. Slice by **cohesive domain capability** (`ohlc.repo.ts`, `fx-gold.repo.ts`, `banking.repo.ts`), keeping each slice `< 250–400 lines` behind a clean barrel.

---

## 3. Active Domain Modeling & `GLOSSARY.md` Discipline

Every non-trivial codebase develops ubiquitous domain nouns (`Period`, `Checkin`, `Tenant`, `Singleflight`, `Candle`, `Position`).

1. **One Noun, One Meaning**: Never call the same domain entity `Workspace` in the UI, `Organization` in the API, and `Team` in the database schema unless an explicit adapter maps them.
2. **Sharpen Types to Make Illegal States Unrepresentable**:
   ```typescript
   // ❌ Weak primitive obsession: allows invalid combinations (status='PAID' with paidAt=null)
   interface Invoice {
     status: string;
     paidAt?: Date;
     failureReason?: string;
   }

   // ✅ Deep domain sum type (discriminated union): compiler enforces invariants
   type InvoiceState =
     | { status: 'PENDING' }
     | { status: 'PAID'; paidAt: Date; transactionRef: string }
     | { status: 'FAILED'; failedAt: Date; failureReason: string };
   ```
3. **Update `GLOSSARY.md` When Domain Terms Shift**: If a refactor introduces or sharpens a core domain concept, record its 1-sentence definition and invariants in the project's `GLOSSARY.md` or `AGENTS.md`.

---

## 4. The 3-Condition Gate for Architectural Decision Records (ADRs)

Do not write ceremonial ADRs for trivial implementation details. Record an ADR **only when all 3 conditions hold**:

1. **Hard to Reverse**: Changing course later requires a data migration, public contract change, or multi-file rewrite.
2. **Surprising Without Context**: A future engineer reading the code would ask *"Why didn't they just use a normal `SELECT` / standard library call here?"*
3. **Real Trade-Off**: At least two viable options existed with competing costs (e.g., latency vs consistency, memory footprint vs CPU spike).
