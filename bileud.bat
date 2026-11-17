@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "APP_NAME=SB3QuestCompleter"
set "ENTRY=%CD%\mina.py"
set "LOGO=%CD%\logo.ico"
set "ASSETS=%CD%\assets"
set "DIST=%CD%\dist"
set "BUILD=%CD%\build"

echo.
echo ==========================================
echo   SB3 Quest Completer - EXE Builder
echo ==========================================
echo.

if not exist "%ENTRY%" (
  echo ERROR: mina.py was not found in this folder.
  pause
  exit /b 1
)
if not exist "%LOGO%" (
  echo ERROR: logo.ico was not found in this folder.
  pause
  exit /b 1
)
if not exist "%ASSETS%\featured_games.json" (
  echo ERROR: assets\featured_games.json was not found.
  pause
  exit /b 1
)

echo [1/3] Installing build requirements...
python -m pip install --upgrade pyinstaller requests pillow pypresence
if errorlevel 1 (
  echo ERROR: Could not install the build requirements.
  pause
  exit /b 1
)

echo [2/3] Creating the EXE...
if exist "%DIST%" rmdir /s /q "%DIST%"
if exist "%BUILD%" rmdir /s /q "%BUILD%"
mkdir "%DIST%"

REM Use python -m PyInstaller so the builder uses the same Python where PyInstaller was installed.
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "%APP_NAME%" --icon "%LOGO%" --add-data "%LOGO%;." --add-data "%ASSETS%;assets" --distpath "%DIST%" --workpath "%BUILD%" --specpath "%BUILD%" "%ENTRY%"
if errorlevel 1 (
  echo ERROR: The EXE build failed. Read the output above for the exact cause.
  pause
  exit /b 1
)

if not exist "%DIST%\%APP_NAME%.exe" (
  echo ERROR: PyInstaller finished but %APP_NAME%.exe was not found in dist.
  pause
  exit /b 1
)

echo.
echo [3/3] SUCCESS
 echo EXE created here:
 echo %DIST%\%APP_NAME%.exe
 echo.
start "" explorer "%DIST%"
pause
