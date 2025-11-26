# PowerShell script to build a single-file (onefile) executable using PyInstaller.
# Usage: Open PowerShell in repo root and run: .\build_onefile.ps1
# This script does NOT modify gui.spec or build.ps1.

param(
    [string]$Entry = 'gui.py'
)

Write-Host "Starting PyInstaller onefile build for $Entry"

# Ensure PyInstaller is available
$pyinstaller = Get-Command pyinstaller -ErrorAction SilentlyContinue
if (-not $pyinstaller) {
    Write-Host "PyInstaller not found. Installing..."
    python -m pip install --user pyinstaller
}

# Prepare --add-data arguments by scanning project directories for resource files
$excludeDirs = @('dist','build','__pycache__','.git','.venv')
$addDataArgs = @()

# Include font3.ttf if present
if (Test-Path -Path 'font3.ttf') {
    $addDataArgs += "--add-data `"font3.ttf;.`""
}

# Always include background folder if exists
if (Test-Path -Path 'background') {
    $addDataArgs += "--add-data `"background;background`""
}

# Include any top-level directories that contain image or font files (likely role folders)
Get-ChildItem -Directory | ForEach-Object {
    $name = $_.Name
    if ($excludeDirs -contains $name) { return }
    # look for image/font files inside
    $found = Get-ChildItem -Path $_.FullName -Recurse -File -Include *.png, *.jpg, *.jpeg, *.ttf -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) {
        # add as data; destination folder named same as source dir
        $src = $_.FullName
        $dest = $name
        # Use relative paths to avoid issues
        $relSrc = (Resolve-Path -Path $src).ProviderPath
        $addDataArgs += "--add-data `"$relSrc;$dest`""
    }
}

# Build the full pyinstaller command
$hidden = @('--hidden-import=keyboard','--hidden-import=pyperclip','--hidden-import=win32clipboard')
$common = @('--noconfirm','--clean','--onefile','--console')

$cmdParts = @('pyinstaller') + $common + $hidden + $addDataArgs + @($Entry)

Write-Host "Running:" ($cmdParts -join ' ')

$processInfo = New-Object System.Diagnostics.ProcessStartInfo
$processInfo.FileName = 'pyinstaller'
$processInfo.Arguments = ($common + $hidden + $addDataArgs + @($Entry)) -join ' '
$processInfo.UseShellExecute = $true
$processInfo.RedirectStandardOutput = $false
$processInfo.RedirectStandardError = $false

$proc = [System.Diagnostics.Process]::Start($processInfo)
$proc.WaitForExit()
if ($proc.ExitCode -eq 0) {
    Write-Host "Onefile build completed. Output exe located at dist\$([System.IO.Path]::GetFileNameWithoutExtension($Entry)).exe"
} else {
    Write-Host "Build failed with exit code $($proc.ExitCode)"
}
