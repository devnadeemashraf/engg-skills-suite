# engg-skills-suite v2 — Refactor Plan

Status: **Draft for approval** · Target version: `2.0.0` · Repo: `github.com/devnadeemashraf/engg-skills-suite`

The aim of v2 is for the suite to do two jobs reliably:

1. **Greenfield:** build a project that is correct, secure, fast and maintainable from day one.
2. **Brownfield:** take a messy codebase, strip out what isn't needed, and reorganise and harden the rest piece by piece and layer by layer, checked against an architecture that has been written down.

The biggest change from v1: **v1 describes standards in prose and trusts the model to follow them. v2 turns every standard into something a tool checks, and every claim into something with evidence behind it.** Production engineering teams work the same way.

---

## 1. What production teams actually do (research summary)

| Practice | What it looks like | Source |
|---|---|---|
| **Small changes on trunk, always reviewed** | Nearly all development happens at head, not on long-lived branches. Every change is reviewed by at least one other engineer. Changes are kept small. Each subtree can define its own presubmit checks. | [Google eng-practices summary](https://github.com/joelparkerhenderson/ways-of-working/blob/main/doc/software-engineering-at-google/index.md) |
| **Merge queue → canary → automatic deploy** | Shopify: PR → CI → merge queue (CI runs on queued PRs, merged in batches) → automatic deploy to a canary taking a random 5% of traffic → production. Nobody presses "deploy". | [Shopify: release culture](https://shopify.engineering/software-release-culture-shopify), [merge queue](https://shopify.engineering/introducing-the-merge-queue), [automatic deployment](https://shopify.engineering/blogs/engineering/automatic-deployment-at-shopify) |
| **Feature flags plus fast rollback** | Deploying and releasing are separate steps. Flags let a change be turned off without a redeploy. | [GitHub: feature flags](https://github.blog/engineering/ship-code-faster-safer-feature-flags), [Stripe change management](https://stripe.com/careers/listing/staff-engineer-release-engineering/8038771) |
| **Measure delivery** | DORA: lead time, deploy frequency, change failure rate, time to restore. The 2025 report says AI raises output per author but adds review load, so small reviewable changes matter more now. | [DORA 2025](https://cloud.google.com/resources/devops/state-of-devops), [DORA: AI tensions](https://dora.dev/insights/balancing-ai-tensions/) |
| **Architecture is enforced by tests** | Layer and dependency rules run as tests or CI gates: ArchUnit (JVM), dependency-cruiser (JS/TS), import-linter (Python), go-arch-lint (Go), and the young archfit (cross-language, built for AI agents; see the Phase 1 note in §11). | [ArchUnit](https://archunit.org/), [archfit](https://github.com/coupling-dev/archfit) |
| **Supply-chain hygiene** | SLSA provenance, Sigstore signing, OpenSSF Scorecard, OSV for known vulnerabilities, and third-party CI actions pinned to a commit SHA. | [Scorecard](https://github.com/ossf/scorecard), [SLSA/OpenSSF](https://openssf.org/tag/slsa) |
| **Why pinning to a SHA matters (2026)** | In March 2026, attackers force-pushed malicious commits onto 76 of 77 `aquasecurity/trivy-action` version tags (CVE-2026-33634). Only workflows pinned to a SHA, plus the one immutable release, were safe. | [Aqua](https://www.aquasec.com/blog/trivy-supply-chain-attack/), [GHSA-69fq-xp46-6x23](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23) |
| **Security baseline** | OWASP ASVS 5.0.0 (May 2025): three cumulative levels, requirements cited as `v5.0.0-<ch>.<sec>.<req>`. | [OWASP ASVS](https://owasp.org/ASVS/) |
| **Fully open-source static analysis** | Semgrep's rules moved to a restrictive licence in December 2024. Opengrep is the LGPL-2.1 community fork of the engine. | [InfoQ](https://www.infoq.com/news/2025/02/semgrep-forked-opengrep), [Semgrep's own comparison](https://semgrep.dev/docs/faq/comparisons/opengrep) |

**What this means for the suite:**

- Standards stick when **a machine enforces them** (formatter, linter, architecture test, required CI check, CODEOWNERS, branch protection). Written guidance alone doesn't hold.
- Brownfield clean-ups succeed through **ratchets**: record today's violations as a baseline, block any new ones, and shrink the baseline chunk by chunk. A big-bang rewrite is the alternative that fails.
- **Rigor scales with risk.** Teams don't run the same ceremony on a README typo and on a payments migration. v1 applies maximum ceremony to everything, which wastes tokens and leads the model to skip steps.

---

## 2. Diagnosis of v1

| # | Problem in v1 | Effect | v2 fix |
|---|---|---|---|
| 1 | Standards are prose only ("enforce SOLID", "bounded everything") | The model can claim compliance without proving it | Every rule maps to a check (tool command, test, or a citation the reviewer can check) |
| 2 | No machine-readable architecture | "Does this code follow the architecture?" can't be answered mechanically | New `.engg/architecture.yaml` **Architecture Contract**, compiled into native enforcement configs |
| 3 | Whole-codebase audit (`engg-audit` Mode B) relies on the model reading and remembering | Doesn't scale past a few thousand lines; misses things; not resumable | New **`engg-deep-audit`** skill: tools build the map, review goes one unit at a time, state is kept on disk |
| 4 | No skill for restructuring existing code | Clean-up gets pushed through `engg-build`, whose test-first loop is designed for new code | New **`engg-refactor`** skill: characterization tests, deletion and move refactors, ratchets |
| 5 | Same heavy ceremony for every change | Token bloat; the model learns to skip steps | **Risk tiers T0–T3** scale the required gates |
| 6 | OSS tools are never named or installed | The model re-derives by reading what a tool computes in milliseconds | **Toolchain registry** plus a **Tool Consent Protocol** |
| 7 | The constitution is copied five times by hand | Copies will drift | One canonical copy in `shared/`, synced into skills by a build step, sync checked in CI |
| 8 | Repo hygiene gaps (README tab bug, `install.ps1` doesn't match `install.sh`, validator fails on CRLF and multi-line YAML, CI doesn't pin actions) | The suite doesn't meet its own standards | Phase 0 of the rollout |
| 9 | Overlapping triggers (audit Mode B vs a future deep audit; build vs refactor) | The agent picks the wrong skill | A strict trigger-boundary table (§8) |
| 10 | No way to tell whether v2 is better than v1 | Changes are judged by feel | Eval fixtures: seeded messy repos with known defects (§10) |

---

## 3. Core v2 concepts (used by every skill)

### 3.1 Architecture Contract — `.engg/architecture.yaml`

This is the single machine-readable source of truth for how a target codebase must be structured. `engg-architect` writes it (greenfield) or ratifies it from an as-is draft (brownfield). `engg-deep-audit`, `engg-audit`, `engg-extend` and `engg-refactor` read it.

```yaml
version: 1
style: hexagonal            # hexagonal | clean | layered | feature-sliced | mvvm | ecs | modular-monolith
languages: [typescript]
layers:                     # ordered inner → outer; a layer may depend only on layers listed before it
  - name: domain
    paths: ["src/*/domain/**"]
    may_import: []                       # pure: no framework, I/O, or SDK
    forbid_external: ["*"]               # except allowlist below
    allow_external: ["zod"]
  - name: application
    paths: ["src/*/app/**"]
    may_import: [domain]
  - name: adapters
    paths: ["src/*/adapters/**"]
    may_import: [domain, application]
  - name: transport
    paths: ["src/*/http/**", "src/*/ui/**"]
    may_import: [application, domain]
  - name: composition
    paths: ["src/main.ts", "src/wiring/**"]
    may_import: ["*"]
modules:                    # vertical slices: talk only through public entrypoints
  isolation: strict
  public_entry: "index.ts"
  cross_module: via_public_entry_only
rules:
  no_cycles: true
  max_file_loc: 400
  max_function_cyclomatic: 12
  max_fan_out: 15
budgets:                    # surface-specific, optional
  http_p99_ms: 300
  bundle_kb_gz: 180
baseline: .engg/baseline/   # existing violations recorded; CI blocks only new ones
```

The suite **compiles** this contract into the target ecosystem's native enforcer, so the same rules run in the IDE, pre-commit and CI:

| Ecosystem | Enforcer generated |
|---|---|
| JS/TS | `.dependency-cruiser.cjs` (+ `knip.json`) |
| Python | `.importlinter` contracts |
| JVM / .NET | ArchUnit / ArchUnitNET test class |
| Go | `go-arch-lint` config |
| Multi-language (optional, experimental) | `archfit` `.archfit.yaml`, only alongside the native enforcers above, never as the only gate |

The compiler is a script in `shared/scripts/compile_contract.py`: deterministic and unit-tested. The model never hand-writes these configs.

### 3.2 Evidence Protocol (accuracy)

- **Every finding cites a source:** `file:line`, or a tool result ID (SARIF rule, dependency-cruiser violation, graphify edge with its `EXTRACTED`/`INFERRED` tag).
- **Nothing counts as "verified" until a command ran and exited 0.** The skill shows the command and the tail of its output.
- **High-impact claims need two independent signals.** Before declaring code dead, or deleting or moving it, two of these must agree: static tool (knip/vulture/deadcode), reference search (ripgrep/ast-grep, including strings and reflection), coverage data, graphify fan-in = 0.
- **Tool output is evidence, not verdict.** The model triages false positives explicitly (`TRUE` / `FALSE-POSITIVE: reason` / `NEEDS-HUMAN`).
- **Versions, flags and API signatures come from live sources only** (engg-research), never from memory.

### 3.3 Risk Tiers (rigor proportional to risk)

| Tier | Example | Required gates |
|---|---|---|
| **T0 Trivial** | Docs, copy, config value | Format + lint |
| **T1 Standard** | Internal logic, UI component | T0 + unit tests (happy + boundary) + typecheck + architecture check |
| **T2 Sensitive** | Public API, persistence, concurrency, performance-critical path | T1 + all 5 test-matrix categories + contract tests + `engg-audit` |
| **T3 Critical** | Authn/authz, money, PII, migrations, crypto, infrastructure | T2 + mutation testing on changed code + SAST/secret/dependency scan + threat-model note + human approval gate |

`engg-plan` assigns a tier to each chunk. `engg-build`, `engg-audit` and `engg-ship` read it.

### 3.4 Ratchet

For brownfield code, run each enforcer once, store the violations in `.engg/baseline/`, and make CI fail only on **new** violations. Each remediation chunk must **shrink** the baseline, and a script checks the count only goes down. This is how large organisations adopt strict rules on legacy code without stopping delivery.

### 3.5 Disk-backed state (stop relying on the model's memory)

Long-running skills (`engg-deep-audit`, `engg-refactor`, `engg-roadmap`) keep their working state in the target repo:

```
.engg/
  architecture.yaml        # committed
  baseline/                # committed (ratchet)
  toolchain.lock           # committed: tool name → version → install method
  audit/<run-id>/          # git-ignored by default
    raw/                   # tool outputs (JSON/SARIF)
    map.md                 # system map (sizes, layers, hotspots, god nodes)
    ledger.jsonl           # one line per unit: status, findings, summary
    findings/<unit>.md
    REPORT.md
```

Every step reads only what it needs from disk. A crashed or context-compacted session resumes from `ledger.jsonl`.

### 3.6 Tool Consent Protocol

Each skill that benefits from a tool follows this protocol (`shared/references/tool-consent.md`):

1. **Detect:** `shared/scripts/toolcheck.(sh|ps1)` reports which tools are installed and at what version. It is read-only.
2. **Propose:** for each missing tool, ask once in a grouped message:
   > **graphify** (Apache-2.0/MIT, Python) — builds a local code knowledge graph with tree-sitter. Code is parsed offline; nothing leaves your machine. **Why:** the audit can ask "what depends on X" instead of reading hundreds of files, which cuts tokens and catches dependencies a reader would miss. **Install:** `uv tool install graphifyy` · **Remove:** `uv tool uninstall graphifyy`. Install? [yes / no / yes to all listed]
3. **Verify before installing:** check the current version, licence and advisories via `engg-research` (registry CLI or OSV). Prefer installs that are user-scoped and easy to remove (`uv tool`, `pipx`, `npx`, `go install`, `cargo binstall`, a project dev-dependency). Never use `sudo` or a global system package without explicit approval. Watch for name collisions (for example only-cli's `oc` binary clashes with OpenShift's `oc`; offer `npx @only-cli/oc` instead).
4. **Record:** write the chosen version to `.engg/toolchain.lock` so CI and other machines use the same one.
5. **Degrade gracefully:** if the user declines, use the documented fallback (ripgrep, git, the language's built-in tooling) and **state which accuracy is lost**.

---

## 4. Open-source toolchain registry

`shared/references/toolchain.md` is the canonical copy, synced into skills. Versions are **not** pinned in the suite; they are resolved live at install time and written to `toolchain.lock`.

| Job | Default (cross-language) | Per ecosystem | Used by |
|---|---|---|---|
| **Web/docs reading with fewer tokens** | `oc` (only-cli, MIT): `oc open`, `oc raw`, `--budget` (≈500 tokens/page by default; no JS rendering yet) | — | research, all |
| **Code knowledge graph** | `graphify` (code-only and offline by default): `graphify update .`, `query`, `path`, `explain`, `graphify-mcp`; output `graphify-out/graph.json`, `GRAPH_REPORT.md` | — | deep-audit, audit, refactor, extend, roadmap |
| **Fast search / structural search** | `ripgrep`, `ast-grep` | — | all |
| **Repo inventory / size** | `scc` (LOC, languages, complexity estimate) | — | deep-audit, roadmap |
| **Architecture conformance** | Native per ecosystem (right) · `archfit` optional/experimental | dependency-cruiser · import-linter / grimp · ArchUnit · go-arch-lint | architect, deep-audit, audit, ship |
| **Complexity** | `lizard` (many languages) | ESLint complexity · radon · gocyclo | deep-audit, refactor |
| **Duplication** | `jscpd` | — | deep-audit, refactor |
| **Dead code / unused dependencies** | — | knip · vulture · `deadcode` (Go) · cargo-udeps / cargo-machete | deep-audit, refactor |
| **SAST** | `opengrep` (LGPL-2.1) with community rules | gosec · bandit · Roslyn analyzers | audit, deep-audit, ship |
| **Secrets** | `gitleaks` (pre-commit) + `trufflehog` (CI, verifies whether keys are live) | — | audit, deep-audit, ship |
| **Dependency vulnerabilities** | `osv-scanner` | `npm audit` · `pip-audit` · `govulncheck` · `cargo audit` | research, deep-audit, ship |
| **SBOM / image scanning** | `syft` + `grype` (or `trivy`, **pinned by digest/SHA**) | — | ship |
| **CI / IaC / container lint** | `actionlint`, `zizmor` (GitHub Actions security), `hadolint`, `checkov` or `trivy config` | tflint · kube-linter | ship |
| **Repo security posture** | OpenSSF `scorecard` | — | ship, deep-audit |
| **Migration safety** | `squawk` (Postgres) / Atlas lint | sqlfluff | data |
| **Testing depth** | Property tests: fast-check · Hypothesis · proptest. Mutation: Stryker · mutmut · cargo-mutants · PIT | — | build, refactor (T3) |
| **Profiling** | `perf` / `samply`, `py-spy`, `pprof`, clinic.js / 0x, `EXPLAIN (ANALYZE, BUFFERS)` | — | debug |
| **Git hooks / tool pinning** | `lefthook` or `pre-commit`; `mise` for pinning tool versions per repo | — | ship, build |
| **Dependency updates** | Renovate (self-hosted CLI or app) | — | ship |
| **Load / web performance / accessibility** | `k6`, Lighthouse CI, `axe-core` CLI | — | ship, build |

Tool facts above come from project READMEs and listings (graphify, oc, archfit, Opengrep) or well-established tools. Phase 1 re-verified every entry against its repository; the result is `shared/references/toolchain.md`, which supersedes this table where they differ.

---

## 5. New skill: `engg-deep-audit`

**Purpose:** audit an entire codebase layer by layer and unit by unit against its Architecture Contract. Tools build the map; the model only judges what tools can't. The skill is **read-only**: it produces a report, a strip list and a remediation plan, and never edits production code.

**Triggers:** "audit the whole repo", "go through this codebase layer by layer", "how far is this repo from its architecture", onboarding onto a messy project.
**Not triggered by:** a diff or PR (→ `engg-audit`) or a spec (→ `engg-audit` Mode Spec).

### Workflow

**Phase 0: Preflight**
- Working tree is clean (or the run is labelled "dirty").
- Detect the stack.
- Run `toolcheck`, then the Tool Consent Protocol.
- Create `.engg/audit/<run-id>/` and add it to `.gitignore`.

**Phase 1: Machine map (deterministic, no model reading code)**

All of these write to `raw/`:
- `scc --format json`
- `graphify update .` (code-only)
- native dependency graph and architecture report (dependency-cruiser / import-linter / ArchUnit / go-arch-lint; `archfit analyze` as an optional extra)
- `lizard` (complexity)
- `jscpd` (duplication)
- dead-code tool for the stack
- `gitleaks`
- `opengrep --sarif`
- `osv-scanner`
- `hadolint` / `actionlint` / `zizmor` / `checkov` where relevant
- git history: churn per file (`git log --numstat` over 12 months), authors, last-touched dates
- tests: run the suite once, with coverage if available

`shared/scripts/build_map.py` merges these into `map.md`:
- size per layer and module
- **hotspots** (churn × complexity)
- **god nodes** and communities (graphify)
- cycles
- untested hotspots
- a summary of tool findings by category

**Phase 2: Contract gate**
- If `.engg/architecture.yaml` is missing, **stop**. Offer to draft an as-is contract from graphify communities and the directory layout, then hand off to `engg-architect` (brownfield mode) to ratify the to-be contract.
- **An audit without an agreed architecture isn't run.**
- Otherwise, run the native enforcer compiled from the contract and record every layer violation, cycle and forbidden import as `ARCH-*` findings.

**Phase 3: Plan the traversal**
- Split the repo into **units**: a module × layer slice of about 300–800 LOC, split further if larger.
- Order units **bottom-up by layer** (domain → application → adapters → transport/UI → composition → build/CI/infra), so inner layers are judged before the code that depends on them.
- Within a layer, order by risk (hotspot score, T3 tags such as auth or payments, fan-in).
- Write `ledger.jsonl`, one line per unit with status `pending`.

**Phase 4: Unit-by-unit review (context-bounded loop)**

For each unit, load **only**:
- the unit's files
- its contract slice (which layer, what it may import)
- its raw tool findings
- its graph neighbourhood (`graphify explain <symbol>` / `query --budget N` for callers and callees)

Then:
1. Review it against `references/unit-checklist.md`, the six v1 pillars made concrete with per-layer questions. Example for domain: "zero I/O imports? invariants enforced in constructors? errors typed?"
2. Triage each tool finding (true / false-positive / needs-human).
3. Add judgment findings, each with a citation and a severity (P0–P3).
4. Tag each finding with an **action class**: `STRIP` (delete), `MOVE` (wrong layer/module), `SPLIT`, `MERGE` (duplication), `HARDEN` (security/bounds), `TEST` (missing proof), `SIMPLIFY`.
5. Write `findings/<unit>.md` and a five-line summary to the ledger, mark the unit done, and **drop the unit's content from working context**.

Checkpoint with the user every N units, or at each layer boundary (configurable).

**Phase 5: Layer synthesis**
- Read the ledger summaries per layer, not the code, and find cross-unit patterns: the same validation in five handlers, an adapter leaking through every service, an inconsistent error model.
- Spot-check with targeted graphify queries.

**Phase 6: System report — `REPORT.md`**
- **Scorecard (1–5):** Correctness, Security, Performance, Reliability, Architecture Conformance, Testability, Simplicity (new: measures dead code, duplication and over-abstraction).
- **Strip List:** everything proposed for deletion, each with its two-signal evidence. Grouped as unused files/exports/dependencies, dead feature flags, duplicate implementations, speculative abstractions with one implementation, and abandoned scripts and configs.
- **Move/Reorganise List:** the target location for each misplaced piece, per the contract.
- **Severity-ranked findings:** P0 to P3.
- **Remediation waves**, ready for `engg-plan`:
  - **Wave 1:** safety-net tests on hotspots, plus P0 fixes, plus the CI ratchet installed
  - **Wave 2:** Strip List (cheap and high-value: less code to harden)
  - **Wave 3:** P1 hardening (bounds, timeouts, authz, leaks)
  - **Wave 4:** Move/Split/Merge to reach the contract, layer by layer from the inside out
  - **Wave 5:** P2/P3 simplification

**Phase 7: Enforcement handoff**
- Generate (don't apply) the enforcement configs from the contract, plus the baseline.
- Propose the CI and pre-commit wiring so the codebase can't drift back. Applying it is the first chunk of Wave 1.

### Files

```
skills/engg-deep-audit/
  SKILL.md                          (<150 lines)
  references/unit-checklist.md      per-layer review questions
  references/finding-schema.md      ID, severity, action class, evidence fields
  references/tool-recipes.md        exact commands per ecosystem, output → raw/
  references/toolchain.md           (synced from shared/)
  references/tool-consent.md        (synced)
  references/architecture-contract.md (synced)
  scripts/toolcheck.sh|ps1          (synced)
  scripts/build_map.py              merge raw outputs → map.md, hotspot scores
  scripts/ledger.py                 init / next-unit / mark-done / summary
```

---

## 6. New skill: `engg-refactor`

**Purpose:** carry out the deep-audit remediation waves (or any behaviour-preserving restructure) safely, one chunk at a time.

**Kept separate from `engg-build`** because the loop is different: build is *test → new behaviour*; refactor is *pin current behaviour → change structure → prove behaviour unchanged*.

**Loop for each chunk:**

1. **Pin behaviour.** Add characterization tests (snapshot/approval or golden-master) around the affected surface until coverage of the touched code meets the threshold for its tier.
2. **Ratchet check before.** Record the baseline count for the violations this chunk targets.
3. **One kind of transformation per commit:**
   - `STRIP`: delete only after the two-signal evidence is re-verified at HEAD, then run the full test suite and build.
   - `MOVE`: move the code, update imports, run the architecture check.
   - Use the language's automated refactoring where possible (IDE/LSP rename, `ast-grep` rewrite rules) instead of hand edits.
4. **Prove nothing changed:** tests green, architecture check green, baseline strictly smaller, public API diff empty unless intended (api-extractor / `cargo public-api` / similar), no performance regression on any budgeted path.
5. **Atomic conventional commit** (`refactor:` / `chore: remove dead …`), then `engg-audit` on the diff.

**Strangler fig** for the big moves: build the new module behind the port, switch callers over in small batches, then delete the old path. Never do a big-bang rewrite.

---

## 7. Changes to existing skills

| Skill | v2 changes |
|---|---|
| **engg-ideate** | Add a "build vs buy vs OSS" check that names concrete open-source candidates (verified through research). Make the charter's success metrics measurable. Otherwise minor. |
| **engg-roadmap** | Reality check uses `scc` + graphify + `map.md` from a deep audit, instead of the model reading the repo. Add DORA baseline metrics from git history (lead time and deploy frequency where measurable). Route to `engg-deep-audit` when foundations are unknown. |
| **engg-architect** | **Writes `.engg/architecture.yaml`**, C4 context/container diagrams (Mermaid), and ADRs in MADR format. Generates the native enforcement configs with `compile_contract.py`. Adds a **brownfield mode**: as-is draft from the graph → grill → ratified to-be contract plus the migration delta. Chooses an ASVS 5.0 level for the threat model. Defaults to a modular monolith unless budgets prove otherwise. |
| **engg-plan** | Each chunk card gains **Risk Tier**, **Gates** (exact commands that must exit 0), **Ratchet delta** (expected baseline reduction) and **Rollback**. Can ingest the deep-audit `REPORT.md` waves directly. Keeps chunks small enough for review (DORA review-load finding). |
| **engg-build** | Gates come from the tier rather than "all five categories always". Add property-based tests for parsers and invariants, and mutation testing on changed code at T3. The architecture check is part of the green bar. Adds a pre-commit wiring step in chunk 1 (lefthook/pre-commit, formatter, linter, gitleaks, architecture check). |
| **engg-extend** | Reads the contract to find which layer and module the new slice or adapter belongs to. Generated architecture rules must still pass. Contract tests stay. Uses graphify to find the reference slice to copy conventions from. |
| **engg-audit** | **Narrowed to diffs/PRs and specs.** Mode B moves to `engg-deep-audit`. Diff mode adds: blast radius via graphify neighbours of changed symbols; diff-scoped opengrep, gitleaks and architecture check; the Evidence Protocol. Spec mode adds an ASVS level check and verification of stale claims through research. |
| **engg-research** | Fetches docs with `oc` (falling back to the agent's web tool), checks registries through CLIs (`npm view`, `pip index versions`, `go list -m -versions`, `cargo search`), checks advisories through OSV, and checks repo health through Scorecard. Writes a dated Research Brief with every source URL. Pins CI actions by SHA and images by digest. |
| **engg-debug** | Per-stack profiler matrix from the registry. Uses `git bisect run` with the reproduction script. Every fix carries a regression test, plus an evidence table showing before/after numbers. |
| **engg-data** | Lints migrations with squawk or Atlas in CI. Reviews query plans with `EXPLAIN (ANALYZE, BUFFERS)` on realistic data. Backfill script template with checkpoint and resume. PII inventory columns go in the contract. |
| **engg-ship** | Adds a **merge queue**, **canary/progressive delivery**, **feature flags (OpenFeature)** and DORA measurement. **CI actions pinned by SHA**, with `zizmor` and `actionlint`, using the Trivy 2026 incident as the worked example. SLSA provenance and Sigstore signing. Scorecard in CI. Renovate configured with grouping and an automerge policy. Required status checks and CODEOWNERS. Generated pipeline templates per platform (GitHub Actions first). |

**Shared constitution changes** (`shared/references/engineering-constitution.md`):
- Add a **Simplicity / YAGNI deletion rule**: code that isn't used is a liability.
- Add the **Evidence Protocol**, **Risk Tiers** and **Ratchet** sections.
- Turn each principle into a "how this is checked" line. For example, *DIP → enforced by the architecture contract's `may_import`*; *Bounded Everything → opengrep rules for missing timeouts plus review checklist item*.

---

## 8. Trigger boundaries (no overlap)

| User intent | Skill |
|---|---|
| Vague idea → charter | ideate |
| Existing roadmap → hardened roadmap | roadmap |
| Design / define the architecture contract | architect |
| Spec or report → chunks | plan |
| New behaviour, test-first | build |
| New slice or adapter in an existing architecture | extend |
| Review a **diff, PR or spec** | audit |
| Review a **whole codebase or subsystem** against the contract | **deep-audit** |
| Restructure or clean up **without changing behaviour** | **refactor** |
| Bug / performance problem | debug |
| Schema / migration / query | data |
| CI/CD, release, infrastructure | ship |
| Library / version / API facts | research |

**Brownfield loop:**

```
deep-audit → (architect, if no contract) → plan(REPORT waves) → [refactor | build] → audit → ship → re-run deep-audit (baseline shrinking)
```

---

## 9. Repository changes

```
engg-skills-suite/
  shared/                          # canonical single source of truth
    references/  engineering-constitution.md, toolchain.md, tool-consent.md,
                 architecture-contract.md, evidence-protocol.md, risk-tiers.md
    scripts/     toolcheck.sh, toolcheck.ps1, compile_contract.py
    manifest.yaml                  # which shared files each skill gets
  skills/<13 skills>/              # self-contained after sync (still installable one at a time)
  tools/
    sync_shared.py                 # copies shared/ → skills/ per manifest
    validate_suite.py              # upgraded (see below)
  evals/                           # §10
  tests/                           # pytest for scripts and validator
  CHANGELOG.md
```

**Validator upgrades:**
- Parse frontmatter with a real YAML parser, so CRLF and multi-line values work.
- Require `license` and `metadata.version`.
- Check the spec limits: `compatibility` ≤ 500 characters, `allowed-tools` format.
- Check references are at most one level deep.
- Fail if any synced file differs from `shared/`.
- Fail if a SKILL.md is over 150 lines (the suite's own budget; the spec limit is 500).
- Run the official `skills-ref validate` on every skill as well.
- Script tests: pytest for Python, `shellcheck`, and PSScriptAnalyzer.

**Installer fixes:**
- `install.ps1` gets the same behaviour as `install.sh`: a canonical store plus symlinks or junctions, with a `-Copy` switch.
- Clear error when `--project` is given without a path.
- Both installers get `--uninstall` and `--dry-run`.
- Both are tested in CI on ubuntu, macos and windows.

**Dogfooding the suite's own CI:**
- Actions pinned by SHA, plus `zizmor`, `actionlint` and Scorecard.
- Renovate for action bumps.
- Signed releases with a CHANGELOG.

**README:**
- Fix the tab bug.
- Replace `<your-username>` with `devnadeemashraf`.
- Add a "Toolchain & consent" section and the brownfield loop.

---

## 10. Proving v2 is better: evals

Under `evals/`, add 3–4 small **fixture repos with seeded defects**, each with an answer key (`expected.yaml`):

| Fixture | Seeded problems |
|---|---|
| `ts-messy-api` | Layer violation (domain imports ORM), import cycle, dead export + unused dependency, duplicated validation ×3, missing timeout on an HTTP client, hardcoded secret, IDOR in one handler, no tests on the hotspot |
| `py-flask-legacy` | Same categories, Python flavour (import-linter, vulture, bandit/opengrep) |
| `go-service` | Goroutine leak, unbounded query, `deadcode`, `govulncheck` hit |
| `clean-reference` | A clean repo, to measure false positives |

**Metrics:**
- deep-audit **recall** of seeded defects
- **false-positive rate** on `clean-reference`
- tokens per 1k LOC audited (v1 Mode B compared with v2)
- resumability: kill the run mid-way and resume from the ledger

A run script records results per model. The release gate for 2.0.0 is: recall ≥ 90% and no P0/P1 false positives on `clean-reference`.

---

## 11. Rollout (each phase is a set of atomic commits)

| Phase | Scope | Exit criteria |
|---|---|---|
| **0. Hygiene** | README fixes, installer parity, validator upgrades (YAML parsing, CRLF), CI pinned by SHA + actionlint/zizmor, pytest/shellcheck | CI green on 3 operating systems; validator catches a seeded CRLF/multi-line case |
| **1. Shared core** | `shared/` + `sync_shared.py` + manifest; new constitution sections (Evidence, Tiers, Ratchet, Simplicity); `toolchain.md` (verified live) + `tool-consent.md`; `toolcheck.sh/.ps1` | Sync check in CI; toolcheck runs on Windows, macOS and Linux |
| **2. Architecture Contract** | Schema + docs; `compile_contract.py` → dependency-cruiser, import-linter, go-arch-lint (ArchUnit later; archfit optional); unit tests; architect writes the contract | Compiled configs flag the seeded layer violation in the ts and py fixtures |
| **3. engg-deep-audit** | Skill + `build_map.py` + `ledger.py` + checklists; eval fixtures | Meets the §10 release-gate metrics on the fixtures |
| **4. engg-refactor** | Skill + characterization-test guidance + ratchet script | Executes Waves 1–2 on `ts-messy-api` with tests green and the baseline shrinking |
| **5. Upgrade the 11 existing skills** | Per §7, one skill per commit; audit narrowed; tiers wired through plan/build/audit/ship | Validator + evals green; trigger table has no overlaps |
| **6. Release 2.0.0** | CHANGELOG, migration notes from v1 (Mode B → deep-audit), signed tag | Dogfood: run deep-audit on one of your real projects and review the report together |

---

### Phase 1 findings (2026-11-22)

- **archfit is not ready to be the default.** The original repository was archived on 2026-11-20 and moved to `coupling-dev/archfit` (v0.9.0, 0 stars, 3 contributors at the time of checking). Native, mature enforcers per ecosystem are the default for the Architecture Contract; archfit stays optional and experimental.
- **Licences checked.** TruffleHog, Renovate and k6 are AGPL-3.0, and hadolint is GPL-3.0. That's fine for running them as CLIs; the registry notes it.
- **only-cli 0.5.8 has no `--version` flag** (the 0.5.10 README lists one). `toolcheck` identifies `oc` by its `--help` text instead, which also catches OpenShift's `oc`.
- **Simplification:** the Evidence Protocol, Risk Tiers and Ratchet live as sections of the shared constitution, not as separate files. The architecture contract reference arrives in Phase 2.

### Phase 2 findings (2026-11-22)

- **dependency-cruiser rejects regexes with nested quantifiers** (its safe-regex check), and then refuses to run at all. The obvious glob translations (`(?:[^/]+/)*`, `(?:/.*)?`) trip it. The compiler now emits only unnested forms, and a test enforces this.
- **dependency-cruiser 18.8.0 excludes TypeScript 7.0.x** (supported: `<7.0.0 || >=7.1.0`), so TypeScript is pinned to 6.0.3. Revisit when 7.1 ships.
- **import-linter checks indirect imports by default.** The compiler sets `allow_indirect_imports = True`, so every target enforces the same thing: direct imports between layers.
- **Coverage gaps are reported, not hidden.** import-linter can't express external allowlists, public-entry exceptions, or cycles; go-arch-lint has no module isolation. The compiler's coverage report marks these NOT COVERED. The deep audit (Phase 3) checks them from the code graph instead.
- **Generated configs go to `.engg/generated/`**, so they never overwrite a project's own `.dependency-cruiser.*` or `.importlinter`.
- go-arch-lint output is verified structurally only; running the real binary in CI is a follow-up.

### Phase 3 findings (2026-11-22)

- **graphify import edges point at files, not symbols**, so "unreferenced symbol" from the graph alone was 18 candidates with many false hits. The map now requires a second signal (no other file mentions the name, and its own file mentions it only at its definition) and skips entry layers. That brought the list down to exactly the 4 truly dead functions, with zero on the clean fixture.
- **gitleaks stores the secret itself in its JSON report unless run with `--redact`.** The recipe always redacts, and scans git history (`gitleaks git`) so deleted-but-committed secrets are caught.
- **osv-scanner exits 128 when a repo has no lockfiles.** That isn't an error; the recipe records "not applicable".
- **lizard's CSV has no header, and both lizard and jscpd report backslash paths on Windows, relative to the scanned folder.** The map normalises and resolves them; the recorded real outputs in the tests keep this covered.
- **YAML reads an unquoted `TRUE` as a boolean**, which broke triage validation on the first hand-written findings file. Fixed, with a regression test.
- `.git/info/exclude` keeps audit artefacts out of git without touching the project's `.gitignore`, so no permission is needed.
- **The tools found defects the author hadn't listed.** dependency-cruiser flagged two real contract breaches in the messy fixture beyond the planted ones, and review found three more. The answer key now has 20 defects.
- **Eval honesty:** the dry run's 100% recall was by the fixtures' author and only proves the pipeline. A fair recall number needs a fresh agent that has never seen the fixtures. The clean fixture's tool-level zero-false-alarm result is objective and runs in CI.
- Scope: one language (TypeScript) of fixtures so far. The Python and Go fixtures from §10 are follow-ups.

## 12. Decisions needed from you

1. **Names:** `engg-deep-audit` and `engg-refactor`? (Alternatives: `engg-xray`, `engg-conform`, `engg-restructure`.)
2. **Is `.engg/audit/` output committed in target repos?** Proposal: commit `architecture.yaml`, `baseline/` and `toolchain.lock`; git-ignore the audit runs.
3. **graphify semantic pass:** keep it **off by default** (code-only, fully offline), and allow it per run for docs/PDFs, which sends content to a model?
4. **Antigravity/Gemini install paths:** keep them in v2 or narrow to the open-standard `.agents/skills` plus Claude Code?
5. **Proceed with Phase 0** (hygiene) right away, since it's independent of the other decisions?
