#region Helper functions
function Get-EnvVar {
    param([string]$Key)
    (Get-Content .env -ErrorAction SilentlyContinue) -match "^$Key=" |
        ForEach-Object { ($_ -split '=', 2)[1] }
}

function Test-CertFile {
    param([string]$Path)
    if (Test-Path $Path) {
        Write-Host "Certificate file '$Path' already exists. Skipping creation." -ForegroundColor Yellow
        Write-Host "Delete the file if you want to create a new certificate." -ForegroundColor Yellow
        $true
    } else { $false }
}
function Get-ExistingCert {
    param([string]$Subject)
    Get-ChildItem Cert:\CurrentUser\My |
        Where-Object { $_.Subject -eq "CN=$Subject" }
}

function Remove-ExpiredCert {
    param($Cert)
    Write-Host "Certificate has expired. Removing and creating new one..." -ForegroundColor Red
    $Cert | Remove-Item
}

function New-CodeSigningCert {
    param([string]$Subject)
    $params = @{
        Type              = 'CodeSigningCert'
        Subject           = "CN=$Subject"
        CertStoreLocation = 'Cert:\CurrentUser\My'
        KeyExportPolicy   = 'Exportable'
        NotAfter          = (Get-Date).AddYears(1)
    }
    New-SelfSignedCertificate @params
}

function Export-CertToPfx {
    param($Cert, [string]$Path, [securestring]$Password)
    Export-PfxCertificate -Cert $Cert -FilePath $Path -Password $Password
}

function Write-CertInfo {
    param($Cert, [string]$Action)
    Write-Host "Certificate $Action successfully!" -ForegroundColor Green
    Write-Host "Thumbprint: $($Cert.Thumbprint)" -ForegroundColor Cyan
    Write-Host "Valid until: $($Cert.NotAfter)" -ForegroundColor Cyan
}

function Get-PfxPassword {
    $password = Get-EnvVar 'PFX_PASSWORD'
    if (-not $password) {
        $password = Read-Host "PFX_PASSWORD not found in .env – please enter it now" -AsSecureString
        if (-not $password) {
            Write-Host "No password supplied; aborting." -ForegroundColor Red
            exit 1
        }
        return $password
    }
    ConvertTo-SecureString $password -AsPlainText -Force
}
#endregion

#region Configuration
$CertPath   = "certificate.pfx"
$AuthorName = "MrAndi Scripted LLC"
$Version    = Get-Content VERSION.txt
$Executable = "dist\Sigma Auto Clicker (v$Version).exe"
#endregion

# Early exit if PFX already present
if (Test-CertFile $CertPath) { 
    # Launch certmgr.msc if it exists
    if (Get-Command certmgr.msc -ErrorAction SilentlyContinue) {
        Start-Process certmgr.msc
    }
    exit 
}

# Load password once
$SecurePassword = Get-PfxPassword

# Check store for existing cert
$ExistingCert = Get-ExistingCert $AuthorName
if ($ExistingCert) {
    Write-Host "Certificate for '$AuthorName' already exists in certificate store." -ForegroundColor Yellow
    Write-Host "Thumbprint: $($ExistingCert.Thumbprint)" -ForegroundColor Cyan
    Write-Host "NotAfter: $($ExistingCert.NotAfter)" -ForegroundColor Cyan

    $DaysLeft = ($ExistingCert.NotAfter - (Get-Date)).Days
    Write-Host "Days remaining: $DaysLeft" -ForegroundColor Cyan

    if ($DaysLeft -gt 0) {
        Write-Host "Certificate is still valid. Skipping creation." -ForegroundColor Yellow
        # Launch certmgr.msc if it exists
        if (Get-Command certmgr.msc -ErrorAction SilentlyContinue) {
            Start-Process certmgr.msc
        }
        exit
    }
    Remove-ExpiredCert $ExistingCert
}

# Create and export new certificate
Write-Host "Creating new code signing certificate..." -ForegroundColor Green
try {
    $Cert = New-CodeSigningCert $AuthorName
    Write-CertInfo $Cert 'created'

    Export-CertToPfx -Cert $Cert -Path $CertPath -Password $SecurePassword
    Write-Host "Certificate exported to '$CertPath'" -ForegroundColor Green

    # Verify export
    if (Test-Path $CertPath) {
        $Size = (Get-Item $CertPath).Length
        Write-Host "Export verified. File size: $Size bytes" -ForegroundColor Green
    }
} catch {
    Write-Host "Error creating certificate: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host "`nCertificate creation completed successfully!" -ForegroundColor Green
Write-Host "To use this certificate for signing:" -ForegroundColor Cyan
Write-Host "Set-AuthenticodeSignature -FilePath '$Executable' -Certificate (Get-ChildItem Cert:\CurrentUser\My\$($Cert.Thumbprint))" -ForegroundColor White

# Launch certmgr.msc if it exists
if (Get-Command certmgr.msc -ErrorAction SilentlyContinue) {
    Start-Process certmgr.msc
}

# Invoke embedded batch signing script
$Batch = @'
@ECHO OFF
SETLOCAL EnableDelayedExpansion

REM ==== Configuration ====
SET "CERT_FILE=certificate.pfx"
SET "TIMESTAMP_SERVER=http://timestamp.digicert.com"
SET "SIGN_ALGORITHM=sha256"
SET /P VERSION=<VERSION.txt
SET "FILE_TO_SIGN=dist\Sigma Auto Clicker (v%VERSION%).exe"
SET "ENV_FILE=.env"
SET "PASSWORD_KEY=PFX_PASSWORD"

REM ==== Load password ====
IF NOT EXIST "%ENV_FILE%" (
    ECHO ERROR: %ENV_FILE% file not found!
    GOTO :ERROR
)

SET "CERT_PASSWORD="
FOR /F "tokens=1,2 delims== " %%A IN (%ENV_FILE%) DO (
    IF /I "%%A"=="%PASSWORD_KEY%" SET "CERT_PASSWORD=%%B"
)

IF NOT DEFINED CERT_PASSWORD (
    ECHO ERROR: %PASSWORD_KEY% not found in %ENV_FILE%!
    GOTO :ERROR
)

REM ==== Sign file ====
ECHO Signing "%FILE_TO_SIGN%"...
signtool.exe sign /f "%CERT_FILE%" /p "%CERT_PASSWORD%" /tr "%TIMESTAMP_SERVER%" /td %SIGN_ALGORITHM% /fd %SIGN_ALGORITHM% "%FILE_TO_SIGN%"
IF %ERRORLEVEL% NEQ 0 GOTO :SIGNING_FAILED

ECHO Signing completed successfully.
GOTO :END

:SIGNING_FAILED
ECHO ERROR: Signing failed with error code %ERRORLEVEL%.
GOTO :ERROR

:ERROR
ECHO.
ECHO Script execution failed.
PAUSE
EXIT /B 1

:END
ECHO.
ECHO Script completed.
PAUSE
EXIT /B 0
'@

$BatchPath = "$env:TEMP\sign_embedded.bat"
$Batch | Out-File -FilePath $BatchPath -Encoding ASCII
cmd /c "`"$BatchPath`""