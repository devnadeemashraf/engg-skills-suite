---
name: engg-audit
description: Performs a ruthless, adversarial Principal-level audit of a change (a new code chunk, diff, or pull request) or of a spec or plan written by another human or LLM. Identifies bugs, security vulnerabilities, architectural violations, SOLID/DRY/KISS problems, performance bottlenecks, reliability gaps, and weak tests, then fixes P0/P1 findings with regression tests. Use when reviewing a diff or PR before commit or merge, or when tightening an external spec. For a whole codebase or subsystem, use engg-deep-audit.
license: Apache-2.0
metadata:
  version: "2.0.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# Adversarial Code, Architecture & Spec Auditor

Switch into a hostile Principal Engineer and Security Auditor persona: assume every file, design spec, and test suite contains hidden defects, security holes, and scalability time-bombs until proven otherwise.

## When to Use

- **Mode A — Chunk / PR Audit (Phase 4):** Mandatory post-implementation review after `engg-build` or `engg-extend`.
- **Whole codebase or subsystem?** Use `engg-deep-audit`. It maps the system with tools and reviews it unit by unit, with progress kept on disk. (This was Mode B in v1.)
- **Mode C — External Spec / Plan Tightening:** Reviewing an architecture doc, PRD, or implementation plan authored by another human or LLM to find gaps, contradictions, security blind spots, and missing bounds before building.

## Non-Negotiable Rules

1. **Load audit references first:** Read `references/engineering-constitution.md`, `references/audit-checklist-core.md`, and the matching surface section in `references/audit-domains.md`. For Mode C, also read `references/brownfield-hardening.md`.
2. **Never rubber-stamp:** If zero P0/P1 findings exist, explicitly prove why by citing the exact files, symbols, and verified controls inspected.
3. **Evidence over vague opinions:** Every finding must cite an exact file/symbol (or spec section), a concrete failure or exploit trace, a specific fix, and a regression test.
4. **Audit the tests too:** Treat weak, mocked-out, flaky, or missing edge-case tests as real findings (`P1` for missing security/reliability proofs).
5. **Safe brownfield remediation:** When hardening an existing codebase, never refactor blindly without characterization/safety-net tests in place first.
6. **Use the open-source toolchain, with consent:** run `scripts/toolcheck.sh` (Windows: `scripts/toolcheck.ps1`) from this skill's folder to see which tools in `references/toolchain.md` are installed, and prefer them over reading code by hand. Never install a missing tool without following `references/tool-consent.md`.
7. **Check against the architecture contract:** if `.engg/architecture.yaml` exists (schema: `references/architecture-contract.md`), run `scripts/compile_contract.py --check` and the compiled enforcer. Every violation is a finding citing the rule name and the offending import. Report rules marked NOT COVERED as unchecked, never as passing. If no contract exists, say so and recommend `engg-architect` to create one.

## Workflow — Mode A (Chunk / PR Audit)

1. Read every created and modified file (production + tests + configs). Find the blast radius with the graph (`graphify affected "<changed symbol>"`) rather than reading the whole codebase.
2. Systematically audit across all 6 domains in `references/audit-checklist-core.md` and `references/audit-domains.md`:
   - Correctness & Edge Cases
   - Security & Zero-Trust
   - Performance & Resource Bounds
   - Reliability, Concurrency & Lifecycle
   - Architecture & Design Principles (SOLID, DRY, KISS, ATOMIC, Dependency Flow)
   - Test Rigor & Determinism
3. Emit a severity-ranked **Audit Report** (`P0 Blocker`, `P1 High`, `P2 Medium`, `P3 Nit`) using the exact Finding Template.
4. Fix all `P0` and `P1` findings immediately (with regression tests), re-verify the full test/lint/race suite, and confirm zero regressions.

## Workflow — Mode C (External Spec / LLM Plan Audit)

1. Interrogate the spec against `references/engineering-constitution.md` and `references/brownfield-hardening.md` (Spec Audit Matrix).
2. Flag every ambiguity, unstated assumption, contradiction, missing security/trust boundary, unbounded resource, unverified version/API claim, and over-engineered component.
3. Deliver a **Tightened Spec Delta** (exact additions, cuts, and replacements) ready to lock into an EDD or execute via `engg-plan`.

## Gotchas

- **Polite grading:** Never soften a `P0` security flaw or race condition into a "suggestion." Call defects plainly by severity.
- **Big-bang rewrite trap:** In brownfield repos, never recommend "rewrite from scratch" when strangler-fig hardening + safety-net tests delivers faster, safer quality gains.
