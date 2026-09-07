---
name: fix-sonarqube
description: Mandatory workflow step to run linter (bun run lint / eslint-sonar) and resolve all SonarQube code smells, type errors, prefer-for-of, prefer-optional-chain, and any-casts before completing any task.
---

# Fix SonarQube & ESLint Code Quality Skill

Use this skill whenever completing code implementation, feature additions, or refactoring in this project.

## Workflow

1. **Run Linter Check**:
   ```bash
   bun run lint
   ```
2. **Inspect and Resolve All Violations**:
   - **`@typescript-eslint/prefer-for-of`**: Replace indexed `for (let i=0; i<str.length; i++)` loops with `for (const char of str)` loops.
   - **`@typescript-eslint/prefer-optional-chain`**: Replace manual `&&` guards like `obj.prop && obj.prop.method()` with optional chaining `obj.prop?.method()`.
   - **`@typescript-eslint/no-explicit-any`**: Replace `any` casts with explicit interfaces or `Record<string, unknown>`.
   - **Unused Imports & Variables**: Remove unused imports or variable assignments.
3. **Verify Clean Pass**:
   - Re-run `bun run lint` to verify **0 errors**.
   - Re-run `bun run build` to verify clean TypeScript compilation.
