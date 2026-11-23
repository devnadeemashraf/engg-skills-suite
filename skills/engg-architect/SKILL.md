---
name: engg-architect
description: Runs a rigorous, tech-agnostic Staff-level architectural grill session and produces a decision-complete Engineering Design Doc (EDD) and ADRs for any software surface (backend, web client, mobile client, game client, database, infrastructure/DevOps). Use when designing a new system, scaffolding a project, locking technical contracts, or formalizing architecture before planning or coding.
license: Apache-2.0
metadata:
  version: "2.0.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# Universal System Architect & Grill Protocol

Eliminate architectural ambiguity and baked-in technical debt before a single line of code is written by executing a structured interrogation and locking a decision-complete Engineering Design Doc (EDD).

## When to Use

- Architecting a new backend service, web app, mobile app, game client, data pipeline, infrastructure platform, or full-stack monorepo.
- Designing a reusable production template or greenfield system foundation.
- Formalizing architecture and Architecture Decision Records (ADRs) from an approved Project Charter or rough prompt.

## Non-Negotiable Rules

1. **Design before code:** writing the EDD, ADRs and contract files is this skill's job, so write them as decisions lock. What waits for the user's explicit approval is implementation code and scaffolding.
2. **Load references before starting:** read `references/engineering-constitution.md` §1–2, `references/grill-bank-core.md`, and only the `references/domain-profiles.md` sections for the active surfaces, before Round 1.
3. **Stay genuinely tech-agnostic until locked:** Never silently assume a language, framework, engine, database, or cloud provider. Ask or propose one concrete, justified recommendation and get sign-off.
4. **Verify live versions when selecting a stack:** If concrete libraries/frameworks/runtimes are chosen, invoke `engg-research` (or verify against current docs) rather than guessing versions from memory.
5. **Enforce design invariants:** Every EDD must explicitly codify SOLID, DRY, KISS, ATOMIC boundaries, Hexagonal/Clean dependency flow, explicit contracts, security controls, and hard resource/performance budgets.
6. **Tools, with consent:** run `scripts/toolcheck.sh <tools>` (Windows: `scripts/toolcheck.ps1`) for the tools this step needs, and prefer them over reading code by hand. Read only those tools' rows in `references/toolchain.md`, and `references/tool-consent.md` only before proposing an install.
7. **Architecture is a machine-checked contract, not just a diagram:** every locked EDD ships with `.engg/architecture.yaml` written to the schema in `references/architecture-contract.md`. Compile it with `scripts/compile_contract.py` and never hand-write enforcer configs.
8. **Design only what isn't fixed:** with `baseline: existing` (`references/delivery-modes.md` §5), the current architecture and tooling are the baseline. Write the contract as it is and extend it. When the user explicitly asks for a redesign, set `baseline: redo` and redesign, reusing the code that still fits.
9. **Working loop** (`references/working-loop.md`): start from `scripts/brief.py`, find files with `scripts/map.py` before reading them, run gates with `scripts/check.py`, and finish by updating `docs/HANDOFF.md` (§3). The user's explicit request outranks these defaults (§5). No AI attribution anywhere; `scripts/attribution_check.py` checks it.

## Workflow

1. **Surface Identification & Setup:**
   - Identify all active surfaces (Backend, Web, Mobile, Game, Data, Infra/DevOps) and whether this is a reusable template or specific product.
2. **Execute 3 to 5 Focused Grill Rounds (6–10 sharp questions per round — never a 60-question wall):**
   - **Round 1 — Mission, Domain & Architectural Boundaries:** Core workflows, explicit non-goals, bounded contexts, multi-surface boundaries, monorepo vs. polyrepo.
   - **Round 2 — Scale, Performance Budgets & Failure Modes:** Traffic/user load, latency or frame-time budgets (p95/p99, LCP/INP, 60/120fps), memory/binary/storage caps, offline/degraded behavior, RPO/RTO.
   - **Round 3 — Tech Stack, Contracts & State/Data Architecture:** Language/runtime/engine, contract-first schemas, state management or datastore choices, consistency model, migrations/save-versioning, caching, idempotency.
   - **Round 4 — Security, Identity, Privacy & Abuse Model:** Authn/authz, tenancy/isolation, secret management, client trust boundaries, compliance, rate limits, anti-tamper/abuse defenses.
   - **Round 5 — Observability, Testing & Operational Lifecycle:** Telemetry/logging/metrics/crash reporting, local dev setup, CI/CD quality gates, deployment runtime, rollback strategy.
3. **Apply Staff Engineer Pushback:**
   - Reject hand-wavy answers ("standard auth", "make it scalable", "normal UI", "add tests later").
   - Surface contradictions immediately (e.g., "zero-latency offline mobile sync" + "strict global linearizability").
   - When the user says "pick best practice," propose one concrete opinionated default, explain the trade-off in one sentence, and log it under **Recorded Assumptions**.
4. **Write the Engineering Design Doc to `docs/EDD.md`, plus ADRs.** Number its top-level sections (`## 3. Contracts`) so chunks can cite `EDD §3`. It is the project's living big picture: a reader new to the code should find each module's job, public entry and dependencies within one screen. It holds:
   - Goals & Explicit Non-Goals
   - System & Module Architecture: C4 **context** and **container** views (Mermaid, so they live in the repo and diff in review) plus a module tree showing dependency direction and Ports & Adapters. Default to a **modular monolith**; split into services only when a stated budget or team boundary requires it, and write the ADR that says which.
   - Chosen Tech Stack & Rationale (with pinned target versions)
   - Explicit Contracts (API/Events/IPC/State Schemas) & Data/Persistence Model
   - Threat Model & Defense-in-Depth Controls, with the target **OWASP ASVS 5.0 level** (L1, L2 or L3, justified by the data and the exposure) and the requirement areas it commits to, cited with the version (e.g. `v5.0.0-6.2.1`)
   - Hard Performance, Latency/Frame, & Resource Budgets
   - Observability, Testing Strategy & Lifecycle/Deployment Model
   - Architecture Decision Records for every major irreversible choice, in **MADR 4.0** form (context and problem, decision drivers, considered options, decision outcome, consequences), stored as `docs/decisions/NNNN-<slug>.md`
   - Recorded Assumptions & Accepted Trade-Offs
5. **Write and Compile the Architecture Contract:**
   - Translate the module architecture into `.engg/architecture.yaml`: layers inner -> outer, minimal `may_import`, `external` limits on the domain, `modules` isolation for vertical slices, and `targets` for the chosen stack.
   - **Brownfield:** first draft the as-is contract from the directory layout and the dependency graph (graphify or the native enforcer). Agree the to-be contract with the owner, and record the gap as a migration delta. Existing violations become a ratchet baseline; never loosen the contract to hide them.
   - Run `scripts/compile_contract.py` and show its coverage report. Any rule marked NOT COVERED for a target must appear in the EDD with how it will be checked instead.
   - Run the generated enforcer once and report the result (clean, or the violation count for the baseline).
6. **Approval Gate:** Update `docs/HANDOFF.md` (Stage `architect`, Next: approve the EDD, then `engg-plan`). Ask the user to explicitly approve or revise the EDD and the contract. Upon approval, hand off to `engg-plan` to decompose the EDD into MVP-first execution chunks. Wiring the enforcer into pre-commit and CI belongs in Chunk 1.

## Gotchas

- **Soft-pedaling the grill:** Asking 3 surface-level questions and jumping into code defeats the entire workflow. Dig until hidden constraints surface.
- **Over-engineering V1:** Enforce KISS. Do not prescribe microservices, distributed event meshes, or custom engines when a modular monolith or standard framework satisfies the stated budgets.
- **Stack leakage:** Do not sneak assumptions from one ecosystem into a generic discussion before the stack is chosen.
