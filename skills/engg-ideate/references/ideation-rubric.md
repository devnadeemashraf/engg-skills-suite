# Ideation & Feasibility Rubric

Use this rubric to pressure-test ideas and compare candidate approaches objectively.

## 1. Evaluation Dimensions (Score 1–5)

| Dimension | 1 (Weak / High Risk) | 3 (Acceptable) | 5 (Strong / High Leverage) |
|---|---|---|---|
| **Problem Sharpness** | Vague nice-to-have | Clear pain, moderate frequency | Acute, frequent, measurable pain |
| **Time-to-Signal** | Months before first usable test | Weeks to playable/usable slice | Days to end-to-end validation |
| **Technical Feasibility** | Unproven core tech or severe constraints | Known tech with moderate integration risk | Well-understood primitives, clear bounds |
| **Differentiation / Leverage** | Commodity clone without edge | Meaningful UX or workflow improvement | Distinct 10x workflow, performance, or UX advantage |
| **Operational / Maintenance Cost** | High ongoing ops/content burden | Moderate steady-state upkeep | Lean, automated, low toil |

## 2. Mandatory Stress-Test Questions

- **The "Why Now / Why Build" Check:** What off-the-shelf tool or open-source component already solves 70% of this? What is the remaining 30% that justifies custom engineering?
- **The Day-1 Constraint Check:** Solo developer or team? Target timeline? Zero-budget local/free-tier or funded cloud infrastructure? Offline-first or always-connected?
- **The Kill-Criteria Check:** What measurable evidence after V1 launch would prove this direction is working—or tell us to pivot?
- **The Simplicity Razor:** If we had to cut V1 scope in half and still deliver core value, what survives?

## 3. Project Charter Template

```markdown
# Project Charter: <Project Name>

## 1. Problem & Target Audience
- **Who:** ...
- **Problem:** ...
- **Why Existing Options Fall Short:** ...

## 2. Chosen Direction & Trade-Offs
- **Selected Approach:** ...
- **Alternatives Considered & Rejected:** ...

## 3. V1 Core Journeys (In Scope)
1. ...
2. ...
3. ...

## 4. Explicit Non-Goals (Out of Scope for V1)
- ...

## 5. Success Metrics & Validation Gates
- ...

## 6. Top Risks & Mitigations
| Risk | Impact | Likelihood | Cheap Validation / Mitigation |
|---|---|---|---|
| ... | ... | ... | ... |

## 7. Target Surfaces & Constraints
- **Surfaces:** (Backend / Web / Mobile / Game / Data / Infra)
- **Constraints:** (Timeline, team size, budget, compliance, target devices)
```
