# Offline Agent Harness Eval Gate Contract

## Purpose & Zero-Token-Tax Guarantee
This contract defines an offline, deterministic, zero-dependency release gate for `agent-harness-kit`. Because every check runs against repository source files (`AGENTS.md`, `rules/`, `skills/*/SKILL.md`, and `evals/harness_cases.jsonl`) in CI and pre-install verification, it adds **+0 tokens/turn** to live agent context windows.

## 2-Layer Harness Gate Architecture

### Layer 1: Structural, Collision & Context-Tax Gate
Evaluated directly over all active top-level skills (`skills/*/SKILL.md`, excluding `skills/drafts/` and hidden folders):
1. **Frontmatter Integrity**: Every skill must declare valid YAML frontmatter with a non-empty `name` (matching folder name) and non-empty `description` (`<= 1024` chars).
2. **Always-On Context Tax Budget**: Total frontmatter token estimate across all top-level skills (`sum(max(1, round(len(f"{name}: {description}") / 4)))`) MUST be **`<= 4,000` tokens/turn** (matching `skill-doctor` accounting).
3. **Trigger Collision Guard**: Pairwise Jaccard similarity over non-stopword `description` tokens MUST have **`0` collisions** (`Jaccard >= 0.35` with `>= 4` shared non-stopword tokens).

### Layer 2: Behavioral Eval Suite (`evals/harness_cases.jsonl`)
1. **`skill_trigger` (Bilingual EN/VI Routing Recall)**:
   - Deterministic relevance scorer using `skills/*/SKILL.md` frontmatter `name` & `description` only:
     - Explicit slash command matches declared in `description` (`+10.0`) or skill command name (`+3.5`).
     - Quoted trigger phrases declared in `description` (`+6.5` per matched phrase, capped at `+12.0`).
     - Exact skill name mentions (`+3.0`).
     - BM25/IDF-weighted token overlap (with lightweight Vietnamese-to-English technical synonym augmentation and gentle description-length normalization) plus bigram overlap.
   - Evaluates whether `expected_skill` ranks within the **top-3** candidates for each prompt.
2. **`rule_contract` (Critical Invariant Verification)**:
   - Evaluates regex `must_match` and `must_not_match` assertions across `AGENTS.md`, `rules/core.md`, and `rules/adapters/*.md` to prevent silent deletion or drift of mandatory safety, escalation, OPSEC, and English-first policies.

## Acceptance Thresholds (`ALLOW_RELEASE` vs `BLOCK_RELEASE`)
All four conditions MUST hold for `ALLOW_RELEASE` (exit code `0`); any violation emits `BLOCK_RELEASE` (exit code `1`):

| Gate Dimension | Release Threshold | On Failure |
|---|---|---|
| `skill_trigger` top-3 recall | `>= 95.0%` | `BLOCK_RELEASE` |
| `skill_trigger` critical cases (`critical: true`) | `0` failures (`100%` hit top-3) | `BLOCK_RELEASE` |
| `rule_contract` invariants | `100.0%` pass (`0` failures) | `BLOCK_RELEASE` |
| `context_tax` (frontmatter total) | `<= 4,000 tokens/turn` | `BLOCK_RELEASE` |
| `trigger_collisions` (`Jaccard >= 0.35`) | `0` collisions | `BLOCK_RELEASE` |

## Case Schema (`evals/harness_cases.jsonl`)
- **`skill_trigger` case**:
  ```json
  {"id": "trig-pattern-to-prod-en", "type": "skill_trigger", "lang": "en", "critical": true, "prompt": "...", "expected_skill": "pattern-to-prod"}
  ```
- **`rule_contract` case**:
  ```json
  {"id": "rule-01-escalation-git-push", "type": "rule_contract", "critical": true, "files": ["rules/core.md"], "must_match": ["..."], "must_not_match": []}
  ```

## CLI Usage
```bash
# Run offline eval gate against current repository root (portable Path resolution)
python3 scripts/eval_harness.py

# Target a specific kit checkout or mutated temp directory
python3 scripts/eval_harness.py --root /path/to/kit

# Output machine-readable JSON verdict and per-slice metrics
python3 scripts/eval_harness.py --json

# Run live gate + 3 seeded regression mutation tests (rule deletion, collision, broken trigger)
python3 scripts/eval_harness.py --self-test
```

## CI Integration
- `scripts/verify.sh`: compiles `scripts/eval_harness.py` via `py_compile` and executes `python3 "$kit_root/scripts/eval_harness.py" --self-test` whenever `evals/harness_cases.jsonl` exists.
- `tests/test_harness.sh`: verifies live `ALLOW_RELEASE` and confirms `BLOCK_RELEASE` (non-zero exit) on mutated temporary copies with seeded rule, collision, and trigger regressions.
