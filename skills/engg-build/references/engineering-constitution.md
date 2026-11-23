# Unified Engineering Constitution

Every design document, module, test suite, migration, and deployment artifact produced across this suite must uphold these standards, whatever the language, runtime, platform, or product surface.

**A standard that nothing checks is a suggestion.** Each principle below names how it is checked: a tool, a test, or a citation a reviewer can verify. When you claim a principle holds, show that check.

## 1. Timeless Software Design Principles

- **SOLID:**
  - **Single Responsibility (SRP):** Every module, class, function, component, or shader has one clear reason to change. _Checked by:_ complexity and size limits (cyclomatic complexity, file and function length) plus review.
  - **Open/Closed (OCP):** Extend behaviour through composition, ports/interfaces, or strategy tables, not by editing sprawling `switch`/`if-else` chains. _Checked by:_ review; a growing branch count in hotspot reports.
  - **Liskov Substitution (LSP):** Every implementation of an interface honours its exact preconditions, postconditions, error contracts, and invariants. _Checked by:_ shared contract tests run against every implementation.
  - **Interface Segregation (ISP):** Depend on narrow, consumer-owned interfaces (1–4 cohesive methods), never god-interfaces. _Checked by:_ review; fan-out limits.
  - **Dependency Inversion (DIP):** Core domain logic depends only on abstractions (ports). Frameworks, databases, UI toolkits, engines, and SDKs live at the outer edge (adapters). _Checked by:_ an architecture rule that runs in CI (layer and import rules).
- **DRY (knowledge, not coincidental code):** Never duplicate business rules, schemas, validation invariants, or constants. Prefer a little explicit local clarity over premature abstractions that couple unrelated domains. _Checked by:_ a duplication detector on changed code, then review of each clone.
- **KISS:** Pick the simplest design that meets verified requirements and budgets. Reject speculative generality, needless indirection, and résumé-driven complexity. _Checked by:_ review; an abstraction with one implementation and no planned second is a finding.
- **YAGNI and deletion:** Code that is not used is a liability: it must be read, secured, and kept compiling. Delete unused files, exports, dependencies, flags, and configs. _Checked by:_ dead-code and unused-dependency tools, confirmed by a second signal (see §4).
- **ATOMIC:**
  - **Atomic modules:** Compose systems from small, pure, deterministic building blocks.
  - **Atomic state transitions:** Mutations complete cleanly or roll back cleanly: no half-written records, torn UI states, or dangling resources. _Checked by:_ fault-injection tests.
  - **Atomic commits and chunks:** Each change delivers one reviewable, testable, reversible increment. _Checked by:_ one Conventional Commit title describes the whole change.
- **Architectural discipline:**
  - Prefer **Hexagonal (Ports & Adapters)** or **Clean Architecture** for services and apps, **data-oriented / ECS / scene-graph boundaries** for real-time games, and **composable modules** for infrastructure code. Default to a modular monolith until budgets prove otherwise.
  - Dependencies flow one way: outer layers depend inward, and the domain core has no framework, I/O, or platform imports. _Checked by:_ the architecture rule in CI.
  - Apply patterns (Strategy, Factory, Adapter, Repository, Outbox, Circuit Breaker, State Machine, Observer) deliberately, never ceremonially.

## 2. Five Production Engineering Invariants

1. **Explicit contracts first:** Strongly typed boundaries, versioned schemas and APIs, strict validation at every trust boundary, and deterministic error envelopes. Never pass untyped maps across layers. _Checked by:_ strict typechecker, schema validation tests, contract tests.
2. **Defence-in-depth security:** Zero-trust defaults, least privilege, authn/authz checks at data boundaries, strict input and payload bounds, safe secret handling, constant-time secret comparison, and no PII or secrets in logs, traces, crash dumps, or user-facing errors. _Checked by:_ static security analysis, secret scanning, dependency vulnerability scanning, abuse-case tests.
3. **Bounded everything:** Explicit timeouts, cancellation, pagination and batch caps, memory and cache ceilings, pool limits, frame-time budgets, and backpressure on every I/O or compute hot path. _Checked by:_ static-analysis rules for missing timeouts where available, plus review and load tests on budgeted paths.
4. **Observable by default:** Structured logs with correlation or trace IDs, RED/USE or UX/frame metrics, tracing where it applies, health and readiness signals, and actionable error context. _Checked by:_ review; a test that asserts key log or metric emission on critical paths.
5. **Graceful lifecycle:** Fail fast on invalid startup config, deterministic initialisation order, idempotent mutations and deployments, clean dependency injection, and shutdown that drains in-flight work and releases every handle. _Checked by:_ startup-config tests, shutdown tests, idempotency tests.

## 3. Code Style & Readability

- **Self-documenting structure:** Short cohesive functions, guard clauses over deep nesting, names that express domain intent, immutable-by-default data where idiomatic. _Checked by:_ formatter and linter in pre-commit and CI.
- **Comments explain why, never what:** Document invariants, non-obvious trade-offs, ordering guarantees, and protocol quirks.
- **No silent failures:** Never swallow errors, ignore return codes, or use bare catch-alls. Handle, enrich, or propagate every error. _Checked by:_ linter rules for ignored errors and empty catch blocks.
- **Deterministic tests:** No wall-clock flakiness, no real `sleep()`, no order coupling. Prefer real or ephemeral integration boundaries over tautological mocks.

## 4. Evidence Protocol (accuracy)

1. **Cite everything:** every finding or claim points to `file:line`, a tool result (rule ID, violation, graph edge), or a primary-source URL.
2. **"Verified" means a command ran and exited 0.** Show the command and the relevant tail of its output. Never report a check as passing without running it.
3. **Two signals before destructive action:** before declaring code dead, or deleting or moving it, at least two independent signals must agree: a static tool, a reference search that includes strings, reflection, and config, coverage data, or graph fan-in of zero.
4. **Tool output is evidence, not verdict:** triage every tool finding as `TRUE`, `FALSE-POSITIVE: <reason>`, or `NEEDS-HUMAN`.
5. **Facts that change come from live sources only:** versions, flags, API signatures, and advisories are looked up, never recalled. When no live source is reachable, still write the work: mark each unchecked claim `unverified` and list it for the human. Don't refuse, and don't present it as checked.

## 5. Risk Tiers (rigour proportional to risk)

Assign each change a tier, and run the gates for that tier and every tier below it.

| Tier | Typical change | Required gates |
|---|---|---|
| **T0 Trivial** | Docs, copy, a config value | Formatter + linter |
| **T1 Standard** | Internal logic, a UI component | T0 + unit tests (happy path + boundaries) + typecheck + architecture rule |
| **T2 Sensitive** | Public API, persistence, concurrency, a performance-budgeted path | T1 + all five test-matrix categories + contract tests + adversarial review |
| **T3 Critical** | Authn/authz, money, PII, migrations, crypto, infrastructure | T2 + mutation testing on changed code + static security, secret, and dependency scans + a threat-model note + explicit human approval |

When unsure, pick the higher tier. Never lower a tier to get a change through.

## 6. Ratchet (adopting standards on existing code)

1. Run each enforcer once and record today's violations as a committed **baseline**.
2. CI fails on any **new** violation; existing ones are tracked, not ignored.
3. Every remediation chunk must **shrink** the baseline and may never grow it.
4. Never weaken a rule, raise a threshold, or add a suppression to make a check pass. Fix the code, or record an explicit, reviewed exception with a reason.

## 7. Authorship

Code, comments, commits, pull requests, docs and release notes carry **no AI attribution**: no `Co-Authored-By` or `Generated-by` trailer naming an AI tool or model, no "generated with" line, and no mention of an AI tool as an author. This holds even when a tool adds one by default. _Checked by:_ `scripts/attribution_check.py` in the commit-msg hook (`--message-file`) and in CI (`--range`).
