# Core Adversarial Audit Checklist

Inspect every target across all six domains. Assume bugs exist until verified absent.

## 1. Correctness & Edge-Case Integrity
- **Boundary values:** Zero, negative, empty/whitespace strings, null/nil, integer overflow, NaN/Infinity, massive collections handled deterministically?
- **Encoding & time:** Multibyte UTF-8, emojis, control chars, null bytes safe? Timestamps in UTC (RFC 3339)? Durations measured with monotonic clocks?
- **Numeric precision:** Money/exact quantities stored as minor-unit integers or fixed-precision decimals (never IEEE 754 float)?
- **Error propagation:** Zero silently swallowed errors, empty catch blocks, or overwritten root causes? Internal errors logged richly while external errors stay sanitized?
- **Atomic state:** If step 2 of 3 fails, does state roll back cleanly with zero orphans?

## 2. Security & Zero-Trust Verification
- **Injection:** SQL, NoSQL, LDAP, OS command, template/HTML/XSS, and log inputs strictly parameterized or encoded? Check dynamic `ORDER BY`, `LIMIT`, column names, and shell args.
- **Authn & Authz:** Tokens verified for signature, algorithm pinning, `exp`, `nbf`, `iss`, `aud`? Constant-time secret comparisons? Authz enforced on *every* endpoint/resource lookup? Tenant/owner scope derived strictly from verified auth context (never request body/params)?
- **Mass assignment:** Request DTOs strictly separated from persistence/domain models so protected fields cannot be overwritten?
- **Bounds & SSRF:** Request sizes, header sizes, upload sizes, nesting depths, and array lengths capped? Remote URL fetches block private/loopback/link-local/metadata IPs post-DNS and across redirects?
- **Data leakage & crypto:** Zero secrets, tokens, PII, or raw stack traces in logs/metrics/client errors? CSPRNGs for tokens/nonces, modern password hashing (Argon2id/bcrypt/scrypt), and AEAD ciphers?

## 3. Performance & Resource Bounds
- **Algorithmic & I/O efficiency:** Any O(N^2) loops on unbounded inputs, N+1 queries, missing indexes, `SELECT *`, or full-table scans?
- **Pagination & streaming:** Hard max page size + stable ordering (keyset/cursor for large sets)? Large exports/files streamed rather than buffered in RAM? Caches bounded by max size + TTL?
- **Pools & concurrency:** Connection/worker pools explicitly bounded and reused? Blocking I/O or CPU work kept off async event loops / UI main threads? Locks never held across network/disk I/O?
- **Cardinality:** Zero unbounded dynamic IDs (user IDs, raw paths) in metric labels?

## 4. Reliability, Concurrency & Lifecycle
- **Timeouts & cancellation:** Explicit timeouts and propagated cancellation context on every inbound, outbound, DB, and lock operation?
- **Idempotency & retries:** Duplicate delivery safe via unique constraints or idempotency keys? Retries restricted to transient safe errors with exponential backoff + jitter + retry cap?
- **Resource cleanup:** DB rows/txs, HTTP bodies, file handles, subscriptions, timers, GPU/audio handles, and background tasks guaranteed closed on success, error, and panic?
- **Lifecycle:** Fail-fast startup config validation, distinct liveness vs. readiness probes, and bounded graceful shutdown draining?

## 5. Architecture & Design Discipline (SOLID / DRY / KISS / ATOMIC)
- **Dependency direction:** Zero transport/UI/ORM/SDK/engine imports leaking into core domain logic?
- **SRP & modularity:** Any god-classes, 300-line functions, deep nesting, or boolean-flag soup that should be split or turned into an explicit state machine?
- **DRY & KISS:** Duplicated business rules across modules? Or speculative over-abstraction adding indirection without value?
- **Hidden state:** Mutable global singletons, scattered env lookups outside config, or circular dependencies?

## 6. Test Rigor & Determinism
- **Real assertions:** Do tests verify observable contracts and failure/security paths, or are they tautological mock choreography?
- **Determinism:** Zero real `sleep()`, wall-clock assumptions, network dependence, shared mutable test state, or order-dependence?

## Severity Rubric & Finding Template

- **P0 Blocker:** Exploitable vulnerability, data loss/corruption, race condition, crash, or broken core contract. Must fix immediately.
- **P1 High:** Missing timeout/bound, resource leak, severe perf/frame bottleneck, weak authz guard, or missing critical edge-case test. Must fix before sign-off.
- **P2 Medium:** Architectural/SOLID erosion, leaky abstraction, maintainability debt, or suboptimal ergonomics. Fix now or schedule explicitly.
- **P3 Nit:** Minor naming, clarity, or polish improvement.

For every finding, output:
1. **`[P0|P1|P2|P3]` Title**
2. **Location:** Exact file path and symbol/function (or spec section)
3. **Failure / Exploit Scenario:** Concrete step-by-step trace
4. **Recommended Fix:** Concrete code patch or architectural change
5. **Regression Test:** Exact test case that permanently prevents recurrence
