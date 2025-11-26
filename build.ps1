# PowerShell build script for creating a one-folder build using PyInstaller.
# Usage: Open PowerShell in repo root and run: .\build.ps1

param(
    [string]$SpecFile = 'build.spec'
)

Write-Host "Starting PyInstaller build (one-folder) using spec: $SpecFile"

# Ensure PyInstaller is available
$pyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyinstaller) {
    Write-Host "PyInstaller not found. Installing..."
    python -m pip install --user pyinstaller
}

# Run PyInstaller with the spec file
pyinstaller $SpecFile -y

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build completed. Output in dist\gui"
} else {
    Write-Host "Build failed with exit code $LASTEXITCODE"
}
