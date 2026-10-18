<#
.SYNOPSIS
    Runs the backend test suite (unit, controller, and emulator integration tests).

.DESCRIPTION
    Executes unit tests and emulator-backed integration tests for the
    Health Awareness backend using pytest.  Ensures execution occurs
    strictly inside the Python 3.12 virtual environment and verifies
    loopback-only connectivity for integration tests.

.PARAMETER UnitOnly
    Switch to run only the unit tests (Domain validation + API controllers, no emulator required).

.PARAMETER IntegrationOnly
    Switch to run only emulator-backed storage & API integration tests.

.PARAMETER ApiOnly
    Switch to run only API tests (controller unit tests + API integration tests).

.PARAMETER HostPort
    The local host:port where the emulator is running. Default: '127.0.0.1:8080'.

.PARAMETER ProjectId
    The local development project ID. Default: 'health-awareness-local'.
#>

[CmdletBinding()]
param(
    [switch]$UnitOnly,
    [switch]$IntegrationOnly,
    [switch]$ApiOnly,
    [string]$HostPort = "127.0.0.1:8080",
    [string]$ProjectId = "health-awareness-local"
)

$ErrorActionPreference = "Stop"

# 1. Verify virtual environment Python
$pythonExe = ".\backend\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error "Backend virtual environment not found at '$pythonExe'. Please create it first."
    exit 1
}

# 2. Configure environment variables for safety
$env:DATASTORE_EMULATOR_HOST = $HostPort
$env:DATASTORE_PROJECT_ID = $ProjectId

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Health Awareness - Backend Test Suite Runner" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Python: $pythonExe" -ForegroundColor Gray
Write-Host "DATASTORE_EMULATOR_HOST: $env:DATASTORE_EMULATOR_HOST" -ForegroundColor Gray
Write-Host "DATASTORE_PROJECT_ID:    $env:DATASTORE_PROJECT_ID" -ForegroundColor Gray

# 3. Determine test targets
$testArgs = @("-m", "pytest")

if ($UnitOnly) {
    Write-Host "Mode: Unit tests only (Domain validation + Controller + Security + Concern tests)" -ForegroundColor Yellow
    $testArgs += "backend/tests/test_domain_validation.py"
    $testArgs += "backend/tests/test_api_controllers.py"
    $testArgs += "backend/tests/test_security.py"
    $testArgs += "backend/tests/test_concerns.py"
} elseif ($IntegrationOnly) {
    Write-Host "Mode: Integration tests only (Persistence + API + Admin + Creator Studio tests)" -ForegroundColor Yellow
    $testArgs += "backend/tests/test_integration.py"
    $testArgs += "backend/tests/test_api_integration.py"
    $testArgs += "backend/tests/test_admin.py"
    $testArgs += "backend/tests/test_creator_studio.py"
    $testArgs += "backend/tests/test_datastore_persistence.py"
    $testArgs += "backend/tests/test_datastore_smoke.py"
} elseif ($ApiOnly) {
    Write-Host "Mode: API tests only (Controller unit tests + API Integration tests + Concerns)" -ForegroundColor Yellow
    $testArgs += "backend/tests/test_api_controllers.py"
    $testArgs += "backend/tests/test_api_integration.py"
    $testArgs += "backend/tests/test_concerns.py"
} else {
    Write-Host "Mode: Full test suite (All Unit + All Integration + Security + Case Management)" -ForegroundColor Green
    $testArgs += "backend/tests"
}

Write-Host "------------------------------------------------------------" -ForegroundColor Gray

& $pythonExe @testArgs
$exitCode = $LASTEXITCODE

Write-Host "------------------------------------------------------------" -ForegroundColor Gray
if ($exitCode -eq 0) {
    Write-Host "[SUCCESS] All requested tests passed!" -ForegroundColor Green
} else {
    Write-Host "[FAILED] Test run failed with exit code $exitCode." -ForegroundColor Red
}

exit $exitCode
