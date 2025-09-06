param(
    [Parameter(Mandatory=$true)]
    [string]$ProfileName,

    [ValidateSet('jobspy-pipeline','fast-pipeline','scrape','process-jobs')]
    [string]$Action = 'jobspy-pipeline'
)

$taskName = "JobQst Daily ${Action} (${ProfileName})"

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Unregistered scheduled task: $taskName"
} else {
    Write-Host "No scheduled task found: $taskName"
}
