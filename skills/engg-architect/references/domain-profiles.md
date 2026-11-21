# Cross-Stack Domain Profiles

Load only the section(s) matching the active project surface(s). Combine multiple profiles for full-stack or multi-platform systems.

## 1. Backend & Distributed Services
- **Architecture:** Hexagonal / Clean Architecture (`transport -> application/service -> domain -> ports <- adapters`).
- **Key Budgets:** p50/p95/p99 latency, RPS + burst multiplier, availability SLO, RPO/RTO, payload size cap, connection pool bounds.
- **Critical Concerns:** Idempotency keys, transactional outbox/sagas, tenant isolation (anti-IDOR), SSRF egress guards, rate limiting, backpressure, liveness vs. readiness probes, SIGTERM graceful drain.
- **Testing:** Unit (domain purity), integration (ephemeral real DB/broker), contract tests (OpenAPI/Protobuf + adapter port suites), race detector, fault injection.

## 2. Web Client (SPA / SSR / Edge / PWA)
- **Architecture:** Atomic UI components + Feature-Sliced or Modular Domain Architecture; strict separation of server state, client UI state, and domain logic.
- **Key Budgets:** Core Web Vitals (LCP, INP, CLS), initial JS/CSS bundle budget, hydration time, frame smoothness (60fps/120fps interactions).
- **Critical Concerns:** XSS/CSRF/CSP/Trusted Types hygiene, accessible semantics (WCAG AA keyboard, ARIA, focus management), optimistic UI rollback, race-condition-safe async fetching (AbortController), offline/stale-while-revalidate handling, responsive layout stability.
- **Testing:** Component/interaction tests (user-centric queries, not implementation details), accessibility assertions, state-machine unit tests, visual/E2E critical journeys, network failure/slow-3G simulation.

## 3. Mobile Client (iOS / Android / Cross-Platform)
- **Architecture:** Clean MVVM / MVI / Unidirectional Data Flow (UDF) with strict repository/use-case separation from UI views and OS lifecycle.
- **Key Budgets:** Cold/warm startup time, 16.6ms/8.3ms frame budget (zero main-thread I/O), memory footprint, battery/wake-lock impact, APK/IPA binary size.
- **Critical Concerns:** Offline-first local persistence + conflict resolution, process death & state restoration, secure storage (Keychain/Keystore, never plaintext prefs), certificate pinning / deep-link validation, permission denial flows, background task constraints, graceful network handoffs.
- **Testing:** Unit tests for ViewModels/reducers/use-cases, offline/sync conflict tests, process-death & rotation recovery tests, UI/instrumented critical-path tests, memory/leak profiling.

## 4. Game Client & Real-Time Simulation
- **Architecture:** Strict separation of fixed-timestep Simulation/Gameplay Logic (deterministic where possible), Rendering, Audio, Input, Asset Streaming, and Networking. Prefer ECS or modular component/state-machine architecture over deep inheritance hierarchies.
- **Key Budgets:** Hard frame budget (e.g., 16.67ms @ 60fps or 8.33ms @ 120fps), zero GC allocations in hot update/render loops, draw-call/triangle/VRAM/audio-voice ceilings, asset streaming memory caps.
- **Critical Concerns:** Fixed-timestep physics vs. render interpolation, object pooling, save-file versioning & corruption recovery (atomic write + checksum), input buffering & remapping, anti-tamper/server-authoritative state validation (for multiplayer), deterministic replay/seed support, thermal/device tier scaling.
- **Testing:** Headless deterministic simulation tests, state-machine transition tests, save/load migration & corruption fuzzing, frame-time soak tests, multiplayer desync/latency/packet-loss simulation.

## 5. Database & Data Engineering
- **Architecture:** Schema-first contracts, explicit ownership per service/bounded context, clear separation of OLTP transactional paths vs. OLAP analytical pipelines.
- **Key Budgets:** Query p95/p99, index selectivity, lock-wait limits, replication lag ceiling, storage growth rate, RPO/RTO backup restore SLA.
- **Critical Concerns:** Zero-downtime expand-and-contract migrations, safe locking (no full-table rewrites under live load), parameterized queries, keyset/cursor pagination, idempotent batch/ETL ingestion, PII encryption/retention/erasure compliance, query plan (`EXPLAIN ANALYZE`) verification.
- **Testing:** Migration up/down + backward-compatibility tests, concurrency/isolation-level anomaly tests, realistic data-volume query-plan checks, backup restore drills.

## 6. Infrastructure, DevOps & Platform Engineering
- **Architecture:** Declarative, modular Infrastructure-as-Code (IaC) with strict environment parity (dev/staging/prod), immutable artifacts, and GitOps/automated pipelines.
- **Key Budgets:** Deploy time, rollback time, cold-start latency, cost ceiling/FinOps guardrails, blast-radius limits, MTTR.
- **Critical Concerns:** Least-privilege IAM, zero hardcoded secrets (OIDC/workload identity + secret managers), minimal hardened container images (non-root, read-only rootfs, pinned digests), SBOM & vulnerability scanning, progressive delivery (canary/blue-green), automated rollback triggers, drift detection.
- **Testing:** IaC static validation (`validate`/`plan`/policy-as-code), container security scanning, synthetic smoke/canary probes, chaos/failover drills, dry-run rollback verification.
