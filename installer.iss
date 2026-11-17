#define MyAppName "SB3 Quest Completer"
#define MyAppVersion "0.1.9"
#define MyAppPublisher "Sba3 Dev"
#define MyAppExeName "SB3QuestCompleter.exe"

[Setup]
AppId={{D7D4B76A-6F51-4F3A-8A43-4A2D6DB0C2E1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\SB3QuestCompleter
DefaultGroupName={#MyAppName}
OutputDir=installer-output
OutputBaseFilename=SB3QuestCompleter-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=yes
SetupIconFile=logo.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "logo.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Add a desktop shortcut"; GroupDescription: "Additional options:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall
