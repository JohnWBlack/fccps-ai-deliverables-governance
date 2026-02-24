param(
    [ValidateSet("DetectChanges", "FullRebuild")]
    [string]$Mode = "DetectChanges",
    [string]$Branch = "main",
    [string]$PythonExe = "python"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "../..")).Path
$PublicFiles = @(
    "public/public_snapshot.json",
    "public/file_catalog.json",
    "public/ref_index.json",
    "public/quality_report.json",
    "public/kpis.json",
    "public/kpi_evidence.json"
)
$WatchPathspec = @("sor", "governance_docs", "project_files", "scripts", "requirements.txt", "CHANGELOG_PUBLIC.md")
$LockFile = Join-Path $RepoRoot ".task_publish.lock"
$LogDir = Join-Path $RepoRoot "logs"
$LogPath = Join-Path $LogDir "health-dashboard-task.log"

if (!(Test-Path -LiteralPath $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssK"
    "$timestamp [$Mode] $Message" | Tee-Object -FilePath $LogPath -Append
}

function Invoke-Git {
    param([string[]]$GitArgs)
    & git @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "git $($GitArgs -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Get-GitOutput {
    param([string[]]$GitArgs)
    $output = & git @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "git $($GitArgs -join ' ') failed with exit code $LASTEXITCODE"
    }
    return $output
}

if (Test-Path -LiteralPath $LockFile) {
    Write-Log "Lock file present; skipping run to avoid overlap."
    exit 0
}

New-Item -ItemType File -Path $LockFile -Force | Out-Null

try {
    Set-Location $RepoRoot
    Write-Log "Task starting in repo: $RepoRoot"

    $currentBranch = (Get-GitOutput -GitArgs @("rev-parse", "--abbrev-ref", "HEAD")).Trim()
    if ($currentBranch -ne $Branch) {
        throw "Current branch is '$currentBranch'; expected '$Branch'."
    }

    $dirty = (Get-GitOutput -GitArgs @("status", "--porcelain")).Count -gt 0
    if ($dirty) {
        Write-Log "Working tree is dirty; skipping to avoid committing unintended files."
        exit 0
    }

    Invoke-Git -GitArgs @("fetch", "origin", $Branch)

    $remoteDiffArgs = @("diff", "--name-only", "HEAD..origin/$Branch", "--") + $WatchPathspec
    $remoteRelevant = @(Get-GitOutput -GitArgs $remoteDiffArgs)
    $hasRemoteRelevantChanges = $remoteRelevant.Count -gt 0

    $localStatusArgs = @("status", "--porcelain", "--") + $WatchPathspec
    $localRelevant = @(Get-GitOutput -GitArgs $localStatusArgs)
    $hasLocalRelevantChanges = $localRelevant.Count -gt 0

    if ($Mode -eq "DetectChanges" -and -not $hasRemoteRelevantChanges -and -not $hasLocalRelevantChanges) {
        Write-Log "No relevant local/remote changes detected; exiting."
        exit 0
    }

    if ($hasRemoteRelevantChanges) {
        Write-Log "Remote relevant changes detected; fast-forwarding local branch."
        Invoke-Git -GitArgs @("merge", "--ff-only", "origin/$Branch")
    }

    Write-Log "Running deterministic build pipeline."
    & $PythonExe "scripts/validate_sor.py"
    if ($LASTEXITCODE -ne 0) { throw "validate_sor.py failed" }
    & $PythonExe "scripts/build_snapshot.py"
    if ($LASTEXITCODE -ne 0) { throw "build_snapshot.py failed" }
    & $PythonExe "scripts/build_catalog.py"
    if ($LASTEXITCODE -ne 0) { throw "build_catalog.py failed" }
    & $PythonExe "scripts/extract_refs.py"
    if ($LASTEXITCODE -ne 0) { throw "extract_refs.py failed" }
    & $PythonExe "scripts/quality_checks.py"
    if ($LASTEXITCODE -ne 0) { throw "quality_checks.py failed" }
    & $PythonExe "scripts/build_kpis.py"
    if ($LASTEXITCODE -ne 0) { throw "build_kpis.py failed" }

    $publicDiffArgs = @("diff", "--name-only", "--") + $PublicFiles
    $changedPublic = @(Get-GitOutput -GitArgs $publicDiffArgs)
    if ($changedPublic.Count -eq 0) {
        Write-Log "No public artifact changes after rebuild; exiting."
        exit 0
    }

    Write-Log ("Public artifacts changed: " + ($changedPublic -join ", "))
    $addArgs = @("add") + $PublicFiles
    Invoke-Git -GitArgs $addArgs

    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Invoke-Git -GitArgs @("commit", "-m", "chore(public): auto-update dashboard artifacts ($Mode, $stamp) [skip ci]")
    Invoke-Git -GitArgs @("push", "origin", $Branch)

    Write-Log "Push complete."
}
catch {
    Write-Log ("ERROR: " + $_.Exception.Message)
    throw
}
finally {
    if (Test-Path -LiteralPath $LockFile) {
        Remove-Item -LiteralPath $LockFile -Force
    }
    Write-Log "Task finished."
}
