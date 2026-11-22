#!/usr/bin/env python3
"""Validate every skill in the suite against the Agent Skills spec and suite rules.

Spec: https://agentskills.io/specification
Usage: python tools/validate_suite.py [skills_root]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - exercised manually
    sys.exit("PyYAML is required: python -m pip install -r requirements-dev.txt")

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SKILLS_ROOT = REPO_ROOT / "skills"

# Spec limits
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX = 64
DESCRIPTION_MAX = 1024
COMPATIBILITY_MAX = 500
SPEC_FIELDS = {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}

# Suite rules (stricter than the spec)
SKILL_MD_MAX_LINES = 150
REQUIRED_FIELDS = {"name", "description", "license", "metadata"}
REQUIRED_METADATA_KEYS = {"version", "suite"}
RESOURCE_DIRS = ("references", "scripts", "assets")
FORBIDDEN_TERMS = ["google", "faang", "anthropic", "openai", "meta", "amazon"]
TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".py", ".sh", ".ps1"}

# A resource mention: `references/x.md`, `scripts/x.py`, `assets/x` (backticked or in a link).
RESOURCE_REF_RE = re.compile(r"(?<![\w./-])((?:references|scripts|assets)/[A-Za-z0-9_./-]+)")
# Any relative path that starts by climbing out of the current folder, e.g. `../other-skill/x.md`.
PARENT_PATH_RE = re.compile(r"(?<![\w./-])(\.\.[/\\][^\s`)\"'>\]]*)")


def read_text(path: Path) -> str:
    """Read UTF-8 text with line endings normalised, so CRLF checkouts validate identically."""
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


def split_frontmatter(text: str) -> tuple[str, str] | None:
    """Return (frontmatter, body), or None if the file has no closed frontmatter block."""
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---\n", 3)
    if end == -1:
        if text.endswith("\n---"):
            return text[4:-4], ""
        return None
    return text[4:end + 1], text[end + 5:]


def check_frontmatter(skill: str, data: object) -> list[str]:
    if not isinstance(data, dict):
        return [f"{skill}: frontmatter must be a YAML mapping"]
    errors: list[str] = []

    for key in sorted(REQUIRED_FIELDS - data.keys()):
        errors.append(f"{skill}: missing required field '{key}'")
    for key in sorted(set(data) - SPEC_FIELDS):
        errors.append(f"{skill}: unknown frontmatter field '{key}' (spec allows {sorted(SPEC_FIELDS)})")

    name = data.get("name")
    if "name" in data:
        if not isinstance(name, str) or not NAME_RE.match(name) or len(name) > NAME_MAX:
            errors.append(f"{skill}: invalid name {name!r} (lowercase a-z0-9 and single hyphens, <= {NAME_MAX})")
        elif name != skill:
            errors.append(f"{skill}: name '{name}' does not match directory '{skill}'")

    desc = data.get("description")
    if "description" in data and (not isinstance(desc, str) or not desc.strip() or len(desc) > DESCRIPTION_MAX):
        length = len(desc) if isinstance(desc, str) else "non-string"
        errors.append(f"{skill}: description must be a non-empty string <= {DESCRIPTION_MAX} chars (got {length})")

    lic = data.get("license")
    if "license" in data and (not isinstance(lic, str) or not lic.strip()):
        errors.append(f"{skill}: license must be a non-empty string")

    if "compatibility" in data:
        compat = data["compatibility"]
        if not isinstance(compat, str) or not compat.strip() or len(compat) > COMPATIBILITY_MAX:
            errors.append(f"{skill}: compatibility must be a non-empty string <= {COMPATIBILITY_MAX} chars")

    if "allowed-tools" in data:
        tools = data["allowed-tools"]
        if not isinstance(tools, str) or not tools.split():
            errors.append(f"{skill}: allowed-tools must be a space-separated string")

    if "metadata" in data:
        meta = data["metadata"]
        if not isinstance(meta, dict):
            errors.append(f"{skill}: metadata must be a mapping")
        else:
            for key, value in meta.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    errors.append(f"{skill}: metadata entries must be string -> string (bad entry {key!r}: {value!r})")
            for key in sorted(REQUIRED_METADATA_KEYS - meta.keys()):
                errors.append(f"{skill}: metadata missing '{key}'")
    return errors


def check_references(skill: str, sdir: Path, body: str) -> list[str]:
    errors: list[str] = []
    mentioned: set[str] = set()
    for path in sorted(set(PARENT_PATH_RE.findall(body))):
        errors.append(f"{skill}: path '{path}' climbs outside the skill folder (skills must be self-contained)")

    for ref in sorted(set(RESOURCE_REF_RE.findall(body))):
        ref = ref.rstrip(".")
        if ref.count("/") != 1:
            errors.append(f"{skill}: reference '{ref}' must be one level deep (e.g. references/<file>)")
        if not (sdir / ref).is_file():
            errors.append(f"{skill}: broken reference '{ref}'")
        mentioned.add(ref)

    for res_dir in RESOURCE_DIRS:
        root = sdir / res_dir
        if not root.is_dir():
            continue
        for fpath in sorted(p for p in root.rglob("*") if p.is_file() and not is_cache(p)):
            rel = fpath.relative_to(sdir).as_posix()
            if rel not in mentioned:
                errors.append(f"{skill}: '{rel}' is never referenced from SKILL.md, so agents will never load it")
    return errors


def is_cache(path: Path) -> bool:
    """Interpreter caches are local build artefacts (git-ignored), not skill resources."""
    return "__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"}


def check_brand_names(skills_root: Path, sdir: Path) -> list[str]:
    errors: list[str] = []
    for fpath in sorted(p for p in sdir.rglob("*") if p.is_file() and p.suffix in TEXT_SUFFIXES):
        text = read_text(fpath).lower()
        for term in FORBIDDEN_TERMS:
            if re.search(rf"\b{term}\b", text):
                rel = fpath.relative_to(skills_root).as_posix()
                errors.append(f"{rel}: contains forbidden brand name '{term}'")
    return errors


def validate_skill(sdir: Path, skills_root: Path) -> list[str]:
    skill = sdir.name
    skill_md = sdir / "SKILL.md"
    if not skill_md.is_file():
        return [f"{skill}: missing SKILL.md"]

    text = read_text(skill_md)
    errors: list[str] = []

    line_count = len(text.splitlines())
    if line_count > SKILL_MD_MAX_LINES:
        errors.append(f"{skill}: SKILL.md has {line_count} lines (suite budget is {SKILL_MD_MAX_LINES})")

    parts = split_frontmatter(text)
    if parts is None:
        return errors + [f"{skill}: SKILL.md must start with a '---' frontmatter block closed by '---'"]
    frontmatter, body = parts

    try:
        data = yaml.safe_load(frontmatter)
    except yaml.YAMLError as exc:
        return errors + [f"{skill}: frontmatter is not valid YAML: {exc}"]

    errors += check_frontmatter(skill, data)
    errors += check_references(skill, sdir, body)
    errors += check_brand_names(skills_root, sdir)
    return errors


def validate_suite(skills_root: Path) -> tuple[list[str], list[Path]]:
    if not skills_root.is_dir():
        return [f"skills directory not found: {skills_root}"], []
    skill_dirs = sorted(p for p in skills_root.iterdir() if p.is_dir())
    if not skill_dirs:
        return ["no skill directories found"], []
    errors: list[str] = []
    for sdir in skill_dirs:
        errors += validate_skill(sdir, skills_root)
    return errors, skill_dirs


def main(argv: list[str]) -> int:
    skills_root = Path(argv[1]).resolve() if len(argv) > 1 else DEFAULT_SKILLS_ROOT
    errors, skill_dirs = validate_suite(skills_root)
    if errors:
        print("VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"VALIDATION PASSED: {len(skill_dirs)} skills")
    for sdir in skill_dirs:
        lines = len(read_text(sdir / "SKILL.md").splitlines())
        resources = sorted(
            p.relative_to(sdir).as_posix()
            for d in RESOURCE_DIRS if (sdir / d).is_dir()
            for p in (sdir / d).rglob("*") if p.is_file()
        )
        print(f"  [OK] {sdir.name:<16} SKILL.md ({lines:3d} lines) | {', '.join(resources) or 'no resources'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
