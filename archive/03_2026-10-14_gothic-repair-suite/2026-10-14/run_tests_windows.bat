@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" call launch_windows.bat
.venv\Scripts\python.exe -m pip install -e ".[test]"
.venv\Scripts\python.exe -m pytest

