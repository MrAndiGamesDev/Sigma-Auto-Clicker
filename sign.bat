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
IF NOT EXIST "%ENV_FILE%" (
    ECHO ERROR: %ENV_FILE% file not found!
    PAUSE & EXIT /B 1
)

FOR /F "tokens=1,2 delims== " %%A IN (%ENV_FILE%) DO (
    IF /I "%%A"=="%PASSWORD_KEY%" SET "CERT_PASSWORD=%%B"
)

IF NOT DEFINED CERT_PASSWORD (
    ECHO ERROR: %PASSWORD_KEY% not found in %ENV_FILE%!
    PAUSE & EXIT /B 1
)

REM ================================
REM Sign the file
REM ================================
ECHO Signing "%FILE_TO_SIGN%"...
signtool.exe sign /f "%CERT_FILE%" /p "%CERT_PASSWORD%" /tr "%TIMESTAMP_SERVER%" /td %SIGN_ALGORITHM% /fd %SIGN_ALGORITHM% "%FILE_TO_SIGN%"
IF %ERRORLEVEL% NEQ 0 (
    ECHO ERROR: Signing failed with error code %ERRORLEVEL%.
    PAUSE & EXIT /B 1
)

ECHO Signing completed successfully.
PAUSE & EXIT /B 0