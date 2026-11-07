@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv || goto :error
  .venv\Scripts\python.exe -m pip install --upgrade pip || goto :error
  .venv\Scripts\python.exe -m pip install -e . || goto :error
)
.venv\Scripts\python.exe -m gothic_repair.app
exit /b %errorlevel%
:error
echo Setup failed. Verify Python 3.10 or newer is installed.
pause
exit /b 1

