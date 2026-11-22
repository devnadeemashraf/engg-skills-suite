#!/usr/bin/env python3
"""Score a deep-audit run against an answer key.

Usage:
    python evals/score.py --findings <run-dir>/findings --expected evals/expected/<fixture>.yaml [--clean]

Messy fixtures: reports recall (defects found / defects planted), under-rated severities, and extra findings.
Clean fixtures (--clean): reports every finding; any P0 or P1 is a false alarm.
Exit 0 when the release gate passes: recall >= 0.9 and no under-rated P0 defects (messy), or zero P0/P1 (clean).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

RANK = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def load_findings(directory: Path) -> list[dict]:
    findings = []
    for path in sorted(directory.glob("*.yaml")):
        findings += yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return findings


def file_of(location: str) -> str:
    return location.split(":", 1)[0]


def matches(finding: dict, defect: dict) -> bool:
    text = f"{finding.get('title', '')} {finding.get('evidence', '')}".lower()
    return (file_of(str(finding.get("location", ""))) in defect["files"]
            and finding.get("action") in defect["actions"]
            and any(k.lower() in text for k in defect["keywords"]))


def score(findings: list[dict], defects: list[dict]) -> tuple[dict[str, dict], list[dict]]:
    """Greedy one-to-one matching, most specific defects first (fewest candidate findings)."""
    candidates = {d["id"]: [i for i, f in enumerate(findings) if matches(f, d)] for d in defects}
    used: set[int] = set()
    matched: dict[str, dict] = {}
    for d in sorted(defects, key=lambda d: len(candidates[d["id"]])):
        free = [i for i in candidates[d["id"]] if i not in used]
        if free:
            best = min(free, key=lambda i: RANK.get(findings[i].get("severity"), 9))
            used.add(best)
            matched[d["id"]] = findings[best]
    extras = [f for i, f in enumerate(findings) if i not in used]
    return matched, extras


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--findings", required=True)
    ap.add_argument("--expected", required=True)
    ap.add_argument("--clean", action="store_true")
    a = ap.parse_args(argv)
    findings = load_findings(Path(a.findings))

    if a.clean:
        alarms = [f for f in findings if f.get("severity") in ("P0", "P1")]
        print(f"clean fixture: {len(findings)} findings, {len(alarms)} P0/P1 false alarms")
        for f in findings:
            print(f"  {f.get('severity')} {f.get('action'):<8} {f.get('location')}: {f.get('title')}")
        return 0 if not alarms else 1

    defects = yaml.safe_load(Path(a.expected).read_text(encoding="utf-8"))["defects"]
    matched, extras = score(findings, defects)
    under = [d for d in defects if d["id"] in matched
             and RANK.get(matched[d["id"]].get("severity"), 9) > RANK[d["max_severity"]]]
    recall = len(matched) / len(defects)
    print(f"recall: {len(matched)}/{len(defects)} = {recall:.0%}")
    for d in defects:
        f = matched.get(d["id"])
        mark = "FOUND " if f else "MISSED"
        sev = f" as {f['severity']} {f['id']}" if f else ""
        flag = "  (under-rated: expected " + d["max_severity"] + " or worse)" if d in under else ""
        print(f"  {mark} {d['id']} [{d['max_severity']}] {d['what']}{sev}{flag}")
    print(f"extra findings (not in the answer key): {len(extras)}")
    for f in extras:
        print(f"  {f.get('severity')} {f.get('action'):<8} {f.get('location')}: {f.get('title')}")
    p0_under = [d for d in under if d["max_severity"] == "P0"]
    return 0 if recall >= 0.9 and not p0_under else 1


if __name__ == "__main__":
    sys.exit(main())
