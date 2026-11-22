<#
.SYNOPSIS
  Reports which toolchain tools are installed. Read-only: it never installs anything.

.DESCRIPTION
  No tools named: report every known tool, exit 0.
  Tools named: exit 1 if any is missing or conflicting, 2 if a name is unknown.
  Statuses: ok | missing | conflict (another program owns the command name).
  Keep $Tools in sync with toolcheck.sh (a test compares the two lists).

.EXAMPLE
  .\toolcheck.ps1
.EXAMPLE
  .\toolcheck.ps1 graphify rg gitleaks -Json
#>
[CmdletBinding()]
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$Tool = @(),

  [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Name, command alternatives (first found wins), version argument, identity marker.
# The identity marker, when set, must appear in the output; otherwise another program owns the name
# (OpenShift also installs `oc`; only-cli's `oc --help` names itself, and some versions lack --version).
$Tools = @(
  @("git", "git", "--version", ""),
  @("python", "python3 python", "--version", ""),
  @("node", "node", "--version", ""),
  @("uv", "uv", "--version", ""),
  @("pipx", "pipx", "--version", ""),
  @("go", "go", "version", ""),
  @("cargo", "cargo", "--version", ""),
  @("graphify", "graphify", "--version", ""),
  @("rg", "rg", "--version", ""),
  @("ast-grep", "ast-grep sg", "--version", ""),
  @("scc", "scc", "--version", ""),
  @("oc", "oc", "--help", "only-cli"),
  @("archfit", "archfit", "--version", ""),
  @("lizard", "lizard", "--version", ""),
  @("opengrep", "opengrep", "--version", ""),
  @("gitleaks", "gitleaks", "version", ""),
  @("trufflehog", "trufflehog", "--version", ""),
  @("osv-scanner", "osv-scanner", "--version", ""),
  @("syft", "syft", "version", ""),
  @("grype", "grype", "version", ""),
  @("trivy", "trivy", "--version", ""),
  @("scorecard", "scorecard", "version", ""),
  @("actionlint", "actionlint", "--version", ""),
  @("zizmor", "zizmor", "--version", ""),
  @("hadolint", "hadolint", "--version", ""),
  @("checkov", "checkov", "--version", ""),
  @("lefthook", "lefthook", "version", ""),
  @("pre-commit", "pre-commit", "--version", ""),
  @("mise", "mise", "--version", "")
)

$byName = @{}
foreach ($t in $Tools) { $byName[$t[0]] = $t }

if ($Tool.Count -gt 0) {
  foreach ($n in $Tool) {
    if (-not $byName.ContainsKey($n)) {
      [Console]::Error.WriteLine("toolcheck: unknown tool '$n' (see references/toolchain.md)")
      exit 2
    }
  }
  $names = $Tool
} else {
  $names = @($Tools | ForEach-Object { $_[0] })
}

function Get-ToolStatus([object[]]$Entry) {
  $result = [ordered]@{ tool = $Entry[0]; status = "missing"; version = "-"; path = "-" }
  foreach ($cmd in ($Entry[1] -split " ")) {
    # Applications only: a PowerShell alias or function with the same name is not the tool.
    $found = Get-Command -Name $cmd -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $found) { continue }
    $result.path = $found.Source
    $result.status = "ok"
    $output = ""
    $version = "unknown"
    try {
      $lines = @(& $found.Source $Entry[2] 2>&1 | ForEach-Object { "$_" })
      $output = $lines -join "`n"
      if ($LASTEXITCODE -eq 0) {
        $first = $lines | Where-Object { $_.Trim() } | Select-Object -First 1
        if ($first) { $version = $first.Trim() }
      }
    } catch {
      $version = "unknown"
    }
    $result.version = $version
    # A tool with a known name clash must identify itself, or another program owns the command.
    if ($Entry[3] -and ($output -notlike "*$($Entry[3])*")) { $result.status = "conflict" }
    break
  }
  return [pscustomobject]$result
}

# Native tools writing to stderr must not become terminating errors here.
$ErrorActionPreference = "Continue"
$rows = @(foreach ($n in $names) { Get-ToolStatus $byName[$n] })
$ErrorActionPreference = "Stop"

if ($Json) {
  # -InputObject keeps a single row as an array; -Compress keeps it on one line.
  ConvertTo-Json -InputObject $rows -Compress
} else {
  "{0,-12} {1,-9} {2}" -f "TOOL", "STATUS", "VERSION"
  foreach ($r in $rows) { "{0,-12} {1,-9} {2}" -f $r.tool, $r.status, $r.version }
}

if ($Tool.Count -gt 0 -and @($rows | Where-Object { $_.status -ne "ok" }).Count -gt 0) { exit 1 }
exit 0
