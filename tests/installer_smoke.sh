#!/usr/bin/env bash
# Smoke tests for install.sh. Runs against throwaway HOME and project directories.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALLER="${REPO_ROOT}/install.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

SKILLS=()
for d in "${REPO_ROOT}"/skills/*/; do SKILLS+=("$(basename "$d")"); done

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "ok - $*"; }

# On Git Bash without native symlinks, `ln -s` copies, so link-type assertions only run where links are real.
links_supported() {
  ln -s "$WORK" "$WORK/.probe" 2>/dev/null && [[ -L "$WORK/.probe" ]]
  local rc=$?; rm -rf "$WORK/.probe"; return $rc
}

assert_installed() {  # <canonical_dir> <tool_dir> <expect_links:0|1>
  local canonical="$1" tool="$2" expect_links="$3"
  for s in "${SKILLS[@]}"; do
    [[ -f "${canonical}/${s}/SKILL.md" ]] || fail "missing ${canonical}/${s}/SKILL.md"
    [[ -f "${tool}/${s}/SKILL.md" ]] || fail "missing ${tool}/${s}/SKILL.md"
    if [[ "$expect_links" -eq 1 ]]; then
      [[ -L "${tool}/${s}" ]] || fail "${tool}/${s} should be a symlink"
    else
      [[ ! -L "${tool}/${s}" ]] || fail "${tool}/${s} should be a copy"
    fi
  done
}

assert_removed() {  # <dir>...
  for dir in "$@"; do
    for s in "${SKILLS[@]}"; do
      [[ ! -e "${dir}/${s}" && ! -L "${dir}/${s}" ]] || fail "${dir}/${s} still present after uninstall"
    done
  done
}

LINKS=0
if links_supported; then LINKS=1; fi

# --- argument errors -------------------------------------------------------
if bash "$INSTALLER" >/dev/null 2>&1; then fail "no scope should exit non-zero"; fi
if bash "$INSTALLER" --project >/dev/null 2>&1; then fail "--project without a path should exit non-zero"; fi
if bash "$INSTALLER" --project --copy >/dev/null 2>&1; then fail "--project followed by a flag should exit non-zero"; fi
if bash "$INSTALLER" --global --project "$WORK" >/dev/null 2>&1; then fail "two scopes should exit non-zero"; fi
if bash "$INSTALLER" --bogus >/dev/null 2>&1; then fail "unknown option should exit non-zero"; fi
if bash "$INSTALLER" --project "$WORK/does-not-exist" >/dev/null 2>&1; then fail "missing project dir should exit non-zero"; fi
err="$(bash "$INSTALLER" --project 2>&1 || true)"
[[ "$err" == *"--project needs a repository path"* ]] || fail "unclear error for --project without a path: $err"
pass "argument errors"

# --- project scope ----------------------------------------------------------
PROJ="${WORK}/proj"; mkdir -p "$PROJ/.claude/skills/someone-elses-skill"
bash "$INSTALLER" --project "$PROJ" >/dev/null
assert_installed "$PROJ/.agents/skills" "$PROJ/.claude/skills" "$LINKS"
assert_installed "$PROJ/.agents/skills" "$PROJ/.codex/skills" "$LINKS"
if [[ "$LINKS" -eq 1 ]]; then
  target="$(readlink "$PROJ/.claude/skills/${SKILLS[0]}")"
  [[ "$target" == "../../.agents/skills/${SKILLS[0]}" ]] || fail "project link should be relative, got $target"
fi
pass "project install"

bash "$INSTALLER" --project "$PROJ" >/dev/null
assert_installed "$PROJ/.agents/skills" "$PROJ/.claude/skills" "$LINKS"
pass "project reinstall is idempotent"

bash "$INSTALLER" --project "$PROJ" --uninstall >/dev/null
assert_removed "$PROJ/.agents/skills" "$PROJ/.claude/skills" "$PROJ/.codex/skills"
[[ -d "$PROJ/.claude/skills/someone-elses-skill" ]] || fail "uninstall removed a skill that is not part of the suite"
pass "project uninstall leaves other skills alone"

bash "$INSTALLER" --project "$PROJ" --copy >/dev/null
assert_installed "$PROJ/.agents/skills" "$PROJ/.claude/skills" 0
pass "project --copy"

# --- dry run ----------------------------------------------------------------
DRY="${WORK}/dry"; mkdir -p "$DRY"
out="$(bash "$INSTALLER" --project "$DRY" --dry-run)"
[[ -z "$(ls -A "$DRY")" ]] || fail "--dry-run changed the project directory"
[[ "$out" == *"dry run"* ]] || fail "--dry-run should say so"
pass "dry run changes nothing"

# --- global scope (throwaway HOME) ------------------------------------------
FAKE_HOME="${WORK}/home"; mkdir -p "$FAKE_HOME"
HOME="$FAKE_HOME" bash "$INSTALLER" --global >/dev/null
assert_installed "$FAKE_HOME/.engg-skills-suite/skills" "$FAKE_HOME/.claude/skills" "$LINKS"
assert_installed "$FAKE_HOME/.engg-skills-suite/skills" "$FAKE_HOME/.codex/skills" "$LINKS"
assert_installed "$FAKE_HOME/.engg-skills-suite/skills" "$FAKE_HOME/.gemini/config/skills" "$LINKS"
pass "global install"

HOME="$FAKE_HOME" bash "$INSTALLER" --global --uninstall >/dev/null
assert_removed "$FAKE_HOME/.engg-skills-suite/skills" "$FAKE_HOME/.claude/skills" "$FAKE_HOME/.codex/skills" "$FAKE_HOME/.gemini/config/skills"
[[ -f "${REPO_ROOT}/skills/${SKILLS[0]}/SKILL.md" ]] || fail "uninstall touched the source skills"
pass "global uninstall"

echo "All install.sh smoke tests passed (symlinks: $([[ $LINKS -eq 1 ]] && echo real || echo unavailable, copies checked))."
