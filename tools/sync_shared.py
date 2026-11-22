#!/usr/bin/env python3
"""Copy shared files into the skills listed in shared/manifest.yaml.

Usage:
    python tools/sync_shared.py           # write copies, remove stale ones
    python tools/sync_shared.py --check   # report drift and exit 1; change nothing (CI)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - exercised manually
    sys.exit("PyYAML is required: python -m pip install -r requirements-dev.txt")

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Plan:
    copies: dict[Path, Path]  # destination inside skills/ -> source inside shared/
    stale: list[Path]         # copies of shared files in skills that the manifest no longer assigns


def normalised(path: Path) -> bytes:
    """File bytes with CRLF folded to LF, so a CRLF checkout does not count as drift."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def load_manifest(shared_root: Path, skills_root: Path) -> tuple[dict[str, list[str]], list[str]]:
    """Return ({shared file: [skills]}, errors)."""
    manifest_path = shared_root / "manifest.yaml"
    if not manifest_path.is_file():
        return {}, [f"missing {manifest_path}"]
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    errors: list[str] = []
    assignments: dict[str, list[str]] = {}

    groups = data.get("groups")
    if not isinstance(groups, dict) or not groups:
        return {}, ["manifest.yaml must define a non-empty 'groups' mapping"]
    extra = set(data) - {"groups"}
    if extra:
        errors.append(f"manifest.yaml: unknown top-level keys {sorted(extra)}")

    for gname, group in groups.items():
        if not isinstance(group, dict) or set(group) != {"files", "skills"}:
            errors.append(f"group '{gname}' must have exactly 'files' and 'skills'")
            continue
        for rel in group["files"]:
            if not (shared_root / rel).is_file():
                errors.append(f"group '{gname}': shared file not found: shared/{rel}")
            elif rel.count("/") != 1 or rel.split("/")[0] not in ("references", "scripts", "assets"):
                errors.append(f"group '{gname}': '{rel}' must be <references|scripts|assets>/<file>")
        for skill in group["skills"]:
            if not (skills_root / skill / "SKILL.md").is_file():
                errors.append(f"group '{gname}': unknown skill '{skill}'")
        for rel in group["files"]:
            assignments.setdefault(rel, [])
            for skill in group["skills"]:
                if skill in assignments[rel]:
                    errors.append(f"'{rel}' is assigned to '{skill}' twice")
                else:
                    assignments[rel].append(skill)
    return assignments, errors


def make_plan(assignments: dict[str, list[str]], shared_root: Path, skills_root: Path) -> Plan:
    copies = {
        skills_root / skill / rel: shared_root / rel
        for rel, skills in assignments.items()
        for skill in skills
    }
    stale = sorted(
        candidate
        for rel in assignments
        for sdir in skills_root.iterdir() if sdir.is_dir()
        if (candidate := sdir / rel).is_file() and candidate not in copies
    )
    return Plan(copies=copies, stale=stale)


def drift(plan: Plan, repo_root: Path) -> list[str]:
    problems = []
    for dst, src in sorted(plan.copies.items()):
        rel = dst.relative_to(repo_root).as_posix()
        if not dst.is_file():
            problems.append(f"missing copy: {rel}")
        elif normalised(dst) != normalised(src):
            problems.append(f"out of date: {rel} (edit shared/{src.relative_to(src.parents[1]).as_posix()} instead)")
    problems += [f"stale copy (no longer assigned): {p.relative_to(repo_root).as_posix()}" for p in plan.stale]
    return problems


def apply(plan: Plan) -> int:
    changed = 0
    for dst, src in sorted(plan.copies.items()):
        if dst.is_file() and normalised(dst) == normalised(src):
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(normalised(src))
        changed += 1
    for path in plan.stale:
        path.unlink()
        changed += 1
    return changed


def run(repo_root: Path, check: bool) -> int:
    shared_root, skills_root = repo_root / "shared", repo_root / "skills"
    assignments, errors = load_manifest(shared_root, skills_root)
    if errors:
        print("MANIFEST INVALID:")
        for e in errors:
            print(f"  - {e}")
        return 1
    plan = make_plan(assignments, shared_root, skills_root)

    if check:
        problems = drift(plan, repo_root)
        if problems:
            print("SHARED FILES OUT OF SYNC (run: python tools/sync_shared.py):")
            for p in problems:
                print(f"  - {p}")
            return 1
        print(f"SHARED FILES IN SYNC: {len(plan.copies)} copies across {len({d.parts[-3] for d in plan.copies})} skills")
        return 0

    changed = apply(plan)
    print(f"synced: {changed} file(s) changed, {len(plan.copies)} copies managed")
    return 0


def main(argv: list[str]) -> int:
    args = argv[1:]
    if args not in ([], ["--check"]):
        print(__doc__)
        return 2
    return run(REPO_ROOT, check=args == ["--check"])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
