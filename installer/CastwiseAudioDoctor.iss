; Castwise Audio Doctor 1.3.0
#define MyAppName "Castwise Audio Doctor"
#define MyAppVersion "3.1.0"
#define MyPublisher "Castwise Studio"
#define MyExeName "CastwiseAudioDoctor.exe"

[Setup]
AppId={{8B6E1B9A-6B40-4D1D-A4AA-CA7F8B2A1C30}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyPublisher}
DefaultDirName={autopf}\Castwise Audio Doctor
DefaultGroupName=Castwise Audio Doctor
OutputDir=installer
OutputBaseFilename=Castwise-Audio-Doctor-Setup-{#MyAppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyExeName}

[Files]
Source: "dist\CastwiseAudioDoctor\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\Castwise Audio Doctor"; Filename: "{app}\{#MyExeName}"
Name: "{commondesktop}\Castwise Audio Doctor"; Filename: "{app}\{#MyExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"

[Run]
Filename: "{app}\{#MyExeName}"; Description: "Launch Castwise Audio Doctor"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
