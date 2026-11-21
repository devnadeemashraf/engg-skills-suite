# Universal Grill Session Question Bank

Select and adapt 6–10 sharp questions per round based on the project's active surfaces. Do not dump all questions at once.

## Round 1: Mission, Scope & Bounded Contexts
- Is this a **reusable golden template** or a **specific product**? Which boundaries must stay swappable vs. opinionated?
- What are the exact 2–4 core Day-1 workflows that define success?
- What are the **explicit non-goals** this architecture must deliberately refuse to support in V1?
- Which surfaces are in scope (backend, web, mobile, game, data, infra), and what is the contract boundary between them?
- Monorepo (shared contracts/packages) or standalone repositories?

## Round 2: Performance Budgets, Scale & Failure Modes
- **Backend / Data:** Day-1 vs. 12-month RPS, burst multiplier, p50/p95/p99 latency budgets, availability SLO, RPO/RTO, max payload sizes.
- **Web Client:** Target devices/network conditions (low-end mobile on 3G?), Core Web Vitals budgets (LCP/INP/CLS), JS bundle size cap, SSR vs. CSR vs. static needs.
- **Mobile Client:** Min OS versions, cold-start budget, offline-first requirements, background sync limits, battery/memory constraints.
- **Game Client:** Target hardware/platforms, hard frame-time budget (16.67ms vs. 8.33ms), memory/VRAM budget, deterministic physics or multiplayer tick rate.
- **Degradation:** What happens when a dependency stalls, the network drops, storage fills, or a frame budget spikes? Fail fast, degrade gracefully, serve stale cache, or queue locally?

## Round 3: Stack, Contracts & State/Data Design
- What language, runtime, framework, or engine is preferred—or should we select one driven by latency, team skill, and ecosystem constraints?
- Are we going **contract-first** (OpenAPI, Protobuf, JSON Schema, GraphQL SDL, typed IPC/packets) or code-first with strict runtime boundary validation?
- Where is **strong consistency** mandatory vs. **eventual consistency / optimistic UI** acceptable?
- How do schema migrations, API versioning, or client save-file upgrades work without breaking active users?
- Which operations must be strictly **idempotent** to survive retries, double-clicks, or packet replays?
- How will core domain logic remain decoupled from frameworks, UI libraries, databases, or game engines (Ports & Adapters)?

## Round 4: Security, Privacy & Trust Boundaries
- Where are the exact trust boundaries? (Remember: web, mobile, and game clients are untrusted environments.)
- What authentication and authorization model fits (OIDC/OAuth2, passkeys, mTLS, API keys; RBAC, ABAC, ReBAC)?
- Is the system multi-tenant? How is tenant isolation enforced structurally at the data layer to eliminate cross-tenant IDOR?
- What sensitive data (PII, payment, credentials, telemetry) enters the system, and what compliance/retention/erasure rules apply?
- How are secrets injected and rotated across local dev, CI, and production?
- What are the top abuse vectors (credential stuffing, scraping, SSRF, XSS/CSRF, client tampering/cheating, DoS via expensive queries)?

## Round 5: Observability, Verification & Operational Lifecycle
- What telemetry stack/standard will collect structured logs, metrics, traces, or client crash/performance reports?
- What should one-command local dev and test execution look like (ephemeral containers, seed data, deterministic fixtures)?
- What CI gates are mandatory before merge (formatting, strict lint, typecheck, SAST, dependency audit, unit/integration/contract tests, coverage threshold)?
- What is the target deployment/distribution channel (containers/K8s, serverless, CDN/edge, App Store/Play Store, Steam/itch/consoles), and what is the rollback plan?

## Staff Engineer Pushback Playbook
- **"Just standard auth / standard UI / standard DB":** Demand specifics on verification, isolation, failure handling, and data modeling.
- **"Make it infinitely scalable":** Anchor to concrete orders of magnitude (100 vs. 10k vs. 1M users). Premature scale destroys velocity.
- **"We will add tests / security / observability later":** Refuse. Retrofitting observability, test harnesses, and trust boundaries costs 10x more than wiring them in Wave 1.
- **"Pick best practice":** Propose ONE concrete choice, state its primary trade-off in one line, and record it under Assumptions for explicit sign-off.
