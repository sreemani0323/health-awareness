<#
.SYNOPSIS
    Tests PostgreSQL 18 service status, connectivity, and database access for HealthAware.
#>

[CmdletBinding()]
param(
    [string]$DatabaseUrl = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$projectRoot = (Resolve-Path (Join-Path $scriptDir "..")).Path
$pythonExe = Join-Path $projectRoot "backend\.venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Backend virtual environment Python executable not found at '$pythonExe'."
    exit 1
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "HealthAware - PostgreSQL 18 Connectivity Verification" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Check Windows Service
$svc = Get-Service -Name "postgresql-x64-18" -ErrorAction SilentlyContinue
if ($svc) {
    Write-Host "[OK] Windows Service: $($svc.Name) - Status: $($svc.Status)" -ForegroundColor Green
} else {
    Write-Host "[INFO] Service 'postgresql-x64-18' not found by exact name. Checking for any PostgreSQL service..." -ForegroundColor Yellow
    Get-Service *postgres* | ForEach-Object {
        Write-Host "  Found Service: $($_.Name) - Status: $($_.Status)" -ForegroundColor Gray
    }
}

# Run Python-based verification with scoped PYTHONPATH
$verifyScript = Join-Path $projectRoot "backend\tests\verify_live_postgres_workflow.py"
if (Test-Path $verifyScript) {
    Write-Host "`nRunning full live workflow verification..." -ForegroundColor Cyan
    $origPythonPath = $env:PYTHONPATH
    try {
        if ($origPythonPath) {
            $env:PYTHONPATH = "$projectRoot;$origPythonPath"
        } else {
            $env:PYTHONPATH = $projectRoot
        }
        & $pythonExe $verifyScript
        $exitCode = $LASTEXITCODE
    } finally {
        $env:PYTHONPATH = $origPythonPath
    }

    if ($exitCode -eq 0) {
        Write-Host "`n[SUCCESS] PostgreSQL 18 connection and HealthAware workflows verified successfully." -ForegroundColor Green
    } else {
        Write-Host "`n[FAILED] PostgreSQL verification failed with exit code $exitCode." -ForegroundColor Red
    }
    exit $exitCode
} else {
    Write-Host "[WARNING] Live verification script not found at '$verifyScript'." -ForegroundColor Yellow
}
