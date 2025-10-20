<#
.SYNOPSIS
    Build script for Sigma Auto Clicker.
.DESCRIPTION
    Automates setup, formatting, packaging, and validation of the Sigma Auto Clicker application.
    Supports dependency installation, code formatting, PyInstaller packaging, and execution for Windows.
.PARAMETER Debug
    Retains temporary files (e.g., .spec, build folders) for debugging.
.PARAMETER Run
    Runs the compiled executable after building.
.PARAMETER Arguments
    Arguments to pass to the executable when running.
#>

param (
    [switch]$Debug,
    [switch]$Run,
    [string]$Arguments
)

# Configuration
$Config = @{
    ScriptName       = "autoclicker.py"
    VersionFile      = "VERSION.txt"
    WorkingDir       = $PSScriptRoot
    MinPythonVersion = "3.11"
    VenvDir          = Join-Path $PSScriptRoot "AutoClickerPY"
    Dependencies     = @("keyboard", "mouse", "Pillow", "pyautogui", "colorama", "requests", "psutil", "PySide6", "pyinstaller", "autopep8")
    DataFiles        = @(
        ("src/Packages/CustomLogging", "src/Packages/CustomLogging")
    )
    Formatter        = "autopep8"  # Options: "autopep8", "black", "none"
    IconFile         = $null  # Set to icon path (e.g., "src/Assets/icons/mousepointer.ico") if available
}

# Initialize version and output paths
$version = if (Test-Path $Config.VersionFile) { Get-Content $Config.VersionFile } else { "0.0.0" }
$Config.OutputExecutable = "Sigma Auto Clicker (v$version).exe"
$Config.SpecFile = "Sigma Auto Clicker (v$version).spec"

# Function to update progress
function Update-Progress {
    param (
        [Parameter(Mandatory)]
        [string]$StatusMessage,
        [Parameter(Mandatory)]
        [ValidateRange(0, 100)]
        [int]$Percent,
        [string]$Activity = "Building Sigma Auto Clicker"
    )
    Write-Progress -Activity $Activity -Status $StatusMessage -PercentComplete $Percent
}

# Function to set up virtual environment
function Initialize-VirtualEnvironment {
    Update-Progress "Setting up virtual environment" 5
    if (-not (Test-Path $Config.VenvDir)) {
        Write-Host "Creating virtual environment at $($Config.VenvDir)"
        python -m venv $Config.VenvDir
    }
    $script:pythonCmd = Join-Path $Config.VenvDir "Scripts\python.exe"
    $script:pipCmd = Join-Path $Config.VenvDir "Scripts\pip.exe"
    if (-not (Test-Path $script:pythonCmd)) {
        Write-Warning "Python executable not found in virtual environment: $script:pythonCmd"
        exit 1
    }
}

# Function to check Python version
function Test-PythonVersion {
    Update-Progress "Checking Python version" 10
    try {
        $pythonVersion = & $script:pythonCmd --version 2>&1 | ForEach-Object { $_ -replace 'Python ', '' }
        if ($pythonVersion -lt $Config.MinPythonVersion) {
            Write-Warning "Python $pythonVersion found. Minimum required: $($Config.MinPythonVersion)"
            exit 1
        }
        Write-Host "Python $pythonVersion is compatible."
    } catch {
        Write-Warning "Python not found or inaccessible in virtual environment."
        Write-Host "$($Error[0])" -ForegroundColor Red
        exit 1
    }
}

# Function to install dependencies
function Install-Dependencies {
    Update-Progress "Installing dependencies" 15
    try {
        & $script:pythonCmd -m pip install --upgrade pip --quiet
        $reqFile = Join-Path $Config.WorkingDir "requirements.txt"
        if (-not (Test-Path $reqFile)) {
            Write-Host "Generating requirements.txt from known dependencies."
            $Config.Dependencies | Out-File -FilePath $reqFile -Encoding ascii
        }
        & $script:pipCmd install -r $reqFile --quiet
        Write-Host "Dependencies installed successfully."
    } catch {
        Write-Warning "Failed to install dependencies."
        Write-Host "$($Error[0])" -ForegroundColor Red
        exit 1
    }
}

# Function to format Python code
function Format-PythonCode {
    Update-Progress "Formatting Python code" 20
    if ($Config.Formatter -eq "none") {
        Write-Host "Code formatting skipped (Formatter set to 'none')."
        return
    }
    try {
        $formatterCmd = Join-Path $Config.VenvDir "Scripts\$($Config.Formatter).exe"
        if (-not (Test-Path $formatterCmd)) {
            Write-Host "Formatter '$($Config.Formatter)' not found. Skipping code formatting."
            return
        }
        $excludedFiles = @('.gitignore', 'LICENSE', 'requirements.txt', 'VERSION.txt', '*.pyc', '*.pyo', '*.pyd', '*.exe', '*.spec', 'dist/*', 'build/*', '__pycache__/*')
        if (Test-Path '.\.gitignore') {
            $excludedFiles += Get-Content '.\.gitignore' -ErrorAction SilentlyContinue | Where-Object { $_ -and $_ -notmatch '^\s*#' } | ForEach-Object { $_ -replace '^/', '' }
        }
        Get-ChildItem -Path . -Recurse -Include *.py -Exclude $excludedFiles | ForEach-Object {
            & $formatterCmd --in-place --aggressive --aggressive $_.FullName
            Write-Host "Formatted ($($Config.Formatter)): $($_.FullName)"
        }
    } catch {
        Write-Warning "Failed to format code with $($Config.Formatter)."
        Write-Host "$($Error[0])" -ForegroundColor Red
    }
}

# Function to generate PyInstaller spec file
function New-PyInstallerSpec {
    Update-Progress "Generating PyInstaller spec" 40
    $scriptPath = Join-Path $Config.WorkingDir $Config.ScriptName
    if (-not (Test-Path $scriptPath)) {
        Write-Warning "Main script '$($Config.ScriptName)' not found in '$($Config.WorkingDir)'."
        exit 1
    }
    $header = "# WARNING: This file is automatically generated. DO NOT modify directly."
    $dataFiles = $Config.DataFiles | ForEach-Object { "        ('$($_[0])', '$($_[1])')" } | Join-String -Separator ",`n"
    $hiddenImports = $Config.Dependencies | Where-Object { $_ -ne "pyinstaller" -and $_ -ne "autopep8" } | ForEach-Object { "'$_'" } | Join-String -Separator ", "
    $iconLine = if ($Config.IconFile -and (Test-Path $Config.IconFile)) { "    icon='$($Config.IconFile -replace '\\', '\\\\')'" } else { "" }
    $specContent = @"
# -*- mode: python ; coding: utf-8 -*-
block_cipher = None
a = Analysis(
    ['$($Config.ScriptName)'],
    pathex=['$($Config.WorkingDir -replace '\\', '\\\\')'],
    binaries=[],
    datas=[
$dataFiles
    ],
    hiddenimports=[$hiddenImports],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pyinstaller', 'autopep8'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='$($Config.OutputExecutable -replace '\.exe$')',
    debug=$($Debug.IsPresent.ToString().ToLower()),
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=$($Debug.IsPresent.ToString().ToLower()),
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
$iconLine
)
"@
    try {
        Set-Content -Path $Config.SpecFile -Value ($header + "`r`n" + $specContent) -Encoding ASCII
        Write-Host "Generated PyInstaller spec file: $($Config.SpecFile)"
    } catch {
        Write-Warning "Failed to write PyInstaller spec file."
        Write-Host "$($Error[0])" -ForegroundColor Red
        exit 1
    }
}

# Function to build the executable
function Build-Executable {
    Update-Progress "Building executable with PyInstaller" 60
    try {
        $pyinstallerCmd = Join-Path $Config.VenvDir "Scripts\pyinstaller.exe"
        if (-not (Test-Path $pyinstallerCmd)) {
            Write-Warning "PyInstaller not found in virtual environment. Install with 'pip install pyinstaller'."
            exit 1
        }
        & $pyinstallerCmd --noconfirm --clean $Config.SpecFile
        $outputPath = Join-Path $Config.WorkingDir "dist\$($Config.OutputExecutable)"
        if (-not (Test-Path $outputPath)) {
            Write-Warning "PyInstaller ran, but executable not found at $outputPath."
            exit 1
        }
        Write-Host "Executable built successfully: $outputPath"
    } catch {
        Write-Warning "PyInstaller build failed."
        Write-Host "$($Error[0])" -ForegroundColor Red
        exit 1
    }
}

# Function to clean up temporary files
function Clear-TemporaryFiles {
    if (-not $Debug) {
        Update-Progress "Cleaning up temporary files" 80
        Remove-Item $Config.SpecFile -ErrorAction SilentlyContinue
        Remove-Item ".\build\*" -Recurse -ErrorAction SilentlyContinue
        Remove-Item ".\__pycache__\*", ".\src\__pycache__\*", ".\src\Packages\__pycache__\*", ".\src\Packages\CustomLogging\__pycache__\*" -Recurse -ErrorAction SilentlyContinue
    }
}

# Function to validate the executable
function Test-Executable {
    Update-Progress "Validating executable" 90
    $outputPath = Join-Path $Config.WorkingDir "dist\$($Config.OutputExecutable)"
    if (Test-Path $outputPath) {
        Write-Host "Validation: Executable exists at $outputPath"
    } else {
        Write-Warning "Validation failed: Executable not found at $outputPath."
        exit 1
    }
}

# Function to run the executable
function Start-Executable {
    if ($Run) {
        Update-Progress "Running Sigma Auto Clicker" 95
        $executablePath = Join-Path $Config.WorkingDir "dist\$($Config.OutputExecutable)"
        try {
            Start-Process $executablePath -ArgumentList $Arguments
            Write-Host "Started executable: $executablePath"
        } catch {
            Write-Warning "Failed to run executable."
            Write-Host "$($Error[0])" -ForegroundColor Red
            exit 1
        }
    }
}

# Main execution
try {
    Set-Location $Config.WorkingDir
    if (-not (Test-Path $Config.ScriptName)) {
        Write-Warning "Main script $($Config.ScriptName) not found in $($Config.WorkingDir)."
        exit 1
    }
    Initialize-VirtualEnvironment
    Test-PythonVersion
    Install-Dependencies
    Format-PythonCode
    New-PyInstallerSpec
    Build-Executable
    Clear-TemporaryFiles
    Test-Executable
    Start-Executable
    Write-Host "Build process completed successfully."
} catch {
    Write-Warning "Build process failed."
    Write-Host "$($Error[0])" -ForegroundColor Red
    exit 1
} finally {
    Write-Progress -Activity "Building Sigma Auto Clicker" -Completed
}