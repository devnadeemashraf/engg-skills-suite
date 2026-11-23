"""Tests for tools/validate_suite.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import validate_suite as vs  # noqa: E402

VALID_FRONTMATTER = """\
name: demo-skill
description: Does a demo thing. Use when testing the validator.
license: Apache-2.0
metadata:
  version: "2.0.0"
  suite: "engg-skills-suite"
"""

VALID_BODY = """
# Demo

Read `references/guide.md` before starting.
"""


def make_skill(root: Path, name: str = "demo-skill", frontmatter: str = VALID_FRONTMATTER,
               body: str = VALID_BODY, newline: str = "\n", refs: dict[str, str] | None = None) -> Path:
    sdir = root / name
    sdir.mkdir(parents=True)
    text = f"---\n{frontmatter}---\n{body}"
    (sdir / "SKILL.md").write_bytes(text.replace("\n", newline).encode("utf-8"))
    for rel, content in ({"references/guide.md": "# Guide\n"} if refs is None else refs).items():
        path = sdir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return sdir


def errors_for(root: Path) -> list[str]:
    errors, _ = vs.validate_suite(root)
    return errors


def test_valid_skill_passes(tmp_path: Path) -> None:
    make_skill(tmp_path)
    assert errors_for(tmp_path) == []


def test_crlf_skill_passes(tmp_path: Path) -> None:
    make_skill(tmp_path, newline="\r\n")
    assert errors_for(tmp_path) == []


def test_multiline_folded_description_passes(tmp_path: Path) -> None:
    fm = VALID_FRONTMATTER.replace(
        "description: Does a demo thing. Use when testing the validator.\n",
        "description: >\n  Does a demo thing.\n  Use when testing the validator.\n",
    )
    make_skill(tmp_path, frontmatter=fm)
    assert errors_for(tmp_path) == []


def test_multiline_description_length_is_measured_after_folding(tmp_path: Path) -> None:
    long_desc = "word " * 300  # ~1500 chars once folded
    fm = VALID_FRONTMATTER.replace(
        "description: Does a demo thing. Use when testing the validator.\n",
        f"description: >\n  {long_desc}\n",
    )
    make_skill(tmp_path, frontmatter=fm)
    assert any("description must be" in e for e in errors_for(tmp_path))


@pytest.mark.parametrize("field", ["license", "metadata", "name", "description"])
def test_missing_required_field_fails(tmp_path: Path, field: str) -> None:
    lines = VALID_FRONTMATTER.splitlines(keepends=True)
    if field == "metadata":
        fm = "".join(l for l in lines if not l.startswith(("metadata:", "  ")))
    else:
        fm = "".join(l for l in lines if not l.startswith(f"{field}:"))
    make_skill(tmp_path, frontmatter=fm)
    assert any(f"missing required field '{field}'" in e for e in errors_for(tmp_path))


def test_metadata_missing_version_fails(tmp_path: Path) -> None:
    make_skill(tmp_path, frontmatter=VALID_FRONTMATTER.replace('  version: "2.0.0"\n', ""))
    assert any("metadata missing 'version'" in e for e in errors_for(tmp_path))


def test_metadata_non_string_value_fails(tmp_path: Path) -> None:
    make_skill(tmp_path, frontmatter=VALID_FRONTMATTER.replace('"2.0.0"', "2.0"))
    assert any("string -> string" in e for e in errors_for(tmp_path))


def test_name_must_match_directory(tmp_path: Path) -> None:
    make_skill(tmp_path, name="other-skill")
    assert any("does not match directory" in e for e in errors_for(tmp_path))


@pytest.mark.parametrize("bad", ["Demo-Skill", "demo--skill", "-demo", "demo_skill", "a" * 65])
def test_invalid_names_fail(tmp_path: Path, bad: str) -> None:
    make_skill(tmp_path, name=bad, frontmatter=VALID_FRONTMATTER.replace("demo-skill", bad))
    assert any("invalid name" in e for e in errors_for(tmp_path))


def test_unknown_field_fails(tmp_path: Path) -> None:
    make_skill(tmp_path, frontmatter=VALID_FRONTMATTER + "author: someone\n")
    assert any("unknown frontmatter field 'author'" in e for e in errors_for(tmp_path))


def test_optional_spec_fields_pass(tmp_path: Path) -> None:
    fm = VALID_FRONTMATTER + "compatibility: Requires git and Python 3.11+\nallowed-tools: Bash(git:*) Read\n"
    make_skill(tmp_path, frontmatter=fm)
    assert errors_for(tmp_path) == []


def test_compatibility_too_long_fails(tmp_path: Path) -> None:
    make_skill(tmp_path, frontmatter=VALID_FRONTMATTER + f"compatibility: {'x' * 501}\n")
    assert any("compatibility must be" in e for e in errors_for(tmp_path))


def test_invalid_yaml_fails(tmp_path: Path) -> None:
    make_skill(tmp_path, frontmatter=VALID_FRONTMATTER + "bad: [unclosed\n")
    assert any("not valid YAML" in e for e in errors_for(tmp_path))


def test_unclosed_frontmatter_fails(tmp_path: Path) -> None:
    sdir = tmp_path / "demo-skill"
    sdir.mkdir()
    (sdir / "SKILL.md").write_text(f"---\n{VALID_FRONTMATTER}# no closing fence\n", encoding="utf-8")
    assert any("frontmatter block" in e for e in errors_for(tmp_path))


def test_broken_reference_fails(tmp_path: Path) -> None:
    make_skill(tmp_path, body=VALID_BODY + "Also `references/missing.md`.\n")
    assert any("broken reference 'references/missing.md'" in e for e in errors_for(tmp_path))


def test_nested_reference_fails(tmp_path: Path) -> None:
    make_skill(tmp_path, body="Read `references/deep/guide.md`.\n", refs={"references/deep/guide.md": "x\n"})
    assert any("one level deep" in e for e in errors_for(tmp_path))


def test_parent_climbing_reference_fails(tmp_path: Path) -> None:
    make_skill(tmp_path, body=VALID_BODY + "See `../other/references/x.md`.\n")
    assert any("climbs outside" in e for e in errors_for(tmp_path))


@pytest.mark.parametrize("path", ["../references/x.md", "../../shared/constitution.md", "[link](../x.md)"])
def test_any_parent_climbing_path_fails(tmp_path: Path, path: str) -> None:
    make_skill(tmp_path, body=VALID_BODY + f"See `{path}`.\n")
    assert any("climbs outside" in e for e in errors_for(tmp_path))


def test_ellipsis_is_not_a_parent_path(tmp_path: Path) -> None:
    make_skill(tmp_path, body=VALID_BODY + "Expand -> Backfill -> ... -> Contract.\n")
    assert errors_for(tmp_path) == []


def test_unreferenced_resource_fails(tmp_path: Path) -> None:
    make_skill(tmp_path, refs={"references/guide.md": "x\n", "references/orphan.md": "x\n"})
    assert any("references/orphan.md' is never referenced" in e for e in errors_for(tmp_path))


def test_scripts_are_checked_like_references(tmp_path: Path) -> None:
    make_skill(tmp_path, body=VALID_BODY + "Run `scripts/check.sh`.\n")
    assert any("broken reference 'scripts/check.sh'" in e for e in errors_for(tmp_path))


def test_brand_name_in_reference_fails(tmp_path: Path) -> None:
    make_skill(tmp_path, refs={"references/guide.md": "Built like Amazon does it.\n"})
    assert any("forbidden brand name 'amazon'" in e for e in errors_for(tmp_path))


def test_brand_exemption_covers_only_the_attribution_checker(tmp_path: Path) -> None:
    body = VALID_BODY + "Run `scripts/attribution_check.py` and `scripts/other.py`.\n"
    vendor = "VENDORS = ['anthropic']\n"
    make_skill(tmp_path, body=body, refs={"references/guide.md": "# Guide\n",
                                          "scripts/attribution_check.py": vendor, "scripts/other.py": vendor})
    errors = errors_for(tmp_path)
    assert any("scripts/other.py: contains forbidden brand name 'anthropic'" in e for e in errors)
    assert not any("attribution_check.py" in e for e in errors)


def test_brand_word_boundary_allows_metadata(tmp_path: Path) -> None:
    make_skill(tmp_path, refs={"references/guide.md": "Record metadata and metadata keys.\n"})
    assert errors_for(tmp_path) == []


def test_line_budget_enforced(tmp_path: Path) -> None:
    body = VALID_BODY + "line\n" * vs.SKILL_MD_MAX_LINES
    make_skill(tmp_path, body=body)
    assert any("suite budget" in e for e in errors_for(tmp_path))


def test_missing_skill_md_fails(tmp_path: Path) -> None:
    (tmp_path / "empty-skill").mkdir()
    assert errors_for(tmp_path) == ["empty-skill: missing SKILL.md"]


def test_empty_root_fails(tmp_path: Path) -> None:
    assert errors_for(tmp_path) == ["no skill directories found"]


def test_repository_skills_pass() -> None:
    errors, skill_dirs = vs.validate_suite(vs.DEFAULT_SKILLS_ROOT)
    assert errors == []
    assert len(skill_dirs) >= 11


def test_interpreter_caches_are_ignored(tmp_path: Path) -> None:
    sdir = make_skill(tmp_path, body=VALID_BODY + "Run `scripts/tool.py`.\n",
                      refs={"references/guide.md": "x\n", "scripts/tool.py": "print(1)\n"})
    cache = sdir / "scripts" / "__pycache__"
    cache.mkdir()
    (cache / "tool.cpython-312.pyc").write_bytes(b"\x00")
    assert errors_for(tmp_path) == []
