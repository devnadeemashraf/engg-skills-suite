# Brownfield Codebase & External Spec Hardening Playbook

## Part 1: Existing Codebase Triage Protocol

1. **Map Before Touching:**
   - Identify entrypoints, dependency manifest/lockfiles, architecture boundaries, build/test/lint commands, and top 5 highest-churn or highest-risk files.
2. **Baseline Health Check:**
   - Do tests currently exist and pass? Is static analysis/typechecking strict? Are dependencies pinned and vulnerability-free?
3. **Codebase Health Scorecard (1–5 each):**
   - Correctness & Safety | Security | Performance & Bounds | Reliability & Lifecycle | Architecture (SOLID/DRY/KISS) | Testability & CI
4. **Strangler-Fig Hardening Order (Never Big-Bang):**
   - **Step 1 — Safety Net:** Lock CI formatting/lint/type checks and add characterization tests around fragile high-value flows *before* refactoring.
   - **Step 2 — Stop the Bleeding (`P0`):** Fix active security holes, data corruption/race bugs, unpinned/vulnerable deps, and crash paths.
   - **Step 3 — Bound & Observe (`P1`):** Add timeouts, pool/payload/frame limits, structured logging/metrics, graceful shutdown, and key query/render optimizations.
   - **Step 4 — Architectural Tightening (`P2`):** Extract domain ports, break god-modules, enforce unidirectional dependencies, and eliminate duplicated business logic incrementally chunk by chunk.

## Part 2: External LLM / Human Spec Audit Matrix

When handed a spec, PRD, or architecture plan written elsewhere, interrogate these 8 failure modes:
1. **Hallucinated or Stale Tech:** Unverified library versions, deprecated APIs, or non-existent framework features (flag for `engg-research`).
2. **Missing Non-Goals & Scope Bloat:** Vague ambitions with no V1 cut line.
3. **Unstated Budgets:** Claims of "fast" or "scalable" with zero numeric latency, frame-time, throughput, memory, or payload bounds.
4. **Broken Trust Boundaries:** Client-side authz/validation assumed safe, missing tenant scoping, or unguarded egress/uploads.
5. **Happy-Path-Only Design:** Zero mention of timeouts, partial failures, retries, idempotency, offline states, or rollback paths.
6. **Leaky / Coupled Architecture:** Domain rules tangled directly into controllers, UI components, ORM models, or game engine hooks.
7. **Migration & Lifecycle Blind Spots:** No zero-downtime migration plan, save-file versioning, secret rotation, or graceful shutdown design.
8. **Untestable Acceptance Criteria:** Prose goals that cannot be translated into deterministic automated tests.

Output a **Tightened Spec Delta** clearly marking: `[KEEP]`, `[REVISE]`, `[ADD — MISSING REQUIREMENT]`, and `[CUT — OVER-ENGINEERED]`.
