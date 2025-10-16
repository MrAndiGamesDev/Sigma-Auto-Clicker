@ECHO OFF
REM ================================
REM Configuration - edit these lines
REM ================================
SET PFX_FILE=certificate.pfx
SET PFX_PASSWORD=2006
SET /P VERSION=<version.txt
SET FILE_TO_SIGN=.\Sigma Auto Clicker (%VERSION%).exe
SET TIMESTAMP_URL=http://timestamp.digicert.com

REM ================================
REM Signing the file
REM ================================
signtool.exe sign /f "%PFX_FILE%" /p "%PFX_PASSWORD%" /tr "%TIMESTAMP_URL%" /td sha256 /fd sha256 "%FILE_TO_SIGN%"

REM ================================
REM Check result
REM ================================
IF %ERRORLEVEL% EQU 0 (
    ECHO Signing completed successfully.
) ELSE (
    ECHO Signing failed with error code %ERRORLEVEL%.
)

PAUSE