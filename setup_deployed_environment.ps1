# PowerShell Environment Configuration for PharmaCopilot Deployment
# This script sets up environment variables for the deployed system

Write-Host "Setting up PharmaCopilot environment variables..." -ForegroundColor Green

# Set the deployed prediction API endpoint
$env:PREDICTION_API_URL = "http://165.22.211.17:8000"

# Set other configuration variables
$env:REPORT_API_PORT = "8001"
$env:UI_SERVER_PORT = "3001"

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host " PharmaCopilot Environment Configuration" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host " PREDICTION_API_URL: $env:PREDICTION_API_URL" -ForegroundColor Yellow
Write-Host " REPORT_API_PORT: $env:REPORT_API_PORT" -ForegroundColor Yellow
Write-Host " UI_SERVER_PORT: $env:UI_SERVER_PORT" -ForegroundColor Yellow
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Environment variables set successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To start the systems:" -ForegroundColor White
Write-Host ' 1. UI Server: cd "UI Code"; node server_fixed.js' -ForegroundColor Gray
Write-Host ' 2. Report API: cd "Report Generation"; python simple_run.py' -ForegroundColor Gray
Write-Host ' 3. React Client: cd "UI Code\client"; npm start' -ForegroundColor Gray
Write-Host ""
Write-Host "To test the deployed API directly:" -ForegroundColor White
Write-Host " Invoke-RestMethod -Uri $env:PREDICTION_API_URL/api/health" -ForegroundColor Gray
Write-Host ""

# Keep the PowerShell session open
Read-Host "Press Enter to continue..."
