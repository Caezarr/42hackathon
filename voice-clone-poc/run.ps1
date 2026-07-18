$ErrorActionPreference = "Stop"

$pythonPath = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw "Environnement absent. Lance d'abord .\setup.ps1"
}

& $pythonPath -m voice_clone_poc.app
