$ErrorActionPreference = "Stop"
$env:UV_SYSTEM_CERTS = "true"

uv python install 3.11
uv sync --python 3.11 --frozen

Write-Host "Installation terminée. Lance .\run.ps1"
