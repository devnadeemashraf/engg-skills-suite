---
name: engg-roadmap
description: Grills, reality-checks, re-sequences, and hardens an existing product or engineering roadmap against the actual codebase, delivery constraints, and technical risks, then routes each milestone to the rest of the engineering skill suite (engg-architect, engg-plan, engg-build, engg-extend, engg-refactor, engg-audit, engg-deep-audit, engg-research, engg-debug, engg-data, engg-ship). Use when improving an in-progress roadmap, cutting scope bloat, de-risking milestones, aligning roadmap promises with real code, or accelerating shipping velocity.
license: Apache-2.0
metadata:
  version: "2.1.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# Product & Engineering Roadmap Griller and Hardener

Pressure-test an existing roadmap against engineering reality, strip out drag and hidden risk, re-sequence milestones for fastest validated value, and hand off cleanly into the rest of the engineering suite for execution.

## When to Use

- Auditing and tightening an existing `ROADMAP.md`, milestone backlog, or quarterly/release plan for an in-progress product.
- Accelerating a stalled or bloated project by cutting non-essential scope and eliminating hidden technical prerequisites.
- Re-aligning a roadmap authored by another human or LLM against the real state of the repository before building further.

## Non-Negotiable Rules

1. **Load references before grilling:** Always read `references/engineering-constitution.md`, `references/roadmap-grill-bank.md`, and `references/roadmap-hardening-template.md` before Round 1.
2. **Anchor to repository reality first, with tools:** If a codebase exists, measure it _before_ grilling: `scc` for size per area, `graphify update .` and its `GRAPH_REPORT.md` for the real module structure and hubs, the test and CI configuration, and a recent `engg-deep-audit` `map.md`/`REPORT.md` if one exists. Never critique a roadmap in a vacuum, or from a skim, when real code is available.
3. **Grill interactively before rewriting:** Run **2 to 4 focused Grill Rounds** (5–7 sharp questions per round). Never silently rewrite a roadmap without resolving priority, risk, and scope trade-offs with the owner.
4. **Enforce the 50% Timeline Razor:** Every hardening pass must identify what survives if the delivery window is cut in half, forcing crisp V-Next vs. Deferred boundaries.
5. **Route every hardened milestone into the suite:** Every surviving item must map explicitly to its next execution skill (`engg-research`, `engg-architect`, `engg-deep-audit`, `engg-audit`, `engg-plan`, `engg-build`, `engg-extend`, `engg-refactor`, `engg-data`, `engg-debug`, or `engg-ship`)—never leave vague prose milestones.
6. **Tools, with consent:** run `scripts/toolcheck.sh <tools>` (Windows: `scripts/toolcheck.ps1`) for the tools this step needs, and prefer them over reading code by hand. Read only those tools' rows in `references/toolchain.md`, and `references/tool-consent.md` only before proposing an install.
7. **Respect the delivery mode and the baseline:** read `.engg/delivery.yaml`, or ask the question in `references/delivery-modes.md` if it's missing. In `mvp-first`, Milestone 1 delivers the `core_flow`, and anything that doesn't serve it moves to a later milestone or the backlog. With `baseline: existing`, never schedule redesigns, re-layouts or tool swaps unless the user asked for them.
8. **Working loop** (`references/working-loop.md`): start from `scripts/brief.py`, find files with `scripts/map.py` before reading them, run gates with `scripts/check.py`, and finish by updating `docs/HANDOFF.md` (§3). The user's explicit request outranks these defaults (§5). No AI attribution anywhere; `scripts/attribution_check.py` checks it.

## Workflow

1. **Baseline Reconnaissance (Codebase vs. Roadmap Reality Check):**
   - Read the existing roadmap (e.g., `docs/ROADMAP.md`, issues, or pasted plan).
   - If working in an existing repo, map what is genuinely built, tested, and production-hardened vs. what is partially wired, untested, or assumed. Cite the evidence (file paths, test files, CI jobs, graph communities).
   - **Delivery baseline (DORA):** from git and CI history, estimate deployment frequency, change lead time, change fail rate, failed deployment recovery time, and deployment rework rate (the share of deployments that were unplanned fixes). Where the data doesn't exist, say so: a missing baseline is itself a Milestone-1 prerequisite.
   - Surface immediate **Reality Gaps** (e.g., Milestone 2 assumes auth, migrations, or telemetry that do not exist yet).
2. **Execute 2 to 4 Focused Grill Rounds (`references/roadmap-grill-bank.md`):**
   - **Round 1 — Outcome Sharpness & Reality Gaps:** Target user outcome per milestone, dead-weight items, and mismatches between roadmap claims and actual code.
   - **Round 2 — Scope Razor & Explicit Non-Goals:** Apply the 50% Timeline Razor, expose gold-plating and premature scale, and carve explicit `CUT / DEFER` items.
   - **Round 3 — Risk-First Re-Sequencing & Dependencies:** Pull highest-risk unknowns, architectural seams, and hard prerequisites to the front; split horizontal layers into shippable vertical milestones.
   - **Round 4 — Quality Gates, Budgets & Delivery Readiness:** Attach measurable exit criteria, performance/reliability budgets, migration/rollback needs, and observability gates to every milestone.
3. **Emit Tightened Roadmap Delta (`references/roadmap-hardening-template.md`):**
   - Score the original roadmap (1–5 across Focus, Sequencing, Reality Alignment, Risk Coverage, and Testability).
   - Output an item-by-item **Roadmap Delta** tagged with `[KEEP]`, `[RE-SEQUENCE]`, `[SPLIT]`, `[REVISE]`, `[ADD — PREREQ]`, or `[CUT — DEFER]`.
4. **Lock Living `docs/ROADMAP.md` & Suite Handoff Table:**
   - Once approved, write the hardened roadmap using the template in `references/roadmap-hardening-template.md`, including a **Decisions & Cuts Log** and a **Next-Skill Routing Table**.
   - Create or update `docs/HANDOFF.md` (Stage `plan`, Next: the first milestone and the skill that runs it).
5. **Seamless Handoff to the Rest of the Suite:**
   - Unknown library/API or breaking upgrade in next milestone -> `engg-research`
   - Major unarchitected subsystem or contract gap -> `engg-architect`
   - Foundations unknown, or fragile/untested modules blocking the milestone -> `engg-deep-audit`, then its cleanup waves -> `engg-refactor`
   - Ready next milestone (1–2 max at a time) -> `engg-plan` -> **[`engg-build` / `engg-extend` / `engg-data` / `engg-debug` -> `engg-audit` (Mode A)]** -> `engg-ship`

## Gotchas

- **Chunking the entire year:** Harden the whole roadmap at the milestone level, but only decompose the **next 1–2 active milestones** into `engg-plan` chunks so plans stay fresh as you learn.
- **Wishful milestones:** Reject milestones phrased as "Add AI / Add Analytics / Polish UX" with zero exit criteria, budgets, or dependencies.
- **Ignoring debt tax:** Scheduling 5 feature milestones on top of untested, unpinned, or broken foundations slows velocity to zero. Pull targeted hardening prerequisites into Milestone 1.
