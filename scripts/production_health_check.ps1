# AutoJobAgent Production Health Check Script
# Purpose: Monitor production microservices and system health
# Run: powershell -ExecutionPolicy Bypass .\scripts\production_health_check.ps1

param(
    [string]$OutputFile = ".\temp\health_check_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
)

Write-Host "AutoJobAgent Production Health Check" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# Ensure temp directory exists
New-Item -ItemType Directory -Force -Path ".\temp" | Out-Null

# Initialize health report
$healthReport = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    overall_status = "healthy"
    checks = @{}
    metrics = @{}
    recommendations = @()
}

# Check 1: Production Launcher Process
Write-Host "`nChecking production launcher..." -ForegroundColor Yellow
try {
    $pythonProcess = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { 
        $_.CommandLine -like "*production_launcher.py*" 
    }
    
    if ($pythonProcess) {
        $healthReport.checks.production_launcher = @{
            status = "running"
            pid = $pythonProcess.Id
            cpu_usage = $pythonProcess.CPU
            memory_mb = [math]::Round($pythonProcess.WorkingSet64 / 1MB, 2)
        }
        Write-Host "✅ Production launcher is running (PID: $($pythonProcess.Id))" -ForegroundColor Green
    } else {
        $healthReport.checks.production_launcher = @{
            status = "not_running"
            message = "Production launcher process not found"
        }
        $healthReport.overall_status = "warning"
        Write-Host "⚠️ Production launcher not running" -ForegroundColor Yellow
    }
} catch {
    $healthReport.checks.production_launcher = @{
        status = "error"
        error = $_.Exception.Message
    }
    Write-Host "❌ Error checking production launcher: $($_.Exception.Message)" -ForegroundColor Red
}

# Check 2: Database Health
Write-Host "`nChecking database health..." -ForegroundColor Yellow
try {
    if (Test-Path ".\jobs.db") {
        $dbFile = Get-Item ".\jobs.db"
        $healthReport.checks.database = @{
            status = "available"
            size_mb = [math]::Round($dbFile.Length / 1MB, 2)
            last_modified = $dbFile.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
        }
        Write-Host "✅ Database file available ($([math]::Round($dbFile.Length / 1MB, 2)) MB)" -ForegroundColor Green
    } else {
        $healthReport.checks.database = @{
            status = "missing"
            message = "jobs.db file not found"
        }
        $healthReport.overall_status = "warning"
        Write-Host "⚠️ Database file not found" -ForegroundColor Yellow
    }
} catch {
    $healthReport.checks.database = @{
        status = "error"
        error = $_.Exception.Message
    }
    Write-Host "❌ Error checking database: $($_.Exception.Message)" -ForegroundColor Red
}

# Check 3: Cache Status
Write-Host "`nChecking cache status..." -ForegroundColor Yellow
try {
    if (Test-Path ".\cache\processed") {
        $cacheFiles = Get-ChildItem ".\cache\processed" -File | Measure-Object
        $healthReport.checks.cache = @{
            status = "available"
            files_count = $cacheFiles.Count
            directory_exists = $true
        }
        Write-Host "✅ Cache directory available ($($cacheFiles.Count) files)" -ForegroundColor Green
    } else {
        $healthReport.checks.cache = @{
            status = "missing"
            message = "Cache directory not found"
        }
        Write-Host "⚠️ Cache directory not found" -ForegroundColor Yellow
    }
} catch {
    $healthReport.checks.cache = @{
        status = "error"
        error = $_.Exception.Message
    }
    Write-Host "❌ Error checking cache: $($_.Exception.Message)" -ForegroundColor Red
}

# Check 4: Disk Space
Write-Host "`nChecking disk space..." -ForegroundColor Yellow
try {
    $drive = Get-PSDrive -Name (Split-Path (Get-Location) -Qualifier).Replace(":", "")
    $freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
    $totalSpaceGB = [math]::Round(($drive.Used + $drive.Free) / 1GB, 2)
    $usedPercentage = [math]::Round(($drive.Used / ($drive.Used + $drive.Free)) * 100, 1)
    
    $healthReport.checks.disk_space = @{
        status = if ($freeSpaceGB -gt 5) { "healthy" } elseif ($freeSpaceGB -gt 1) { "warning" } else { "critical" }
        free_space_gb = $freeSpaceGB
        total_space_gb = $totalSpaceGB
        used_percentage = $usedPercentage
    }
    
    if ($freeSpaceGB -gt 5) {
        Write-Host "✅ Disk space healthy ($freeSpaceGB GB free, $usedPercentage% used)" -ForegroundColor Green
    } elseif ($freeSpaceGB -gt 1) {
        Write-Host "⚠️ Disk space warning ($freeSpaceGB GB free, $usedPercentage% used)" -ForegroundColor Yellow
        $healthReport.overall_status = "warning"
    } else {
        Write-Host "❌ Disk space critical ($freeSpaceGB GB free, $usedPercentage% used)" -ForegroundColor Red
        $healthReport.overall_status = "critical"
    }
} catch {
    $healthReport.checks.disk_space = @{
        status = "error"
        error = $_.Exception.Message
    }
    Write-Host "❌ Error checking disk space: $($_.Exception.Message)" -ForegroundColor Red
}

# Check 5: Archive Integrity
Write-Host "`nChecking archive integrity..." -ForegroundColor Yellow
try {
    if (Test-Path ".\archive") {
        $archiveSize = (Get-ChildItem ".\archive" -Recurse -File | Measure-Object -Property Length -Sum).Sum
        $archiveSizeMB = [math]::Round($archiveSize / 1MB, 2)
        $archiveCount = (Get-ChildItem ".\archive" -Recurse -File | Measure-Object).Count
        
        $healthReport.checks.archive = @{
            status = "healthy"
            size_mb = $archiveSizeMB
            file_count = $archiveCount
        }
        Write-Host "✅ Archive directory healthy ($archiveSizeMB MB, $archiveCount files)" -ForegroundColor Green
    } else {
        $healthReport.checks.archive = @{
            status = "missing"
            message = "Archive directory not found"
        }
        Write-Host "⚠️ Archive directory not found" -ForegroundColor Yellow
    }
} catch {
    $healthReport.checks.archive = @{
        status = "error"
        error = $_.Exception.Message
    }
    Write-Host "❌ Error checking archive: $($_.Exception.Message)" -ForegroundColor Red
}

# Generate recommendations
if ($healthReport.overall_status -eq "warning" -or $healthReport.overall_status -eq "critical") {
    if ($healthReport.checks.production_launcher.status -eq "not_running") {
        $healthReport.recommendations += "Start production launcher: python production_launcher.py"
    }
    if ($healthReport.checks.database.status -eq "missing") {
        $healthReport.recommendations += "Initialize database or restore from backup"
    }
    if ($healthReport.checks.disk_space.status -in @("warning", "critical")) {
        $healthReport.recommendations += "Free up disk space or extend storage capacity"
    }
}

# Save detailed report
$healthReport | ConvertTo-Json -Depth 4 | Out-File -FilePath $OutputFile -Encoding UTF8

# Display summary
Write-Host "`nHEALTH CHECK SUMMARY" -ForegroundColor Cyan
Write-Host "=====================" -ForegroundColor Cyan
Write-Host "Overall Status: " -NoNewline
switch ($healthReport.overall_status) {
    "healthy" { Write-Host "HEALTHY ✅" -ForegroundColor Green }
    "warning" { Write-Host "WARNING ⚠️" -ForegroundColor Yellow }
    "critical" { Write-Host "CRITICAL ❌" -ForegroundColor Red }
}

Write-Host "Detailed report saved to: $OutputFile" -ForegroundColor Green

if ($healthReport.recommendations.Count -gt 0) {
    Write-Host "`nRECOMMENDATIONS:" -ForegroundColor Yellow
    foreach ($recommendation in $healthReport.recommendations) {
        Write-Host "  • $recommendation" -ForegroundColor Yellow
    }
}

Write-Host "`nProduction health check complete!" -ForegroundColor Green

# Return appropriate exit code
switch ($healthReport.overall_status) {
    "healthy" { exit 0 }
    "warning" { exit 1 }
    "critical" { exit 2 }
}
