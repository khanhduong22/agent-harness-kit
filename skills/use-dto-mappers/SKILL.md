---
name: use-dto-mappers
description: Isolate complex entity-to-DTO data mapping into dedicated *.mapper.ts files using pure export functions instead of bloating NestJS Service classes with long private mapping methods.
---

# Use DTO Data Mappers (*.mapper.ts)

## Overview
When transforming raw database entities (Prisma, TypeORM, or SQL queries) into API DTO response objects (`PostResponseDto`, `GroupResponseDto`, `CryptoDetailDto`), DO NOT write private 50+ line `mapToResponseDto()` helper methods inside Service classes.

Instead, extract the transformation logic into a dedicated **Mapper Utility** file at `src/<domain>/mappers/<domain>.mapper.ts`.

## Guidelines & Usage Patterns

### 1. Pure Function Definition Pattern
Always export pure functions from `<domain>.mapper.ts`:

```typescript
// src/post/mappers/post.mapper.ts
import { PostResponseDto } from '../dtos/post-response.dto';

export function mapPostToResponseDto(post: Record<string, unknown>): PostResponseDto {
  return {
    id: String(post.id),
    title: (post.title as string) || undefined,
    content: post.content as string,
    // ... complete mapping logic ...
  };
}
```

### 2. Service Integration Pattern
Import and call the mapper function cleanly inside your NestJS service:

```typescript
// src/post/services/post.service.ts
import { mapPostToResponseDto } from '../mappers/post.mapper';

@Injectable()
export class PostService {
  async getPostByIdOrSlug(idOrSlug: string): Promise<PostResponseDto> {
    const post = await this.postRepository.findOneByIdOrSlug(idOrSlug);
    if (!post) throw new NotFoundException(...);
    return mapPostToResponseDto(post);
  }
}
```

### 3. Co-located Unit Testing (`*.mapper.spec.ts`)
Write pure, fast unit tests covering all data mapping edge cases:

```typescript
// src/post/mappers/post.mapper.spec.ts
import { mapPostToResponseDto } from './post.mapper';

describe('post.mapper', () => {
  it('should map raw post record to PostResponseDto', () => {
    const dto = mapPostToResponseDto(mockRawPost);
    expect(dto.id).toBe('101');
  });
});
```
