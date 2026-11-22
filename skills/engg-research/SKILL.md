---
name: engg-research
description: Enforces zero-memory-guessing live research for APIs, frameworks, SDKs, protocols, CVEs, and exact dependency version pinning across any package ecosystem. Use when selecting libraries, verifying current documentation or breaking changes, resolving dependency conflicts, checking security advisories, or pinning exact versions in lockfiles and catalogs.
license: Apache-2.0
metadata:
  version: "2.0.0"
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
6. **Read the web token-cheaply:** fetch docs, changelogs and release notes with `oc open <url>` / `oc raw <url>` (only-cli; if toolcheck reports `conflict`, use `npx @only-cli/oc`). Fall back to the agent's own web tool when `oc` exits 2 (a JavaScript-only page or a bot wall).
7. **Verify the package is the real one:** confirm the registry entry links to the project's official repository, and watch for look-alike names. PyPI, for example, hosts unaffiliated `graphify*` packages next to the real `graphifyy`.
8. **Use the open-source toolchain, with consent:** run `scripts/toolcheck.sh` (Windows: `scripts/toolcheck.ps1`) from this skill's folder to see which tools in `references/toolchain.md` are installed, and prefer them over reading code by hand. Never install a missing tool without following `references/tool-consent.md`.

## Workflow

1. **Define Research Question:** Specify exact ecosystem, runtime version, OS/platform target, and compatibility constraints.
2. **Verify Live Facts:**
   - **Latest stable version**, from the registry's own CLI (`npm view <pkg> version time`, `pip index versions <pkg>`, `go list -m -versions <mod>`, `cargo search <crate>`). Avoid alpha/beta/RC unless explicitly required.
   - **Compatibility:** read the package's declared engine and peer ranges. For example, dependency-cruiser 18.8.0 supports TypeScript `<7.0.0 || >=7.1.0`, so "latest TypeScript" (7.0.x) would have broken it.
   - **Maintenance health:** the repository isn't archived or moved (`gh api repos/<owner>/<repo>` shows `archived` and the last push), releases are recent, and the OpenSSF Scorecard result is acceptable (`https://api.scorecard.dev/projects/github.com/<owner>/<repo>`). Licence compatibility: flag GPL/AGPL/SSPL explicitly.
   - **Known vulnerabilities:** OSV for the exact version (`osv-scanner scan source -r .` after adding it, or the OSV API for one package), plus the ecosystem's own audit.
   - **API signatures and breaking changes** for the target major version, from that version's docs and changelog.
3. **Compare Candidates (when selecting):**
   - Present a compact 2–3 option comparison matrix (Maturity, Performance/Size, License, Security/Maintenance, Ecosystem Fit) and make ONE decisive recommendation.
4. **Apply Strict Pinning:**
   - Pin exact versions in the project's central dependency catalog/manifest + commit updated lockfile.
   - Pin container base images by immutable SHA256 digest (`image:tag@sha256:...`) and CI actions by full commit SHA, resolving the SHA from the tag live (`git ls-remote https://github.com/<owner>/<repo> 'refs/tags/<tag>*'`). For an annotated tag, use the `^{}` line, which is the commit; the other line is the tag object.
   - Run the ecosystem's built-in vulnerability/license audit command.
5. **Emit a dated Research Brief** (template in `references/version-pinning-policy.md`): verified versions, the date checked, a source link for every fact, breaking-change notes, and upgrade constraints. Downstream skills (`engg-architect`, `engg-build`, `engg-extend`, `engg-ship`) work from the brief, not from memory. Mark anything you couldn't verify as **unverified**; never present it as fact.

## Gotchas

- **Silent major-version mismatch:** Copying a code snippet from a v3 tutorial while installing v5 causes hours of wasted debugging. Always match docs strictly to the pinned major version.
- **Unpinned transitive drift:** Relying solely on `requirements.txt` or loose ranges without a committed lockfile breaks reproducible builds across dev and CI.
