<#
PowerShell helper to install or verify Node.js (preferred version 18.20.0) on Windows.

Usage:
  - Open PowerShell and run: .\scripts\install-node-windows.ps1
  - Recommended: run from an elevated prompt if you expect system-wide installs.

This script will:
  1. Check whether `node` and `npm` are available.
  2. If missing and `winget` is present, attempt to install `OpenJS.NodeJS.LTS` via winget.
  3. If winget install fails, attempt to install `nvm-windows` via winget and instruct you to use `nvm` to install a specific version.

Notes:
  - A successful winget install may require you to restart the shell for PATH changes to take effect.
  - If automatic installs fail, follow the manual links printed by the script.
#>

$ErrorActionPreference = 'Stop'
$desiredVersion = '18.20.0'

function Has-Command($name) {
    return (Get-Command $name -ErrorAction SilentlyContinue) -ne $null
}

if (Has-Command node) {
    Write-Host "Node is already installed: $(node -v)"
    Write-Host "npm: $(npm -v)"
    exit 0
}

if (Has-Command winget) {
    Write-Host "winget detected. Attempting to install Node LTS (OpenJS.NodeJS.LTS)..."
    $args = @('install','--id','OpenJS.NodeJS.LTS','-e','--accept-package-agreements','--accept-source-agreements')
    $proc = Start-Process -FilePath winget -ArgumentList $args -NoNewWindow -Wait -PassThru
    if ($proc.ExitCode -eq 0) {
        Write-Host "winget install completed. Checking for node in PATH..."
        if (Has-Command node) {
            Write-Host "Node installed: $(node -v)"
            Write-Host "npm: $(npm -v)"
            exit 0
        } else {
            Write-Host "Node not found in PATH after winget install. Try restarting your terminal or logging out/in."
        }
    } else {
        Write-Host "winget install returned exit code $($proc.ExitCode)."
    }

    Write-Host "Attempting to install nvm-windows via winget as fallback..."
    $args2 = @('install','--id','GitHub.CoreyButler.NVM','-e','--accept-package-agreements','--accept-source-agreements')
    $proc2 = Start-Process -FilePath winget -ArgumentList $args2 -NoNewWindow -Wait -PassThru
    if ($proc2.ExitCode -eq 0) {
        Write-Host "nvm-windows installer installed. Open a NEW PowerShell window and run the following commands to install Node ${desiredVersion}:"
        Write-Host "nvm install ${desiredVersion}"
        Write-Host "nvm use ${desiredVersion}"
        Write-Host "Then confirm: node -v ; npm -v"
        exit 0
    } else {
        Write-Host "nvm install via winget returned exit code $($proc2.ExitCode)."
    }
} else {
    Write-Host "winget is not available on this machine."
}

Write-Host "Automatic installation did not complete. Please install Node.js manually or install nvm-windows and use it to install Node ${desiredVersion}."
Write-Host "Manual download links:"
Write-Host "  - Node.js LTS: https://nodejs.org/"
Write-Host "  - nvm-windows releases: https://github.com/coreybutler/nvm-windows/releases"
Write-Host "After installation, verify with: node -v ; npm -v"

exit 1
