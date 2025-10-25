# Build and Release (Windows)

Everything you need to ship a Windows build lives in `tools/build/`.

## Prerequisites
- Windows 10/11
- Python 3.10+ on PATH
- Inno Setup (for the installer):
  - Quick install (recommended):
    - `winget install Jrsoftware.InnoSetup`
  - Or download: https://jrsoftware.org/isdl.php

## Local build (EXE)
1) Right‑click `tools/build/build_exe.ps1` → “Run with PowerShell”.
  - Installs PyInstaller if needed
  - Produces: `dist/MCCraftingCalculator/MCCraftingCalculator.exe`
  - Bundles: `recepies.json`, `recepies/`, `pic/`
  - Optional icon: place `tools/build/app.ico` to brand the EXE

## Local build (Installer)
Two ways:

1) Command line (after installing Inno Setup):
  - Run: `& tools/build/build_installer.ps1` (supports `-Version` and `-Publisher` overrides)
  - Output: `dist/installer/MCCraftingCalculator-Setup.exe`

2) GUI compiler:
  - Open `tools/build/installer.iss` in Inno Setup Compiler, then press F9
  - Output: `dist/installer/MCCraftingCalculator-Setup.exe`

## One-shot build (EXE + ZIP + Installer)
- Use `& tools/build/build_all.ps1`
  - Builds EXE, creates a portable ZIP, and compiles the installer if Inno Setup is installed.

## Ship it on GitHub Releases
Two options:
- Recommended: Upload the installer EXE; also attach a portable ZIP for advanced users.
- Alternative: Only the installer.

Manual steps:
1) Create a new release on GitHub (Draft → “Publish release”)
2) Upload:
  - `dist/installer/MCCraftingCalculator-Setup.exe`
  - (Optional) a ZIP of `dist/MCCraftingCalculator/`
3) Add short notes and checksums if desired

CI (optional): a GitHub Actions workflow can build and attach artifacts when you push a version tag. See `.github/workflows/release.yml` if present.

## Artifacts
- One‑folder app: `dist/MCCraftingCalculator/`
- Installer: `dist/installer/MCCraftingCalculator-Setup.exe`
- Optional portable ZIP: `dist/MCCraftingCalculator-portable.zip`

## Tips
- Missing images: Right‑click a material → “Set image…”.
- SmartScreen/AV: Code‑sign the EXE/installer or offer both installer + ZIP.
- Virtualenv: Activate it before running the PowerShell script to bundle the right env.
