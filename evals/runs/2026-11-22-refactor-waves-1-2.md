# Run: engg-refactor, Waves 1 and 2 on ts-messy-api (2026-11-22)

**Goal (Phase 4 exit criterion):** execute remediation Waves 1–2 from the deep-audit dry run on `ts-messy-api`, with tests green after every commit and the ratchet baseline only shrinking.

**Setup:** `evals/prepare.py` copy of the fixture (answer comments stripped). The harness transpiles with TypeScript 6.0.3 `--noCheck` and runs `node:test`. Gates per commit: tests, compiled dependency-cruiser contract, `gitleaks dir src --redact`, `ratchet.py check`.

**Not a gate in this run:** type checking and linting. The fixture has no `@types/node`, and none was installed. See finding 3 below for what that cost.

## Result

| | Before | After |
|---|---|---|
| Ratchet baseline (contract violations + secrets in the tree) | **8** | **5** |
| Tests | 0 | 22, all passing after every commit |
| Characterization tests proven able to fail | n/a | 4 of 4 deliberate breaks, each caught by exactly one test |
| P0 defects | 3 (SQL injection, IDOR, committed secret) | 0 |
| Dead code (strip list) | 4 items | 0 |

## Commits (oldest first)

```
test: add a transpile-and-run test harness
test: drop deprecated moduleResolution from the harness
chore: record the ratchet baseline (8 known violations) and add a single gates script
test(orders): pin current behaviour before remediation (19 tests; 4 mutations each caught)
fix(orders): parameterise order queries to close SQL injection (U004-01)
fix(orders): only the owner can read an order; others get 404 (U005-01)
fix(config): read the payment secret from the environment, fail fast if missing (U007-01)
chore: remove the unused tmp-migrate script and its only helper toRow (U008-01, U008-02)
chore: remove unused legacy-format.ts (U006-01)
chore: remove unused formatCurrencyOld (U006-02)
refactor(orders): drop the Order import left unused by removing toRow
chore: shrink the ratchet baseline (order-repo <-> order cycle gone)
```

- Each `fix:` commit was test-first: the characterization test that pinned the bug was flipped and run **red**, then the fix made it green.
- Each `chore:` deletion was re-verified at HEAD with two fresh signals: a rebuilt graphify graph showing fan-in 0, and `git grep` over every tracked file.

## What the run taught the skill (now in the playbook)

1. **Check that a deliberate break really applied.** The first attempt used `sed` with broken escaping: two of three breaks silently changed nothing, and the green runs "proved" nothing. Redone with exact replacement and a `git diff` check.
2. **The ratchet shrink must ship with the fix.** One commit landed before `ratchet.py update`. Added `ratchet.py check --require-tight` for CI, which fails when a fix arrives without its baseline shrink.
3. **A cleanup needs type-check and lint gates.** Removing `toRow` left an unused `Order` import that no gate caught (TypeScript `TS6133` found it on request). That import was half of the `order-repo <-> order` cycle, so removing it shrank the ratchet a further step.
4. **Scan the working tree for secrets in the ratchet; scan history in the audit.** The committed secret stays in history until it is rotated, so a history scan would never let the ratchet go down.
5. The harness's first config used `moduleResolution: node10`, which TypeScript 6 deprecates. The chained command committed it anyway, because `| tail` hid the failure. Use `set -o pipefail` in any gate script.

## Remaining (Waves 3–5, not in scope)

Remaining violations in the baseline (5):
- domain imports an adapter (U001-01)
- the `place-order <-> pricing` cycle (U002-02)
- users reaching into orders internals (U003-01)
- adapter importing config (U004-04)
- transport bypassing the application layer (U005-02)

Still open from the findings: the P1 hardening items (timeout, swallowed errors, float money, cancel authorization), the email-validation merge, and `placeOrder` simplification.

The same caveat as the deep-audit dry run applies: the agent that ran this also wrote the fixture.
