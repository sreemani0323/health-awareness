<#
.SYNOPSIS
    Starts the local Google Cloud Firestore emulator in Datastore mode.

.DESCRIPTION
    Launches the local Datastore-mode emulator bound to a local loopback address (default: 127.0.0.1:8080).
    Checks that the port is free before starting, auto-detects existing local export metadata for data import,
    and configures automatic data export upon graceful shutdown.

.PARAMETER HostPort
    The host:port on which the emulator listens. Default is '127.0.0.1:8080'.

.PARAMETER PersistDir
    Directory path for export/import persistence. Default is 'local_db\datastore_export'.

.PARAMETER NoExport
    Switch to disable automatic export on shutdown.
#>

[CmdletBinding()]
param(
    [string]$HostPort = "127.0.0.1:8080",
    [string]$PersistDir = "local_db\datastore_export",
    [switch]$NoExport
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting Google Cloud Firestore Emulator in Datastore Mode" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Resolve gcloud executable
$gcloudCmd = Get-Command "gcloud.cmd" -ErrorAction SilentlyContinue
if (-not $gcloudCmd) {
    $standardPath = "C:\Users\nalli\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
    if (Test-Path $standardPath) {
        $env:Path = "C:\Users\nalli\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin;$env:Path"
        $gcloudCmd = Get-Command "gcloud.cmd" -ErrorAction SilentlyContinue
    }
}

if (-not $gcloudCmd) {
    Write-Error "Google Cloud CLI (gcloud) is not found in PATH or standard installation directory."
    exit 1
}

# 2. Check if the target port is already in use
$port = [int]($HostPort -split ":")[-1]
$activeConnection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
if ($activeConnection) {
    $procId = $activeConnection.OwningProcess | Select-Object -First 1
    $procName = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName
    Write-Error "Port $port is already occupied by process ID $procId ($procName). Refusing to start emulator to avoid port conflicts."
    exit 1
}

# 3. Resolve persistence directory and check for existing metadata
$resolvedPersistDir = (Resolve-Path -Path ".").Path + "\" + $PersistDir
if (-not (Test-Path $resolvedPersistDir)) {
    New-Item -ItemType Directory -Path $resolvedPersistDir -Force | Out-Null
}

$argsList = @(
    "emulators",
    "firestore",
    "start",
    "--database-mode=datastore-mode",
    "--host-port=$HostPort"
)

# Look for existing overall export metadata file for import (select latest by LastWriteTime)
$existingMetadata = Get-ChildItem -Path $resolvedPersistDir -Recurse -Filter "*.overall_export_metadata" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($existingMetadata) {
    Write-Host "[PERSISTENCE] Found previous export metadata at: $($existingMetadata.FullName)" -ForegroundColor Green
    Write-Host "[PERSISTENCE] Emulator will import existing database state." -ForegroundColor Green
    $argsList += "--import-data=$($existingMetadata.FullName)"
} else {
    Write-Host "[PERSISTENCE] No prior database export found. Starting clean database session." -ForegroundColor Yellow
}

if (-not $NoExport) {
    Write-Host "[PERSISTENCE] Export on exit configured to: $resolvedPersistDir" -ForegroundColor Green
    $argsList += "--export-on-exit=$resolvedPersistDir"
}

Write-Host "Binding endpoint: $HostPort" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to gracefully stop the emulator and export data." -ForegroundColor Yellow
Write-Host "------------------------------------------------------------" -ForegroundColor Gray

& gcloud.cmd @argsList
