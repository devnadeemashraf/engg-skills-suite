#!/usr/bin/env bash
# toolcheck.sh: report which toolchain tools are installed. Read-only: it never installs anything.
#
# Usage: toolcheck.sh [--json] [tool ...]
#   no tools named   report every known tool, exit 0
#   tools named      report those tools, exit 1 if any is missing or conflicting, 2 if a name is unknown
#
# Uses bash builtins only (plus each tool's own version command), so it runs on macOS, Linux, and Git Bash.
# Keep TOOLS in sync with toolcheck.ps1 (a test compares the two lists).
set -uo pipefail

usage() {
  cat <<'EOF'
Usage: toolcheck.sh [--json] [tool ...]
  no tools named   report every known tool, exit 0
  tools named      exit 1 if any is missing or conflicting, 2 if a name is unknown
Statuses: ok | missing | conflict (another program owns the command name)
EOF
}

# name|command alternatives (first found wins)|version argument|identity marker
# The identity marker, when set, must appear in the output; otherwise another program owns the name
# (OpenShift also installs `oc`; only-cli's `oc --help` names itself, and some versions lack --version).
TOOLS=(
  "git|git|--version|"
  "python|python3 python|--version|"
  "node|node|--version|"
  "uv|uv|--version|"
  "pipx|pipx|--version|"
  "go|go|version|"
  "cargo|cargo|--version|"
  "graphify|graphify|--version|"
  "rg|rg|--version|"
  "ast-grep|ast-grep sg|--version|"
  "scc|scc|--version|"
  "oc|oc|--help|only-cli"
  "archfit|archfit|--version|"
  "lizard|lizard|--version|"
  "opengrep|opengrep|--version|"
  "gitleaks|gitleaks|version|"
  "trufflehog|trufflehog|--version|"
  "osv-scanner|osv-scanner|--version|"
  "syft|syft|version|"
  "grype|grype|version|"
  "trivy|trivy|--version|"
  "scorecard|scorecard|version|"
  "actionlint|actionlint|--version|"
  "zizmor|zizmor|--version|"
  "hadolint|hadolint|--version|"
  "checkov|checkov|--version|"
  "lefthook|lefthook|version|"
  "pre-commit|pre-commit|--version|"
  "mise|mise|--version|"
)

JSON=0
REQUESTED=()
for arg in "$@"; do
  case "$arg" in
    --json) JSON=1 ;;
    -h|--help) usage; exit 0 ;;
    -*) echo "toolcheck: unknown option $arg" >&2; usage >&2; exit 2 ;;
    *) REQUESTED+=("$arg") ;;
  esac
done

lookup() {  # name -> prints the TOOLS entry, or returns 1
  local entry
  for entry in "${TOOLS[@]}"; do
    if [[ "${entry%%|*}" == "$1" ]]; then printf '%s' "$entry"; return 0; fi
  done
  return 1
}

json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"; s="${s//\"/\\\"}"; s="${s//$'\t'/ }"; s="${s//$'\r'/}"
  printf '%s' "$s"
}

# First non-empty line of a block of text. Builtins only.
first_line() {
  local line
  while IFS= read -r line; do
    line="${line//$'\r'/}"
    if [[ -n "${line// /}" ]]; then printf '%s' "$line"; return 0; fi
  done <<<"$1"
  return 1
}

if [[ ${#REQUESTED[@]} -gt 0 ]]; then
  NAMES=("${REQUESTED[@]}")
  for n in "${NAMES[@]}"; do
    lookup "$n" >/dev/null || { echo "toolcheck: unknown tool '$n' (see references/toolchain.md)" >&2; exit 2; }
  done
else
  NAMES=()
  for entry in "${TOOLS[@]}"; do NAMES+=("${entry%%|*}"); done
fi

missing=0
rows=()
for name in "${NAMES[@]}"; do
  IFS='|' read -r _ commands version_arg identity_marker <<<"$(lookup "$name")"
  status="missing"; version="-"; path="-"
  for cmd in $commands; do
    if found="$(command -v "$cmd" 2>/dev/null)"; then
      path="$found"
      status="ok"
      if out="$("$cmd" "$version_arg" 2>&1 </dev/null)"; then
        version="$(first_line "$out")" || version="unknown"
      else
        version="unknown"
      fi
      version="${version//|//}"
      # A tool with a known name clash must identify itself, or another program owns the command.
      if [[ -n "$identity_marker" && "$out" != *"$identity_marker"* ]]; then status="conflict"; fi
      break
    fi
  done
  [[ "$status" == "ok" ]] || missing=1
  rows+=("$name|$status|$version|$path")
done

if [[ "$JSON" -eq 1 ]]; then
  printf '['
  sep=""
  for row in "${rows[@]}"; do
    IFS='|' read -r name status version path <<<"$row"
    printf '%s{"tool":"%s","status":"%s","version":"%s","path":"%s"}' "$sep" \
      "$(json_escape "$name")" "$status" "$(json_escape "$version")" "$(json_escape "$path")"
    sep=","
  done
  printf ']\n'
else
  printf '%-12s %-9s %s\n' "TOOL" "STATUS" "VERSION"
  for row in "${rows[@]}"; do
    IFS='|' read -r name status version path <<<"$row"
    printf '%-12s %-9s %s\n' "$name" "$status" "$version"
  done
fi

if [[ ${#REQUESTED[@]} -gt 0 && "$missing" -eq 1 ]]; then exit 1; fi
exit 0
