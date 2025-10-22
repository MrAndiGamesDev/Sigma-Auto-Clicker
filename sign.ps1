# Load .env variables
get-content .env | foreach {
    $name, $value = $_.split('=')
}

$certPath = "certificate.pfx"
$Authername = "MrAndi Scripted LLC"
$version = Get-Content -Path "VERSION.txt"
$target = "Sigma Auto Clicker (v$version)"
$executetype = "$target.exe"

# Ensure certificate.pfx exists; create if missing
if (-not (Test-Path $certPath)) {
    Write-Host "Certificate file '$certPath' not found. Creating..." -ForegroundColor Yellow

    # Check for existing cert in store
    $existingCert = Get-ChildItem -Path Cert:\CurrentUser\My | Where-Object { $_.Subject -eq "CN=$Authername" }

    if ($existingCert) {
        Write-Host "Certificate for '$Authername' already exists in certificate store." -ForegroundColor Yellow
        Write-Host "Thumbprint: $($existingCert.Thumbprint)" -ForegroundColor Cyan
        Write-Host "NotAfter: $($existingCert.NotAfter)" -ForegroundColor Cyan
        $daysLeft = ($existingCert.NotAfter - (Get-Date)).Days
        Write-Host "Days remaining: $daysLeft" -ForegroundColor Cyan
        if ($daysLeft -le 0) {
            Write-Host "Certificate has expired. Removing and creating new one..." -ForegroundColor Red
            $existingCert | Remove-Item
        } else {
            # Export existing valid cert to PFX
            $pswrd = ConvertTo-SecureString -String $value -Force -AsPlainText
            Export-PfxCertificate -Cert $existingCert -FilePath $certPath -Password $pswrd
            Write-Host "Existing valid certificate exported to '$certPath'" -ForegroundColor Green
            exit
        }
    }

    # Create new self-signed certificate valid for 1 year
    Write-Host "Creating new code signing certificate..." -ForegroundColor Green
    try {
        $cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=$Authername" -CertStoreLocation Cert:\CurrentUser\My -KeyExportPolicy Exportable -NotAfter (Get-Date).AddYears(1)
        Write-Host "Certificate created successfully!" -ForegroundColor Green
        Write-Host "Thumbprint: $($cert.Thumbprint)" -ForegroundColor Cyan
        Write-Host "Valid until: $($cert.NotAfter)" -ForegroundColor Cyan

        # Export to PFX
        $pswrd = ConvertTo-SecureString -String $value -Force -AsPlainText
        Export-PfxCertificate -Cert $cert -FilePath $certPath -Password $pswrd

        Write-Host "Certificate exported to '$certPath'" -ForegroundColor Green

        # Verify export
        if (Test-Path $certPath) {
            $pfxSize = (Get-Item $certPath).Length
            Write-Host "Export verified. File size: ${pfxSize} bytes" -ForegroundColor Green
        }
    } catch {
        Write-Host "Error creating certificate: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }

    Write-Host "`nCertificate creation completed successfully!" -ForegroundColor Green
    Write-Host "To use this certificate for signing:" -ForegroundColor Cyan
    Write-Host "Set-AuthenticodeSignature -FilePath '$executetype' -Certificate (Get-ChildItem Cert:\CurrentUser\My\$($cert.Thumbprint))" -ForegroundColor White
} else {
    Write-Host "Certificate file '$certPath' already exists." -ForegroundColor Green
}