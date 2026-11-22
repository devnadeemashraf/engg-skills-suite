#!/usr/bin/env python3
"""Merge raw tool outputs into the deep audit's system map and unit plan.

Usage:
    python build_map.py --run-dir .engg/audit/<run-id> [--contract .engg/architecture.yaml] [--max-unit-lines 600]

Reads <run-dir>/raw/ (see references/tool-recipes.md for the commands that produce each file).
Only raw/files.txt is required; every other input is optional and its absence is recorded in the map
as "not run", so the report can say exactly what was and was not checked.

Writes <run-dir>/map.json (machine-readable) and <run-dir>/map.md (human summary).
Requires Python 3.10+ and PyYAML; imports compile_contract.py from this folder.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compile_contract as cc  # noqa: E402  (same folder; provides contract parsing and glob translation)

SOURCE_EXTENSIONS = {
    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".py", ".go", ".rs", ".java", ".kt", ".kts",
    ".cs", ".rb", ".php", ".swift", ".scala", ".c", ".h", ".cc", ".cpp", ".hpp", ".m", ".dart", ".vue", ".svelte",
}
TEST_PATTERN = re.compile(r"(^|/)(tests?|__tests__|spec)/|[._-](test|spec)\.[a-z]+$|_test\.go$|^test_.*\.py$|/test_[^/]*\.py$")
REFERENCE_RELATIONS = {"imports", "imports_from", "calls", "re_exports", "inherits", "uses", "references"}
TOOLS = {
    "files": "files.txt", "churn": "churn.txt", "scc": "scc.json", "lizard": "lizard.csv",
    "jscpd": "jscpd/jscpd-report.json", "gitleaks": "gitleaks.json", "depcruise": "depcruise.json",
    "graph": "graph.json", "graph_report": "GRAPH_REPORT.md", "osv": "osv.json", "import_linter": "import-linter.txt",
}


def norm(path: str) -> str:
    """Repo-relative, forward-slash path."""
    path = path.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path


def resolve(path: str, files: set[str]) -> str | None:
    """Map a tool-reported path onto a tracked file. Tools report paths relative to where they ran."""
    p = norm(path)
    if p in files:
        return p
    matches = [f for f in files if f.endswith("/" + p)]
    return matches[0] if len(matches) == 1 else None


# --------------------------------------------------------------------------- readers (each tolerant of absence)


def read_churn(path: Path) -> dict[str, int]:
    churn: dict[str, int] = defaultdict(int)
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            churn[norm(parts[2])] += int(parts[0]) + int(parts[1])
    return churn


def read_scc(path: Path, files: set[str]) -> dict[str, int]:
    loc = {}
    for lang in json.loads(path.read_text(encoding="utf-8")):
        for f in lang.get("Files", []):
            target = resolve(f["Location"], files)
            if target:
                loc[target] = int(f["Code"])
    return loc


def read_lizard(path: Path, files: set[str]) -> dict[str, list[dict]]:
    """lizard --csv has no header: NLOC, CCN, token, PARAM, length, location, file, function, long_name, start, end."""
    funcs: dict[str, list[dict]] = defaultdict(list)
    with path.open(encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.reader(fh):
            if len(row) < 11 or not row[0].isdigit():
                continue
            target = resolve(row[6], files)
            if target:
                funcs[target].append({"name": row[7], "nloc": int(row[0]), "ccn": int(row[1]), "line": int(row[9])})
    return funcs


def read_jscpd(path: Path, files: set[str]) -> list[dict]:
    clones = []
    for dup in json.loads(path.read_text(encoding="utf-8")).get("duplicates", []):
        a, b = resolve(dup["firstFile"]["name"], files), resolve(dup["secondFile"]["name"], files)
        if a and b:
            clones.append({"lines": int(dup.get("lines", 0)),
                           "a": {"file": a, "start": dup["firstFile"]["start"]},
                           "b": {"file": b, "start": dup["secondFile"]["start"]}})
    return clones


def read_gitleaks(path: Path, files: set[str]) -> list[dict]:
    out = []
    for leak in json.loads(path.read_text(encoding="utf-8") or "[]"):
        target = resolve(leak.get("File", ""), files)
        if target:
            # Never copy the secret itself; the raw report should already be redacted.
            out.append({"tool": "gitleaks", "file": target, "line": leak.get("StartLine"),
                        "rule": leak.get("RuleID"), "detail": f"commit {str(leak.get('Commit', ''))[:7]}".strip()})
    return out


def read_depcruise(path: Path, files: set[str]) -> tuple[list[dict], list[list[str]]]:
    findings, cycles = [], []
    for v in json.loads(path.read_text(encoding="utf-8"))["summary"].get("violations", []):
        src = resolve(v.get("from", ""), files)
        rule = v.get("rule", {}).get("name", "")
        if v.get("cycle"):
            cycle = [norm(c["name"] if isinstance(c, dict) else c) for c in v["cycle"]]
            if sorted(cycle) not in [sorted(c) for c in cycles]:
                cycles.append(cycle)
        if src:
            findings.append({"tool": "dependency-cruiser", "file": src, "line": None, "rule": rule,
                             "detail": f"{norm(v.get('from', ''))} -> {norm(v.get('to', ''))}"})
    return findings, cycles


def read_sarif(path: Path, files: set[str]) -> list[dict]:
    out = []
    data = json.loads(path.read_text(encoding="utf-8"))
    for run in data.get("runs", []):
        tool = run.get("tool", {}).get("driver", {}).get("name", path.stem)
        for res in run.get("results", []):
            for loc in res.get("locations", [])[:1]:
                phys = loc.get("physicalLocation", {})
                target = resolve(phys.get("artifactLocation", {}).get("uri", ""), files)
                if target:
                    out.append({"tool": tool, "file": target, "line": phys.get("region", {}).get("startLine"),
                                "rule": res.get("ruleId"), "detail": res.get("message", {}).get("text", "")[:200]})
    return out


def read_graph(path: Path, files: set[str]) -> tuple[dict[str, set[str]], dict[str, set[str]], list[dict]]:
    """File-level fan-in/fan-out and symbols nothing in another file references. Edges carry the
    referencing file in 'source_file' and point at the referenced node."""
    g = json.loads(path.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in g.get("nodes", [])}
    fan_in: dict[str, set[str]] = defaultdict(set)
    fan_out: dict[str, set[str]] = defaultdict(set)
    referenced: set[str] = set()
    for e in g.get("links", g.get("edges", [])):
        if e.get("relation") not in REFERENCE_RELATIONS:
            continue
        src = resolve(e.get("source_file", ""), files) if e.get("source_file") else None
        dst_node = nodes.get(e.get("target"), {})
        dst = resolve(dst_node.get("source_file", ""), files) if dst_node.get("source_file") else None
        if src and dst and src != dst:
            fan_in[dst].add(src)
            fan_out[src].add(dst)
            referenced.add(e["target"])
    unreferenced = []
    for nid, n in nodes.items():
        f = resolve(n.get("source_file", ""), files) if n.get("source_file") else None
        label = n.get("label", "")
        # Functions only: import edges point at files, not symbols, so types and methods give too many false hits.
        if f and n.get("_callable") and nid not in referenced and label.endswith("()") and not label.startswith("."):
            unreferenced.append({"symbol": label[:-2], "file": f, "line": n.get("source_location")})
    return fan_in, fan_out, unreferenced


def confirm_by_text(candidates: list[dict], sources: list[str], repo_root: Path) -> list[dict]:
    """Second signal for unreferenced functions: the name appears in no other source file and only once
    (its definition) in its own file. Strings, reflection and config can still reference it; the
    reviewer must check those before deleting anything."""
    texts = {}
    for f in sources:
        path = repo_root / f
        texts[f] = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
    confirmed = []
    for c in candidates:
        rx = re.compile(rf"\b{re.escape(c['symbol'])}\b")
        if len(rx.findall(texts.get(c["file"], ""))) > 1:
            continue
        if any(rx.search(t) for f, t in texts.items() if f != c["file"]):
            continue
        confirmed.append(c)
    return confirmed


def read_graph_cycles(path: Path) -> list[list[str]]:
    cycles = []
    for m in re.finditer(r"cycle: `([^`]+)`", path.read_text(encoding="utf-8", errors="replace")):
        parts = [p.strip() for p in m.group(1).split("->")]
        cycles.append(parts[:-1] if len(parts) > 1 and parts[0] == parts[-1] else parts)
    return cycles


# --------------------------------------------------------------------------- map


def build(run_dir: Path, contract_path: Path, max_unit_lines: int, repo_root: Path) -> dict:
    raw = run_dir / "raw"
    if not (raw / TOOLS["files"]).is_file():
        raise SystemExit(f"build_map: {raw / TOOLS['files']} is required (git ls-files > raw/files.txt)")
    present = {k: (raw / v).is_file() for k, v in TOOLS.items()}
    sarif_files = sorted(raw.glob("*.sarif"))

    contract = cc.parse_contract(cc.yaml.safe_load(contract_path.read_text(encoding="utf-8")))
    layer_rx = [(l, [re.compile(cc.glob_to_regex(p)) for p in l.paths]) for l in contract.layers]
    module_rx = re.compile(f"^{cc.escape_literal(contract.modules.prefix)}/([^/]+)/") if contract.modules else None
    limits = contract.limits

    tracked = [norm(l) for l in (raw / TOOLS["files"]).read_text(encoding="utf-8").splitlines() if l.strip()]
    sources = sorted(f for f in tracked if Path(f).suffix in SOURCE_EXTENSIONS)
    files = set(sources)

    churn = read_churn(raw / TOOLS["churn"]) if present["churn"] else {}
    loc = read_scc(raw / TOOLS["scc"], files) if present["scc"] else {}
    funcs = read_lizard(raw / TOOLS["lizard"], files) if present["lizard"] else {}
    clones = read_jscpd(raw / TOOLS["jscpd"], files) if present["jscpd"] else []
    tool_findings = read_gitleaks(raw / TOOLS["gitleaks"], files) if present["gitleaks"] else []
    cycles: list[list[str]] = []
    if present["depcruise"]:
        dc, cycles = read_depcruise(raw / TOOLS["depcruise"], files)
        tool_findings += dc
    for sarif in sarif_files:
        tool_findings += read_sarif(sarif, files)
    fan_in, fan_out, unreferenced = read_graph(raw / TOOLS["graph"], files) if present["graph"] else ({}, {}, [])
    unreferenced = confirm_by_text(unreferenced, sources, repo_root)
    if present["graph_report"]:
        for c in read_graph_cycles(raw / TOOLS["graph_report"]):
            if sorted(c) not in [sorted(x) for x in cycles]:
                cycles.append(c)

    per_file: dict[str, dict] = {}
    overlaps = []
    for f in sources:
        layers = [l.name for l, rxs in layer_rx if any(rx.match(f) for rx in rxs)]
        if len(layers) > 1:
            overlaps.append({"file": f, "layers": layers})
        if f not in loc:
            path = repo_root / f
            loc[f] = sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()) if path.is_file() else 0
        fn = funcs.get(f, [])
        over = [x for x in fn
                if x["ccn"] > limits.get("max_function_complexity", 10**9) or x["nloc"] > limits.get("max_function_lines", 10**9)]
        dup = sum(c["lines"] for c in clones if f in (c["a"]["file"], c["b"]["file"]))
        findings = [t for t in tool_findings if t["file"] == f]
        max_ccn = max((x["ccn"] for x in fn), default=None)
        sec = sum(1 for t in findings if t["tool"] != "dependency-cruiser")
        arch = len(findings) - sec
        risk = (1 + churn.get(f, 0)) * max(1, max_ccn or 1) * math.log2(2 + loc[f]) + 25 * sec + 10 * arch + dup
        mm = module_rx.match(f) if module_rx else None
        per_file[f] = {
            "layer": layers[0] if layers else None,
            "module": mm.group(1) if mm else None,
            "loc": loc[f], "churn": churn.get(f, 0), "max_ccn": max_ccn,
            "functions_over_limit": over, "duplicated_lines": dup,
            "fan_in": len(fan_in.get(f, ())) if present["graph"] else None,
            "fan_out": len(fan_out.get(f, ())) if present["graph"] else None,
            "is_test": bool(TEST_PATTERN.search(f)),
            "tool_findings": findings,
            "risk": round(risk, 1),
            "over_file_limit": loc[f] > limits.get("max_file_lines", 10**9),
        }

    # Entry points (layers that may import anything, e.g. main/composition) are reached by the runtime, not by imports.
    entry_layers = {l.name for l in contract.layers if l.may_import == ("*",)}
    unreferenced = [s for s in unreferenced if per_file.get(s["file"], {}).get("layer") not in entry_layers]
    dead_file_candidates = [
        f for f, m in per_file.items()
        if m["fan_in"] == 0 and not m["is_test"] and m["layer"] not in entry_layers
    ] if present["graph"] else []

    units = plan_units(contract, per_file, max_unit_lines)
    return {
        "schema": 1,
        "contract": contract_path.as_posix(),
        "inputs": {k: ("ran" if v else "not run") for k, v in present.items()} | {"sarif": [s.name for s in sarif_files]},
        "limits": limits,
        "layers": [{"name": l.name, "may_import": list(l.may_import),
                    "files": sum(1 for m in per_file.values() if m["layer"] == l.name),
                    "loc": sum(m["loc"] for m in per_file.values() if m["layer"] == l.name)} for l in contract.layers],
        "unassigned": sorted(f for f, m in per_file.items() if m["layer"] is None),
        "overlaps": overlaps,
        # Production risk first: test files get their own short list instead of crowding out the code they test.
        "hotspots": sorted((f for f in per_file if not per_file[f]["is_test"]), key=lambda f: -per_file[f]["risk"])[:10],
        "test_hotspots": sorted((f for f in per_file if per_file[f]["is_test"]), key=lambda f: -per_file[f]["risk"])[:5],
        "dead_file_candidates": sorted(dead_file_candidates),
        "unreferenced_symbols": unreferenced,
        "duplicates": clones,
        "cycles": cycles,
        "files": per_file,
        "units": units,
    }


def plan_units(contract: cc.Contract, per_file: dict[str, dict], max_unit_lines: int) -> list[dict]:
    """Group files by (layer, module), inner layers first, riskiest first; split groups over the line budget."""
    order = {l.name: i for i, l in enumerate(contract.layers)}
    groups: dict[tuple[int, str, str], list[str]] = defaultdict(list)
    for f, m in per_file.items():
        layer = m["layer"] or "unassigned"
        groups[(order.get(layer, len(order)), layer, m["module"] or "-")].append(f)

    units = []
    ranked = sorted(groups.items(), key=lambda kv: (kv[0][0], -max(per_file[f]["risk"] for f in kv[1]), kv[0][2]))
    for (_, layer, module), members in ranked:
        members.sort(key=lambda f: -per_file[f]["risk"])
        chunk: list[str] = []
        for f in members:
            if chunk and sum(per_file[x]["loc"] for x in chunk) + per_file[f]["loc"] > max_unit_lines:
                units.append(chunk_unit(len(units) + 1, layer, module, chunk, per_file))
                chunk = []
            chunk.append(f)
        if chunk:
            units.append(chunk_unit(len(units) + 1, layer, module, chunk, per_file))
    return units


def chunk_unit(n: int, layer: str, module: str, files: list[str], per_file: dict[str, dict]) -> dict:
    return {"id": f"U{n:03d}", "layer": layer, "module": module, "files": files,
            "loc": sum(per_file[f]["loc"] for f in files), "risk": round(max(per_file[f]["risk"] for f in files), 1)}


# --------------------------------------------------------------------------- markdown


def render_md(m: dict) -> str:
    out = [f"# System Map\n\nContract: `{m['contract']}`\n", "## Inputs\n", "| Input | Status |", "|---|---|"]
    out += [f"| {k} | {v} |" for k, v in m["inputs"].items() if k != "sarif"]
    out.append(f"| SARIF files | {', '.join(m['inputs']['sarif']) or 'none'} |")
    out += ["\nInputs marked **not run** were not checked. Say so in the report.\n",
            "## Layers\n", "| Layer | May import | Files | Lines |", "|---|---|---|---|"]
    out += [f"| {l['name']} | {', '.join(l['may_import']) or '-'} | {l['files']} | {l['loc']} |" for l in m["layers"]]
    if m["unassigned"]:
        out += ["\n## Files in no layer (every rule misses them)\n"] + [f"- `{f}`" for f in m["unassigned"]]
    if m["overlaps"]:
        out += ["\n## Files matching more than one layer\n"] + [f"- `{o['file']}`: {', '.join(o['layers'])}" for o in m["overlaps"]]
    out += ["\n## Hotspots, production code (risk = churn × complexity × size, plus tool findings)\n",
            "| File | Layer | Lines | Max CCN | Churn | Fan-in | Tool findings | Risk |", "|---|---|---|---|---|---|---|---|"]
    for f in m["hotspots"]:
        x = m["files"][f]
        out.append(f"| `{f}` | {x['layer'] or 'unassigned'} | {x['loc']} | {x['max_ccn'] if x['max_ccn'] is not None else '-'} | "
                   f"{x['churn']} | {x['fan_in'] if x['fan_in'] is not None else '-'} | {len(x['tool_findings'])} | {x['risk']} |")
    if m["test_hotspots"]:
        out += ["\n## Hotspots, test code\n"] + [f"- `{f}`: risk {m['files'][f]['risk']}" for f in m["test_hotspots"]]
    if m["dead_file_candidates"]:
        out += ["\n## Dead-file candidates (signal 1 of 2: no incoming references in the graph)\n"]
        out += [f"- `{f}`" for f in m["dead_file_candidates"]]
    if m["unreferenced_symbols"]:
        out += ["\n## Unreferenced functions (graph + text search agree; still check strings, reflection, config)\n"]
        out += [f"- `{s['symbol']}` in `{s['file']}` {s['line'] or ''}" for s in m["unreferenced_symbols"]]
    if m["duplicates"]:
        out += ["\n## Duplicated code\n"]
        out += [f"- {c['lines']} lines: `{c['a']['file']}:{c['a']['start']}` ≈ `{c['b']['file']}:{c['b']['start']}`" for c in m["duplicates"]]
    if m["cycles"]:
        out += ["\n## Import cycles\n"] + [f"- {' -> '.join(c)} -> {c[0]}" for c in m["cycles"]]
    out += ["\n## Unit plan (inner layers first, riskiest first)\n", "| Unit | Layer | Module | Files | Lines | Risk |", "|---|---|---|---|---|---|"]
    out += [f"| {u['id']} | {u['layer']} | {u['module']} | {len(u['files'])} | {u['loc']} | {u['risk']} |" for u in m["units"]]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--contract", default=".engg/architecture.yaml")
    ap.add_argument("--max-unit-lines", type=int, default=600)
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args(argv)
    run_dir = Path(args.run_dir)
    try:
        m = build(run_dir, Path(args.contract), args.max_unit_lines, Path(args.repo_root))
    except cc.ContractError as exc:
        print("build_map: the contract is invalid:\n" + "\n".join(f"  - {e}" for e in exc.errors), file=sys.stderr)
        return 2
    (run_dir / "map.json").write_text(json.dumps(m, indent=2), encoding="utf-8", newline="\n")
    (run_dir / "map.md").write_text(render_md(m), encoding="utf-8", newline="\n")
    print(f"map: {len(m['files'])} source files, {len(m['units'])} units, {len(m['unassigned'])} unassigned, "
          f"{len(m['dead_file_candidates'])} dead-file candidates, {len(m['cycles'])} cycles -> {run_dir.as_posix()}/map.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
