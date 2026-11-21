#!/usr/bin/env bash
set -euo pipefail

# Unified Engineering Skills Suite Installer
# Supports: Claude Code CLI, Antigravity CLI, Antigravity IDE (plus Codex, Cursor, Copilot, OpenCode)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_SKILLS_DIR="${SCRIPT_DIR}/skills"
MODE=""
PROJECT_DIR=""
USE_COPY=0

usage() {
  cat <<'EOF'
Usage:
  ./install.sh --global [--copy]
      Installs skills globally for:
        - Antigravity CLI & Antigravity IDE (~/.gemini/config/skills/)
        - Claude Code CLI (~/.claude/skills/)
      (Canonical copy stored in ~/.engg-skills-suite/skills/ and symlinked unless --copy is set)

  ./install.sh --project <repo_path> [--copy]
      Installs skills into a specific repository:
        - Canonical workspace path: <repo>/.agents/skills/  (Antigravity IDE, Antigravity CLI, Codex, Cursor, Copilot)
        - Claude Code link:         <repo>/.claude/skills/  (symlinked to ../.agents/skills/<skill>)

Options:
  --copy    Copy files instead of creating symlinks (useful when symlinks are restricted)
  -h,--help Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global) MODE="global"; shift ;;
    --project) MODE="project"; PROJECT_DIR="${2:-}"; shift 2 ;;
    --copy) USE_COPY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$MODE" ]]; then
  usage
  exit 1
fi

install_skill() {
  local src="$1"
  local dst="$2"
  local rel_link="${3:-}"

  rm -rf "$dst"
  if [[ "$USE_COPY" -eq 1 ]]; then
    cp -R "$src" "$dst"
  else
    if [[ -n "$rel_link" ]]; then
      ln -s "$rel_link" "$dst"
    else
      ln -s "$src" "$dst"
    fi
  fi
}

if [[ "$MODE" == "global" ]]; then
  CANONICAL_DIR="${HOME}/.engg-skills-suite/skills"
  AGY_GLOBAL="${HOME}/.gemini/config/skills"
  CLAUDE_GLOBAL="${HOME}/.claude/skills"

  mkdir -p "$CANONICAL_DIR" "$AGY_GLOBAL" "$CLAUDE_GLOBAL"

  for skill_path in "${SRC_SKILLS_DIR}"/*; do
    [[ -d "$skill_path" ]] || continue
    skill_name="$(basename "$skill_path")"

    rm -rf "${CANONICAL_DIR}/${skill_name}"
    cp -R "$skill_path" "${CANONICAL_DIR}/${skill_name}"

    install_skill "${CANONICAL_DIR}/${skill_name}" "${AGY_GLOBAL}/${skill_name}"
    install_skill "${CANONICAL_DIR}/${skill_name}" "${CLAUDE_GLOBAL}/${skill_name}"
    echo "Installed global skill: ${skill_name}"
  done

  echo ""
  echo "Done! Installed $(ls -1 "${SRC_SKILLS_DIR}" | wc -l | tr -d ' ') skills globally:"
  echo "  - Canonical store:              ${CANONICAL_DIR}"
  echo "  - Antigravity IDE & CLI:        ${AGY_GLOBAL}"
  echo "  - Claude Code CLI:              ${CLAUDE_GLOBAL}"
  echo ""
  echo "Verify with:"
  echo "  Claude Code CLI:  claude skills list  (or ask: 'What skills do you have?')"
  echo "  Antigravity CLI:  /skills"
  echo "  Antigravity IDE:  Ask the agent 'Which skills are installed?' or type '/'"

elif [[ "$MODE" == "project" ]]; then
  if [[ -z "$PROJECT_DIR" || ! -d "$PROJECT_DIR" ]]; then
    echo "Error: Provide an existing project directory path after --project" >&2
    exit 1
  fi

  PROJECT_ABS="$(cd "$PROJECT_DIR" && pwd)"
  AGENTS_DIR="${PROJECT_ABS}/.agents/skills"
  CLAUDE_DIR="${PROJECT_ABS}/.claude/skills"

  mkdir -p "$AGENTS_DIR" "$CLAUDE_DIR"

  for skill_path in "${SRC_SKILLS_DIR}"/*; do
    [[ -d "$skill_path" ]] || continue
    skill_name="$(basename "$skill_path")"

    rm -rf "${AGENTS_DIR}/${skill_name}"
    cp -R "$skill_path" "${AGENTS_DIR}/${skill_name}"

    # Relative symlink from .claude/skills/<name> -> ../../.agents/skills/<name>
    install_skill "${AGENTS_DIR}/${skill_name}" "${CLAUDE_DIR}/${skill_name}" "../../.agents/skills/${skill_name}"
    echo "Installed project skill: ${skill_name}"
  done

  echo ""
  echo "Done! Installed project-scoped skills into ${PROJECT_ABS}:"
  echo "  - Canonical (.agents/skills):   ${AGENTS_DIR}  (Antigravity IDE/CLI, Codex, Cursor, Copilot)"
  echo "  - Claude Code (.claude/skills): ${CLAUDE_DIR}"
fi
