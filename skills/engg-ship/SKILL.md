---
name: engg-ship
description: Prepares, automates, hardens, and executes production deployments, CI/CD pipelines, Infrastructure-as-Code (IaC), containerization, observability setup, release checklists, and atomic Git commits. Use when setting up CI/CD, writing Dockerfiles or IaC, preparing a release, verifying production readiness, or rolling out and rolling back software safely.
license: Apache-2.0
metadata:
  version: "1.0.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# Release, Infrastructure & Production Operations Engineer

Ship software reliably, repeatably, and reversibly—with hardened build pipelines, declarative infrastructure, verifiable observability, and zero-drama rollbacks.

## When to Use

- Authoring or hardening CI/CD pipelines, Dockerfiles, Kubernetes manifests, Terraform/OpenTofu/Pulumi IaC, or mobile/web/game build & release pipelines.
- Running a pre-launch Production Readiness Review (PRR).
- Preparing atomic Conventional Commits, changelogs, canary rollouts, or incident rollback runbooks.

## Non-Negotiable Rules

1. **Read readiness gate first:** Load `references/production-readiness-gate.md` before signing off any release or infra change.
2. **Immutable, reproducible builds:** Build artifacts once from pinned dependencies and promote the exact same artifact across dev -> staging -> prod (config injected via environment/secret manager, never rebuilt per env).
3. **Every rollout must have a tested rollback:** Never ship a deployment, feature flag flip, or infra change without an explicit, fast rollback path verified beforehand.
4. **Least-privilege & zero plaintext secrets:** Use OIDC/workload identity, scoped IAM roles, secret managers, non-root containers, and automated secret scanning in CI.
5. **Atomic Conventional Commits:** Group changes cleanly (`feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`) with concise imperative subjects explaining _why_.
6. **Use the open-source toolchain, with consent:** run `scripts/toolcheck.sh` (Windows: `scripts/toolcheck.ps1`) from this skill's folder to see which tools in `references/toolchain.md` are installed, and prefer them over reading code by hand. Never install a missing tool without following `references/tool-consent.md`.

## Workflow

1. **CI Quality Gate Pipeline (Fast Fail Order):**
   - Stage 1 (Seconds): Secret scan, formatting check, strict linter, static typecheck.
   - Stage 2 (Fast): Unit tests, contract tests, IaC validate/lint.
   - Stage 3 (Thorough): Integration tests (ephemeral deps), race/sanitizer checks, SAST, dependency/container CVE scan, SBOM generation.
   - Stage 4 (Artifact): Reproducible immutable build signed/tagged with commit SHA.
2. **Infrastructure & Packaging Hardening:**
   - Multi-stage minimal containers (non-root UID, read-only rootfs, dropped capabilities, pinned base image digests, explicit CPU/memory limits).
   - Modular, declarative IaC with remote locked state, drift detection, and strict environment isolation (separate state/blast radius for staging vs. prod).
3. **Observability & Alerting Wiring:**
   - Verify structured logs, core SLIs/SLOs (latency/error/saturation for backend; Web Vitals/JS errors for web; crash-free sessions/ANR for mobile; crash/FPS telemetry for games), dashboards, and symptom-based alerts (alert on user-facing SLO burn, not noisy CPU spikes).
4. **Progressive Rollout & Verification:**
   - Execute pre-flight checks against `references/production-readiness-gate.md`.
   - Roll out progressively (canary / staged rollout / blue-green / feature flag ramp) with automated health/SLO gate checks.
   - Verify synthetic smoke tests and telemetry after cutover.
5. **Runbook & Atomic Commit Hygiene:**
   - Document rollback command, common failure modes, and dashboards in a concise runbook.
   - Commit cleanly with atomic Conventional Commits and release notes.

## Gotchas

- **ClickOps drift:** Manual console edits that bypass IaC create unrepeatable outages during recovery.
- **Rebuilding artifacts per environment:** "Works in staging, breaks in prod" happens when prod runs a fresh build pulling drifted dependencies.
- **Alert fatigue:** Paging on every transient warning teaches engineers to ignore alerts. Page strictly on actionable SLO impact.
