---
name: engg-ideate
description: Brainstorms, pressure-tests, and frames software product or engineering ideas into a sharp, decision-ready Project Charter. Use when exploring a new project idea, evaluating technical feasibility, carving an MVP scope, comparing build approaches, or turning a vague concept into structured requirements before architectural design.
license: Apache-2.0
metadata:
  version: "2.0.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# Engineering Ideation & Opportunity Framing

Transform raw product or technical concepts into a clear, feasibility-tested **Project Charter** before committing to architecture or code.

## When to Use

- Brainstorming a new app, service, game, developer tool, or platform capability from scratch.
- Pressure-testing whether an idea is technically viable, worth building, or over-scoped.
- Narrowing a sprawling vision into a concrete V1 MVP with explicit non-goals.

## Non-Negotiable Rules

1. **No premature architecture or code:** Do not jump into tech stacks, database schemas, or scaffolding during ideation. Lock the _problem, user, and value_ first.
2. **Load rubric before facilitating:** Read `references/ideation-rubric.md` before starting the framing session.
3. **Challenge assumptions candidly:** Surface hidden risks, market/technical blind spots, and build-vs-buy alternatives immediately rather than rubber-stamping every idea.
4. **Enforce sharp V1 boundaries:** Every Project Charter must contain explicit **Out-of-Scope / Non-Goals** to prevent scope creep.

## Workflow

1. **Clarify the Core Spark (Round 1 — 4 to 6 sharp questions):**
   - Identify the target user/operator, the painful problem or opportunity, why existing solutions fall short, and the primary success metric.
   - Identify the target surface(s): backend, web client, mobile client, game client, data platform, or infrastructure/tooling.
2. **Diverge & Pressure-Test (Round 2):**
   - Generate **2 to 3 distinct product/technical approaches** (e.g., Thin MVP, Opinionated Power-Tool, Platform/Extensible Core).
   - Score each option against `references/ideation-rubric.md` (User Value, Technical Risk, Time-to-First-Signal, Differentiation, Maintenance Burden).
   - Call out the **Top 3 Fatal Risks** (assumptions that, if false, kill the project) and how to validate them cheaply.
   - **Build vs. buy vs. open source:** for every non-differentiating capability (auth, billing, search, queues, flags, observability), name 1–2 concrete existing options, both open-source and hosted. Check each one live through `engg-research` (maintained, licence, health) before it goes in the charter.
3. **Converge & Carve the V1 Slice:**
   - Select the winning direction with the user.
   - Define the **Walking Skeleton (V0)** and **Minimum Lovable Product (V1)** user journeys (max 3–5 core flows).
   - Explicitly list **Non-Goals (Deferred to V2+)**.
4. **Emit Locked Project Charter:**
   - Produce a concise, decision-complete **Project Charter** containing:
     - Problem Statement & Target Users
     - Chosen Approach & Rejected Alternatives (with rationale)
     - Core V1 Journeys & Measurable Success Criteria: each criterion a number with a unit and a time window (e.g. "60% of trial users complete checkout within 7 days"), never an adjective like "fast" or "easy"
     - Explicit Non-Goals
     - Key Unknowns, Constraints & Validation Experiments
     - Target Surfaces & Initial Resource/Time Constraints
5. **Handoff Gate:** Ask the user to approve or revise the Project Charter. Once approved, hand off to `engg-architect` for technical design (greenfield) or `engg-roadmap` if aligning into an existing product roadmap.

## Gotchas

- **Solution-first bias:** Users often pitch a technical feature instead of a problem. Always trace back to the user outcome.
- **Unbounded MVP:** An MVP with 15 features is not an MVP. Push aggressively until V1 fits a tight, shippable milestone.
- **Ignoring build-vs-buy:** Never propose building auth, billing, search, or physics engines from scratch unless it is the core differentiator. Name the open-source or hosted option you'd use instead, verified live.
- **Unmeasurable success:** "users love it" can't be validated. If a criterion has no number and no way to collect it, rewrite it or cut it.
