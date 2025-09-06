# Runs JobQst pipelines with logging; intended for Scheduled Task or manual runs.
param(
    [Parameter(Mandatory=$true)]
    [string]$ProfileName,

    [ValidateSet('jobspy-pipeline','fast-pipeline','scrape','process-jobs')]
    [string]$Action = 'jobspy-pipeline',

    # Common options
    [int]$Jobs = 50,
    [switch]$VerboseMode,

    # Scrape/fast-pipeline options
    [int]$Pages = 3,
    [string]$Keywords,
    [switch]$Headless,
    [ValidateSet('auto','gpu','hybrid','rule_based')]
    [string]$ProcessingMethod = 'auto',
    [int]$ExternalWorkers = 6,

    # JobSpy options
    [ValidateSet('fast','comprehensive','quality','mississauga','toronto','remote','canadian_cities','canada_comprehensive','tech_hubs')]
    [string]$JobSpyPreset = 'quality',
    [string]$Sites,
    [int]$HoursOld = 336,
    [int]$MaxJobsTotal,
    [switch]$JobSpyOnly
)

$ErrorActionPreference = 'Stop'

try {
    # Resolve repo root (scripts folder is one level down)
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $RepoRoot = Split-Path -Parent $ScriptDir
    Set-Location $RepoRoot

    # Prepare logging
    $logDir = Join-Path $RepoRoot 'logs/scheduled_jobs'
    if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
    $dateStamp = (Get-Date).ToString('yyyy-MM-dd')
    $logFile = Join-Path $logDir ("run_${dateStamp}.log")

    # Build argument array for python CLI
    $mainPy = Join-Path $RepoRoot 'main.py'
    $argsList = @()
    $argsList += $mainPy
    $argsList += $ProfileName
    $argsList += '--action'
    $argsList += $Action

    switch ($Action) {
        'scrape' {
            $argsList += @('--pages', $Pages.ToString())
            $argsList += @('--jobs', $Jobs.ToString())
            if ($Headless) { $argsList += '--headless' }
            if ($Keywords) { $argsList += @('--keywords', $Keywords) }
        }
        'fast-pipeline' {
            $argsList += @('--jobs', $Jobs.ToString())
            $argsList += @('--processing-method', $ProcessingMethod)
            $argsList += @('--external-workers', $ExternalWorkers.ToString())
        }
        'process-jobs' {
            $argsList += @('--jobs', $Jobs.ToString())
        }
        'jobspy-pipeline' {
            $argsList += @('--jobs', $Jobs.ToString())
            $argsList += @('--jobspy-preset', $JobSpyPreset)
            $argsList += @('--hours-old', $HoursOld.ToString())
            $argsList += @('--processing-method', $ProcessingMethod)
            $argsList += @('--external-workers', $ExternalWorkers.ToString())
            if ($Sites) { $argsList += @('--sites', $Sites) }
            if ($MaxJobsTotal) { $argsList += @('--max-jobs-total', $MaxJobsTotal.ToString()) }
            if ($JobSpyOnly) { $argsList += '--jobspy-only' }
        }
    }

    if ($VerboseMode) { $argsList += '--verbose' }

    # Determine launcher: prefer conda if available
    $useConda = $false
    $condaCmd = Get-Command conda -ErrorAction SilentlyContinue
    if ($condaCmd) { $useConda = $true }

    if ($useConda) {
        $exe = $condaCmd.Source
        $finalArgs = @('run','-n','auto_job','python') + $argsList
    } else {
        # Fallback; main.py will attempt to re-invoke via conda if possible
        $exe = (Get-Command python).Source
        $finalArgs = $argsList
    }

    # Timestamp header
    $startStamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "`n===== JobQst run started $startStamp (Action=$Action, Profile=$ProfileName) =====" | Tee-Object -FilePath $logFile -Append | Out-Null
    "Command: $exe $($finalArgs -join ' ')" | Tee-Object -FilePath $logFile -Append | Out-Null

    # Execute and stream to log
    & $exe @finalArgs 2>&1 | Tee-Object -FilePath $logFile -Append
    $exitCode = $LASTEXITCODE

    $endStamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    "===== JobQst run ended $endStamp (ExitCode=$exitCode) =====`n" | Tee-Object -FilePath $logFile -Append | Out-Null

    exit $exitCode
}
catch {
    $err = $_
    try {
        if (-not $logFile) {
            $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
            $RepoRoot = Split-Path -Parent $ScriptDir
            $logDir = Join-Path $RepoRoot 'logs/scheduled_jobs'
            if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }
            $logFile = Join-Path $logDir ("run_" + (Get-Date -Format 'yyyy-MM-dd') + ".log")
        }
        "[ERROR] $($err.Exception.Message)`n$($err.ScriptStackTrace)" | Tee-Object -FilePath $logFile -Append | Out-Null
    } catch {}
    exit 1
}
