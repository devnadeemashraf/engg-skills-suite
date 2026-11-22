---
name: engg-plan
description: Decomposes an approved Engineering Design Doc (EDD), feature spec, hardened roadmap milestone, or deep-audit report into small, atomic, MVP-first vertical execution chunks organized into progressive waves. Each chunk carries a risk tier, gates written as exact commands, a ratchet delta, and a rollback path. Use when breaking down a project into implementation milestones, creating a chunk roadmap, sequencing dependencies, or converting an audit report into an actionable remediation plan.
license: Apache-2.0
metadata:
  version: "2.0.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# MVP-First Chunked Planning Engine

Break complex systems, features, or remediation backlogs into small, vertical, independently testable **Chunks** so a working, hardened walking skeleton ships first and is recursively strengthened in subsequent waves.

## When to Use

- Converting a locked EDD (from `engg-architect`) or a hardened milestone roadmap (from `engg-roadmap`) into executable vertical chunks.
- Breaking down a large new feature or refactor in an existing codebase into safe, atomic increments.
- Turning an `engg-deep-audit` report into remediation chunks for `engg-refactor` and `engg-build`.

## Non-Negotiable Rules

1. **Read template first:** Load `references/chunk-template.md` and the Risk Tiers and Ratchet sections of `references/engineering-constitution.md` before structuring the plan.
2. **Thin vertical slices over horizontal layers:** Never plan "Chunk 1: all DB tables, Chunk 2: all services, Chunk 3: all UI." Every chunk must deliver an end-to-end verifiable vertical slice or a self-contained foundational capability.
3. **No bloated Wave 1:** Wave 1 is the leanest production-grade skeleton—never bundle multi-region failover, secondary caches, or nice-to-have features into Chunk 1.
4. **Right-sized atomic chunks:** Each chunk must be small enough to implement via strict TDD and audit completely in a single focused session (typically 1–5 tightly related files/modules plus tests).
5. **Explicit exit criteria:** Every chunk must define concrete **Definition of Done (DoD)** checks and **Key Edge Cases to Prove in Tests**.
6. **Tier every chunk; gates are commands.** Assign each chunk a risk tier (T0–T3). Its gates are the exact commands that must exit 0 for that tier, never prose like "tests pass". When unsure, pick the higher tier.
7. **Every chunk is reversible and measurable.** State its rollback (usually "revert the commit"; migrations and flags need more), and for brownfield work its **ratchet delta**: which baseline violations it removes. A chunk that can't shrink the baseline or ship a verified behaviour is not a chunk.
8. **Plan to the delivery mode:** read `.engg/delivery.yaml`, or ask the question in `references/delivery-modes.md` first. The mode sets Wave 1, chunk size, the default tier and what goes to the backlog. Record the mode and baseline at the top of the plan.

## Workflow

1. **Ingest Inputs:**
   - Review the approved EDD (`engg-architect`), hardened roadmap (`engg-roadmap`), feature request, or deep-audit `REPORT.md` (`engg-deep-audit`), plus the repository state and `.engg/architecture.yaml`.
   - Identify hard technical dependencies and riskiest unknowns (tackle high-risk architectural seams early).
2. **Organize into Progressive Waves:**
   - **Wave 1 — Production Walking Skeleton (MVP Foundation):** Project structure, fail-fast config, structured logging/telemetry bootstrap, uniform error handling, core contracts, the test/lint/typecheck harness, **pre-commit hooks and CI running the compiled architecture contract and a secret scan**, a local dev runner, and **one complete vertical reference slice** proving the architecture end-to-end.
   - **Wave 2 — Security, Resilience & Quality Hardening:** Authn/authz, input/rate/resource bounds, timeouts/retries/offline recovery, idempotency, graceful shutdown/teardown, and strict CI gates.
   - **Wave 3+ — Domain Features, Adapters & Scale Expansion:** Core business slices, additional swappable adapters, performance optimizations, caching/streaming, migrations, load/soak testing, and deployment automation.
   - _(Brownfield remediation follows the deep-audit waves: **1** safety-net tests + P0 fixes + ratchet baseline; **2** strip list; **3** P1 hardening; **4** moves/splits/merges toward the contract, inside-out; **5** P2/P3 simplification. Structural chunks go to `engg-refactor`; behaviour fixes go to `engg-build`.)_
3. **Define Every Chunk Precisely:**
   - Using `references/chunk-template.md`, specify for each chunk:
     - **Chunk ID & Name**
     - **Wave & Goal (User/System Value Delivered)**
     - **Dependencies (Upstream Chunks)**
     - **Files / Modules Created or Modified**
     - **Design Invariants Applied (SOLID / Hexagonal / Budgets)**
     - **Risk Tier & Gates (exact commands)**
     - **Definition of Done (Concrete Verifiable Criteria)**
     - **Mandatory Edge Cases for the Test Matrix**
     - **Ratchet Delta & Rollback**
4. **Render Dependency Map & Roadmap Table:**
   - Present a clean summary table showing Chunk ID, Wave, Tier, Goal, Dependencies, and Estimated Scope, followed by detailed chunk cards.
   - Highlight parallelizable chunks (if multiple engineers or agents will execute concurrently).
5. **Approval Gate:** Ask the user to approve or adjust the chunk roadmap and confirm which chunk to execute first (defaulting to Chunk 1). Hand off to `engg-build` (new behaviour), `engg-extend` (new slice or adapter), or `engg-refactor` (structural cleanup).

## Gotchas

- **Horizontal slicing:** Building a full persistence layer before any consumer exists hides contract mismatches until late integration.
- **Giant "implement core app" chunks:** If a chunk touches 20 files across 4 domains, split it until each chunk has one clear responsibility and clean rollback boundary.
- **Skipping the test harness in Chunk 1:** Chunk 1 must establish the runnable test, lint, and typecheck commands so every subsequent chunk runs strict TDD effortlessly.
- **Mixing structure and behaviour in one chunk:** "move the repository and add authorization" is two chunks: one `engg-refactor`, one `engg-build`.
