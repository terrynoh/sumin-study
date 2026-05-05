param(
    [string]$ShortcutDirectory = ([Environment]::GetFolderPath("Desktop"))
)

$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$ShortcutDirectory = (Resolve-Path $ShortcutDirectory).Path
$PowerShell = Join-Path $env:SystemRoot "System32\WindowsPowerShell\v1.0\powershell.exe"
$WScriptShell = New-Object -ComObject WScript.Shell

function New-StudyShortcut {
    param(
        [string]$Name,
        [string]$Arguments,
        [string]$Description
    )

    $shortcutPath = Join-Path $ShortcutDirectory "$Name.lnk"
    $shortcut = $WScriptShell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = $PowerShell
    $shortcut.Arguments = $Arguments
    $shortcut.WorkingDirectory = $Root
    $shortcut.Description = $Description
    $shortcut.Save()
    Write-Host "Created $shortcutPath"
}

$startScript = Join-Path $Root "scripts\start_local.ps1"
$stopScript = Join-Path $Root "scripts\stop_local.ps1"

New-StudyShortcut `
    -Name "SUMIN STUDY" `
    -Arguments "-NoProfile -ExecutionPolicy Bypass -File `"$startScript`" -View student" `
    -Description "Start SUMIN STUDY student view"

New-StudyShortcut `
    -Name "SUMIN STUDY Operator" `
    -Arguments "-NoProfile -ExecutionPolicy Bypass -File `"$startScript`" -View operator" `
    -Description "Start SUMIN STUDY operator view"

New-StudyShortcut `
    -Name "Stop SUMIN STUDY" `
    -Arguments "-NoProfile -ExecutionPolicy Bypass -File `"$stopScript`"" `
    -Description "Stop SUMIN STUDY local services"
