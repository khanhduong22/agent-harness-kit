# Suspense Boundaries

Client hooks that cause CSR bailout without Suspense boundaries.

## useSearchParams

Always requires Suspense boundary in static routes. Without it, the entire page becomes client-side rendered.

```tsx
// Bad: Entire page becomes CSR
'use client'

import { useSearchParams } from 'next/navigation'

export default function SearchBar() {
  const searchParams = useSearchParams()
  return <div>Query: {searchParams.get('q')}</div>
}
```

```tsx
// Good: Wrap in Suspense
import { Suspense } from 'react'
import SearchBar from './search-bar'

export default function Page() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <SearchBar />
    </Suspense>
  )
}
```

## usePathname

Requires Suspense boundary when route has dynamic parameters.

```tsx
// In dynamic route [slug]
// Bad: No Suspense
'use client'
import { usePathname } from 'next/navigation'

export function Breadcrumb() {
  const pathname = usePathname()
  return <nav>{pathname}</nav>
}
```

```tsx
// Good: Wrap in Suspense
<Suspense fallback={<BreadcrumbSkeleton />}>
  <Breadcrumb />
</Suspense>
```

If you use `generateStaticParams`, Suspense is optional.

## Quick Reference

| Hook | Suspense Required |
|------|-------------------|
| `useSearchParams()` | Yes |
| `usePathname()` | Yes (dynamic routes) |
| `useParams()` | No |
| `useRouter()` | No |

## Performance Pitfall: React 19 Fizz `div[hidden]#S:0` Paint-Holding Trap

Wrapping already-awaited Server Component content in `<Suspense fallback={<Skeleton />}>` or calling `useSearchParams()` inside a top-level Client Component shell (e.g. `HomeTabs`) causes Next.js 15/16 to emit `<!--$?--><template id="B:0"></template>` and place the entire real SSR DOM inside `<div hidden id="S:0">` at the bottom of the HTML document.

React 19's Fizz runtime delays revealing `<div hidden id="S:0">` (`setTimeout($RV, 2300)`) until client chunks finish downloading, stalling Mobile LCP by 2.3+ seconds on Slow 4G.

```tsx
// Bad: Hides already-awaited SSR content inside <div hidden id="S:0">
export default async function Page() {
  const data = await getData()
  return (
    <Suspense fallback={<Skeleton />}>
      <HomeTabs>
        <Overview data={data} />
      </HomeTabs>
    </Suspense>
  )
}

// Good: Read searchParams in the Server Component and pass initialTab as a prop
export default async function Page(props: { searchParams?: Promise<{ tab?: string }> }) {
  const searchParams = await props.searchParams
  const initialTab = searchParams?.tab || 'overview'
  const data = await getData()
  return (
    <HomeTabs initialTab={initialTab}>
      <Overview data={data} />
    </HomeTabs>
  )
}
```

