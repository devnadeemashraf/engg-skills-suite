---
name: engg-deep-audit
description: Audits an entire existing codebase or subsystem layer by layer and unit by unit against its agreed architecture contract, using open-source tools (code graph, complexity, duplication, dead-code, secret and dependency scanners) to map the system first, then reviewing one bounded unit at a time with progress kept on disk. Produces a severity-ranked report, a strip list of everything unnecessary, a move list to reach the contract, and remediation waves. Read-only. Use when auditing a whole repository, onboarding onto a messy codebase, measuring how far code has drifted from its architecture, or planning a cleanup. Not for a single diff or PR (use engg-audit).
license: Apache-2.0
metadata:
  version: "2.1.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# Deep Codebase Audit: Layer by Layer, Piece by Piece

Tools build the map; you judge only what tools can't. Reading thousands of lines and holding them in memory is slow and inaccurate. This skill bounds what you read at every step, and keeps all state in files, so a run can stop and resume at any point.

## When to Use

- Auditing a whole repository or a large subsystem, for example before cleaning up an in-progress project.
- Measuring drift between the code and its agreed architecture.
- Producing an evidence-backed cleanup plan: what to delete, what to move, what to harden.

**Not for:** a single diff or PR, or a spec document. Use `engg-audit` for those.

## Non-Negotiable Rules

1. **Read-only for production code.** Never edit it during the audit; fixes run later through `engg-plan` → `engg-refactor` / `engg-build`. Writing the audit's own files, the report, and any document the user asks for (a proposal, a redesign brief) is part of the job.
2. **No contract, no conformance verdict.** The audit measures code against `.engg/architecture.yaml` (schema: `references/architecture-contract.md`). If it's missing, draft the as-is contract (Phase 2) and continue once the user agrees. If the user has asked for a redesign, that's `baseline: redo`: finish the map and the findings, then hand the redesign to `engg-architect` (`references/delivery-modes.md` §5).
3. **Tools first, then judgment.** Build the machine map (Phase 1) before reading any code. Use `scripts/toolcheck.sh` (Windows: `scripts/toolcheck.ps1`) for the tools in `references/tool-recipes.md`, read only the missing tools' rows in `references/toolchain.md`, and install nothing without `references/tool-consent.md`.
4. **Bounded reading.** Review one ledger unit at a time and read only its files and context pack. For anything else, query the graph (`graphify explain`, `graphify affected`) or search (`rg`).
5. **State lives on disk, not in memory.** The ledger (`scripts/ledger.py`) is the source of truth for progress. After each unit, its findings are in a file and its content can leave your working context.
6. **Evidence or it didn't happen.** Follow the Evidence Protocol in `references/engineering-constitution.md`: cite `file:line` or a tool result, triage every tool finding, and require two signals before proposing deletion. Findings follow `references/finding-schema.md`.
7. **Say what wasn't checked.** Every input the map lists as "not run", and every contract rule the compiler marks NOT COVERED, appears in the report as unchecked.
8. **Shape the remediation by the delivery mode** (`.engg/delivery.yaml`; only if it's missing, ask the question in `references/delivery-modes.md` §1). In `mvp-first`, Wave 1 holds only the P0s and what blocks the `core_flow`; everything else goes to later waves or the backlog. The audit itself is never shortened, and work that drifted from the recorded mode is a finding.
9. **Working loop** (`references/working-loop.md`): start from `scripts/brief.py`, find files with `scripts/map.py` before reading them, run gates with `scripts/check.py`, and finish by updating `docs/HANDOFF.md` (§3). The user's explicit request outranks these defaults (§5). No AI attribution anywhere; `scripts/attribution_check.py` checks it.

## Workflow

**Phase 0: Preflight**
- Confirm the working tree is clean (`git status`); otherwise label the run "dirty".
- Pick a run id (date plus a short label) and set `RUN=.engg/audit/<run-id>`.
- Keep the audit's own files out of git. Add `.engg/audit/`, `.engg/generated/` and `graphify-out/` to `.git/info/exclude`: it is local to this clone and changes no tracked file. Editing `.gitignore` is a project change, so ask first.
- Run toolcheck for the tools in `references/tool-recipes.md`. Ask once for any missing ones (tool consent protocol), and note the ones declined.

**Phase 1: Machine map (no code reading)**
- Run the commands in `references/tool-recipes.md` into `$RUN/raw/`.
- Run `python scripts/build_map.py --run-dir $RUN`.
- Read `$RUN/map.md`: layer sizes, files in no layer, overlaps, hotspots, dead-code candidates, duplication, cycles, and the unit plan.

**Phase 2: Contract gate**
- If `.engg/architecture.yaml` is missing, draft the as-is contract from the directory layout and graph communities (`GRAPH_REPORT.md`) and show it to the owner. Continue once they agree it describes the code; agreeing the to-be contract is `engg-architect`'s job (brownfield mode, or `redo` if they asked for a redesign).
- Run `python scripts/compile_contract.py` and keep its coverage report for the final report.

**Phase 3: Unit plan**
- Run `python scripts/ledger.py init --run-dir $RUN`. Units run inner layers first (domain before the code that depends on it), and riskiest first within each layer.
- Share the plan (unit count, layers, the top hotspots). Ask whether to pause at each layer boundary or run straight through.

**Phase 4: Unit loop (repeat until the ledger is empty)**
1. `python scripts/ledger.py next --run-dir $RUN` prints the context pack: files, metrics, tool findings to triage, duplicates, cycles, and dead-code candidates.
2. Review the unit with `references/unit-checklist.md`, reading only the listed files.
3. Write `$RUN/findings/<unit>.yaml` (`[]` if clean).
4. `python scripts/ledger.py done --run-dir $RUN --unit <id> --summary "..."`. If it rejects the findings, fix them and rerun. Then drop the unit's code from working context.
5. A unit you decide not to read line by line (for example, test code judged by tool signals only) is recorded with `ledger.py skip --unit <id> --reason "..."`, never left pending or marked done. The report then says PARTIAL and lists every skipped unit with its reason.

**Phase 5: Layer synthesis**
- For each layer, read `ledger.py summaries --layer <name>`, not the code.
- Look for patterns across units: the same rule re-implemented, a leaky adapter everywhere, inconsistent error handling. Spot-check with targeted graph queries.
- Record each pattern as one finding in a synthesis unit file (`findings/S-<layer>.yaml`, ids `S-<layer>-NN`).

**Phase 6: Report**
- Run `python scripts/ledger.py report --run-dir $RUN`, then write `$RUN/REPORT.md` around `report-data.md`:
  - **Scorecard (1–5):** Correctness, Security, Performance, Reliability, Architecture conformance, Testability, Simplicity. Each score cites findings.
  - **Checks not run** and **contract rules NOT COVERED**.
  - **Strip list** and **move list** (from the report data).
  - **Remediation waves** for `engg-plan`:
    - Wave 1: safety-net tests on hotspots + P0 fixes + the CI ratchet
    - Wave 2: the strip list
    - Wave 3: P1 hardening
    - Wave 4: moves, splits and merges toward the contract, inside-out
    - Wave 5: P2/P3 simplification

**Phase 7: Enforcement handoff and the pointer**
- Create or update `docs/HANDOFF.md` (Stage `audit`, Next: `engg-plan` turns the waves into `docs/BLUEPRINT.md`), pointing at `$RUN/REPORT.md`. The audit folder is git-excluded, so record the run id there.
- Propose (don't apply) wiring the compiled enforcer, gitleaks, and the formatter and linter into pre-commit and CI.
- Propose recording today's violations as the ratchet baseline with `python scripts/ratchet.py record --baseline .engg/baseline/violations.json --depcruise $RUN/raw/depcruise.json --gitleaks $RUN/raw/gitleaks.json`, so new violations block merges while old ones are paid down wave by wave (`engg-refactor` runs the waves).

## Gotchas

- **Skimming instead of tooling:** reading files to "get a feel" before the map exists burns context and misses cross-file facts the graph has for free.
- **Dead code that isn't:** entry points, framework conventions (routes, DI, plugins), reflection, and string-based imports reach code no static graph sees. Two signals, then check those.
- **Re-litigating the contract mid-audit:** if the contract itself looks wrong, record it as a finding for `engg-architect`. Don't silently audit against a different architecture.
- **One finding per copy:** duplicated code is one `MERGE` finding listing every location, not one finding per file.
