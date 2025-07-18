# Simple Tool Stack Test Script
# Tests essential components of the AutoJobAgent development environment

param(
    [switch]$Quick,
    [switch]$Verbose
)

Write-Host "AutoJobAgent Simple Test Suite" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host ""

# Test results tracking
$testResults = @{
    Passed = 0
    Failed = 0
    Total = 0
}

# Function to log test results
function Write-TestResult {
    param(
        [string]$TestName,
        [string]$Status,
        [string]$Message = ""
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
    }
    
    if ($Message) {
        Write-Host "   $Message" -ForegroundColor Gray
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
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec 5 -UseBasicParsing
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

# Function to test Python module
function Test-PythonModule {
    param([string]$ModuleName)
    
    try {
        $output = python -c "import $ModuleName; print('OK')" 2>$null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

# ============================================================================
# DOCKER & INFRASTRUCTURE TESTS
# ============================================================================

Write-Host "Testing Docker & Infrastructure" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

# Test Docker installation
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-TestResult "Docker Installation" "PASS" "Docker is available"
    } else {
        Write-TestResult "Docker Installation" "FAIL" "Docker is not available"
    }
} catch {
    Write-TestResult "Docker Installation" "FAIL" "Docker is not available"
}

# Test Docker daemon
try {
    $dockerPs = docker ps 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-TestResult "Docker Daemon" "PASS" "Docker daemon is running"
    } else {
        Write-TestResult "Docker Daemon" "FAIL" "Docker daemon is not running"
    }
} catch {
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

# Test SQLite
try {
    $sqliteTest = python -c "import sqlite3; print('OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-TestResult "SQLite Database" "PASS" "SQLite is working"
    } else {
        Write-TestResult "SQLite Database" "FAIL" "SQLite is not working"
    }
} catch {
    Write-TestResult "SQLite Database" "FAIL" "SQLite is not working"
}

# ============================================================================
# CODE INTELLIGENCE TESTS
# ============================================================================

Write-Host "Testing Code Intelligence Tools" -ForegroundColor Cyan
Write-Host "-----------------------------------" -ForegroundColor Cyan

# Test Sourcegraph
if (Test-HttpEndpoint "http://localhost:7080" "Sourcegraph") {
    Write-TestResult "Sourcegraph Web UI" "PASS" "Sourcegraph is accessible"
} else {
    Write-TestResult "Sourcegraph Web UI" "FAIL" "Sourcegraph is not accessible"
}

# Test Sourcegraph API
try {
    $response = Invoke-WebRequest -Uri "http://localhost:7080/.api/health" -TimeoutSec 5 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-TestResult "Sourcegraph API" "PASS" "Sourcegraph API is responding"
    } else {
        Write-TestResult "Sourcegraph API" "FAIL" "Sourcegraph API is not responding"
    }
} catch {
    Write-TestResult "Sourcegraph API" "FAIL" "Sourcegraph API is not responding"
}

# Test Python Sourcegraph client
try {
    $clientTest = python -c "from src.utils.sourcegraph_client import SourcegraphClient; print('OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-TestResult "Sourcegraph Python Client" "PASS" "Client can be imported"
    } else {
        Write-TestResult "Sourcegraph Python Client" "FAIL" "Client cannot be imported"
    }
} catch {
    Write-TestResult "Sourcegraph Python Client" "FAIL" "Client cannot be imported"
}

# ============================================================================
# TASK QUEUE TESTS
# ============================================================================

Write-Host "Testing Task Queue & Background Processing" -ForegroundColor Cyan
Write-Host "------------------------------------------------" -ForegroundColor Cyan

# Test Celery configuration
try {
    $celeryTest = python -c "from src.core.celery_app import celery_app; print('OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-TestResult "Celery Configuration" "PASS" "Celery app can be imported"
    } else {
        Write-TestResult "Celery Configuration" "FAIL" "Celery app cannot be imported"
    }
} catch {
    Write-TestResult "Celery Configuration" "FAIL" "Celery app cannot be imported"
}

# Test Flower monitoring
if (Test-HttpEndpoint "http://localhost:5555" "Flower") {
    Write-TestResult "Flower Monitoring" "PASS" "Flower is accessible"
} else {
    Write-TestResult "Flower Monitoring" "FAIL" "Flower is not accessible"
}

# Test Redis connection for Celery
try {
    $redisTest = python -c "import redis; r = redis.Redis(host='localhost', port=6379, db=0); r.ping(); print('OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-TestResult "Redis for Celery" "PASS" "Redis is accessible for Celery"
    } else {
        Write-TestResult "Redis for Celery" "FAIL" "Redis is not accessible for Celery"
    }
} catch {
    Write-TestResult "Redis for Celery" "FAIL" "Redis is not accessible for Celery"
}

# ============================================================================
# MONITORING TESTS
# ============================================================================

Write-Host "Testing Monitoring & Observability" -ForegroundColor Cyan
Write-Host "---------------------------------------" -ForegroundColor Cyan

# Test Prometheus
if (Test-HttpEndpoint "http://localhost:9090" "Prometheus") {
    Write-TestResult "Prometheus" "PASS" "Prometheus is accessible"
} else {
    Write-TestResult "Prometheus" "FAIL" "Prometheus is not accessible"
}

# Test Grafana
if (Test-HttpEndpoint "http://localhost:3000" "Grafana") {
    Write-TestResult "Grafana" "PASS" "Grafana is accessible"
} else {
    Write-TestResult "Grafana" "FAIL" "Grafana is not accessible"
}

# Test Prometheus client
try {
    $prometheusTest = python -c "from prometheus_client import Counter; print('OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-TestResult "Prometheus Client" "PASS" "Prometheus client can be imported"
    } else {
        Write-TestResult "Prometheus Client" "FAIL" "Prometheus client cannot be imported"
    }
} catch {
    Write-TestResult "Prometheus Client" "FAIL" "Prometheus client cannot be imported"
}

# ============================================================================
# DEVELOPMENT TOOLS TESTS
# ============================================================================

Write-Host "Testing Development Tools" -ForegroundColor Cyan
Write-Host "-----------------------------" -ForegroundColor Cyan

# Test Python modules
$modules = @("pytest", "black", "isort", "flake8")
foreach ($module in $modules) {
    if (Test-PythonModule $module) {
        Write-TestResult "$module Module" "PASS" "$module is available"
    } else {
        Write-TestResult "$module Module" "FAIL" "$module is not available"
    }
}

# ============================================================================
# BROWSER AUTOMATION TESTS
# ============================================================================

Write-Host "Testing Browser Automation" -ForegroundColor Cyan
Write-Host "-----------------------------" -ForegroundColor Cyan

# Test Playwright
try {
    $playwrightTest = python -c "from playwright.sync_api import sync_playwright; print('OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-TestResult "Playwright" "PASS" "Playwright is available"
    } else {
        Write-TestResult "Playwright" "FAIL" "Playwright is not available"
    }
} catch {
    Write-TestResult "Playwright" "FAIL" "Playwright is not available"
}

# Test Selenium
try {
    $seleniumTest = python -c "from selenium import webdriver; print('OK')" 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-TestResult "Selenium" "PASS" "Selenium is available"
    } else {
        Write-TestResult "Selenium" "FAIL" "Selenium is not available"
    }
} catch {
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
    try {
        $moduleTest = python -c "import $module; print('OK')" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-TestResult "$module Module" "PASS" "$module can be imported"
        } else {
            Write-TestResult "$module Module" "FAIL" "$module cannot be imported"
        }
    } catch {
        Write-TestResult "$module Module" "FAIL" "$module cannot be imported"
    }
}

# ============================================================================
# SUMMARY
# ============================================================================

Write-Host ""
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "=============" -ForegroundColor Cyan

$totalTests = $testResults.Total
$passedTests = $testResults.Passed
$failedTests = $testResults.Failed
$successRate = [math]::Round(($passedTests / $totalTests) * 100, 1)

Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $failedTests" -ForegroundColor Red
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