# Cross-Ecosystem Dependency & Version Pinning Policy

## 1. Universal Pinning Rules
- **Centralize versions:** In monorepos, manage shared dependency versions in one canonical catalog (e.g., pnpm catalogs, Gradle version catalogs, Cargo workspace dependencies, Python `pyproject.toml` + lockfile, Go `go.mod`/`go.sum`).
- **Commit lockfiles always** for applications, services, clients, games, and infrastructure repos.
- **Verify integrity hashes:** Use lockfiles with cryptographic checksums (`package-lock.json`, `pnpm-lock.yaml`, `Cargo.lock`, `go.sum`, `uv.lock`, `poetry.lock`, `.terraform.lock.hcl`).
- **Pin base images & CI actions:** Pin container images by digest (`@sha256:...`) and CI workflow actions by full 40-char commit SHA (with version tag in a trailing comment).

## 2. Dependency Admission Checklist
Before adding ANY third-party dependency, verify:
1. **Necessity:** Can the standard library or <30 lines of tested internal code solve this cleanly?
2. **Maintenance:** Released/maintained actively? Clear security reporting policy?
3. **Security:** Zero unresolved critical/high CVEs via native audit (`npm audit`, `cargo audit`, `govulncheck`, `pip-audit`, `trivy`)?
4. **License:** Compatible with project distribution model (flag GPL/AGPL/SSPL explicitly)?
5. **Footprint:** Acceptable binary/bundle size, cold-start cost, and transitive dependency count?

## 3. Ecosystem Quick-Verification Commands
- **JS/TS:** `npm view <pkg> dist-tags`, `pnpm audit` / `npm audit`, `npm ci` / `pnpm install --frozen-lockfile`
- **Python:** `uv lock --locked`, `pip-audit`
- **Go:** `go list -m -versions <mod>`, `govulncheck ./...`
- **Rust:** `cargo info <crate>`, `cargo audit`, `cargo deny check`
- **Containers / IaC:** `trivy image`, `terraform providers lock`, `checkov` / `tfsec`
