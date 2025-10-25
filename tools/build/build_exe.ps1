$ErrorActionPreference = 'Stop'

# Resolve repo root from this script location (tools/build)
$repoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
Set-Location $repoRoot

Write-Host "Repo root: $repoRoot"

# Pick a Python (PowerShell 5.1 compatible)
$python = $env:PYTHON
if (-not $python) { $python = 'python' }
try {
  & $python -V | Out-Null
} catch {
  $python = 'py'
  try {
    & $python -V | Out-Null
  } catch {
    throw "Python not found. Install Python 3.x or set $env:PYTHON to your interpreter path."
  }
}

# Show which Python will be used
Write-Host "Using Python:"
& $python -c "import sys; print(sys.executable)"

# Ensure PyInstaller is available (avoid importlib.util to prevent shadowing issues)
Write-Host "Checking for PyInstaller..."
& $python -c "import PyInstaller" 2>$null
$hasPyInstaller = ($LASTEXITCODE -eq 0)
if (-not $hasPyInstaller) {
  Write-Host "Installing PyInstaller..."
  & $python -m pip install --upgrade pip
  # Use --user to avoid permission issues on some systems
  & $python -m pip install --user pyinstaller
  # Re-check
  & $python -c "import PyInstaller" 2>$null
  $hasPyInstaller = ($LASTEXITCODE -eq 0)
  if (-not $hasPyInstaller) {
    throw "PyInstaller is not available after installation. Ensure pip installs to the same Python ($python)."
  }
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
