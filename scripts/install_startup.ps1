$ErrorActionPreference = "Stop"

$taskName = "Orion Home Cinema"

$projectRoot = Split-Path `
    -Parent $PSScriptRoot

$pythonLauncher = Join-Path `
    $projectRoot `
    ".venv\Scripts\pythonw.exe"

$backgroundLauncher = Join-Path `
    $projectRoot `
    "background.py"

if (-not (Test-Path -LiteralPath $pythonLauncher)) {

    throw (
        "Python background launcher was not found: " +
        $pythonLauncher
    )
}

if (-not (Test-Path -LiteralPath $backgroundLauncher)) {

    throw (
        "Orion background launcher was not found: " +
        $backgroundLauncher
    )
}

$userId = (
    [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
)

$action = New-ScheduledTaskAction `
    -Execute $pythonLauncher `
    -Argument "`"$backgroundLauncher`"" `
    -WorkingDirectory $projectRoot

$trigger = New-ScheduledTaskTrigger `
    -AtLogOn `
    -User $userId

$principal = New-ScheduledTaskPrincipal `
    -UserId $userId `
    -LogonType Interactive `
    -RunLevel Limited

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $taskName `
    -Description "Starts Orion after Windows sign-in." `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Force | Out-Null

Write-Host
Write-Host "Orion startup task installed successfully."
Write-Host
Write-Host "Task       : $taskName"
Write-Host "User       : $userId"
Write-Host "Launcher   : $pythonLauncher"
Write-Host "Application: $backgroundLauncher"
Write-Host
Write-Host "Orion will start automatically at your next sign-in."