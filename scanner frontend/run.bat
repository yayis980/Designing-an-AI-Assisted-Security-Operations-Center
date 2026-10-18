@echo off
rem Double-click this file to start the app. First run installs what it needs.
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (set PYTHON=py -3) else (set PYTHON=python)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PYTHON% -m venv .venv
)

call ".venv\Scripts\activate.bat"
pip install -r requirements.txt --quiet
python main.py
if %errorlevel% neq 0 pause
