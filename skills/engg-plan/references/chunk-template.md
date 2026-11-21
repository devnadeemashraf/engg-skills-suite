# Chunk Specification Template & Sizing Rules

## Chunk Sizing Heuristic
- **Ideal scope:** 1 cohesive capability, 1–5 production files + matching test files, cleanly verifiable in one Red -> Green -> Refactor -> Audit cycle.
- **Split trigger:** If a chunk requires more than one major architectural decision, modifies unrelated bounded contexts, or cannot be summarized in one Conventional Commit title, split it.

## Roadmap Overview Table Format

| Chunk | Wave | Title | Dependencies | Primary Surface | Core Value Delivered |
|---|---|---|---|---|---|
| C1 | Wave 1 | Bootstrap, Config & Harness | None | Core | Fail-fast config, logging, lint/test runner |
| C2 | Wave 1 | Reference Vertical Slice | C1 | Full/Core | Proves end-to-end architecture & contracts |

## Individual Chunk Card Template

```markdown
### [C<N>] <Chunk Title> (Wave <W>)
- **Goal:** <One sentence stating the exact capability or risk eliminated>
- **Dependencies:** <None | C1, C2>
- **Files / Modules:**
  - Create: `<path/to/module>`, `<path/to/test>`
  - Modify: `<path/to/wiring>`
- **Architectural & Design Invariants:**
  - <e.g., Core domain has zero framework imports; port interface defined in domain package>
- **Definition of Done (DoD):**
  - [ ] All 5 test matrix categories pass with zero skips/flakes
  - [ ] Linter, formatter, strict typechecker, and race/static checks pass clean
  - [ ] Adversarial audit (`engg-audit`) reports zero P0/P1 findings
- **Key Edge Cases to Prove in Tests:**
  - <Boundary / malformed input case>
  - <Concurrency / ordering / retry case>
  - <Failure / fault-injection case>
  - <Security / isolation / abuse case>
```
