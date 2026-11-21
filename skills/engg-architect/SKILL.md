---
name: engg-architect
description: Runs a rigorous, tech-agnostic Staff-level architectural grill session and produces a decision-complete Engineering Design Doc (EDD) and ADRs for any software surface (backend, web client, mobile client, game client, database, infrastructure/DevOps). Use when designing a new system, scaffolding a project, locking technical contracts, or formalizing architecture before planning or coding.
license: Apache-2.0
metadata:
  version: "1.0.0"
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

1. **No premature code:** Never generate implementation files or boilerplate until the EDD is explicitly approved by the user.
2. **Load references before starting:** Always read `references/engineering-constitution.md`, `references/grill-bank-core.md`, and the matching section(s) of `references/domain-profiles.md` before Round 1.
3. **Stay genuinely tech-agnostic until locked:** Never silently assume a language, framework, engine, database, or cloud provider. Ask or propose one concrete, justified recommendation and get sign-off.
4. **Verify live versions when selecting a stack:** If concrete libraries/frameworks/runtimes are chosen, invoke `engg-research` (or verify against current docs) rather than guessing versions from memory.
5. **Enforce design invariants:** Every EDD must explicitly codify SOLID, DRY, KISS, ATOMIC boundaries, Hexagonal/Clean dependency flow, explicit contracts, security controls, and hard resource/performance budgets.

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
4. **Produce the Locked Engineering Design Doc (EDD) & Key ADRs:**
   - Goals & Explicit Non-Goals
   - System & Module Architecture (diagram/tree enforcing dependency direction and Ports & Adapters)
   - Chosen Tech Stack & Rationale (with pinned target versions)
   - Explicit Contracts (API/Events/IPC/State Schemas) & Data/Persistence Model
   - Threat Model & Defense-in-Depth Controls
   - Hard Performance, Latency/Frame, & Resource Budgets
   - Observability, Testing Strategy & Lifecycle/Deployment Model
   - Architecture Decision Records (ADRs) for every major irreversible choice
   - Recorded Assumptions & Accepted Trade-Offs
5. **Approval Gate:** Ask the user to explicitly approve or revise the EDD. Upon approval, hand off to `engg-plan` to decompose the EDD into MVP-first execution chunks.

## Gotchas

- **Soft-pedaling the grill:** Asking 3 surface-level questions and jumping into code defeats the entire workflow. Dig until hidden constraints surface.
- **Over-engineering V1:** Enforce KISS. Do not prescribe microservices, distributed event meshes, or custom engines when a modular monolith or standard framework satisfies the stated budgets.
- **Stack leakage:** Do not sneak assumptions from one ecosystem into a generic discussion before the stack is chosen.
