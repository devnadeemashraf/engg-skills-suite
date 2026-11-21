# Domain-Specific Adversarial Audit Checks

Apply alongside `references/audit-checklist-core.md` for the active project surface(s).

## Web Client Checks
- **XSS / DOM Safety:** Any unsafe HTML injection, unvalidated `javascript:` URLs, weak CSP, or tokens exposed in `localStorage`?
- **Async & State Races:** Missing `AbortController` causing stale responses to overwrite newer state? Unbounded `useEffect`/reactive loops? Unnecessary re-renders on hot state?
- **Performance & Bundle:** Missing code-splitting, unoptimized images causing CLS, unvirtualized multi-thousand-row lists, bloated third-party imports?
- **Accessibility:** Clickable `div`/`span` without semantics/keyboard support, missing labels/focus traps in modals, poor contrast?

## Mobile Client Checks
- **Main-Thread Starvation:** Any disk read, JSON parse of large payloads, DB query, or image decode on the UI thread?
- **Lifecycle & Leaks:** Listeners/subscriptions/callbacks retaining Activity/ViewController references? Unhandled process death or orientation reset wiping user form/progress?
- **Storage & Transport:** Secrets/tokens in plain `SharedPreferences`/`UserDefaults`? Unvalidated deep links / intent parameters? Cleartext HTTP allowed?
- **Offline & Battery:** Infinite retry loops draining battery offline? Missing conflict resolution on sync?

## Game Client Checks
- **Frame-Time & GC Spikes:** Per-frame heap allocations, LINQ/closures/string concatenation, or synchronous asset loads inside update/render loops?
- **Determinism & Physics:** Frame-rate-dependent physics (`dt` used without clamping/fixed step)? Floating-point drift over long sessions?
- **Save Integrity & Cheating:** Non-atomic save overwrites risking total save loss on crash? Client-trusted multiplayer state (health, currency, cooldowns, positions)?
- **Memory & Asset Leaks:** Unreleased textures, meshes, audio clips, event delegates, or scene singletons surviving level transitions?

## Database & Data Pipeline Checks
- **Migration Hazards:** `ALTER TABLE` locking hot production tables, adding non-null columns without safe defaults, destructive drops without expand-and-contract?
- **Query & Index Health:** Implicit type casts defeating indexes, leading-wildcard `LIKE '%x'`, missing composite index column order, deep `OFFSET` scans?
- **Isolation & Consistency:** Read-modify-write race without `SELECT ... FOR UPDATE`, atomic SQL update, or optimistic version column?

## Infrastructure & DevOps Checks
- **IAM & Secrets:** Wildcard IAM permissions (`*:*`), secrets baked into container layers/env files/git history, static long-lived credentials instead of OIDC?
- **Container & Runtime:** Running as `root`, `:latest` unpinned base images, missing resource limits (OOM risk), missing health probes or pod disruption budgets?
- **Deployment Safety:** Non-idempotent deploy scripts, no automated rollback trigger, missing state locking in IaC, zero blast-radius isolation between staging and prod?
