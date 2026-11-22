"""Tests for shared/scripts/ratchet.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO_ROOT / "shared" / "scripts"))

import ratchet  # noqa: E402

RAW = REPO_ROOT / "tests" / "fixtures" / "deep-audit-raw" / "ts-messy-api"

# Real lint-imports output shape (from the Phase 2 fixture run).
IMPORT_LINTER_TEXT = """\
Contracts
---------

Analyzed 9 files, 6 dependencies.
---------------------------------

Layer 'domain' must not import layer 'application' KEPT
Layer 'domain' must not import layer 'adapters' BROKEN

Contracts: 1 kept, 1 broken.

----------------
Broken contracts
----------------

Layer 'domain' must not import layer 'adapters'
-----------------------------------------------

shop.*.domain is not allowed to import shop.*.adapters:

-   shop.orders.domain.leak -> shop.orders.adapters.repo (l.1)
"""


def depcruise_file(tmp_path: Path, violations: list[dict]) -> Path:
    path = tmp_path / f"dc-{len(violations)}-{id(violations)}.json"
    path.write_text(json.dumps({"summary": {"violations": violations}}), encoding="utf-8")
    return path


def v(rule: str, src: str, dst: str) -> dict:
    return {"rule": {"name": rule, "severity": "error"}, "from": src, "to": dst}


def run(*args: str) -> int:
    return ratchet.main(list(args))


def test_keys_from_real_tool_output() -> None:
    dc = ratchet.from_depcruise(RAW / "depcruise.json")
    assert "dependency-cruiser:domain-not-to-adapters:src/orders/domain/order.ts->src/orders/adapters/order-repo.ts" in dc
    assert all(":" in k and "->" in k for k in dc)
    assert ratchet.from_gitleaks(RAW / "gitleaks.json") == ["gitleaks:generic-api-key:src/config.ts"]


def test_keys_from_import_linter_text(tmp_path: Path) -> None:
    f = tmp_path / "il.txt"
    f.write_text(IMPORT_LINTER_TEXT, encoding="utf-8")
    assert ratchet.from_import_linter(f) == [
        "import-linter:Layer 'domain' must not import layer 'adapters':shop.orders.domain.leak->shop.orders.adapters.repo"
    ]


def test_keys_from_sarif(tmp_path: Path) -> None:
    f = tmp_path / "x.sarif"
    f.write_text(json.dumps({"runs": [{"tool": {"driver": {"name": "opengrep"}}, "results": [
        {"ruleId": "sql-injection", "locations": [{"physicalLocation": {"artifactLocation": {"uri": "src\\db.ts"}, "region": {"startLine": 9}}}]}
    ]}]}), encoding="utf-8")
    assert ratchet.from_sarif(f) == ["opengrep:sql-injection:src/db.ts"]


def test_record_check_update_cycle(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    base = str(tmp_path / ".engg/baseline/violations.json")
    three = depcruise_file(tmp_path, [v("a", "x.ts", "y.ts"), v("b", "p.ts", "q.ts"), v("b", "p.ts", "q.ts")])
    assert run("record", "--baseline", base, "--depcruise", str(three)) == 0
    assert json.loads(Path(base).read_text(encoding="utf-8"))["total"] == 3
    assert run("record", "--baseline", base, "--depcruise", str(three)) == 1  # never overwrite

    assert run("check", "--baseline", base, "--depcruise", str(three)) == 0

    # A brand-new violation fails, and so does a second copy of a known one.
    worse = depcruise_file(tmp_path, [v("a", "x.ts", "y.ts"), v("b", "p.ts", "q.ts"), v("b", "p.ts", "q.ts"), v("c", "m.ts", "n.ts")])
    capsys.readouterr()
    assert run("check", "--baseline", base, "--depcruise", str(worse)) == 1
    assert "NEW     dependency-cruiser:c:m.ts->n.ts" in capsys.readouterr().out
    dup = depcruise_file(tmp_path, [v("a", "x.ts", "y.ts"), v("a", "x.ts", "y.ts"), v("b", "p.ts", "q.ts"), v("b", "p.ts", "q.ts")])
    assert run("check", "--baseline", base, "--depcruise", str(dup)) == 1

    # Update refuses to grow the baseline.
    assert run("update", "--baseline", base, "--depcruise", str(worse)) == 1
    assert json.loads(Path(base).read_text(encoding="utf-8"))["total"] == 3

    # Fixing violations passes, suggests shrinking, and update shrinks.
    better = depcruise_file(tmp_path, [v("b", "p.ts", "q.ts")])
    capsys.readouterr()
    assert run("check", "--baseline", base, "--depcruise", str(better)) == 0
    out = capsys.readouterr().out
    assert "FIXED   dependency-cruiser:a:x.ts->y.ts" in out and "can shrink" in out
    assert run("update", "--baseline", base, "--depcruise", str(better)) == 0
    assert json.loads(Path(base).read_text(encoding="utf-8"))["violations"] == {"dependency-cruiser:b:p.ts->q.ts": 1}


def test_dropping_a_source_is_refused(tmp_path: Path) -> None:
    base = str(tmp_path / "b.json")
    dc = depcruise_file(tmp_path, [v("a", "x.ts", "y.ts")])
    assert run("record", "--baseline", base, "--depcruise", str(dc), "--gitleaks", str(RAW / "gitleaks.json")) == 0
    # Leaving gitleaks out would make its findings look fixed; refuse instead of shrinking dishonestly.
    assert run("check", "--baseline", base, "--depcruise", str(dc)) == 2
    assert run("update", "--baseline", base, "--depcruise", str(dc)) == 2


def test_line_moves_are_not_new_violations(tmp_path: Path) -> None:
    base = str(tmp_path / "b.json")
    leaks = tmp_path / "leaks.json"
    leaks.write_text(json.dumps([{"RuleID": "generic-api-key", "File": "src/config.ts", "StartLine": 4}]), encoding="utf-8")
    assert run("record", "--baseline", base, "--gitleaks", str(leaks)) == 0
    leaks.write_text(json.dumps([{"RuleID": "generic-api-key", "File": "src/config.ts", "StartLine": 40}]), encoding="utf-8")
    assert run("check", "--baseline", base, "--gitleaks", str(leaks)) == 0


def test_needs_a_source_and_a_baseline(tmp_path: Path) -> None:
    assert run("check", "--baseline", str(tmp_path / "b.json")) == 2
    dc = depcruise_file(tmp_path, [])
    assert run("check", "--baseline", str(tmp_path / "missing.json"), "--depcruise", str(dc)) == 2


def test_require_tight_fails_on_an_unshrunk_baseline(tmp_path: Path) -> None:
    base = str(tmp_path / "b.json")
    two = depcruise_file(tmp_path, [v("a", "x.ts", "y.ts"), v("b", "p.ts", "q.ts")])
    one = depcruise_file(tmp_path, [v("b", "p.ts", "q.ts")])
    assert run("record", "--baseline", base, "--depcruise", str(two)) == 0
    assert run("check", "--baseline", base, "--depcruise", str(one)) == 0
    assert run("check", "--baseline", base, "--depcruise", str(one), "--require-tight") == 1
    assert run("update", "--baseline", base, "--depcruise", str(one)) == 0
    assert run("check", "--baseline", base, "--depcruise", str(one), "--require-tight") == 0
