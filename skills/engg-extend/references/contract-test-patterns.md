# Shared Port Contract Test Patterns

Contract tests guarantee Liskov Substitution (LSP): any adapter claiming to implement a port behaves identically under normal, concurrent, and failure conditions.

## 1. Structure of a Reusable Contract Suite
Write a single test suite parameterized by a `setupAdapter() -> (PortImpl, cleanupFn)` factory. Run that exact same suite against:
- The fast in-memory fake used in unit tests.
- Every production adapter (e.g., PostgreSQL, SQLite, Redis, S3, local FS, cloud API sandbox).

## 2. Mandatory Contract Invariants to Verify

| Category | Required Assertions |
|---|---|
| **Round-Trip Fidelity** | Values saved/sent return byte-for-byte/semantically identical (including Unicode, UTC timestamps, empty vs. null fields, exact decimal precision). |
| **Canonical Error Mapping** | Missing item -> `ErrNotFound`; duplicate unique key -> `ErrConflict`; invalid input -> `ErrInvalidArgument`; canceled context -> `ErrCanceled`. Never leak raw vendor exceptions. |
| **Idempotency & Uniqueness** | Repeated creates with same idempotency/unique key are deterministic and never duplicate records. |
| **Tenant / Scope Isolation** | Lookup or mutation with mismatched `tenant_id` / owner scope behaves identically to `ErrNotFound` (no existence leak). |
| **Pagination & Ordering** | Deterministic sort order, hard page-size cap enforcement, stable cursor continuation with zero duplicates or skipped items. |
| **Concurrency Safety** | Parallel writes/updates honor optimistic version checks or atomic semantics without lost updates or data races. |
| **Timeouts & Cancellation** | Pre-canceled or short-deadline contexts abort promptly and release underlying connections/handles. |
| **Lifecycle & Health** | Clean startup validation, accurate health/readiness probe, and clean resource disposal on `Close()`/`Shutdown()`. |
