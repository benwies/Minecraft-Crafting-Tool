$ErrorActionPreference = 'Stop'

# Resolve repo root from this script location (tools/build)
$repoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $repoRoot

Write-Host "Repo root: $repoRoot"

# Pick a Python
$python = $env:PYTHON ?? 'python'
try {
  & $python -V | Out-Null
} catch {
  $python = 'py'
}

# Ensure PyInstaller is available
$hasPyInstaller = $false
try {
  & $python -m PyInstaller --version | Out-Null
  $hasPyInstaller = $true
} catch {
  $hasPyInstaller = $false
}
if (-not $hasPyInstaller) {
  Write-Host "Installing PyInstaller..."
  & $python -m pip install --upgrade pip
  & $python -m pip install pyinstaller
}

# Build name
$appName = 'MinecraftFarmCalc'

# Ensure output is clean
if (Test-Path "$repoRoot\dist\$appName") { Remove-Item -Recurse -Force "$repoRoot\dist\$appName" }
if (Test-Path "$repoRoot\build\$appName") { Remove-Item -Recurse -Force "$repoRoot\build\$appName" }

# Compose --add-data values (use ; separator on Windows)
$datas = @(
  "recepies.json;.",
  "recepies;recepies",
  "pic;pic"
)

# Optional icon (place tools/build/app.ico to enable)
$iconArg = ''
if (Test-Path "$repoRoot\tools\build\app.ico") { $iconArg = "--icon tools\\build\\app.ico" }

# Hidden imports for GUI & PIL image bridge
$hidden = @(
  "--hidden-import", "tkinter",
  "--hidden-import", "PIL.ImageTk"
)

# Build exe (one-folder, windowed)
$piArgs = @(
  "--noconfirm",
  "--clean",
  "--windowed",
  "--name", $appName
)
foreach ($d in $datas) { $piArgs += @("--add-data", $d) }
if ($iconArg) { $piArgs += $iconArg.Split(' ') }
$piArgs += $hidden
$piArgs += "main.py"

Write-Host "Running PyInstaller..."
& $python -m PyInstaller @piArgs

if ($LASTEXITCODE -ne 0) {
  throw "PyInstaller failed with code $LASTEXITCODE"
}

Write-Host "Build complete: dist\$appName\$appName.exe"
