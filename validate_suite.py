#!/usr/bin/env python3
"""Validates the Unified Engineering Skills Suite against agentskills.io and suite standards."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "skills"
FORBIDDEN_TERMS = ["google", "faang", "anthropic", "openai", "meta", "amazon"]
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
REF_RE = re.compile(r"`(references/[a-zA-Z0-9_./-]+)`")

errors = []
skill_dirs = sorted([p for p in ROOT.iterdir() if p.is_dir()])

if not skill_dirs:
    errors.append("No skill directories found.")

for sdir in skill_dirs:
    skill_md = sdir / "SKILL.md"
    if not skill_md.exists():
        errors.append(f"{sdir.name}: Missing SKILL.md")
        continue

    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    if len(lines) > 500:
        errors.append(f"{sdir.name}: SKILL.md exceeds 500 lines ({len(lines)})")

    if not text.startswith("---\n"):
        errors.append(f"{sdir.name}: Missing YAML frontmatter")
        continue

    parts = text.split("---\n", 2)
    if len(parts) < 3:
        errors.append(f"{sdir.name}: Malformed YAML frontmatter")
        continue

    frontmatter, body = parts[1], parts[2]
    name_m = re.search(r"^name:\s*(.+)$", frontmatter, re.MULTILINE)
    desc_m = re.search(r"^description:\s*(.+)$", frontmatter, re.MULTILINE)

    if not name_m:
        errors.append(f"{sdir.name}: Missing 'name' field")
    else:
        name_val = name_m.group(1).strip().strip('"\'')
        if name_val != sdir.name:
            errors.append(f"{sdir.name}: name '{name_val}' != directory '{sdir.name}'")
        if not NAME_RE.match(name_val) or len(name_val) > 64:
            errors.append(f"{sdir.name}: invalid kebab-case name '{name_val}'")

    if not desc_m:
        errors.append(f"{sdir.name}: Missing 'description' field")
    else:
        desc_val = desc_m.group(1).strip().strip('"\'')
        if len(desc_val) == 0 or len(desc_val) > 1024:
            errors.append(f"{sdir.name}: description length invalid ({len(desc_val)})")

    # Verify all referenced files exist
    for ref in set(REF_RE.findall(body)):
        ref_path = sdir / ref
        if not ref_path.exists():
            errors.append(f"{sdir.name}: Broken reference '{ref}'")

    # Verify zero forbidden company names across all files in skill folder
    for fpath in sdir.rglob("*.md"):
        ftext = fpath.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_TERMS:
            if re.search(rf"\b{term}\b", ftext):
                errors.append(f"{fpath.relative_to(ROOT)}: Contains forbidden brand name '{term}'")

if errors:
    print("VALIDATION FAILED:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(f"VALIDATION PASSED: {len(skill_dirs)} skills verified clean (agentskills.io compliant, zero broken refs, zero brand names).")
for sdir in skill_dirs:
    line_count = len((sdir / "SKILL.md").read_text(encoding="utf-8").splitlines())
    refs = sorted([str(p.relative_to(sdir)) for p in (sdir / "references").glob("*.md")]) if (sdir / "references").exists() else []
    print(f"  [OK] {sdir.name:<15} SKILL.md ({line_count:3d} lines) | refs: {', '.join(refs)}")
