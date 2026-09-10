---
name: prisma-safe-migration
description: Prisma techniques for complex databases (custom SQL, Replication, manual DB updates) to avoid accidental database resets and handle schema drift safely.
---

# Prisma Safe Migration & Conflict Resolution

This skill outlines the safe use of Prisma in complex environments (Triggers, Views, Replication, or manual SQL DDL modifications) to prevent structural drift and dangerous Data Loss ("Do you want to reset the database?" warnings).

## 1. The "Three-Tier" Collaboration

Understand the roles of different DB tools:
- **Top Tier (Raw SQL/Manual DBA):** For advanced features (Triggers, Stored Procedures, Postgres Views, Replication). Prisma has limited native support for these.
- **Middle Tier (Introspect - `db pull`):** The "Scanner". Pulls manual changes from the DB back into your `schema.prisma` code.
- **Base Tier (Migrate - `migrate dev` / `deploy`):** The "Ledger". Tracks history via `.sql` files and pushes schema updates to the DB.

## 2. Preventing Database Resets

When you modify the database manually via `psql` or external GUIs, running standard `prisma migrate dev` flags a "drift" and may prompt to wipe your database. **To avoid this:**

### Technique A: "The Gatekeeper" (`--create-only`)
When blending Prisma schema changes with Manual SQL (e.g., Triggers):
1. Update `schema.prisma`.
2. Run `npx prisma migrate dev --create-only --name <name>`.
3. Prisma generates the `.sql` migration file but **stops** without executing it.
4. Open the `.sql` file, review it, and append your custom Raw SQL (Triggers, Indexes).
5. Run `npx prisma migrate dev` again to execute the final, reviewed script.

### Technique B: "The History Rewrite" (`migrate resolve`)
If you **already executed** raw SQL on the database (e.g., `ALTER TABLE ... ADD COLUMN ...`) to quickly resolve an issue, Prisma's next sync will fail because the column already exists.
1. Force Prisma to generate the migration file without running it:
   `npx prisma migrate dev --create-only --name manual_update_fix`
2. Mark the migration as successfully applied so Prisma ignores executing it:
   `npx prisma migrate resolve --applied <migration_folder_name>`
This inserts a record into `_prisma_migrations`, syncing the history flawlessly without conflicts.

### Technique C: The Validation Check (`db pull`)
Before creating any migration, run `npx prisma db pull`. If the `schema.prisma` file changes unexpectedly, it means someone edited the DB manually. Validate these changes before running `migrate dev`.

## 3. Deployment Safety
- **Local/Development (`migrate dev`):** Compares schema to DB, generates and executes SQL. **High risk** on drifted databases.
- **Server/Production (`migrate deploy`):** Only reads the `/migrations` folder to apply new scripts. It ignores schema drift and **never resets databases**. ALWAYS use `deploy` for CI/CD or Staging.

## 4. Considerations for Replication
If using Postgres Logical/Streaming Replication, standard Prisma `migrate dev` DDLS might unexpectedly lock tables.
**Best Practice:** Write non-blocking SQL manually (e.g., `CREATE INDEX CONCURRENTLY`), apply it to the DB directly, use `db pull` to update the schema in code, and then use `migrate resolve` to formally record the operation without breaking replication pipelines.
