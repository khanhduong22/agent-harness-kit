# 200Lab MCP Integration for Motion Specs

The `200lab` MCP server connects coding agents directly to the 200Lab motion library containing 726+ verified records and 528 animation patterns.

---

## 1. Setup & Verification

Check if the `200lab` MCP server is installed and enabled in your client:

- **Claude Code**:
  ```bash
  claude mcp add --transport http 200lab-ai-tutor https://mcp.200lab.io/mcp/learner
  ```
- **Antigravity / Gemini CLI**:
  Pre-configured in `~/.gemini/antigravity/mcp/200lab/`.

---

## 2. Searching Motion Patterns

When an implementation task requires a specific interaction, call the `search` MCP tool with `types: ["motion"]`:

```json
{
  "query": "toast slide in",
  "types": ["motion"]
}
```

### Search Result Format:
```json
{
  "id": "sonner-toast-enter",
  "name": "Sonner toast enter",
  "type": "pattern",
  "category": "toasts",
  "trigger": "mount",
  "component": "toast",
  "source": "Sonner",
  "rule": "Slide a new toast up from 100% of its height while fading in over 400ms.",
  "summary": "Values: initial offset translateY(100%); transition transform 400ms, opacity 400ms, height 400ms; mounted state translateY(0), opacity 1"
}
```

---

## 3. Reading Full Motion Record

Call the `get` tool with `entity: "motion"` and the discovered `slug`:

```json
{
  "entity": "motion",
  "slug": "sonner-toast-enter"
}
```

### Payload Received:
- **Rule**: Narrative design rule and rationale.
- **Properties**: Exact delta transitions (`translateY 100% → 0`, `opacity 0 → 1`, durations, delays).
- **Observed Sources**: Benchmark citations (e.g. Radix, Apple HIG, Sonner).
- **Reduced Motion Fallback**: Exact CSS `@media (prefers-reduced-motion)` override rule.

---

## 4. Fallback Workflow (Offline / Zero-MCP)

If MCP is unavailable or rate-limited:
1. Consult the 18 canonical patterns in [patterns.md](./patterns.md).
2. Follow the universal timing & easing constants in [motion-rules.md](./motion-rules.md).
3. Apply standard cubic-bezier curves:
   - Enter: `cubic-bezier(0.23, 1, 0.32, 1)`
   - Exit: `cubic-bezier(0.4, 0, 1, 1)`
   - Move: `cubic-bezier(0.65, 0, 0.35, 1)`
