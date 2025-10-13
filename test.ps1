# Create a self-signed certificate valid for 1 year
$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject "CN=MrAndi Scripted" -CertStoreLocation Cert:\CurrentUser\My -KeyExportPolicy Exportable -NotAfter (Get-Date).AddYears(1)

# Export to PFX
$pswd = ConvertTo-SecureString -String "2006" -Force -AsPlainText
Export-PfxCertificate -Cert $cert -FilePath "certificate.pfx" -Password $pswd