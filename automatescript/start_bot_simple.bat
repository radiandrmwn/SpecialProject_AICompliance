@echo off
REM Simple bot starter - Direct Python call

REM Change to project directory (parent of automatescript)
cd /d "%~dp0.."

REM Set PYTHONPATH to project root so src module can be found
set PYTHONPATH=%CD%

echo Starting bot...
echo.

REM Call Python directly without launcher
call .venv\Scripts\python.exe src\delivery\telegram_bot_interactive.py

echo.
echo Bot stopped.
pause
