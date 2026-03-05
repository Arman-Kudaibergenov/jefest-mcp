# dispatch-lite.ps1 - Minimal SDD-first dispatcher (standalone version)
# Validates SDD, writes marker, opens new terminal tab with Claude Code.
# Usage: dispatch-lite.ps1 -ProjectPath <path> -SddPath <path> [-Model sonnet] [-Force] [-NewProject] [-Profile budget|balanced|quality]
#
# Requirements: Claude Code CLI installed and on PATH
# Optional: RLM integration (see comments marked "# Optional: RLM integration")

param(
    [Parameter(Mandatory=$true)]
    [string]$ProjectPath,

    [Parameter(Mandatory=$true)]
    [string]$SddPath,

    [string]$Model = "sonnet",
    [switch]$Force,
    [switch]$NewProject,
    [ValidateSet("budget","balanced","quality")]
    [string]$Profile = "balanced"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Find claude executable
$claudeExe = "claude"
$claudeLocal = Join-Path $env:USERPROFILE ".local\bin\claude.exe"
if (Test-Path $claudeLocal) { $claudeExe = $claudeLocal }

# ── 1. Validate paths ──
if (-not (Test-Path $ProjectPath)) {
    if (-not $NewProject) {
        Write-Error "ProjectPath does not exist: $ProjectPath (use -NewProject for new projects)"
        exit 1
    }
    Write-Host "[dispatch-lite] New project path - skipping existence check." -ForegroundColor Yellow
}

if (-not (Test-Path $SddPath)) {
    Write-Error "SDD file not found: $SddPath"
    exit 1
}

$projectName = Split-Path $ProjectPath -Leaf

# ── 2. SDD validation ──
if (-not $Force) {
    $validateScript = Join-Path $ScriptDir "validate-sdd.ps1"
    if (Test-Path $validateScript) {
        Write-Host "[dispatch-lite] Validating SDD..." -ForegroundColor Cyan
        & powershell.exe -NoProfile -File $validateScript -SddPath $SddPath
        $validateCode = $LASTEXITCODE
        if ($validateCode -ne 0) {
            Write-Error "SDD validation FAILED (code $validateCode). Fix or use -Force."
            exit $validateCode
        }
    } else {
        Write-Host "[dispatch-lite] validate-sdd.ps1 not found, skipping validation." -ForegroundColor Yellow
    }

    # Check SDD has result-JSON step
    $sddText = [System.IO.File]::ReadAllText($SddPath, [System.Text.Encoding]::UTF8)
    if ($sddText -notmatch 'result-.*\.json') {
        Write-Error "[dispatch-lite] SDD missing result-JSON step in Finalize. Add result-<project>.json write step. Use -Force to bypass."
        exit 9
    }
}

# ── 3. Setup lock dir ──
$lockDir = Join-Path $env:TEMP "jefest-dispatch"
if (-not (Test-Path $lockDir)) { New-Item -ItemType Directory -Path $lockDir -Force | Out-Null }

# Remove stale lock files (dead PIDs)
Get-ChildItem $lockDir -Filter "lock-*.json" -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $lockData = Get-Content $_.FullName -Encoding UTF8 | ConvertFrom-Json
        $lockPid = [int]$lockData.pid
        $proc = Get-Process -Id $lockPid -ErrorAction SilentlyContinue
        if ($null -eq $proc) {
            Remove-Item $_.FullName -Force
            Write-Host "[dispatch-lite] Cleaned stale lock: $($_.Name)" -ForegroundColor Yellow
        }
    } catch {
        Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    }
}

# Check if same project already has an active dispatch
$pidFilePath = Join-Path $lockDir "pid-$projectName.txt"
if ((Test-Path $pidFilePath) -and -not $Force) {
    try {
        $launcherPid = [int](Get-Content $pidFilePath -Encoding UTF8 -ErrorAction Stop)
        $launcherProc = Get-Process -Id $launcherPid -ErrorAction SilentlyContinue
        if ($null -ne $launcherProc) {
            Write-Error "[dispatch-lite] Project '$projectName' already has active dispatch (PID=$launcherPid). Use -Force to override."
            exit 2
        } else {
            Remove-Item $pidFilePath -Force -ErrorAction SilentlyContinue
        }
    } catch {
        Remove-Item $pidFilePath -Force -ErrorAction SilentlyContinue
    }
}

# ── 4. Apply Profile settings ──
if ($Profile -eq "budget") {
    $Model = "haiku"
    Write-Host "[dispatch-lite] Profile=budget: using model=haiku" -ForegroundColor Yellow
}

# ── 5. Write marker ──
$markerPath = Join-Path $lockDir "active-$projectName.json"
$markerData = @{
    projectPath = $ProjectPath
    sddPath     = $SddPath
    model       = $Model
    profile     = $Profile
    timestamp   = (Get-Date -Format "o")
    pid         = $PID
}
$markerData | ConvertTo-Json -Depth 5 | Out-File $markerPath -Encoding UTF8

# ── 6. Write task file ──
$sddAbsPath = (Resolve-Path $SddPath).Path
$taskFilePath = Join-Path $lockDir "task-$projectName.txt"
[System.IO.File]::WriteAllText($taskFilePath, "Read the SDD file at $sddAbsPath and execute ALL steps including Finalize section.", [System.Text.Encoding]::UTF8)

# ── 7. Read agent system prompt ──
$agentPromptPath = Join-Path $ScriptDir "agent-system-prompt.md"
$agentPrompt = ""
if (Test-Path $agentPromptPath) {
    $agentPrompt = [System.IO.File]::ReadAllText($agentPromptPath, [System.Text.Encoding]::UTF8)

    # Inject skills from SDD
    $skillsContent = ""
    $sddTextForSkills = [System.IO.File]::ReadAllText($SddPath, [System.Text.Encoding]::UTF8)
    if ($sddTextForSkills -match '(?m)^\s*-?\s*Skills:\s*(.+)$') {
        $skillNames = $Matches[1] -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
        $skillParts = @()
        foreach ($skillName in $skillNames) {
            # Look for skills in ~/.claude/skills/ or project .claude/skills/
            $globalSkillPath = Join-Path $env:USERPROFILE ".claude\skills\$skillName\SKILL.md"
            $localSkillPath = Join-Path $ProjectPath ".claude\skills\$skillName\SKILL.md"
            $skillPath = if (Test-Path $globalSkillPath) { $globalSkillPath } `
                         elseif (Test-Path $localSkillPath) { $localSkillPath } `
                         else { $null }
            if ($skillPath) {
                try {
                    $skillMd = [System.IO.File]::ReadAllText($skillPath, [System.Text.Encoding]::UTF8)
                    $skillParts += "### Skill: $skillName`n`n$skillMd"
                    Write-Host "[dispatch-lite] Loaded skill: $skillName" -ForegroundColor DarkGray
                } catch {
                    Write-Host "[dispatch-lite] Failed to load skill $skillName`: $_" -ForegroundColor Yellow
                }
            } else {
                Write-Host "[dispatch-lite] Skill not found: $skillName" -ForegroundColor Yellow
            }
        }
        $skillsContent = $skillParts -join "`n`n---`n`n"
    }
    $agentPrompt = $agentPrompt -replace '\{\{SKILLS_PLACEHOLDER\}\}', $skillsContent
    $agentPrompt = $agentPrompt -replace '\{\{KNOWN_ISSUES_PLACEHOLDER\}\}', ""

    # Optional: RLM integration — inject known issues from RLM here
    # Example: $knownIssues = Invoke-RestMethod -Uri "$rlmUrl/context?project=$projectName"
    # $agentPrompt = $agentPrompt -replace '\{\{KNOWN_ISSUES_PLACEHOLDER\}\}', $knownIssues
} else {
    Write-Host "[dispatch-lite] agent-system-prompt.md not found, launching without system prompt." -ForegroundColor Yellow
}

# ── 8. Launch Claude Code ──
$sddTitle = Split-Path $SddPath -Leaf
Write-Host "[dispatch-lite] Launching: $projectName | $sddTitle | model=$Model" -ForegroundColor Cyan

$launcherPath = Join-Path $lockDir "launcher-$projectName.ps1"
$escapedClaudeExe = $claudeExe.Replace("'","''")
$escapedTaskFile = $taskFilePath.Replace("'","''")
$escapedPidPath = $pidFilePath.Replace("'","''")

$launcherContent = @"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Remove-Item Env:CLAUDECODE -ErrorAction SilentlyContinue
`$env:JEFEST_PROJECT = '$projectName'
`$PID | Set-Content '$escapedPidPath' -Encoding UTF8
`$taskMsg = [System.IO.File]::ReadAllText('$escapedTaskFile', [System.Text.Encoding]::UTF8)
"@

if ($agentPrompt) {
    $tempPromptPath = Join-Path $lockDir "prompt-$projectName.md"
    [System.IO.File]::WriteAllText($tempPromptPath, $agentPrompt, [System.Text.Encoding]::UTF8)
    $escapedPromptPath = $tempPromptPath.Replace("'","''").Replace('\','\\')
    $launcherContent += @"

`$instruction = "CRITICAL: First read and follow ALL instructions from file '$escapedPromptPath'. Then execute: `$taskMsg"
& '$escapedClaudeExe' '--model' '$Model' '--permission-mode' 'bypassPermissions' `$instruction
"@
} else {
    $launcherContent += @"

& '$escapedClaudeExe' '--model' '$Model' '--permission-mode' 'bypassPermissions' `$taskMsg
"@
}

[System.IO.File]::WriteAllText($launcherPath, $launcherContent, [System.Text.Encoding]::UTF8)

# Launch in Windows Terminal if available, otherwise start new PowerShell window
if (Get-Command wt -ErrorAction SilentlyContinue) {
    wt new-tab -d "$ProjectPath" --title "dispatch: $projectName" -- powershell.exe -NoProfile -ExecutionPolicy Bypass -File $launcherPath
} else {
    Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File `"$launcherPath`"" -WorkingDirectory $ProjectPath
}

# Optional: RLM integration — log dispatch event
# Invoke-RestMethod -Uri "$rlmUrl/log" -Method Post -Body (@{ project=$projectName; event="dispatch_started" } | ConvertTo-Json)

Write-Host ""
Write-Host "[dispatch-lite] Dispatched:" -ForegroundColor Green
Write-Host "  Project : $ProjectPath"
Write-Host "  SDD     : $SddPath"
Write-Host "  Model   : $Model"
Write-Host "  Marker  : $markerPath"
Write-Host ""

exit 0
