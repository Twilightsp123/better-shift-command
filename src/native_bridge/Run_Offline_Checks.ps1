# No game access; builds standalone test programs.
[CmdletBinding()]
param([string]$Python='C:\Python313\python.exe',[string]$CMake='cmake')
$ErrorActionPreference='Stop'
& $Python (Join-Path $PSScriptRoot 'tools\run_checks.py') --cmake $CMake --generator 'Visual Studio 16 2019' --config Release
if ($LASTEXITCODE -ne 0) { throw 'Offline checks failed. See output/offline.' }
