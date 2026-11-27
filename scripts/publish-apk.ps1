<#
.SYNOPSIS
    HealthAware Automated Android Release & Web Distribution Script.

.DESCRIPTION
    1. Bumps/verifies version in build.gradle.
    2. Builds the cryptographically signed release APK using Gradle.
    3. Copies the release APK to frontend/public/download/healthaware-v{version}.apk.
    4. Computes exact byte size and SHA-256 cryptographic checksum.
    5. Updates frontend/public/download/version.json with the published release manifest.
    6. Rebuilds the Angular web bundle so the updated download portal is ready for deployment.

.PARAMETER KeystorePassword
    Password for the release keystore. If not provided and not generating new, prompts interactively.

.PARAMETER KeyPassword
    Password for the key alias. If omitted, uses KeystorePassword.

.PARAMETER GenerateNewKeystore
    Generates a fresh release keystore at %LOCALAPPDATA%\HealthAware\Signing\healthaware-release.jks.

.EXAMPLE
    .\scripts\publish-apk.ps1 -GenerateNewKeystore -KeystorePassword "MySecurePass123"
    .\scripts\publish-apk.ps1 -KeystorePassword "ExistingPass123"
#>

[CmdletBinding()]
param(
    [string]$KeystorePassword,
    [string]$KeyPassword,
    [switch]$GenerateNewKeystore,
    [string]$KeystorePath = "$env:LOCALAPPDATA\HealthAware\Signing\healthaware-release.jks",
    [string]$KeyAlias = "healthaware"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$FrontendDir = Join-Path $ProjectRoot "frontend"
$AndroidDir = Join-Path $FrontendDir "android"
$PublicDownloadDir = Join-Path $FrontendDir "public\download"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " HealthAware Android Release & Distribution Pipeline" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Locate keytool
$KeytoolPath = "C:\Program Files\Java\jdk-21.0.10\bin\keytool.exe"
if (-not (Test-Path $KeytoolPath)) {
    $cmd = Get-Command keytool -ErrorAction SilentlyContinue
    if ($cmd) { $KeytoolPath = $cmd.Source }
}

# 1. Handle Keystore Creation or Verification
$SigningDir = Split-Path -Parent $KeystorePath
if (-not (Test-Path $SigningDir)) {
    New-Item -ItemType Directory -Path $SigningDir -Force | Out-Null
}

if ($GenerateNewKeystore -or (-not (Test-Path $KeystorePath))) {
    if (-not $KeystorePassword) {
        $sec = Read-Host -Prompt "Enter password for NEW Release Keystore" -AsSecureString
        $KeystorePassword = [System.Net.NetworkCredential]::new('', $sec).Password
    }
    if (-not $KeyPassword) { $KeyPassword = $KeystorePassword }

    if (Test-Path $KeystorePath) {
        $backupPath = "$KeystorePath.bak-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Move-Item -Path $KeystorePath -Destination $backupPath -Force
        Write-Host "Existing keystore backed up to: $backupPath" -ForegroundColor Yellow
    }

    Write-Host "`nGenerating fresh 2048-bit RSA release keystore..." -ForegroundColor Cyan
    & $KeytoolPath -genkeypair -v `
        -keystore $KeystorePath `
        -alias $KeyAlias `
        -keyalg RSA `
        -keysize 2048 `
        -validity 10000 `
        -storepass $KeystorePassword `
        -keypass $KeyPassword `
        -dname "CN=HealthAware Release, OU=HealthAware, O=HealthAware, C=US"

    if ($LASTEXITCODE -ne 0) { throw "Keytool failed to generate release keystore." }
    Write-Host "Release keystore generated successfully at: $KeystorePath" -ForegroundColor Green
} else {
    if (-not $KeystorePassword) {
        $sec = Read-Host -Prompt "Enter Keystore Password for $KeystorePath" -AsSecureString
        $KeystorePassword = [System.Net.NetworkCredential]::new('', $sec).Password
    }
    if (-not $KeyPassword) { $KeyPassword = $KeystorePassword }

    # Fast preflight check
    Write-Host "`nVerifying keystore credentials..." -ForegroundColor Cyan
    $null = & $KeytoolPath -list -keystore $KeystorePath -alias $KeyAlias -storepass $KeystorePassword 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Keystore password verification failed. Please check password or use -GenerateNewKeystore."
    }
    Write-Host "Keystore credentials verified!" -ForegroundColor Green
}

# 2. Extract Version from build.gradle
$BuildGradle = Join-Path $AndroidDir "app\build.gradle"
$GradleContent = Get-Content $BuildGradle -Raw
$versionCodeMatch = [regex]::Match($GradleContent, 'versionCode\s+(\d+)')
$versionNameMatch = [regex]::Match($GradleContent, 'versionName\s+"([^"]+)"')

$VersionCode = if ($versionCodeMatch.Success) { [int]$versionCodeMatch.Groups[1].Value } else { 2 }
$VersionName = if ($versionNameMatch.Success) { $versionNameMatch.Groups[1].Value } else { "1.1" }

Write-Host "Target Release Version: v$VersionName (versionCode: $VersionCode)" -ForegroundColor Green

# 3. Synchronize Capacitor Assets
Write-Host "`n[1/4] Synchronizing Capacitor Android assets..." -ForegroundColor Yellow
Push-Location $FrontendDir
try {
    npx cap sync android
    if ($LASTEXITCODE -ne 0) { throw "Capacitor sync failed" }
} finally {
    Pop-Location
}

# 4. Compile Signed Release APK
Write-Host "`n[2/4] Compiling signed release APK via Gradle..." -ForegroundColor Yellow
try {
    $env:HEALTHAWARE_KEYSTORE_PATH = $KeystorePath
    $env:HEALTHAWARE_KEY_ALIAS = $KeyAlias
    $env:HEALTHAWARE_KEYSTORE_PASSWORD = $KeystorePassword
    $env:HEALTHAWARE_KEY_PASSWORD = $KeyPassword

    Push-Location $AndroidDir
    .\gradlew.bat assembleRelease
    if ($LASTEXITCODE -ne 0) { throw "Gradle assembleRelease failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
    Remove-Item Env:\HEALTHAWARE_KEYSTORE_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:\HEALTHAWARE_KEY_PASSWORD -ErrorAction SilentlyContinue
    Remove-Item Env:\HEALTHAWARE_KEYSTORE_PATH -ErrorAction SilentlyContinue
    Remove-Item Env:\HEALTHAWARE_KEY_ALIAS -ErrorAction SilentlyContinue
}

$BuiltApkPath = Join-Path $AndroidDir "app\build\outputs\apk\release\app-release.apk"
if (-not (Test-Path $BuiltApkPath)) {
    throw "Compiled APK not found at $BuiltApkPath"
}

# 5. Copy APK to Public Download Directory
Write-Host "`n[3/4] Packaging APK and computing cryptographic checksum..." -ForegroundColor Yellow
if (-not (Test-Path $PublicDownloadDir)) {
    New-Item -ItemType Directory -Path $PublicDownloadDir -Force | Out-Null
}

$TargetFileName = "healthaware-v$VersionName.apk"
$TargetApkPath = Join-Path $PublicDownloadDir $TargetFileName
Copy-Item -Path $BuiltApkPath -Destination $TargetApkPath -Force

$FileItem = Get-Item $TargetApkPath
$FileSizeBytes = $FileItem.Length
$FileSizeMb = [math]::Round(($FileSizeBytes / 1MB), 1)
$FileSizeFormatted = "$FileSizeMb MB"
$Sha256Hash = (Get-FileHash -Path $TargetApkPath -Algorithm SHA256).Hash.ToUpper()
$ReleaseDate = (Get-Date).ToString("yyyy-MM-dd")

Write-Host "APK File:      $TargetFileName" -ForegroundColor Cyan
Write-Host "File Size:     $FileSizeFormatted ($FileSizeBytes bytes)" -ForegroundColor Cyan
Write-Host "SHA-256 Hash:  $Sha256Hash" -ForegroundColor Cyan

# 6. Update version.json Release Manifest
$ManifestJson = @{
    applicationId = "org.healthaware.app"
    appName = "HealthAware"
    versionName = $VersionName
    versionCode = $VersionCode
    minAndroidVersion = "Android 7.0 (API 24)"
    targetAndroidVersion = "Android 16 (API 36)"
    fileName = $TargetFileName
    downloadUrl = "/download/$TargetFileName"
    fileSizeBytes = $FileSizeBytes
    fileSizeFormatted = $FileSizeFormatted
    sha256 = $Sha256Hash
    releaseDate = $ReleaseDate
    isAvailable = $true
    status = "published"
    statusMessage = "Official signed release build v$VersionName is verified and available for direct download."
    requiresManualPermission = $true
} | ConvertTo-Json -Depth 4

$ManifestPath = Join-Path $PublicDownloadDir "version.json"
[System.IO.File]::WriteAllText($ManifestPath, $ManifestJson, [System.Text.Encoding]::UTF8)
Write-Host "Updated release manifest: $ManifestPath" -ForegroundColor Green

# 7. Rebuild Angular Web Distribution
Write-Host "`n[4/4] Rebuilding Angular production bundle..." -ForegroundColor Yellow
Push-Location $FrontendDir
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Angular build failed" }
    Write-Host "Angular distribution rebuilt successfully." -ForegroundColor Green
} finally {
    Pop-Location
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " SUCCESS: HealthAware v$VersionName is packaged & ready!" -ForegroundColor Green
Write-Host " Run 'git commit -am' and 'git push' to deploy to Cloudflare Pages." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
