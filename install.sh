#!/usr/bin/env bash
# Unified Engineering Skills Suite installer (macOS / Linux).
# On Windows, use install.ps1: Git Bash's `ln -s` silently copies unless native symlinks are enabled.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_SKILLS_DIR="${SCRIPT_DIR}/skills"
MODE=""
PROJECT_DIR=""
USE_COPY=0
UNINSTALL=0
DRY_RUN=0

usage() {
  cat <<'EOF'
Usage:
  ./install.sh --global  [--copy] [--uninstall] [--dry-run]
  ./install.sh --project <repo_path> [--copy] [--uninstall] [--dry-run]

Scopes:
  --global            Canonical copy in ~/.engg-skills-suite/skills/, linked into:
                        ~/.claude/skills/            (Claude Code)
                        ~/.gemini/config/skills/     (Antigravity CLI & IDE)
  --project <path>    Canonical copy in <repo>/.agents/skills/ (open standard: Antigravity,
                      Codex, Cursor, Copilot, OpenCode), linked into <repo>/.claude/skills/.

Options:
  --copy        Copy files instead of creating symlinks
  --uninstall   Remove only the skills that ship with this suite (other skills are untouched)
  --dry-run     Print what would happen without changing anything
  -h, --help    Show this help
EOF
}

die() { echo "Error: $*" >&2; echo >&2; usage >&2; exit 1; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global) [[ -z "$MODE" ]] || die "choose exactly one of --global or --project"; MODE="global"; shift ;;
    --project)
      [[ -z "$MODE" ]] || die "choose exactly one of --global or --project"
      [[ $# -ge 2 && "$2" != --* ]] || die "--project needs a repository path"
      MODE="project"; PROJECT_DIR="$2"; shift 2 ;;
    --copy) USE_COPY=1; shift ;;
    --uninstall) UNINSTALL=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) die "unknown option: $1" ;;
  esac
done

[[ -n "$MODE" ]] || die "choose a scope: --global or --project <path>"
[[ -d "$SRC_SKILLS_DIR" ]] || die "skills directory not found next to this script: $SRC_SKILLS_DIR"

# Print the command; run it unless --dry-run.
run() {
  echo "+ $*"
  if [[ "$DRY_RUN" -eq 0 ]]; then "$@"; fi
}

# Remove a previous install entry. `rm -rf` on a symlink path (no trailing slash) removes the link, not its target.
remove_entry() {
  local path="$1"
  if [[ -L "$path" || -e "$path" ]]; then run rm -rf "$path"; fi
}

# Link (or copy with --copy) src to dst. link_target lets project installs use a relative link.
place() {
  local src="$1" dst="$2" link_target="${3:-$1}"
  remove_entry "$dst"
  if [[ "$USE_COPY" -eq 1 ]]; then
    run cp -R "$src" "$dst"
  else
    run ln -s "$link_target" "$dst"
  fi
}

SKILLS=()
for skill_path in "${SRC_SKILLS_DIR}"/*/; do
  [[ -f "${skill_path}SKILL.md" ]] || continue
  SKILLS+=("$(basename "$skill_path")")
done
[[ ${#SKILLS[@]} -gt 0 ]] || die "no skills found in $SRC_SKILLS_DIR"

if [[ "$MODE" == "global" ]]; then
  CANONICAL_DIR="${HOME}/.engg-skills-suite/skills"
  TOOL_DIRS=("${HOME}/.claude/skills" "${HOME}/.gemini/config/skills")
else
  [[ -d "$PROJECT_DIR" ]] || die "project directory does not exist: $PROJECT_DIR"
  PROJECT_ABS="$(cd "$PROJECT_DIR" && pwd)"
  CANONICAL_DIR="${PROJECT_ABS}/.agents/skills"
  TOOL_DIRS=("${PROJECT_ABS}/.claude/skills")
fi

if [[ "$UNINSTALL" -eq 1 ]]; then
  for skill in "${SKILLS[@]}"; do
    for dir in "${TOOL_DIRS[@]}"; do remove_entry "${dir}/${skill}"; done
    remove_entry "${CANONICAL_DIR}/${skill}"
    echo "Removed: ${skill}"
  done
  echo "Done. Uninstalled ${#SKILLS[@]} skills (${MODE} scope)."
  exit 0
fi

run mkdir -p "$CANONICAL_DIR" "${TOOL_DIRS[@]}"
for skill in "${SKILLS[@]}"; do
  remove_entry "${CANONICAL_DIR}/${skill}"
  run cp -R "${SRC_SKILLS_DIR}/${skill}" "${CANONICAL_DIR}/${skill}"
  for dir in "${TOOL_DIRS[@]}"; do
    if [[ "$MODE" == "project" ]]; then
      # <repo>/.claude/skills/<name> -> ../../.agents/skills/<name> (survives moving the repo)
      place "${CANONICAL_DIR}/${skill}" "${dir}/${skill}" "../../.agents/skills/${skill}"
    else
      place "${CANONICAL_DIR}/${skill}" "${dir}/${skill}"
    fi
  done
  echo "Installed: ${skill}"
done

echo ""
echo "Done. Installed ${#SKILLS[@]} skills (${MODE} scope)."
echo "  Canonical store: ${CANONICAL_DIR}"
for dir in "${TOOL_DIRS[@]}"; do echo "  Linked into:     ${dir}"; done
if [[ "$DRY_RUN" -eq 1 ]]; then echo "(dry run: nothing was changed)"; fi
