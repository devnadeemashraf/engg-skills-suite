# Unified Engineering Constitution

Every design document, module, test suite, migration, and deployment artifact produced across this suite must uphold these non-negotiable standards—regardless of language, runtime, platform, or product surface.

## 1. Timeless Software Design Principles

- **SOLID (Strictly Enforced):**
  - **Single Responsibility (SRP):** Every module, class, function, component, or shader has one clear reason to change.
  - **Open/Closed (OCP):** Extend behavior via composition, ports/interfaces, or strategy tables—not by editing sprawling `switch`/`if-else` chains.
  - **Liskov Substitution (LSP):** Any adapter or implementation of an interface must honor its exact preconditions, postconditions, error contracts, and invariants—proven by shared contract tests.
  - **Interface Segregation (ISP):** Depend on narrow, consumer-owned interfaces (1–4 cohesive methods), never bloated god-interfaces.
  - **Dependency Inversion (DIP):** Core domain logic depends only on abstractions (ports). Frameworks, databases, UI toolkits, engines, and SDKs live at the outer edge (adapters).
- **DRY (Knowledge, Not Coincidental Code):** Never duplicate business rules, schemas, validation invariants, or constants. Prefer a small amount of explicit local clarity over premature, tangled abstractions that couple unrelated domains.
- **KISS (Aggressive Simplicity):** Pick the simplest architecture that satisfies verified requirements and budgets. Reject speculative generality, unnecessary indirection, and resume-driven complexity.
- **ATOMIC (Modular & Incremental):**
  - **Atomic Design & Modules:** Compose complex systems from small, pure, deterministic building blocks (atoms -> molecules -> domain slices/features).
  - **Atomic State Transitions:** Mutations either complete cleanly or roll back cleanly; no half-written records, torn UI states, or dangling resources.
  - **Atomic Commits & Chunks:** Every change unit delivers one reviewable, testable, reversible increment.
- **Architectural Discipline:**
  - Prefer **Hexagonal (Ports & Adapters)** or **Clean Architecture** for services and apps; **Data-Oriented / ECS / Scene-Graph boundaries** for real-time games; **Composable Modules** for IaC.
  - Enforce **unidirectional dependency flow**: outer layers depend inward; domain core has zero framework, I/O, or platform imports.
  - Apply **GoF & Distributed Patterns** deliberately (Strategy, Factory, Adapter, Repository, Outbox, Circuit Breaker, State Machine, Observer/Event Bus)—never ceremonially.

## 2. Five Production Engineering Invariants

1. **Explicit Contracts First:** Strongly typed boundaries, versioned schemas/APIs, strict validation at every trust boundary, and deterministic error envelopes. Never pass untyped maps across architectural layers.
2. **Defense-in-Depth Security:** Zero-trust defaults, least privilege, explicit authn/authz checks at data boundaries, strict input/payload bounds, safe secret handling, constant-time secret comparisons, and zero PII/secrets in logs, traces, crash dumps, or user errors.
3. **Bounded Everything:** Explicit timeouts, context cancellation, pagination/batch caps, memory/cache ceilings, connection/thread pool limits, frame-time/draw-call budgets, and backpressure on every I/O or compute hot path.
4. **Observable by Default:** Structured telemetry (JSON logs with correlation/trace IDs, RED/USE or UX/frame metrics, distributed tracing where applicable), explicit health/readiness signals, and actionable error context.
5. **Graceful Lifecycle:** Fail fast on invalid startup configuration, deterministic initialization order, idempotent mutations/deployments, clean dependency injection, and graceful shutdown/teardown that drains in-flight work and releases all handles.

## 3. Code Style & Readability Standards

- **Self-Documenting Structure:** Short cohesive functions, early returns/guard clauses over deep nesting, explicit naming that expresses domain intent, and immutable-by-default data where idiomatic.
- **Comments Explain "Why", Never "What":** Document invariants, non-obvious trade-offs, concurrency ordering guarantees, and protocol quirks—not line-by-line narration.
- **Zero Silent Failures:** Never swallow errors, ignore return codes, or use bare catch-all blocks. Every error is handled, enriched with context, or explicitly propagated.
- **Deterministic Tests:** Zero wall-clock flakiness, zero real `sleep()` calls, zero execution-order coupling, and real/ephemeral integration boundaries over brittle tautological mocks.
