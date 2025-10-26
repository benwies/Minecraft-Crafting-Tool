; Inno Setup script for MC Crafting Calculator
; Allow command-line overrides for defines (passed via ISCC /D switches)
#ifndef MyAppName
	#define MyAppName "MC Crafting Calculator"
#endif
#ifndef MyAppVersion
	#define MyAppVersion "1.0.0"
#endif
#ifndef MyAppPublisher
	#define MyAppPublisher "Your Name or Org"
#endif
#ifndef MyAppExeName
	#define MyAppExeName "MCCraftingCalculator.exe"
#endif
#ifndef MyAppFolderName
	#define MyAppFolderName "MC Crafting Calculator"
#endif

; Optional signing parameters (set via /DSignPfxPath=..., /DSignPfxPassword=..., /DTimestampUrl=...)
#ifndef TimestampUrl
	#define TimestampUrl "http://timestamp.digicert.com"
#endif

[Setup]
AppId={{A8C84F6E-44B6-4F46-80E9-2E3C7D9B1C49}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppFolderName}
DisableDirPage=no
DefaultGroupName={#MyAppFolderName}
DisableProgramGroupPage=no
; Output relative to repo root (two levels up from this script)
OutputDir={#SourcePath}\..\..\dist\installer
OutputBaseFilename=MCCraftingCalculator-Setup
Compression=lzma
SolidCompression=yes
; Use recommended architecture identifier to avoid deprecation warnings
ArchitecturesInstallIn64BitMode=x64compatible
; Show license during install
LicenseFile={#SourcePath}\..\..\LICENSE
#ifdef MyAppIcon
SetupIconFile={#MyAppIcon}
#endif
#ifdef SignPfxPath
; Enable signing of installer and uninstaller when PFX is supplied
SignTool=SignToolCmd
SignedUninstaller=yes
#endif

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Include everything from the PyInstaller one-folder dir at repo root
Source: "{#SourcePath}\..\..\dist\MCCraftingCalculator\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

#ifdef SignPfxPath
[SignTools]
Name: "SignToolCmd"; Command: "signtool sign /fd SHA256 /f \"{#SignPfxPath}\" /p \"{#SignPfxPassword}\" /tr \"{#TimestampUrl}\" /td SHA256 $f"
#endif
