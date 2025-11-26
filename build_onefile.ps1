# PowerShell script to build a single-file (onefile) executable using PyInstaller.
# Usage: Open PowerShell in repo root and run: .\build_onefile.ps1

param(
    [string]$SpecFile = 'build_onefile.spec'
)

Write-Host "Starting PyInstaller onefile build using spec: $SpecFile"

# Ensure PyInstaller is available
$pyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyinstaller) {
    Write-Host "PyInstaller not found. Installing..."
    python -m pip install --user pyinstaller
}

# Run PyInstaller with the spec file
pyinstaller $SpecFile -y

if ($LASTEXITCODE -eq 0) {
    Write-Host "Onefile build completed. Output exe located at dist\gui.exe"
} else {
    Write-Host "Build failed with exit code $LASTEXITCODE"
}
