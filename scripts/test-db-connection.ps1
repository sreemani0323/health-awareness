<#
.SYNOPSIS
    Runs the Datastore emulator connectivity smoke test.

.PARAMETER HostPort
    The local host:port where the emulator is running. Default is '127.0.0.1:8080'.

.PARAMETER ProjectId
    The local development project ID. Default is 'health-awareness-local'.
#>

[CmdletBinding()]
param(
    [string]$HostPort = "127.0.0.1:8080",
    [string]$ProjectId = "health-awareness-local"
)

$ErrorActionPreference = "Stop"

$pythonExe = ".\backend\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error "Backend virtual environment Python executable not found at '$pythonExe'. Please run setup first."
    exit 1
}

$testScript = "backend\tests\test_datastore_smoke.py"
if (-not (Test-Path $testScript)) {
    Write-Error "Smoke test script '$testScript' not found."
    exit 1
}

$env:DATASTORE_EMULATOR_HOST = $HostPort
$env:DATASTORE_PROJECT_ID = $ProjectId

Write-Host "Running smoke test with:" -ForegroundColor Cyan
Write-Host "  DATASTORE_EMULATOR_HOST: $env:DATASTORE_EMULATOR_HOST" -ForegroundColor Gray
Write-Host "  DATASTORE_PROJECT_ID:    $env:DATASTORE_PROJECT_ID" -ForegroundColor Gray
Write-Host "------------------------------------------------------------" -ForegroundColor Gray

& $pythonExe $testScript
$testExitCode = $LASTEXITCODE

if ($testExitCode -eq 0) {
    Write-Host "[SUCCESS] Smoke test completed successfully." -ForegroundColor Green
} else {
    Write-Host "[FAILED] Smoke test failed with exit code $testExitCode." -ForegroundColor Red
}

exit $testExitCode
