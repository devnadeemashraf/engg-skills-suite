---
name: engg-data
description: Designs schemas, data models, indexing strategies, query plans, and zero-downtime migrations across relational, NoSQL, caching, and analytical stores. Use when modeling domain data, writing schema migrations, optimizing queries/indexes, planning backfills, or validating consistency and backup/recovery guarantees.
license: Apache-2.0
metadata:
  version: "2.1.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# Database, Schema & Migration Engineer

Design durable, high-performance data models and zero-downtime schema evolutions that protect data integrity under live production traffic.

## When to Use

- Designing new schemas, tables, collections, key spaces, or analytical models.
- Authoring schema migrations, index changes, or large data backfills.
- Auditing query plans, locking behavior, transaction isolation, or backup/restore readiness.

## Non-Negotiable Rules

1. **Read checklist first:** Load `references/migration-safety-checklist.md` before writing any schema or migration.
2. **Enforce integrity in the datastore:** Express primary keys, foreign keys, unique constraints, check constraints, and `NOT NULL` invariants at the database layer—not only in application code.
3. **Zero-downtime expand-and-contract:** Never ship a single-step destructive migration (rename/drop column, tighten type, blocking table rewrite) against a live system. Always split into backward-compatible Expand -> Backfill -> Cutover -> Contract phases.
4. **Verify real query plans:** Every non-trivial query or new index must be validated with realistic cardinality via `EXPLAIN (ANALYZE, BUFFERS)` (or datastore equivalent).
5. **Bounded, idempotent backfills:** Data migrations must execute in throttled, resumable, idempotent batches—never one giant locking transaction.
6. **Migrations are linted by a machine:** run `squawk <migration>.sql` (Postgres) on every migration file in CI, so a lock-taking or table-rewriting statement can't merge on review alone. Migrations are risk tier **T3** (`references/engineering-constitution.md`).
7. **Tools, with consent:** run `scripts/toolcheck.sh <tools>` (Windows: `scripts/toolcheck.ps1`) for the tools this step needs, and prefer them over reading code by hand. Read only those tools' rows in `references/toolchain.md`, and `references/tool-consent.md` only before proposing an install.
8. **Working loop** (`references/working-loop.md`): start from `scripts/brief.py`, find files with `scripts/map.py` before reading them, run gates with `scripts/check.py`, and finish by updating `docs/HANDOFF.md` (§3). The user's explicit request outranks these defaults (§5). No AI attribution anywhere; `scripts/attribution_check.py` checks it.

## Workflow

1. **Access-Pattern & Invariant Mapping:**
   - List every read/write access pattern, expected volume, growth rate, consistency requirement (ACID vs. eventual), and retention/deletion policy (including PII erasure).
   - Maintain the **PII inventory** in the checklist's format: each personal-data column, why it's needed, its retention, how it's erased, and whether it can reach logs.
2. **Schema & Index Design:**
   - Choose normalized relational modeling by default; denormalize only for proven read-path budgets with an explicit synchronization strategy.
   - Design composite indexes aligned with equality-first, range/sort-second column order; cover pagination via stable keyset/cursor keys.
   - Standardize timestamps (UTC), exact numeric types for money, and explicit tenant/ownership scoping columns.
3. **Zero-Downtime Migration Plan:**
   - Produce deterministic, ordered migration files (`up` and safe rollback/remediation notes).
   - Verify locking characteristics (e.g., `CREATE INDEX CONCURRENTLY`, `NOT VALID` constraint followed by `VALIDATE CONSTRAINT`), and run `squawk` on each file. Treat its findings like any tool result: fix, or record why a rule doesn't apply.
   - Write backfills with the checkpointed template in `references/migration-safety-checklist.md`: bounded batches, a resumable cursor, idempotent writes, throttling, and a dry-run mode.
4. **Verification Suite:**
   - Test migrations against an ephemeral real engine: fresh DB apply, upgrade from previous version with populated realistic data, backward compatibility with N-1 application code, and concurrency/isolation edge cases.
   - Check query plans on **realistic volumes**: load or generate data at production-like cardinality first. A plan on a 100-row dev table says nothing about the 50-million-row production one. Record `EXPLAIN (ANALYZE, BUFFERS)` before and after.
5. **Audit Handoff:** Record a data-model change in `docs/EDD.md` (and an ADR if it's a lasting decision). Validate schema, queries, and migrations through `engg-audit` (Mode A) before release.

## Gotchas

- **Adding a column with a volatile default or table rewrite:** Can acquire an `ACCESS EXCLUSIVE` lock and take down production traffic.
- **Unindexed foreign keys:** Cause full-table scans on parent deletes/updates and trigger deadlocks.
- **Deep `OFFSET` pagination:** Degrades linearly as pages grow and skips/duplicates rows under concurrent writes. Use keyset/cursor pagination.
