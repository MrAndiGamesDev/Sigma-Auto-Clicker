@ECHO OFF
SETLOCAL EnableDelayedExpansion

REM ================================
REM Configuration
REM ================================
SET "CERT_FILE=certificate.pfx"
SET "TIMESTAMP_SERVER=http://timestamp.digicert.com"
SET "SIGN_ALGORITHM=sha256"
SET /P VERSION=<VERSION.txt
SET "FILE_TO_SIGN=.\dist\Sigma Auto Clicker (v%VERSION%).exe"
SET "ENV_FILE=.env"
SET "PASSWORD_KEY=PFX_PASSWORD"

REM ================================
REM Load password from .env
REM ================================
CALL :LoadEnvVar "%ENV_FILE%" "%PASSWORD_KEY%" CERT_PASSWORD
IF ERRORLEVEL 1 PAUSE & EXIT /B 1

REM ================================
REM Check if file to sign exists
REM ================================
IF NOT EXIST "%FILE_TO_SIGN%" (
    ECHO ERROR: File to sign not found at "%FILE_TO_SIGN%".
    PAUSE & EXIT /B 1
)

REM ================================
REM Sign the file
REM ================================
CALL :SignFile "%FILE_TO_SIGN%"
IF ERRORLEVEL 1 PAUSE & EXIT /B 1

ECHO Signing completed successfully.
PAUSE & EXIT /B 0

REM ================================
REM Functions
REM ================================
:LoadEnvVar
SET "ENV_FILE=%~1"
SET "KEY=%~2"
SET "RESULT_VAR=%~3"
IF NOT EXIST "%ENV_FILE%" (
    ECHO ERROR: %ENV_FILE% file not found!
    EXIT /B 1
)
FOR /F "tokens=1,2 delims== " %%A IN (%ENV_FILE%) DO (
    IF /I "%%A"=="%KEY%" SET "%RESULT_VAR%=%%B"
)
IF NOT DEFINED %RESULT_VAR% (
    ECHO ERROR: %KEY% not found in %ENV_FILE%!
    EXIT /B 1
)
EXIT /B 0

:SignFile
SET "TARGET=%~1"
ECHO Signing "%TARGET%"...
signtool.exe sign /f "%CERT_FILE%" /p "%CERT_PASSWORD%" /tr "%TIMESTAMP_SERVER%" /td %SIGN_ALGORITHM% /fd %SIGN_ALGORITHM% "%TARGET%"
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Signing failed with error code %ERRORLEVEL%.
    EXIT /B 1
)
EXIT /B 0