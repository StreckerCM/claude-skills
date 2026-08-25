<#
.SYNOPSIS
    Install this repository's skills into the Claude Code configuration
    directory.

.DESCRIPTION
    Copies every directory under skills/ into ~/.claude/skills/, creating the
    target directory if it does not exist. Existing skills are replaced.

.PARAMETER Destination
    The Claude configuration directory. Defaults to ~/.claude.

.PARAMETER WhatIf
    Show what would be copied without copying anything.

.EXAMPLE
    ./install.ps1

.EXAMPLE
    ./install.ps1 -Destination C:\project\.claude
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Destination = (Join-Path $HOME '.claude')
)

$ErrorActionPreference = 'Stop'

$skillsSource = Join-Path $PSScriptRoot 'skills'

if (-not (Test-Path $skillsSource)) {
    throw "Source not found: $skillsSource. Run this script from the repository root."
}

$skills = Get-ChildItem -Path $skillsSource -Directory |
    Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }

if (-not $skills) {
    throw "No skills found under $skillsSource."
}

$skillsTarget = Join-Path $Destination 'skills'

if (-not (Test-Path $skillsTarget)) {
    if ($PSCmdlet.ShouldProcess($skillsTarget, 'Create directory')) {
        New-Item -ItemType Directory -Path $skillsTarget -Force | Out-Null
    }
}

foreach ($skill in $skills) {
    $target = Join-Path $skillsTarget $skill.Name
    if ($PSCmdlet.ShouldProcess($target, "Install $($skill.Name)")) {
        if (Test-Path $target) {
            Remove-Item -Path $target -Recurse -Force
        }
        Copy-Item -Path $skill.FullName -Destination $target -Recurse -Force
    }
}

Write-Output "Installed to $skillsTarget"
foreach ($skill in $skills) {
    Write-Output "  $($skill.Name)\"
}
Write-Output ""
Write-Output "Next: restart Claude Code if ~\.claude\skills\ did not exist before,"
Write-Output "then run /skills to confirm. No other activation is needed."
