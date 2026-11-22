# Refactor Playbook

Each transformation is **one commit**, with verification commands that must exit 0 before it lands.
"The gates" means: tests, typecheck, linter, the compiled architecture enforcer, and `scripts/ratchet.py check`.

## 1. Pin behaviour first (characterization tests)

Before changing any code that has no tests, record what it does **today**, bugs included. Characterization tests pin current behaviour; they don't judge it.

1. List the unit's public entry points: exported functions, routes, CLI commands.
2. For each one, pick inputs covering every branch the complexity report shows: boundaries, empty and error paths, each coupon or flag.
3. Assert today's exact outputs. When the output is obviously a bug, still pin it, and mark it with a comment naming the finding id (for example `pins bug U002-04; flip when fixed`).
4. Prefer real collaborators or in-memory fakes over mocks. A test that only checks "A called mock B" can't catch a refactor breaking behaviour.
5. **Prove the tests can fail.** Break the code on purpose (or run a mutation tool on the touched lines) and see a test go red, then restore it. **Check the break really applied** (`git diff --stat` shows a changed line) before trusting a green run: a search-and-replace that silently matched nothing proves nothing.
6. **Make sure a type checker and linter are gates.** Deleting code leaves unused imports and parameters behind, and only those tools catch them. If the project has neither, add them (with the owner's agreement) in this safety-net step, before the first STRIP.

Commit: `test(<area>): pin current behaviour of <unit> before refactor`.

## 2. Transformation catalog

| Action | Steps | Extra verification |
|---|---|---|
| **STRIP** (delete) | Re-check at HEAD with **two signals**: the graph or dead-code tool shows no users, and a text search (`git grep -n "<name>"` across every tracked file, config included) finds nothing. Check dynamic imports, reflection, string-based routing and framework conventions. Then delete the code and anything that only it used, including imports it leaves unused. | Build, the full test suite, and the type checker with unused-locals on. The ratchet often shrinks further than expected: an unused import can be one half of a cycle. |
| **MOVE** | Use automated tools where possible: an IDE or LSP rename/move, or `ast-grep` rewrite rules, rather than hand-editing imports. Move the code, update every import, and keep the public entry point stable (re-export from the old path for one release if outside callers exist). | The architecture enforcer: the targeted rule violation disappears and no new one appears. |
| **SPLIT** | Extract pure functions first (no I/O), then the remaining orchestration. Leave the original signature as a thin wrapper until every caller has moved. | Characterization tests unchanged and green |
| **MERGE** (duplicates) | Pick the single owner location the contract allows (usually domain or shared). Make the copies identical, then swap each caller to the owner one at a time, then delete the copies. | The duplication report no longer lists the clone. The tests of every former copy pass. |
| **SIMPLIFY** | Guard clauses instead of nesting, lookup tables instead of branch ladders, remove one-implementation abstractions. Keep the observable behaviour identical. | The complexity report shows the function under the contract limit |
| **TEST** | Add the missing proof. That adds tests; it never changes production code. | The new tests fail when the code is broken on purpose |

**HARDEN findings change behaviour on purpose**, for example adding an owner check or parameterising a query. They are not refactors. Follow `engg-build`'s test-first order: write the failing test that proves the defect, fix it, and commit as `fix(...)`. A characterization test that pinned the old buggy behaviour flips in the same commit, with the finding id in the message.

## 3. Strangler fig (for large moves)

When a module is too big to move in one safe commit:

1. Build the new implementation beside the old one, behind the same port or interface.
2. Route **one** caller (or a small slice of traffic) to the new path. Run the gates.
3. Repeat caller by caller. Each switch is its own commit and can be reverted alone.
4. When nothing calls the old path, STRIP it with the two-signal check.

Never rewrite from scratch while the old code is still serving. Never run two half-migrated paths without a test that proves they agree.

## 4. Public API safety

If the code is a library, or has external callers, compare the public surface before and after: API Extractor (TS), `cargo public-api` (Rust), `apidiff` (Go), or a `__all__`/exports snapshot test (Python). An unintended API change blocks the commit. An intended one needs a deprecation path and a changelog entry.

## 5. Commit discipline

- One transformation kind per commit. Never mix a MOVE with a behaviour change: reviewers must be able to trust that a `refactor:` commit changes no behaviour.
- Message: `refactor(<area>): <what moved or changed> (<finding ids>)`, `chore: remove dead <thing> (<ids>)`, or `fix(<area>): <defect> (<ids>)`.
- After each change: run the gates and `ratchet.py check`. If the ratchet shows fixed violations, run `ratchet.py update` **before committing**, so the smaller baseline lands in the same commit as the fix. In CI, run `ratchet.py check --require-tight`, which fails when a fix arrives without its baseline shrink.
- Ratchet sources: scan the **working tree** for secrets (`gitleaks dir <src> --redact ...`), because the question is "is the secret still in the code?". A committed secret stays in history until rotated, so a history scan would never let the ratchet go down. The audit still scans history.
- If any gate fails and the cause isn't obvious within one attempt, revert the commit and split the change smaller.
