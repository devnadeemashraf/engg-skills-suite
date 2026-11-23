# Delivery Modes and the Established Baseline

Two things shape every plan and every chunk:
- **what kind of result the user expects** (the delivery mode)
- **what already exists and must be respected** (the baseline)

Settle both before planning or building, and record them, so no later session has to guess.

## 1. Ask once per effort

At the start of a new effort (a new project, a new milestone, a new feature, or an audit's remediation), check `.engg/delivery.yaml`:
- **If it exists**, use it, and don't ask again.
- **If it's missing, or the effort is new**, ask one question with both options and a recommendation:

> **What result do you want from this effort?**
> 1. **MVP first, then iterate** (`mvp-first`): get the core flow working end-to-end quickly, with everything critical around it done properly, then add features, improvements and fixes in small increments.
> 2. **Everything, in order** (`full-sequence`): build every planned part one by one, each one complete and polished before the next.
>
> *Recommended: `<mode>`, because `<one line tied to this effort>`.*

Recommend **`mvp-first`** when:
- the core idea is unproven, or there are fatal risks or experiments
- there is a demo or deadline
- the scope is still moving

Recommend **`full-sequence`** when:
- the scope is fixed and well understood, and the risks are already retired
- it's a library, platform or infrastructure piece where partial work is useless
- the user says quality now matters more than speed

The user may switch modes at any time. Record the switch with the date.

## 2. Record it: `.engg/delivery.yaml`

```yaml
mode: mvp-first            # mvp-first | full-sequence
baseline: existing         # greenfield | existing | redo   (see section 4)
core_flow: "sign in -> import a video -> preview -> export"   # mvp-first: the one flow the MVP must demonstrate
decided: 2026-11-23        # update when the mode changes, with a one-line reason below
reason: "Core claim unproven; demo in two weeks."
```

Commit it with the plan.

## 3. What each mode changes

| | `mvp-first` | `full-sequence` |
|---|---|---|
| **First wave** | The thinnest end-to-end path through `core_flow`, plus everything critical (below). Risky assumptions are tested first. | The foundation in full, then each part in planned order. |
| **Chunk size** | One step of the core flow per chunk, vertical and demonstrable. | Smaller chunks, one concern each. |
| **Default risk tier** | T1. Raise a chunk to T2/T3 by what it touches (auth, money, PII, migrations stay T3). | T2. T1 only for trivial chunks. |
| **Deferred to iterations** | Non-core features, polish, extra adapters, performance work beyond stated budgets, and refactors or hardening of code the core flow doesn't need, all logged in a backlog. | Nothing is deferred by default; every planned part is finished before the next. |
| **Docs** | Always written when their step needs them: the charter, EDD, ADRs, blueprint, handoff, agent file, README and setup, plus any document the user asks for. Deferred: optional polish documentation, such as tutorials or long guides, until the core flow works. | Docs updated with every chunk. |
| **After the MVP** | One small chunk per feature, improvement or fix, each shippable alone, in backlog priority order. | n/a |
| **Done means** | The core flow works end-to-end on a real environment, with CI green. | Every planned part is complete and green. |

## 4. Never changed by either mode

- **Security at trust boundaries:** input validation, authentication and authorization, and no secrets in code or logs.
- **The architecture contract and the ratchet:** new code adds zero violations.
- **Tests before code at the chunk's risk tier, and no weakened gates:** no skipped tests, no suppressions, no lowered thresholds.
- **The Evidence Protocol:** claims are cited and verified.

`mvp-first` cuts scope, never quality: what's built is built properly.

## 5. The established baseline

| `baseline` | Means | Rule |
|---|---|---|
| `greenfield` | Nothing exists yet | Design it (`engg-architect`), then build it. |
| `existing` | The project already has an architecture (a contract, ADRs or documented layers), tooling (CI, linters, formatter, test runner) and conventions | **They are fixed.** Build within them. Don't redesign the architecture, re-layout folders, swap tools, or "clean up" code outside the current chunk. Any improvement you notice goes in the backlog with a reason, not into the chunk. |
| `redo` | The user explicitly asked to rebuild or redesign | Only then: re-architect with `engg-architect`, and plan the migration with `engg-refactor`. |

An explicit request such as "re-architect it", "start over" or "assume every decision is wrong" sets `baseline: redo` at once. Record it in `.engg/delivery.yaml` with the date and the user's words, and route the redesign to `engg-architect`. From then on, don't treat the old design as fixed. Reuse the code that still fits.

Decide the baseline from what's in the repository: an architecture doc or contract, CI config, lint config, a test suite. Then confirm it with the user in the same question as the mode. Never assume `redo`.

When a fixed part of the baseline blocks the current goal, stop and ask. Don't work around it silently, and don't rewrite it.

## 6. Keeping to the mode

Before starting any chunk, check it against `.engg/delivery.yaml`:
- In `mvp-first`, does the chunk move `core_flow` forward, or is it a critical item? If not, it goes in the backlog.
- With `baseline: existing`, does the chunk stay inside the existing architecture and tools? If not, ask first.

Work that drifts from the mode is a finding, not a judgement call.
