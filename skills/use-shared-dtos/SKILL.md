---
name: use-shared-dtos
description: Prefer reusing shared DTOs (e.g. PaginationParamsDTO, SearchDTO from ~/shared/dtos/) over defining duplicate pagination or search query DTOs in domain modules.
---

# Prefer Shared DTOs (`~/shared/dtos/`)

## Overview
When designing or refactoring DTOs for query parameter handling, pagination, or keyword search across NestJS services (e.g. `src/community/dtos/`, `src/post/dtos/`), DO NOT redefine local duplicate fields for pagination (`page`, `perPage`, `sortBy`, `sortDirection`) or search (`keyword`, `q`).

Instead, always import and extend shared DTOs from `~/shared/dtos/` (such as `PaginationParamsDTO` or `SearchDTO`).

## Guidelines & Usage Patterns

### 1. Import & Extend Shared DTOs
- **`PaginationParamsDTO`**: From `~/shared/dtos/pagination-params.dto` for standard pagination (`page`, `perPage`, `sortBy`, `sortDirection`).
- **`SearchDTO`**: From `~/shared/dtos/search-request.dto` (extends `PaginationParamsDTO`) for pagination with keyword search (`keyword`) and keyset cursor (`cursor`).
- **DO NOT Re-declare `limit`, `q`, or `cursor`**: When extending `PaginationParamsDTO` or `SearchDTO`, DO NOT re-declare duplicate fields like `limit`, `q`, or `cursor` in the child DTO class. Use inherited `perPage`, `keyword`, and `cursor` directly.

### 2. Extend Shared DTOs for Feature Queries
When a feature domain query needs domain-specific fields (e.g. `groupId`, `symbol`, `status`), extend `PaginationParamsDTO` or `SearchDTO`:

```typescript
// src/community/dtos/post.dto.ts
import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsNumber, IsOptional, IsString } from 'class-validator';

import { SearchDTO } from '~/shared/dtos/search-request.dto';

export class QueryPostDto extends SearchDTO {
  @ApiPropertyOptional()
  @IsOptional()
  @IsNumber()
  groupId?: number;

  @ApiPropertyOptional()
  @IsOptional()
  @IsString()
  symbol?: string;
}
```

### 3. Benefits
- Eliminates duplicate DTO definitions across modules.
- Ensures consistent Swagger documentation, `@ApiPropertyOptional()` descriptions, and `class-validator` / `class-transformer` rules across all API endpoints.
- Simplifies pagination handling in repositories and services via `~/shared/Handlers/pagination`.
