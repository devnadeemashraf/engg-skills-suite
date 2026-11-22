# Chunk Specification Template & Sizing Rules

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
- **Files / Modules:**
  - Create: `<path/to/module>`, `<path/to/test>`
  - Modify: `<path/to/wiring>`
- **Architectural & Design Invariants:**
  - <e.g., Core domain has zero framework imports; port interface defined in domain package>
- **Gates (exact commands):**
  - `<npm test>` · `<npx tsc --noEmit>` · `<npx depcruise --config .engg/generated/dependency-cruiser.cjs src>` · `<python scripts/ratchet.py check --baseline .engg/baseline/violations.json --depcruise ... --require-tight>`
- **Definition of Done (DoD):**
  - [ ] Every gate above exits 0, with zero skipped or flaky tests
  - [ ] The test categories required by the tier are present and can fail (proven once)
  - [ ] `engg-audit` reports zero P0/P1 findings (T2+)
- **Key Edge Cases to Prove in Tests:**
  - <Boundary / malformed input case>
  - <Concurrency / ordering / retry case>
  - <Failure / fault-injection case>
  - <Security / isolation / abuse case>
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
- **Key Edge Cases:** an id of `x' OR '1'='1` returns no rows; the SQL text sent to the database never contains caller input.
- **Ratchet delta:** none (injection isn't a contract rule); covered by a new test instead.
- **Rollback:** revert the commit.
```
