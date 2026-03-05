# verify-completion.ps1 - Post-execution task checker (standalone version)
# Checks result-JSON and Acceptance criteria from SDD against git diff.
# Writes signal JSON: $TEMP/jefest-dispatch/verify-<project>.json
# Usage: verify-completion.ps1 -SddPath <path> [-ProjectPath <path>]
#
# Note: This standalone version does structural checks only (no Haiku AI grading).
# For AI-powered grading, see the full Jefest toolkit.

param(
    [Parameter(Mandatory=$true)]
    [string]$SddPath,

    [string]$ProjectPath = (Get-Location).Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

if (-not (Test-Path $SddPath)) {
    Write-Error "SDD file not found: $SddPath"
    exit 1
}

$projectName = Split-Path $ProjectPath -Leaf

# ── 1. Read SDD ──
$sddContent = [System.IO.File]::ReadAllText($SddPath, [System.Text.Encoding]::UTF8)

# ── 2. Check result-JSON exists ──
$signalDir = Join-Path $env:TEMP "jefest-dispatch"
$resultPath = Join-Path $signalDir "result-$projectName.json"
$resultExists = Test-Path $resultPath

$checks = @()
$passed = 0
$failed = 0

if ($resultExists) {
    $checks += @{ item = "result-$projectName.json exists"; status = "DONE" }
    $passed++

    try {
        $resultData = Get-Content $resultPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($resultData.status -eq "success") {
            $checks += @{ item = "result status=success"; status = "DONE" }
            $passed++
        } elseif ($resultData.status -eq "partial") {
            $checks += @{ item = "result status=partial (some tasks failed)"; status = "DONE" }
            $passed++
        } else {
            $checks += @{ item = "result status=$($resultData.status) (not success)"; status = "NOT_DONE" }
            $failed++
        }
    } catch {
        $checks += @{ item = "result-JSON is valid JSON"; status = "NOT_DONE" }
        $failed++
    }
} else {
    $checks += @{ item = "result-$projectName.json exists"; status = "NOT_DONE" }
    $failed++
    $checks += @{ item = "result status check (skipped — file missing)"; status = "NOT_DONE" }
    $failed++
}

# ── 3. Check git diff for changed files ──
try {
    $mergeBase = (git -C $ProjectPath merge-base HEAD master 2>$null).Trim()
    if ($mergeBase) {
        $filesChanged = (git -C $ProjectPath diff --name-only "$mergeBase" 2>$null) -join "`n"
    } else {
        $filesChanged = (git -C $ProjectPath diff --name-only HEAD~1 2>$null) -join "`n"
    }
} catch { $filesChanged = "" }

if ($filesChanged) {
    $checks += @{ item = "git diff shows changes from master"; status = "DONE" }
    $passed++
} else {
    $checks += @{ item = "git diff shows changes from master"; status = "NOT_DONE" }
    $failed++
}

# ── 4. Check Acceptance criteria (structural, keyword match) ──
$acceptanceMatch = [regex]::Match($sddContent, '(?ms)^##\s+Acceptance\s*\n(.+?)(?=^##|\Z)')
if ($acceptanceMatch.Success) {
    $acceptanceText = $acceptanceMatch.Groups[1].Value
    $criteriaLines = $acceptanceText -split "`n" | Where-Object { $_ -match '^\s*-\s+.+' } | ForEach-Object { $_.Trim() -replace '^\s*-\s+', '' }
    foreach ($criterion in $criteriaLines) {
        # Extract key nouns/paths from criterion for file matching
        $keyWords = $criterion -split '[\s,`]+' | Where-Object { $_.Length -gt 4 -and $_ -notmatch '^(should|must|have|with|that|this|from|into|does|does|file|each|all|any)$' }
        $matchFound = $false
        foreach ($word in $keyWords) {
            if ($filesChanged -match [regex]::Escape($word) -or $sddContent -match [regex]::Escape($word)) {
                $matchFound = $true
                break
            }
        }
        $status = if ($matchFound) { "DONE" } else { "UNCLEAR" }
        $checks += @{ item = $criterion; status = $status }
        if ($status -eq "DONE") { $passed++ } else { $failed++ }
    }
}

# ── 5. Determine overall status ──
$total = $passed + $failed
$ratio = if ($total -gt 0) { $passed / $total } else { 0 }
$overallStatus = if ($ratio -ge 1.0) { "verified" } elseif ($ratio -ge 0.5) { "partial" } else { "failed" }
$exitCode = if ($ratio -ge 1.0) { 0 } elseif ($ratio -ge 0.5) { 3 } else { 4 }

# ── 6. Write signal file ──
if (-not (Test-Path $signalDir)) { New-Item -ItemType Directory -Path $signalDir -Force | Out-Null }
$signalPath = Join-Path $signalDir "verify-$projectName.json"
@{
    project   = $projectName
    sdd       = $SddPath
    timestamp = (Get-Date -Format "o")
    status    = $overallStatus
    passed    = $passed
    failed    = $failed
    checks    = $checks
    exit_code = $exitCode
} | ConvertTo-Json -Depth 10 | Out-File $signalPath -Encoding UTF8

# ── 7. Print summary ──
Write-Host ""
Write-Host "[verify-completion] $projectName - $overallStatus ($passed/$total checks passed)" -ForegroundColor Cyan
foreach ($c in $checks) {
    $color = if ($c.status -eq "DONE") { "Green" } elseif ($c.status -eq "UNCLEAR") { "Yellow" } else { "Red" }
    Write-Host "  $($c.status)  $($c.item)" -ForegroundColor $color
}
Write-Host ""
Write-Host "  Signal: $signalPath" -ForegroundColor DarkGray
Write-Host ""

exit $exitCode
