param(
    [string]$DnsName = "your-public-bridge.example.com",
    [string]$OutDir = ".\\certs",
    [string]$Password = "replace_with_dev_passphrase"
)

$ErrorActionPreference = "Stop"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$cert = New-SelfSignedCertificate `
    -DnsName $DnsName `
    -CertStoreLocation "Cert:\\CurrentUser\\My" `
    -FriendlyName "qpyclaw-openclaw-tls-bridge" `
    -KeyAlgorithm RSA `
    -KeyLength 2048 `
    -HashAlgorithm sha256 `
    -NotAfter (Get-Date).AddYears(1)

$secure = ConvertTo-SecureString -String $Password -AsPlainText -Force
$pfxPath = Join-Path $OutDir "openclaw-tls-bridge.pfx"

Export-PfxCertificate `
    -Cert ("Cert:\\CurrentUser\\My\\" + $cert.Thumbprint) `
    -FilePath $pfxPath `
    -Password $secure | Out-Null

Write-Host ("PFX exported: " + $pfxPath)
Write-Host ("Thumbprint: " + $cert.Thumbprint)
