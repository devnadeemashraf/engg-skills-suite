<#
.SYNOPSIS
  Installs the Unified Engineering Skills Suite for Claude Code CLI, Antigravity CLI, and Antigravity IDE.
.EXAMPLE
  .\install.ps1 -Scope Global
  .\install.ps1 -Scope Project -ProjectPath "C:\work\my-repo"
#>
param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("Global", "Project")]
  [string]$Scope,

  [string]$ProjectPath = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcSkills = Join-Path $ScriptDir "skills"

function Copy-SkillFolder($Source, $Dest) {
  if (Test-Path $Dest) { Remove-Item -Recurse -Force $Dest }
  Copy-Item -Recurse -Force $Source $Dest
}

if ($Scope -eq "Global") {
  $AgyGlobal = Join-Path $HOME ".gemini\config\skills"
  $ClaudeGlobal = Join-Path $HOME ".claude\skills"
  New-Item -ItemType Directory -Force -Path $AgyGlobal, $ClaudeGlobal | Out-Null

  Get-ChildItem -Directory $SrcSkills | ForEach-Object {
    Copy-SkillFolder $_.FullName (Join-Path $AgyGlobal $_.Name)
    Copy-SkillFolder $_.FullName (Join-Path $ClaudeGlobal $_.Name)
    Write-Host "Installed global skill: $($_.Name)"
  }
  Write-Host "`nInstalled globally to:`n  - $AgyGlobal (Antigravity IDE & CLI)`n  - $ClaudeGlobal (Claude Code CLI)"
} else {
  if (-not $ProjectPath -or -not (Test-Path $ProjectPath)) {
    throw "Provide an existing -ProjectPath when using -Scope Project."
  }
  $AgentsDir = Join-Path $ProjectPath ".agents\skills"
  $ClaudeDir = Join-Path $ProjectPath ".claude\skills"
  New-Item -ItemType Directory -Force -Path $AgentsDir, $ClaudeDir | Out-Null

  Get-ChildItem -Directory $SrcSkills | ForEach-Object {
    Copy-SkillFolder $_.FullName (Join-Path $AgentsDir $_.Name)
    Copy-SkillFolder $_.FullName (Join-Path $ClaudeDir $_.Name)
    Write-Host "Installed project skill: $($_.Name)"
  }
  Write-Host "`nInstalled project skills to:`n  - $AgentsDir (Antigravity IDE & CLI, Codex, Cursor, Copilot)`n  - $ClaudeDir (Claude Code CLI)"
}
