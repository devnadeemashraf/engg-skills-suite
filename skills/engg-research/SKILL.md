---
name: engg-research
description: Enforces zero-memory-guessing live research for APIs, frameworks, SDKs, protocols, CVEs, and exact dependency version pinning across any package ecosystem. Use when selecting libraries, verifying current documentation or breaking changes, resolving dependency conflicts, checking security advisories, or pinning exact versions in lockfiles and catalogs.
license: Apache-2.0
metadata:
  version: "1.0.0"
  suite: "engg-skills-suite"
  standard: "agentskills.io"
---

# Live Technical Research & Strict Version Pinning

Eliminate hallucinated APIs, stale package versions, deprecated flags, and supply-chain drift by verifying live primary sources and enforcing strict dependency pinning.

## When to Use

- Choosing a library, framework, runtime, game engine plugin, database driver, or cloud module.
- Upgrading packages or resolving breaking changes, peer conflicts, or CVEs.
- Implementing against any fast-moving SDK, CLI, or external API where training memory may be stale.

## Non-Negotiable Rules

1. **Zero memory-guessing:** Never guess latest package versions, CLI flags, API signatures, or deprecation status from recall. Always inspect live official documentation, release notes, or registry metadata (via web search, package manager CLI, or installed docs).
2. **Load policy first:** Read `references/version-pinning-policy.md` before modifying any manifest or lockfile.
3. **Primary sources only:** Prefer official docs, release changelogs, RFCs, and package registries over random blog posts or stale Q&A threads.
4. **Pin exact, auditable versions:** No floating ranges (`latest`, `*`, unpinned `^`/`~` in critical manifests/Dockerfiles) without an explicit lockfile and digest policy.
5. **Justify every dependency:** Adding a dependency is taking on permanent security and maintenance liability. Reject bloated libraries when 20 lines of clean standard-library code suffice (KISS).
6. **Use the open-source toolchain, with consent:** run `scripts/toolcheck.sh` (Windows: `scripts/toolcheck.ps1`) from this skill's folder to see which tools in `references/toolchain.md` are installed, and prefer them over reading code by hand. Never install a missing tool without following `references/tool-consent.md`.

## Workflow

1. **Define Research Question:** Specify exact ecosystem, runtime version, OS/platform target, and compatibility constraints.
2. **Verify Live Facts:**
   - Check latest stable version (avoid alpha/beta/RC unless explicitly required).
   - Check maintenance health (recent releases, active maintainers, issue triage, license compatibility e.g. MIT/Apache-2.0/BSD vs. copyleft).
   - Check known CVEs / security advisories and transitive dependency footprint.
   - Verify exact API signatures and breaking changes for the target major version.
3. **Compare Candidates (when selecting):**
   - Present a compact 2–3 option comparison matrix (Maturity, Performance/Size, License, Security/Maintenance, Ecosystem Fit) and make ONE decisive recommendation.
4. **Apply Strict Pinning:**
   - Pin exact versions in the project's central dependency catalog/manifest + commit updated lockfile.
   - Pin container base images by immutable SHA256 digest (`image:tag@sha256:...`).
   - Run the ecosystem's built-in vulnerability/license audit command.
5. **Emit Research Brief:** Record verified versions, source links, breaking-change notes, and upgrade constraints so downstream skills (`engg-architect`, `engg-build`, `engg-extend`) execute with 100% factual accuracy.

## Gotchas

- **Silent major-version mismatch:** Copying a code snippet from a v3 tutorial while installing v5 causes hours of wasted debugging. Always match docs strictly to the pinned major version.
- **Unpinned transitive drift:** Relying solely on `requirements.txt` or loose ranges without a committed lockfile breaks reproducible builds across dev and CI.
