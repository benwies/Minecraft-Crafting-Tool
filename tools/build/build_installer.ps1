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

# Ensure the PyInstaller output exists
$oneFolderDir = Join-Path $repoRoot 'dist\MCCraftingCalculator'
if (-not (Test-Path $oneFolderDir)) {
  throw "PyInstaller output not found at $oneFolderDir. Run tools/build/build_exe.ps1 first."
}

# Locate ISCC (Inno Setup Command-Line Compiler)
function Get-ISCCPath {
  try {
    $null = & iscc /? 2>$null
    if ($LASTEXITCODE -eq 0) { return 'iscc' }
  } catch {}

  $candidates = @(
    (Join-Path $env:ProgramFiles 'Inno Setup 6\\ISCC.exe'),
    (Join-Path $env:ProgramFiles 'Inno Setup\\ISCC.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup 6\\ISCC.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Inno Setup\\ISCC.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\\Inno Setup 6\\ISCC.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\\Inno Setup\\ISCC.exe'),
    'C:\\Program Files\\Inno Setup 6\\ISCC.exe',
    'C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe'
  )
  foreach ($p in $candidates) { if (Test-Path $p) { return $p } }

  # Registry lookup (some installers set uninstall info)
  $regKeys = @(
    'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1',
    'HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1'
  )
  foreach ($rk in $regKeys) {
    try {
      $k = Get-ItemProperty -Path $rk -ErrorAction SilentlyContinue
      if ($k) {
        $appPath = $k.'Inno Setup: App Path'
        if (-not $appPath -and $k.InstallLocation) { $appPath = $k.InstallLocation }
        if ($appPath) {
          $exe = Join-Path $appPath 'ISCC.exe'
          if (Test-Path $exe) { return $exe }
        }
      }
    } catch {}
  }
  return $null
}

$iscc = Get-ISCCPath
if (-not $iscc) {
  throw @"
Inno Setup is not installed.
Install it via:
  winget install Jrsoftware.InnoSetup

Or download from https://jrsoftware.org/isdl.php
Then re-run this script.
"@
}

$iss = Join-Path $repoRoot 'tools\build\installer.iss'
if (-not (Test-Path $iss)) { throw "Installer script not found: $iss" }

# Ensure output directory exists
$outDir = Join-Path $repoRoot 'dist\installer'
if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

# Build argument list
$isccArgs = @()
if ($Version) { $isccArgs += "/DMyAppVersion=$Version" }
if ($Publisher) { $isccArgs += "/DMyAppPublisher=$Publisher" }
# Optional signing defines for Inno Setup
if ($SignPfxPath)    { $isccArgs += "/DSignPfxPath=$SignPfxPath" }
if ($SignPfxPassword){ $isccArgs += "/DSignPfxPassword=$SignPfxPassword" }
if ($TimestampUrl)   { $isccArgs += "/DTimestampUrl=$TimestampUrl" }
# If an app icon exists, pass it so the installer UI uses it
$appIco = Join-Path $repoRoot 'tools\build\app.ico'
if (Test-Path $appIco) { $isccArgs += "/DMyAppIcon=$appIco" }
# Pass the .iss path as a single argument; PowerShell will quote if needed
$isccArgs += $iss

Write-Host "Building installer with Inno Setup..."
& $iscc @isccArgs
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed with code $LASTEXITCODE" }

Write-Host "Installer complete: dist\\installer\\MCCraftingCalculator-Setup.exe"
