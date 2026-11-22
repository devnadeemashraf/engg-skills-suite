# Evals: Does the Deep Audit Actually Find Things?

Small fixture repos with known content, and answer keys that score an audit run.

| Fixture | What it is | Pass when |
|---|---|---|
| `fixtures/ts-messy-api` | A TypeScript orders/users API with 20 known defects. Some were planted; three more were found by the first dry run and added to the key. | Recall ≥ 90% against `expected/ts-messy-api.yaml`, and no P0 defect rated milder than P0 |
| `fixtures/ts-clean-api` | The same API written cleanly, following its contract | Zero P0/P1 findings (anything at P0/P1 is a false alarm) |

## Running one

```bash
python evals/prepare.py evals/fixtures/ts-messy-api /tmp/eval-messy   # strips the answer comments, makes it a git repo
# In /tmp/eval-messy, run the engg-deep-audit skill end to end with a FRESH agent session.
python evals/score.py --findings /tmp/eval-messy/.engg/audit/<run-id>/findings --expected evals/expected/ts-messy-api.yaml
python evals/score.py --findings /tmp/eval-clean/.engg/audit/<run-id>/findings --expected unused --clean
```

## Reading the numbers honestly

- **A run is only a fair measurement if the agent has never seen the fixture or the answer key.** The fixture files carry `// DEFECT` comments for humans. `prepare.py` strips them, but an agent that read this repo knows the answers anyway.
- The first dry run (2026-11-22) was done by the agent that wrote the fixtures. It scored 17/17 on the original key. That proves the **mechanics** work: recipes, map, ledger, schema and scorer. It does not prove recall on unseen code.
- **Tool-level false alarms are tested in CI:** `tests/test_deep_audit.py` checks that the recorded tool outputs for the clean fixture produce no tool findings, dead-code candidates, cycles or duplicates.
- An answer key only lists what someone knew to look for. Extra findings aren't automatically wrong. Review them; if one is a real defect, add it to the key (as D18 to D20 were).

## Refreshing the recorded tool outputs

`tests/fixtures/deep-audit-raw/` holds real tool output used by the tests. After changing a fixture or upgrading a tool:

```bash
python tools/capture_audit_raw.py evals/fixtures/ts-messy-api tests/fixtures/deep-audit-raw/ts-messy-api
python tools/capture_audit_raw.py evals/fixtures/ts-clean-api tests/fixtures/deep-audit-raw/ts-clean-api
```

The capture strips absolute paths and environment details, and refuses to write if any local path remains.
