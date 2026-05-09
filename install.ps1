$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$kritaRes = Join-Path $env:APPDATA "krita\pykrita"
$kritaActions = Join-Path $env:APPDATA "krita\pykrita\actions"

if (-not (Test-Path $kritaRes)) {
    New-Item -ItemType Directory -Path $kritaRes -Force | Out-Null
}
if (-not (Test-Path $kritaActions)) {
    New-Item -ItemType Directory -Path $kritaActions -Force | Out-Null
}

$desktopLink = Join-Path $kritaRes "krita_file_browser.desktop"
$moduleLink = Join-Path $kritaRes "krita_file_browser"
$actionLink = Join-Path $kritaActions "krita_file_browser.action"

if (Test-Path $desktopLink) { Remove-Item $desktopLink -Force }
if (Test-Path $moduleLink) { Remove-Item $moduleLink -Recurse -Force }
if (Test-Path $actionLink) { Remove-Item $actionLink -Force }

New-Item -ItemType SymbolicLink -Path $desktopLink -Target (Join-Path $projectRoot "krita_file_browser.desktop") | Out-Null
New-Item -ItemType SymbolicLink -Path $moduleLink -Target (Join-Path $projectRoot "krita_file_browser") | Out-Null
New-Item -ItemType SymbolicLink -Path $actionLink -Target (Join-Path $projectRoot "krita_file_browser.action") | Out-Null

Write-Host "Symlinks created in $kritaRes"
Write-Host "Restart Krita and enable the plugin in Settings > Configure Krita > Python Plugin Manager."
