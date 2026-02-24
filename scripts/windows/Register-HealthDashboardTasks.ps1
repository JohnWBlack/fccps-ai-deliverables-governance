param(
    [string]$TaskPrefix = "FCCPS-HealthDashboard",
    [string]$RepoRoot = "c:\Users\JohnBlack\OneDrive - OFFSET3\FCCPS AI Committee\fccps-ai-deliverables-governance",
    [string]$PythonExe = "python",
    [string]$RunAsUser = "$env:USERDOMAIN\$env:USERNAME"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$null = Import-Module ScheduledTasks -ErrorAction Stop

$RunnerScript = Join-Path $RepoRoot "scripts\windows\Publish-HealthDashboard.ps1"
if (!(Test-Path -LiteralPath $RunnerScript)) {
    throw "Runner script not found: $RunnerScript"
}

$detectTaskName = "$TaskPrefix-DetectChanges"
$dailyTaskName = "$TaskPrefix-DailyRebuild"

$principal = New-ScheduledTaskPrincipal -UserId $RunAsUser -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$detectStart = (Get-Date).Date.AddMinutes(1)

$detectAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$RunnerScript`" -Mode DetectChanges -Branch main -PythonExe `"$PythonExe`""
$detectTrigger = New-ScheduledTaskTrigger -Once -At $detectStart -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 1)

$dailyAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$RunnerScript`" -Mode FullRebuild -Branch main -PythonExe `"$PythonExe`""
$dailyTrigger = New-ScheduledTaskTrigger -Daily -At 2:30AM

Register-ScheduledTask -TaskName $detectTaskName -Action $detectAction -Trigger $detectTrigger -Principal $principal -Settings $settings -Force | Out-Null
Register-ScheduledTask -TaskName $dailyTaskName -Action $dailyAction -Trigger $dailyTrigger -Principal $principal -Settings $settings -Force | Out-Null

Write-Host "Created/updated tasks:"
Write-Host " - $detectTaskName (every 15 minutes, change-detection trigger)"
Write-Host " - $dailyTaskName (daily 02:30 local, cron-style full rebuild)"

Get-ScheduledTask -TaskName $detectTaskName | Select-Object TaskName, State | Format-List
Get-ScheduledTask -TaskName $dailyTaskName | Select-Object TaskName, State | Format-List
