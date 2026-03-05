# validate-sdd.ps1 - Structural SDD validator (standalone version)
# Checks SDD for required sections without requiring API key.
# Exits 0=PASS, non-zero=FAIL
# Usage: validate-sdd.ps1 -SddPath openspec/specs/my-task.md

param(
    [Parameter(Mandatory=$true)]
    [string]$SddPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if (-not (Test-Path $SddPath)) {
    Write-Error "SDD file not found: $SddPath"
    exit 1
}

# ── Read SDD ──
$sddContent = [System.IO.File]::ReadAllText($SddPath, [System.Text.Encoding]::UTF8)

$errors = @()
$checks = @()

# ── Check required sections ──
$requiredSections = @(
    @{ name = "Context";      pattern = '(?m)^##\s+Context' },
    @{ name = "Environment";  pattern = '(?m)^##\s+Environment' },
    @{ name = "Atomic Tasks"; pattern = '(?m)^##\s+Atomic Tasks' },
    @{ name = "Acceptance";   pattern = '(?m)^##\s+(Acceptance|Acceptance Criteria)' },
    @{ name = "Finalize";     pattern = '(?m)^##\s+Finalize' },
    @{ name = "Files";        pattern = '(?m)^##\s+Files' }
)

foreach ($section in $requiredSections) {
    if ($sddContent -match $section.pattern) {
        $checks += "[PASS] Has ## $($section.name) section"
    } else {
        $checks += "[FAIL] Missing ## $($section.name) section"
        $errors += "Missing ## $($section.name)"
    }
}

# ── Check Finalize has /exit ──
if ($sddContent -match '/exit') {
    $checks += "[PASS] Finalize contains /exit"
} else {
    $checks += "[FAIL] Finalize missing /exit step"
    $errors += "Finalize missing /exit"
}

# ── Check Finalize has result-JSON ──
if ($sddContent -match 'result-.*\.json') {
    $checks += "[PASS] Finalize has result-JSON step"
} else {
    $checks += "[FAIL] Finalize missing result-JSON step"
    $errors += "Finalize missing result-<project>.json step"
}

# ── Check Atomic Tasks is not empty ──
if ($sddContent -match '(?ms)^##\s+Atomic Tasks\s*\n+(\d+\.)') {
    $checks += "[PASS] Atomic Tasks has numbered steps"
} else {
    $checks += "[FAIL] Atomic Tasks section is empty or not numbered"
    $errors += "Atomic Tasks is empty"
}

# ── Check routing (SDD should be in project's openspec/specs/) ──
$sddAbsDir = [System.IO.Path]::GetDirectoryName([System.IO.Path]::GetFullPath($SddPath))
if ($sddContent -match '(?ms)##\s*Environment.*?path:\s*([^\n,\r]+)') {
    $expectedPath = $Matches[1].Trim().TrimEnd('\').TrimEnd('/')
    $expectedPathNorm = $expectedPath.Replace('/', '\').ToLowerInvariant()
    $sddDirNorm = $sddAbsDir.Replace('/', '\').ToLowerInvariant()
    if (-not $sddDirNorm.StartsWith($expectedPathNorm)) {
        $checks += "[FAIL] SDD routing mismatch: SDD is in $sddAbsDir but Environment.path is $expectedPath"
        $errors += "SDD should be in $expectedPath\openspec\specs\"
    } else {
        $checks += "[PASS] SDD location matches Environment.path"
    }
}

# ── Print results ──
Write-Host ""
Write-Host "[validate-sdd] Results for: $SddPath" -ForegroundColor Cyan
foreach ($check in $checks) {
    if ($check -match '^\[PASS\]') {
        Write-Host "  $check" -ForegroundColor Green
    } else {
        Write-Host "  $check" -ForegroundColor Red
    }
}
Write-Host ""

if ($errors.Count -gt 0) {
    Write-Host "[validate-sdd] FAILED - $($errors.Count) issue(s) found:" -ForegroundColor Red
    foreach ($err in $errors) {
        Write-Host "  - $err" -ForegroundColor Red
    }
    Write-Host ""
    exit 1
} else {
    Write-Host "[validate-sdd] PASSED - all structural checks OK." -ForegroundColor Green
    exit 0
}
