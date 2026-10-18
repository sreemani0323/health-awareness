<#
.SYNOPSIS
    Runs the Angular frontend unit test suite.

.DESCRIPTION
    Executes all Vitest unit tests in the frontend directory with --watch=false.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$frontendDir = Join-Path $projectRoot "frontend"

if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
    Write-Error "Frontend directory not found at '$frontendDir'."
    exit 1
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Health Awareness - Angular Frontend Unit Test Suite" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Directory: $frontendDir" -ForegroundColor Gray
Write-Host "Runner:    Vitest (ng test --watch=false)" -ForegroundColor Gray
Write-Host "============================================================" -ForegroundColor Cyan

Set-Location $frontendDir
npx ng test --watch=false

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] All Angular frontend tests passed!" -ForegroundColor Green
} else {
    Write-Error "`n[FAILED] One or more Angular frontend tests failed."
    exit $LASTEXITCODE
}
