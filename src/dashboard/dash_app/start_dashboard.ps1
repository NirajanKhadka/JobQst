# JobLens Dash Dashboard Launcher for PowerShell
# This script activates the conda environment and starts the dashboard

Write-Host "Starting JobLens Dash Dashboard..." -ForegroundColor Green
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "app.py")) {
    Write-Host "Error: app.py not found. Please run this script from the dashboard directory." -ForegroundColor Red
    Write-Host "Expected location: src\dashboard\dash_app\" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate conda environment
Write-Host "Activating conda environment..." -ForegroundColor Blue
try {
    conda activate auto_job
    if ($LASTEXITCODE -ne 0) {
        throw "Conda activation failed"
    }
} catch {
    Write-Host "Error: Could not activate auto_job conda environment" -ForegroundColor Red
    Write-Host "Please ensure the environment exists: conda create -n auto_job python=3.9" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Environment activated successfully" -ForegroundColor Green
Write-Host ""
Write-Host "Starting dashboard..." -ForegroundColor Blue
Write-Host "Dashboard will be available at: http://127.0.0.1:8050" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the dashboard" -ForegroundColor Yellow
Write-Host ""

# Start the dashboard
python app.py

Read-Host "Press Enter to exit"