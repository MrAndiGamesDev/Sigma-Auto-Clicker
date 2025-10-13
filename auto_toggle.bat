@echo off
setlocal

:: Path to the virtual environment
set VENV_PATH=AutoClickerPy\Scripts

:: Check if the virtual environment is active
if defined VIRTUAL_ENV (
    echo Deactivating virtual environment...
    call "%VENV_PATH%\deactivate.bat"
) else (
    echo Activating virtual environment...
    "%VENV_PATH%\Activate.ps1"
)

endlocal