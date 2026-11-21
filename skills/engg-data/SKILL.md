---
name: engg-data
description: Designs schemas, data models, indexing strategies, query plans, and zero-downtime migrations across relational, NoSQL, caching, and analytical stores. Use when modeling domain data, writing schema migrations, optimizing queries/indexes, planning backfills, or validating consistency and backup/recovery guarantees.
license: Apache-2.0
metadata:
  version: "1.0.0"
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

## Workflow

1. **Access-Pattern & Invariant Mapping:**
   - List every read/write access pattern, expected volume, growth rate, consistency requirement (ACID vs. eventual), and retention/deletion policy (including PII erasure).
2. **Schema & Index Design:**
   - Choose normalized relational modeling by default; denormalize only for proven read-path budgets with an explicit synchronization strategy.
   - Design composite indexes aligned with equality-first, range/sort-second column order; cover pagination via stable keyset/cursor keys.
   - Standardize timestamps (UTC), exact numeric types for money, and explicit tenant/ownership scoping columns.
3. **Zero-Downtime Migration Plan:**
   - Produce deterministic, ordered migration files (`up` and safe rollback/remediation notes).
   - Verify locking characteristics (e.g., `CREATE INDEX CONCURRENTLY`, `NOT VALID` constraint followed by `VALIDATE CONSTRAINT`).
4. **Verification Suite:**
   - Test migrations against an ephemeral real engine: fresh DB apply, upgrade from previous version with populated realistic data, backward compatibility with N-1 application code, and concurrency/isolation edge cases.
5. **Audit Handoff:** Validate schema, queries, and migrations through `engg-audit` (Mode A) before release.

## Gotchas

- **Adding a column with a volatile default or table rewrite:** Can acquire an `ACCESS EXCLUSIVE` lock and take down production traffic.
- **Unindexed foreign keys:** Cause full-table scans on parent deletes/updates and trigger deadlocks.
- **Deep `OFFSET` pagination:** Degrades linearly as pages grow and skips/duplicates rows under concurrent writes. Use keyset/cursor pagination.
