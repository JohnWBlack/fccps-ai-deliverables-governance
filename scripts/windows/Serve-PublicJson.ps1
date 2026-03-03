param(
    [string]$HostName = "127.0.0.1",
    [int]$Port = 8010,
    [string]$PythonExe = "python"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "../..")).Path
$PublicDir = Join-Path $RepoRoot "public"

if (!(Test-Path -LiteralPath $PublicDir)) {
    throw "Public directory not found: $PublicDir"
}

Write-Host "Serving $PublicDir at http://$HostName`:$Port"
& $PythonExe -m http.server $Port --bind $HostName --directory $PublicDir
