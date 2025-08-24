@echo off
REM JobLens Dash Dashboard Launcher for Windows
REM This script activates the conda environment and starts the dashboard

echo Starting JobLens Dash Dashboard...
echo.

REM Check if we're in the right directory
if not exist "app.py" (
    echo Error: app.py not found. Please run this script from the dashboard directory.
    echo Expected location: src\dashboard\dash_app\
    pause
    exit /b 1
)

REM Activate conda environment and run the dashboard
call conda activate auto_job
if %errorlevel% neq 0 (
    echo Error: Could not activate auto_job conda environment
    echo Please ensure the environment exists: conda create -n auto_job python=3.9
    pause
    exit /b 1
)

echo Environment activated successfully
echo.
echo Starting dashboard...
echo Dashboard will be available at: http://127.0.0.1:8050
echo.
echo Press Ctrl+C to stop the dashboard
echo.

python app.py

pause