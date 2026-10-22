@echo off
rem Builds a standalone MCPScanner.exe (no Python needed to run it).
rem Output: dist\MCPScanner\MCPScanner.exe  (share the whole MCPScanner folder)
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (set PYTHON=py -3) else (set PYTHON=python)

if not exist ".venv\Scripts\python.exe" (
    %PYTHON% -m venv .venv
)

call ".venv\Scripts\activate.bat"
pip install -r requirements.txt pyinstaller --quiet
pyinstaller --noconfirm --windowed --name MCPScanner main.py
echo.
echo Done. Open dist\MCPScanner\MCPScanner.exe
pause
