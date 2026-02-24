# Windows Task Scheduler Automation

This repo includes local Windows automation for rebuilding public dashboard artifacts and pushing updates.

## Scripts

- `scripts/windows/Publish-HealthDashboard.ps1`
  - Runs validation + rebuild pipeline.
  - Commits/pushes only when public artifacts changed.
  - Modes:
    - `DetectChanges`: only runs full pipeline when relevant repo changes are detected.
    - `FullRebuild`: always runs pipeline.
- `scripts/windows/Register-HealthDashboardTasks.ps1`
  - Creates/updates scheduled tasks.

## Task Design: Change Detection vs Cron

1. **Change-detection task** (polling trigger):
   - Name: `FCCPS-HealthDashboard-DetectChanges`
   - Schedule: every 15 minutes.
   - Purpose: near-real-time updates when relevant files change.

2. **Cron-style safety task** (time-based trigger):
   - Name: `FCCPS-HealthDashboard-DailyRebuild`
   - Schedule: daily at 02:30 local time.
   - Purpose: safety rebuild to correct drift, missed runs, or environment hiccups.

## Deploy Tasks

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/windows/Register-HealthDashboardTasks.ps1 `
  -RepoRoot "c:\Users\JohnBlack\OneDrive - OFFSET3\FCCPS AI Committee\fccps-ai-deliverables-governance" `
  -PythonExe "C:/Program Files/Microsoft SDKs/Azure/CLI2/python.exe"
```

## View Task Logs

- Local log file: `logs/health-dashboard-task.log`
