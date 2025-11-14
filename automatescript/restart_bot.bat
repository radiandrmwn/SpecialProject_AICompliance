@echo off
REM Restart PPE-Watch Telegram Bot

echo Restarting PPE-Watch Telegram Bot...

REM Stop bot first
call "%~dp0stop_bot.bat"

REM Wait a moment
timeout /t 2 /nobreak >nul

REM Start bot again
call "%~dp0start_bot_background.bat"

echo Bot restarted!
