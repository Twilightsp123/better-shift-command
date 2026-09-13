
param([string]$GameRoot = "")
$ErrorActionPreference = "Stop"
$stateRoot = Join-Path $env:LOCALAPPDATA "BetterShiftCommand"
$receiptPath = Join-Path $stateRoot "install_receipt.json"
if (-not (Test-Path $receiptPath)) {
    Write-Host "No installer receipt found. Nothing was removed." -ForegroundColor Yellow
    Write-Host "Manual files are: better_shift_command.pack, wh3_native_bridge.dll, minhook.x64.dll"
    exit 0
}
$r = Get-Content -Raw -LiteralPath $receiptPath | ConvertFrom-Json
foreach ($f in $r.files) {
    $path = [string]$f.path
    if (Test-Path $path) {
        $actual = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
        if ($actual -eq ([string]$f.sha256).ToLowerInvariant()) {
            Remove-Item -LiteralPath $path -Force
            Write-Host "Removed: $path" -ForegroundColor Green
        } else {
            Write-Host "Kept modified file: $path" -ForegroundColor Yellow
        }
    }
    if ($f.backup -and (Test-Path ([string]$f.backup))) {
        Copy-Item -LiteralPath ([string]$f.backup) -Destination $path -Force
        Write-Host "Restored backup: $path" -ForegroundColor Green
    }
}
Remove-Item -LiteralPath $receiptPath -Force -ErrorAction SilentlyContinue
Write-Host "Better Shift Command uninstall complete." -ForegroundColor Cyan
