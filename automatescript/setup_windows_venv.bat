@echo off
REM Setup Windows Virtual Environment for PPE-Watch

echo ========================================
echo PPE-Watch - Windows venv Setup
echo ========================================
echo.

REM Change to project directory (parent of automatescript)
cd /d "%~dp0.."

REM Check if old venv exists
if exist .venv (
    echo Old venv found, backing up...
    if exist .venv_backup rmdir /s /q .venv_backup
    ren .venv .venv_backup
    echo Backup created: .venv_backup
    echo.
)

echo Creating new Windows virtual environment...
python -m venv .venv
if %errorlevel% neq 0 (
    echo Python not found with 'python' command, trying 'py'...
    py -m venv .venv
)

if not exist .venv\Scripts\python.exe (
    echo.
    echo ERROR: Failed to create virtual environment!
    echo Please install Python for Windows from python.org
    pause
    exit /b 1
)

echo.
echo Virtual environment created successfully!
echo.

echo Installing requirements...
.venv\Scripts\pip install -U pip
.venv\Scripts\pip install -r requirements.txt

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo You can now run the bot with:
echo   automatescript\start_bot_simple.bat
echo.
pause
