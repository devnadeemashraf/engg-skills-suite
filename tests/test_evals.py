"""Tests for evals/score.py and evals/prepare.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "evals"))

import prepare  # noqa: E402
import score  # noqa: E402

DEFECTS = [
    {"id": "D1", "what": "sqli", "files": ["a.ts"], "actions": ["HARDEN"], "keywords": ["sql"], "max_severity": "P0"},
    {"id": "D2", "what": "timeout", "files": ["a.ts"], "actions": ["HARDEN"], "keywords": ["timeout"], "max_severity": "P1"},
    {"id": "D3", "what": "dead", "files": ["b.ts"], "actions": ["STRIP"], "keywords": ["unused"], "max_severity": "P3"},
]


def finding(fid: str, location: str, action: str, title: str, severity: str = "P1") -> dict:
    return {"id": fid, "location": location, "action": action, "title": title, "evidence": "", "severity": severity}


def test_matching_needs_file_action_and_keyword() -> None:
    assert score.matches(finding("x", "a.ts:3", "HARDEN", "SQL injection"), DEFECTS[0])
    assert not score.matches(finding("x", "b.ts:3", "HARDEN", "SQL injection"), DEFECTS[0])  # wrong file
    assert not score.matches(finding("x", "a.ts:3", "MOVE", "SQL injection"), DEFECTS[0])  # wrong action
    assert not score.matches(finding("x", "a.ts:3", "HARDEN", "Bad query"), DEFECTS[0])  # no keyword


def test_one_finding_matches_one_defect() -> None:
    # One finding mentioning both problems must not count for both defects.
    both = finding("x", "a.ts:1", "HARDEN", "SQL injection and no timeout")
    matched, extras = score.score([both], DEFECTS)
    assert len(matched) == 1 and extras == []


def test_cli_messy_gate(tmp_path: Path) -> None:
    (tmp_path / "f").mkdir()
    expected = tmp_path / "expected.yaml"
    expected.write_text(yaml.safe_dump({"fixture": "t", "defects": DEFECTS}), encoding="utf-8")
    good = [finding("U1-01", "a.ts:1", "HARDEN", "SQL injection", "P0"),
            finding("U1-02", "a.ts:5", "HARDEN", "No timeout", "P1"),
            finding("U1-03", "b.ts", "STRIP", "unused file", "P3")]
    (tmp_path / "f/U1.yaml").write_text(yaml.safe_dump(good), encoding="utf-8")
    assert score.main(["--findings", str(tmp_path / "f"), "--expected", str(expected)]) == 0
    # The P0 rated as P2 is under-rated: the gate fails even with full recall.
    good[0]["severity"] = "P2"
    (tmp_path / "f/U1.yaml").write_text(yaml.safe_dump(good), encoding="utf-8")
    assert score.main(["--findings", str(tmp_path / "f"), "--expected", str(expected)]) == 1


def test_cli_clean_gate(tmp_path: Path) -> None:
    (tmp_path / "f").mkdir()
    (tmp_path / "f/U1.yaml").write_text(yaml.safe_dump([finding("U1-01", "a.ts", "TEST", "more tests", "P2")]), encoding="utf-8")
    assert score.main(["--findings", str(tmp_path / "f"), "--expected", "unused", "--clean"]) == 0
    (tmp_path / "f/U2.yaml").write_text(yaml.safe_dump([finding("U2-01", "a.ts", "HARDEN", "bug", "P1")]), encoding="utf-8")
    assert score.main(["--findings", str(tmp_path / "f"), "--expected", "unused", "--clean"]) == 1


def test_answer_key_is_well_formed() -> None:
    key = yaml.safe_load((REPO_ROOT / "evals/expected/ts-messy-api.yaml").read_text(encoding="utf-8"))
    ids = [d["id"] for d in key["defects"]]
    assert len(ids) == len(set(ids)) >= 17
    fixture = REPO_ROOT / "evals/fixtures/ts-messy-api"
    for d in key["defects"]:
        assert d["max_severity"] in score.RANK
        assert d["actions"] and d["keywords"]
        for f in d["files"]:
            assert (fixture / f).is_file(), f"{d['id']}: {f} does not exist in the fixture"


def test_prepare_strips_answers_and_makes_git_repo(tmp_path: Path) -> None:
    target = tmp_path / "messy"
    assert prepare.main(["prepare.py", str(REPO_ROOT / "evals/fixtures/ts-messy-api"), str(target)]) == 0
    texts = [p.read_text(encoding="utf-8") for p in target.rglob("*.ts")]
    assert texts and not any("DEFECT" in t for t in texts)
    out = subprocess.run(["git", "ls-files"], cwd=target, capture_output=True, text=True, check=True).stdout
    assert "src/orders/domain/order.ts" in out
    assert prepare.main(["prepare.py", str(REPO_ROOT / "evals/fixtures/ts-messy-api"), str(target)]) == 1
