# Definition of Done (DoD)

Companion reference for `incremental-implementation`, `planning-and-task-breakdown`, and `shipping-and-launch`.

## Mandatory Completion Criteria
1. **Scoped Implementation**: All acceptance criteria in the task specification are implemented at the root cause with zero unrelated file churn.
2. **Type Safety & Static Analysis**: `tsc --noEmit` and linter (`bun run lint`) pass with `0` errors and `0` unchecked `any` or `@ts-ignore` suppressions.
3. **Automated Tests**: Unit, integration, and (where UI is modified) Playwright E2E tests cover happy paths, edge cases, and regression scenarios and pass (`0` failures).
4. **Build Verification**: Production build (`bun run build`) completes cleanly with no SSR/prerender or bundle size regressions.
5. **Runtime Evidence**: Passing command outputs are captured and reported in the Handover Summary (What changed, What was tested, Residual risks).
