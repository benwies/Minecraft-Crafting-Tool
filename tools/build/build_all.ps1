param(
  [string]$Version,
  [string]$Publisher,
  [string]$SignPfxPath,
  [string]$SignPfxPassword,
  [string]$TimestampUrl = 'http://timestamp.digicert.com'
)

$ErrorActionPreference = 'Stop'

# Resolve repo root from this script location (tools/build)
$repoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $repoRoot

Write-Host "Repo root: $repoRoot"

# 1) Build the one-folder app
Write-Host "Step 1/3: Building EXE with PyInstaller..."
. "$PSScriptRoot\build_exe.ps1" -SignPfxPath $SignPfxPath -SignPfxPassword $SignPfxPassword -TimestampUrl $TimestampUrl

$oneFolderDir = Join-Path $repoRoot 'dist\MCCraftingCalculator'
if (-not (Test-Path $oneFolderDir)) {
  throw "Expected one-folder output at $oneFolderDir not found."
}

# 2) Create a portable ZIP
Write-Host "Step 2/3: Creating portable ZIP..."
$zipPath = Join-Path $repoRoot 'dist\MCCraftingCalculator-portable.zip'
if (Test-Path $zipPath) { Remove-Item -Force $zipPath }
Compress-Archive -Path (Join-Path $oneFolderDir '*') -DestinationPath $zipPath
Write-Host "Portable ZIP: $zipPath"

# 3) Build the installer (if ISCC is available)
Write-Host "Step 3/3: Building installer (if Inno Setup is installed)..."
try {
  . "$PSScriptRoot\build_installer.ps1" -Version $Version -Publisher $Publisher -SignPfxPath $SignPfxPath -SignPfxPassword $SignPfxPassword -TimestampUrl $TimestampUrl
} catch {
  Write-Warning "Skipping installer step: $($_.Exception.Message)"
  Write-Host "Install Inno Setup with: winget install Jrsoftware.InnoSetup"
}

Write-Host "All done. Artifacts in dist/ and dist/installer/."
