@echo off
setlocal
cd /d "%~dp0"
python mina.py
if errorlevel 1 (
  echo.
  echo The application stopped with an error.
  pause
)
