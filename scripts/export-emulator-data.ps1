<#
.SYNOPSIS
    Exports data from a running Firestore emulator in Datastore mode.

.PARAMETER ExportDir
    Destination directory where the export data and metadata should be written.
    Default is 'local_db\datastore_export'.

.PARAMETER ProjectId
    Project identifier used with the local emulator. Default is 'health-awareness-local'.

.PARAMETER Port
    Port where the emulator is running. Default is 8080.
#>

[CmdletBinding()]
param(
    [string]$ExportDir = "local_db\datastore_export",
    [string]$ProjectId = "health-awareness-local",
    [int]$Port = 8080
)

$ErrorActionPreference = "Stop"

$resolvedExportDir = (Resolve-Path -Path ".").Path + "\" + $ExportDir
if (-not (Test-Path $resolvedExportDir)) {
    New-Item -ItemType Directory -Path $resolvedExportDir -Force | Out-Null
}

$url = "http://127.0.0.1:$Port/emulator/v1/projects/$ProjectId`:export"
$normalizedDir = $resolvedExportDir.Replace("\", "/")

# Datastore mode expects 'projects/<project>/databases/'
$payload = @{
    database = "projects/$ProjectId/databases/"
    export_directory = $normalizedDir
} | ConvertTo-Json

Write-Host "Triggering export to: $normalizedDir via $url" -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri $url -Method Post -Body $payload -ContentType "application/json"
    Write-Host "[SUCCESS] Datastore emulator data exported successfully." -ForegroundColor Green
    if ($response) {
        Write-Output $response
    }
} catch {
    Write-Error "Failed to export emulator data: $_"
    exit 1
}
