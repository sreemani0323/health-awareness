<#
.SYNOPSIS
    Starts the Flask backend API server for the Health Awareness application.

.DESCRIPTION
    Runs the backend Flask development server bound to a local loopback address (default: 127.0.0.1:5000).
    Configures environment variables to direct all database traffic to the local Datastore emulator (127.0.0.1:8080).
    Prerequisite: The Datastore emulator must already be running via 'scripts/start-emulator.ps1'.

.PARAMETER Host
    The local address on which the API listens. Default: '127.0.0.1'.

.PARAMETER Port
    The local port on which the API listens. Default: 5000.

.PARAMETER EmulatorHost
    The local Datastore emulator host:port. Default: '127.0.0.1:8080'.

.PARAMETER ProjectId
    The local development project ID. Default: 'health-awareness-local'.
#>

[CmdletBinding()]
param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 5000,
    [string]$EmulatorHost = "127.0.0.1:8080",
    [string]$ProjectId = "health-awareness-local"
)

$ErrorActionPreference = "Stop"

# 1. Resolve Python executable in virtual environment
$pythonExe = ".\backend\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error "Backend virtual environment Python executable not found at '$pythonExe'. Please create it first."
    exit 1
}

# 2. Check if port is already occupied
$activeConnection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($activeConnection) {
    $procId = $activeConnection.OwningProcess | Select-Object -First 1
    $procName = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName
    Write-Error "Port $Port is already occupied by process ID $procId ($procName). Refusing to start backend."
    exit 1
}

# 3. Configure environment variables for safety and routing
$env:DATASTORE_EMULATOR_HOST = $EmulatorHost
$env:DATASTORE_PROJECT_ID = $ProjectId
$env:PYTHONPATH = (Resolve-Path ".").Path

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting Health Awareness Backend REST API Server" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "API Endpoint:            http://${ListenHost}:${Port}/api/v1" -ForegroundColor Green
Write-Host "Datastore Emulator Host: $env:DATASTORE_EMULATOR_HOST" -ForegroundColor Gray
Write-Host "Datastore Project ID:    $env:DATASTORE_PROJECT_ID" -ForegroundColor Gray
Write-Host "Python Interpreter:      $pythonExe" -ForegroundColor Gray
Write-Host "------------------------------------------------------------" -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop the backend server." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray

& $pythonExe -m backend.app
