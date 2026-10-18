<#
.SYNOPSIS
    Stops the local Google Cloud Firestore emulator running on the specified port.

.PARAMETER Port
    The port number on which the emulator is listening. Default is 8080.
#>

[CmdletBinding()]
param(
    [int]$Port = 8080
)

$ErrorActionPreference = "Stop"

Write-Host "Checking for running emulator on port $Port..." -ForegroundColor Cyan

$connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if (-not $connections) {
    Write-Host "No active emulator found listening on port $Port." -ForegroundColor Yellow
    exit 0
}

$procIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique

foreach ($pidToStop in $procIds) {
    if ($pidToStop -eq 0 -or $pidToStop -eq 4) {
        continue
    }
    $proc = Get-Process -Id $pidToStop -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "Stopping emulator process PID: $pidToStop ($($proc.ProcessName))..." -ForegroundColor Yellow
        Stop-Process -Id $pidToStop -Force
        Write-Host "Process $pidToStop stopped." -ForegroundColor Green
    }
}

Start-Sleep -Seconds 1
$remaining = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if (-not $remaining) {
    Write-Host "Local Datastore emulator on port $Port has stopped successfully." -ForegroundColor Green
} else {
    Write-Warning "Port $Port is still occupied. You may need to inspect running tasks manually."
}
