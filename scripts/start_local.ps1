param(
    [ValidateSet("student", "operator")]
    [string]$View = "student",
    [string]$Python = "python",
    [string]$Npm = "npm.cmd",
    [string]$DbPath = "",
    [int]$ApiPort = 8000,
    [int]$WebPort = 4173,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$FrontendRoot = Join-Path $Root "frontend"
$TmpDir = Join-Path $Root ".tmp"
$DistDir = Join-Path $FrontendRoot "dist"

New-Item -ItemType Directory -Force -Path $TmpDir | Out-Null

if (-not (Test-Path $DistDir)) {
    throw "Frontend build not found at $DistDir. Run 'npm.cmd run build' in frontend first."
}

if ($DbPath) {
    $env:SUMIN_STUDY_DB_PATH = $DbPath
}

$apiOut = Join-Path $TmpDir "local-api.out"
$apiErr = Join-Path $TmpDir "local-api.err"
$webOut = Join-Path $TmpDir "local-web.out"
$webErr = Join-Path $TmpDir "local-web.err"

Start-Process -FilePath $Python `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$ApiPort") `
    -WorkingDirectory $Root `
    -RedirectStandardOutput $apiOut `
    -RedirectStandardError $apiErr `
    -WindowStyle Hidden

Start-Process -FilePath $Npm `
    -ArgumentList @("run", "preview", "--", "--host", "127.0.0.1", "--port", "$WebPort") `
    -WorkingDirectory $FrontendRoot `
    -RedirectStandardOutput $webOut `
    -RedirectStandardError $webErr `
    -WindowStyle Hidden

$path = if ($View -eq "operator") { "/?view=operator" } else { "/" }
$url = "http://127.0.0.1:$WebPort$path"

Write-Host "SUMIN STUDY local app started."
Write-Host "API: http://127.0.0.1:$ApiPort"
Write-Host "Web: $url"
Write-Host "Logs: $TmpDir"
Write-Host "Stop with: scripts\\stop_local.ps1"

if (-not $NoBrowser) {
    Start-Process $url
}
