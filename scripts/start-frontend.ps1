<#
.SYNOPSIS
    Starts the Angular frontend development server.

.DESCRIPTION
    Runs 'npm start' (ng serve) in the frontend directory.
    Serves the modern HealthAware SPA on http://127.0.0.1:4200.

.PARAMETER Port
    The local port for the dev server. Default: 4200.
#>

[CmdletBinding()]
param(
    [int]$Port = 4200
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir
$frontendDir = Join-Path $projectRoot "frontend"

if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
    Write-Error "Frontend directory not found at '$frontendDir'."
    exit 1
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Health Awareness - Angular Frontend Dev Server" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Directory: $frontendDir" -ForegroundColor Gray
Write-Host "Port:      $Port" -ForegroundColor Gray
Write-Host "URL:       http://localhost:$Port" -ForegroundColor Green
Write-Host "Press Ctrl+C to terminate the development server." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan

Set-Location $frontendDir
npm start -- --port $Port --host 127.0.0.1
