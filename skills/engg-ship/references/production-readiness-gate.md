# Production Readiness Gate (PRR) Checklist

Complete before first production launch or major architectural rollout.

## 1. Build, Supply Chain & Artifacts
- [ ] All dependencies, base images, and CI actions are pinned with lockfiles/digests/SHAs.
- [ ] CI enforces format, lint, typecheck, tests, race/static checks, SAST, secret scanning, and CVE audit.
- [ ] Single immutable build artifact promoted across environments; zero secrets embedded in build outputs or client bundles.

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
- [ ] Tested rollback procedure executes in minutes (previous image tag, feature flag kill-switch, staged store halt).

## 4. Observability & Operations
- [ ] Structured logs carry trace/correlation IDs with verified PII/secret scrubbing.
- [ ] Core SLIs/SLOs and golden-signal dashboard live (Traffic, Errors, Latency/Frame-Time, Saturation).
- [ ] Actionable symptom-based alerts routed to on-call with direct links to runbooks.
- [ ] Concise operational runbook covers: start/stop, rollback, key metrics, top 3 failure scenarios, and dependency contacts.
