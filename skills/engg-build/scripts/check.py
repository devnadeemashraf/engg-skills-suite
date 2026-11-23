#!/usr/bin/env python3
"""Run the project's gates with compact output: one line per passing stage, only the tail of a failing one.

Usage (from the repo root):
    check.py                  run every stage in .engg/check.toml, stopping at the first failure
    check.py lint test        run only the named stages
    check.py --keep-going     run every stage even after a failure
    check.py --tail 80        lines of a failing stage's output to show (default 60)
    check.py --list           print the stages and their commands

.engg/check.toml holds one [[stage]] table per gate, fastest first:

    [[stage]]
    name = "lint"
    run = "npm run lint"
    timeout = 600   # seconds, optional (default 1800)

Exit code: 0 when every stage run passed, 1 when any failed, 2 for a configuration error.
Requires Python 3.10+ only (uses tomllib on 3.11+, and a parser for the format above on 3.10).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from pathlib import Path

CONFIG = ".engg/check.toml"
DEFAULT_TIMEOUT = 1800


class ConfigError(Exception):
    pass


def parse_minimal(text: str) -> dict[str, list[dict[str, object]]]:
    """Parse the [[stage]] subset of TOML: string and integer values, comments, blank lines."""
    stages: list[dict[str, object]] = []
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[[stage]]":
            stages.append({})
            continue
        match = re.match(r'^(\w+)\s*=\s*("(?:[^"\\]|\\.)*"|\'[^\']*\'|-?\d+)\s*(?:#.*)?$', line)
        if not match or not stages:
            raise ConfigError(f"{CONFIG}:{number}: can't read `{line}` (expected [[stage]] tables with key = value)")
        key, value = match.groups()
        if value[0] == '"':
            stages[-1][key] = bytes(value[1:-1], "utf-8").decode("unicode_escape")
        elif value[0] == "'":
            stages[-1][key] = value[1:-1]
        else:
            stages[-1][key] = int(value)
    return {"stage": stages}


def load_stages(root: Path) -> list[dict[str, object]]:
    path = root / CONFIG
    if not path.is_file():
        raise ConfigError(f"no {CONFIG}: add one [[stage]] per gate (see references/working-loop.md §4)")
    text = path.read_text(encoding="utf-8")
    try:
        import tomllib
    except ModuleNotFoundError:
        data = parse_minimal(text)
    else:
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(f"{CONFIG}: {exc}") from exc
    stages = data.get("stage")
    if not isinstance(stages, list) or not stages:
        raise ConfigError(f"{CONFIG} has no [[stage]] tables")
    for i, stage in enumerate(stages, 1):
        if not isinstance(stage.get("name"), str) or not isinstance(stage.get("run"), str):
            raise ConfigError(f"{CONFIG}: stage {i} needs a string `name` and `run`")
        if "timeout" in stage and not isinstance(stage["timeout"], int):
            raise ConfigError(f"{CONFIG}: stage {stage['name']}: `timeout` must be whole seconds")
    return stages


def run_stage(root: Path, stage: dict[str, object], tail: int) -> bool:
    name, command = str(stage["name"]), str(stage["run"])
    timeout = int(stage.get("timeout", DEFAULT_TIMEOUT))  # type: ignore[arg-type]
    start = time.monotonic()
    try:
        result = subprocess.run(
            command, shell=True, cwd=root, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired:
        print(f"FAIL {name}: timed out after {timeout}s: {command}")
        return False
    seconds = time.monotonic() - start
    if result.returncode == 0:
        print(f"ok   {name} ({seconds:.1f}s)")
        return True
    output = (result.stdout + result.stderr).rstrip().splitlines()
    print(f"FAIL {name} (exit {result.returncode}, {seconds:.1f}s): {command}")
    if len(output) > tail:
        print(f"... {len(output) - tail} earlier lines omitted ...")
    print("\n".join(output[-tail:]))
    return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("names", nargs="*", help="run only these stages")
    parser.add_argument("--keep-going", action="store_true")
    parser.add_argument("--tail", type=int, default=60)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    root = Path(args.root)
    try:
        stages = load_stages(root)
    except ConfigError as exc:
        print(f"check.py: {exc}")
        return 2
    if args.list:
        for stage in stages:
            print(f"{stage['name']}: {stage['run']}")
        return 0
    if args.names:
        known = {str(s["name"]) for s in stages}
        unknown = [n for n in args.names if n not in known]
        if unknown:
            print(f"check.py: unknown stage(s): {', '.join(unknown)} (have: {', '.join(sorted(known))})")
            return 2
        stages = [s for s in stages if s["name"] in args.names]
    failed = 0
    for stage in stages:
        if not run_stage(root, stage, args.tail):
            failed += 1
            if not args.keep_going:
                break
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
