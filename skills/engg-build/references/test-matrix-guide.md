# 5-Category Test Matrix Guide

Before writing implementation code for any chunk, enumerate concrete test cases for the categories its risk tier requires. Adapt the examples to the active surface.

| Tier | Required categories | Extra proof |
|---|---|---|
| T0 | none (formatter and linter only) | none |
| T1 | 1 Happy path, 2 Boundaries | none |
| T2 | all five | contract tests at every port |
| T3 | all five | mutation testing on changed code: no surviving non-equivalent mutants |

**Property-based tests** belong in category 2 whenever the input space is large: parsers, serializers, money arithmetic, sorting/merging, state machines. Write the property ("decode(encode(x)) == x", "total is always an integer number of cents") and let the tool hunt for the counterexample.

## 1. Standard / Happy Path
- Core functional behaviors with typical valid inputs and realistic configurations.
- Contract conformance (exact response schema, status/error codes, rendered accessible DOM/UI state, physics/simulation output, generated IaC plan).

## 2. Boundary & Input Fuzzing
- Empty strings, whitespace-only strings, null/nil/undefined, zero, negative values, max integer bounds, NaN/Infinity, huge arrays/strings.
- Encoding & locale: multibyte UTF-8, emojis, RTL text, zero-width/control characters, null bytes, case-folding, timezone/DST/leap-year boundaries.
- Schema strictness: extra unknown fields, missing required fields, wrong primitive types, deeply nested JSON/payloads.
- Client/Game specifics: extreme viewport sizes/DPI, rapid double-taps, 0 delta-time or huge delta-time spike, empty/corrupt save files.

## 3. Concurrency, Ordering, State & Idempotency
- Duplicate concurrent/sequential mutations with the same idempotency key or double-click submission.
- Parallel read/write contention, optimistic locking collisions, race detector verification.
- Context cancellation / `AbortController` / screen unmount mid-flight (verify no state update on unmounted view and no leaked goroutine/task).
- Out-of-order async responses (stale response arriving after newer request).
- State machine illegal transitions (e.g., `Completed -> Pending`).

## 4. Failure & Fault Injection
- Downstream timeouts, connection drops, partial network reads, 5xx storms, malformed upstream payloads.
- Disk full / permission denied / corrupt cache entry / missing environment config on startup (fail-fast proof).
- Partial multi-step failure rollback (verify zero orphaned records or torn UI/world state).
- Offline mode, flaky network handoff, process death/restart recovery.

## 5. Security, Isolation & Abuse
- Missing, expired, tampered, or wrong-audience/wrong-algorithm credentials.
- Cross-tenant / horizontal & vertical privilege escalation (IDOR) attempts.
- Mass assignment / over-posting protected fields (`role`, `tenant_id`, `is_admin`, currency/inventory tampering).
- Oversized bodies, deep nesting, rate-limit exhaustion, injection payloads (SQL/NoSQL/HTML/XSS/Command/Log injection), SSRF internal IP targets.
- Secret/PII scrubbing verification: inspect captured logs and error outputs to prove zero sensitive values leak.

## Proving the tests can fail

A test that can't fail proves nothing. For every new suite, break the production code once on purpose, or run a mutation tool on it, and see the suite go red. Check the break actually applied (`git diff --stat` shows a change) before trusting the result.
