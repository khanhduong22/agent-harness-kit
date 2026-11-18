# Browser Platform Defenses, Origin Validation & Passkeys Lifecycle

> Distilled from `GoogleChrome/modern-web-guidance` (Security & Privacy guides). Supplements server-side security controls in `SKILL.md` with browser-native XSS defenses, strict `Origin` comparison, Passkeys/WebAuthn lifecycle, and Fetch Metadata isolation.

---

## 1. Native HTML Sanitizer API (`Element.setHTML()` & `Sanitizer`)

When rendering untrusted HTML on the client, prefer the native **Sanitizer API** (`setHTML()` / `Document.parseHTML()`) over regex strippers or naive innerHTML wrappers. Because parsing and sanitization happen inside the browser's native C++ HTML parser in the exact target element's context, mutation XSS (`mXSS`) parser differentials are eliminated:

```js
// Default Sanitizer strips <script>, on* handlers, and XSS-unsafe attributes/elements
container.setHTML(untrustedHTML);

// Restrictive allowlist configuration (Sanitizer never lets custom configs re-enable XSS-unsafe elements)
const strictSanitizer = new Sanitizer({
  elements: ['p', 'b', 'i', 'strong', 'em', 'a'],
  attributes: ['class', 'href'],
  replaceWithChildrenElements: ['div'],
});

if ('setHTML' in Element.prototype) {
  container.setHTML(untrustedHTML, { sanitizer: strictSanitizer });
} else {
  // Fallback via vetted library such as DOMPurify on browsers without native Sanitizer API
  container.innerHTML = DOMPurify.sanitize(untrustedHTML);
}
```

- Always enforce equivalent **server-side** HTML sanitization whenever user content is also SSR-rendered, emailed, or served to non-browser clients (defense in depth).

---

## 2. Trusted Types, Incremental CSP & Safe Origin Validation

### DOM XSS Elimination via Trusted Types
Enable CSP enforcement (`require-trusted-types-for 'script'`) so dangerous DOM sinks (`innerHTML`, `outerHTML`, `document.write`, `eval`, `script.src`) reject raw strings and only accept explicit `TrustedHTML` / `TrustedScriptURL` tokens:

```js
import DOMPurify from 'dompurify';

const htmlPolicy = window.trustedTypes?.createPolicy('app-sanitize-html', {
  createHTML: (dirty) => DOMPurify.sanitize(dirty, { RETURN_TRUSTED_TYPE: false }),
});
```

- **Hard Trap**: An `escapeHTML` entity-replacement policy (`<` -> `&lt;`) converts markup to text and is **NOT** a full context-aware HTML sanitizer; use `element.textContent` for plain text, and never interpolate escaped strings into unquoted attributes or URL `href` attributes (`javascript:` still executes).

### Incremental CSP Rollout (`Report-Only`)
1. Deploy `Content-Security-Policy-Report-Only` + `Reporting-Endpoints` before switching to blocking enforcement.
2. Scrub tokens, OAuth codes, and PII from collected report URLs and monitor violation noise.
3. Enforce strict directives: `script-src 'nonce-<random>' 'strict-dynamic'`, `object-src 'none'`, `base-uri 'none'`, `frame-ancestors 'none'` (or `'self'`), plus `require-trusted-types-for 'script'`.

### Structured Origin Validation (`Origin` API vs String Traps)
Manual origin checks fail in 4 classic ways: prefix spoofing (`https://app.example.com.evil.com`), port/path normalization mismatches (`:443`), Public Suffix List (`a.co.uk` vs `b.co.uk`), and opaque origin collisions (`"null" === "null"` from `<iframe sandbox>` or `data:` URLs).

Use the native **`Origin` API** (`Origin.from()`, `isSameOrigin()`, `isSameSite()`, `origin.opaque`) when available (with `new URL()` strict fallback):

```js
const TRUSTED_ORIGIN = 'Origin' in globalThis ? Origin.from('https://app.example.com') : new URL('https://app.example.com');

function extractOrigin(candidate) {
  try {
    return Origin.from(candidate); // Handles URLs, MessageEvent (browser-dispatched), <a>, self
  } catch {
    return Origin.from(candidate.origin); // Fallback for synthetic unit-test MessageEvent
  }
}

window.addEventListener('message', (event) => {
  if (event.origin === 'null') return; // Reject unpinned opaque sandbox/data origins
  if ('Origin' in globalThis) {
    if (!extractOrigin(event).isSameOrigin(TRUSTED_ORIGIN)) return;
  } else if (event.origin !== TRUSTED_ORIGIN.origin) {
    return;
  }
  handleVerifiedMessage(event.data);
});
```

- **Outgoing `window.postMessage(payload, targetOrigin)`**: Always specify the exact destination origin (`https://app.example.com`), NEVER `'*'` for sensitive data.
- **Note on `Origin.from()` inputs**: Do NOT pass `Location`, `Document`, `Request`, or `Response` directly to `Origin.from()` (throws `TypeError`)—pass `self`, `request.url`, or `response.url`. Use `.isSameSite()` strictly for cross-subdomain navigation validation (`?returnTo=`), never for privileged `postMessage` capability checks.

---

## 3. Passkeys / WebAuthn Full Lifecycle & Credential Signal APIs

### Core Security Invariants
- **Secure Context Only**: WebAuthn works strictly on `https://` or `http://localhost`.
- **Never Guess `rpId` on the Client**: Always read `rpId` from server-provided WebAuthn JSON options (`publicKey.rp.id` / `publicKey.rpId`), NEVER `window.location.hostname` (breaks on parent-domain or Related Origin Request setups like `login.example.com` with `rpId: 'example.com'`).
- **Base64URL Discipline**: Store and exchange credential IDs and `passkeyUserId` exclusively as unpadded Base64URL (`[A-Za-z0-9_-]`, no `=`).
- **AAGUID Is UX-Only**: Use returned AAGUID solely to display provider names/icons (e.g., iCloud Keychain, Google Password Manager, 1Password) in credential lists—never use AAGUID as an authorization or security decision boundary.

### Seamless Sign-In & Credential Synchronization
1. **Conditional UI (Autofill Passkeys)**: Call `navigator.credentials.get({ publicKey: options, mediation: 'conditional' })` only after checking `PublicKeyCredential.isConditionalMediationAvailable?.()`, paired with `<input autocomplete="username webauthn">`. Pass `allowCredentials: []` on discoverable sign-in.
2. **Capability Detection**: Call `await PublicKeyCredential.getClientCapabilities()` before rendering "Create passkey" buttons so unsupported browsers fall back to MFA enrollment cleanly.
3. **Password Manager Sync via Signal APIs** (always feature-detect first):
   - When deleting a passkey on the server (and on credential management page load), sync accepted IDs:
     `await PublicKeyCredential.signalAllAcceptedCredentials?.({ rpId, userId, allAcceptedCredentialIds })`
   - When an assertion uses an unknown/revoked credential ID on the server:
     `await PublicKeyCredential.signalUnknownCredential?.({ rpId, credentialId })`
   - When the user updates account `name` or `displayName` (NOT individual key nicknames):
     `await PublicKeyCredential.signalCurrentUserDetails?.({ rpId, userId, name, displayName })`

---

## 4. Fetch Metadata Isolation, SRI & Companion Headers

### Server-Side `Sec-Fetch-*` Resource Isolation
Reject unexpected cross-site requests to state/data endpoints before business logic runs (and always include `Vary: Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site`):
- Allow `Sec-Fetch-Site` in `['same-origin', 'none']` (drop `'same-site'` if any subdomain hosts untrusted or user-generated content).
- Allow `'cross-site'` ONLY for explicit top-level GET navigations (`mode === 'navigate' && req.method === 'GET' && !['object', 'embed'].includes(dest)`) or intentionally public webhook/CORS API endpoints.

### Companion Browser Defense Headers
- **SRI**: Add `integrity="sha384-..." crossorigin="anonymous"` on all third-party `<script>` and `<link rel="stylesheet">` tags.
- **Cross-Origin Isolation**: Pair `Cross-Origin-Opener-Policy: same-origin` (`COOP`), `Cross-Origin-Embedder-Policy: require-corp` (`COEP`), and `Cross-Origin-Resource-Policy: same-origin` (`CORP`).
- **Session Hygiene**: Combine `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, strict `Permissions-Policy`, and `Clear-Site-Data: "cookies", "storage"` on logout responses.
