[Setup]
; App Information
AppName=Multi Reference Downloader
AppVersion=1.1.0
AppPublisher=Academic Open Access Tools
AppPublisherURL=https://github.com/
AppSupportURL=https://github.com/
AppUpdatesURL=https://github.com/

; Default installation folder
DefaultDirName={autopf}\Multi Reference Downloader
DisableProgramGroupPage=yes

; EULA / License file to display during setup
LicenseFile=license.txt

; Icon for the Installer itself
SetupIconFile=icon.ico

; Output installer settings
OutputDir=installer_build
OutputBaseFilename=Multi_Reference_Downloader_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copy the compiled PyInstaller output
Source: "dist\Multi_Reference_Downloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Copy the license file, icon, and watermark
Source: "license.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "github_icon.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Multi Reference Downloader"; Filename: "{app}\Multi_Reference_Downloader.exe"; IconFilename: "{app}\icon.ico"
Name: "{autodesktop}\Multi Reference Downloader"; Filename: "{app}\Multi_Reference_Downloader.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\Multi_Reference_Downloader.exe"; Description: "{cm:LaunchProgram,Multi Reference Downloader}"; Flags: nowait postinstall skipifsilent
