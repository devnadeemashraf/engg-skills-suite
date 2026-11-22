# Smoke tests for install.ps1 (Windows PowerShell 5.1 and PowerShell 7+).
# Runs against throwaway HOME and project directories.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$Installer = Join-Path $RepoRoot "install.ps1"
$Work = Join-Path ([IO.Path]::GetTempPath()) ("engg-smoke-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $Work | Out-Null

$Skills = @(Get-ChildItem -LiteralPath (Join-Path $RepoRoot "skills") -Directory | Select-Object -ExpandProperty Name)

function Assert-True([bool]$Condition, [string]$Message) {
  if (-not $Condition) { throw "FAIL: $Message" }
}

function Test-IsLink([string]$Path) {
  $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
  return ($null -ne $item) -and (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
}

function Invoke-Installer([hashtable]$Arguments) {
  # *> also silences Write-Host (information stream); errors still throw because of $ErrorActionPreference.
  & $Installer @Arguments *> $null
}

function Assert-Installed([string]$Canonical, [string]$Tool, [bool]$ExpectLinks) {
  foreach ($s in $Skills) {
    Assert-True (Test-Path -LiteralPath (Join-Path $Canonical "$s/SKILL.md")) "missing $Canonical/$s/SKILL.md"
    Assert-True (Test-Path -LiteralPath (Join-Path $Tool "$s/SKILL.md")) "missing $Tool/$s/SKILL.md"
    Assert-True ((Test-IsLink (Join-Path $Tool $s)) -eq $ExpectLinks) "$Tool/$s link state should be $ExpectLinks"
    Assert-True (-not (Test-IsLink (Join-Path $Canonical $s))) "canonical $Canonical/$s must be a real folder"
  }
}

function Assert-Removed([string[]]$Dirs) {
  foreach ($dir in $Dirs) {
    foreach ($s in $Skills) {
      $p = Join-Path $dir $s
      Assert-True (-not (Test-Path -LiteralPath $p) -and -not (Test-IsLink $p)) "$p still present after uninstall"
    }
  }
}

try {
  # --- argument errors ------------------------------------------------------
  $threw = $false
  try { Invoke-Installer @{ Scope = "Project" } } catch { $threw = $_.Exception.Message -like "*-ProjectPath is required*" }
  Assert-True $threw "-Scope Project without -ProjectPath should fail with a clear message"
  $threw = $false
  try { Invoke-Installer @{ Scope = "Project"; ProjectPath = (Join-Path $Work "missing") } } catch { $threw = $true }
  Assert-True $threw "missing project directory should fail"
  Write-Host "ok - argument errors"

  # --- project scope --------------------------------------------------------
  $proj = Join-Path $Work "proj"
  $foreign = Join-Path $proj ".claude/skills/someone-elses-skill"
  New-Item -ItemType Directory -Force -Path $foreign | Out-Null
  Invoke-Installer @{ Scope = "Project"; ProjectPath = $proj }
  Assert-Installed (Join-Path $proj ".agents/skills") (Join-Path $proj ".claude/skills") $true
  Write-Host "ok - project install"

  # Reinstall replaces the canonical folder and then removes the old link. If link removal followed
  # the link (the Windows PowerShell 5.1 junction hazard), the fresh canonical files would vanish.
  Invoke-Installer @{ Scope = "Project"; ProjectPath = $proj }
  Assert-Installed (Join-Path $proj ".agents/skills") (Join-Path $proj ".claude/skills") $true
  Write-Host "ok - project reinstall is idempotent and keeps link targets intact"

  Invoke-Installer @{ Scope = "Project"; ProjectPath = $proj; Uninstall = $true }
  Assert-Removed @((Join-Path $proj ".agents/skills"), (Join-Path $proj ".claude/skills"))
  Assert-True (Test-Path -LiteralPath $foreign) "uninstall removed a skill that is not part of the suite"
  Write-Host "ok - project uninstall leaves other skills alone"

  Invoke-Installer @{ Scope = "Project"; ProjectPath = $proj; Copy = $true }
  Assert-Installed (Join-Path $proj ".agents/skills") (Join-Path $proj ".claude/skills") $false
  Write-Host "ok - project -Copy"

  # Switching from copies back to links must replace the copied folders cleanly.
  Invoke-Installer @{ Scope = "Project"; ProjectPath = $proj }
  Assert-Installed (Join-Path $proj ".agents/skills") (Join-Path $proj ".claude/skills") $true
  Write-Host "ok - copies replaced by links"

  # --- dry run --------------------------------------------------------------
  $dry = Join-Path $Work "dry"
  New-Item -ItemType Directory -Path $dry | Out-Null
  Invoke-Installer @{ Scope = "Project"; ProjectPath = $dry; DryRun = $true }
  Assert-True (@(Get-ChildItem -LiteralPath $dry -Force).Count -eq 0) "-DryRun changed the project directory"
  Write-Host "ok - dry run changes nothing"

  # --- global scope (throwaway HOME) ----------------------------------------
  $fakeHome = Join-Path $Work "home"
  New-Item -ItemType Directory -Path $fakeHome | Out-Null
  Invoke-Installer @{ Scope = "Global"; HomeDir = $fakeHome }
  $canonical = Join-Path $fakeHome ".engg-skills-suite/skills"
  Assert-Installed $canonical (Join-Path $fakeHome ".claude/skills") $true
  Assert-Installed $canonical (Join-Path $fakeHome ".gemini/config/skills") $true
  Write-Host "ok - global install"

  Invoke-Installer @{ Scope = "Global"; HomeDir = $fakeHome; Uninstall = $true }
  Assert-Removed @($canonical, (Join-Path $fakeHome ".claude/skills"), (Join-Path $fakeHome ".gemini/config/skills"))
  Assert-True (Test-Path -LiteralPath (Join-Path $RepoRoot "skills/$($Skills[0])/SKILL.md")) "uninstall touched the source skills"
  Write-Host "ok - global uninstall"

  Write-Host "All install.ps1 smoke tests passed (PowerShell $($PSVersionTable.PSVersion))."
} finally {
  # Remove links first (non-recursively) so cleanup never follows them.
  Get-ChildItem -LiteralPath $Work -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 } |
    ForEach-Object { [IO.Directory]::Delete($_.FullName, $false) }
  Remove-Item -LiteralPath $Work -Recurse -Force -ErrorAction SilentlyContinue
}
