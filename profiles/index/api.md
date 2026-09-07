# Project Sub-Profile: Index API (`index-api`)

## 1. Service Overview & Architecture
- **Framework**: NestJS with TypeScript, running on `bun`.
- **Database & ORM**: PostgreSQL with Prisma ORM (`prisma/api/schema.prisma` and raw data readonly schema).
- **Observability**: OpenTelemetry instrumentation (`otel.js`).

## 2. Real Verification & Build Commands
All commands run from within `index-api/`:
- **Unit / Fast Tests**: `bun test` or `bun run test` (`vitest run`).
- **Watch Tests**: `bun run test:watch`.
- **E2E Tests**: `bun run test:e2e` (`jest --config ./test/jest-e2e.json`).
- **Postman / Integration Tests**: `bun run test:postman` (`bun postman/run-newman.ts`).
- **Linter & Code Formatting**: `bun run lint` (`eslint "{src,apps,libs,test}/**/*.ts" --fix`).
- **Typecheck & Build**: `bun run build` (`nest build -b tsc`).
- **Prisma Client Generation**: `bun run generate` (`bun prisma generate`).

## 3. Strict Coding Conventions
- **BaseRepository Enforcement**: Use inherited `BaseRepository` methods (`this.create`, `this.update`, `this.delete`, `this.findUnique`, `this.findById`) for primary entities instead of calling `this.prismaService.<entity>` directly.
- **Shared DTOs**: Reuse centralized DTOs from `~/shared/dtos/` (e.g., `PaginationParamsDTO`, `SearchDTO`) instead of creating duplicate DTOs in domain modules.
- **DTO Mappers**: Keep service classes lean by separating entity-to-DTO data mapping into dedicated `*.mapper.ts` files.
- **Centralized Slugify**: Use `slugify.util.ts` for URL/entity slugs with Vietnamese locale support rather than custom regexes.
- **Constants & Enums**: Use defined enums/constants for workflow stages, roles, and status codes.

## 4. Safety & Operational Constraints
- **Destructive DB Commands Blocked**: `bun run migrate:reset` and `prisma db push --force-reset` are strictly prohibited without explicit user sign-off.
- **Manual Migrations**: Follow `bun run db:manual:api` workflow for custom SQL patches.
- **Unknown APIs**: `[TBD: Need User Input]` Rate limiting policies for third-party public integrations.
