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

## 3. Data Integrity, Privacy & Recovery
- [ ] Monetary values use integer minor units or `NUMERIC/DECIMAL`—zero `FLOAT`/`DOUBLE`.
- [ ] Timestamps use timezone-aware UTC (`TIMESTAMPTZ` / RFC 3339).
- [ ] Multi-tenant tables include `tenant_id` in primary/unique/composite indexes to prevent cross-tenant collisions and speed scoped queries.
- [ ] PII columns documented with retention TTL and deletion/anonymization workflow.
- [ ] Point-in-time recovery (PITR) and automated backup restore drills meet target RPO/RTO.
