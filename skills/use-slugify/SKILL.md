---
name: use-slugify
description: Mandate the use of centralized slugify utility (slugify.util.ts) wrapping npm slugify package with Vietnamese locale support instead of writing ad-hoc inline regexes or manual toLowerCase replacements for URL/entity slugs.
---

# Use Centralized Slugify Utility

## Overview
When generating URL slugs or entity slugs for posts, groups, tags, categories, or articles in this repository, NEVER write custom inline string replacement logic like `.toLowerCase().replace(/[^a-z0-9]+/g, '-')`.

Always use the centralized `slugify` utility wrapper located at `~/shared/utils/slugify.util`.

## Guidelines & Usage Patterns

### 1. Standard Import
```typescript
import { slugify } from '~/shared/utils/slugify.util';
```

### 2. Generating Entity Slugs with Unique Random Suffix
When generating unique slugs for posts, groups, or articles:
```typescript
const slug = slugify(dto.title, {
  fallback: 'post',
  withRandomSuffix: true,
});
// Output: "bai-viet-moi-1234"
```

### 3. Vietnamese Diacritics Support
The underlying `slugify` npm package is configured with `locale: 'vi'` to automatically map:
- `đ` / `Đ` $\rightarrow$ `d`
- Accent vowels (`à, á, ả, ã, ạ, ê, ế, ố, ...`) $\rightarrow$ unaccented equivalents (`a, e, o, ...`)
- Punctuation & special symbols $\rightarrow$ stripped cleanly
