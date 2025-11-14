@echo off
REM Stop PPE-Watch Telegram Bot

echo Stopping PPE-Watch Telegram Bot...

REM Kill all pythonw.exe processes running telegram_bot_interactive.py
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq pythonw.exe" /fo list ^| findstr /i "PID"') do (
    wmic process where "ProcessId=%%a and CommandLine like '%%telegram_bot_interactive%%'" delete 2>nul
)

echo Bot stopped!
timeout /t 2 /nobreak >nul
