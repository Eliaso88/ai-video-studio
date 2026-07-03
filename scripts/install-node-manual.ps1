$ErrorActionPreference = 'Stop'

$url = 'https://nodejs.org/dist/v18.20.0/node-v18.20.0-x64.msi'
$dest = Join-Path $env:TEMP 'node-v18.20.0-x64.msi'

if (Test-Path $dest) {
    Remove-Item $dest -Force
}

Write-Host "Downloading Node 18.20.0 installer to $dest"
Invoke-WebRequest -Uri $url -OutFile $dest -UseBasicParsing

if (-not (Test-Path $dest)) {
    Write-Host "Download failed: installer not found at $dest"
    exit 1
}

Write-Host "Running Node installer..."
$process = Start-Process -FilePath msiexec -ArgumentList @('/i', $dest, '/qn', '/norestart') -Wait -PassThru
Write-Host "Installer exit code: $($process.ExitCode)"

if ($process.ExitCode -ne 0) {
    Write-Host "Node installation failed with exit code $($process.ExitCode)."
    Write-Host "If this is due to permissions, run the installer manually or use nvm-windows."
    exit $process.ExitCode
}

Write-Host "Installation completed, verifying installation..."
if (Get-Command node -ErrorAction SilentlyContinue) {
    Write-Host "node: $(node -v)"
} else {
    Write-Host "node not found after install"
}

if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "npm: $(npm -v)"
} else {
    Write-Host "npm not found after install"
}
