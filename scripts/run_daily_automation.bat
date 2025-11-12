@echo off
REM ========================================
REM PPE-Watch Daily Automation
REM ========================================
REM
REM This batch file runs the daily report automation.
REM Designed to be scheduled via Windows Task Scheduler.
REM
REM Schedule: Daily at 18:00
REM ========================================

echo ========================================
echo PPE-Watch Daily Automation
echo ========================================
echo Starting at %DATE% %TIME%
echo.

REM Change to project directory
cd /d "C:\Users\Radian Try\Documents\2nd Asia University (TW)\2nd Semester\SpecialProject"

REM Run automation script
python scripts\daily_report_automation.py

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS: Automation completed
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ERROR: Automation failed with code %ERRORLEVEL%
    echo ========================================
)

echo.
echo Finished at %DATE% %TIME%
echo.

REM Keep window open if run manually (not from Task Scheduler)
if "%1" NEQ "scheduled" (
    echo Press any key to close...
    pause >nul
)

exit /b %ERRORLEVEL%
