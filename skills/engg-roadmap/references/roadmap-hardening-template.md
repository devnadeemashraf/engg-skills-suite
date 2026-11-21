# Roadmap Hardening Scorecard, Delta & Living Template

## 1. Original Roadmap Scorecard (Score 1–5)

| Pillar | Score (1–5) | Key Gap Identified |
|---|---|---|
| **Focus & Scope Discipline** | _/5 | |
| **Codebase Reality Alignment** | _/5 | |
| **Risk-First Sequencing** | _/5 | |
| **Vertical Slice & Shippability** | _/5 | |
| **Verifiable Exit Criteria & Budgets** | _/5 | |

## 2. Tightened Roadmap Delta Format

Tag every existing or newly surfaced roadmap item with exactly one disposition:
- **`[KEEP]`** — High leverage, well-scoped, correctly placed.
- **`[RE-SEQUENCE]`** — Valuable, but must move earlier (high risk/prerequisite) or later (premature).
- **`[SPLIT]`** — Too large or horizontal; break into thin vertical shippable milestones.
- **`[REVISE]`** — Keep intent, but sharpen acceptance criteria, budgets, or architecture constraints.
- **`[ADD — PREREQ]`** — Missing foundational requirement exposed by repo reality check (tests, CI, authz, migration, telemetry).
- **`[CUT — DEFER]`** — Scope drag or speculative complexity; move to Icebox / Non-Goals.

## 3. Living `docs/ROADMAP.md` Template

```markdown
# Product & Engineering Roadmap: <Project Name>

> **Last Hardened:** <YYYY-MM-DD> | **Active Surfaces:** <Backend / Web / Mobile / Game / Data / Infra>

## North-Star Outcome & Constraints
- **Current Stage:** <Prototype / Alpha / Beta / Production>
- **Primary Goal for Current Cycle:** <One concrete measurable outcome>
- **Hard Guardrails / Budgets:** <e.g., p99 < 150ms, 60fps steady, zero P0/P1 audit findings>

## Explicit Non-Goals (Out of Scope for Current Cycle)
- <Deferred item + one-line rationale>

## Milestone Roadmap (Risk-First, Vertically Sliced)

### Milestone 1: <Name> (ACTIVE — Ready for `engg-plan`)
- **Outcome:** <Measurable user/engineering value delivered>
- **Dependencies / Prerequisites:** <None | Repo gap fixed first>
- **Key Risks Retired:** <Risky assumption validated in this milestone>
- **Exit Criteria (Definition of Done):**
  - [ ] <Concrete verifiable behavior / metric / test proof>
  - [ ] Zero P0/P1 findings in `engg-audit`
- **Suite Execution Path:** `<e.g., engg-research -> engg-plan -> engg-build -> engg-audit -> engg-ship>`

### Milestone 2: <Name> (NEXT)
- **Outcome:** ...
- **Dependencies:** Milestone 1
- **Key Risks Retired:** ...
- **Exit Criteria:** ...
- **Suite Execution Path:** ...

### Milestone 3+: <Name> (LATER — High-Level Only, Do Not Chunk Yet)
- **Outcome:** ...

## Suite Routing Matrix (Active Cycle)

| Workstream / Item | Primary Skill | Supporting Skills | Artifact Produced |
|---|---|---|---|
| Verify SDK/API versions | `engg-research` | — | Verified version pins & brief |
| Resolve unarchitected seam | `engg-architect` | `engg-research` | Locked EDD & ADRs |
| Harden fragile existing module | `engg-audit` (Mode B) | `engg-plan` | Scorecard & remediation chunks |
| Decompose Milestone 1 | `engg-plan` | — | Wave 1/Wave 2 atomic chunks |
| Implement chunks (TDD) | `engg-build` | `engg-audit` (Mode A) | Tested, audited code |
| Add vertical feature / adapter | `engg-extend` | `engg-research`, `engg-audit` | Contract-tested slice/adapter |
| Schema / zero-downtime migration | `engg-data` | `engg-audit` | Expand-and-contract migration |
| Investigate bug / perf bottleneck | `engg-debug` | `engg-audit` | Root-cause fix + regression test |
| CI/CD, IaC & release rollout | `engg-ship` | `engg-audit` | Hardened pipeline & PRR sign-off |

## Decisions & Cuts Log
| Date | Decision / Cut | Rationale | Revisit Trigger |
|---|---|---|---|
| YYYY-MM-DD | Cut X from M1 | Saved 2 weeks; not needed for core validation | >1,000 active users |
```
