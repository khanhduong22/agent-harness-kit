# Durable Workflows, Distributed Sagas & High-Concurrency Review

> Distilled from `temporalio/skill-temporal-developer` and `alibaba/open-code-review`. Apply whenever designing multi-step payment/provisioning flows, background queues that must survive worker crashes, or auditing high-concurrency backend diffs.

---

## 1. Temporal Durable Execution & Replay Determinism

Temporal restores interrupted or long-running workflows by **replaying Workflow code from its recorded Event History**, matching generated Commands 1:1 against past Events without re-executing Activities:

### Hard Determinism Invariants (Inside Workflow Definitions)
| Forbidden in Workflow Code | Why It Causes `NondeterminismError` | Deterministic Replacement |
|---|---|---|
| `Date.now()` / `new Date()` | Replay runs later in wall-clock time and branches differently | Use SDK workflow clock (`workflowInfo()` / `workflow.now()`) |
| `Math.random()` / `crypto.randomUUID()` | Generates different IDs on replay vs initial run | Use SDK deterministic RNG / `uuid4()` (`sideEffect` / Activity) |
| Direct DB queries, `fetch()`, `fs.*` | Live network/disk state drifts between run and replay | Push **100% of external I/O** into idempotent **Activities** |
| Unordered `Map`/Object iteration where order triggers Commands | Language/runtime hash-order drift changes Command sequence | Sort keys explicitly before looping over Activity schedules |
| Long blocking `sleep` in process memory | Dies on pod restart | Use durable SDK `sleep(duration)` timers |

### Activities: Idempotency, Timeouts & Heartbeats
- **Idempotency Keys Mandatory**: Even Local Activities retry across worker crashes. Derive a deterministic key (`${workflowId}:${activityId}`) and pass it to every payment, ledger, webhook, or email provider.
- **Always Set `startToCloseTimeout`**: Never schedule an Activity without an explicit execution timeout (`scheduleToStartTimeout` alone does NOT detect hung workers).
- **Checkpoint Long Jobs with Heartbeats**: For multi-minute ETL, video transcoding, or batch indexing Activities, set `heartbeatTimeout` (e.g., `30s`) and call `heartbeat(cursor)` every batch—on worker eviction, the retried worker resumes cleanly from `activityInfo().heartbeatDetails`.
- **Fail Fast on Business Errors**: Classify permanent validation/4xx/auth errors under `nonRetryableErrorTypes` so corrupted inputs don't burn retry queues until `scheduleToCloseTimeout`.

---

## 2. Distributed Saga Compensation & Safe Evolution

### Forward-Failure Saga Pattern
When orchestrating multi-service mutations without distributed 2PC (`ReserveInventory` $\to$ `ChargePayment` $\to$ `ProvisionTenant`):

```ts
const compensations: Array<() => Promise<void>> = [];
try {
  await reserveInventory(orderId);
  compensations.push(() => releaseInventory(orderId)); // Register BEFORE next step!

  await chargeCustomer(orderId, idempotencyKey);
  compensations.push(() => refundCustomer(orderId, `${idempotencyKey}:refund`));

  await provisionWorkspace(orderId);
} catch (err) {
  // Run compensations in reverse (LIFO) order inside non-cancellable scope; log partial failures
  for (const compensate of compensations.reverse()) {
    await compensate();
  }
  throw err;
}
```
- Make every compensation Activity **idempotent and backward-tolerant** (safe even if the forward Activity partially succeeded or never committed).

### History Limits & Safe Zero-Downtime Versioning
- **Never Edit Active Workflow Control Flow Blindly**: Guard step additions or ordering changes behind SDK `patched("v2-add-fraud-check")` gates (or Worker Versioning deployments) until all pre-patch workflows finish; only remove old branches once zero open executions remain.
- **Prevent Unbounded Event Histories (`Continue-As-New`)**: Workflows processing endless loops/webhooks must call `continueAsNew(...)` cleanly every `~1,000–2,500` iterations (well before the `50k` event / `50MB` history ceiling).

---

## 3. High-Concurrency Backend PR Review Checklist (`alibaba/open-code-review`)

Audit every critical backend concurrency, billing, or state-transition diff against these 6 invariants:

1. **Atomicity & Lock Ordering**: Multi-row updates acquire row locks in a consistent canonical order (`ORDER BY id ASC`) to prevent deadlocks; check-then-act paths use conditional `UPDATE ... WHERE version = $v` or atomic `INSERT ... ON CONFLICT`.
2. **Cache-Database Write Race**: Mutating DB paths write inside transactions first and invalidate caches **after** `COMMIT` (or use delayed double-delete/versioned keys) so concurrent readers never backfill stale pre-commit rows.
3. **Bounded Parallelism & Backpressure**: Replace unbounded `Promise.all(items.map(...))` or unbounded goroutines/threads over user-controlled arrays with bounded concurrency pools (`p-limit`, semaphores) and `AbortSignal.timeout`.
4. **Partial Batch Failure Semantics**: Explicitly classify whether batch loops are all-or-nothing transactional vs per-item idempotent with dead-letter reporting (`Promise.allSettled` + persisted error status)—never silently swallow failed items inside `catch {}`.
5. **Payload & Memory Ceilings**: Paginate list queries (`cursor` + `LIMIT` cap) and stream file/export payloads instead of loading unbounded ORM relations into heap memory.
6. **Clean Retry & Outbox Coupling**: External webhooks, queues, and search-index syncs use a transactional outbox or post-commit relay rather than firing unrecoverable network calls mid-transaction.
