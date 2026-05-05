param(
    [int[]]$Ports = @(8000, 4173, 5173)
)

$ErrorActionPreference = "SilentlyContinue"

foreach ($port in $Ports) {
    Get-NetTCPConnection -LocalPort $port -State Listen | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force
        Write-Host "Stopped process $($_.OwningProcess) on port $port"
    }
}
