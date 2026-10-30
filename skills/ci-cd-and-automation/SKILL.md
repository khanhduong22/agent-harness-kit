---
name: ci-cd-and-automation
description: Automates CI/CD pipeline setup. Use when setting up or modifying build and deployment pipelines. Use when you need to automate quality gates, configure test runners in CI, or establish deployment strategies.
---

# CI/CD and Automation

## Overview

Automate quality gates so that no change reaches production without passing tests, lint, type checking, and build. CI/CD is the enforcement mechanism for every other skill — it catches what humans and agents miss, and it does so consistently on every single change.

**Shift Left:** Catch problems as early in the pipeline as possible. A bug caught in linting costs minutes; the same bug caught in production costs hours. Move checks upstream — static analysis before tests, tests before staging, staging before production.

**Faster is Safer:** Smaller batches and more frequent releases reduce risk, not increase it. A deployment with 3 changes is easier to debug than one with 30. Frequent releases build confidence in the release process itself.

## When to Use

- Setting up a new project's CI pipeline
- Adding or modifying automated checks
- Configuring deployment pipelines
- When a change should trigger automated verification
- Debugging CI failures

## The Quality Gate Pipeline

Every change goes through these gates before merge:

```
Pull Request Opened
    │
    ▼
┌─────────────────┐
│   LINT CHECK     │  eslint, prettier
│   ↓ pass         │
│   TYPE CHECK     │  tsc --noEmit
│   ↓ pass         │
│   UNIT TESTS     │  jest/vitest
│   ↓ pass         │
│   BUILD          │  npm run build
│   ↓ pass         │
│   INTEGRATION    │  API/DB tests
│   ↓ pass         │
│   E2E (optional) │  Playwright/Cypress
│   ↓ pass         │
│   SECURITY AUDIT │  npm audit
│   ↓ pass         │
│   BUNDLE SIZE    │  bundlesize check
└─────────────────┘
    │
    ▼
  Ready for review
```

**No gate can be skipped.** If lint fails, fix lint — don't disable the rule. If a test fails, fix the code — don't skip the test.

## GitHub Actions Configuration

### Basic CI Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npx tsc --noEmit

      - name: Test
        run: npm test -- --coverage

      - name: Build
        run: npm run build

      - name: Security audit
        run: npm audit --audit-level=high
```

### With Database Integration Tests

```yaml
  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: testdb
          POSTGRES_USER: ci_user
          POSTGRES_PASSWORD: ${{ secrets.CI_DB_PASSWORD }}
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      - run: npm ci
      - name: Run migrations
        run: npx prisma migrate deploy
        env:
          DATABASE_URL: postgresql://ci_user:${{ secrets.CI_DB_PASSWORD }}@localhost:5432/testdb
      - name: Integration tests
        run: npm run test:integration
        env:
          DATABASE_URL: postgresql://ci_user:${{ secrets.CI_DB_PASSWORD }}@localhost:5432/testdb
```

> **Note:** Even for CI-only test databases, use GitHub Secrets for credentials rather than hardcoding values. This builds good habits and prevents accidental reuse of test credentials in other contexts.

### E2E Tests

```yaml
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      - run: npm ci
      - name: Install Playwright
        run: npx playwright install --with-deps chromium
      - name: Build
        run: npm run build
      - name: Run E2E tests
        run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

## Feeding CI Failures Back to Agents

The power of CI with AI agents is the feedback loop. When CI fails:

```
CI fails
    │
    ▼
Copy the failure output
    │
    ▼
Feed it to the agent:
"The CI pipeline failed with this error:
[paste specific error]
Fix the issue and verify locally before pushing again."
    │
    ▼
Agent fixes → pushes → CI runs again
```

**Key patterns:**

```
Lint failure → Agent runs `npm run lint --fix` and commits
Type error  → Agent reads the error location and fixes the type
Test failure → Agent follows debugging-and-error-recovery skill
Build error → Agent checks config and dependencies
```

## Deployment Strategies

### Preview Deployments

Every PR gets a preview deployment for manual testing:

```yaml
# Deploy preview on PR (Vercel/Netlify/etc.)
deploy-preview:
  runs-on: ubuntu-latest
  if: github.event_name == 'pull_request'
  steps:
    - uses: actions/checkout@v4
    - name: Deploy preview
      run: npx vercel --token=${{ secrets.VERCEL_TOKEN }}
```

### Feature Flags

Feature flags decouple deployment from release. Deploy incomplete or risky features behind flags so you can:

- **Ship code without enabling it.** Merge to main early, enable when ready.
- **Roll back without redeploying.** Disable the flag instead of reverting code.
- **Canary new features.** Enable for 1% of users, then 10%, then 100%.
- **Run A/B tests.** Compare behavior with and without the feature.

```typescript
// Simple feature flag pattern
if (featureFlags.isEnabled('new-checkout-flow', { userId })) {
  return renderNewCheckout();
}
return renderLegacyCheckout();
```

**Flag lifecycle:** Create → Enable for testing → Canary → Full rollout → Remove the flag and dead code. Flags that live forever become technical debt — set a cleanup date when you create them.

### Staged Rollouts

```
PR merged to main
    │
    ▼
  Staging deployment (auto)
    │ Manual verification
    ▼
  Production deployment (manual trigger or auto after staging)
    │
    ▼
  Monitor for errors (15-minute window)
    │
    ├── Errors detected → Rollback
    └── Clean → Done
```

### Rollback Plan

Every deployment should be reversible:

```yaml
# Manual rollback workflow
name: Rollback
on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to rollback to'
        required: true

jobs:
  rollback:
    runs-on: ubuntu-latest
    steps:
      - name: Rollback deployment
        run: |
          # Deploy the specified previous version
          npx vercel rollback ${{ inputs.version }}
```

## Environment Management

```
.env.example       → Committed (template for developers)
.env                → NOT committed (local development)
.env.test           → Committed (test environment, no real secrets)
CI secrets          → Stored in GitHub Secrets / vault
Production secrets  → Stored in deployment platform / vault
```

CI should never have production secrets. Use separate secrets for CI testing.

## Automation Beyond CI

### Dependabot / Renovate

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: npm
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
```

### Build Cop Role

Designate someone responsible for keeping CI green. When the build breaks, the Build Cop's job is to fix or revert — not the person whose change caused the break. This prevents broken builds from accumulating while everyone assumes someone else will fix it.

### PR Checks

- **Required reviews:** At least 1 approval before merge
- **Required status checks:** CI must pass before merge
- **Branch protection:** No force-pushes to main
- **Auto-merge:** If all checks pass and approved, merge automatically

## CI Optimization

When the pipeline exceeds 10 minutes, apply these strategies in order of impact:

```
Slow CI pipeline?
├── Cache dependencies
│   └── Use actions/cache or setup-node cache option for node_modules
├── Run jobs in parallel
│   └── Split lint, typecheck, test, build into separate parallel jobs
├── Only run what changed
│   └── Use path filters to skip unrelated jobs (e.g., skip e2e for docs-only PRs)
├── Use matrix builds
│   └── Shard test suites across multiple runners
├── Optimize the test suite
│   └── Remove slow tests from the critical path, run them on a schedule instead
└── Use larger runners
    └── GitHub-hosted larger runners or self-hosted for CPU-heavy builds
```

**Example: caching and parallelism**
```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22', cache: 'npm' }
      - run: npm ci
      - run: npm run lint

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22', cache: 'npm' }
      - run: npm ci
      - run: npx tsc --noEmit

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22', cache: 'npm' }
      - run: npm ci
      - run: npm test -- --coverage
```

## Tier-1 Docker BuildKit & Self-Hosted CI/CD Acceleration (Sub-2-Minute Builds)

On self-hosted runners (`[app_pro]`, `[data_pro]`, bare-metal servers), Docker builds and zero-downtime Blue-Green deployments should complete in **under 2 minutes** (and **<15s on warm code changes**). When builds drag out to 5–10 minutes or deployments fail with port conflicts and orphaned containers, apply these battle-tested patterns:

### 1. Eliminating the 120s+ BuildKit Post-Build `contenthash` Scan Bottleneck
- **Symptom**: In multi-stage Docker builds, `RUN bun run build` (or `npm run build`) completes in 20 seconds, but the pipeline hangs completely without output for 2–3 minutes at the subsequent `COPY --from=builder` instruction.
- **Root Cause**: When the `builder` stage inherits from `deps` (with 100,000+ files in `node_modules`) and the `runner` stage has multiple `COPY --from=builder` commands, BuildKit pauses to compute recursive cryptographic `contenthash` trees across the entire 1.5 GB+ `builder` rootfs for every separate target path.
- **CI/CD Fix**:
  1. Purge `node_modules` and standalone artifacts at the end of the `RUN build` step so the builder stage snapshot is minimal:
     ```dockerfile
     RUN bun run build && \
         rm -rf node_modules .next/standalone/node_modules
     ```
  2. Copy static files (`package.json`, `public`, `messages`, `otel.js`, `entrypoint.sh`) directly from the local build context in `runner`. This is cached at `0.0s` independent of the builder stage.
  3. Consolidate built artifacts into a single `COPY --from=builder` instruction:
     ```dockerfile
     COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
     COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static
     ```

### 2. Per-Environment BuildKit Cache Namespace (`id=next-cache-${CACHE_ENV}`)
- **Symptom**: Cache thrashing ("Cache Ping-Pong"). When `develop`, `staging`, and `main` deploy on the same self-hosted runner, sharing a single `--mount=type=cache,target=/app/.next/cache` invalidates cache chunks on every build because different environment variables (`NEXT_PUBLIC_*`, `STRAPI_ADMIN_*`) change client bundle hashes.
- **CI/CD Fix**: Parameterize the cache mount by environment in both Dockerfile and GitHub Actions workflow:
  ```dockerfile
  ARG CACHE_ENV=dev
  RUN --mount=type=cache,id=next-cache-${CACHE_ENV},target=/app/.next/cache \
      --mount=type=cache,id=bun-cache,target=/root/.bun/install/cache \
      bun run build
  ```
  In GitHub Actions deployment step:
  ```yaml
  - name: Build production container
    run: |
      docker build \
        --build-arg CACHE_ENV=${{ inputs.environment || 'prod' }} \
        -t myapp:${{ github.sha }} .
  ```

### 3. Zero-Copy `FROM deps AS builder` & Direct Runner Layering
- In multi-stage Dockerfiles with large dependency trees (1.2–1.5 GB):
  - Place `COPY --from=deps --chown=appuser:appgroup /app/node_modules ./node_modules` in `runner` **before** copying application code. When application source code changes without touching `package.json` or lockfiles, the entire 1.5 GB dependency layer is `CACHED [0.0s]`.
  - In `builder`, never overlay source code on top of existing `node_modules` without pruning; build directly on `FROM deps AS builder` and clean up before artifact export.

### 4. Pre-Source Prisma Client Generation Layer
- In NestJS, Bun, or Node.js microservices utilizing Prisma ORM, generating the client during application compilation forces re-generation on every code change.
- **CI/CD Fix**: Isolate schema generation before copying application source code:
  ```dockerfile
  # 1. Dependencies layer
  COPY package.json bun.lockb ./
  RUN bun install --frozen-lockfile

  # 2. Prisma Client layer (CACHED 0.0s when schema untouched)
  COPY prisma ./prisma
  RUN bun prisma generate

  # 3. Source code compilation
  COPY tsconfig*.json nest-cli.json ./
  COPY src ./src
  RUN bun run build
  ```
  Schema edits are rare; source code edits are frequent. This orders layers by rate of change, saving 20–40 seconds per CI run.

### 5. Blue-Green Deployment Zombie Container & Concurrency Guard
- **Symptom**: Concurrent CI runs collide on host ports (`bind: address already in use`), or failed deployments leave containers running with `restart: unless-stopped`, creating zombie containers that interfere with subsequent deployments.
- **CI/CD Fix**:
  1. **Enforce Workflow Concurrency**: Set `concurrency:` with `cancel-in-progress: false` to guarantee deployments queue safely without interleaving:
     ```yaml
     concurrency:
       group: deploy-${{ inputs.environment || 'prod' }}
       cancel-in-progress: false
     ```
  2. **Automated Dual-Container Resolution**: Before building or starting containers, check if both `blue` and `green` are running. Compare `.State.StartedAt`, designate the newer container as `ACTIVE_SERVICE`, and stop/remove the older stale container:
     ```bash
     BLUE_RUNNING=$(docker inspect -f '{{.State.Running}}' myapp_blue 2>/dev/null || echo "false")
     GREEN_RUNNING=$(docker inspect -f '{{.State.Running}}' myapp_green 2>/dev/null || echo "false")

     if [ "$BLUE_RUNNING" = "true" ] && [ "$GREEN_RUNNING" = "true" ]; then
       BLUE_TIME=$(docker inspect -f '{{.State.StartedAt}}' myapp_blue)
       GREEN_TIME=$(docker inspect -f '{{.State.StartedAt}}' myapp_green)
       if [[ "$BLUE_TIME" > "$GREEN_TIME" ]]; then
         ACTIVE_SERVICE="blue"; INACTIVE_SERVICE="green"
       else
         ACTIVE_SERVICE="green"; INACTIVE_SERVICE="blue"
       fi
       echo "Dual running containers detected. Keeping $ACTIVE_SERVICE, pruning $INACTIVE_SERVICE..."
       docker compose stop $INACTIVE_SERVICE && docker compose rm -f $INACTIVE_SERVICE
     fi
     ```
  3. **Exit-Trap Cleanup on Healthcheck Timeout**: When the candidate `$INACTIVE_SERVICE` fails its health probe timeout, explicitly stop and remove it **before** triggering `exit 1`. This stops Docker's `restart: unless-stopped` policy from respawning a broken container in the background:
     ```bash
     if [ "$HEALTHY" != "true" ]; then
       echo "Healthcheck timed out for candidate $INACTIVE_SERVICE. Removing container before exit..."
       docker compose stop "$INACTIVE_SERVICE" && docker compose rm -f "$INACTIVE_SERVICE"
       exit 1
     fi
     ```

### 6. Alpine Container Healthcheck IPv4 & Next.js 16 RSC OpenTelemetry Guard
1. **Alpine Linux IPv4 Healthcheck Bindings (`127.0.0.1` vs `localhost`)**:
   In Alpine-based minimal containers, `localhost` resolves to IPv6 `[::1]` first. When Node.js/Bun servers bind to IPv4 wildcard `0.0.0.0`, Alpine's BusyBox `wget` fails with `Connection refused`. Always use explicit IPv4 loopback `http://127.0.0.1:<port>` in CI health check scripts and Dockerfile `HEALTHCHECK` directives:
   ```bash
   # CI Health Probe
   curl -s -f http://127.0.0.1:3000/api/health | grep -q '"status":"ok"'
   ```
2. **Next.js 16 RSC OpenTelemetry `Math.random` Guard**:
   In Next.js 16 App Router builds with component caching (`cacheComponents: true`), Next.js patches `Math.random()` to trap non-deterministic behavior during static prerendering. Synchronous OpenTelemetry span generation inside React Server Components triggers `NEXT_STATIC_GEN_BAILOUT`.
   - **CI Solution**: Ensure `otel.js` captures `const nativeMathRandom = Math.random.bind(Math)` before Next.js initializes, passing a custom `idGenerator` into `new NodeSDK({ idGenerator })` so CI static page builds never abort unexpectedly.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "CI is too slow" | Optimize the pipeline (see CI Optimization below), don't skip it. A 5-minute pipeline prevents hours of debugging. |
| "This change is trivial, skip CI" | Trivial changes break builds. CI is fast for trivial changes anyway. |
| "The test is flaky, just re-run" | Flaky tests mask real bugs and waste everyone's time. Fix the flakiness. |
| "We'll add CI later" | Projects without CI accumulate broken states. Set it up on day one. |
| "Manual testing is enough" | Manual testing doesn't scale and isn't repeatable. Automate what you can. |

## Red Flags

- No CI pipeline in the project
- CI failures ignored or silenced
- Tests disabled in CI to make the pipeline pass
- Production deploys without staging verification
- No rollback mechanism
- Secrets stored in code or CI config files (not secrets manager)
- Long CI times with no optimization effort

## Verification

After setting up or modifying CI:

- [ ] All quality gates are present (lint, types, tests, build, audit)
- [ ] Pipeline runs on every PR and push to main
- [ ] Failures block merge (branch protection configured)
- [ ] CI results feed back into the development loop
- [ ] Secrets are stored in the secrets manager, not in code
- [ ] Deployment has a rollback mechanism
- [ ] Pipeline runs in under 10 minutes for the test suite
