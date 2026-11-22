---
name: engg-build
description: Executes a single implementation chunk using strict Test-First Development (Red-Green-Refactor), with test depth and gates scaled to the chunk's risk tier (property-based tests for parsers and invariants, mutation testing for critical code). Enforces SOLID, DRY, KISS, ATOMIC design, the architecture contract, and production invariants across backend, web, mobile, game, database, and DevOps stacks. Use when implementing a planned chunk, writing new production behaviour test-first, or fixing a defect with a failing test first. For behaviour-preserving cleanup, use engg-refactor.
license: Apache-2.0
metadata:
  version: "2.0.0"
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
2. **Strict test-first order, scaled by tier:** Write the runnable tests **before** the production code, and see them fail for the right reason. The chunk's risk tier (Risk Tiers in `references/engineering-constitution.md`) sets the depth: T1 needs happy-path and boundary tests; T2 and T3 need all five matrix categories; T3 also needs mutation testing on the changed code. Never drop below the tier.
3. **One chunk at a time:** Finish implementing, verifying, and auditing (`engg-audit`) the current chunk before starting the next—unless the user explicitly requests batching.
4. **Zero memory-guessing on libraries:** If adding or upgrading any dependency or calling an unfamiliar API, run `engg-research` first to verify live docs and exact pinned versions.
5. **No shortcuts:** Never swallow errors, bypass type safety (`any`/`unsafe` without documented proof), omit timeouts/bounds, hardcode secrets, or weaken a failing test to make it pass.
6. **The architecture contract is part of green:** if `.engg/architecture.yaml` exists, the compiled enforcer runs with the tests, and a new violation means red. Never touch the ratchet baseline to make room for new code.
7. **Use the open-source toolchain, with consent:** run `scripts/toolcheck.sh` (Windows: `scripts/toolcheck.ps1`) from this skill's folder to see which tools in `references/toolchain.md` are installed, and prefer them over reading code by hand. Never install a missing tool without following `references/tool-consent.md`.
8. **Stay inside the mode and the baseline:** before starting, check the chunk against `.engg/delivery.yaml` (`references/delivery-modes.md`). In `mvp-first` it must serve the `core_flow` or a critical item. With `baseline: existing`, never change the architecture, layout or tooling; log improvements to the backlog instead.

## Workflow

1. **Chunk Contract Verification:**
   - Restate the chunk's Goal, Files/Modules, Contracts, and Definition of Done.
   - Confirm the chunk's risk tier and its gate commands. If the plan has none, assign the tier yourself; when unsure, pick the higher one.
   - Verify no architectural boundary violations (e.g., domain importing transport/UI/DB/engine packages).
   - **Chunk 1 of a project:** wire the harness first. That means formatter, linter, typecheck and test commands; pre-commit hooks (lefthook or pre-commit) running them plus a secret scan; and CI running the same commands plus the compiled architecture contract.
2. **Step 1 — Test Matrix Design (Before Any Code):**
   - Using `references/test-matrix-guide.md`, list concrete test cases for the categories the tier requires (all 5 at T2+):
     1. **Standard / Happy Path**
     2. **Boundary & Input Fuzzing**
     3. **Concurrency, Ordering, State & Idempotency**
     4. **Failure & Fault Injection**
     5. **Security, Isolation & Abuse**
3. **Step 2 — RED (Write Failing Tests First):**
   - Write complete, idiomatic, deterministic test files covering every case in the matrix. Use property-based tests (fast-check, Hypothesis, proptest) for parsers, serializers, money and invariants, where hand-picked cases miss the edges.
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
     - The compiled architecture enforcer (and `ratchet.py check` in brownfield repos)
     - **T3 only:** mutation testing on the changed files (Stryker, mutmut, cargo-mutants, PIT). Surviving mutants mean missing tests: add them, or record why a mutant is equivalent.
6. **Step 5 — Mandatory Audit Handoff:**
   - Immediately transition to `engg-audit` (Mode A) to adversarially review every file created or modified in this chunk before marking it Done or committing.

## Gotchas

- **Test-after drift:** Writing implementation first and tacking on shallow happy-path assertions afterward misses edge cases and produces tightly coupled designs.
- **Tautological mocks:** Mocking every collaborator so tests only verify "function A called mock B" hides serialization, SQL, layout, and concurrency bugs. Test behavior at real boundaries.
- **Scope creep mid-chunk:** If you spot an unrelated defect or future refactor while building, log it in the backlog instead of bloating the current chunk.
- **Ceremony on trivia, shortcuts on risk:** a T0 copy change doesn't need five test categories; a T3 auth change never ships without them. The tier decides, not the mood.
