# Contributing to `engg-skills-suite`

Every skill in this repository is held to the same engineering standard it enforces on production codebases. Every rule below marked _(enforced)_ is checked by `tools/validate_suite.py` in CI.

## Non-Negotiable Authoring Standards

1. **Open Specification Compliance ([agentskills.io](https://agentskills.io/specification)):**
   - Each skill lives in `skills/<kebab-case-name>/SKILL.md`. The directory name must match the frontmatter `name` _(enforced)_.
   - `name`: lowercase `a-z0-9` and single hyphens, at most 64 characters _(enforced)_.
   - `description`: third person, says what the skill does **and when to use it**, at most 1024 characters _(enforced)_.
   - `license` and `metadata` (with string `version` and `suite` keys) are required by this suite _(enforced)_.
   - Only spec fields are allowed: `name`, `description`, `license`, `compatibility` (at most 500 characters), `metadata`, `allowed-tools` _(enforced)_.
2. **Progressive Disclosure Budget:**
   - Keep `SKILL.md` concise and procedural: **at most 150 lines** _(enforced)_. The spec's hard limit is 500.
   - Put heavy question banks, checklists, templates, and domain profiles in `references/`, scripts in `scripts/`, and templates in `assets/`.
   - Mention every resource file from `SKILL.md` by its relative path (for example `references/<file>.md`), one level deep. A file that is never mentioned is never loaded, so the validator rejects it _(enforced)_.
3. **Self-Contained Skill Folders:**
   - Never use paths that climb out of a skill's own directory (`../`). Every skill must install cleanly on its own _(enforced)_.
4. **Strict Vendor Neutrality:**
   - No company or model brand names anywhere inside `skills/` _(enforced)_.
   - Skills stay genuinely tech-agnostic until the user locks a stack.
5. **Orthogonal Trigger Scope:**
   - Before adding a skill, confirm it doesn't duplicate or blur the activation boundaries of an existing `engg-*` skill.
6. **Shared Files Live in `shared/`:**
   - Files several skills need (the engineering constitution, the toolchain registry, the tool consent protocol, `toolcheck` scripts) are edited **only** in `shared/`. Run `python tools/sync_shared.py` to copy them into the skills listed in `shared/manifest.yaml`.
   - Never edit a synced copy inside `skills/`. CI runs `python tools/sync_shared.py --check` and fails on any drift _(enforced)_.
   - A shared file's name is reserved: if a skill isn't assigned that file in the manifest, the sync removes the skill's copy.
7. **Tools Need Consent:**
   - Skills may recommend tools from `shared/references/toolchain.md`, but must follow `shared/references/tool-consent.md`: detect with `toolcheck`, ask once with a clear reason, verify the package live, prefer user-scoped installs, and say what accuracy is lost if the user declines.
   - When adding a tool to the registry, check its licence and maintenance status on its repository, then add it to both `toolcheck.sh` and `toolcheck.ps1` (a test compares the two lists).

## Local Verification Before Opening a PR

```bash
python -m venv .venv && . .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --require-hashes -r requirements-dev.txt
python tools/sync_shared.py --check
python tools/validate_suite.py
python -m pytest -q
bash tests/installer_smoke.sh                         # Windows: .\tests\installer_smoke.ps1
```

All checks must pass with zero errors. CI also runs shellcheck, actionlint, zizmor, and PSScriptAnalyzer.

## Dependencies and Pinning

- **Python:** `requirements-dev.txt` and `requirements-lint.txt` are generated, with every file hash-pinned. To bump, edit the versions in `tools/pin_requirements.py` (transitive dependencies included), run `python tools/pin_requirements.py`, and commit the result. Check the new versions on PyPI and OSV first.
- **GitHub Actions:** pin every `uses:` to a full commit SHA, with the tag in a trailing comment (`# v7.0.1`). Tags can be force-pushed by an attacker; SHAs can't.
- **Downloaded binaries in CI:** verify against the release's published SHA-256 checksum before running them.
