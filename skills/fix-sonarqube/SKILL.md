---
name: fix-sonarqube
description: Mandatory workflow step to run the linter (bun run lint / eslint-sonar) and resolve all SonarQube code smells, type errors, prefer-for-of, prefer-optional-chain, and any-casts before completing any task.
---

# Fix SonarQube & ESLint Code Quality

## Overview
SonarQube and `eslint-plugin-sonarjs` flag code smells, cognitive complexity bottlenecks, security vulnerabilities (e.g. insecure random, weak crypto, regex DoS), and logic bugs. This skill is the protocol for fetching, analyzing, and fixing those issues.

---

## Issue Discovery Protocol

### Method 1: Query the SonarQube Server API
Fetch unresolved issues directly over REST. `SONAR_PROJECT_KEY` is the component key of the repository you are working in — read it from `sonar-project.properties` if present, otherwise it is usually the repository name.

```bash
# Open Bugs and Vulnerabilities
curl -s -u "$SONAR_TOKEN:" \
  "$SONAR_HOST_URL/api/issues/search?componentKeys=$SONAR_PROJECT_KEY&types=VULNERABILITY,BUG&resolved=false" | jq .

# High-severity Code Smells
curl -s -u "$SONAR_TOKEN:" \
  "$SONAR_HOST_URL/api/issues/search?componentKeys=$SONAR_PROJECT_KEY&types=CODE_SMELL&severities=CRITICAL,BLOCKER,MAJOR&resolved=false" | jq .
```

### Method 2: Offline ESLint-Sonar Scan
Run fast local linting in the target repository:
```bash
bun run lint
# or
bun run eslint-sonar
```

---

## Common SonarQube Rules & Fix Patterns

| Rule Key | Violation Pattern | Standard Fix |
| :--- | :--- | :--- |
| `sonarjs/pseudo-random` | `Math.random()` used for token / ID | Use `crypto.randomBytes()` or `crypto.getRandomValues()` |
| `sonarjs/cognitive-complexity` | Complexity > 15 (deeply nested if/else) | Extract nested logic into helper methods or strategy mappers |
| `sonarjs/no-nested-conditional` | Nested ternary: `a ? (b ? c : d) : e` | Refactor into `if / else` or early returns |
| `sonarjs/no-nested-template-literals` | `` `...${`...`}...` `` | Extract nested template string into a constant variable |
| `sonarjs/no-redundant-optional` | `arg?: string \| undefined` | Remove `\| undefined` when `?` is already specified |
| `sonarjs/use-type-alias` | Long union type repeated | Declare `type Status = 'A' \| 'B' \| 'C'` alias |
| `sonarjs/no-dead-store` | Variable assigned but never used | Remove unused variable assignment |

---

## Verification Loop
After applying fixes:
1. Re-run the linter: `bun run lint` (0 errors).
2. Re-run the SonarQube scan for the repository you are in.
3. Check the Quality Gate: verify status is **`OK`**.
