---
name: engg-ship
description: Prepares, automates, hardens, and executes production delivery. Covers CI/CD quality gates (including the architecture contract and violation ratchet), supply-chain security (SHA-pinned actions, workflow linting, SBOMs, SLSA provenance), merge queues, containerization, Infrastructure-as-Code, observability, feature-flagged progressive rollouts with tested rollbacks, DORA delivery metrics, and atomic Git commits. Use when setting up or hardening CI/CD, writing Dockerfiles or IaC, preparing a release, verifying production readiness, or rolling software out and back safely.
license: Apache-2.0
metadata:
  version: "2.1.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# Release, Supply Chain & Production Operations Engineer

Ship software reliably, repeatably, and reversibly, with gates that machines enforce, a supply chain an attacker can't quietly rewrite, and rollbacks that have already been tested.

## When to Use

- Authoring or hardening CI/CD pipelines, Dockerfiles, Kubernetes manifests, Terraform/OpenTofu/Pulumi IaC, or mobile/web/game release pipelines.
- Running a pre-launch Production Readiness Review (PRR).
- Setting up merge queues, feature flags, canary rollouts, delivery metrics, or incident rollback runbooks.

## Non-Negotiable Rules

1. **Read the readiness gate first:** load `references/production-readiness-gate.md` before signing off any release or infrastructure change. Infrastructure and release changes are risk tier **T3** (`references/engineering-constitution.md`).
2. **Immutable, reproducible builds:** build once from pinned dependencies and promote the exact same artifact from dev to staging to prod. Config is injected from the environment or a secret manager, never rebuilt per environment.
3. **Every rollout has a tested rollback:** never ship a deployment, flag flip, or infrastructure change without a fast rollback path that has been exercised beforehand.
4. **Least privilege, no plaintext secrets:** use OIDC or workload identity, scoped roles, secret managers, non-root containers, and secret scanning in pre-commit and CI.
5. **Pin every third-party input immutably:**
   - CI actions by full commit SHA (tag in a comment), container images by digest, dependencies by lockfile.
   - A tag can be force-pushed: in March 2026, 76 of 77 `trivy-action` tags were rewritten to steal CI secrets (CVE-2026-33634).
   - Lint workflows with `actionlint` and `zizmor`. Keep pins fresh with Renovate (`helpers:pinGitHubActionDigests`) rather than hand-editing.
6. **Standards are machine-enforced:** required status checks and branch protection on the default branch, CODEOWNERS for sensitive paths, and in CI the compiled architecture contract plus `scripts/ratchet.py check --require-tight`, so violations can only go down.
7. **Atomic Conventional Commits:** `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build`, `ci`, `chore`, with concise imperative subjects that explain *why*. They describe the change, never how it was produced: no AI attribution in commits, PRs, tags or release notes (constitution §7).
8. **Use the open-source toolchain, with consent:** check what's installed with `scripts/toolcheck.sh <tools>` (Windows: `scripts/toolcheck.ps1`), read only those tools' rows in `references/toolchain.md`, and follow `references/tool-consent.md` before installing anything. Look up every action, image and tool version live through `engg-research`; never from memory.
9. **Working loop** (`references/working-loop.md`): start from `scripts/brief.py`, find files with `scripts/map.py` before reading them, run gates with `scripts/check.py`, and finish by updating `docs/HANDOFF.md` (§3). The user's explicit request outranks these defaults (§5). No AI attribution anywhere; `scripts/attribution_check.py` checks it.

## Workflow

1. **Local and pre-commit (seconds):** formatter, linter, typecheck, secret scan of what is about to be committed (`gitleaks git --pre-commit --staged --redact`), via lefthook or pre-commit. A commit-msg hook runs `python scripts/attribution_check.py --message-file <msg file>` (copy the script into the repo's own scripts folder so hooks and CI don't depend on where the skills are installed). The same commands run again in CI; hooks are a convenience, not the gate.
2. **CI quality gates (fail fast):**
   - **Stage 1, seconds:** secret scan, format check, lint, typecheck, `attribution_check.py --range origin/<main>..HEAD` (check out with `fetch-depth: 0`), `actionlint` + `zizmor` on workflow changes.
   - **Stage 2, fast:** unit and contract tests, the compiled architecture enforcer, the ratchet check, IaC validate and lint (`checkov` / `tflint`), Dockerfile lint (`hadolint`).
   - **Stage 3, thorough:** integration tests against ephemeral dependencies, race and sanitizer runs, SAST, dependency and image vulnerability scans (`osv-scanner`, `grype` or digest-pinned `trivy`), an SBOM (`syft`).
   - **Stage 4, artifact:** one reproducible build tagged with the commit SHA, with signed provenance. SLSA v1.2 Build L2 or higher, via GitHub artifact attestations (`actions/attest`) or Sigstore `cosign`. Check it with `gh attestation verify` or `cosign verify` before deploying. On GitHub, private repos need Enterprise Cloud for attestations.
   - **Workflow hygiene:** `permissions: contents: read` by default, widened per job only when needed; `persist-credentials: false` on checkout; no `pull_request_target` with untrusted code.
3. **Merge discipline:** small, trunk-based pull requests. On busy repositories, a **merge queue** that runs the full gates on the merged result before it lands (on GitHub, CI must also trigger on the `merge_group` event). Run OpenSSF Scorecard on the repository and fix its high-risk checks.
4. **Packaging and infrastructure:**
   - Multi-stage minimal containers: non-root UID, read-only root filesystem, dropped capabilities, digest-pinned base images, explicit CPU and memory limits.
   - Modular declarative IaC with remote locked state, drift detection, and separate state per environment.
5. **Observability:** structured logs with correlation ids, SLIs and SLOs per surface (latency/errors/saturation for backends; Web Vitals and JS errors for web; crash-free sessions and ANRs for mobile; crashes and FPS for games), dashboards, and alerts on user-facing SLO burn rather than noisy resource spikes.
6. **Release: separate deploy from release.**
   - Ship dark behind a feature flag. Prefer the vendor-neutral OpenFeature API (a CNCF incubating project), so the flag provider can change without code changes.
   - Ramp progressively (canary, staged rollout, blue-green) with automated health and SLO checks that roll back on their own.
   - Run synthetic smoke tests after cutover. Remove the flag once it's at 100% and stable, because stale flags are dead code.
7. **Measure delivery (DORA, five metrics):** deployment frequency, change lead time, change fail rate, failed deployment recovery time, and deployment rework rate (the share of deployments that are unplanned fixes for production incidents). Derive them from git, CI and incident data, and review the trend, not single values.
8. **Runbook and release notes:** rollback command, top failure modes, dashboards and owners in a concise runbook; atomic commits and a changelog entry per release.

## Gotchas

- **ClickOps drift:** manual console edits that bypass IaC create outages nobody can reproduce during recovery.
- **Rebuilding per environment:** "works in staging, breaks in prod" happens when prod runs a fresh build that pulled drifted dependencies.
- **Pinned once, never updated:** SHA pins without Renovate rot into known-vulnerable versions. Pin *and* automate the updates.
- **Alert fatigue:** paging on every transient warning teaches people to ignore pages. Page only on actionable SLO impact.
- **Flags forever:** a flag left in after full rollout is a second code path nobody tests.
