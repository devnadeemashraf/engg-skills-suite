# Zero-Downtime Migration & Data Safety Checklist

## 1. Expand-and-Contract Pattern (Mandatory for Breaking Changes)
For renaming/splitting columns, changing data types, or dropping fields in live systems:
1. **Expand:** Add new nullable column/table; deploy code that dual-writes both old and new while reading old (with fallback).
2. **Backfill:** Run throttled, idempotent batched backfill with progress checkpointing and replication-lag monitoring.
3. **Validate & Switch Reads:** Add constraint as `NOT VALID`, validate without blocking writes, deploy code reading exclusively from new column.
4. **Contract:** Stop writing old column; after safe rollback window passes, drop old column/table in a separate migration.

## 2. Lock & Production Safety Checks
- [ ] **Index creation:** Uses non-blocking online/concurrent creation (`CONCURRENTLY` / `ALGORITHM=INPLACE, LOCK=NONE`) outside an explicit transaction block where required.
- [ ] **Lock timeout set:** Migration session enforces strict `lock_timeout` (e.g., 2s–5s) and `statement_timeout` so it fails safely instead of queuing every live query behind it.
- [ ] **Constraint addition:** Foreign keys and check constraints added as `NOT VALID` first, then validated separately to avoid full-table write locks.
- [ ] **N-1 compatibility:** Old application instances running during rolling deployment continue working cleanly after migration applies.
- [ ] **No ORM auto-sync in prod:** Schema changes are explicit, version-controlled SQL/migration artifacts reviewed in PRs.
- [ ] **Linted:** `squawk` (Postgres) passes on every migration file in CI, or each finding is fixed or explicitly justified.

## 3. Data Integrity, Privacy & Recovery
- [ ] Monetary values use integer minor units or `NUMERIC/DECIMAL`—zero `FLOAT`/`DOUBLE`.
- [ ] Timestamps use timezone-aware UTC (`TIMESTAMPTZ` / RFC 3339).
- [ ] Multi-tenant tables include `tenant_id` in primary/unique/composite indexes to prevent cross-tenant collisions and speed scoped queries.
- [ ] PII columns documented with retention TTL and deletion/anonymization workflow.
- [ ] Point-in-time recovery (PITR) and automated backup restore drills meet target RPO/RTO.

## 4. PII Inventory (keep next to the schema; review on every migration touching these tables)

| Table.column | Purpose | Retention | Erasure method | Can reach logs? |
|---|---|---|---|---|
| users.email | login, receipts | account life + 30 days | hard delete on account deletion | no (scrubbed) |

## 5. Checkpointed Backfill Template (pseudocode; adapt to the stack)

```text
cursor = load_checkpoint("backfill_orders_total_cents") or MIN_ID
loop:
    batch = SELECT id, ... FROM orders WHERE id > cursor ORDER BY id LIMIT 1000   -- keyset, never OFFSET
    if batch is empty: break
    in one short transaction (with lock_timeout and statement_timeout set):
        UPDATE orders SET total_cents = <derived> WHERE id IN (batch) AND total_cents IS NULL   -- idempotent
    cursor = last id in batch; save_checkpoint(cursor)                                          -- resumable
    if replication_lag > LIMIT: sleep and back off                                              -- throttled
--dry-run: count the rows each batch would change, write nothing
```

Prove it in tests: rerunning after a crash mid-batch changes no row twice, and the final row count matches the dry run.
