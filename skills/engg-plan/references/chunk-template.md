# Chunk Specification Template & Sizing Rules

The plan lives in `docs/BLUEPRINT.md`, in this layout, so `scripts/brief.py` can print the next chunk:

```markdown
# Blueprint
<plan header, below>

## Done
- C1 Bootstrap, config, harness and CI — Wave 1 — #3
- Gate 1 — 2026-12-02

## Wave 2 — Security and resilience
### [C4] Rate limits on public routes (Wave 2, Tier T2)
<full card, below>

## Wave 3 — Features (outline)
- C7 Export to PDF — depends on C4 — goal: <one line>

## Backlog
```

- **Detail only the next wave.** Later waves are one line per chunk until their wave gate splits them, so plans stay fresh and cheap to read.
- **Closing a chunk** deletes its card and adds one Done line. Nothing else in the file changes.

## Plan Header (top of every plan)

```markdown
**Delivery mode:** mvp-first | full-sequence   (from .engg/delivery.yaml, decided <date>: <reason>)
**Baseline:** greenfield | existing | redo   (existing = architecture and tooling are fixed; see delivery-modes)
**Core flow (mvp-first):** <step -> step -> step>   Wave 1 is done when this works end-to-end with CI green.
```

## Backlog (bottom of every plan)

Work noticed but outside the mode or the current wave: deferred features, polish, refactors of code the core flow doesn't need, and baseline improvements nobody asked for. One line each: what, why, and which finding or chunk it came from. Nothing moves from the backlog into a chunk without the user agreeing.

## Chunk Sizing Heuristic
- **Ideal scope:** 1 cohesive capability, 1–5 production files + matching test files, cleanly verifiable in one Red -> Green -> Refactor -> Audit cycle.
- **Split trigger:** split the chunk if it needs more than one major architectural decision, modifies unrelated bounded contexts, mixes a structural refactor with a behaviour change, or can't be summarized in one Conventional Commit title.

## Roadmap Overview Table Format

| Chunk | Wave | Tier | Title | Dependencies | Executor | Core Value Delivered |
|---|---|---|---|---|---|---|
| C1 | Wave 1 | T1 | Bootstrap, Config, Harness & CI | None | engg-build | Fail-fast config, logging, test/lint/typecheck, pre-commit, contract check in CI |
| C2 | Wave 1 | T2 | Reference Vertical Slice | C1 | engg-build | Proves end-to-end architecture & contracts |
| R1 | Wave 2 | T1 | Strip dead code (audit strip list) | C1 | engg-refactor | Ratchet −1; less code to secure |

## Risk Tier → Gates (from the constitution; write the project's real commands)

| Tier | Gates (each an exact command that must exit 0) |
|---|---|
| T0 | formatter check, linter |
| T1 | T0 + unit tests + typecheck + compiled architecture enforcer + `ratchet.py check` |
| T2 | T1 + all five test-matrix categories + contract tests + `engg-audit` Mode A |
| T3 | T2 + mutation testing on changed code + SAST, secret and dependency scans + threat-model note + explicit human approval |

## Individual Chunk Card Template

```markdown
### [C<N>] <Chunk Title> (Wave <W>, Tier T<0-3>)
- **Goal:** <One sentence stating the exact capability or risk eliminated>
- **Executor:** <engg-build | engg-extend | engg-refactor | engg-data>
- **Findings addressed:** <None | U004-01, S-application-01>   (brownfield only)
- **Dependencies:** <None | C1, C2>
- **Cites:** <EDD §3, §5 · CHARTER §2 · ADR-0004>   (brief.py prints these sections with the card)
- **Follow:** `<path of the closest existing file to mirror>`, `<its test>`   (none for the very first slice)
- **Files in scope:** `<path/to/module>`, `<path/to/test>`, `<path/to/wiring>`   (anything else needs the user's yes)
- **Architectural & Design Invariants:**
  - <e.g., Core domain has zero framework imports; port interface defined in domain package>
- **Gates (exact commands):**
  - `<npm test>` · `<npx tsc --noEmit>` · `<npx depcruise --config .engg/generated/dependency-cruiser.cjs src>` · `<python scripts/ratchet.py check --baseline .engg/baseline/violations.json --depcruise ... --require-tight>`
- **Definition of Done (DoD):**
  - [ ] Every gate above exits 0, with zero skipped or flaky tests
  - [ ] The test categories required by the tier are present and can fail (proven once)
  - [ ] `engg-audit` reports zero P0/P1 findings (T2+)
- **Test cases** (each becomes a test named `[<ID> #<n>] <case>`; 4–10, never more than 12):
  1. <given state and input → expected result — risk in ≤ 8 words>   (boundary / malformed input)
  2. <...>   (concurrency / ordering / retry)
  3. <...>   (failure / fault injection)
  4. <...>   (security / isolation / abuse)
  Derive cases, don't brainstorm them: one per equivalence class or boundary that could fail differently. Where a rule can be stated generally (parsing, money, dates, permissions, state transitions), use one property-based test.
- **Ratchet delta:** <e.g. removes `dependency-cruiser:transport-not-to-adapters:src/orders/http/routes.ts->...` (baseline 6 -> 5) | none: new code, must add 0>
- **Rollback:** <revert the commit | feature flag `<name>` off | migration down-step `<file>` verified on a copy>
```

## Example (brownfield, from a deep-audit report)

```markdown
### [R3] Parameterise order queries (Wave 1, Tier T3)
- **Goal:** Close the SQL injection in order lookups.
- **Executor:** engg-build (behaviour change, test-first)
- **Findings addressed:** U004-01
- **Gates:** `bash test.sh` · `npx depcruise ...` · `gitleaks dir src --redact ...` · `python scripts/ratchet.py check ... --require-tight`
- **Test cases:**
  1. id `x' OR '1'='1` → no rows — injection through the id
  2. any id → the SQL text sent never contains caller input — query built by concatenation
- **Ratchet delta:** none (injection isn't a contract rule); covered by a new test instead.
- **Rollback:** revert the commit.
```
