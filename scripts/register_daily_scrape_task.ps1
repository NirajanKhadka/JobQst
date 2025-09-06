# Registers a Windows Scheduled Task to run JobQst daily.
param(
    [Parameter(Mandatory=$true)]
    [string]$ProfileName,

    [ValidateSet('jobspy-pipeline','fast-pipeline','scrape','process-jobs')]
    [string]$Action = 'jobspy-pipeline',

    # Time in 24h format HH:mm (local time)
    [string]$DailyTime = '07:30',

    # Optional: job volume and preset tuning
    [int]$Jobs = 200,
    [ValidateSet('fast','comprehensive','quality','canadian_cities','canada_comprehensive','tech_hubs')]
    [string]$JobSpyPreset = 'canada_comprehensive',
    [int]$ExternalWorkers = 6,
    [ValidateSet('auto','gpu','hybrid','rule_based')]
    [string]$ProcessingMethod = 'auto',
    [int]$HoursOld = 336,
    [int]$MaxJobsTotal = 1000,
    [string]$Sites,
    [switch]$JobSpyOnly
)

$ErrorActionPreference = 'Stop'

# Resolve script paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$runner = Join-Path $ScriptDir 'run_job_pipeline.ps1'

if (-not (Test-Path $runner)) {
    throw "Runner script not found: $runner"
}

# Ensure logs folder exists (created by runner on first run, but safe here too)
$logDir = Join-Path $RepoRoot 'logs/scheduled_jobs'
if (-not (Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

# Build argument string for the runner
$argList = @(
    "-ProfileName", $ProfileName,
    "-Action", $Action,
    "-Jobs", $Jobs
)

switch ($Action) {
    'jobspy-pipeline' {
        $argList += @(
            "-JobSpyPreset", $JobSpyPreset,
            "-ExternalWorkers", $ExternalWorkers,
            "-ProcessingMethod", $ProcessingMethod,
            "-HoursOld", $HoursOld,
            "-MaxJobsTotal", $MaxJobsTotal
        )
        if ($Sites) { $argList += @('-Sites', $Sites) }
        if ($JobSpyOnly) { $argList += '-JobSpyOnly' }
    }
    'fast-pipeline' {
        $argList += @('-ExternalWorkers', $ExternalWorkers, '-ProcessingMethod', $ProcessingMethod)
    }
}

# Task settings
$taskName = "JobQst Daily ${Action} (${ProfileName})"

# Build actions and triggers
$pwsh = (Get-Command pwsh -ErrorAction SilentlyContinue)?.Source
if (-not $pwsh) { $pwsh = (Get-Command powershell).Source }

$taskAction = New-ScheduledTaskAction -Execute $pwsh -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runner`" $($argList -join ' ')"

# Parse DailyTime
if ($DailyTime -notmatch '^[0-2][0-9]:[0-5][0-9]$') { throw "DailyTime must be HH:mm in 24h format" }
$hour = [int]$DailyTime.Split(':')[0]
$minute = [int]$DailyTime.Split(':')[1]

$trigger = New-ScheduledTaskTrigger -Daily -At (Get-Date).Date.AddHours($hour).AddMinutes($minute)

# Run as current user, whether logged on or not is controlled by principal settings
$principal = New-ScheduledTaskPrincipal -UserId $env:UserName -LogonType S4U -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances Parallel

# Register or update
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false | Out-Null
}

Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger $trigger -Principal $principal -Settings $settings | Out-Null

Write-Host "Registered scheduled task: $taskName at $DailyTime"
Write-Host "Logs: $logDir"
