#!/usr/bin/env python3
"""Disk-backed ledger for a deep audit: one unit at a time, resumable after any interruption.

Usage (all commands take --run-dir .engg/audit/<run-id>):
    ledger.py init                      create ledger.jsonl from map.json (refuses to overwrite)
    ledger.py next                      print the context pack for the next unit and mark it in_progress
    ledger.py done --unit U001 --summary "..."
                                        validate findings/U001.yaml, then mark the unit done
    ledger.py status                    progress per layer
    ledger.py summaries --layer domain  summaries of finished units in one layer (for layer synthesis)
    ledger.py skip --unit U040 --reason "..."
                                        record that a unit is deliberately not reviewed, and why
    ledger.py report                    aggregate every finding into report-data.md

Findings files follow references/finding-schema.md. Requires Python 3.10+ and PyYAML.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - exercised manually
    sys.exit("ledger: PyYAML is required (ask before installing it).")

SEVERITIES = ("P0", "P1", "P2", "P3")
ACTIONS = ("STRIP", "MOVE", "SPLIT", "MERGE", "HARDEN", "TEST", "SIMPLIFY")
PILLARS = ("correctness", "security", "performance", "reliability", "architecture", "testability", "simplicity")
REQUIRED = ("id", "title", "severity", "action", "pillar", "location", "evidence", "source", "fix")
OPTIONAL = ("triage", "test", "related")
TRIAGE_RE = re.compile(r"^(TRUE|NEEDS-HUMAN|FALSE-POSITIVE: .+)$")
LOCATION_RE = re.compile(r"^[^\s:]+(:\d+(-\d+)?)?$")
SOURCE_RE = re.compile(r"^(review|tool:[a-z0-9][a-z0-9._-]*)$")
SUMMARY_MAX = 600


# --------------------------------------------------------------------------- storage


def load(run_dir: Path) -> list[dict]:
    path = run_dir / "ledger.jsonl"
    if not path.is_file():
        raise SystemExit("ledger: no ledger.jsonl; run `ledger.py init` first")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def save(run_dir: Path, units: list[dict]) -> None:
    """Atomic replace, so an interrupted write never corrupts the ledger."""
    fd, tmp = tempfile.mkstemp(dir=run_dir, prefix=".ledger-", suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        for u in units:
            fh.write(json.dumps(u, sort_keys=True) + "\n")
    os.replace(tmp, run_dir / "ledger.jsonl")


def load_map(run_dir: Path) -> dict:
    path = run_dir / "map.json"
    if not path.is_file():
        raise SystemExit("ledger: no map.json; run build_map.py first")
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- validation


def validate_findings(path: Path, unit: dict) -> tuple[list[dict], list[str]]:
    if not path.is_file():
        return [], [f"missing {path.as_posix()} (write `[]` if the unit is clean, and say why in the summary)"]
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return [], [f"{path.name}: not valid YAML: {exc}"]
    if data is None:
        data = []
    if not isinstance(data, list):
        return [], [f"{path.name}: must be a YAML list of findings (or [])"]
    errors: list[str] = []
    ids = set()
    for i, f in enumerate(data):
        where = f"{path.name}[{i}]"
        if not isinstance(f, dict):
            errors.append(f"{where}: must be a mapping")
            continue
        for key in REQUIRED:
            if not str(f.get(key, "")).strip():
                errors.append(f"{where}: missing '{key}'")
        for key in sorted(set(f) - set(REQUIRED) - set(OPTIONAL)):
            errors.append(f"{where}: unknown field '{key}'")
        fid = str(f.get("id", ""))
        if fid and not fid.startswith(unit["id"] + "-"):
            errors.append(f"{where}: id '{fid}' must start with '{unit['id']}-'")
        if fid in ids:
            errors.append(f"{where}: duplicate id '{fid}'")
        ids.add(fid)
        if f.get("severity") not in SEVERITIES:
            errors.append(f"{where}: severity must be one of {SEVERITIES}")
        if f.get("action") not in ACTIONS:
            errors.append(f"{where}: action must be one of {ACTIONS}")
        if f.get("pillar") not in PILLARS:
            errors.append(f"{where}: pillar must be one of {PILLARS}")
        loc = str(f.get("location", ""))
        if loc and not LOCATION_RE.match(loc):
            errors.append(f"{where}: location must be 'path' or 'path:line' or 'path:start-end'")
        src = str(f.get("source", ""))
        if src and not SOURCE_RE.match(src):
            errors.append(f"{where}: source must be 'review' or 'tool:<name>'")
        if f.get("triage") is True:  # YAML reads an unquoted TRUE as a boolean
            f["triage"] = "TRUE"
        if src.startswith("tool:") and not TRIAGE_RE.match(str(f.get("triage", ""))):
            errors.append(f"{where}: tool findings need triage: TRUE | NEEDS-HUMAN | 'FALSE-POSITIVE: <reason>'")
        if f.get("severity") in ("P0", "P1") and not str(f.get("test", "")).strip():
            errors.append(f"{where}: P0/P1 findings need a 'test' that proves the fix")
    return data, errors


# --------------------------------------------------------------------------- commands


def cmd_init(run_dir: Path, force: bool) -> int:
    if (run_dir / "ledger.jsonl").exists() and not force:
        print("ledger: ledger.jsonl already exists; resume with `ledger.py next` (or pass --force to restart)")
        return 1
    m = load_map(run_dir)
    units = [{"id": u["id"], "layer": u["layer"], "module": u["module"], "files": u["files"], "loc": u["loc"],
              "risk": u["risk"], "status": "pending", "summary": "", "counts": {}} for u in m["units"]]
    (run_dir / "findings").mkdir(exist_ok=True)
    save(run_dir, units)
    print(f"ledger: {len(units)} units ready. Next: ledger.py next --run-dir {run_dir.as_posix()}")
    return 0


def context_pack(unit: dict, m: dict) -> str:
    files = m["files"]
    layer = next((l for l in m["layers"] if l["name"] == unit["layer"]), None)
    members = set(unit["files"])
    lines = [
        f"# Unit {unit['id']}: layer `{unit['layer']}`, module `{unit['module']}` ({unit['loc']} lines)",
        "",
        f"May import: {', '.join(layer['may_import']) or 'nothing'} (and its own layer)." if layer
        else "This code belongs to NO layer in the contract: decide whether it should move, or be deleted.",
        "",
        "## Files (read only these)",
    ]
    for f in unit["files"]:
        x = files[f]
        lines.append(f"- `{f}`: {x['loc']} lines, max CCN {x['max_ccn'] if x['max_ccn'] is not None else '-'}, "
                     f"churn {x['churn']}, fan-in {x['fan_in'] if x['fan_in'] is not None else '-'}"
                     + (", OVER FILE LIMIT" if x["over_file_limit"] else ""))
        for fn in x["functions_over_limit"]:
            lines.append(f"  - over limit: `{fn['name']}` at line {fn['line']}: CCN {fn['ccn']}, {fn['nloc']} lines")
    tool = [t for f in unit["files"] for t in files[f]["tool_findings"]]
    lines += ["", "## Tool findings to triage (TRUE / FALSE-POSITIVE: reason / NEEDS-HUMAN)"]
    lines += [f"- [{t['tool']}] {t['rule']} at `{t['file']}`{':' + str(t['line']) if t['line'] else ''}: {t['detail']}" for t in tool] or ["- none"]
    dups = [c for c in m["duplicates"] if c["a"]["file"] in members or c["b"]["file"] in members]
    lines += ["", "## Duplicated code involving this unit"]
    lines += [f"- {c['lines']} lines: `{c['a']['file']}:{c['a']['start']}` ≈ `{c['b']['file']}:{c['b']['start']}`" for c in dups] or ["- none"]
    cyc = [c for c in m["cycles"] if members & set(c)]
    lines += ["", "## Import cycles touching this unit"]
    lines += [f"- {' -> '.join(c)} -> {c[0]}" for c in cyc] or ["- none"]
    dead = [f for f in m["dead_file_candidates"] if f in members]
    syms = [s for s in m["unreferenced_symbols"] if s["file"] in members]
    lines += ["", "## Dead-code candidates (confirm strings, reflection, config before STRIP)"]
    lines += [f"- whole file `{f}`: nothing references it" for f in dead]
    lines += [f"- `{s['symbol']}` in `{s['file']}` {s['line'] or ''}" for s in syms]
    if not dead and not syms:
        lines.append("- none")
    lines += ["", "## Write",
              f"- findings to `findings/{unit['id']}.yaml` (schema: references/finding-schema.md); `[]` if clean",
              f"- then: ledger.py done --unit {unit['id']} --summary \"<5 lines max: what this unit is, what's wrong, what's solid>\""]
    return "\n".join(lines)


def cmd_next(run_dir: Path) -> int:
    units = load(run_dir)
    unit = next((u for u in units if u["status"] == "in_progress"), None) or next((u for u in units if u["status"] == "pending"), None)
    if unit is None:
        print("ledger: every unit is done. Next: layer synthesis (ledger.py summaries --layer <name>), then ledger.py report")
        return 0
    if unit["status"] == "pending":
        unit["status"] = "in_progress"
        save(run_dir, units)
    print(context_pack(unit, load_map(run_dir)))
    return 0


def cmd_done(run_dir: Path, unit_id: str, summary: str) -> int:
    units = load(run_dir)
    unit = next((u for u in units if u["id"] == unit_id), None)
    if unit is None:
        print(f"ledger: unknown unit {unit_id}")
        return 2
    if not summary.strip():
        print("ledger: --summary is required")
        return 2
    if len(summary) > SUMMARY_MAX:
        print(f"ledger: summary is {len(summary)} chars; keep it under {SUMMARY_MAX} (detail belongs in findings)")
        return 2
    findings, errors = validate_findings(run_dir / "findings" / f"{unit_id}.yaml", unit)
    if errors:
        print("ledger: findings rejected, fix and rerun:")
        for e in errors:
            print(f"  - {e}")
        return 1
    unit["status"] = "done"
    unit["summary"] = summary.strip()
    unit["counts"] = dict(Counter(f["severity"] for f in findings))
    save(run_dir, units)
    left = sum(1 for u in units if u["status"] != "done")
    print(f"ledger: {unit_id} done ({len(findings)} findings). {left} unit(s) left.")
    return 0


def cmd_skip(run_dir: Path, unit_id: str, reason: str) -> int:
    """Record a deliberate decision not to review a unit. A skipped unit is never reported as reviewed."""
    units = load(run_dir)
    unit = next((u for u in units if u["id"] == unit_id), None)
    if unit is None:
        print(f"ledger: unknown unit {unit_id}")
        return 2
    if unit["status"] == "done":
        print(f"ledger: {unit_id} is already reviewed; it can't be skipped")
        return 1
    if len(reason.strip()) < 10:
        print("ledger: --reason is required: say why this unit is not reviewed (at least 10 characters)")
        return 2
    if len(reason) > SUMMARY_MAX:
        print(f"ledger: reason is {len(reason)} chars; keep it under {SUMMARY_MAX}")
        return 2
    unit["status"] = "skipped"
    unit["summary"] = reason.strip()
    save(run_dir, units)
    print(f"ledger: {unit_id} skipped ({reason.strip()[:60]})")
    return 0


def cmd_status(run_dir: Path) -> int:
    units = load(run_dir)
    by_layer: dict[str, list[dict]] = defaultdict(list)
    for u in units:
        by_layer[u["layer"]].append(u)
    print(f"{'LAYER':<16} {'DONE':>5} {'SKIP':>5} {'TOTAL':>6}  P0  P1  P2  P3")
    for layer, us in by_layer.items():
        sev = Counter()
        for u in us:
            sev.update(u["counts"])
        print(f"{layer:<16} {sum(u['status'] == 'done' for u in us):>5} {sum(u['status'] == 'skipped' for u in us):>5} {len(us):>6}  "
              + "  ".join(f"{sev.get(s, 0):>2}" for s in SEVERITIES))
    return 0


def cmd_summaries(run_dir: Path, layer: str) -> int:
    for u in load(run_dir):
        if u["layer"] == layer and u["status"] == "done":
            print(f"## {u['id']} ({u['module']}): {u['counts'] or 'clean'}\n{u['summary']}\n")
    return 0


def cmd_report(run_dir: Path) -> int:
    units = load(run_dir)
    pending = [u["id"] for u in units if u["status"] in ("pending", "in_progress")]
    skipped = [u for u in units if u["status"] == "skipped"]
    all_findings: list[dict] = []
    for u in units:
        path = run_dir / "findings" / f"{u['id']}.yaml"
        if path.is_file():
            all_findings += [dict(f, unit=u["id"], layer=u["layer"]) for f in (yaml.safe_load(path.read_text(encoding="utf-8")) or [])]
    # Layer-synthesis findings (cross-unit patterns) live in findings/S-<layer>.yaml with ids S-<layer>-NN.
    for path in sorted((run_dir / "findings").glob("S-*.yaml")):
        found, errors = validate_findings(path, {"id": path.stem})
        if errors:
            print(f"ledger: {path.name} rejected, fix and rerun:")
            for e in errors:
                print(f"  - {e}")
            return 1
        all_findings += [dict(f, unit=path.stem, layer=path.stem[2:]) for f in found]
    m = load_map(run_dir)
    sev = Counter(f["severity"] for f in all_findings)
    out = ["# Report Data (generated by ledger.py report; the narrative REPORT.md builds on this)", ""]
    if pending:
        out += [f"**INCOMPLETE:** units not done: {', '.join(pending)}. Do not present this as a full audit.", ""]
    if skipped:
        out += [f"**PARTIAL:** {len(skipped)} unit(s) deliberately not reviewed (listed below). Say so in the report.", ""]
    not_run = [k for k, v in m["inputs"].items() if v == "not run"]
    out += ["## Checks not run", "", (", ".join(not_run) or "none") + "", ""]
    if skipped:
        out += ["## Units not reviewed (skipped on purpose)", ""]
        out += [f"- **{u['id']}** `{u['layer']}` ({u['loc']} lines): {u['summary']}" for u in skipped] + [""]
    out += ["## Findings by severity", "", "| P0 | P1 | P2 | P3 |", "|---|---|---|---|",
            "| " + " | ".join(str(sev.get(s, 0)) for s in SEVERITIES) + " |", ""]
    order = {s: i for i, s in enumerate(SEVERITIES)}
    for title, actions in (("Strip list", {"STRIP"}), ("Move / reorganise list", {"MOVE", "SPLIT", "MERGE"})):
        rows = sorted((f for f in all_findings if f["action"] in actions), key=lambda f: (order[f["severity"]], f["id"]))
        out += [f"## {title}", ""] + ([f"- **{f['id']}** {f['severity']} `{f['location']}`: {f['title']}" for f in rows] or ["- none"]) + [""]
    out += ["## All findings, by severity", "", "| ID | Sev | Action | Pillar | Location | Title |", "|---|---|---|---|---|---|"]
    for f in sorted(all_findings, key=lambda f: (order[f["severity"]], f["id"])):
        out.append(f"| {f['id']} | {f['severity']} | {f['action']} | {f['pillar']} | `{f['location']}` | {f['title']} |")
    (run_dir / "report-data.md").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    flag = " (INCOMPLETE)" if pending else (" (PARTIAL)" if skipped else "")
    print(f"ledger: {len(all_findings)} findings -> {run_dir.as_posix()}/report-data.md" + flag)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["init", "next", "done", "skip", "status", "summaries", "report"])
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--unit")
    ap.add_argument("--summary", default="")
    ap.add_argument("--reason", default="")
    ap.add_argument("--layer")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args(argv)
    run_dir = Path(a.run_dir)
    if a.command == "init":
        return cmd_init(run_dir, a.force)
    if a.command == "next":
        return cmd_next(run_dir)
    if a.command == "done":
        if not a.unit:
            print("ledger: done needs --unit")
            return 2
        return cmd_done(run_dir, a.unit, a.summary)
    if a.command == "skip":
        if not a.unit:
            print("ledger: skip needs --unit")
            return 2
        return cmd_skip(run_dir, a.unit, a.reason)
    if a.command == "status":
        return cmd_status(run_dir)
    if a.command == "summaries":
        if not a.layer:
            print("ledger: summaries needs --layer")
            return 2
        return cmd_summaries(run_dir, a.layer)
    return cmd_report(run_dir)


if __name__ == "__main__":
    sys.exit(main())
