# Finding Schema

Each unit's findings go in `findings/<unit-id>.yaml` as a YAML list. `ledger.py done` rejects the file unless every finding validates. Write `[]` for a clean unit, and say in the summary what you checked and why it's clean.

```yaml
- id: U002-01                       # <unit id>-<two digits>, unique
  title: placeOrder mixes pricing rules, coupons and validation in one 14-branch function
  severity: P2                      # P0 | P1 | P2 | P3 (see below)
  action: SIMPLIFY                  # what fixing it means (see below)
  pillar: simplicity                # correctness | security | performance | reliability | architecture | testability | simplicity
  location: src/orders/app/place-order.ts:30-57     # path, path:line, or path:start-end
  evidence: >-                      # exactly what was seen: tool output, or the code path that fails
    lizard: placeOrder CCN 14 (limit 10). Branches on qty tiers, three coupon kinds and express shipping.
  source: tool:lizard               # review | tool:<name>
  triage: TRUE                      # required for tool findings: TRUE | NEEDS-HUMAN | "FALSE-POSITIVE: <reason>"
  fix: >-
    Extract quantity-discount and coupon rules into pure functions in the domain layer, each with its own tests.
  test: >-                          # required for P0/P1: the test that proves the fix
    Table-driven tests over qty tiers and each coupon, then placeOrder's own tests shrink to wiring.
  related: [U002-02]                # optional: other finding ids
```

## Severity

| Level | Meaning | Examples |
|---|---|---|
| **P0 Blocker** | Exploitable security hole, data loss or corruption, or a crash on a normal path | SQL injection, missing authorization (IDOR), committed secret, unbounded delete |
| **P1 High** | Breaks under realistic load or failure, or breaks the architecture contract in a way that spreads | No timeout on an outbound call, swallowed errors on a money path, domain importing an adapter, missing tests on security logic |
| **P2 Medium** | Raises the cost of every future change | Duplicated business rules, import cycles, a module bypassing a public entry, a hotspot function with very high complexity |
| **P3 Nit** | Cleanup with small payoff | Unused export, naming, a stale comment |

Never soften a severity to be polite. When unsure between two levels, pick the higher one and say why in `evidence`.

## Action classes

| Action | Means | Before proposing it |
|---|---|---|
| `STRIP` | Delete it | Two independent signals that nothing uses it (graph fan-in 0, text search, coverage, a dead-code tool). Check strings, reflection, config, and dynamic imports. |
| `MOVE` | Wrong layer or module; relocate it | Name the target path the contract allows |
| `SPLIT` | One unit doing several jobs | Name the pieces |
| `MERGE` | Duplicated knowledge; keep one copy | Name the single owner location |
| `HARDEN` | Security, bounds, timeouts, error handling | Give the concrete control: parameterised query, owner check, AbortSignal |
| `TEST` | A missing proof (no tests, or tests that can't fail) | Name the behaviours the tests must pin down |
| `SIMPLIFY` | Too complex or over-abstracted for what it does | Show the simpler shape |

## Rules

- **Cite or it didn't happen.** Every finding has a real `location` and `evidence` you read or ran. Never cite a line you didn't open.
- **One finding per root cause.** Report three copies of the same validation as one `MERGE` finding listing all three locations in `evidence`, not three findings.
- **Triage every tool finding listed in the unit's context pack.** A false positive gets a finding with `triage: "FALSE-POSITIVE: <reason>"` and severity P3, so the next run doesn't re-raise it unexplained.
- **Contract violations cite the rule name**, for example `dependency-cruiser domain-not-to-adapters`.
