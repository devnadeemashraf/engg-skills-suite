#!/usr/bin/env python3
"""Fail when commits, added lines or a message carry AI attribution.

Usage (from the repo root):
    attribution_check.py --range origin/main..HEAD   commit messages in the range, plus lines the range adds
    attribution_check.py --staged                    lines added in the staged diff (pre-commit)
    attribution_check.py --message-file FILE         one commit message or PR body (commit-msg hook: pass $1)
    attribution_check.py --exempt 'docs/legal/**'    skip more paths (repeatable; globs)

Attribution means a trailer or phrase that credits an AI tool or model: `Co-Authored-By:` naming one,
`Generated-by:`/`Assisted-by:` trailers, "generated with <tool>", "AI-generated", a robot-emoji
"Generated with" line, or an AI vendor's noreply address. Products that merely use or integrate an AI
API are not flagged: only crediting one for the work is. Agent instruction files are exempt by default.
Exit code: 0 clean, 1 attribution found, 2 usage or git error.
Requires Python 3.10+ and git (no third-party packages).
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
from pathlib import Path

# Named AI tools and vendors. Co-author trailers match only these, so a human co-author at a `.ai` domain passes.
AI_TOOLS = (r"(?:claude(?:\s+code)?|anthropic|chatgpt|gpt-?\d[\w.-]*|openai|codex|copilot|gemini|"
            r"windsurf|devin|aider|tabnine|antigravity|grok|deepseek|qwen)")
AI = rf"(?:ai|a\.i\.|llm|{AI_TOOLS})"
PATTERNS = [
    ("AI co-author trailer", re.compile(rf"^\s*co-authored-by:.*\b{AI_TOOLS}\b", re.IGNORECASE)),
    ("AI vendor noreply address", re.compile(r"noreply@(?:anthropic\.com|openai\.com)|\bcopilot@|\[bot\]@users\.noreply\.github\.com.*copilot", re.IGNORECASE)),
    ("generated-by trailer", re.compile(r"^\s*(?:generated|assisted|written|created)-(?:by|with):", re.IGNORECASE)),
    ("'generated with' credit", re.compile(rf"\b(?:generated|written|authored|co-written)\s+(?:with|by|using)\s+(?:the\s+help\s+of\s+)?\[?(?:an?\s+)?{AI}\b", re.IGNORECASE)),
    ("'AI-generated' label", re.compile(r"\b(?:ai|llm)[- ](?:generated|assisted|written|authored)\b", re.IGNORECASE)),
    ("robot-emoji credit line", re.compile("\N{ROBOT FACE}\\s*(?:generated|created|written|made)", re.IGNORECASE)),
    ("AI tool link credit", re.compile(r"claude\.com/claude-code|claude\.ai/code\b", re.IGNORECASE)),
]
DEFAULT_EXEMPT = [
    "AGENTS.md", "**/AGENTS.md", "CLAUDE.md", "**/CLAUDE.md", "GEMINI.md", "**/GEMINI.md",
    ".claude/**", ".codex/**", ".cursor/**", ".gemini/**", ".agents/**", ".github/copilot-instructions.md",
    "**/attribution_check.py", "**/test_attribution_check.py",
]


def git(args: list[str]) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def scan_text(text: str) -> list[tuple[int, str, str]]:
    """(line number, label, line) for every line carrying attribution."""
    hits: list[tuple[int, str, str]] = []
    for number, line in enumerate(text.splitlines(), 1):
        for label, pattern in PATTERNS:
            if pattern.search(line):
                hits.append((number, label, line.strip()[:160]))
                break
    return hits


def exempt(path: str, globs: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, g) or fnmatch.fnmatch(Path(path).name, g) for g in globs)


def scan_diff(diff: str, globs: list[str]) -> list[str]:
    """Scan the added lines of a `git diff --unified=0` for attribution, skipping exempt paths."""
    hits: list[str] = []
    path, number = "", 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else ""
            continue
        hunk = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)", line)
        if hunk:
            number = int(hunk.group(1))
            continue
        if line.startswith("+") and path:
            if not exempt(path, globs):
                hits.extend(f"{path}:{number}: {label}: {text}" for _, label, text in scan_text(line[1:]))
            number += 1
    return hits


def split_range(spec: str) -> tuple[str, str]:
    match = re.fullmatch(r"(.+?)\.{2,3}(.*)", spec)
    if not match:
        raise RuntimeError(f"--range must look like BASE..HEAD, got {spec!r}")
    return match.group(1), match.group(2) or "HEAD"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--range", help="e.g. origin/main..HEAD")
    mode.add_argument("--staged", action="store_true")
    mode.add_argument("--message-file")
    parser.add_argument("--exempt", action="append", default=[], help="extra path glob to skip (repeatable)")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    globs = DEFAULT_EXEMPT + args.exempt
    hits: list[str] = []
    try:
        if args.message_file:
            text = Path(args.message_file).read_text(encoding="utf-8", errors="replace")
            body = "\n".join(line for line in text.splitlines() if not line.startswith("#"))
            hits = [f"{args.message_file}:{n}: {label}: {text}" for n, label, text in scan_text(body)]
        elif args.staged:
            hits = scan_diff(git(["diff", "--cached", "--unified=0", "--no-color"]), globs)
        else:
            base, head = split_range(args.range)
            for sha in git(["rev-list", f"{base}..{head}"]).split():
                message = git(["log", "-1", "--format=%B", sha])
                hits.extend(f"commit {sha[:12]}:{n}: {label}: {text}" for n, label, text in scan_text(message))
            hits.extend(scan_diff(git(["diff", "--unified=0", "--no-color", f"{base}...{head}"]), globs))
    except (RuntimeError, OSError) as exc:
        print(f"attribution_check: {exc}")
        return 2
    if hits:
        print("AI attribution found. Remove it (amend the message or edit the line):")
        print("\n".join(hits))
        return 1
    print("ok   no AI attribution")
    return 0


if __name__ == "__main__":
    sys.exit(main())
