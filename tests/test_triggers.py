"""Keep skill trigger boundaries explicit: one skill per request, and confusable pairs point at each other."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = sorted(p.name for p in (REPO_ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())

# (skill, must name in its description): pairs that compete for similar requests.
CONFUSABLE = [
    ("engg-audit", "engg-deep-audit"),
    ("engg-deep-audit", "engg-audit"),
    ("engg-build", "engg-refactor"),
    ("engg-refactor", "engg-build"),
    ("engg-refactor", "engg-extend"),
]


def description(skill: str) -> str:
    text = (REPO_ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    return yaml.safe_load(text.split("---", 2)[1])["description"]


def trigger_table() -> list[str]:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("## Which Skill When", 1)[1].split("\n## ", 1)[0]
    return re.findall(r"^\| [^|]+ \| `(engg-[a-z-]+)` \|", section, re.MULTILINE)


def test_every_skill_appears_exactly_once_in_the_trigger_table() -> None:
    rows = trigger_table()
    assert sorted(rows) == SKILLS, f"table rows {sorted(rows)} != skills {SKILLS}"


@pytest.mark.parametrize(("skill", "other"), CONFUSABLE)
def test_confusable_skills_name_each_other(skill: str, other: str) -> None:
    assert other in description(skill), f"{skill}'s description should say when to use {other} instead"


def test_all_skills_share_the_suite_metadata() -> None:
    for skill in SKILLS:
        text = (REPO_ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
        meta = yaml.safe_load(text.split("---", 2)[1])["metadata"]
        assert meta["suite"] == "engg-skills-suite"
        assert meta["version"] == "2.1.0", f"{skill} is still at {meta['version']}"


# Skills that plan or build must all know the delivery mode and the baseline rule.
PLANS_OR_BUILDS = ["engg-architect", "engg-build", "engg-deep-audit", "engg-extend", "engg-ideate",
                   "engg-plan", "engg-refactor", "engg-roadmap"]


@pytest.mark.parametrize("skill", PLANS_OR_BUILDS)
def test_planning_and_building_skills_follow_the_delivery_mode(skill: str) -> None:
    text = (REPO_ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    assert "references/delivery-modes.md" in text
    assert (REPO_ROOT / "skills" / skill / "references" / "delivery-modes.md").is_file()


def test_delivery_modes_example_is_valid() -> None:
    doc = (REPO_ROOT / "shared" / "references" / "delivery-modes.md").read_text(encoding="utf-8")
    example = doc.split("```yaml", 1)[1].split("```", 1)[0]
    data = yaml.safe_load(example)
    assert data["mode"] in {"mvp-first", "full-sequence"}
    assert data["baseline"] in {"greenfield", "existing", "redo"}
    for mode in ("mvp-first", "full-sequence"):
        assert f"`{mode}`" in doc
    for baseline in ("greenfield", "existing", "redo"):
        assert f"`{baseline}`" in doc
