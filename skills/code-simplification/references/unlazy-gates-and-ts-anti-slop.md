# Unlazy Completion Gates & TypeScript Anti-Slop Rules (`Leonxlnx/unlazy` + `dmmulroy/anti-slop`)

Synthesized from [`Leonxlnx/unlazy`](https://github.com/Leonxlnx/unlazy) (`★ 4.2k+`) and [`dmmulroy/anti-slop`](https://github.com/dmmulroy/anti-slop) (`★ 5.8k+`). Use this reference during multi-axis code review, autonomous `/goal` execution, and TypeScript/React refactoring.

---

## 1. The 4-Pass Unlazy Leaf Discipline (`Leonxlnx/unlazy`)

When executing or reviewing a non-trivial implementation task, never accept the first rough draft that compiles. Run **4 sequential passes** on every deliverable:

1. **Pass 1 — Complete Deliverable (Zero Placeholders)**:
   - Implement the full scope with zero `TODO`, `FIXME`, mock return stubs, or deferred edge cases.
2. **Pass 2 — Domain-Expert Upgrade (Replace the Cheap Version)**:
   - Re-read your own diff as a Staff Engineer in that specific domain (DB, Security, UI, Infra) and replace the naive/cheap implementation of each critical part (e.g., replacing sequential `await` in a loop with batched `Promise.all`, or replacing unindexed filter with a compound index).
3. **Pass 3 — Defect & Boundary Hunt**:
   - Actively hunt null/undefined boundaries, race conditions, IEEE-754 rounding issues, unclosed streams/timers, and cross-file contract mismatches.
4. **Pass 4 — Honest Gate Verification (`CHECK` + `EXPECT`)**:
   - Every completion claim must be backed by a runnable command oracle (`CHECK:`) whose exit code is `0` and whose stdout matches a specific expectation (`EXPECT:`).
   - **Negative Control Rule**: Ensure your test/check actually fails when the fix is reverted or broken — an oracle that always passes proves nothing.

---

## 2. TypeScript & React Anti-Slop Rules (`dmmulroy/anti-slop`)

Reject these 12 high-frequency LLM TypeScript/JavaScript code smells during code review and authoring:

| Rule ID | Slop Pattern (`❌ Reject`) | Production Standard (`✅ Enforce`) |
|---|---|---|
| **`no-accumulating-spread`** | `items.reduce((acc, x) => ({ ...acc, [x.id]: x }), {})` ($O(N^2)$ heap allocations!) | Mutate the fresh local accumulator (`acc[x.id] = x; return acc;`) or use `Object.fromEntries(items.map(...))` ($O(N)$) |
| **`no-reduce-accumulator-copy`** | `items.reduce((acc, x) => acc.concat(x.tags), [])` ($O(N^2)$ array copies) | Use `items.flatMap(x => x.tags)` or `acc.push(...x.tags)` on a local array |
| **`no-array-filter-map`** | Chaining `.filter(...).map(...)` over large hot arrays (allocates intermediate array) | Use a single `flatMap` pass, `for...of` loop, or lazy iterator `.values().filter(...).map(...).toArray()` |
| **`no-chained-type-assertions`** | `data as unknown as UserProfile` (double-cast type laundering) | Parse with a Zod schema (`UserProfileSchema.parse(data)`) or write a type guard |
| **`no-widen-then-assert`** | Widening a typed value to `any` / `Record<string, unknown>` only to cast it back | Preserve the narrow generic or discriminated union type through the call chain |
| **`require-safety-comment-for-type-assertion`** | Bare `as SomeType` without explanation | Every unavoidable `as` assertion must have an adjacent `// SAFETY: ...` comment explaining why the runtime invariant holds |
| **`no-conditional-empty-object-spread`** | `{ ...base, ...(cond ? { a: 1 } : {}) }` (allocates throwaway `{}` when false) | Assign conditionally or use `cond && { a: 1 }` only where clean |
| **`no-unsafe-dictionary-type`** | `Record<string, User>` where `dict[missingKey]` is typed as `User` instead of `User \| undefined` | Use `Map<string, User>` or `Record<string, User \| undefined>` (with `noUncheckedIndexedAccess`) |
| **`no-unknown-parameters` / `returns`** | Exporting public functions taking `unknown` or `any` when the callers pass a known domain type | Define explicit domain interfaces or discriminated unions at module boundaries |
| **`no-shape-in-symbol-names`** | Naming variables `userArray`, `configObject`, `idString`, `statusMap` | Name by domain plural/role: `users`, `config`, `userId`, `statusByUserId` |
| **`no-module-mocking`** | `vi.mock('./database')` mocking internal module seams across 15 tests | Inject narrow dependencies or test against real in-memory/test-container adapters |
| **`no-runtime-typeof` on trusted types** | Redundant `if (typeof id === 'string')` inside internal functions where `id: string` is already guaranteed by TypeScript | Validate once at the external trust boundary; trust static types inside the core domain |
