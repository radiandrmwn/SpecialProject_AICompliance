@echo off
REM PPE-Watch Telegram Bot - Background Startup Script
REM This script starts the Telegram bot in the background (minimized window)

echo Starting PPE-Watch Telegram Bot in background...
echo Bot will run minimized. Check logs/bot.log for output.

REM Change to project directory (parent of automatescript)
cd /d "%~dp0.."

REM Set PYTHONPATH so imports work
set PYTHONPATH=%CD%

REM Start bot using python.exe with minimized window
start /min "" ".venv\Scripts\python.exe" "src\delivery\telegram_bot_interactive.py"

echo Bot started! Check logs/bot.log to verify.
echo You can close this window - bot is running minimized.
timeout /t 5 /nobreak >nul
