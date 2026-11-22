#!/usr/bin/env python3
"""Ratchet: record today's violations as a baseline, fail on any new one, let the baseline only shrink.

Usage:
    ratchet.py record --baseline .engg/baseline/violations.json [sources]   create the baseline (refuses to overwrite)
    ratchet.py check  --baseline .engg/baseline/violations.json [sources]   exit 1 on any violation not in the baseline
    ratchet.py update --baseline .engg/baseline/violations.json [sources]   shrink the baseline to what remains (never grows)

    check --require-tight   also fail when violations were fixed but the baseline wasn't shrunk. Use it in CI,
                            so every fix lands together with its smaller baseline and progress can't slip back.

Sources (give at least one; each is a tool's output file):
    --depcruise FILE       dependency-cruiser --output-type json
    --import-linter FILE   lint-imports text output
    --gitleaks FILE        gitleaks --report-format json (always run with --redact)
    --sarif FILE           any SARIF 2.1 file (repeatable)

Violations are keyed without line numbers ("tool:rule:file[->target]"), so unrelated edits that shift
lines don't look like new violations. Counts are kept per key: a second copy of an existing violation is new.
Requires Python 3.10+ only (no third-party packages).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

BASELINE_VERSION = 1


def norm(path: str) -> str:
    path = path.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path


def from_depcruise(path: Path) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [f"dependency-cruiser:{v['rule']['name']}:{norm(v['from'])}->{norm(v['to'])}"
            for v in data.get("summary", {}).get("violations", [])]


def from_import_linter(path: Path) -> list[str]:
    """Parse 'lint-imports' text: a '<name> BROKEN' contract line, then '- a -> b (l.N)' import lines."""
    keys, contract = [], None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.endswith(" BROKEN"):
            contract = stripped[: -len(" BROKEN")]
            continue
        if stripped.endswith(" KEPT"):
            contract = None
            continue
        m = re.match(r"^-\s+([\w.]+)\s+->\s+([\w.]+)", stripped)
        if m and contract:
            keys.append(f"import-linter:{contract}:{m.group(1)}->{m.group(2)}")
    return keys


def from_gitleaks(path: Path) -> list[str]:
    return [f"gitleaks:{leak.get('RuleID')}:{norm(leak.get('File', ''))}"
            for leak in json.loads(path.read_text(encoding="utf-8") or "[]")]


def from_sarif(path: Path) -> list[str]:
    keys = []
    for run in json.loads(path.read_text(encoding="utf-8")).get("runs", []):
        tool = run.get("tool", {}).get("driver", {}).get("name", path.stem)
        for res in run.get("results", []):
            uri = ""
            for loc in res.get("locations", [])[:1]:
                uri = loc.get("physicalLocation", {}).get("artifactLocation", {}).get("uri", "")
            keys.append(f"{tool}:{res.get('ruleId')}:{norm(uri)}")
    return keys


def collect(args: argparse.Namespace) -> Counter[str]:
    keys: list[str] = []
    if args.depcruise:
        keys += from_depcruise(Path(args.depcruise))
    if args.import_linter:
        keys += from_import_linter(Path(args.import_linter))
    if args.gitleaks:
        keys += from_gitleaks(Path(args.gitleaks))
    for sarif in args.sarif or []:
        keys += from_sarif(Path(sarif))
    return Counter(keys)


def sources_used(args: argparse.Namespace) -> list[str]:
    used = [name for name, val in (("dependency-cruiser", args.depcruise), ("import-linter", args.import_linter),
                                   ("gitleaks", args.gitleaks)) if val]
    return used + [f"sarif:{Path(s).name}" for s in args.sarif or []]


def load_baseline(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("version") != BASELINE_VERSION:
        raise SystemExit(f"ratchet: {path} has unsupported version {data.get('version')!r}")
    return data


def write_baseline(path: Path, counts: Counter[str], sources: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "version": BASELINE_VERSION,
        "note": "Known violations. CI fails on any violation not listed here. This file may only shrink "
                "(ratchet.py update); never add entries by hand to get a change through.",
        "sources": sources,
        "total": sum(counts.values()),
        "violations": dict(sorted(counts.items())),
    }
    path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8", newline="\n")


def diff(baseline: Counter[str], current: Counter[str]) -> tuple[Counter[str], Counter[str]]:
    """(new violations, fixed violations), counting multiplicity."""
    return current - baseline, baseline - current


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["record", "check", "update"])
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--depcruise")
    ap.add_argument("--import-linter")
    ap.add_argument("--gitleaks")
    ap.add_argument("--sarif", action="append")
    ap.add_argument("--require-tight", action="store_true")
    a = ap.parse_args(argv)

    if not sources_used(a):
        print("ratchet: give at least one source (--depcruise, --import-linter, --gitleaks, --sarif)")
        return 2
    baseline_path = Path(a.baseline)
    current = collect(a)

    if a.command == "record":
        if baseline_path.exists():
            print(f"ratchet: {baseline_path} already exists; use `check`, or `update` to shrink it")
            return 1
        write_baseline(baseline_path, current, sources_used(a))
        print(f"ratchet: recorded {sum(current.values())} known violation(s) in {baseline_path.as_posix()}")
        return 0

    if not baseline_path.is_file():
        print(f"ratchet: no baseline at {baseline_path}; run `record` first")
        return 2
    base = load_baseline(baseline_path)
    known = Counter(base["violations"])
    missing_sources = sorted(set(base["sources"]) - set(sources_used(a)))
    if missing_sources:
        # Dropping a source would make its violations look "fixed" and shrink the baseline dishonestly.
        print(f"ratchet: the baseline was recorded with {missing_sources}; pass the same sources")
        return 2
    new, fixed = diff(known, current)

    if a.command == "check":
        for key, n in sorted(new.items()):
            print(f"NEW     {key}" + (f" (x{n})" if n > 1 else ""))
        for key, n in sorted(fixed.items()):
            print(f"FIXED   {key}" + (f" (x{n})" if n > 1 else ""))
        print(f"ratchet: {sum(current.values())} current, {sum(known.values())} in baseline, "
              f"{sum(new.values())} new, {sum(fixed.values())} fixed")
        if new:
            print("ratchet: FAIL. Fix the new violations; never add them to the baseline.")
            return 1
        if fixed and a.require_tight:
            print("ratchet: FAIL (--require-tight). Violations were fixed but the baseline wasn't shrunk: "
                  "run `ratchet.py update` and commit it with the fix.")
            return 1
        if fixed:
            print("ratchet: pass. The baseline can shrink: run `ratchet.py update` and commit it.")
        return 0

    # update: shrink only
    if new:
        print(f"ratchet: refusing to update: {sum(new.values())} violation(s) are not in the baseline. "
              "The baseline only shrinks.")
        for key in sorted(new):
            print(f"NEW     {key}")
        return 1
    write_baseline(baseline_path, current, base["sources"])
    print(f"ratchet: baseline shrank from {sum(known.values())} to {sum(current.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
