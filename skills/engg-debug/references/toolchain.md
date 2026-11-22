# Open-Source Toolchain Registry

Tools that make engineering work faster, cheaper in tokens, and more accurate than reading code by hand. Every tool here is free and open source.

- **Versions are not pinned here.** Resolve the current stable version live at install time, then record it in `.engg/toolchain.lock`.
- **Follow `tool-consent.md` before installing anything.**
- Licences and project health were checked against each project's repository on 2026-11-22.
- Licence notes: **AGPL/GPL** tools are fine to *run* as CLIs. Get legal review before modifying and redistributing them, or offering them as a hosted service.

## Reading and navigating code

| Tool (command) | Job | Licence | Install (user-scoped) | If declined |
|---|---|---|---|---|
| **graphify** (`graphify`) | Builds a local code knowledge graph with tree-sitter: callers and callees, god nodes, communities, paths between symbols. Code is parsed offline. Its optional doc/PDF pass sends content to a model, so keep it **off** unless the user agrees. | Apache-2.0 | `uv tool install graphifyy` or `pipx install graphifyy` (package name has **two y's**; other `graphify*` packages are unaffiliated). Update the graph with `graphify update .`, query with `graphify query "<question>"`, `graphify path "<A>" "<B>"`, `graphify explain "<symbol>"` | `rg` reference searches per symbol; state that indirect and inferred edges are missed |
| **ripgrep** (`rg`) | Fast text search that respects `.gitignore` | Unlicense / MIT | `brew install ripgrep`, `scoop install ripgrep`, `winget`, or a release binary | `git grep` |
| **ast-grep** (`ast-grep`, `sg`) | Structural search and rewrite by syntax-tree pattern: precise refactors, custom lint rules | MIT | `npm i -g @ast-grep/cli`, `pip install ast-grep-cli`, `brew install ast-grep` | `rg` with careful regexes (more false hits) |
| **scc** (`scc`) | Lines of code, languages, and rough complexity per file and directory | MIT | `brew install scc` or a release binary | `git ls-files` + `wc -l` |

## Reading the web with fewer tokens

| Tool | Job | Licence | Install | If declined |
|---|---|---|---|---|
| **only-cli** (`oc`) | Turns a web page into compact, numbered text (about 500 tokens by default; `--budget N`). `oc open <url>`, `oc read <n>`, `oc raw <url>` for whole-page markdown. Doesn't render JavaScript yet: exit code 2 means a JS-only page or a bot wall. | MIT | `npx @only-cli/oc` (no install), or `npm i -g @only-cli/oc` (Node 20+). **Name clash:** OpenShift also installs `oc`. If toolcheck reports `conflict`, use `npx @only-cli/oc`. | The agent's built-in web fetch |

## Architecture conformance

| Tool | Job | Licence | Install | If declined |
|---|---|---|---|---|
| **dependency-cruiser** (JS/TS) | Layer, path, and cycle rules on the module graph | MIT | Project dev-dependency: `npm i -D dependency-cruiser` | Import search with `rg` |
| **import-linter** (Python) | Layer, independence, and forbidden-import contracts | BSD-2-Clause | `pip install import-linter` in the project's dev environment | Import search with `rg` |
| **ArchUnit** (JVM) | Architecture rules written as unit tests | Apache-2.0 | Test dependency in the build file | Package-import review |
| **go-arch-lint** (Go) | Component and dependency rules for Go modules | MIT | `go install` from the project's releases | `go list -deps` review |
| **archfit** (multi-language) | Checks changes against a declared `.archfit.yaml`; output is designed for agents. **Experimental:** the project moved to `coupling-dev/archfit` in Nov 2026 (v0.9.0). Don't make it the only gate yet. | Apache-2.0 | `brew install coupling-dev/tap/archfit` or `go install github.com/coupling-dev/archfit/cmd/archfit@latest` | The per-language tools above |

## Complexity, duplication, dead code

| Tool | Job | Licence | Install | If declined |
|---|---|---|---|---|
| **lizard** | Cyclomatic complexity and function length across many languages | MIT | `pipx install lizard` | Linter complexity rules, where configured |
| **jscpd** | Copy-paste detection across many languages | MIT | `npx jscpd` | Review only; state that duplication may be missed |
| **knip** (JS/TS) | Unused files, exports, and dependencies | ISC | `npx knip` (or dev-dependency) | `rg` reference searches |
| **vulture** (Python) | Unused code, with confidence scores | MIT | `pipx install vulture` | `rg` reference searches |
| **deadcode** (Go) | Unreachable functions | BSD-3-Clause | `go install golang.org/x/tools/cmd/deadcode@latest` | `rg` reference searches |
| **cargo-machete** (Rust) | Unused crate dependencies | MIT | `cargo install cargo-machete` | Manual `Cargo.toml` review |

## Security

| Tool | Job | Licence | Install | If declined |
|---|---|---|---|---|
| **opengrep** | Static analysis (SAST) with pattern rules; the LGPL fork of the Semgrep engine | LGPL-2.1 | Release binary from the project (verify the checksum) | Language linters' security rules |
| **gitleaks** | Fast secret scanning; suits pre-commit | MIT | `brew install gitleaks` or a release binary | `rg` for common key patterns (weak) |
| **TruffleHog** | Deep secret scanning, including git history; checks whether found keys are live | AGPL-3.0 | `brew install trufflehog` or a release binary | gitleaks alone |
| **osv-scanner** | Known-vulnerability scan of lockfiles against the OSV database | Apache-2.0 | `brew install osv-scanner` or a release binary | The ecosystem's audit: `npm audit`, `pip-audit`, `govulncheck`, `cargo audit` |
| **syft** + **grype** | SBOM generation, then vulnerability matching for images and filesystems | Apache-2.0 | `brew install syft grype` or release binaries | osv-scanner on lockfiles |
| **trivy** | All-in-one image, filesystem, and IaC scanner. **Pin by digest or SHA only**: its GitHub Action and images were compromised in March 2026 (CVE-2026-33634). | Apache-2.0 | `brew install trivy` or a digest-pinned image | syft + grype |
| **OpenSSF Scorecard** (`scorecard`) | Scores a repository's supply-chain practices: pinned actions, branch protection, and more | Apache-2.0 | `brew install scorecard` or a release binary | Manual review of the CI and branch settings |

## CI, containers, infrastructure code

| Tool | Job | Licence | Install | If declined |
|---|---|---|---|---|
| **actionlint** | Lints GitHub Actions workflows, including embedded shell | MIT | `brew install actionlint` or a checksum-verified release binary | Review |
| **zizmor** | Security audit of GitHub Actions: unpinned actions, template injection, excessive permissions | MIT | `pipx install zizmor` or `uvx zizmor` | Review against its documented audits |
| **hadolint** | Dockerfile linter | GPL-3.0 | `brew install hadolint` or a release binary | Review |
| **checkov** | IaC misconfiguration scanner (Terraform, Kubernetes, CloudFormation, and more) | Apache-2.0 | `pipx install checkov` | `trivy config` |
| **squawk** | Flags unsafe Postgres migrations: locking, table rewrites | Apache-2.0 or MIT | `npx squawk-cli` or a release binary | `migration-safety-checklist` review |

## Tests and performance

| Tool | Job | Licence | Install | If declined |
|---|---|---|---|---|
| **fast-check** (JS/TS) · **Hypothesis** (Python) | Property-based testing for parsers, invariants, and state machines | MIT · MPL-2.0 | Test dev-dependency | Hand-written boundary tables |
| **Stryker** (JS/TS) · **mutmut** (Python) · **cargo-mutants** (Rust) | Mutation testing: shows whether tests can catch real bugs (T3 changes) | Apache-2.0 · BSD-3-Clause · MIT | Test dev-dependency / `cargo install cargo-mutants` | Coverage alone (weaker) |
| **py-spy** · **samply** | Sampling profilers (Python; native, with Firefox Profiler output) | MIT · Apache-2.0 | `pipx install py-spy` · `cargo install samply` | Language built-in profilers |
| **k6** | Load testing with scripted scenarios and thresholds | AGPL-3.0 | `brew install k6` or a release binary | Small custom load script |

## Workflow and hygiene

| Tool | Job | Licence | Install | If declined |
|---|---|---|---|---|
| **lefthook** or **pre-commit** | Run formatter, linter, secret scan, and architecture check before each commit | MIT · MIT | `brew install lefthook` / `pipx install pre-commit` | CI-only checks (slower feedback) |
| **mise** | Pins tool and runtime versions per repository | MIT | `brew install mise`, `winget`, or the project installer | Versions documented in the README |
| **Renovate** | Automated, grouped dependency and action-SHA updates | AGPL-3.0 | Hosted app, or self-hosted CLI | Scheduled manual updates |
