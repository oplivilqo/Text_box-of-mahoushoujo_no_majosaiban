# Quick Build Script for Magic Girl Text Box
# Minimal output, maximum speed

$ErrorActionPreference = "Stop"

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if ($isAdmin) {
    Write-Host ""
    Write-Host "ERROR: Running as Administrator" -ForegroundColor Red
    Write-Host ""
    Write-Host "PyInstaller does not allow running as admin." -ForegroundColor Yellow
    Write-Host "Please close this window and open a normal PowerShell window." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Steps:" -ForegroundColor Cyan
    Write-Host "  1. Close this PowerShell window" -ForegroundColor White
    Write-Host "  2. Open PowerShell normally (without 'Run as Administrator')" -ForegroundColor White
    Write-Host "  3. Navigate to project directory" -ForegroundColor White
    Write-Host "  4. Run: .\build_quick.ps1" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host "Starting build..." -ForegroundColor Cyan

# Step 1: Clean old build files
Write-Host "Cleaning..." -ForegroundColor Gray
if (Test-Path "dist") { 
    Remove-Item "dist" -Recurse -Force -ErrorAction SilentlyContinue
}
if (Test-Path "build") { 
    Remove-Item "build" -Recurse -Force -ErrorAction SilentlyContinue
}

# Step 2: Run PyInstaller
Write-Host "Building..." -ForegroundColor Gray

$BuildSuccess = $false
try {
    & pyinstaller `
        --name=MagicGirlTextBox `
        --windowed `
        --onedir `
        --noconfirm `
        --clean `
        --noupx `
        --log-level=WARN `
        --hidden-import=PIL._tkinter_finder `
        --hidden-import=PIL.Image `
        --hidden-import=PIL.ImageDraw `
        --hidden-import=PIL.ImageFont `
        --hidden-import=win32clipboard `
        --hidden-import=win32con `
        --hidden-import=win32api `
        --hidden-import=win32gui `
        --hidden-import=win32process `
        --hidden-import=pywintypes `
        --hidden-import=keyboard `
        --hidden-import=pyperclip `
        --hidden-import=psutil `
        --collect-all=pilmoji `
        --collect-all=emoji `
        gui.py 2>&1 | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        $BuildSuccess = $true
    }
} catch {
    Write-Host "Build failed: $_" -ForegroundColor Red
    exit 1
}

if (-not $BuildSuccess) {
    Write-Host "Build failed with exit code: $LASTEXITCODE" -ForegroundColor Red
    exit 1
}

# Step 3: Copy assets
Write-Host "Copying assets..." -ForegroundColor Gray
if (Test-Path "dist\MagicGirlTextBox") {
    if (Test-Path "assets") {
        Copy-Item -Path "assets" -Destination "dist\MagicGirlTextBox\assets" -Recurse -Force
        Write-Host ""
        Write-Host "Build complete!" -ForegroundColor Green
        Write-Host "Output: dist\MagicGirlTextBox\MagicGirlTextBox.exe" -ForegroundColor White
    } else {
        Write-Host "Warning: assets folder not found" -ForegroundColor Yellow
        Write-Host "Build complete but assets missing!" -ForegroundColor Yellow
    }
} else {
    Write-Host "Build failed: output directory not found" -ForegroundColor Red
    exit 1
}
