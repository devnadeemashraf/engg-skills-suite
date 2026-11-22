---
name: engg-extend
description: Extends an existing or in-progress codebase cleanly by either adding a new vertical business feature module or implementing a new swappable infrastructure/platform adapter behind a port interface with shared contract tests. Use when adding features, integrating new databases/APIs/SDKs/engines, or swapping adapters without breaking architectural boundaries.
license: Apache-2.0
metadata:
  version: "2.0.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# Codebase Extension: Vertical Slices & Swappable Adapters

Grow an in-progress codebase rapidly without architectural drift by enforcing strict vertical feature slicing and contract-tested Ports & Adapters.

## When to Use

- **Mode A — Add Vertical Feature Module:** Adding a new domain capability/feature end-to-end across an existing project (backend endpoint + service + repo, web/mobile feature slice, game gameplay module).
- **Mode B — Add/Swap Infrastructure Adapter:** Integrating or replacing a concrete technology (database, cache, queue, auth provider, payment gateway, storage SDK, UI/rendering backend, analytics SDK) behind a domain-owned port interface.

## Non-Negotiable Rules

1. **Read references first:** Load `references/engineering-constitution.md` and `references/contract-test-patterns.md` before modifying code.
2. **Match existing repo conventions strictly:** Inspect existing sibling modules/adapters first so naming, error types, DI wiring, and folder layout remain 100% consistent.
3. **Never leak adapter details into core:** Domain code must never import SDK types, ORM models, HTTP frameworks, or vendor error codes. Map all external errors and DTOs at the adapter boundary.
4. **Shared Contract Tests are mandatory for adapters:** Every port interface must have a reusable contract test suite that runs identically against fakes/in-memory implementations and every real adapter (proving Liskov Substitution).
5. **Strict TDD + Post-Audit:** Follow `engg-build` test-first discipline and finish with `engg-audit` (Mode A).
6. **Use the open-source toolchain, with consent:** run `scripts/toolcheck.sh` (Windows: `scripts/toolcheck.ps1`) from this skill's folder to see which tools in `references/toolchain.md` are installed, and prefer them over reading code by hand. Never install a missing tool without following `references/tool-consent.md`.
7. **Respect the architecture contract:** if `.engg/architecture.yaml` exists (schema: `references/architecture-contract.md`), use it to place the new slice or adapter in the right layer and module. Before declaring done, run `scripts/compile_contract.py --check` and then the enforcer command it prints. If the change needs a new layer or dependency direction, change the contract with the owner first; never work around it.

## Workflow — Mode A: Vertical Feature Module

1. **Inspect Existing Architecture:** Pick 1–2 reference vertical slices with the graph rather than browsing: `graphify query "<feature like the new one>"` and `graphify explain "<its entry point>"` show the files and wiring. Read those slices to align with conventions, error envelopes, validation, and DI wiring. Place the new slice in the layers and module `.engg/architecture.yaml` prescribes.
2. **Define Slice Contract:** Lock explicit input/output DTOs, domain types/invariants, error cases, authorization rules, and any new port methods needed.
3. **Write Tests First:**
   - Domain unit tests (pure business rules & invariants).
   - Transport/UI/boundary tests (validation, authz, error mapping, state transitions).
   - End-to-end vertical integration test covering the complete slice.
4. **Implement Inside-Out:**
   - Domain entities & rules -> Application use-case/service -> Adapter persistence/client implementation -> Transport/UI handler -> Composition root wiring.
5. **Verify & Audit:** Run the gates for the slice's risk tier (Risk Tiers in `references/engineering-constitution.md`): tests, lint, typecheck, and the compiled architecture enforcer, which must report **zero new violations**. New code never enters a ratchet baseline. Then execute `engg-audit`.

## Workflow — Mode B: Swappable Infrastructure Adapter

1. **Inspect or Define the Port Interface:** Verify the interface is narrow (ISP), domain-typed, context/cancellation-aware, and free of vendor leakage.
2. **Research Live SDK/Driver Details:** Run `engg-research` to confirm exact pinned package version, pooling/timeout defaults, and known pitfalls.
3. **Write or Extend the Shared Port Contract Test Suite:**
   - Using `references/contract-test-patterns.md`, ensure every behavioral invariant (CRUD/semantics, not-found, conflict/uniqueness, concurrency, timeout/cancellation, resource cleanup) is tested via a parameterized factory.
4. **Implement Adapter & Wiring:**
   - Implement explicit timeouts, bounded pools, structured error translation, telemetry hooks, and health/readiness check integration.
   - Wire into composition root via config/feature toggle so swapping implementations requires zero domain edits.
5. **Run Contract Suite + Audit:** Execute the shared contract suite against both the reference fake and the new real adapter (ephemeral container/emulator), then run `engg-audit`.

## Gotchas

- **Anemic pass-through wrappers:** Do not expose a raw SQL/ORM query builder or vendor SDK client through a port—that destroys swappability.
- **Cross-slice spaghetti:** Feature modules must communicate through explicit public contracts/events, never by reaching directly into another module's internal tables or private state. The contract's `modules` rule catches this; don't add an exception to get past it.
- **Copying a bad neighbour:** "matching repo conventions" means the conventions the contract endorses. If the nearest slice breaks the contract (check the deep-audit report or the enforcer), copy a clean one instead and log the bad one for `engg-refactor`.
