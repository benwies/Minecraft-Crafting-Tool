; Inno Setup script for Minecraft Farm Calculator
#define MyAppName "Minecraft Farm Calculator"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Your Name or Org"
#define MyAppExeName "MinecraftFarmCalc.exe"
#define MyAppFolderName "Minecraft Farm Calculator"

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
OutputBaseFilename=MinecraftFarmCalculator-Setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Include everything from the PyInstaller one-folder dir at repo root
Source: "{#SourcePath}\..\..\dist\MinecraftFarmCalc\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
