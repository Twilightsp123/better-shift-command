
param([string]$GameRoot = "")
$ErrorActionPreference = "Stop"

function Test-Wh3Root([string]$p) {
    if ([string]::IsNullOrWhiteSpace($p)) { return $false }
    return (Test-Path (Join-Path $p "Warhammer3.exe")) -and (Test-Path (Join-Path $p "data"))
}

function Get-SteamRoots {
    $roots = New-Object System.Collections.Generic.List[string]
    foreach ($reg in @("HKCU:\Software\Valve\Steam", "HKLM:\SOFTWARE\WOW6432Node\Valve\Steam")) {
        try {
            $v = Get-ItemProperty -Path $reg -ErrorAction Stop
            foreach ($name in @("SteamPath", "InstallPath")) {
                $x = $v.$name
                if ($x -and (Test-Path $x) -and -not $roots.Contains($x)) { $roots.Add($x) }
            }
        } catch {}
    }
    foreach ($candidate in @("C:\Program Files (x86)\Steam", "C:\Program Files\Steam")) {
        if ((Test-Path $candidate) -and -not $roots.Contains($candidate)) { $roots.Add($candidate) }
    }
    return $roots
}

function Find-Wh3Root {
    foreach ($steam in Get-SteamRoots) {
        $libs = New-Object System.Collections.Generic.List[string]
        $libs.Add($steam)
        $vdf = Join-Path $steam "steamapps\libraryfolders.vdf"
        if (Test-Path $vdf) {
            $txt = Get-Content -Raw -LiteralPath $vdf
            foreach ($m in [regex]::Matches($txt, '"path"\s+"([^"]+)"')) {
                $lib = $m.Groups[1].Value -replace '\\\\','\'
                if ((Test-Path $lib) -and -not $libs.Contains($lib)) { $libs.Add($lib) }
            }
        }
        foreach ($lib in $libs) {
            $manifest = Join-Path $lib "steamapps\appmanifest_1142710.acf"
            if (Test-Path $manifest) {
                $txt = Get-Content -Raw -LiteralPath $manifest
                $m = [regex]::Match($txt, '"installdir"\s+"([^"]+)"')
                if ($m.Success) {
                    $root = Join-Path $lib ("steamapps\common\" + $m.Groups[1].Value)
                    if (Test-Wh3Root $root) { return $root }
                }
            }
            $fallback = Join-Path $lib "steamapps\common\Total War WARHAMMER III"
            if (Test-Wh3Root $fallback) { return $fallback }
        }
    }
    return $null
}

if (-not (Test-Wh3Root $GameRoot)) {
    $GameRoot = Find-Wh3Root
}
if (-not (Test-Wh3Root $GameRoot)) {
    Write-Host "Could not auto-detect Total War WARHAMMER III." -ForegroundColor Yellow
    $GameRoot = Read-Host "Paste the folder containing Warhammer3.exe"
}
if (-not (Test-Wh3Root $GameRoot)) { throw "Invalid game root: $GameRoot" }

$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$stateRoot = Join-Path $env:LOCALAPPDATA "BetterShiftCommand"
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupRoot = Join-Path $stateRoot ("backup_" + $stamp)
New-Item -ItemType Directory -Force -Path $stateRoot | Out-Null
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null

$items = @(
    @{ Source = (Join-Path $SourceRoot "wh3_native_bridge.dll"); Dest = (Join-Path $GameRoot "wh3_native_bridge.dll") },
    @{ Source = (Join-Path $SourceRoot "minhook.x64.dll"); Dest = (Join-Path $GameRoot "minhook.x64.dll") }
)
if (-not ($false)) {
    $items += @{ Source = (Join-Path $SourceRoot "data\better_shift_command.pack"); Dest = (Join-Path $GameRoot "data\better_shift_command.pack") }
}

$receipt = [ordered]@{ version="1.0.0"; game_root=$GameRoot; bridge_only=[bool]($false); installed_at=(Get-Date).ToString("o"); backup_root=$backupRoot; files=@() }
foreach ($item in $items) {
    if (-not (Test-Path $item.Source)) { throw "Release file missing: $($item.Source)" }
    $backup = $null
    if (Test-Path $item.Dest) {
        $backup = Join-Path $backupRoot ([IO.Path]::GetFileName($item.Dest))
        Copy-Item -LiteralPath $item.Dest -Destination $backup -Force
    }
    Copy-Item -LiteralPath $item.Source -Destination $item.Dest -Force
    $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $item.Dest).Hash.ToLowerInvariant()
    $receipt.files += [ordered]@{ path=$item.Dest; sha256=$h; backup=$backup }
    Write-Host "Installed: $($item.Dest)" -ForegroundColor Green
}
$receiptPath = Join-Path $stateRoot "install_receipt.json"
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8
Write-Host ""
Write-Host "Better Shift Command v1.0.0 installed." -ForegroundColor Cyan
if (-not ($false)) { Write-Host "Enable better_shift_command.pack in your WH3 Mod Manager before launching." }
Write-Host "Receipt: $receiptPath"
