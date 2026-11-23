#!/usr/bin/env python3
"""Map the repository cheaply: files with their exported symbols, or the shape of a large repo.

Usage (from the repo root):
    map.py [prefix]           tracked and new files under prefix, each with its exported symbols
    map.py --dirs [prefix]    directories with file counts (the big picture of a large repo)
    map.py --depth N          directory depth for --dirs (default 2)

With no prefix and more than --max files (default 400), prints --dirs instead and says so.
Symbols are read with simple per-language patterns (TS/JS, Python, Go, Rust, Java, Kotlin, C#):
a quick index for finding files, not a parser. Lockfiles, generated and vendored paths are skipped.
Requires Python 3.10+ and git (no third-party packages).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

SKIP_RE = re.compile(
    r"(^|/)(node_modules|vendor|dist|build|coverage|target|\.venv|__pycache__|\.next|out)/"
    r"|(^|/)\.engg/(generated|audit)/|(^|/)graphify-out/"
    r"|(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|bun\.lockb?|poetry\.lock|uv\.lock|Pipfile\.lock"
    r"|Cargo\.lock|go\.sum|composer\.lock|Gemfile\.lock|gradle\.lockfile)$"
    r"|\.(min\.js|map|png|jpe?g|gif|webp|ico|pdf|zip|gz|woff2?|ttf|eot|mp4|mp3|wasm)$"
    r"|(^|/)\.gitkeep$"
)
MAX_BYTES = 512_000

TS_NAMED = re.compile(r"^export\s+(?:default\s+)?(?:declare\s+)?(?:async\s+)?(?:abstract\s+)?"
                      r"(?:function\*?|class|const|let|var|interface|type|enum|namespace)\s+([A-Za-z_$][\w$]*)")
TS_BRACES = re.compile(r"^export\s+(?:type\s+)?\{([^}]*)\}")
TS_STAR = re.compile(r"^export\s+\*\s+(?:as\s+(\w+)\s+)?from\s+['\"]([^'\"]+)['\"]")
TS = [TS_NAMED, TS_BRACES, TS_STAR]
PATTERNS: dict[str, list[re.Pattern[str]]] = {
    ".ts": TS, ".tsx": TS, ".mts": TS, ".cts": TS, ".js": TS, ".jsx": TS, ".mjs": TS, ".cjs": TS,
    ".py": [re.compile(r"^(?:async\s+)?def\s+([A-Za-z]\w*)"), re.compile(r"^class\s+([A-Za-z]\w*)")],
    ".go": [re.compile(r"^func\s+(?:\([^)]*\)\s*)?([A-Z]\w*)"), re.compile(r"^type\s+([A-Z]\w*)"),
            re.compile(r"^(?:var|const)\s+([A-Z]\w*)")],
    ".rs": [re.compile(r"^pub\s+(?:async\s+)?(?:unsafe\s+)?(?:fn|struct|enum|trait|type|const|static|mod)\s+(\w+)")],
    ".java": [re.compile(r"^public\s+(?:final\s+|abstract\s+|sealed\s+)*(?:class|interface|enum|record)\s+(\w+)")],
    ".kt": [re.compile(r"^(?:data\s+|sealed\s+|abstract\s+|open\s+|enum\s+)*(?:class|interface|object|fun)\s+(?:<[^>]+>\s*)?([A-Za-z]\w*)")],
    ".cs": [re.compile(r"^\s*public\s+(?:static\s+|sealed\s+|abstract\s+|partial\s+)*(?:class|interface|enum|record|struct)\s+(\w+)")],
}


def git_files(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    if result.returncode != 0:
        sys.exit(f"map.py: git ls-files failed: {result.stderr.strip() or 'not a git repository?'}")
    return sorted({f for f in result.stdout.splitlines() if f and not SKIP_RE.search(f)})


def symbols(path: Path) -> list[str]:
    patterns = PATTERNS.get(path.suffix)
    if not patterns or not path.is_file() or path.stat().st_size > MAX_BYTES:
        return []
    found: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if path.suffix == ".kt" and line.startswith(("private ", "internal ")):
            continue
        for pattern in patterns:
            match = pattern.match(line)
            if not match:
                continue
            if pattern is TS_BRACES:
                names = [part.split(" as ")[-1].strip() for part in match.group(1).split(",")]
                found.extend(n.removeprefix("type ").strip() for n in names if n.strip())
            elif pattern is TS_STAR:
                found.append(f"{match.group(1)} (*)" if match.group(1) else f"* from {match.group(2)}")
            else:
                found.append(match.group(1))
            break
    return list(dict.fromkeys(found))


def dir_counts(files: list[str], depth: int) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for f in files:
        parts = f.split("/")[:-1]
        key = "/".join(parts[:depth]) + "/" if parts else "./"
        counts[key] += 1
    return sorted(counts.items())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("prefix", nargs="?", default="")
    parser.add_argument("--dirs", action="store_true", help="directories with file counts")
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--max", type=int, default=400, help="file count above which a bare run shows --dirs")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    root = Path(args.root)
    prefix = args.prefix.replace("\\", "/").removeprefix("./")
    files = [f for f in git_files(root) if f.startswith(prefix)]

    if args.dirs or (not prefix and len(files) > args.max):
        if not args.dirs:
            print(f"({len(files)} files: showing directories. Run map.py <dir> for files and symbols.)")
        for directory, count in dir_counts(files, args.depth):
            print(f"{directory}  {count}")
        return 0
    for f in files:
        names = symbols(root / f)
        print(f"{f}: {', '.join(names)}" if names else f)
    return 0


if __name__ == "__main__":
    sys.exit(main())
