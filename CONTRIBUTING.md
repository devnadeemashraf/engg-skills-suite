# Contributing to `engg-skills-suite`

Every skill in this repository is held to the same engineering standard it enforces on production codebases.

## Non-Negotiable Authoring Standards

1. **Open Specification Compliance (`agentskills.io`):**
   - Each skill lives in `skills/<kebab-case-name>/SKILL.md`.
   - Directory name must match the YAML frontmatter `name` field exactly.
   - Frontmatter must include `name`, `description` (third-person, clear trigger phrases, <=1024 chars), `license`, and `metadata`.
2. **Progressive Disclosure Budget:**
   - Keep `SKILL.md` concise and procedural (**target <100 lines**, hard max 500 lines).
   - Place heavy question banks, checklists, templates, and domain profiles in `references/*.md` and reference them explicitly with relative paths (`references/<file>.md`).
3. **Self-Contained Skill Folders:**
   - Never rely on relative links climbing outside a skill's own directory (`../`). Every skill must remain cleanly installable on its own.
4. **Strict Vendor Neutrality:**
   - Zero company or model brand names inside `skills/` (`validate_suite.py` enforces this automatically).
   - Skills must remain genuinely tech-agnostic until the user locks a stack.
5. **Orthogonal Trigger Scope:**
   - Before adding a new skill, confirm it does not duplicate or blur the activation boundaries of an existing `engg-*` skill.

## Local Verification Before Opening a PR

```bash
python3 validate_suite.py
bash -n install.sh
```

All checks must pass with zero errors.
