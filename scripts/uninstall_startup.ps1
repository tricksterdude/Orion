$ErrorActionPreference = "Stop"

$taskName = "Orion Home Cinema"

$task = Get-ScheduledTask `
    -TaskName $taskName `
    -ErrorAction SilentlyContinue

if ($null -eq $task) {

    Write-Host
    Write-Host "Orion startup task is not installed."
    Write-Host

    exit 0
}

Unregister-ScheduledTask `
    -TaskName $taskName `
    -Confirm:$false

Write-Host
Write-Host "Orion startup task removed successfully."
Write-Host
Write-Host (
    "Orion will no longer start automatically " +
    "when you sign in."
)
Write-Host