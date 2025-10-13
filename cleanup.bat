@echo off
setlocal

echo Cleaning build artifacts...
timeout /t 1 /nobreak >nul

rem Define items to remove
set "items=build dist autoclicker.spec"

for %%I in (%items%) do (
    if exist "%%I" (
        if "%%~xI"=="" (
            rmdir /s /q "%%I"
        ) else (
            del /f /q "%%I"
        )
        echo Removed: %%I
        timeout /t 1 /nobreak >nul
    )
)

echo Cleanup complete.
endlocal