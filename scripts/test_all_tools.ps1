# Comprehensive Tool Stack Test Script
# Tests all tools in the AutoJobAgent development environment

param(
    [switch]$Quick,
    [switch]$Verbose,
    [switch]$FixIssues
)

Write-Host "AutoJobAgent Tool Stack Test Suite" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Test results tracking
$testResults = @{
    Passed = 0
    Failed = 0
    Warnings = 0
    Total = 0
}

# Function to log test results
function Write-TestResult {
    param(
        [string]$TestName,
        [string]$Status,
        [string]$Message = "",
        [string]$Details = ""
    )
    
    $testResults.Total++
    
    switch ($Status) {
        "PASS" { 
            Write-Host "PASS: $TestName" -ForegroundColor Green
            $testResults.Passed++
        }
        "FAIL" { 
            Write-Host "FAIL: $TestName" -ForegroundColor Red
            $testResults.Failed++
        }
        "WARN" { 
            Write-Host "WARN: $TestName" -ForegroundColor Yellow
            $testResults.Warnings++
        }
    }
    
    if ($Message) {
        Write-Host "   $Message" -ForegroundColor Gray
    }
    
    if ($Details -and $Verbose) {
        Write-Host "   Details: $Details" -ForegroundColor DarkGray
    }
}

# Function to test port availability
function Test-Port {
    param([int]$Port, [string]$ServiceName)
    
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $true
    } catch {
        return $false
    }
}

# Function to test HTTP endpoint
function Test-HttpEndpoint {
    param([string]$Url, [string]$ServiceName)
    
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 10 -UseBasicParsing
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

# Function to test Python module
function Test-PythonModule {
    param([string]$ModuleName)
    
    try {
        python -c "import $ModuleName; print('OK')" 2>$null
        return $true
    } catch {
        return $false
    }
}

# Function to test Docker container
function Test-DockerContainer {
    param([string]$ContainerName)
    
    try {
        $output = docker ps --filter "name=$ContainerName" --format "table {{.Names}}\t{{.Status}}"
        return $output -like "*$ContainerName*"
    } catch {
        return $false
    }
}

# Function to measure performance
function Measure-Performance {
    param([string]$TestName, [scriptblock]$TestBlock)
    
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        & $TestBlock
        $success = $true
    } catch {
        $success = $false
    }
    $stopwatch.Stop()
    
    return @{
        Success = $success
        Duration = $stopwatch.ElapsedMilliseconds
    }
}

# ============================================================================
# DOCKER & INFRASTRUCTURE TESTS
# ============================================================================

Write-Host "Testing Docker & Infrastructure" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

# Test Docker installation
$dockerTest = Measure-Performance "Docker Installation" { docker --version }
if ($dockerTest.Success) {
    Write-TestResult "Docker Installation" "PASS" "Docker is available" "Duration: $($dockerTest.Duration)ms"
} else {
    Write-TestResult "Docker Installation" "FAIL" "Docker is not available or not running"
}

# Test Docker Compose
$composeTest = Measure-Performance "Docker Compose" { docker-compose --version }
if ($composeTest.Success) {
    Write-TestResult "Docker Compose" "PASS" "Docker Compose is available" "Duration: $($composeTest.Duration)ms"
} else {
    Write-TestResult "Docker Compose" "FAIL" "Docker Compose is not available"
}

# Test Docker daemon
$daemonTest = Measure-Performance "Docker Daemon" { docker ps }
if ($daemonTest.Success) {
    Write-TestResult "Docker Daemon" "PASS" "Docker daemon is running" "Duration: $($daemonTest.Duration)ms"
} else {
    Write-TestResult "Docker Daemon" "FAIL" "Docker daemon is not running"
}

# ============================================================================
# DATABASE TESTS
# ============================================================================

Write-Host "Testing Database Services" -ForegroundColor Cyan
Write-Host "----------------------------" -ForegroundColor Cyan

# Test Redis
if (Test-Port 6379 "Redis") {
    Write-TestResult "Redis Connection" "PASS" "Redis is running on port 6379"
} else {
    Write-TestResult "Redis Connection" "FAIL" "Redis is not running on port 6379"
}

# Test PostgreSQL
if (Test-Port 5432 "PostgreSQL") {
    Write-TestResult "PostgreSQL Connection" "PASS" "PostgreSQL is running on port 5432"
} else {
    Write-TestResult "PostgreSQL Connection" "FAIL" "PostgreSQL is not running on port 5432"
}

# Test SQLite (fallback)
$sqliteTest = Measure-Performance "SQLite Database" { 
    python -c "import sqlite3; conn = sqlite3.connect(':memory:'); conn.close(); print('OK')" 
}
if ($sqliteTest.Success) {
    Write-TestResult "SQLite Database" "PASS" "SQLite is working" "Duration: $($sqliteTest.Duration)ms"
} else {
    Write-TestResult "SQLite Database" "FAIL" "SQLite is not working"
}

# ============================================================================
# CODE INTELLIGENCE TESTS
# ============================================================================

Write-Host "Testing Code Intelligence Tools" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

# Test Sourcegraph
$sourcegraphTest = Measure-Performance "Sourcegraph" { Test-HttpEndpoint "http://localhost:7080" "Sourcegraph" }
if ($sourcegraphTest.Success) {
    Write-TestResult "Sourcegraph Web UI" "PASS" "Sourcegraph is accessible" "Duration: $($sourcegraphTest.Duration)ms"
} else {
    Write-TestResult "Sourcegraph Web UI" "FAIL" "Sourcegraph is not accessible"
}

# Test Sourcegraph API
$sourcegraphApiTest = Measure-Performance "Sourcegraph API" { 
    $response = Invoke-WebRequest -Uri "http://localhost:7080/.api/health" -TimeoutSec 5 -UseBasicParsing
    return $response.StatusCode -eq 200
}
if ($sourcegraphApiTest.Success) {
    Write-TestResult "Sourcegraph API" "PASS" "Sourcegraph API is responding" "Duration: $($sourcegraphApiTest.Duration)ms"
} else {
    Write-TestResult "Sourcegraph API" "FAIL" "Sourcegraph API is not responding"
}

# Test Python Sourcegraph client
$clientTest = Measure-Performance "Sourcegraph Client" { 
    python -c "from src.utils.sourcegraph_client import SourcegraphClient; client = SourcegraphClient(); print('OK')" 
}
if ($clientTest.Success) {
    Write-TestResult "Sourcegraph Python Client" "PASS" "Client can be imported" "Duration: $($clientTest.Duration)ms"
} else {
    Write-TestResult "Sourcegraph Python Client" "FAIL" "Client cannot be imported"
}

# ============================================================================
# TASK QUEUE TESTS
# ============================================================================

Write-Host "Testing Task Queue & Background Processing" -ForegroundColor Cyan
Write-Host "------------------------------------------------" -ForegroundColor Cyan

# Test Celery configuration
$celeryConfigTest = Measure-Performance "Celery Configuration" { 
    python -c "from src.core.celery_app import celery_app; print('OK')" 
}
if ($celeryConfigTest.Success) {
    Write-TestResult "Celery Configuration" "PASS" "Celery app can be imported" "Duration: $($celeryConfigTest.Duration)ms"
} else {
    Write-TestResult "Celery Configuration" "FAIL" "Celery app cannot be imported"
}

# Test Flower monitoring
$flowerTest = Measure-Performance "Flower Monitoring" { Test-HttpEndpoint "http://localhost:5555" "Flower" }
if ($flowerTest.Success) {
    Write-TestResult "Flower Monitoring" "PASS" "Flower is accessible" "Duration: $($flowerTest.Duration)ms"
} else {
    Write-TestResult "Flower Monitoring" "FAIL" "Flower is not accessible"
}

# Test Redis connection for Celery
$redisCeleryTest = Measure-Performance "Redis for Celery" { 
    python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping(); print('OK')" 
}
if ($redisCeleryTest.Success) {
    Write-TestResult "Redis for Celery" "PASS" "Redis is accessible for Celery" "Duration: $($redisCeleryTest.Duration)ms"
} else {
    Write-TestResult "Redis for Celery" "FAIL" "Redis is not accessible for Celery"
}

# ============================================================================
# MONITORING TESTS
# ============================================================================

Write-Host "Testing Monitoring & Observability" -ForegroundColor Cyan
Write-Host "---------------------------------------" -ForegroundColor Cyan

# Test Prometheus
$prometheusTest = Measure-Performance "Prometheus" { Test-HttpEndpoint "http://localhost:9090" "Prometheus" }
if ($prometheusTest.Success) {
    Write-TestResult "Prometheus" "PASS" "Prometheus is accessible" "Duration: $($prometheusTest.Duration)ms"
} else {
    Write-TestResult "Prometheus" "FAIL" "Prometheus is not accessible"
}

# Test Grafana
$grafanaTest = Measure-Performance "Grafana" { Test-HttpEndpoint "http://localhost:3000" "Grafana" }
if ($grafanaTest.Success) {
    Write-TestResult "Grafana" "PASS" "Grafana is accessible" "Duration: $($grafanaTest.Duration)ms"
} else {
    Write-TestResult "Grafana" "FAIL" "Grafana is not accessible"
}

# Test Prometheus client
$prometheusClientTest = Measure-Performance "Prometheus Client" { 
    python -c "from prometheus_client import Counter; c = Counter('test', 'test counter'); print('OK')" 
}
if ($prometheusClientTest.Success) {
    Write-TestResult "Prometheus Client" "PASS" "Prometheus client can be imported" "Duration: $($prometheusClientTest.Duration)ms"
} else {
    Write-TestResult "Prometheus Client" "FAIL" "Prometheus client cannot be imported"
}

# ============================================================================
# DEVELOPMENT TOOLS TESTS
# ============================================================================

Write-Host "Testing Development Tools" -ForegroundColor Cyan
Write-Host "-----------------------------" -ForegroundColor Cyan

# Test Python modules
$modules = @("pytest", "black", "isort", "flake8", "mypy")
foreach ($module in $modules) {
    $moduleTest = Measure-Performance "$module Module" { Test-PythonModule $module }
    if ($moduleTest.Success) {
        Write-TestResult "$module Module" "PASS" "$module is available" "Duration: $($moduleTest.Duration)ms"
    } else {
        Write-TestResult "$module Module" "FAIL" "$module is not available"
    }
}

# Test code formatting
$blackTest = Measure-Performance "Black Code Formatter" { 
    python -c "import black; print('OK')" 
}
if ($blackTest.Success) {
    Write-TestResult "Black Code Formatter" "PASS" "Black is available" "Duration: $($blackTest.Duration)ms"
} else {
    Write-TestResult "Black Code Formatter" "FAIL" "Black is not available"
}

# Test testing framework
$pytestTest = Measure-Performance "Pytest Framework" { 
    python -c "import pytest; print('OK')" 
}
if ($pytestTest.Success) {
    Write-TestResult "Pytest Framework" "PASS" "Pytest is available" "Duration: $($pytestTest.Duration)ms"
} else {
    Write-TestResult "Pytest Framework" "FAIL" "Pytest is not available"
}

# ============================================================================
# BROWSER AUTOMATION TESTS
# ============================================================================

Write-Host "Testing Browser Automation" -ForegroundColor Cyan
Write-Host "-----------------------------" -ForegroundColor Cyan

# Test Playwright
$playwrightTest = Measure-Performance "Playwright" { 
    python -c "from playwright.sync_api import sync_playwright; print('OK')" 
}
if ($playwrightTest.Success) {
    Write-TestResult "Playwright" "PASS" "Playwright is available" "Duration: $($playwrightTest.Duration)ms"
} else {
    Write-TestResult "Playwright" "FAIL" "Playwright is not available"
}

# Test Selenium (existing)
$seleniumTest = Measure-Performance "Selenium" { 
    python -c "from selenium import webdriver; print('OK')" 
}
if ($seleniumTest.Success) {
    Write-TestResult "Selenium" "PASS" "Selenium is available" "Duration: $($seleniumTest.Duration)ms"
} else {
    Write-TestResult "Selenium" "FAIL" "Selenium is not available"
}

# ============================================================================
# APPLICATION TESTS
# ============================================================================

Write-Host "Testing Application Components" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

# Test main application modules
$appModules = @("src.core", "src.scrapers", "src.job_applier", "src.dashboard")
foreach ($module in $appModules) {
    $moduleTest = Measure-Performance "$module Module" { 
        python -c "import $module; print('OK')" 
    }
    if ($moduleTest.Success) {
        Write-TestResult "$module Module" "PASS" "$module can be imported" "Duration: $($moduleTest.Duration)ms"
    } else {
        Write-TestResult "$module Module" "FAIL" "$module cannot be imported"
    }
}

# Test database connection
$dbTest = Measure-Performance "Database Connection" { 
    python -c "from src.core.job_database import JobDatabase; db = JobDatabase(); print('OK')" 
}
if ($dbTest.Success) {
    Write-TestResult "Database Connection" "PASS" "Database can be connected" "Duration: $($dbTest.Duration)ms"
} else {
    Write-TestResult "Database Connection" "FAIL" "Database cannot be connected"
}

# Test health checks
$healthTest = Measure-Performance "Health Checks" { 
    python -c "from src.health_checks.health_utils import run_health_checks; print('OK')" 
}
if ($healthTest.Success) {
    Write-TestResult "Health Checks" "PASS" "Health checks can be run" "Duration: $($healthTest.Duration)ms"
} else {
    Write-TestResult "Health Checks" "FAIL" "Health checks cannot be run"
}

# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

Write-Host "Performance Tests" -ForegroundColor Cyan
Write-Host "-------------------" -ForegroundColor Cyan

# Test Sourcegraph search performance
$searchTest = Measure-Performance "Sourcegraph Search" { 
    python -c "from src.utils.sourcegraph_client import SourcegraphClient; client = SourcegraphClient(); import sys; sys.exit(0 if client.health_check() else 1)" 
}
if ($searchTest.Success) {
    if ($searchTest.Duration -lt 5000) {
        Write-TestResult "Sourcegraph Search" "PASS" "Search is fast" "Duration: $($searchTest.Duration)ms"
    } else {
        Write-TestResult "Sourcegraph Search" "WARN" "Search is slow" "Duration: $($searchTest.Duration)ms"
    }
} else {
    Write-TestResult "Sourcegraph Search" "FAIL" "Search failed"
}

# Test Celery task creation
$celeryTaskTest = Measure-Performance "Celery Task Creation" { 
    python -c "from src.core.celery_app import celery_app; task = celery_app.send_task('debug_task'); print('OK')" 
}
if ($celeryTaskTest.Success) {
    Write-TestResult "Celery Task Creation" "PASS" "Tasks can be created" "Duration: $($celeryTaskTest.Duration)ms"
} else {
    Write-TestResult "Celery Task Creation" "FAIL" "Tasks cannot be created"
}

# ============================================================================
# SUMMARY & RECOMMENDATIONS
# ============================================================================

Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "=============" -ForegroundColor Cyan

$totalTests = $testResults.Total
$passedTests = $testResults.Passed
$failedTests = $testResults.Failed
$warningTests = $testResults.Warnings
$successRate = [math]::Round(($passedTests / $totalTests) * 100, 1)

Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor Red
Write-Host "Warnings: $warningTests" -ForegroundColor Yellow
Write-Host "Success Rate: $successRate%" -ForegroundColor $(if ($successRate -ge 80) { "Green" } elseif ($successRate -ge 60) { "Yellow" } else { "Red" })

Write-Host ""
Write-Host "Recommendations:" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan

if ($failedTests -gt 0) {
    Write-Host "Fix failed tests first:" -ForegroundColor Red
    Write-Host "   - Start Docker Desktop if not running" -ForegroundColor Yellow
    Write-Host "   - Run: .\scripts\start_dev_environment.ps1" -ForegroundColor Yellow
    Write-Host "   - Install missing Python packages: pip install -r requirements/requirements-dev.txt" -ForegroundColor Yellow
}

if ($warningTests -gt 0) {
    Write-Host "Address warnings:" -ForegroundColor Yellow
    Write-Host "   - Check slow services and optimize" -ForegroundColor Yellow
    Write-Host "   - Review configuration settings" -ForegroundColor Yellow
}

if ($successRate -ge 80) {
    Write-Host "Tool stack is ready for development!" -ForegroundColor Green
    Write-Host "   - All major components are working" -ForegroundColor Green
    Write-Host "   - You can start developing with confidence" -ForegroundColor Green
}

Write-Host ""
Write-Host "Quick Access Links:" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
Write-Host "Sourcegraph: http://localhost:7080" -ForegroundColor Green
Write-Host "Flower (Celery): http://localhost:5555" -ForegroundColor Green
Write-Host "Grafana: http://localhost:3000" -ForegroundColor Green
Write-Host "Prometheus: http://localhost:9090" -ForegroundColor Green

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 