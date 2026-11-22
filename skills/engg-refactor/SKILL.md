---
name: engg-refactor
description: Carries out a codebase cleanup safely, one small commit at a time. Pins current behaviour with characterization tests, deletes dead code only on two independent signals, moves, splits and merges code toward the agreed architecture contract, and enforces a ratchet so violations only ever go down. Use when executing deep-audit remediation waves, stripping unnecessary code, reorganising a messy codebase layer by layer, or doing any behaviour-preserving restructure. Behaviour changes such as security fixes are done test-first, in separate commits. For new features use engg-build or engg-extend.
license: Apache-2.0
metadata:
  version: "2.0.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# Safe Refactoring: Strip, Reorganise, Ratchet

Turn a messy codebase into a clean one without breaking it. Every step is small, verified, and reversible, and the measured violation count only goes down.

## When to Use

- Executing remediation waves from an `engg-deep-audit` report (via `engg-plan`).
- Deleting dead code, moving code into the right layer, splitting god-functions, merging duplicates.
- Any restructure where behaviour must stay the same.

**Not for:** new features (`engg-build` / `engg-extend`) or a whole-codebase review (`engg-deep-audit`).

## Non-Negotiable Rules

1. **Pin behaviour before changing structure.** Code without tests gets characterization tests first (`references/refactor-playbook.md` §1), and you prove those tests can fail.
2. **Refactors preserve behaviour; fixes are separate.** STRIP/MOVE/SPLIT/MERGE/SIMPLIFY/TEST commits change no behaviour. HARDEN findings are intended behaviour changes: test-first, `fix(...)` commits, never mixed with a refactor.
3. **Delete on two signals, re-verified at HEAD.** Audit evidence may be stale. Before every STRIP, re-check the graph or dead-code tool and run a full-text search, including config and dynamic references (Evidence Protocol in `references/engineering-constitution.md`).
4. **The ratchet only goes down.** Record the baseline with `scripts/ratchet.py record` before the first change. After every commit, `ratchet.py check` must pass. Shrink the baseline with `ratchet.py update`; never add entries to it.
5. **Never weaken a gate to get green:** no skipped or deleted tests, no loosened contract, no raised thresholds, no new suppressions. If a gate is wrong, raise it with the owner.
6. **One transformation kind per commit,** each passing the gates: tests, typecheck, linter, compiled architecture enforcer (`scripts/compile_contract.py`, schema in `references/architecture-contract.md`), ratchet.
7. **Use tools, with consent.** Prefer automated refactors (LSP rename and move, `ast-grep` rewrites) over hand edits. Check what's installed with `scripts/toolcheck.sh` (Windows: `scripts/toolcheck.ps1`), pick from `references/toolchain.md`, and follow `references/tool-consent.md` before installing.
8. **Refactors respect the baseline:** cleanup moves code toward the existing contract. It never redesigns the architecture or swaps tools unless `.engg/delivery.yaml` says `baseline: redo` (`references/delivery-modes.md`). In `mvp-first`, refactor only what blocks the `core_flow` or the current wave.

## Workflow

1. **Load the plan.** Take one wave from the deep-audit report or the `engg-plan` chunks. Restate each finding id, its action, and its target location.
2. **Baseline.** Run the enforcer and scanners, then `python scripts/ratchet.py record --baseline .engg/baseline/violations.json --depcruise <file> --gitleaks <file>` (whichever sources apply). Commit the baseline.
3. **Safety net.** For every unit the wave touches that lacks tests, add characterization tests and prove they can fail. Make sure a type checker and linter are among the gates. Commit before any change.
4. **For each finding, in wave order:**
   1. Re-verify the finding at HEAD; skip it, with a note, if it no longer holds.
   2. Apply the transformation from `references/refactor-playbook.md` §2. Large moves use the strangler fig (§3).
   3. Run the gates and `ratchet.py check`. If anything was fixed, run `ratchet.py update` **before** committing.
   4. Commit the change, its tests, and the smaller baseline together, with the finding ids in the message. CI runs `ratchet.py check --require-tight`.
5. **Wave report.** Show the ratchet before and after, the findings done, skipped (and why) and deferred, and the gate results with their commands.
6. **Hand off.** Run `engg-audit` (Mode A) on the wave's diff. When all waves are done, re-run `engg-deep-audit` to confirm the drift is gone.

## Gotchas

- **Big-bang refactors:** if a change needs more than one kind of transformation, it's more than one commit.
- **Stale audit evidence:** code moves between the audit and the fix. Re-check before deleting.
- **Characterization tests that can't fail:** tests that mock everything pass after any refactor, including broken ones. Break the code once on purpose to see them go red.
- **Silently fixing bugs during a move:** a behaviour change hidden in a `refactor:` commit defeats review. Pin the bug, move the code, then fix it in its own `fix:` commit.
