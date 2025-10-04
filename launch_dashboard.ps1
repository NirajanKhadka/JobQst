#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Launch JobLens Dashboard with proper environment activation
.DESCRIPTION
    Activates auto_job conda environment and launches the dashboard
    with the specified profile.
.PARAMETER Profile
    Profile name to use (default: Nirajan)
.PARAMETER Port
    Port to run dashboard on (default: 8050)
.EXAMPLE
    .\launch_dashboard.ps1 -Profile Nirajan
#>

param(
    [string]$Profile = "Nirajan",
    [int]$Port = 8050
)

Write-Host "🔥 JOBLENSLAUNCHER - SHIVA MODE ACTIVATED 🔥" -ForegroundColor Cyan
Write-Host ""

# Check if auto_job environment exists
$envExists = conda env list | Select-String "auto_job"
if (-not $envExists) {
    Write-Host "❌ ERROR: auto_job conda environment not found!" -ForegroundColor Red
    Write-Host "💡 Create it with: conda env create -f environment.yml" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found auto_job environment" -ForegroundColor Green

# Activate environment and run dashboard
Write-Host "🚀 Activating auto_job environment..." -ForegroundColor Cyan
Write-Host "📊 Launching dashboard for profile: $Profile" -ForegroundColor Cyan
Write-Host "🌐 Dashboard will be available at: http://localhost:$Port" -ForegroundColor Green
Write-Host ""
Write-Host "⚡ Starting in 3 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Run Python directly (environment should be pre-activated in VS Code terminal)
# If not, the conda activate command would be needed
python main.py $Profile --action dashboard --port $Port

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "❌ Dashboard launch failed!" -ForegroundColor Red
    Write-Host "💡 Troubleshooting steps:" -ForegroundColor Yellow
    Write-Host "   1. Verify you're in the auto_job environment: conda activate auto_job" -ForegroundColor Gray
    Write-Host "   2. Install dashboard dependencies: pip install -r src/dashboard/requirements_dash.txt" -ForegroundColor Gray
    Write-Host "   3. Check profile exists: python -c 'from src.core.user_profile_manager import UserProfileManager; pm = UserProfileManager(); print(pm.list_profiles())'" -ForegroundColor Gray
    Write-Host "   4. Run health check: python main.py $Profile --action health-check" -ForegroundColor Gray
    exit 1
}
