#!/usr/bin/env python3
"""Prepare an eval fixture for a deep-audit run: copy it, strip the answer comments, make it a git repo.

Usage:
    python evals/prepare.py evals/fixtures/<fixture> <target-dir>

Lines containing "DEFECT" are removed so the auditor can't read the answers. The target becomes a git
repository with one commit, because the audit's recipes read `git ls-files` and history.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    src, dst = Path(argv[1]).resolve(), Path(argv[2]).resolve()
    if dst.exists():
        print(f"prepare: {dst} already exists; choose an empty target")
        return 1
    shutil.copytree(src, dst)
    for path in dst.rglob("*"):
        if path.is_file() and path.suffix in {".ts", ".tsx", ".js", ".py", ".go"}:
            lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
            path.write_text("".join(l for l in lines if "DEFECT" not in l), encoding="utf-8", newline="")
    git = ["git", "-c", "user.name=eval", "-c", "user.email=eval@example.test", "-c", "core.autocrlf=false"]
    for cmd in (git + ["init", "-q"], git + ["add", "-A"], git + ["commit", "-q", "-m", "fixture"]):
        subprocess.run(cmd, cwd=dst, check=True)
    print(f"prepared {src.name} -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
