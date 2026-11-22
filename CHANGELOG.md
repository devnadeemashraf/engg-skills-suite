# Changelog

All notable changes to this project. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses [Semantic Versioning](https://semver.org/).

## [2.0.0] - 2026-11-23

v2 turns the suite from written guidance into **checked** guidance. Standards are enforced by tools, claims need evidence, and the agent asks before it assumes. The design and its findings, phase by phase, are in [docs/V2_PLAN.md](docs/V2_PLAN.md).

### Highlights

- **Two new skills.**
  - `engg-deep-audit` audits a whole codebase layer by layer with open-source tools, keeping its progress on disk.
  - `engg-refactor` cleans one up safely, behind a ratchet that only lets violations go down.
- **Architecture as a machine-checked contract.** `.engg/architecture.yaml` compiles into dependency-cruiser, import-linter or go-arch-lint, with a coverage report for anything a checker can't express.
- **Delivery modes.** The skills ask once whether you want `mvp-first` (core flow first, then increments) or `full-sequence` (everything in order). If a project already has an architecture and tooling, they are treated as fixed unless you ask for a redo.
- **Open-source tools with consent.** There is a registry of free tools, a read-only `toolcheck`, and a protocol: ask once, explain why and what data leaves the machine, prefer installs that are easy to undo, and say what is lost if declined.
- **Rigor that matches risk.** Risk tiers T0–T3 set the tests and gates for each change. The Evidence Protocol requires a citation for every claim, and two signals before anything is deleted.

### Added

- `engg-deep-audit`:
  - `build_map.py` merges tool outputs into a system map: layers, files in no layer, production and test hotspots, two-signal dead-code candidates, duplicates and cycles.
  - `ledger.py` hands out one bounded unit at a time, validates findings against a schema, resumes after interruption, and records deliberate skips with a reason (`skip`), so a partial audit is never reported as complete.
  - Tool recipes with verified commands, exit codes and safety rules.
- `engg-refactor`: characterization tests proven able to fail, two-signal deletion re-checked at HEAD, the strangler fig for large moves, and behaviour fixes kept test-first in separate commits.
- `shared/`, the single source for files several skills use, kept in sync by `tools/sync_shared.py` (checked in CI):
  - the engineering constitution v2, with Evidence Protocol, Risk Tiers, Ratchet, and a deletion rule
  - delivery modes, the architecture contract, the toolchain registry, the tool consent protocol
  - `compile_contract.py`, `ratchet.py` (`check --require-tight` for CI), and `toolcheck.sh` / `toolcheck.ps1`
- `compile_contract.py` option `targets.typescript.parser` (`acorn`, `swc` or `tsc`). TypeScript 7.0 projects need `swc`.
- `evals/`: a messy and a clean fixture repo, a 20-defect answer key, `prepare.py`, `score.py`, and recorded runs.
- `docs/SETUP.md`, a full setup guide per tool; `docs/WORKFLOWS.md` Recipe 0 (choose the delivery mode); this changelog.
- A "Which Skill When" table in the README, kept in step with the skills' descriptions by `tests/test_triggers.py`.

### Changed

- **All 11 original skills upgraded to 2.0.0:**
  - **plan:** a tier, gate commands, ratchet delta and rollback per chunk.
  - **build:** test depth by tier; mutation testing at T3.
  - **audit:** diff-scoped tools first; ASVS 5.0 in spec reviews.
  - **ship:** SHA-pinned actions, actionlint and zizmor, SLSA v1.2 provenance, a merge queue, feature flags, five DORA metrics.
  - **research:** docs through only-cli, registry and OSV checks, dated briefs.
  - **data:** squawk, realistic-volume plans, resumable backfills.
  - **debug:** `git bisect run`, repeat-measured evidence.
  - **extend:** graph-picked reference slices, zero new violations.
  - **architect:** C4, MADR 4.0, ASVS level, writes the contract.
  - **roadmap:** a tool-measured reality check and a DORA baseline.
  - **ideate:** verified build-vs-buy-vs-open-source options and numeric success criteria.
- **`engg-audit` is narrowed to diffs, pull requests and specs.** Whole-codebase audits moved to `engg-deep-audit`.
- **Installers:**
  - `install.ps1` now matches `install.sh`: one master copy, linked into each tool, with symlinks or junctions.
  - Both installers add `--uninstall` and `--dry-run`, and now also link Codex (`~/.codex/skills`, `<repo>/.codex/skills`).
- **The README is rewritten around daily use.**

### Fixed

- The validator parses frontmatter as real YAML, so CRLF checkouts and multi-line descriptions validate. It also enforces spec limits, unreferenced or nested resources, and paths that climb out of a skill folder.
- `install.sh` gives a clear error for `--project` with no path.
- Removing a junction in Windows PowerShell 5.1 no longer risks deleting its target.

### Security

- CI actions are pinned to commit SHAs with read-only permissions. Python dependencies are hash-pinned. Node dependencies come from a lockfile with install scripts disabled.
- The deep audit always runs gitleaks with `--redact` and scans git history.

### Migrating from 1.x

1. **Reinstall.** Pull, then run the installer again with your usual scope. Global installs now keep a master copy in `~/.engg-skills-suite/skills/`. If you copied v1 skills by hand, uninstall them first: `./install.sh --global --uninstall` removes only this suite's skills.
2. **"engg-audit Mode B" is now `engg-deep-audit`.** Mode A (diffs and PRs) and Mode C (specs) keep their names, so existing prompts for those still work.
3. **Expect one new question.** The first planning or building skill in a project asks for the delivery mode and baseline, and writes `.engg/delivery.yaml`. Commit it, along with the rest of `.engg/` except `.engg/audit/`.
4. **Contributors:** the validator moved to `tools/validate_suite.py`. Edit shared files in `shared/`, never in `skills/`, then run `python tools/sync_shared.py`.

## [1.0.0] - 2026-11-22

- Initial release: 11 skills covering ideation, roadmap, architecture, planning, test-first building, extension, audit, research, debugging, data and shipping, with installers and a validator.

[2.0.0]: https://github.com/devnadeemashraf/engg-skills-suite/releases/tag/v2.0.0
[1.0.0]: https://github.com/devnadeemashraf/engg-skills-suite/commit/7922d54
