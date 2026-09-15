[CmdletBinding()]
param(
    [string]$GameDir = 'C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III',
    [string]$PackName = 'zzz_better_shift_command_steam.pack'
)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $MyInvocation.MyCommand.Path
if (Get-Process -Name Warhammer3 -ErrorAction SilentlyContinue) { throw 'Warhammer3.exe is running. Exit the game completely before building/installing.' }
$Exe=Join-Path $GameDir 'Warhammer3.exe'
if (-not (Test-Path -LiteralPath $Exe -PathType Leaf)) { throw "Warhammer3.exe not found: $Exe" }

# IMPORTANT: do NOT silently move to VS2022/v143. The runtime-validated v0.5.0 DLL used linker 14.29 (VS2019/v142).
$VsWhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
$CMake=$null; $Gen=$null; $Toolset=$null; $ToolchainLabel=$null
if (Test-Path -LiteralPath $VsWhere) {
    $vs2019 = (& $VsWhere -version '[16.0,17.0)' -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath | Select-Object -First 1)
    if ($vs2019) {
        $candidate=Join-Path $vs2019 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
        if (Test-Path -LiteralPath $candidate) { $CMake=$candidate; $Gen='Visual Studio 16 2019'; $ToolchainLabel='VS2019/v142 native' }
    }
    if (-not $CMake) {
        $vs2022 = (& $VsWhere -version '[17.0,18.0)' -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath | Select-Object -First 1)
        if ($vs2022) {
            $v142 = Get-ChildItem -Path (Join-Path $vs2022 'VC\Tools\MSVC') -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like '14.29*' } | Sort-Object Name -Descending | Select-Object -First 1
            $candidate=Join-Path $vs2022 'Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
            if ($v142 -and (Test-Path -LiteralPath $candidate)) { $CMake=$candidate; $Gen='Visual Studio 17 2022'; $Toolset='v142'; $ToolchainLabel='VS2022 generator + v142 toolset' }
        }
    }
}
if (-not $CMake) {
    # Last explicit VS2019 BuildTools path check.
    $candidate='C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\Common7\IDE\CommonExtensions\Microsoft\CMake\CMake\bin\cmake.exe'
    if (Test-Path -LiteralPath $candidate) { $CMake=$candidate; $Gen='Visual Studio 16 2019'; $ToolchainLabel='VS2019/v142 BuildTools' }
}
if (-not $CMake) {
    throw 'Validated v142 toolchain not found. Install Visual Studio 2019 Build Tools (C++ x64), or install the v142 toolset in Visual Studio 2022. This script intentionally refuses v143.'
}
Write-Host "TOOLCHAIN: $ToolchainLabel" -ForegroundColor Cyan
Write-Host "CMAKE:     $CMake"
Write-Host "GENERATOR: $Gen"
if ($Toolset) { Write-Host "TOOLSET:   $Toolset" }

$Py=(Get-Command py.exe -ErrorAction SilentlyContinue).Source
$Python=(Get-Command python.exe -ErrorAction SilentlyContinue).Source
if (-not $Py -and -not $Python) { throw 'Python 3 not found.' }
function Run-Python([string[]]$Args) { if ($Py) { & $Py -3 @Args } else { & $Python @Args }; if ($LASTEXITCODE) { throw 'Python command failed' } }

$Build=Join-Path $Root 'output\build_win64_v142'
if (Test-Path $Build) { Remove-Item -Recurse -Force $Build }
New-Item -ItemType Directory -Force -Path $Build | Out-Null
Write-Host '[1/6] Configuring release Native Bridge v0.5.1 with validated v142-family toolchain...'
$args=@('-S',(Join-Path $Root 'src\native_bridge'),'-B',$Build,'-G',$Gen,'-A','x64','-DWH3_ALLOW_UNVALIDATED_NATIVE_ISSUE=ON')
if ($Toolset) { $args += @('-T',$Toolset) }
& $CMake @args
if ($LASTEXITCODE) { throw 'CMake configure failed' }

Write-Host '[2/6] Building Bridge + core + Windows backend/module smoke tests...'
& $CMake --build $Build --config Release --target wh3_native_bridge test_identity_gate test_host test_packet_tracker test_integrated_host test_lua_exports backend_smoke module_load_smoke
if ($LASTEXITCODE) { throw 'CMake build failed' }

$CTest=Join-Path (Split-Path $CMake -Parent) 'ctest.exe'
if (-not (Test-Path $CTest)) { $CTest=(Get-Command ctest.exe -ErrorAction Stop).Source }
Write-Host '[3/6] Running core + MinHook private-process + module-load smoke tests...'
& $CTest --test-dir $Build -C Release -R 'identity_gate_scenarios|native_host_forwarding|lua_export_contract|packet_physical_lifetimes|integrated_host_pipeline|backend_private_process|module_private_process' --output-on-failure
if ($LASTEXITCODE) { throw 'Offline/private-process tests failed; NOT installing.' }

$Bridge=Join-Path $Build 'Release\wh3_native_bridge.dll'
if (-not (Test-Path $Bridge)) { $Bridge=(Get-ChildItem -Path $Build -Recurse -Filter wh3_native_bridge.dll | Select-Object -First 1).FullName }
if (-not $Bridge) { throw 'Compiled wh3_native_bridge.dll not found' }
Write-Host '[4/6] Verifying PE toolchain matches runtime-validated linker family (14.29)...'
Run-Python @((Join-Path $Root 'tools\verify_pe_toolchain.py'),$Bridge)

Write-Host '[5/6] Building self-contained Steam PFH5 pack...'
$OutDir=Join-Path $Root 'output\ready_to_install'; New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$Pack=Join-Path $OutDir $PackName
Run-Python @((Join-Path $Root 'tools\build_selfcontained_pack.py'),'--bridge',$Bridge,'--minhook',(Join-Path $Root 'baseline\minhook.x64.dll'),'--controller-template',(Join-Path $Root 'src\better_shift_command_selfcontained.template.lua'),'--license',(Join-Path $Root 'baseline\MINHOOK_LICENSE.txt'),'--out',$Pack)

Write-Host '[6/6] Backing up and installing release pack...'
$Stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
$Backup=Join-Path $Root ("output\backup_release_"+$Stamp); New-Item -ItemType Directory -Force -Path $Backup | Out-Null
$DataDir=Join-Path $GameDir 'data'; $DestPack=Join-Path $DataDir $PackName
foreach ($Item in @($DestPack,(Join-Path $GameDir 'wh3_native_bridge.dll'),(Join-Path $GameDir 'minhook.x64.dll'))) {
    if (Test-Path -LiteralPath $Item -PathType Leaf) { Copy-Item -LiteralPath $Item -Destination (Join-Path $Backup ([IO.Path]::GetFileName($Item))) -Force }
}
Copy-Item -LiteralPath $Pack -Destination $DestPack -Force
$bridgeHash=(Get-FileHash -Algorithm SHA256 -LiteralPath $Bridge).Hash.ToLowerInvariant()
$packHash=(Get-FileHash -Algorithm SHA256 -LiteralPath $Pack).Hash.ToLowerInvariant()
@{game_dir=$GameDir;pack=$DestPack;backup=$Backup;bridge_build=$Bridge;bridge_sha256=$bridgeHash;pack_sha256=$packHash;toolchain=$ToolchainLabel;installed_at=(Get-Date).ToString('o')} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $OutDir 'install_receipt_release.json')
Write-Host ''
Write-Host 'RELEASE BUILD/INSTALL COMPLETE - v1.0.1' -ForegroundColor Green
Write-Host "Bridge SHA256: $bridgeHash"
Write-Host "Pack SHA256:   $packHash"
Write-Host "Pack:          $DestPack"
Write-Host "Backup:        $Backup"
Write-Host 'IMPORTANT: only one Better Shift Command pack should supply script\battle\mod\better_shift_command.lua.'
