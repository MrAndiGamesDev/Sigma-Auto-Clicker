# Check if certificate.pfx already exists
$certPath = "certificate.pfx"
if (Test-Path $certPath) {
    Write-Host "Certificate file '$certPath' already exists. Skipping creation." -ForegroundColor Yellow
    Write-Host "Delete the file if you want to create a new certificate." -ForegroundColor Yellow
    exit
}

# Check if certificate already exists in store
$Authername = "MrAndi Scripted"
$thumbprint = $null
$existingCert = Get-ChildItem -Path Cert:\CurrentUser\My | Where-Object { $_.Subject -eq "CN=$Authername" }

$version = Get-Content -Path "VERSION.txt"
$targetexe = "Sigma Auto Clicker ($version)"

if ($existingCert) {
    Write-Host "Certificate for '$Authername' already exists in certificate store." -ForegroundColor Yellow
    Write-Host "Thumbprint: $($existingCert.Thumbprint)" -ForegroundColor Cyan
    Write-Host "NotAfter: $($existingCert.NotAfter)" -ForegroundColor Cyan
    $daysLeft = ($existingCert.NotAfter - (Get-Date)).Days
    Write-Host "Days remaining: $daysLeft" -ForegroundColor Cyan
    
    if ($daysLeft -gt 0) {
        Write-Host "Certificate is still valid. Skipping creation." -ForegroundColor Yellow
        exit
    } else {
        Write-Host "Certificate has expired. Removing and creating new one..." -ForegroundColor Red
        $existingCert | Remove-Item
    }
}

# Create a self-signed certificate valid for 1 year
Write-Host "Creating new code signing certificate..." -ForegroundColor Green
try {
    $cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=$Authername" -CertStoreLocation Cert:\CurrentUser\My -KeyExportPolicy Exportable -NotAfter (Get-Date).AddYears(1)
    Write-Host "Certificate created successfully!" -ForegroundColor Green
    Write-Host "Thumbprint: $($cert.Thumbprint)" -ForegroundColor Cyan
    Write-Host "Valid until: $($cert.NotAfter)" -ForegroundColor Cyan
    
    # Export to PFX
    $pswrd = ConvertTo-SecureString -String "" -Force -AsPlainText
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
Write-Host "Set-AuthenticodeSignature -FilePath '$targetexe.exe' -Certificate (Get-ChildItem Cert:\CurrentUser\My\$($cert.Thumbprint))" -ForegroundColor White