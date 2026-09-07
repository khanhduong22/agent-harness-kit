---
name: use-base-repository
description: Mandate the use of inherited BaseRepository methods (this.create, this.update, this.delete, this.findUnique, this.findMany, this.findById, this.existById) over calling this.prismaService.<primaryEntity>.<operation> directly for operations on the repository's primary entity.
---

# Skill: Prefer BaseRepository Inherited Methods Over Direct Prisma Calls

## Purpose
Enforce clean architecture and repository abstraction consistency across all NestJS domain repositories in `index-api`. When a repository extends `BaseRepository<T, U>`, all CRUD operations on entity `T` MUST use `BaseRepository` inherited methods rather than calling `this.prismaService.<primaryEntity>` directly.

## Rules & Patterns

### 1. Primary Entity CRUD
When operating on the primary entity `T` managed by the repository:

- ❌ **Incorrect (Direct Prisma Call)**:
  ```typescript
  async incrementShareCount(postId: number) {
    const updated = await this.prismaService.communityPost.update({
      where: { id: postId },
      data: { sharesCount: { increment: 1 } },
    });
    return { sharesCount: updated.sharesCount };
  }
  ```

- ✅ **Correct (Using Inherited `this.update` / `this.create` / `this.delete`)**:
  ```typescript
  async incrementShareCount(postId: number) {
    const updated = await this.update(postId, {
      sharesCount: { increment: 1 },
    });
    return { sharesCount: updated.sharesCount };
  }
  ```

### 2. Supported `BaseRepository` Methods Matrix

| Operation | Standard Inherited Call | Overload / Usage |
| :--- | :--- | :--- |
| **Create** | `this.create(data)` | Accepts `data` object or `{ data: ... }` |
| **Update** | `this.update(id, data)` | Accepts `(id, data)` or full Prisma update args `{ where, data }` |
| **Delete** | `this.delete(id)` | Accepts `(id)` or full delete args `{ where: { id } }` |
| **Find One** | `this.findUnique({ where: { id } })` / `this.findById(id)` | Single record lookup by primary key |
| **Find Many** | `this.findMany({ where })` | Excludes soft-deleted records (`deletedAt: null`) |

### 3. Allowed Exceptions
Direct `this.prismaService` usage is ONLY allowed for:
1. **Multi-model Transactions**: `this.prismaService.$transaction(async (tx) => { ... })`
2. **Cross-table Relation Lookups**: Querying secondary models inside a transaction (e.g. `tx.communityPostBookmark.findUnique()`).
3. **Raw SQL Executions**: `this.prismaService.$executeRaw` / `$queryRaw`.
