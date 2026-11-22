# Production Readiness Gate (PRR) Checklist

Complete before first production launch or major architectural rollout.

## 1. Build, Supply Chain & Artifacts
- [ ] All dependencies, base images, and CI actions are pinned with lockfiles/digests/full commit SHAs, and Renovate (or equivalent) keeps the pins current.
- [ ] Workflows pass `actionlint` and `zizmor`; default `permissions: contents: read`; checkout uses `persist-credentials: false`.
- [ ] CI enforces format, lint, typecheck, tests, race/static checks, SAST, secret scanning (history, redacted), and dependency/image vulnerability audits.
- [ ] The compiled architecture contract and `ratchet.py check --require-tight` are required status checks.
- [ ] Single immutable build artifact promoted across environments; zero secrets embedded in build outputs or client bundles.
- [ ] An SBOM is produced for every release, and build provenance is signed and verified before deploy (SLSA v1.2 Build L2+).
- [ ] Branch protection with required checks and CODEOWNERS on sensitive paths; a merge queue if the repo has more than a few merges a day.

## 2. Security & Compliance
- [ ] Least-privilege IAM/RBAC verified; zero wildcard permissions or static long-lived keys where OIDC is supported.
- [ ] TLS enforced everywhere in transit; sensitive data encrypted at rest with managed key rotation.
- [ ] Containers run as non-root with minimal base image, dropped capabilities, and read-only root filesystem.
- [ ] Rate limits, payload caps, CORS/CSP/security headers, and egress/SSRF rules active.

## 3. Reliability, Scaling & Recovery
- [ ] Explicit CPU/memory limits, autoscaling bounds (min/max), and cost/budget alarms configured.
- [ ] Distinct liveness vs. readiness probes wired (liveness never queries flaky external deps).
- [ ] Graceful shutdown drain window exceeds load-balancer deregistration delay.
- [ ] Database migrations are backward-compatible (N-1 safe); backups and restore drill verified against RPO/RTO.
- [ ] Tested rollback procedure executes in minutes (previous image digest, feature flag kill-switch, staged store halt), exercised before this release.
- [ ] New behaviour ships behind a feature flag with an owner and a removal date.

## 4. Observability & Operations
- [ ] Structured logs carry trace/correlation IDs with verified PII/secret scrubbing.
- [ ] Core SLIs/SLOs and golden-signal dashboard live (Traffic, Errors, Latency/Frame-Time, Saturation).
- [ ] Actionable symptom-based alerts routed to on-call with direct links to runbooks.
- [ ] Concise operational runbook covers: start/stop, rollback, key metrics, top 3 failure scenarios, and dependency contacts.
- [ ] DORA metrics are measured for this service (deployment frequency, change lead time, change fail rate, failed deployment recovery time, deployment rework rate).
