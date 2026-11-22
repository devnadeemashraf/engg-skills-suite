<#
.SYNOPSIS
  Installs the Unified Engineering Skills Suite (Windows PowerShell 5.1+ and PowerShell 7+).

.DESCRIPTION
  Global scope:  canonical copy in ~/.engg-skills-suite/skills, linked into
                 ~/.claude/skills (Claude Code; Cursor and Copilot read it too), ~/.codex/skills (Codex)
                 and ~/.gemini/config/skills (Antigravity CLI & IDE).
  Project scope: canonical copy in <repo>/.agents/skills (open standard: Antigravity, Codex,
                 Cursor, Copilot), linked into <repo>/.claude/skills and <repo>/.codex/skills.

  Links are symbolic links when allowed (Developer Mode or admin), otherwise directory junctions,
  which need no special rights. Use -Copy to copy files instead.

.EXAMPLE
  .\install.ps1 -Scope Global
.EXAMPLE
  .\install.ps1 -Scope Project -ProjectPath "C:\work\my-repo"
.EXAMPLE
  .\install.ps1 -Scope Project -ProjectPath "C:\work\my-repo" -Uninstall -DryRun
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [ValidateSet("Global", "Project")]
  [string]$Scope,

  [string]$ProjectPath = "",

  # Home directory for -Scope Global (defaults to your profile; useful for testing or other users).
  [string]$HomeDir = $HOME,

  # Copy files instead of linking.
  [switch]$Copy,

  # Remove only the skills that ship with this suite; other skills are untouched.
  [switch]$Uninstall,

  # Print what would happen without changing anything.
  [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SrcSkills = Join-Path $PSScriptRoot "skills"
if (-not (Test-Path -LiteralPath $SrcSkills -PathType Container)) {
  throw "Skills directory not found next to this script: $SrcSkills"
}

$Skills = @(Get-ChildItem -LiteralPath $SrcSkills -Directory |
  Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName "SKILL.md") -PathType Leaf } |
  Select-Object -ExpandProperty Name)
if ($Skills.Count -eq 0) { throw "No skills found in $SrcSkills" }

function Write-Step([string]$Message) {
  Write-Host "+ $Message"
}

function Test-IsLink([string]$Path) {
  $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
  return ($null -ne $item) -and (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
}

# Removes a previous install entry. Links are deleted non-recursively: in Windows PowerShell 5.1,
# Remove-Item -Recurse on a junction can delete the contents of the folder it points to.
function Remove-InstallEntry([string]$Path) {
  if (-not (Test-Path -LiteralPath $Path) -and -not (Test-IsLink $Path)) { return }
  Write-Step "remove $Path"
  if ($DryRun) { return }
  if (Test-IsLink $Path) {
    [IO.Directory]::Delete($Path, $false)
  } else {
    Remove-Item -LiteralPath $Path -Recurse -Force
  }
}

function New-InstallDir([string]$Path) {
  if (Test-Path -LiteralPath $Path -PathType Container) { return }
  Write-Step "mkdir $Path"
  if (-not $DryRun) { New-Item -ItemType Directory -Force -Path $Path | Out-Null }
}

function Copy-SkillFolder([string]$Source, [string]$Dest) {
  Write-Step "copy $Source -> $Dest"
  if (-not $DryRun) { Copy-Item -LiteralPath $Source -Destination $Dest -Recurse -Force }
}

# Links Dest to Source: a symbolic link if permitted, otherwise a junction (absolute path).
function New-SkillLink([string]$Source, [string]$Dest, [string]$RelativeTarget, [bool]$AsCopy) {
  if ($AsCopy) { Copy-SkillFolder $Source $Dest; return }
  $target = $Source
  if ($RelativeTarget) { $target = $RelativeTarget }
  Write-Step "link $Dest -> $target"
  if ($DryRun) { return }
  try {
    if ($RelativeTarget) {
      # New-Item resolves relative targets against the current directory, so resolve from Dest's parent.
      Push-Location (Split-Path -Parent $Dest)
      try { New-Item -ItemType SymbolicLink -Path $Dest -Target $RelativeTarget -ErrorAction Stop | Out-Null }
      finally { Pop-Location }
    } else {
      New-Item -ItemType SymbolicLink -Path $Dest -Target $Source -ErrorAction Stop | Out-Null
    }
  } catch {
    if (-not $IsWindowsHost) { throw }
    Write-Host "  symlink not permitted; using a directory junction instead"
    New-Item -ItemType Junction -Path $Dest -Target $Source -ErrorAction Stop | Out-Null
  }
}

# $IsWindows exists only in PowerShell 6+; Windows PowerShell 5.1 always runs on Windows.
$IsWindowsHost = ($PSVersionTable.PSEdition -eq "Desktop") -or ((Get-Variable IsWindows -ValueOnly -ErrorAction SilentlyContinue) -eq $true)

if ($Scope -eq "Global") {
  if (-not (Test-Path -LiteralPath $HomeDir -PathType Container)) { throw "Home directory does not exist: $HomeDir" }
  $CanonicalDir = Join-Path $HomeDir ".engg-skills-suite/skills"
  $ToolDirs = @((Join-Path $HomeDir ".claude/skills"), (Join-Path $HomeDir ".codex/skills"), (Join-Path $HomeDir ".gemini/config/skills"))
  $UseRelative = $false
} else {
  if (-not $ProjectPath) { throw "-ProjectPath is required with -Scope Project." }
  if (-not (Test-Path -LiteralPath $ProjectPath -PathType Container)) {
    throw "Project directory does not exist: $ProjectPath"
  }
  $ProjectAbs = (Resolve-Path -LiteralPath $ProjectPath).ProviderPath
  $CanonicalDir = Join-Path $ProjectAbs ".agents/skills"
  $ToolDirs = @((Join-Path $ProjectAbs ".claude/skills"), (Join-Path $ProjectAbs ".codex/skills"))
  $UseRelative = $true
}

if ($Uninstall) {
  foreach ($skill in $Skills) {
    foreach ($dir in $ToolDirs) { Remove-InstallEntry (Join-Path $dir $skill) }
    Remove-InstallEntry (Join-Path $CanonicalDir $skill)
    Write-Host "Removed: $skill"
  }
  Write-Host "Done. Uninstalled $($Skills.Count) skills ($Scope scope)."
  return
}

New-InstallDir $CanonicalDir
foreach ($dir in $ToolDirs) { New-InstallDir $dir }

foreach ($skill in $Skills) {
  $canonical = Join-Path $CanonicalDir $skill
  Remove-InstallEntry $canonical
  Copy-SkillFolder (Join-Path $SrcSkills $skill) $canonical
  foreach ($dir in $ToolDirs) {
    $dest = Join-Path $dir $skill
    Remove-InstallEntry $dest
    $relative = $null
    # Platform separator: Windows symlinks with "/" in a relative target do not resolve reliably.
    if ($UseRelative) { $relative = [IO.Path]::Combine("..", "..", ".agents", "skills", $skill) }
    New-SkillLink -Source $canonical -Dest $dest -RelativeTarget $relative -AsCopy $Copy.IsPresent
  }
  Write-Host "Installed: $skill"
}

Write-Host ""
Write-Host "Done. Installed $($Skills.Count) skills ($Scope scope)."
Write-Host "  Canonical store: $CanonicalDir"
foreach ($dir in $ToolDirs) { Write-Host "  Linked into:     $dir" }
if ($DryRun) { Write-Host "(dry run: nothing was changed)" }
