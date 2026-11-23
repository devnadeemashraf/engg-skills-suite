"""Tests for the working-loop scripts: brief.py, map.py, check.py, attribution_check.py."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "shared" / "scripts"))

import brief  # noqa: E402
import check  # noqa: E402
import map as repo_map  # noqa: E402

HANDOFF = """\
# Handoff

Stage: build · Mode: mvp-first · Baseline: greenfield

## In progress
None.

## Fix first
None.

## Questions for the human
None.

## Gotchas
- The dev server needs PORT set.

## Next
The next open chunk in docs/BLUEPRINT.md.
"""

BLUEPRINT = """\
# Blueprint

**Delivery mode:** mvp-first

## Done

- C1 Harness and CI — Wave 1 — #1

## Wave 1 — Walking skeleton

### [C2] Reference slice (Wave 1, Tier T2)
- **Goal:** Prove the architecture end to end.
- **Dependencies:** C1
- **Cites:** EDD §3, CHARTER §2, ADR-0002
- **Follow:** `src/orders/app/place-order.ts`, `src/orders/http/routes.ts`

### [C3] Second slice (Wave 1, Tier T1)
- **Dependencies:** C2

## Wave 2 — Hardening

### [C4] Rate limits (Wave 2, Tier T2)
- **Dependencies:** C1

## Backlog

- Dark mode — not core.
"""

EDD = """\
# EDD

## 2. Modules
Modular monolith.

## 3. Contracts
Every request is validated by a schema.

### 3.1 Errors
Error envelope.

## 4. Data
Postgres.
"""


def write(root: Path, rel: str, text: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture()
def loop_repo(tmp_path: Path) -> Path:
    write(tmp_path, "docs/HANDOFF.md", HANDOFF)
    write(tmp_path, "docs/BLUEPRINT.md", BLUEPRINT)
    write(tmp_path, "docs/EDD.md", EDD)
    write(tmp_path, "docs/CHARTER.md", "# Charter\n\n## 2. Users\nJob seekers.\n\n## 3. Scope\nV1.\n")
    write(tmp_path, "docs/decisions/0002-modular-monolith.md", "# ADR 2\n")
    return tmp_path


def run_brief(root: Path, capsys: pytest.CaptureFixture[str], *args: str) -> tuple[int, str]:
    code = brief.main(["--root", str(root), *args])
    return code, capsys.readouterr().out


# ---------- brief.py ----------

def test_brief_prints_next_ready_chunk_with_citations(loop_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out = run_brief(loop_repo, capsys)
    assert code == 0
    assert "== HANDOFF ==" in out and "The dev server needs PORT set." in out
    assert "== NEXT CHUNK ==" in out and "[C2] Reference slice" in out
    assert "[C3]" not in out, "only the next chunk is printed"
    assert "## 3. Contracts" in out and "### 3.1 Errors" in out and "## 4. Data" not in out
    assert "## 2. Users" in out
    assert "ADR 0002: docs/decisions/0002-modular-monolith.md" in out
    assert "src/orders/app/place-order.ts" in out


def test_brief_skips_chunks_with_open_dependencies(loop_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    text = BLUEPRINT.replace("### [C2] Reference slice (Wave 1, Tier T2)\n- **Goal:** Prove the architecture end to end.\n- **Dependencies:** C1",
                             "### [C2] Reference slice (Wave 1, Tier T2)\n- **Goal:** x\n- **Dependencies:** C9")
    write(loop_repo, "docs/BLUEPRINT.md", text)
    _, out = run_brief(loop_repo, capsys)
    assert "[C4] Rate limits" in out


def test_brief_resumes_in_progress_first(loop_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(loop_repo, "docs/HANDOFF.md", HANDOFF.replace("## In progress\nNone.", "## In progress\n- C2 on feat/C2-slice: tests red"))
    _, out = run_brief(loop_repo, capsys)
    assert "resume the In progress entry" in out
    assert "NEXT CHUNK" not in out


def test_brief_puts_fix_first_before_chunks(loop_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(loop_repo, "docs/HANDOFF.md", HANDOFF.replace("## Fix first\nNone.", "## Fix first\n- FIX-3 src/a.ts:10 — off by one"))
    _, out = run_brief(loop_repo, capsys)
    assert "== NEXT: FIX-3 (Fix first) ==" in out
    assert "NEXT CHUNK" not in out


def test_brief_reports_wave_gate_due(loop_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    text = BLUEPRINT.split("## Wave 1")[0] + "## Wave 2 — Hardening\n\n### [C4] Rate limits (Wave 2, Tier T2)\n- **Dependencies:** C1\n"
    write(loop_repo, "docs/BLUEPRINT.md", text)
    _, out = run_brief(loop_repo, capsys)
    assert "WAVE GATE DUE: Wave 1" in out
    write(loop_repo, "docs/BLUEPRINT.md", text.replace("- C1 Harness", "- Gate 1 — 2026-11-23\n- C1 Harness"))
    _, out = run_brief(loop_repo, capsys)
    assert "WAVE GATE DUE" not in out


def test_brief_without_handoff_explains_setup(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out = run_brief(tmp_path, capsys)
    assert code == 0 and "isn't set up" in out


def test_brief_chunk_flag_prints_that_card(loop_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code, out = run_brief(loop_repo, capsys, "--chunk", "C4")
    assert code == 0 and "[C4] Rate limits" in out
    code, out = run_brief(loop_repo, capsys, "--chunk", "C1")
    assert code == 1 and "not an open chunk" in out


# ---------- map.py ----------

def git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.fixture()
def code_repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    write(tmp_path, "src/orders/place-order.ts",
          "export async function placeOrder() {}\nexport type OrderId = string;\nexport { a as b, c };\nconst hidden = 1;\n")
    write(tmp_path, "src/orders/index.ts", "export * from './place-order';\n")
    write(tmp_path, "app/service.py", "def handle():\n    pass\n\nclass Repo:\n    pass\n\ndef _private():\n    pass\n")
    write(tmp_path, "cmd/main.go", "package main\nfunc Run() {}\nfunc helper() {}\ntype Server struct{}\n")
    write(tmp_path, "package-lock.json", "{}\n")
    write(tmp_path, ".engg/generated/x.cjs", "module.exports = {}\n")
    return tmp_path


def test_map_lists_files_with_exported_symbols(code_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert repo_map.main(["--root", str(code_repo)]) == 0
    out = capsys.readouterr().out
    assert "src/orders/place-order.ts: placeOrder, OrderId, b, c" in out
    assert "src/orders/index.ts: * from ./place-order" in out
    assert "app/service.py: handle, Repo" in out and "_private" not in out
    assert "cmd/main.go: Run, Server" in out and "helper" not in out
    assert "package-lock.json" not in out and ".engg/generated" not in out


def test_map_prefix_and_dirs(code_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo_map.main(["--root", str(code_repo), "src/"])
    out = capsys.readouterr().out
    assert "src/orders/index.ts" in out and "app/service.py" not in out
    repo_map.main(["--root", str(code_repo), "--dirs"])
    out = capsys.readouterr().out
    assert "src/orders/  2" in out and "app/  1" in out


def test_map_large_repo_shows_dirs_by_default(code_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo_map.main(["--root", str(code_repo), "--max", "2"])
    out = capsys.readouterr().out
    assert "showing directories" in out and "src/orders/  2" in out


# ---------- check.py ----------

PY = sys.executable.replace("\\", "/")


def test_check_compact_output(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    write(tmp_path, ".engg/check.toml", f"""\
# gates
[[stage]]
name = "lint"
run = '"{PY}" -c "print(1)"'

[[stage]]
name = "test"
run = '"{PY}" -c "import sys; [print(i) for i in range(100)]; sys.exit(3)"'

[[stage]]
name = "never"
run = '"{PY}" -c "print(2)"'
""")
    assert check.main(["--root", str(tmp_path), "--tail", "5"]) == 1
    out = capsys.readouterr().out
    assert out.startswith("ok   lint")
    assert "FAIL test (exit 3" in out
    assert "95 earlier lines omitted" in out and "\n99" in out and "\n50\n" not in out
    assert "never" not in out, "stops at the first failure"
    assert check.main(["--root", str(tmp_path), "--keep-going", "lint", "never"]) == 0


def test_check_reports_configuration_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert check.main(["--root", str(tmp_path)]) == 2
    assert "no .engg/check.toml" in capsys.readouterr().out
    write(tmp_path, ".engg/check.toml", '[[stage]]\nname = "x"\n')
    assert check.main(["--root", str(tmp_path)]) == 2
    write(tmp_path, ".engg/check.toml", '[[stage]]\nname = "x"\nrun = "echo"\n')
    assert check.main(["--root", str(tmp_path), "nope"]) == 2


def test_check_minimal_parser_matches_format() -> None:
    data = check.parse_minimal('# c\n[[stage]]\nname = "a"\nrun = \'x "y"\'  # note\ntimeout = 30\n')
    assert data == {"stage": [{"name": "a", "run": 'x "y"', "timeout": 30}]}
    with pytest.raises(check.ConfigError):
        check.parse_minimal("name = 'orphan'\n")
