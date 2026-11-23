#!/usr/bin/env python3
"""Print what a session needs to begin: the handoff, then the one next thing to do.

Usage (from the repo root):
    brief.py                 handoff + next step (In progress, else Fix first, else the next ready chunk)
    brief.py --chunk <ID>    one chunk card with the sections it cites, e.g. for a reviewer
    brief.py --root <dir>    run against another repository

Reads docs/HANDOFF.md, docs/BLUEPRINT.md, docs/EDD.md and docs/CHARTER.md (formats in
references/working-loop.md and the engg-plan chunk template). Missing files are reported, never fatal.
Requires Python 3.10+ only (no third-party packages).
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HANDOFF = "docs/HANDOFF.md"
BLUEPRINT = "docs/BLUEPRINT.md"
CITABLE = {"EDD": "docs/EDD.md", "CHARTER": "docs/CHARTER.md"}
EMPTY = {"", "none", "none."}

CARD_RE = re.compile(r"^###\s+\[?(?P<id>[A-Z]+-?\d+[a-z]?)\]?\s+(?P<title>.+?)\s*$")
FIELD_RE = re.compile(r"^-\s+\*\*(?P<name>[^*:]+):?\*\*:?\s*(?P<value>.*)$")
DONE_RE = re.compile(r"^-\s+(?P<id>[A-Z]+-?\d+[a-z]?)\b(?P<rest>.*)$")
GATE_RE = re.compile(r"^-\s+Gate\s+(?:Wave\s+)?(?P<wave>\w+)\b", re.IGNORECASE)
WAVE_IN_TITLE_RE = re.compile(r"\(Wave\s+(?P<wave>\w+)", re.IGNORECASE)
WAVE_IN_DONE_RE = re.compile(r"Wave\s+(?P<wave>\w+)", re.IGNORECASE)
CHUNK_ID_RE = re.compile(r"\b[A-Z]+-?\d+[a-z]?\b")
CITE_RE = re.compile(r"\b(?P<doc>EDD|CHARTER)\s*((?:§\s*[\w.]+[\s,;]*(?:and\s+)?)+)")
SECTION_NUM_RE = re.compile(r"§\s*([\w.]+)")
ADR_RE = re.compile(r"\bADR[- ]?(\d{1,4})\b")
BACKTICK_RE = re.compile(r"`([^`]+)`")


@dataclass
class Chunk:
    id: str
    title: str
    text: str
    fields: dict[str, str] = field(default_factory=dict)

    @property
    def wave(self) -> str | None:
        value = self.fields.get("wave")
        if value:
            return value.split()[0]
        match = WAVE_IN_TITLE_RE.search(self.title)
        return match.group("wave") if match else None

    @property
    def depends_on(self) -> list[str]:
        value = self.fields.get("dependencies") or self.fields.get("depends on") or ""
        return CHUNK_ID_RE.findall(value)


@dataclass
class Blueprint:
    chunks: list[Chunk]
    done: set[str]
    done_waves: set[str]
    gated_waves: set[str]


def read(root: Path, rel: str) -> str | None:
    path = root / rel
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def section(markdown: str, heading: str) -> str:
    """Body of the first `## <heading>` section (case-insensitive), without the heading."""
    lines = markdown.split("\n")
    out: list[str] = []
    inside = False
    for line in lines:
        if re.match(r"^##\s", line) and not line.startswith("###"):
            if inside:
                break
            inside = line[2:].strip().lower().startswith(heading.lower())
            continue
        if inside:
            out.append(line)
    return "\n".join(out).strip()


def parse_blueprint(text: str) -> Blueprint:
    chunks: list[Chunk] = []
    done: set[str] = set()
    done_waves: set[str] = set()
    gated: set[str] = set()
    current: Chunk | None = None
    in_done = False
    body: list[str] = []

    def flush() -> None:
        if current is not None:
            current.text = "\n".join(body).rstrip()
            chunks.append(current)

    for line in text.split("\n"):
        if line.startswith("## "):
            flush()
            current, body = None, []
            in_done = line[3:].strip().lower().startswith("done")
            continue
        card = CARD_RE.match(line)
        if card:
            flush()
            current, body = Chunk(card.group("id"), card.group("title"), ""), [line]
            in_done = False
            continue
        if current is not None:
            body.append(line)
            match = FIELD_RE.match(line.strip())
            if match:
                current.fields[match.group("name").strip().lower()] = match.group("value").strip()
            continue
        if in_done:
            gate = GATE_RE.match(line.strip())
            if gate:
                gated.add(gate.group("wave"))
                continue
            entry = DONE_RE.match(line.strip())
            if entry:
                done.add(entry.group("id"))
                wave = WAVE_IN_DONE_RE.search(entry.group("rest"))
                if wave:
                    done_waves.add(wave.group("wave"))
    flush()
    return Blueprint(chunks, done, done_waves, gated)


def next_chunk(bp: Blueprint) -> Chunk | None:
    for chunk in bp.chunks:
        if all(dep in bp.done for dep in chunk.depends_on):
            return chunk
    return None


def gates_due(bp: Blueprint) -> list[str]:
    open_waves = {c.wave for c in bp.chunks if c.wave}
    return sorted(w for w in bp.done_waves if w not in open_waves and w not in bp.gated_waves)


def cited_sections(root: Path, cites: str) -> list[str]:
    out: list[str] = []
    for match in CITE_RE.finditer(cites):
        doc = match.group("doc")
        text = read(root, CITABLE[doc])
        for number in SECTION_NUM_RE.findall(match.group(0)):
            if text is None:
                out.append(f"({doc} §{number}: {CITABLE[doc]} not found)")
                continue
            body = numbered_section(text, number)
            out.append(body if body else f"({doc} §{number} not found in {CITABLE[doc]})")
    for number in ADR_RE.findall(cites):
        hits = sorted((root / "docs" / "decisions").glob(f"{int(number):04d}-*.md"))
        out.append(f"ADR {number}: {hits[0].relative_to(root).as_posix() if hits else 'not found'}")
    return out


def numbered_section(text: str, number: str) -> str | None:
    """A heading like `## 3. Contracts` or `### 3.2 Errors`, with its body up to the next heading of the same or higher level."""
    lines = text.split("\n")
    pattern = re.compile(rf"^(#{{1,4}})\s+§?\s*{re.escape(number)}(?:[.)]|\s|$)")
    for i, line in enumerate(lines):
        match = pattern.match(line)
        if not match:
            continue
        level = len(match.group(1))
        out = [line]
        for nxt in lines[i + 1:]:
            heading = re.match(r"^(#{1,6})\s", nxt)
            if heading and len(heading.group(1)) <= level:
                break
            out.append(nxt)
        return "\n".join(out).strip()
    return None


def print_chunk(root: Path, chunk: Chunk) -> None:
    print(chunk.text)
    cites = chunk.fields.get("cites") or chunk.fields.get("spec") or ""
    if cites:
        print("\n== CITED ==")
        for block in cited_sections(root, cites):
            print(block + "\n")
    follow = BACKTICK_RE.findall(chunk.fields.get("follow", ""))
    print("== FOLLOW ==")
    print("\n".join(follow) if follow else "(none)")


def brief(root: Path) -> int:
    handoff = read(root, HANDOFF)
    if handoff is None:
        print(f"No {HANDOFF}: the working loop isn't set up here. Start from the user's request;")
        print("the first engg skill that finishes a step creates it (references/working-loop.md §4).")
        return 0
    print(f"== HANDOFF ==\n{handoff.strip()}\n")
    if len(handoff.splitlines()) > 60:
        print(f"(note: {HANDOFF} is over 60 lines; trim it at the end of this step)\n")

    in_progress = section(handoff, "In progress")
    if in_progress.lower() not in EMPTY:
        print("== NEXT: resume the In progress entry above before anything else ==")
        return 0
    fix = re.search(r"^-\s+(FIX-\d+)\b.*$", section(handoff, "Fix first"), re.MULTILINE)
    if fix:
        print(f"== NEXT: {fix.group(1)} (Fix first) ==\n{fix.group(0)}")
        print("Branch fix/<FIX-id>-<slug>. Write a regression test that fails before the fix.")
        return 0

    text = read(root, BLUEPRINT)
    if text is None:
        print(f"== NEXT ==\nNo {BLUEPRINT} yet: follow the handoff's Next line.")
        return 0
    bp = parse_blueprint(text)
    for wave in gates_due(bp):
        print(f"== WAVE GATE DUE: Wave {wave} has no open chunks (working-loop §3) ==\n")
    chunk = next_chunk(bp)
    if chunk is None:
        if bp.chunks:
            blocked = ", ".join(f"{c.id} (needs {', '.join(d for d in c.depends_on if d not in bp.done)})" for c in bp.chunks)
            print(f"== NEXT: nothing is ready. Blocked: {blocked} ==")
        else:
            print("== NEXT: every chunk is done. Run the wave gate, then plan the next milestone. ==")
        return 0
    print("== NEXT CHUNK ==")
    print_chunk(root, chunk)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--chunk", help="print this chunk card and its cited sections")
    parser.add_argument("--root", default=".", help="repository root (default: current directory)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    root = Path(args.root)
    if args.chunk:
        text = read(root, BLUEPRINT)
        chunk = next((c for c in parse_blueprint(text).chunks if c.id == args.chunk), None) if text else None
        if chunk is None:
            print(f"Chunk {args.chunk} is not an open chunk in {BLUEPRINT}.")
            return 1
        print_chunk(root, chunk)
        return 0
    return brief(root)


if __name__ == "__main__":
    sys.exit(main())
