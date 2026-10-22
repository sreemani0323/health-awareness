<#
.SYNOPSIS
    HealthAware Android Build & Sync Automation Script
.DESCRIPTION
    Builds the Angular frontend bundle, syncs assets into Capacitor Android,
    and optionally builds the debug APK or launches Android Studio.
.PARAMETER SkipWeb
    Skip building Angular production distribution. Default: $false
.PARAMETER SkipSync
    Skip synchronizing Capacitor assets and plugins. Default: $false
.PARAMETER SkipApk
    Skip compiling Android debug APK via Gradle. Default: $false
.PARAMETER OpenStudio
    Open the Android project in Android Studio. Default: $false
.PARAMETER Install
    Install the built debug APK onto a connected Android device or emulator. Default: $false
.EXAMPLE
    .\scripts\build-android.ps1
    .\scripts\build-android.ps1 -SkipWeb -SkipSync
    .\scripts\build-android.ps1 -OpenStudio
    .\scripts\build-android.ps1 -Install
#>
[CmdletBinding()]
param(
    [switch]$SkipWeb,
    [switch]$SkipSync,
    [switch]$SkipApk,
    [switch]$OpenStudio,
    [switch]$Install
)

$BuildWeb = -not $SkipWeb
$Sync = -not $SkipSync
$BuildApk = -not $SkipApk

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$FrontendDir = Join-Path $ProjectRoot "frontend"
$AndroidDir = Join-Path $FrontendDir "android"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " HealthAware Android Build & Sync Pipeline" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Check & Configure Environment
if (-not $env:ANDROID_HOME) {
    $DefaultSdk = "$env:LOCALAPPDATA\Android\Sdk"
    if (Test-Path $DefaultSdk) {
        $env:ANDROID_HOME = $DefaultSdk
        Write-Host "Configured ANDROID_HOME -> $DefaultSdk" -ForegroundColor Green
    } else {
        Write-Warning "ANDROID_HOME is not set and default SDK not found."
    }
}

if (-not $env:JAVA_HOME) {
    $PotentialJdk = "C:\Program Files\Java\jdk-21.0.10"
    if (Test-Path $PotentialJdk) {
        $env:JAVA_HOME = $PotentialJdk
        Write-Host "Configured JAVA_HOME -> $PotentialJdk" -ForegroundColor Green
    }
}

# 2. Build Angular Frontend
if ($BuildWeb) {
    Write-Host "`n[1/4] Building Angular frontend distribution..." -ForegroundColor Yellow
    Push-Location $FrontendDir
    try {
        npx ng build
        if ($LASTEXITCODE -ne 0) { throw "Angular build failed with exit code $LASTEXITCODE" }
        Write-Host "Angular build complete." -ForegroundColor Green
    } finally {
        Pop-Location
    }
}

# 3. Synchronize Capacitor Assets
if ($Sync) {
    Write-Host "`n[2/4] Synchronizing Capacitor Android assets & plugins..." -ForegroundColor Yellow
    Push-Location $FrontendDir
    try {
        npx cap sync android
        if ($LASTEXITCODE -ne 0) { throw "Capacitor sync failed with exit code $LASTEXITCODE" }
        Write-Host "Capacitor synchronization complete." -ForegroundColor Green
    } finally {
        Pop-Location
    }
}

# 4. Build Debug APK
if ($BuildApk) {
    Write-Host "`n[3/4] Assembling Android debug APK via Gradle..." -ForegroundColor Yellow
    Push-Location $AndroidDir
    try {
        .\gradlew.bat assembleDebug
        if ($LASTEXITCODE -ne 0) { throw "Gradle assembleDebug failed with exit code $LASTEXITCODE" }
        $ApkPath = Join-Path $AndroidDir "app\build\outputs\apk\debug\app-debug.apk"
        if (Test-Path $ApkPath) {
            $ApkSize = [math]::Round(((Get-Item $ApkPath).Length / 1MB), 2)
            Write-Host "Debug APK built successfully: $ApkPath ($ApkSize MB)" -ForegroundColor Green
        }
    } finally {
        Pop-Location
    }
}

# 5. Open in Android Studio (if requested)
if ($OpenStudio) {
    Write-Host "`nOpening Android Studio..." -ForegroundColor Yellow
    Push-Location $FrontendDir
    try {
        npx cap open android
    } finally {
        Pop-Location
    }
}

# 6. Install to connected device or emulator (if requested)
if ($Install) {
    Write-Host "`n[4/4] Checking for connected devices/emulators..." -ForegroundColor Yellow
    $Adb = Join-Path $env:ANDROID_HOME "platform-tools\adb.exe"
    if (Test-Path $Adb) {
        $Devices = & $Adb devices | Select-String "device$"
        if ($Devices) {
            $ApkPath = Join-Path $AndroidDir "app\build\outputs\apk\debug\app-debug.apk"
            Write-Host "Installing APK onto connected target..." -ForegroundColor Cyan
            & $Adb install -r $ApkPath
            Write-Host "APK installed successfully! Launching HealthAware..." -ForegroundColor Green
            & $Adb shell am start -n org.healthaware.app/.MainActivity
        } else {
            Write-Warning "No connected Android devices or emulators found. Start an emulator or connect a device with USB debugging enabled."
        }
    } else {
        Write-Warning "adb.exe not found at $Adb"
    }
}

Write-Host "`n======================================================" -ForegroundColor Cyan
Write-Host " Pipeline Finished Successfully" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
