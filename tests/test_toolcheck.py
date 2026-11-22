"""Tests for shared/scripts/toolcheck.sh and toolcheck.ps1.

Each script runs against fake tools on a PATH that contains only those fakes, so results don't
depend on what happens to be installed on the machine running the tests.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "shared" / "scripts"
IS_WINDOWS = sys.platform == "win32"

# name -> (stdout, exit code). Fakes ignore their arguments.
FAKES = {
    "rg": ("ripgrep 99.0.0", 0),
    "go": ("go version go9.9 fakeos/amd64", 0),
    "python": ("Python 9.9.9", 0),          # no python3: the fallback command must be used
    "oc": ("Client Version: 4.99", 0),      # OpenShift's oc, not only-cli's
    "gitleaks": ("boom", 1),                # installed, but its version command fails
}
REQUESTED = ["rg", "go", "python", "oc", "gitleaks", "scc"]
EXPECTED = {
    "rg": ("ok", "ripgrep 99.0.0"),
    "go": ("ok", "go version go9.9 fakeos/amd64"),
    "python": ("ok", "Python 9.9.9"),
    "oc": ("conflict", "Client Version: 4.99"),
    "gitleaks": ("ok", "unknown"),
    "scc": ("missing", "-"),
}


def parse_sh_tools() -> list[tuple[str, ...]]:
    text = (SCRIPTS / "toolcheck.sh").read_text(encoding="utf-8")
    block = text.split("TOOLS=(", 1)[1].split("\n)", 1)[0]
    return [tuple(m.group(1).split("|")) for m in re.finditer(r'^\s*"([^"]*)"', block, re.MULTILINE)]


def parse_ps1_tools() -> list[tuple[str, ...]]:
    text = (SCRIPTS / "toolcheck.ps1").read_text(encoding="utf-8")
    block = text.split("$Tools = @(", 1)[1].split("\n)", 1)[0]
    return [tuple(re.findall(r'"([^"]*)"', m.group(1))) for m in re.finditer(r"@\((.*)\)", block)]


def test_tool_lists_match() -> None:
    sh, ps1 = parse_sh_tools(), parse_ps1_tools()
    assert len(sh) >= 20
    assert sh == ps1


def test_every_tool_is_in_the_registry() -> None:
    registry = (REPO_ROOT / "shared" / "references" / "toolchain.md").read_text(encoding="utf-8").lower()
    runtimes = {"git", "python", "node", "uv", "pipx", "go", "cargo"}
    for name, *_ in parse_sh_tools():
        if name not in runtimes:
            assert f"`{name}`" in registry or f"**{name}**" in registry, f"{name} missing from toolchain.md"


def make_fakes(directory: Path) -> None:
    for name, (out, code) in FAKES.items():
        # Shell-script fake: found by bash everywhere (Git Bash runs extensionless files with a shebang).
        path = directory / name
        path.write_text(f"#!/bin/sh\necho '{out}'\nexit {code}\n", encoding="ascii", newline="\n")
        path.chmod(0o755)
        if IS_WINDOWS:
            # PowerShell on Windows only runs files with a PATHEXT extension, so add a .cmd twin.
            body = f"@echo off\r\necho {out}\r\nexit /b {code}\r\n"
            (directory / f"{name}.cmd").write_text(body, encoding="ascii", newline="")


def find_bash() -> str | None:
    if not IS_WINDOWS:
        return shutil.which("bash")
    # On Windows use Git Bash; C:\Windows\System32\bash.exe is WSL and runs in a different filesystem.
    git = shutil.which("git")
    if not git:
        return None
    for parent in Path(git).resolve().parents:
        for candidate in (parent / "bin" / "bash.exe", parent / "usr" / "bin" / "bash.exe"):
            if candidate.is_file():
                return str(candidate)
    return None


def isolated_env(fake_dir: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k.upper() != "PATH"}
    env["PATH"] = str(fake_dir)
    return env


def check_rows(rows: list[dict[str, str]]) -> None:
    got = {r["tool"]: (r["status"], r["version"]) for r in rows}
    assert got == EXPECTED
    assert [r["tool"] for r in rows] == REQUESTED
    assert all(r["path"] == "-" for r in rows if r["status"] == "missing")
    assert all(r["path"] != "-" for r in rows if r["status"] != "missing")


BASH = find_bash()
POWERSHELLS = [p for p in ("pwsh", "powershell") if shutil.which(p)] if IS_WINDOWS else (["pwsh"] if shutil.which("pwsh") else [])


@pytest.mark.skipif(BASH is None, reason="bash not available")
def test_sh_reports_fakes(tmp_path: Path) -> None:
    make_fakes(tmp_path)
    proc = subprocess.run(
        [BASH, str(SCRIPTS / "toolcheck.sh"), "--json", *REQUESTED],
        env=isolated_env(tmp_path), capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 1, proc.stderr
    check_rows(json.loads(proc.stdout))


@pytest.mark.skipif(BASH is None, reason="bash not available")
def test_sh_all_present_exits_zero(tmp_path: Path) -> None:
    make_fakes(tmp_path)
    proc = subprocess.run([BASH, str(SCRIPTS / "toolcheck.sh"), "rg", "go"],
                          env=isolated_env(tmp_path), capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.splitlines()[0].split() == ["TOOL", "STATUS", "VERSION"]


@pytest.mark.skipif(BASH is None, reason="bash not available")
def test_sh_no_args_reports_everything_and_exits_zero(tmp_path: Path) -> None:
    make_fakes(tmp_path)
    proc = subprocess.run([BASH, str(SCRIPTS / "toolcheck.sh"), "--json"],
                          env=isolated_env(tmp_path), capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0, proc.stderr
    assert [r["tool"] for r in json.loads(proc.stdout)] == [t[0] for t in parse_sh_tools()]


@pytest.mark.skipif(BASH is None, reason="bash not available")
@pytest.mark.parametrize("args", [["nope"], ["--bogus"]])
def test_sh_bad_input_exits_two(tmp_path: Path, args: list[str]) -> None:
    proc = subprocess.run([BASH, str(SCRIPTS / "toolcheck.sh"), *args],
                          env=isolated_env(tmp_path), capture_output=True, text=True, timeout=60)
    assert proc.returncode == 2


@pytest.mark.skipif(not POWERSHELLS, reason="PowerShell not available")
@pytest.mark.parametrize("shell", POWERSHELLS)
def test_ps1_reports_fakes(tmp_path: Path, shell: str) -> None:
    make_fakes(tmp_path)
    exe = shutil.which(shell)
    proc = subprocess.run(
        [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPTS / "toolcheck.ps1"), *REQUESTED, "-Json"],
        env=isolated_env(tmp_path), capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 1, proc.stderr
    check_rows(json.loads(proc.stdout))


@pytest.mark.skipif(not POWERSHELLS, reason="PowerShell not available")
@pytest.mark.parametrize("shell", POWERSHELLS)
def test_ps1_unknown_tool_exits_two(tmp_path: Path, shell: str) -> None:
    exe = shutil.which(shell)
    proc = subprocess.run(
        [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPTS / "toolcheck.ps1"), "nope"],
        env=isolated_env(tmp_path), capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 2
