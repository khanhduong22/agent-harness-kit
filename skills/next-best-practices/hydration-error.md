# Hydration Errors

Diagnose and fix React hydration mismatch errors.

## Error Signs

- "Hydration failed because the initial UI does not match"
- "Text content does not match server-rendered HTML"

## Debugging

In development, click the hydration error to see the server/client diff.

## Common Causes and Fixes

### Browser-only APIs

```tsx
// Bad: Causes mismatch - window doesn't exist on server
<div>{window.innerWidth}</div>

// Good: Use client component with mounted check
'use client'
import { useState, useEffect } from 'react'

export function ClientOnly({ children }: { children: React.ReactNode }) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])
  return mounted ? children : null
}
```

### Date/Time Rendering

Server and client may be in different timezones:

```tsx
// Bad: Causes mismatch
<span>{new Date().toLocaleString()}</span>

// Good: Render on client only
'use client'
const [time, setTime] = useState<string>()
useEffect(() => setTime(new Date().toLocaleString()), [])
```

### Random Values or IDs

```tsx
// Bad: Random values differ between server and client
<div id={Math.random().toString()}>

// Good: Use useId hook
import { useId } from 'react'

function Input() {
  const id = useId()
  return <input id={id} />
}
```

### Invalid HTML Nesting

```tsx
// Bad: Invalid - div inside p
<p><div>Content</div></p>

// Bad: Invalid - p inside p
<p><p>Nested</p></p>

// Good: Valid nesting
<div><p>Content</p></div>
```

### Third-party Scripts

Scripts that modify DOM during hydration.

```tsx
// Good: Use next/script with afterInteractive
import Script from 'next/script'

export default function Page() {
  return (
    <Script
      src="https://example.com/script.js"
      strategy="afterInteractive"
    />
  )
}
```

### Undeclared Destructured Props (Runtime ReferenceError Hydration Crash)

When a component references `{children}` or other props in JSX expressions without declaring them in the function parameter signature:

```tsx
// ❌ Bad: 'children' is referenced in JSX but omitted from props destructuring!
// In development it may fall through, but in production SSR/hydration it throws
// "ReferenceError: children is not defined" and crashes the entire React root tree.
function HomeTabs({ usdtData, selectedAsset, onSelectAsset }) {
  return <div>{children || <DefaultView />}</div>;
}

// ✅ Good: Always declare and destructure all referenced props
function HomeTabs({ children, usdtData, selectedAsset, onSelectAsset }: HomeTabsProps) {
  return <div>{children || <DefaultView />}</div>;
}
```

### Production Hydration Crash Diagnostics (Server Error Digests)

In production Next.js builds, hydration errors and uncaught component exceptions are scrubbed of raw stack traces for security. The client displays a generic error or browser fallback page, and renders an error digest:

1. **Client / Chrome Symptom**: PageSpeed filmstrip or browser screen shows *"This page couldn't load. Reload to try again, or go back."* with a digest like `digest: '2240224694'`.
2. **Find the root cause on the server**:
   ```bash
   # Check container/server logs for the exact stack trace matching the digest
   docker logs --tail 50 <web-container> | grep -A 5 -B 2 "digest"
   ```
3. **Verify live response for error markers**:
   ```bash
   # Detect if HTML response contains error digest markers
   curl -sL <URL> | grep -i "digest"
   ```

