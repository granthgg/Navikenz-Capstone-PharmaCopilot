@echo off
REM Environment Configuration for PharmaCopilot Deployment
REM This batch file sets up environment variables for the deployed system

echo Setting up PharmaCopilot environment variables...

REM Set the deployed prediction API endpoint
set PREDICTION_API_URL=http://165.22.211.17:8000

REM Set other configuration variables
set REPORT_API_PORT=8001
set UI_SERVER_PORT=3001

echo.
echo ================================================
echo  PharmaCopilot Environment Configuration
echo ================================================
echo  PREDICTION_API_URL: %PREDICTION_API_URL%
echo  REPORT_API_PORT: %REPORT_API_PORT%
echo  UI_SERVER_PORT: %UI_SERVER_PORT%
echo ================================================
echo.
echo Environment variables set successfully!
echo.
echo To start the systems:
echo  1. UI Server: cd "UI Code" ^&^& node server_fixed.js
echo  2. Report API: cd "Report Generation" ^&^& python simple_run.py
echo  3. React Client: cd "UI Code\client" ^&^& npm start
echo.
echo To test the deployed API directly:
echo  curl %PREDICTION_API_URL%/api/health
echo.

pause
