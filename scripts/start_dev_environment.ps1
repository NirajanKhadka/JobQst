# AutoJobAgent Development Environment Startup Script
# This script starts all the tools needed for the job automation system

Write-Host "🚀 Starting AutoJobAgent Development Environment" -ForegroundColor Green
Write-Host "=================================================" -ForegroundColor Green

# Function to check if Docker is running
function Test-DockerRunning {
    try {
        docker ps > $null 2>&1
        return $true
    } catch {
        return $false
    }
}

# Function to check if a port is available
function Test-PortAvailable {
    param([int]$Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.Connect("localhost", $Port)
        $connection.Close()
        return $false
    } catch {
        return $true
    }
}

# Check Docker
if (-not (Test-DockerRunning)) {
    Write-Host "❌ Docker is not running!" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again." -ForegroundColor Yellow
    exit 1
}
Write-Host "✅ Docker is running" -ForegroundColor Green

# Start development environment
Write-Host "`n🐳 Starting Docker services..." -ForegroundColor Cyan

# Check if docker-compose.dev.yml exists
if (Test-Path "docker-compose.dev.yml") {
    Write-Host "Starting services with docker-compose.dev.yml..." -ForegroundColor Yellow
    docker-compose -f docker-compose.dev.yml up -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Docker services started successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to start Docker services" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  docker-compose.dev.yml not found, starting individual services..." -ForegroundColor Yellow
    
    # Start Sourcegraph
    Write-Host "Starting Sourcegraph..." -ForegroundColor Yellow
    docker-compose -f docker-compose.sourcegraph.yml up -d
    
    # Start Redis
    Write-Host "Starting Redis..." -ForegroundColor Yellow
    docker run -d --name redis -p 6379:6379 redis:7-alpine
    
    # Start PostgreSQL
    Write-Host "Starting PostgreSQL..." -ForegroundColor Yellow
    docker run -d --name postgres -p 5432:5432 -e POSTGRES_DB=autojob -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password postgres:15-alpine
}

# Start Celery workers
Write-Host "`n🐰 Starting Celery workers..." -ForegroundColor Cyan

# Check if Redis is available
if (Test-PortAvailable 6379) {
    Write-Host "⚠️  Redis is not running. Starting Redis..." -ForegroundColor Yellow
    docker run -d --name redis -p 6379:6379 redis:7-alpine
    Start-Sleep -Seconds 5
}

# Start Celery worker in background
Write-Host "Starting Celery worker..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-Command", "cd '$PWD'; python -m celery -A src.core.celery_app worker --loglevel=info" -WindowStyle Minimized

# Start Celery beat in background
Write-Host "Starting Celery beat..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-Command", "cd '$PWD'; python -m celery -A src.core.celery_app beat --loglevel=info" -WindowStyle Minimized

# Start Flower monitoring
Write-Host "Starting Flower monitoring..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-Command", "cd '$PWD'; python -m celery -A src.core.celery_app flower --port=5555" -WindowStyle Minimized

# Start monitoring services
Write-Host "`n📊 Starting monitoring services..." -ForegroundColor Cyan

# Check if Prometheus is available
if (Test-PortAvailable 9090) {
    Write-Host "Starting Prometheus..." -ForegroundColor Yellow
    if (Test-Path "monitoring\prometheus.yml") {
        docker run -d --name prometheus -p 9090:9090 -v "${PWD}\monitoring\prometheus.yml:/etc/prometheus/prometheus.yml" prom/prometheus:latest
    }
}

# Check if Grafana is available
if (Test-PortAvailable 3000) {
    Write-Host "Starting Grafana..." -ForegroundColor Yellow
    docker run -d --name grafana -p 3000:3000 -e GF_SECURITY_ADMIN_PASSWORD=admin grafana/grafana:latest
}

# Display service status
Write-Host "`n📋 Service Status:" -ForegroundColor Cyan
Write-Host "=================" -ForegroundColor Cyan

$services = @(
    @{Name="Sourcegraph"; Port=7080},
    @{Name="Redis"; Port=6379},
    @{Name="PostgreSQL"; Port=5432},
    @{Name="Flower (Celery)"; Port=5555},
    @{Name="Prometheus"; Port=9090},
    @{Name="Grafana"; Port=3000}
)

foreach ($service in $services) {
    $status = if (Test-PortAvailable $service.Port) { "❌ Stopped" } else { "✅ Running" }
    Write-Host "$($service.Name): $status" -ForegroundColor $(if ($status -like "*Running*") { "Green" } else { "Red" })
}

# Display access information
Write-Host "`n🌐 Access Information:" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
Write-Host "Sourcegraph (Code Search): http://localhost:7080" -ForegroundColor Green
Write-Host "Flower (Celery Monitoring): http://localhost:5555" -ForegroundColor Green
Write-Host "Grafana (Metrics Dashboard): http://localhost:3000 (admin/admin)" -ForegroundColor Green
Write-Host "Prometheus (Metrics): http://localhost:9090" -ForegroundColor Green
Write-Host "Redis (Cache/Queue): localhost:6379" -ForegroundColor Green
Write-Host "PostgreSQL (Database): localhost:5432" -ForegroundColor Green

# Display useful commands
Write-Host "`n💡 Useful Commands:" -ForegroundColor Cyan
Write-Host "==================" -ForegroundColor Cyan
Write-Host "Stop all services: docker-compose -f docker-compose.dev.yml down" -ForegroundColor Yellow
Write-Host "View logs: docker-compose -f docker-compose.dev.yml logs -f" -ForegroundColor Yellow
Write-Host "Test Sourcegraph: python test_sourcegraph.py" -ForegroundColor Yellow
Write-Host "Start main app: python main.py" -ForegroundColor Yellow

Write-Host "`n🎉 Development environment is ready!" -ForegroundColor Green
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 
$env:PYTHONPATH = "D:\automate_job" 