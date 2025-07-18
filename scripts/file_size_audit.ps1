# AutoJobAgent File Size Audit Script
# Purpose: Regular monitoring of file sizes to catch violations early
# Run: powershell -ExecutionPolicy Bypass .\scripts\file_size_audit.ps1

param(
    [int]$WarningSizeLines = 300,
    [int]$CriticalSizeLines = 500,
    [string]$OutputFile = ".\temp\file_size_audit_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
)

Write-Host "File Size Audit Starting..." -ForegroundColor Cyan
Write-Host "Warning threshold: $WarningSizeLines lines" -ForegroundColor Yellow
Write-Host "Critical threshold: $CriticalSizeLines lines" -ForegroundColor Red

# Ensure temp directory exists
New-Item -ItemType Directory -Force -Path ".\temp" | Out-Null

# Initialize results
$results = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    thresholds = @{
        warning = $WarningSizeLines
        critical = $CriticalSizeLines
    }
    files = @()
    summary = @{
        total_files = 0
        warning_count = 0
        critical_count = 0
        largest_file = @{
            path = ""
            lines = 0
        }
    }
}

# Get all Python and Markdown files
$extensions = @("*.py", "*.md")
$totalFiles = 0
$warningFiles = 0
$criticalFiles = 0
$largestFile = @{ path = ""; lines = 0 }

Write-Host "`nScanning files..." -ForegroundColor Green

foreach ($ext in $extensions) {
    Get-ChildItem -Path "." -Recurse -Filter $ext | Where-Object {
        # Exclude certain directories
        $_.FullName -notmatch "\\__pycache__\\" -and
        $_.FullName -notmatch "\\\.git\\" -and
        $_.FullName -notmatch "\\node_modules\\" -and
        $_.FullName -notmatch "\\archive\\" -and
        $_.FullName -notmatch "\\\.pytest_cache\\"
    } | ForEach-Object {
        $filePath = $_.FullName
        $relativePath = $_.FullName.Replace((Get-Location).Path + "\", "")
        
        try {
            $lineCount = (Get-Content $filePath -ErrorAction SilentlyContinue | Measure-Object -Line).Lines
            $totalFiles++
            
            # Categorize file
            $category = "normal"
            if ($lineCount -ge $CriticalSizeLines) {
                $category = "critical"
                $criticalFiles++
                Write-Host "CRITICAL: $relativePath ($lineCount lines)" -ForegroundColor Red
            }
            elseif ($lineCount -ge $WarningSizeLines) {
                $category = "warning"
                $warningFiles++
                Write-Host "WARNING: $relativePath ($lineCount lines)" -ForegroundColor Yellow
            }
            
            # Track largest file
            if ($lineCount -gt $largestFile.lines) {
                $largestFile = @{
                    path = $relativePath
                    lines = $lineCount
                }
            }
            
            # Add to results
            $results.files += @{
                path = $relativePath
                lines = $lineCount
                category = $category
                size_bytes = $_.Length
                last_modified = $_.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
            }
        }
        catch {
            Write-Warning "Could not read file: $relativePath"
        }
    }
}

# Update summary
$results.summary.total_files = $totalFiles
$results.summary.warning_count = $warningFiles
$results.summary.critical_count = $criticalFiles
$results.summary.largest_file = $largestFile

# Save results to JSON
$results | ConvertTo-Json -Depth 4 | Out-File -FilePath $OutputFile -Encoding UTF8

# Display summary
Write-Host "`nAUDIT SUMMARY" -ForegroundColor Cyan
Write-Host "===================" -ForegroundColor Cyan
Write-Host "Total files scanned: $totalFiles" -ForegroundColor White
Write-Host "Warning files ($WarningSizeLines+ lines): $warningFiles" -ForegroundColor Yellow
Write-Host "Critical files ($CriticalSizeLines+ lines): $criticalFiles" -ForegroundColor Red
Write-Host "Largest file: $($largestFile.path) ($($largestFile.lines) lines)" -ForegroundColor Magenta

if ($criticalFiles -gt 0) {
    Write-Host "`nACTION REQUIRED: $criticalFiles files exceed $CriticalSizeLines lines" -ForegroundColor Red
    Write-Host "   Consider refactoring large files for maintainability" -ForegroundColor Red
}

if ($warningFiles -gt 0) {
    Write-Host "`nMONITORING: $warningFiles files exceed $WarningSizeLines lines" -ForegroundColor Yellow
    Write-Host "   Watch these files to prevent them from growing too large" -ForegroundColor Yellow
}

Write-Host "`nDetailed results saved to: $OutputFile" -ForegroundColor Green
Write-Host "File size audit complete!" -ForegroundColor Green

# Return exit code based on findings
if ($criticalFiles -gt 0) {
    exit 1  # Critical issues found
}
elseif ($warningFiles -gt 0) {
    exit 2  # Warnings found
}
else {
    exit 0  # All good
}
