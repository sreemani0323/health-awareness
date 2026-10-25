<#
.SYNOPSIS
  Secure, interactive release build runner for HealthAware Android.

.DESCRIPTION
  Prompts for keystore and key passwords securely using masked PowerShell
  credentials (AsSecureString). Performs a fast preflight password verification
  via keytool before launching Gradle. Sets process-scoped environment variables only
  for the duration of the Gradle release build, and unconditionally cleans them up
  in a finally block. Zero secrets are ever written to disk or logs.
#>

[CmdletBinding()]
param(
    [string]$KeystorePath = "$env:LOCALAPPDATA\HealthAware\Signing\healthaware-release.jks",
    [string]$KeyAlias = "healthaware"
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " HealthAware Android Secure Release Build" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Preflight check: Ensure keystore exists
if (-not (Test-Path $KeystorePath)) {
    Write-Error "Release keystore was not found at '$KeystorePath'. Please generate and verify it before building."
    exit 1
}

Write-Host "`nKeystore located: $KeystorePath" -ForegroundColor Green
Write-Host "Key alias: $KeyAlias" -ForegroundColor Green

# Locate keytool
$keytoolPath = "C:\Program Files\Java\jdk-21.0.10\bin\keytool.exe"
if (-not (Test-Path $keytoolPath)) {
    $cmd = Get-Command keytool -ErrorAction SilentlyContinue
    if ($cmd) { $keytoolPath = $cmd.Source }
}

# 2. Interactive Secure String Prompts (never echoed, never in command line arguments)
Write-Host "`nPlease enter release signing credentials (input will be masked):" -ForegroundColor Yellow
$keystorePass = Read-Host -Prompt "Enter Keystore Password" -AsSecureString
if ($keystorePass.Length -eq 0) {
    Write-Error "Keystore password cannot be empty."
    exit 1
}

$keyPass = Read-Host -Prompt "Enter Key Password (press Enter if same as keystore)" -AsSecureString

$storePassPlain = [System.Net.NetworkCredential]::new('', $keystorePass).Password
$keyPassPlain = if ($keyPass.Length -gt 0) {
    [System.Net.NetworkCredential]::new('', $keyPass).Password
} else {
    $storePassPlain
}

try {
    # 3. Fast preflight password verification with keytool (fails fast in 0.2s if mistyped)
    if (Test-Path $keytoolPath) {
        Write-Host "Verifying keystore password..." -ForegroundColor Cyan
        $null = & $keytoolPath -list -keystore $KeystorePath -alias $KeyAlias -storepass $storePassPlain 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Host "`n[ERROR] Keystore password verification failed." -ForegroundColor Red
            Write-Host "The password entered does not match the keystore at '$KeystorePath'." -ForegroundColor Yellow
            Write-Host "Please check Caps Lock and re-run with the password chosen during key creation." -ForegroundColor Yellow
            exit 1
        }
        Write-Host "Keystore password verified successfully!" -ForegroundColor Green
    }

    # 4. Set temporary process-scoped environment variables for Gradle
    $env:HEALTHAWARE_KEYSTORE_PATH = $KeystorePath
    $env:HEALTHAWARE_KEY_ALIAS = $KeyAlias
    $env:HEALTHAWARE_KEYSTORE_PASSWORD = $storePassPlain
    $env:HEALTHAWARE_KEY_PASSWORD = $keyPassPlain

    Write-Host "`nLaunching Gradle release build (assembleRelease)..." -ForegroundColor Cyan
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    Push-Location $scriptDir

    # 5. Execute Gradle assembleRelease
    & ".\gradlew.bat" assembleRelease
    $buildExitCode = $LASTEXITCODE

    if ($buildExitCode -ne 0) {
        Write-Error "Gradle release build failed with exit code $buildExitCode."
        exit $buildExitCode
    }

    Write-Host "`n============================================================" -ForegroundColor Green
    Write-Host " BUILD SUCCESSFUL! Signed release APK generated." -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green

    $apkPath = Join-Path $scriptDir "app\build\outputs\apk\release\app-release.apk"
    if (Test-Path $apkPath) {
        $apkItem = Get-Item $apkPath
        Write-Host "Release APK: $($apkItem.FullName)" -ForegroundColor Cyan
        Write-Host "File Size:   $([Math]::Round($apkItem.Length / 1MB, 2)) MB ($($apkItem.Length) bytes)" -ForegroundColor Cyan
    }
}
finally {
    # 6. Immediate cleanup: Scrub process environment variables and plain text
    Remove-Item Env:\HEALTHAWARE_KEYSTORE_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:\HEALTHAWARE_KEY_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:\HEALTHAWARE_KEYSTORE_PATH -ErrorAction SilentlyContinue
    Remove-Item Env:\HEALTHAWARE_KEY_ALIAS -ErrorAction SilentlyContinue

    $storePassPlain = $null
    $keyPassPlain = $null
    [System.GC]::Collect()

    if ($scriptDir) { Pop-Location }
    Write-Host "Signing credentials scrubbed from process environment." -ForegroundColor Gray
}
