@echo off
REM Check if PPE-Watch Telegram Bot is running

echo ======================================
echo PPE-Watch Bot Status Check
echo ======================================
echo.

REM Check if pythonw.exe is running telegram_bot_interactive.py
tasklist /fi "imagename eq pythonw.exe" /v | findstr /i "telegram_bot_interactive" >nul 2>&1

if %errorlevel% equ 0 (
    echo Status: RUNNING
    echo.
    echo Process details:
    wmic process where "name='pythonw.exe' and CommandLine like '%%telegram_bot_interactive%%'" get ProcessId,CreationDate,WorkingSetSize
) else (
    echo Status: NOT RUNNING
    echo.
    echo Use start_bot_background.bat to start the bot.
)

echo.
echo ======================================
echo Latest log entries:
echo ======================================

REM Change to project directory to check logs
cd /d "%~dp0.."

if exist logs\bot.log (
    powershell -command "Get-Content logs\bot.log -Tail 10"
) else (
    echo No log file found.
)

echo.
pause
