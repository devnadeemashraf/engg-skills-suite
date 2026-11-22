"""Tests for tools/sync_shared.py."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import sync_shared as ss  # noqa: E402

MANIFEST = """\
groups:
  core:
    files: [references/rules.md, scripts/check.sh]
    skills: [skill-a, skill-b]
"""


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    (tmp_path / "shared" / "references").mkdir(parents=True)
    (tmp_path / "shared" / "scripts").mkdir()
    (tmp_path / "shared" / "references" / "rules.md").write_text("# Rules\n", encoding="utf-8")
    (tmp_path / "shared" / "scripts" / "check.sh").write_text("echo ok\n", encoding="utf-8")
    (tmp_path / "shared" / "manifest.yaml").write_text(MANIFEST, encoding="utf-8")
    for skill in ("skill-a", "skill-b", "skill-c"):
        (tmp_path / "skills" / skill).mkdir(parents=True)
        (tmp_path / "skills" / skill / "SKILL.md").write_text("---\n---\n", encoding="utf-8")
    return tmp_path


def test_check_reports_missing_copies(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert ss.run(repo, check=True) == 1
    out = capsys.readouterr().out
    assert "missing copy: skills/skill-a/references/rules.md" in out
    assert "missing copy: skills/skill-b/scripts/check.sh" in out


def test_sync_writes_copies_then_check_passes(repo: Path) -> None:
    assert ss.run(repo, check=False) == 0
    assert (repo / "skills/skill-a/references/rules.md").read_text(encoding="utf-8") == "# Rules\n"
    assert (repo / "skills/skill-b/scripts/check.sh").is_file()
    assert not (repo / "skills/skill-c/references").exists()
    assert ss.run(repo, check=True) == 0


def test_check_changes_nothing(repo: Path) -> None:
    ss.run(repo, check=True)
    assert not (repo / "skills/skill-a/references").exists()


def test_edited_copy_is_drift(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ss.run(repo, check=False)
    (repo / "skills/skill-a/references/rules.md").write_text("# Edited locally\n", encoding="utf-8")
    assert ss.run(repo, check=True) == 1
    assert "out of date: skills/skill-a/references/rules.md" in capsys.readouterr().out


def test_crlf_copy_is_not_drift(repo: Path) -> None:
    ss.run(repo, check=False)
    (repo / "skills/skill-a/references/rules.md").write_bytes(b"# Rules\r\n")
    assert ss.run(repo, check=True) == 0


def test_unassigned_copy_is_stale_and_removed(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    ss.run(repo, check=False)
    stray = repo / "skills/skill-c/references/rules.md"
    stray.parent.mkdir(parents=True)
    stray.write_text("# Rules\n", encoding="utf-8")
    assert ss.run(repo, check=True) == 1
    assert "stale copy (no longer assigned): skills/skill-c/references/rules.md" in capsys.readouterr().out
    assert ss.run(repo, check=False) == 0
    assert not stray.exists()


def test_skill_specific_files_are_left_alone(repo: Path) -> None:
    own = repo / "skills/skill-c/references/own-guide.md"
    own.parent.mkdir(parents=True)
    own.write_text("mine\n", encoding="utf-8")
    ss.run(repo, check=False)
    assert own.read_text(encoding="utf-8") == "mine\n"


@pytest.mark.parametrize(
    ("manifest", "expected"),
    [
        ("groups:\n  g:\n    files: [references/nope.md]\n    skills: [skill-a]\n", "shared file not found"),
        ("groups:\n  g:\n    files: [references/rules.md]\n    skills: [skill-z]\n", "unknown skill 'skill-z'"),
        ("groups:\n  g:\n    files: [references/rules.md]\n", "exactly 'files' and 'skills'"),
        ("groups: {}\n", "non-empty 'groups'"),
        ("groups:\n  g:\n    files: [references/rules.md]\n    skills: [skill-a]\nextra: 1\n", "unknown top-level keys"),
        (
            "groups:\n  g:\n    files: [references/rules.md]\n    skills: [skill-a]\n"
            "  h:\n    files: [references/rules.md]\n    skills: [skill-a]\n",
            "assigned to 'skill-a' twice",
        ),
    ],
)
def test_invalid_manifest(repo: Path, capsys: pytest.CaptureFixture[str], manifest: str, expected: str) -> None:
    (repo / "shared/manifest.yaml").write_text(manifest, encoding="utf-8")
    assert ss.run(repo, check=True) == 1
    assert expected in capsys.readouterr().out


def test_nested_shared_path_rejected(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (repo / "shared/references/deep").mkdir()
    (repo / "shared/references/deep/x.md").write_text("x\n", encoding="utf-8")
    (repo / "shared/manifest.yaml").write_text(
        "groups:\n  g:\n    files: [references/deep/x.md]\n    skills: [skill-a]\n", encoding="utf-8"
    )
    assert ss.run(repo, check=True) == 1
    assert "must be <references|scripts|assets>/<file>" in capsys.readouterr().out


def test_repository_is_in_sync() -> None:
    assert ss.run(REPO_ROOT, check=True) == 0


def test_cli_rejects_unknown_arguments() -> None:
    assert ss.main(["sync_shared.py", "--bogus"]) == 2
