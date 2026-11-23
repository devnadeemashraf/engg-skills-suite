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

Review adversarially, the way a Principal engineer and a security auditor would: assume every file, design spec and test suite contains hidden defects, security holes and scalability time-bombs until the evidence shows otherwise.

## When to Use

- **Mode A — Chunk / PR Audit (Phase 4):** Mandatory post-implementation review after `engg-build` or `engg-extend`.
- **Whole codebase or subsystem?** Use `engg-deep-audit`. It maps the system with tools and reviews it unit by unit, with progress kept on disk. (This was Mode B in v1.)
- **Mode C — External Spec / Plan Tightening:** Reviewing an architecture doc, PRD, or implementation plan authored by another human or LLM to find gaps, contradictions, security blind spots, and missing bounds before building.

## Non-Negotiable Rules

1. **Load audit references first:** Read `references/engineering-constitution.md`, `references/audit-checklist-core.md`, and only the matching surface section of `references/audit-domains.md`. For Mode C, also read `references/brownfield-hardening.md`.
2. **Never rubber-stamp:** If zero P0/P1 findings exist, explicitly prove why by citing the exact files, symbols, and verified controls inspected.
3. **Evidence over vague opinions:** Every finding must cite an exact file/symbol (or spec section), a concrete failure or exploit trace, a specific fix, and a regression test.
4. **Audit the tests too:** Treat weak, mocked-out, flaky, or missing edge-case tests as real findings (`P1` for missing security/reliability proofs).
5. **Depth follows the risk tier:** T1 changes get the core checklist. T2 adds all six domains and the test-rigor review. T3 (auth, money, PII, migrations, crypto, infrastructure) also requires the diff-scoped security scans below, a threat-model note, and explicit human sign-off before merge (Risk Tiers in `references/engineering-constitution.md`). Cleanup work is checked for behaviour preservation, which is `engg-refactor`'s standard.
6. **Tools, with consent:** run `scripts/toolcheck.sh <tools>` (Windows: `scripts/toolcheck.ps1`) for the tools this step needs, and prefer them over reading code by hand. Read only those tools' rows in `references/toolchain.md`, and `references/tool-consent.md` only before proposing an install.
7. **Check against the architecture contract:** if `.engg/architecture.yaml` exists (schema: `references/architecture-contract.md`), run `scripts/compile_contract.py --check` and the compiled enforcer. Every violation is a finding citing the rule name and the offending import. Report rules marked NOT COVERED as unchecked, never as passing. If no contract exists, say so and recommend `engg-architect` to create one.
8. **Working loop** (`references/working-loop.md`): start from `scripts/brief.py`, find files with `scripts/map.py` before reading them, run gates with `scripts/check.py`, and finish by updating `docs/HANDOFF.md` (§3). The user's explicit request outranks these defaults (§5). No AI attribution anywhere; `scripts/attribution_check.py` checks it. A defect outside the change under review becomes a Fix first line in `docs/HANDOFF.md`, not a fix in this diff.

## Workflow — Mode A (Chunk / PR Audit)

1. **Tools on the diff first** (`BASE` = the target branch, e.g. `origin/main`):
   - Changed files: `git diff --name-only BASE...HEAD`
   - Secrets in the new commits: `gitleaks git . --log-opts="BASE..HEAD" --redact --no-banner`
   - Architecture: the compiled enforcer, then `scripts/ratchet.py check --require-tight` if a baseline exists
   - If a lockfile changed: `osv-scanner scan source -r .`
   - SAST on the changed files when available (opengrep or the stack's analyser)
   Triage every tool result: TRUE, FALSE-POSITIVE with a reason, or NEEDS-HUMAN.
2. Read every created and modified file (production + tests + configs). Find the blast radius with the graph (`graphify affected "<changed symbol>"`) rather than reading the whole codebase.
3. Systematically audit across all 6 domains in `references/audit-checklist-core.md` and `references/audit-domains.md`:
   - Correctness & Edge Cases
   - Security & Zero-Trust
   - Performance & Resource Bounds
   - Reliability, Concurrency & Lifecycle
   - Architecture & Design Principles (SOLID, DRY, KISS, ATOMIC, Dependency Flow)
   - Test Rigor & Determinism
4. Emit a severity-ranked **Audit Report** (`P0 Blocker`, `P1 High`, `P2 Medium`, `P3 Nit`) using the exact Finding Template.
5. Fix all `P0` and `P1` findings immediately (with regression tests), re-verify the full test/lint/race suite, and confirm zero regressions.

## Workflow — Mode C (External Spec / LLM Plan Audit)

1. Interrogate the spec against `references/engineering-constitution.md` and `references/brownfield-hardening.md` (Spec Audit Matrix).
2. Flag every ambiguity, unstated assumption, contradiction, missing security/trust boundary, unbounded resource, unverified version/API claim, and over-engineered component.
   - **Security bar:** the spec must name its OWASP ASVS 5.0 level (L1, L2 or L3) and the controls it relies on. Cite requirements with their version, e.g. `v5.0.0-6.2.1`. If no level is named, that is a finding, with a recommended level.
   - **Stale claims:** check every library, version and API claim live through `engg-research`; never accept versions from the spec or from memory.
   - **Architecture:** does the spec state its layers and dependency rules precisely enough to write `.engg/architecture.yaml`? If not, that is a finding for `engg-architect`.
3. Deliver a **Tightened Spec Delta** (exact additions, cuts, and replacements) ready to lock into an EDD or execute via `engg-plan`.

## Gotchas

- **Polite grading:** Never soften a `P0` security flaw or race condition into a "suggestion." Call defects plainly by severity.
- **Big-bang rewrite trap:** In brownfield repos, never recommend "rewrite from scratch" when strangler-fig hardening + safety-net tests delivers faster, safer quality gains.
