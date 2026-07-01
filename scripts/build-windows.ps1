param(
    [string]$Version = "1.0.2"
)

$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $PSScriptRoot
$DistDir = Join-Path $ProjectDir "dist"

Write-Host "=== Building SoundVault.exe with PyInstaller ===" -ForegroundColor Cyan
Set-Location $ProjectDir
python -m PyInstaller SoundVault.spec --noconfirm
if (-not (Test-Path (Join-Path $DistDir "SoundVault.exe"))) {
    Write-Error "SoundVault.exe not found in dist/"
    exit 1
}
Write-Host "OK - dist/SoundVault.exe" -ForegroundColor Green

Write-Host "=== Building NSIS Installer ===" -ForegroundColor Cyan
$makensis = Get-Command "makensis" -ErrorAction SilentlyContinue
if ($makensis) {
    $nsiPath = Join-Path $ProjectDir "installer\installer.nsi"
    & "makensis" $nsiPath
    if (Test-Path (Join-Path $ProjectDir "installer\SoundVault_Setup.exe")) {
        Move-Item -Force (Join-Path $ProjectDir "installer\SoundVault_Setup.exe") (Join-Path $DistDir "SoundVault_Setup.exe")
        Write-Host "OK - dist/SoundVault_Setup.exe" -ForegroundColor Green
    }
} else {
    Write-Host "NSIS (makensis) not found, skipping installer build" -ForegroundColor Yellow
}

Write-Host "=== Building MSI Installer ===" -ForegroundColor Cyan
$candle = Get-Command "candle" -ErrorAction SilentlyContinue
$light = Get-Command "light" -ErrorAction SilentlyContinue
if ($candle -and $light) {
    $wxsPath = Join-Path $ProjectDir "installer\installer.wxs"
    $wixobjPath = Join-Path $ProjectDir "installer\installer.wixobj"
    & candle $wxsPath -o $wixobjPath
    & light $wixobjPath -o (Join-Path $DistDir "SoundVault.msi")
    Write-Host "OK - dist/SoundVault.msi" -ForegroundColor Green
} else {
    Write-Host "WiX Toolset (candle/light) not found, skipping MSI build" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Build complete ===" -ForegroundColor Cyan
Get-ChildItem $DistDir | Select-Object Name, Length | Format-Table -AutoSize
