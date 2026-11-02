# AI Agent Runtime Security Hardening (`affaan-m/ECC`)

Distilled from `affaan-m/ECC` (`★ 294k+`, `skills/agent-security-hardening/SKILL.md`). Use when building, reviewing, or hardening AI agent frameworks, MCP servers, autonomous workers, tool gateways, or memory services that turn untrusted data into filesystem, network, memory, or tool side effects.

---

## 1. Core Security Invariants

1. **Everything Is Untrusted Input**: Treat model output, retrieved RAG documents, tool output, persistent memory, and cross-agent messages as untrusted input.
2. **Read-Only Default**: Default external integrations to read-only and grant each write capability separately.
3. **Action-Boundary Validation**: Validate deterministically at the real tool execution boundary even when an upstream prompt or JSON schema already validated the value. Prompt instructions are advisory; code before the side effect is authoritative.
4. **Fail Closed on Ambiguity**: Block execution before any side effect when identity, destination, ownership, or workspace containment cannot be proven.
5. **Dual-Gate Irreversible Operations**: Before any delete, publish, credential rotation, or schema mutation, the tool entry point must authorize the authenticated principal for that exact operation + resource scope and require explicit confirmation or a valid scoped pre-approval.

---

## 2. Trust Boundary Mapping

Map every path from untrusted source to side effect as:
`source -> parser -> validator -> side effect`

| Dimension | Required Evidence Before Side Effect |
|---|---|
| **Principal & Scope** | Authenticated identity and explicit resource scope authorizing the mutation |
| **Boundary Validator** | Exact deterministic function that runs immediately before the I/O call |
| **Payload Bounds** | Hard maximum input bytes and output truncation ceiling from deployment config |
| **Audit Trail** | Structured log recording principal, tool, target resource, and exit status (with secrets redacted *before* logging) |
| **Rollback / Recovery** | Deterministic cleanup (`finally` block, atomic temp file removal) if interrupted |

---

## 3. Identifier, CLI Argv, and Outbound URL Hardening

### Strict Identifier Allowlisting
Use strict regex allowlists and hard length ceilings (`<= 64` chars) for identifiers that become filenames, cache keys, or CLI arguments:

```python
import re

SAFE_AGENT_ID_CHARS = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_-]*$")
HARD_MAX_AGENT_ID_LENGTH = 64

def require_agent_id(value: object, *, max_length: int = 64) -> str:
    if isinstance(max_length, bool) or not isinstance(max_length, int) or not 1 <= max_length <= HARD_MAX_AGENT_ID_LENGTH:
        raise RuntimeError("configured agent ID limit must be between 1 and 64")
    if not isinstance(value, str) or len(value) > max_length or not SAFE_AGENT_ID_CHARS.fullmatch(value):
        raise ValueError("invalid agent identifier")
    return value
```

- **CLI Argument Separation**: Pass identifiers through an `argv` array (never `shell=True`) and place user/model-supplied positional values after the end-of-options marker (`--`).
- **Outbound SSRF & Redirect Re-Validation**:
  - Allow only explicitly required schemes (`https://`), require a hostname, reject embedded URL credentials (`user:pass@host`), and block RFC1918/loopback/link-local/metadata IPs.
  - Pin the resolved public IP at connection time to defeat **DNS rebinding**.
  - Disable automatic cross-origin credential forwarding: on any redirect hop where scheme or origin changes, strip `Authorization`/cookie headers and re-run destination and peer-IP validation.

---

## 4. Portable Filesystem Containment & Symlink Safety

String prefix checks (`path.startswith("/work/app")`) fail against sibling directories (`/work/application`). Always resolve paths and enforce cross-platform component portability:

```python
import re
from pathlib import Path

WINDOWS_RESERVED_NAME = re.compile(
    r"(CON|PRN|AUX|NUL|COM[1-9¹²³]|LPT[1-9¹²³])(\..*)?",
    re.IGNORECASE,
)

def workspace_path(workspace: Path, requested: str) -> Path:
    relative = Path(requested.replace("\\", "/"))
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("path must be workspace-relative")
    for part in relative.parts:
        if ":" in part or part.endswith((".", " ")) or WINDOWS_RESERVED_NAME.fullmatch(part):
            raise ValueError("path component is not portable")

    root = workspace.resolve(strict=True)
    candidate = (root / relative).resolve(strict=False)
    if not candidate.is_relative_to(root):
        raise ValueError("path escapes workspace")
    return candidate
```

- **Symlink Race Mitigation**: Reject symlink targets on sensitive writes, create temporary files atomically with `0o600` inside `0o700` user-private runtime directories, and clean up in `finally` blocks.

---

## 5. Bounded Tool Output & Pre-Log Secret Redaction

1. **Stream Byte Caps**: Read subprocess and tool outputs with a hard byte limit. Strip terminal control sequences, preserve structured fields, and append an explicit truncation marker with the original byte count.
2. **Typed Failure Contracts**: Never coerce malformed tool output into an empty `200 OK` / `{}` success value; return a typed error naming the tool, boundary, and validation failure reason without echoing secret payloads.
3. **Pre-Emission Redaction**: Redact sensitive values *before* they enter loggers, OpenTelemetry spans, exception messages, or model context. Verify with a sentinel secret capture test asserting zero occurrences across all emitted channels.
