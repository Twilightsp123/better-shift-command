# Builds/tests in standalone local processes. DOES NOT install or launch Warhammer.
[CmdletBinding()]
param(
 [string]$GameExe='C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\Warhammer3.exe',
 [string]$Python='C:\Python313\python.exe',
 [string]$Generator='Visual Studio 16 2019',
 [string]$CMake='',
 [switch]$ExperimentalIssue
)
$ErrorActionPreference='Stop'
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw "Existing Python not found: $Python" }
if (-not (Test-Path -LiteralPath $GameExe -PathType Leaf)) { throw "Game EXE not found: $GameExe" }
$Arguments=@((Join-Path $PSScriptRoot 'tools\build_candidate.py'),'--exe',$GameExe,'--generator',$Generator)
if ($CMake) { $Arguments+=@('--cmake',$CMake) }
if ($ExperimentalIssue) { $Arguments+='--experimental-issue' }
& $Python @Arguments
if ($LASTEXITCODE -ne 0) { throw 'Build/verification failed. Keep the current game installation unchanged; return BUILD_RESULT.json and logs.' }
