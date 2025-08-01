@echo off
echo Starting Local Report Generation API on port 8001...
echo.

cd /d "%~dp0..\Report Generation"

if not exist "run_report_system.py" (
    echo Error: run_report_system.py not found in Report Generation directory
    echo Please make sure you're running this from the UI Code directory
    echo and that the Report Generation directory exists at the project root
    pause
    exit /b 1
)

echo Found Report Generation directory
echo Starting the API server...
echo.
echo The API will be available at: http://localhost:8001
echo.
echo Press Ctrl+C to stop the server
echo.

python run_report_system.py

echo.
echo Report Generation API has stopped
pause
