Write-Host "Starting Local Report Generation API on port 8001..." -ForegroundColor Green
Write-Host ""

$reportGenPath = Join-Path (Split-Path $PSScriptRoot -Parent) "Report Generation"
Set-Location $reportGenPath

if (-not (Test-Path "run_report_system.py")) {
    Write-Host "Error: run_report_system.py not found in Report Generation directory" -ForegroundColor Red
    Write-Host "Please make sure you're running this from the UI Code directory" -ForegroundColor Red
    Write-Host "and that the Report Generation directory exists at the project root" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Found Report Generation directory" -ForegroundColor Green
Write-Host "Starting the API server..." -ForegroundColor Green
Write-Host ""
Write-Host "The API will be available at: http://localhost:8001" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

try {
    python run_report_system.py
}
catch {
    Write-Host ""
    Write-Host "Error starting the report API: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Report Generation API has stopped" -ForegroundColor Yellow
Read-Host "Press Enter to exit"
