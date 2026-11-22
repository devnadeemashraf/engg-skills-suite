"""Tests for skills/engg-deep-audit/scripts (build_map.py and ledger.py).

The map tests use real tool outputs recorded from evals/fixtures/ts-messy-api by tools/capture_audit_raw.py,
so the parsers are checked against the formats the tools actually produce (including Windows paths).
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
# Importing skill scripts must not leave __pycache__ inside skill folders (installers copy them).
sys.dont_write_bytecode = True
sys.path.insert(0, str(REPO_ROOT / "skills" / "engg-deep-audit" / "scripts"))

import build_map  # noqa: E402
import ledger  # noqa: E402

FIXTURE = REPO_ROOT / "evals" / "fixtures" / "ts-messy-api"
RAW = REPO_ROOT / "tests" / "fixtures" / "deep-audit-raw" / "ts-messy-api"
CONTRACT = FIXTURE / ".engg" / "architecture.yaml"


@pytest.fixture()
def run_dir(tmp_path: Path) -> Path:
    run = tmp_path / "run"
    shutil.copytree(RAW, run / "raw")
    return run


@pytest.fixture()
def mapped(run_dir: Path) -> dict:
    assert build_map.main(["--run-dir", str(run_dir), "--contract", str(CONTRACT), "--repo-root", str(FIXTURE)]) == 0
    return json.loads((run_dir / "map.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- build_map


def test_every_input_is_recorded(mapped: dict) -> None:
    ran = {k for k, v in mapped["inputs"].items() if v == "ran"}
    assert {"files", "churn", "scc", "lizard", "jscpd", "gitleaks", "depcruise", "graph", "graph_report"} <= ran
    assert mapped["inputs"]["osv"] == "not run"


def test_layers_and_unassigned(mapped: dict) -> None:
    assert mapped["unassigned"] == ["src/scratch/tmp-migrate.ts"]
    assert mapped["overlaps"] == []
    layer_of = {f: m["layer"] for f, m in mapped["files"].items()}
    assert layer_of["src/orders/domain/order.ts"] == "domain"
    assert layer_of["src/orders/index.ts"] == "application"
    assert layer_of["src/shared/index.ts"] == "shared"
    assert layer_of["src/config.ts"] == "composition"


def test_windows_tool_paths_are_resolved(mapped: dict) -> None:
    # lizard and jscpd report backslash paths relative to the scanned folder.
    po = mapped["files"]["src/orders/app/place-order.ts"]
    assert po["max_ccn"] == 14
    assert [f["name"] for f in po["functions_over_limit"]] == ["placeOrder"]
    assert po["duplicated_lines"] > 0


def test_tool_findings_attach_to_files(mapped: dict) -> None:
    leaks = [t for t in mapped["files"]["src/config.ts"]["tool_findings"] if t["tool"] == "gitleaks"]
    assert [(t["rule"], t["line"]) for t in leaks] == [("generic-api-key", 4)]
    rules = {t["rule"] for t in mapped["files"]["src/orders/domain/order.ts"]["tool_findings"]}
    assert "domain-not-to-adapters" in rules
    assert "transport-not-to-adapters" in {t["rule"] for t in mapped["files"]["src/orders/http/routes.ts"]["tool_findings"]}


def test_dead_code_signals(mapped: dict) -> None:
    assert mapped["dead_file_candidates"] == ["src/scratch/tmp-migrate.ts", "src/shared/legacy-format.ts"]
    symbols = {(s["symbol"], s["file"]) for s in mapped["unreferenced_symbols"]}
    assert symbols == {
        ("formatCurrencyOld", "src/shared/utils.ts"),
        ("legacyFormatOrderId", "src/shared/legacy-format.ts"),
        ("legacyParseOrderId", "src/shared/legacy-format.ts"),
        ("migrateAll", "src/scratch/tmp-migrate.ts"),
    }


def test_cycles_and_duplicates(mapped: dict) -> None:
    cycles = [sorted(c) for c in mapped["cycles"]]
    assert sorted(["src/orders/app/place-order.ts", "src/orders/app/pricing.ts"]) in cycles
    dup_files = {c[k]["file"] for c in mapped["duplicates"] for k in ("a", "b")}
    assert dup_files == {"src/orders/app/place-order.ts", "src/orders/app/cancel-order.ts", "src/users/app/register.ts"}


def test_units_cover_every_file_once_inner_layers_first(mapped: dict) -> None:
    units = mapped["units"]
    covered = [f for u in units for f in u["files"]]
    assert sorted(covered) == sorted(mapped["files"])
    assert len(covered) == len(set(covered))
    order = [l["name"] for l in mapped["layers"]] + ["unassigned"]
    positions = [order.index(u["layer"]) for u in units]
    assert positions == sorted(positions)
    assert units[0]["layer"] == "domain" and units[-1]["layer"] == "unassigned"
    assert [u["id"] for u in units] == [f"U{i:03d}" for i in range(1, len(units) + 1)]


def test_hotspot_ranking(mapped: dict) -> None:
    assert mapped["hotspots"][0] == "src/orders/app/place-order.ts"


def test_test_files_are_ranked_apart_from_production(tmp_path: Path) -> None:
    run = tmp_path / "run"
    shutil.copytree(REPO_ROOT / "tests/fixtures/deep-audit-raw/ts-clean-api", run / "raw")
    clean = REPO_ROOT / "evals/fixtures/ts-clean-api"
    assert build_map.main(["--run-dir", str(run), "--contract", str(clean / ".engg/architecture.yaml"),
                           "--repo-root", str(clean)]) == 0
    m = json.loads((run / "map.json").read_text(encoding="utf-8"))
    test_file = "src/orders/app/place-order.test.ts"
    assert test_file not in m["hotspots"]
    assert m["test_hotspots"] == [test_file]
    assert "## Hotspots, test code" in (run / "map.md").read_text(encoding="utf-8")


def test_units_split_at_line_budget(run_dir: Path) -> None:
    assert build_map.main(["--run-dir", str(run_dir), "--contract", str(CONTRACT),
                           "--repo-root", str(FIXTURE), "--max-unit-lines", "20"]) == 0
    m = json.loads((run_dir / "map.json").read_text(encoding="utf-8"))
    app_units = [u for u in m["units"] if u["layer"] == "application" and u["module"] == "orders"]
    assert len(app_units) >= 2
    for u in m["units"]:
        assert u["loc"] <= 20 or len(u["files"]) == 1


def test_map_with_only_file_list(tmp_path: Path) -> None:
    run = tmp_path / "run"
    (run / "raw").mkdir(parents=True)
    shutil.copy(RAW / "files.txt", run / "raw" / "files.txt")
    assert build_map.main(["--run-dir", str(run), "--contract", str(CONTRACT), "--repo-root", str(FIXTURE)]) == 0
    m = json.loads((run / "map.json").read_text(encoding="utf-8"))
    assert m["inputs"]["graph"] == "not run" and m["inputs"]["lizard"] == "not run"
    assert m["files"]["src/orders/app/place-order.ts"]["loc"] > 0  # fallback line count
    assert m["dead_file_candidates"] == []  # no graph, no claim
    assert "not run" in (run / "map.md").read_text(encoding="utf-8")


def test_map_requires_file_list(tmp_path: Path) -> None:
    (tmp_path / "raw").mkdir()
    with pytest.raises(SystemExit, match="files.txt"):
        build_map.main(["--run-dir", str(tmp_path), "--contract", str(CONTRACT), "--repo-root", str(FIXTURE)])


def test_invalid_contract_reported(run_dir: Path, tmp_path: Path) -> None:
    bad = tmp_path / "bad.yaml"
    bad.write_text("version: 2\n", encoding="utf-8")
    assert build_map.main(["--run-dir", str(run_dir), "--contract", str(bad), "--repo-root", str(FIXTURE)]) == 2


# --------------------------------------------------------------------------- ledger


@pytest.fixture()
def ready(run_dir: Path, mapped: dict) -> Path:
    assert ledger.main(["init", "--run-dir", str(run_dir)]) == 0
    return run_dir


def write_findings(run_dir: Path, unit: str, findings: list[dict]) -> None:
    (run_dir / "findings" / f"{unit}.yaml").write_text(yaml.safe_dump(findings, sort_keys=False), encoding="utf-8")


def good_finding(unit: str = "U001", **overrides: object) -> dict:
    f = {
        "id": f"{unit}-01", "title": "Domain imports the order repository adapter", "severity": "P1",
        "action": "MOVE", "pillar": "architecture", "location": "src/orders/domain/order.ts:2",
        "evidence": "dependency-cruiser domain-not-to-adapters", "source": "tool:dependency-cruiser",
        "triage": "TRUE", "fix": "Move OrderRow mapping into the adapter.", "test": "depcruise rule passes",
    }
    f.update(overrides)
    return f


def test_init_refuses_to_overwrite(ready: Path) -> None:
    assert ledger.main(["init", "--run-dir", str(ready)]) == 1
    assert ledger.main(["init", "--run-dir", str(ready), "--force"]) == 0


def test_next_prints_context_pack_and_resumes(ready: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert ledger.main(["next", "--run-dir", str(ready)]) == 0
    first = capsys.readouterr().out
    assert first.startswith("# Unit U001: layer `domain`")
    assert "src/orders/domain/order.ts" in first and "domain-not-to-adapters" in first
    assert "Import cycles touching this unit" in first
    # Interrupted before `done`: the same unit comes back.
    assert ledger.main(["next", "--run-dir", str(ready)]) == 0
    assert capsys.readouterr().out == first
    statuses = [u["status"] for u in ledger.load(ready)]
    assert statuses[0] == "in_progress" and set(statuses[1:]) == {"pending"}


@pytest.mark.parametrize(
    ("findings", "message"),
    [
        (None, "missing"),
        ([good_finding(severity="P5")], "severity must be one of"),
        ([good_finding(action="FIX")], "action must be one of"),
        ([good_finding(pillar="vibes")], "pillar must be one of"),
        ([good_finding(id="U009-01")], "must start with 'U001-'"),
        ([good_finding(), good_finding()], "duplicate id"),
        ([good_finding(test="")], "P0/P1 findings need a 'test'"),
        ([good_finding(triage="")], "tool findings need triage"),
        ([good_finding(triage="FALSE-POSITIVE")], "tool findings need triage"),
        ([good_finding(source="grep")], "source must be"),
        ([good_finding(location="somewhere in order.ts")], "location must be"),
        ([good_finding(owner="me")], "unknown field 'owner'"),
        ([{k: v for k, v in good_finding().items() if k != "evidence"}], "missing 'evidence'"),
    ],
)
def test_done_rejects_invalid_findings(ready: Path, capsys: pytest.CaptureFixture[str], findings, message: str) -> None:
    if findings is not None:
        write_findings(ready, "U001", findings)
    assert ledger.main(["done", "--run-dir", str(ready), "--unit", "U001", "--summary", "s"]) == 1
    assert message in capsys.readouterr().out
    assert ledger.load(ready)[0]["status"] != "done"


def test_done_accepts_valid_and_clean_units(ready: Path) -> None:
    write_findings(ready, "U001", [good_finding(), good_finding(id="U001-02", severity="P3", source="review", triage=None, test=None)])
    # PyYAML writes None as null; strip nulls the way a hand-written file would omit them.
    data = [{k: v for k, v in f.items() if v is not None} for f in yaml.safe_load((ready / "findings/U001.yaml").read_text(encoding="utf-8"))]
    write_findings(ready, "U001", data)
    assert ledger.main(["done", "--run-dir", str(ready), "--unit", "U001", "--summary", "Domain leaks an adapter type."]) == 0
    (ready / "findings" / "U002.yaml").write_text("[]\n", encoding="utf-8")
    assert ledger.main(["done", "--run-dir", str(ready), "--unit", "U002", "--summary", "Clean: checked x, y."]) == 0
    units = ledger.load(ready)
    assert units[0]["status"] == "done" and units[0]["counts"] == {"P1": 1, "P3": 1}
    assert units[1]["counts"] == {}


def test_hand_written_unquoted_true_triage_is_accepted(ready: Path) -> None:
    # Regression: YAML parses an unquoted TRUE as a boolean; the schema's own example writes it unquoted.
    (ready / "findings" / "U001.yaml").write_text(
        "- id: U001-01\n  title: t\n  severity: P2\n  action: MOVE\n  pillar: architecture\n"
        "  location: src/orders/domain/order.ts:1\n  evidence: e\n  source: tool:dependency-cruiser\n"
        "  triage: TRUE\n  fix: f\n", encoding="utf-8")
    assert ledger.main(["done", "--run-dir", str(ready), "--unit", "U001", "--summary", "s"]) == 0


def test_done_requires_short_summary(ready: Path) -> None:
    (ready / "findings" / "U001.yaml").write_text("[]\n", encoding="utf-8")
    assert ledger.main(["done", "--run-dir", str(ready), "--unit", "U001", "--summary", ""]) == 2
    assert ledger.main(["done", "--run-dir", str(ready), "--unit", "U001", "--summary", "x" * 601]) == 2
    assert ledger.main(["done", "--run-dir", str(ready), "--unit", "U999", "--summary", "x"]) == 2


def test_report_aggregates_and_flags_incomplete(ready: Path) -> None:
    write_findings(ready, "U001", [good_finding()])
    assert ledger.main(["done", "--run-dir", str(ready), "--unit", "U001", "--summary", "s"]) == 0
    strip = good_finding("S-shared", id="S-shared-01", action="STRIP", severity="P3", source="review",
                         location="src/shared/legacy-format.ts", title="Legacy formatter is unused")
    strip.pop("triage"); strip.pop("test")
    write_findings(ready, "S-shared", [strip])
    assert ledger.main(["report", "--run-dir", str(ready)]) == 0
    text = (ready / "report-data.md").read_text(encoding="utf-8")
    assert "**INCOMPLETE:**" in text
    assert "osv" in text.split("## Checks not run", 1)[1].split("##", 1)[0]
    assert "S-shared-01" in text.split("## Strip list", 1)[1].split("##", 1)[0]
    assert "U001-01" in text.split("## Move / reorganise list", 1)[1].split("##", 1)[0]


def test_report_rejects_invalid_synthesis_file(ready: Path) -> None:
    write_findings(ready, "S-domain", [good_finding(id="U001-01")])
    assert ledger.main(["report", "--run-dir", str(ready)]) == 1


def test_status_and_summaries(ready: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (ready / "findings" / "U001.yaml").write_text("[]\n", encoding="utf-8")
    ledger.main(["done", "--run-dir", str(ready), "--unit", "U001", "--summary", "Domain unit summary."])
    capsys.readouterr()
    assert ledger.main(["status", "--run-dir", str(ready)]) == 0
    assert "domain" in capsys.readouterr().out
    assert ledger.main(["summaries", "--run-dir", str(ready), "--layer", "domain"]) == 0
    assert "Domain unit summary." in capsys.readouterr().out


# --------------------------------------------------------------------------- clean fixture: no tool-level false alarms


def test_clean_fixture_map_raises_no_alarms(tmp_path: Path) -> None:
    run = tmp_path / "run"
    shutil.copytree(REPO_ROOT / "tests/fixtures/deep-audit-raw/ts-clean-api", run / "raw")
    clean = REPO_ROOT / "evals/fixtures/ts-clean-api"
    assert build_map.main(["--run-dir", str(run), "--contract", str(clean / ".engg/architecture.yaml"),
                           "--repo-root", str(clean)]) == 0
    m = json.loads((run / "map.json").read_text(encoding="utf-8"))
    assert [t for f in m["files"].values() for t in f["tool_findings"]] == []
    assert [x for f in m["files"].values() for x in f["functions_over_limit"]] == []
    assert m["unassigned"] == [] and m["overlaps"] == []
    assert m["dead_file_candidates"] == []
    assert m["unreferenced_symbols"] == []  # compose() in main.ts is an entry point, not dead code
    assert m["duplicates"] == [] and m["cycles"] == []


def test_skip_records_a_reason_and_report_says_partial(ready: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert ledger.main(["skip", "--run-dir", str(ready), "--unit", "U002", "--reason", "short"]) == 2
    assert ledger.main(["skip", "--run-dir", str(ready), "--unit", "U999", "--reason", "a long enough reason"]) == 2
    assert ledger.main(["skip", "--run-dir", str(ready), "--unit", "U002",
                        "--reason", "Tooling only; covered by tool signals, not line-read."]) == 0
    assert [u["status"] for u in ledger.load(ready)][1] == "skipped"
    # next never hands out a skipped unit
    for u in ledger.load(ready):
        if u["id"] not in ("U002",):
            (ready / "findings" / f"{u['id']}.yaml").write_text("[]\n", encoding="utf-8")
            assert ledger.main(["done", "--run-dir", str(ready), "--unit", u["id"], "--summary", "Reviewed: clean."]) == 0
    capsys.readouterr()
    assert ledger.main(["next", "--run-dir", str(ready)]) == 0
    assert "every unit is done" in capsys.readouterr().out
    assert ledger.main(["report", "--run-dir", str(ready)]) == 0
    text = (ready / "report-data.md").read_text(encoding="utf-8")
    assert "**INCOMPLETE:**" not in text and "**PARTIAL:** 1 unit(s)" in text
    assert "**U002**" in text.split("## Units not reviewed (skipped on purpose)", 1)[1]
    assert ledger.main(["status", "--run-dir", str(ready)]) == 0
    assert "SKIP" in capsys.readouterr().out


def test_a_reviewed_unit_cannot_be_skipped(ready: Path) -> None:
    (ready / "findings" / "U001.yaml").write_text("[]\n", encoding="utf-8")
    assert ledger.main(["done", "--run-dir", str(ready), "--unit", "U001", "--summary", "Reviewed: clean."]) == 0
    assert ledger.main(["skip", "--run-dir", str(ready), "--unit", "U001", "--reason", "changed my mind about it"]) == 1
