$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $PSCommandPath

switch ([System.Runtime.InteropServices.RuntimeInformation]::OSDescription) {
    { $_ -match "Windows" } {
        Write-Host "Detected Windows" -ForegroundColor Cyan
        & (Join-Path $ScriptDir "build-windows.ps1")
    }
    { $_ -match "Darwin|macOS|OSX" } {
        Write-Host "Detected macOS" -ForegroundColor Cyan
        & "bash" (Join-Path $ScriptDir "build-macos.sh")
    }
    { $_ -match "Linux" } {
        Write-Host "Detected Linux" -ForegroundColor Cyan
        & "bash" (Join-Path $ScriptDir "build-linux.sh")
    }
    default {
        Write-Error "Unknown OS: $_"
        exit 1
    }
}
