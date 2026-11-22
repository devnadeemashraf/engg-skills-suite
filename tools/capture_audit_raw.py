#!/usr/bin/env python3
"""Regenerate the recorded raw tool outputs that test the deep audit's map step.

Usage:
    python tools/capture_audit_raw.py evals/fixtures/ts-messy-api tests/fixtures/deep-audit-raw/ts-messy-api

Copies the fixture into a throwaway git repo, runs each installed tool exactly as
skills/engg-deep-audit/references/tool-recipes.md says, and writes the outputs to the destination.
Machine-specific metadata (absolute paths, environment) is stripped so nothing private is committed.
Tools that aren't installed are skipped and listed. Needs git, plus whichever of scc, lizard, jscpd,
gitleaks, graphify and dependency-cruiser you want captured.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
NODE_BIN = REPO_ROOT / "node_modules" / ".bin"
PY_BIN = Path(sys.executable).parent


def which(name: str) -> str | None:
    return (shutil.which(name, path=str(NODE_BIN)) or shutil.which(name, path=str(PY_BIN))
            or shutil.which(name) or shutil.which(name, path=str(Path.home() / "go" / "bin")))


def run(cmd: list[str], cwd: Path, stdout: Path | None = None) -> int:
    with (stdout.open("w", encoding="utf-8", newline="\n") if stdout else open(Path(cwd) / ".capture.log", "a")) as out:
        return subprocess.run(cmd, cwd=cwd, stdout=out, stderr=subprocess.DEVNULL, timeout=600).returncode


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    fixture, dest = Path(argv[1]).resolve(), Path(argv[2]).resolve()
    skipped = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp) / "repo"
        shutil.copytree(fixture, repo)
        git = ["git", "-c", "user.name=eval", "-c", "user.email=eval@example.test", "-c", "core.autocrlf=false"]
        for cmd in (["git", "init", "-q"], ["git", "add", "-A"], git + ["commit", "-q", "-m", "fixture"]):
            subprocess.run(cmd, cwd=repo, check=True)
        raw = repo / "raw-out"
        raw.mkdir()
        run(["git", "ls-files"], repo, raw / "files.txt")
        run(["git", "log", "--since=12.months", "--numstat", "--format="], repo, raw / "churn.txt")

        if (scc := which("scc")):
            run([scc, "--by-file", "--format", "json", "-o", str(raw / "scc.json"), "src"], repo)
        else:
            skipped.append("scc")
        if (lizard := which("lizard")):
            run([lizard, "--csv", "src"], repo, raw / "lizard.csv")
        else:
            skipped.append("lizard")
        if (jscpd := which("jscpd")):
            run([jscpd, "--reporters", "json", "--output", str(raw / "jscpd"), "--silent", "src"], repo)
        else:
            skipped.append("jscpd")
        if (gitleaks := which("gitleaks")):
            run([gitleaks, "git", ".", "--redact", "--report-format", "json", "--report-path", str(raw / "gitleaks.json"), "--no-banner"], repo)
        else:
            skipped.append("gitleaks")
        if (graphify := which("graphify")):
            run([graphify, "update", "."], repo)
            for name in ("graph.json", "GRAPH_REPORT.md"):
                if (repo / "graphify-out" / name).is_file():
                    shutil.copy(repo / "graphify-out" / name, raw / name)
        else:
            skipped.append("graphify")
        depcruise = which("depcruise")
        if depcruise and (repo / ".engg/architecture.yaml").is_file():
            run([sys.executable, str(REPO_ROOT / "shared/scripts/compile_contract.py")], repo)
            run([depcruise, "--config", ".engg/generated/dependency-cruiser.cjs", "--output-type", "json", "src"], repo, raw / "depcruise.json")
            data = json.loads((raw / "depcruise.json").read_text(encoding="utf-8"))
            # Keep only what build_map reads; optionsUsed/environment hold absolute local paths.
            slim = {"summary": {"violations": data["summary"]["violations"]}}
            (raw / "depcruise.json").write_text(json.dumps(slim, indent=2) + "\n", encoding="utf-8", newline="\n")
        else:
            skipped.append("dependency-cruiser")

        report = raw / "GRAPH_REPORT.md"
        if report.is_file():  # the report's title line names the temp folder
            lines = report.read_text(encoding="utf-8").splitlines()
            report.write_text("\n".join(["# Graph Report - fixture"] + lines[1:]) + "\n", encoding="utf-8", newline="\n")

        leaked = [str(p) for p in raw.rglob("*") if p.is_file() and tmp.replace("\\", "/").lower()[:20] in
                  p.read_text(encoding="utf-8", errors="replace").replace("\\\\", "/").replace("\\", "/").lower()]
        if leaked:
            print(f"capture: refusing to write; local paths remain in: {leaked}")
            return 1
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(raw, dest)
    print(f"captured -> {dest}" + (f" (skipped, not installed: {', '.join(skipped)})" if skipped else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
