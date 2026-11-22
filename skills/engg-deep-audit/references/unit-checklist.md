# Unit Review Checklist

Use this for each unit the ledger hands you. Read **only** the unit's files and its context pack. For anything outside the unit, ask the graph (`graphify explain "<symbol>"`, `graphify affected "<symbol>"`) or search (`rg`); don't open the whole codebase.

## Every unit

- [ ] **Tool findings triaged:** every item in the context pack is TRUE, FALSE-POSITIVE (with a reason), or NEEDS-HUMAN.
- [ ] **Correctness:** off-by-one errors, null/undefined paths, integer vs. float money, time zones, unchecked return values, wrong error types.
- [ ] **Errors:** no swallowed exceptions, empty catch blocks, or `return false` that hides the cause. Errors carry context.
- [ ] **Bounds:** every outbound call has a timeout or cancellation; loops and queries are bounded; payload sizes are capped.
- [ ] **Security at this layer's trust boundary:** input validated, queries parameterised, authorization checked against the resource owner, no secrets, no PII in logs.
- [ ] **Duplication:** does this unit re-implement a rule that lives elsewhere? (See the duplication list in the context pack.)
- [ ] **Dead code:** confirm or reject each dead-code candidate with a second signal before proposing `STRIP`.
- [ ] **Complexity:** functions over the contract's limits. Is the complexity essential, or tangled?
- [ ] **Tests:** do tests exist for this unit's behaviour? Could they fail if the behaviour broke, or do they only assert that mocks were called?

## By layer

| Layer (typical names) | Ask |
|---|---|
| **domain / core / model** | Zero imports from frameworks, I/O, SDKs, or outer layers? Invariants enforced at construction, so invalid states can't be built? Pure functions with no hidden time or randomness? Money in integer minor units or decimals? |
| **application / use-case / service** | Orchestration only, or is business logic leaking in that belongs in the domain? Depends on ports (interfaces), not concrete adapters? Transactions and idempotency where a retry could double-apply? |
| **adapters / infrastructure / repository / client** | Queries parameterised? Timeouts, retries with backoff and a cap, and connection limits? External errors and DTOs mapped at the boundary, never leaked inward? Resources closed on every path? |
| **transport / http / api / ui** | Input validated and size-capped before use? AuthN and **authZ against the resource owner** (not just "logged in")? Errors mapped to safe responses without stack traces or internals? Rate limits where abuse is cheap? |
| **shared / common / utils** | Really shared, or a dumping ground? Anything domain-specific that belongs in a module? Anything unused? |
| **composition / main / config** | Config validated at startup (fail fast)? Secrets read from the environment or a secret manager, never literals? Graceful shutdown? |
| **unassigned (in no layer)** | Why does this exist? Propose `MOVE` to the right layer, `STRIP` it if unused, or a contract change if it's a legitimate new kind of code (that needs the owner's approval). |

## Writing the unit summary (5 lines max)

What the unit is · the most serious problem · what is solid and verified · anything left for layer synthesis (a pattern that might repeat in other units).
