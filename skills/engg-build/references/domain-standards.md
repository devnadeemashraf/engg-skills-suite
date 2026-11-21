# Stack-Specific Build Standards

Apply the rules matching the active project surface alongside the Unified Engineering Constitution.

## Backend Services
- Keep handlers/controllers razor-thin: parse/validate DTO -> call application service -> map domain error to uniform error envelope.
- Propagate request context/cancellation and correlation IDs through every I/O call.
- Enforce explicit timeouts on server reads/writes, outbound clients, and DB queries.
- Use minor-unit integers or fixed-precision decimals for money—never binary floats.

## Web Clients
- Structure UI atomically: pure presentational atoms/molecules (props in, events out) separated from stateful feature containers and domain hooks/services.
- Separate server cache state from ephemeral UI state; never mirror server data manually into global mutable stores without a clear invalidation strategy.
- Enforce accessibility by construction: semantic HTML, keyboard navigation, focus management, visible focus rings, and accessible names.
- Cancel stale fetches (`AbortController`), bound list rendering (virtualization for large sets), and lazy-load heavy routes/bundles.

## Mobile Clients
- Strictly forbid disk, database, or synchronous network work on the UI/main thread.
- Model screen state as an explicit immutable sealed state/enum (`Loading | Content | Empty | Error`) via Unidirectional Data Flow (UDF).
- Handle lifecycle interruptions (backgrounding, configuration change, OS process death) cleanly via saved state + persistent local store.
- Store tokens/keys exclusively in hardware-backed secure storage (Keychain/Keystore).

## Game Clients
- Decouple fixed-timestep simulation (`fixedUpdate`) from variable-rate presentation (`render` with interpolation).
- Zero heap allocations inside per-frame hot loops; reuse object pools, pre-allocated buffers, and struct-of-arrays/contiguous data where performance-critical.
- Drive entity/UI behavior with explicit finite state machines or data-driven tables rather than nested boolean flag soup.
- Write save files atomically (write temp -> flush -> checksum -> atomic rename) with an explicit schema version header.

## Database & Data Pipelines
- Name migrations deterministically and make data backfills idempotent and batched (never unbounded single-transaction locks).
- Define explicit foreign keys, unique constraints, check constraints, and `NOT NULL` defaults at the schema level—do not rely solely on application validation.
- Use keyset/cursor pagination for growing tables; verify indexes with `EXPLAIN ANALYZE`.

## Infrastructure & DevOps
- Pin exact provider, module, base image (digest), and toolchain versions.
- Tag/label every cloud resource consistently (`service`, `env`, `owner`, `managed_by`).
- Run containers as non-root with read-only root filesystems, dropped Linux capabilities, and explicit CPU/memory requests & limits.
