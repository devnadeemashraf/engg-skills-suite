---
name: engg-plan
description: Decomposes an approved Engineering Design Doc (EDD), feature spec, or codebase hardening report into small, atomic, MVP-first vertical execution chunks organized into progressive hardening waves. Use when breaking down a project into implementation milestones, creating a chunk roadmap, sequencing dependencies, or converting an audit report into an actionable remediation plan.
license: Apache-2.0
metadata:
  version: "1.0.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# MVP-First Chunked Planning Engine

Break complex systems, features, or remediation backlogs into small, vertical, independently testable **Chunks** so a working, hardened walking skeleton ships first and is recursively strengthened in subsequent waves.

## When to Use

- Converting a locked EDD (from `engg-architect`) or a hardened milestone roadmap (from `engg-roadmap`) into executable vertical chunks.
- Breaking down a large new feature or refactor in an existing codebase into safe, atomic increments.
- Turning a brownfield hardening audit (from `engg-audit`) into a prioritized remediation sequence.

## Non-Negotiable Rules

1. **Read template first:** Load `references/chunk-template.md` before structuring the plan.
2. **Thin vertical slices over horizontal layers:** Never plan "Chunk 1: all DB tables, Chunk 2: all services, Chunk 3: all UI." Every chunk must deliver an end-to-end verifiable vertical slice or a self-contained foundational capability.
3. **No bloated Wave 1:** Wave 1 is the leanest production-grade skeleton—never bundle multi-region failover, secondary caches, or nice-to-have features into Chunk 1.
4. **Right-sized atomic chunks:** Each chunk must be small enough to implement via strict TDD and audit completely in a single focused session (typically 1–5 tightly related files/modules plus tests).
5. **Explicit exit criteria:** Every chunk must define concrete **Definition of Done (DoD)** checks and **Key Edge Cases to Prove in Tests**.

## Workflow

1. **Ingest Inputs:**
   - Review the approved EDD (`engg-architect`), hardened roadmap (`engg-roadmap`), feature request, or audit report (`engg-audit`), plus existing repository state.
   - Identify hard technical dependencies and riskiest unknowns (tackle high-risk architectural seams early).
2. **Organize into Progressive Waves:**
   - **Wave 1 — Production Walking Skeleton (MVP Foundation):** Project structure, fail-fast config, structured logging/telemetry bootstrap, uniform error handling, core contracts, test & lint harness, local dev runner, and **one complete vertical reference slice** proving the architecture end-to-end.
   - **Wave 2 — Security, Resilience & Quality Hardening:** Authn/authz, input/rate/resource bounds, timeouts/retries/offline recovery, idempotency, graceful shutdown/teardown, and strict CI gates.
   - **Wave 3+ — Domain Features, Adapters & Scale Expansion:** Core business slices, additional swappable adapters, performance optimizations, caching/streaming, migrations, load/soak testing, and deployment automation.
   - _(For Brownfield Remediation: Wave 1 = P0 Blockers & safety-net tests; Wave 2 = P1 High reliability/security/performance fixes; Wave 3 = Architectural tightening & P2 debt.)_
3. **Define Every Chunk Precisely:**
   - Using `references/chunk-template.md`, specify for each chunk:
     - **Chunk ID & Name**
     - **Wave & Goal (User/System Value Delivered)**
     - **Dependencies (Upstream Chunks)**
     - **Files / Modules Created or Modified**
     - **Design Invariants Applied (SOLID / Hexagonal / Budgets)**
     - **Definition of Done (Concrete Verifiable Criteria)**
     - **Mandatory Edge Cases for the Test Matrix**
4. **Render Dependency Map & Roadmap Table:**
   - Present a clean summary table showing Chunk ID, Wave, Goal, Dependencies, and Estimated Scope, followed by detailed chunk cards.
   - Highlight parallelizable chunks (if multiple engineers or agents will execute concurrently).
5. **Approval Gate:** Ask the user to approve or adjust the chunk roadmap and confirm which chunk to execute first (defaulting to Chunk 1). Hand off to `engg-build` (or `engg-extend` for vertical additions).

## Gotchas

- **Horizontal slicing:** Building a full persistence layer before any consumer exists hides contract mismatches until late integration.
- **Giant "implement core app" chunks:** If a chunk touches 20 files across 4 domains, split it until each chunk has one clear responsibility and clean rollback boundary.
- **Skipping the test harness in Chunk 1:** Chunk 1 must establish the runnable test, lint, and typecheck commands so every subsequent chunk runs strict TDD effortlessly.
