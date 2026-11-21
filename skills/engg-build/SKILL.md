---
name: engg-build
description: Executes a single implementation chunk using strict Test-First Development (Red-Green-Refactor), enforcing SOLID, DRY, KISS, ATOMIC design principles, Hexagonal boundaries, and production invariants across backend, web, mobile, game, database, and DevOps stacks. Use when implementing a planned chunk, writing production code with thorough tests, or building a component from scratch.
license: Apache-2.0
metadata:
  version: "1.0.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# Strict TDD Chunk Builder

Implement one planned chunk at a time using disciplined **Red -> Green -> Refactor** engineering, proving correctness across normal and hostile edge cases before moving forward.

## When to Use

- Implementing a chunk from an approved roadmap (`engg-plan`).
- Building a well-specified module, service slice, UI component, mobile screen, game system, or IaC module with rigorous test coverage.

## Non-Negotiable Rules

1. **Load standards first:** Read `references/engineering-constitution.md`, `references/test-matrix-guide.md`, and the matching stack section in `references/domain-standards.md` before writing any code.
2. **Strict test-first order:** Always enumerate the 5-category Test Matrix and write the complete runnable test suite **before** writing production implementation code.
3. **One chunk at a time:** Finish implementing, verifying, and auditing (`engg-audit`) the current chunk before starting the next—unless the user explicitly requests batching.
4. **Zero memory-guessing on libraries:** If adding or upgrading any dependency or calling an unfamiliar API, run `engg-research` first to verify live docs and exact pinned versions.
5. **No shortcuts:** Never swallow errors, bypass type safety (`any`/`unsafe` without documented proof), omit timeouts/bounds, hardcode secrets, or weaken a failing test to make it pass.

## Workflow

1. **Chunk Contract Verification:**
   - Restate the chunk's Goal, Files/Modules, Contracts, and Definition of Done.
   - Verify no architectural boundary violations (e.g., domain importing transport/UI/DB/engine packages).
2. **Step 1 — Test Matrix Design (Before Any Code):**
   - Using `references/test-matrix-guide.md`, list concrete test cases across all 5 categories:
     1. **Standard / Happy Path**
     2. **Boundary & Input Fuzzing**
     3. **Concurrency, Ordering, State & Idempotency**
     4. **Failure & Fault Injection**
     5. **Security, Isolation & Abuse**
3. **Step 2 — RED (Write Failing Tests First):**
   - Write complete, idiomatic, deterministic test files covering every case in the matrix.
   - Run the test suite (or provide exact command) to confirm tests fail for the _right reason_ (missing implementation, not broken test harness).
4. **Step 3 — GREEN (Minimal Clean Production Implementation):**
   - Write the clean, cohesive production code required to satisfy all tests while upholding `references/engineering-constitution.md` (SOLID, DRY, KISS, ATOMIC, explicit contracts, bounded resources, structured observability).
   - Run the test suite and iterate until 100% green.
5. **Step 4 — REFACTOR (Tighten Without Changing Behavior):**
   - Eliminate duplication of business logic, flatten deep nesting with guard clauses, sharpen names, confirm narrow interfaces, and verify zero dead code or debug leftovers.
   - Re-run the full verification suite:
     - Unit + integration + contract tests (with race detection/sanitizers where supported)
     - Coverage report
     - Formatter, strict linter, typechecker, and static security scan
6. **Step 5 — Mandatory Audit Handoff:**
   - Immediately transition to `engg-audit` (Mode A) to adversarially review every file created or modified in this chunk before marking it Done or committing.

## Gotchas

- **Test-after drift:** Writing implementation first and tacking on shallow happy-path assertions afterward misses edge cases and produces tightly coupled designs.
- **Tautological mocks:** Mocking every collaborator so tests only verify "function A called mock B" hides serialization, SQL, layout, and concurrency bugs. Test behavior at real boundaries.
- **Scope creep mid-chunk:** If you spot an unrelated defect or future refactor while building, log it in the backlog instead of bloating the current chunk.
