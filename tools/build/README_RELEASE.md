# Build and Release (Windows)

Everything you need to ship a Windows build lives in `tools/build/`.

## Prerequisites
- Windows 10/11
- Python 3.10+ on PATH
- Inno Setup (for the installer): https://jrsoftware.org/isinfo.php (recommended)

## Local build (EXE)
1) Right‑click `tools/build/build_exe.ps1` → “Run with PowerShell”.
  - Installs PyInstaller if needed
  - Produces: `dist/MinecraftFarmCalc/MinecraftFarmCalc.exe`
  - Bundles: `recepies.json`, `recepies/`, `pic/`
  - Optional icon: place `tools/build/app.ico` to brand the EXE

## Local build (Installer)
1) Open `tools/build/installer.iss` in Inno Setup Compiler
2) Build (F9)
  - Output: `dist/installer/MinecraftFarmCalculator-Setup.exe`

## Ship it on GitHub Releases
Two options:
- Recommended: Upload the installer EXE; also attach a portable ZIP for advanced users.
- Alternative: Only the installer.

Manual steps:
1) Create a new release on GitHub (Draft → “Publish release”)
2) Upload:
  - `dist/installer/MinecraftFarmCalculator-Setup.exe`
  - (Optional) a ZIP of `dist/MinecraftFarmCalc/`
3) Add short notes and checksums if desired

CI (optional): a GitHub Actions workflow can build and attach artifacts when you push a version tag. See `.github/workflows/release.yml` if present.

## Artifacts
- One‑folder app: `dist/MinecraftFarmCalc/`
- Installer: `dist/installer/MinecraftFarmCalculator-Setup.exe`
- Optional portable ZIP: `MinecraftFarmCalc-Portable.zip`

## Tips
- Missing images: Right‑click a material → “Set image…”.
- SmartScreen/AV: Code‑sign the EXE/installer or offer both installer + ZIP.
- Virtualenv: Activate it before running the PowerShell script to bundle the right env.
